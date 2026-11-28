"""One GRPO update of grpo.py --c7, instrumented: where does a non-finite or huge gradient come from?

Replays step 1 of a run (same model, seed, batch draw and loss as grpo.py) on DEVICE, then the same sequences on the
CPU, and prints for each: finiteness of the old log-probabilities, of the new ones, the largest ratio, each chunk's
loss, the gradient norm before clipping and the first parameters whose gradient is not finite. Nothing is written
under results/. Usage, from sim/llm: DEVICE=mps MICRO=8 ../env-llm/bin/python diag/grad_step.py MODEL SEED [REWARD]
"""
import os, random, sys, json, math
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL, SEED = sys.argv[1], int(sys.argv[2])
REWARD = sys.argv[3] if len(sys.argv) > 3 else "true"
B, G, MAX_NEW, CLIP = 4, 8, 160, 0.2
MICRO = int(os.environ.get("MICRO", 8))
device = os.environ.get("DEVICE", "mps")
REVISION = {"Qwen/Qwen2.5-0.5B-Instruct": "7ae557604adf67be50417f59c2c2f167def9a775",
            "unsloth/Llama-3.2-1B-Instruct": "5a8abab4a5d6f164389b1079fb721cfab8d7126c"}[MODEL]
torch.manual_seed(SEED); random.seed(SEED)
ps = [(a, b) for a in range(12, 100) for b in range(12, 100)]
random.Random(12345).shuffle(ps)
ALL = [(f"What is {a} * {b}?", a * b) for a, b in ps]
TRAIN = ALL[450:]
rng = random.Random(SEED)
tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
tok.pad_token = tok.pad_token or tok.eos_token
tok.padding_side = "left"
eos = None
INSTR = " Think step by step, then finish with the final answer as an integer."


def load(dev):
    kw = {"attn_implementation": os.environ["ATTN"]} if os.environ.get("ATTN") else {}
    m = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, dtype=torch.float32, **kw).to(dev)
    return m


model = load(device)
e = model.generation_config.eos_token_id
STOP = sorted({tok.pad_token_id, tok.eos_token_id, *(e if isinstance(e, list) else [e])} - {None})
prompt = lambda q: tok.apply_chat_template([{"role": "user", "content": q + INSTR}], tokenize=False, add_generation_prompt=True)


def token_logps(m, seqs, plen):
    attn = (seqs != tok.pad_token_id).long()
    if os.environ.get("NOMASK"):
        attn = torch.ones_like(attn)
    logits = m(input_ids=seqs, attention_mask=attn).logits[:, plen - 1:-1]
    target = seqs[:, plen:]
    lp = torch.log_softmax(logits, -1).gather(2, target.unsqueeze(-1)).squeeze(-1)
    stop = torch.isin(target, torch.tensor(STOP, device=target.device)).long()
    mask = ((torch.cumsum(stop, 1) - stop) == 0).float()
    return lp, mask, attn, logits


batch = rng.sample(TRAIN, B)
model.eval()
enc = tok([prompt(q) for q, _ in batch], return_tensors="pt", padding=True).to(device)
with torch.no_grad():
    out = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=True, temperature=1.0, top_p=None, top_k=None,
                         num_return_sequences=G, pad_token_id=tok.pad_token_id, repetition_penalty=1.0)
plen, seqs = enc["input_ids"].shape[1], out.cpu()
import re
def correct(t, a):
    n = re.findall(r"-?\d[\d,]*", t)
    return bool(n) and n[-1].replace(",", "").lstrip("-").isdigit() and int(n[-1].replace(",", "")) == a
answers = [a for _, a in batch for _ in range(G)]
right = [correct(tok.decode(s[plen:], skip_special_tokens=True), a) for s, a in zip(seqs, answers)]
rewards = torch.tensor([float(x) if REWARD == "true" else float(rng.random() < 0.5) for x in right])
groups = rewards.view(B, G)
adv = ((groups - groups.mean(1, keepdim=True)) / (groups.std(1, keepdim=True) + 1e-4)).view(-1)
print(json.dumps(dict(model=MODEL, seed=SEED, device=device, plen=plen, seqlen=seqs.shape[1], right=sum(right),
                      pad_id=tok.pad_token_id, stop=STOP,
                      rows_all_pad_after_prompt=int(((seqs[:, plen:] == tok.pad_token_id).all(1)).sum()),
                      prompt_left_pads=[int((r[:plen] == tok.pad_token_id).sum()) for r in seqs[::G]])))


def one_update(m, dev, label):
    torch.autograd.set_detect_anomaly(bool(os.environ.get("ANOMALY")))
    m.train(); m.zero_grad()
    S, A = seqs.to(dev), adv.to(dev)
    chunks = [slice(i, i + MICRO) for i in range(0, len(S), MICRO)]
    with torch.no_grad():
        old = [token_logps(m, S[c], plen)[0] for c in chunks]
    info = dict(label=label, old_finite=[bool(torch.isfinite(o).all()) for o in old])
    parts = []
    for c, olp in zip(chunks, old):
        lp, mask, attn, logits = token_logps(m, S[c], plen)
        ratio = torch.exp(lp - olp)
        a = A[c].unsqueeze(1)
        surr = torch.min(ratio * a, torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a)
        part = -((surr * mask).sum(1) / mask.sum(1).clamp(min=1)).sum() / len(S)
        part.backward()
        parts.append(dict(lp_finite=bool(torch.isfinite(lp).all()), logits_finite=bool(torch.isfinite(logits).all()),
                          logits_absmax=float(logits.detach().abs().max()), ratio_max=float(ratio.detach().max()),
                          ratio_min=float(ratio.detach().min()), part=float(part.detach())))
    grads = [(n, p.grad) for n, p in m.named_parameters() if p.grad is not None]
    bad = [n for n, g in grads if not torch.isfinite(g).all()]
    norm = math.sqrt(sum(float(g.double().pow(2).sum()) for _, g in grads if torch.isfinite(g).all()))
    info.update(chunks=parts, n_bad_grads=len(bad), first_bad=bad[:5], finite_part_norm=norm)
    print(json.dumps(info))


one_update(model, device, device + " attn=" + str(model.config._attn_implementation))
if device != "cpu" and not os.environ.get("SKIP_CPU"):
    del model
    if device == "mps":
        torch.mps.empty_cache()
    one_update(load("cpu"), "cpu", "cpu (same sequences)")
