"""Hand-written GRPO on small LLMs, on Apple MPS: true reward against a coin-flip reward.

Usage: python grpo.py MODEL_ID TAG TASK REWARD SEED STEPS LR
TASK in {add3, mul2}; REWARD in {true, random}. Writes results/<TAG>/<TASK>/<REWARD>/seed<SEED>.jsonl
"""
import json, os, random, re, sys, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL, TAG, TASK, REWARD, SEED, STEPS, LR = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7])
PILOT = "--pilot" in sys.argv  # no training: base-model accuracy on non-test problems
B, G, MAX_NEW, CLIP, EPOCHS, EVAL_EVERY = 4, 8, 160, 0.2, 2, int(os.environ.get("EVAL_EVERY", 50))
device = "mps" if torch.backends.mps.is_available() else "cpu"
torch.manual_seed(SEED); random.seed(SEED)


def problems(task):
    if task == "add3":
        ps = [(a, b, c) for a in range(10, 100, 3) for b in range(10, 100, 3) for c in range(10, 100, 3)]
        make = lambda p: (f"What is {p[0]} + {p[1]} + {p[2]}?", p[0] + p[1] + p[2])
    else:
        ps = [(a, b) for a in range(12, 100) for b in range(12, 100)]
        make = lambda p: (f"What is {p[0]} * {p[1]}?", p[0] * p[1])
    random.Random(12345).shuffle(ps)  # fixed split, independent of the run seed
    return [make(p) for p in ps]


ALL = problems(TASK)
TEST, TRAIN = ALL[:300], ALL[300:]
rng = random.Random(SEED)  # the reward coins and the problem draws depend on the run seed only
tok = AutoTokenizer.from_pretrained(MODEL)
tok.pad_token = tok.pad_token or tok.eos_token
tok.padding_side = "left"
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32).to(device)
opt = torch.optim.Adam(model.parameters(), lr=LR)
INSTR = " Think step by step, then finish with the final answer as an integer."


def prompt(q):
    return tok.apply_chat_template([{"role": "user", "content": q + INSTR}], tokenize=False, add_generation_prompt=True)


def correct(text, ans):
    nums = re.findall(r"-?\d[\d,]*", text)
    return bool(nums) and nums[-1].replace(",", "").lstrip("-").isdigit() and int(nums[-1].replace(",", "")) == ans


@torch.no_grad()
def generate(qs, n, sample):
    enc = tok([prompt(q) for q in qs], return_tensors="pt", padding=True).to(device)
    out = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=sample, temperature=1.0 if sample else None,
                         top_p=None, top_k=None, num_return_sequences=n, pad_token_id=tok.pad_token_id)
    return enc["input_ids"].shape[1], out


def evaluate():
    model.eval()
    good, n_greedy, n_sampled = 0, 150, 50
    for i in range(0, n_greedy, 32):
        chunk = TEST[i:min(i + 32, n_greedy)]
        plen, out = generate([q for q, _ in chunk], 1, False)
        good += sum(correct(tok.decode(s[plen:], skip_special_tokens=True), a) for s, (_, a) in zip(out, chunk))
    p1, p8 = 0.0, 0
    for i in range(0, n_sampled, 10):
        chunk = TEST[i:i + 10]
        plen, out = generate([q for q, _ in chunk], 8, True)
        for j, (_, a) in enumerate(chunk):
            hits = [correct(tok.decode(s[plen:], skip_special_tokens=True), a) for s in out[j * 8:(j + 1) * 8]]
            p1 += sum(hits) / 8; p8 += any(hits)
    model.train()
    return dict(greedy=good / n_greedy, pass1=p1 / n_sampled, pass8=p8 / n_sampled)


def token_logps(seqs, plen):
    """Log-probability of every completion token, with a mask that stops after the first EOS."""
    attn = (seqs != tok.pad_token_id).long()
    logits = model(input_ids=seqs, attention_mask=attn).logits[:, plen - 1:-1]
    target = seqs[:, plen:]
    lp = torch.log_softmax(logits, -1).gather(2, target.unsqueeze(-1)).squeeze(-1)
    mask = (target != tok.pad_token_id).float()
    return lp, mask


if PILOT:
    print(json.dumps(dict(model=TAG, task=TASK, **evaluate())))
    sys.exit(0)

out_path = f"results/{TAG}/{TASK}/{REWARD}/seed{SEED}.jsonl"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
log = open(out_path, "w")
log.write(json.dumps(dict(step=0, **evaluate())) + "\n"); log.flush()
t0 = time.time()
for step in range(1, STEPS + 1):
    batch = rng.sample(TRAIN, B)
    model.eval()
    plen, seqs = generate([q for q, _ in batch], G, True)
    model.train()
    answers = [a for _, a in batch for _ in range(G)]
    right = [correct(tok.decode(s[plen:], skip_special_tokens=True), a) for s, a in zip(seqs, answers)]
    rewards = torch.tensor([float(x) if REWARD == "true" else float(rng.random() < 0.5) for x in right], device=device)
    groups = rewards.view(B, G)
    adv = ((groups - groups.mean(1, keepdim=True)) / (groups.std(1, keepdim=True) + 1e-4)).view(-1)
    with torch.no_grad():
        old_lp, mask = token_logps(seqs, plen)
    for _ in range(EPOCHS):
        lp, mask = token_logps(seqs, plen)
        ratio = torch.exp(lp - old_lp)
        a = adv.unsqueeze(1)
        surr = torch.min(ratio * a, torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a)
        loss = -((surr * mask).sum(1) / mask.sum(1).clamp(min=1)).mean()
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    if step % 10 == 0:
        log.write(json.dumps(dict(step=step, train_right=sum(right) / len(right), loss=float(loss), wall=round(time.time() - t0, 1))) + "\n"); log.flush()
    if step % EVAL_EVERY == 0 or step == STEPS:
        log.write(json.dumps(dict(step=step, **evaluate())) + "\n"); log.flush()
print(json.dumps(dict(model=TAG, task=TASK, reward=REWARD, seed=SEED, done=True, wall=round(time.time() - t0, 1))))
