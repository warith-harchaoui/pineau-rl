"""Hand-written GRPO on small LLMs, on Apple MPS: true reward against a coin-flip reward.

Usage: python grpo.py MODEL_ID TAG TASK REWARD SEED STEPS LR [--pilot] [--c7]
TASK in {add3, mul2}; REWARD in {true, random}. Writes results/<TAG>/<TASK>/<REWARD>/seed<SEED>.jsonl
--c7 (LLM_PROTOCOL.md, deviation 20) changes only what follows, and nothing without it, so the nineteen runs of
deviations 13 to 16 stay reproducible: repetition_penalty = 1.0 (deviation 18 (a)); a pilot split ALL[300:450] held out
from both test and training (--pilot reads it); an evaluation on all 300 test problems (greedy at 160 tokens, greedy at
512 tokens, 8 samples at 160 tokens), drawing from its own random stream, with per-problem verdicts, lengths and
completions in seed<SEED>.items.jsonl.gz; a training line every step (gradient norms of both passes, groups with zero
advantage); the device and versions in a first line; the gradient mask keeps the first stop token, and every stop id of
the model's generation_config counts as an end (deviation 18 (d)).
"""
import gzip, json, math, os, random, re, sys, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL, TAG, TASK, REWARD, SEED, STEPS, LR = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7])
PILOT = "--pilot" in sys.argv  # no training: base-model accuracy (on TEST without --c7: deviation 18 (b))
C7 = "--c7" in sys.argv  # deviation 20
B, G, MAX_NEW, CLIP, EPOCHS = 4, 8, 160, 0.2, 2
EVAL_EVERY = int(os.environ.get("EVAL_EVERY", 100 if C7 else 50))
MAX_NEW_LONG = 512  # --c7: the greedy answer with a budget the cap of 160 does not bind (length-independent measure)
EVAL_N = int(os.environ.get("EVAL_N", 300))  # --c7: test problems per evaluation (smaller only for a smoke test)
MICRO = int(os.environ.get("MICRO", 8))  # completions per backward pass (same gradient): 32 at once took 65 GB; Llama 1B needs 2
# macOS aborts GPU work that slows the desktop down (kIOGPUCommandBufferCallbackErrorImpactingInteractivity), and an
# aborted computation can come back as NaN or as a finite but absurd gradient (LLM_PROTOCOL.md, écart 10). The same
# update on CPU has a gradient norm of 14 before clipping: above GRAD_SANE, or non-finite, the update is recomputed.
GRAD_SANE, RETRIES = 1e3, 5
device = os.environ.get("DEVICE") or ("mps" if torch.backends.mps.is_available() else "cpu")  # DEVICE=cpu: écart 11
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
if C7:  # deviation 20: 150 pilot problems held out from both test and training
    PILOT_SET, TRAIN = ALL[300:450], ALL[450:]
rng = random.Random(SEED)  # the reward coins and the problem draws depend on the run seed only
# The exact model files every run used: the only revision in the cache, downloaded on 22 and 27 October 2026
REVISION = {"Qwen/Qwen2.5-0.5B-Instruct": "7ae557604adf67be50417f59c2c2f167def9a775",
            "unsloth/Llama-3.2-1B-Instruct": "5a8abab4a5d6f164389b1079fb721cfab8d7126c"}.get(MODEL)
tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
tok.pad_token = tok.pad_token or tok.eos_token
tok.padding_side = "left"
model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float32).to(device)
opt = torch.optim.Adam(model.parameters(), lr=LR)
# --c7: every stop id of the model ends a completion (Llama stops on 128001, 128008 and 128009; Qwen on 151645 and 151643)
eos = model.generation_config.eos_token_id
STOP = sorted({tok.pad_token_id, tok.eos_token_id, *(eos if isinstance(eos, list) else [eos])} - {None})
GEN_EXTRA = dict(repetition_penalty=1.0) if C7 else {}  # deviation 18 (a): Qwen's generation_config sets 1.1
INSTR = " Think step by step, then finish with the final answer as an integer."


def prompt(q):
    return tok.apply_chat_template([{"role": "user", "content": q + INSTR}], tokenize=False, add_generation_prompt=True)


def correct(text, ans):
    nums = re.findall(r"-?\d[\d,]*", text)
    return bool(nums) and nums[-1].replace(",", "").lstrip("-").isdigit() and int(nums[-1].replace(",", "")) == ans


retries = {"generate": 0, "update": 0}


@torch.no_grad()
def generate(qs, n, sample, max_new=MAX_NEW):
    enc = tok([prompt(q) for q in qs], return_tensors="pt", padding=True).to(device)
    for attempt in range(RETRIES):
        try:
            out = model.generate(**enc, max_new_tokens=max_new, do_sample=sample, temperature=1.0 if sample else None,
                                 top_p=None, top_k=None, num_return_sequences=n, pad_token_id=tok.pad_token_id, **GEN_EXTRA)
            out.tolist()  # forces the GPU work to finish here, so that an aborted command buffer raises now
            return enc["input_ids"].shape[1], out
        except torch.AcceleratorError:
            retries["generate"] += 1
    raise RuntimeError(f"generation failed {RETRIES} times in a row")


def truncated(seq, plen):
    """True when the completion hit MAX_NEW tokens without an end-of-sequence token."""
    return not bool((seq[plen:] == tok.pad_token_id).any() or (seq[plen:] == tok.eos_token_id).any())


def ended(seq, plen):
    """--c7: index (in the completion) of the first stop token, or None when the completion was cut off."""
    hit = torch.isin(seq[plen:], torch.tensor(STOP, device=seq.device)).nonzero()
    return int(hit[0]) if len(hit) else None


def evaluate_c7(problems, step):
    """--c7: greedy at 160 and 512 tokens and 8 samples at 160 tokens on every problem, from its own random stream
    (seeded by the run seed and the step, so the true and random runs of a seed draw the same evaluation at step 0)."""
    model.eval()
    cpu_state = torch.get_rng_state()
    mps_state = torch.mps.get_rng_state() if device == "mps" else None
    torch.manual_seed(1_000_003 * SEED + step)
    items = [dict(i=i) for i in range(len(problems))]

    def verdicts(out, plen, chunk, per):
        res = []
        for j, (_, a) in enumerate(chunk):
            rows = []
            for s in out[j * per:(j + 1) * per]:
                e = ended(s, plen)
                text = tok.decode(s[plen:], skip_special_tokens=True)
                rows.append(dict(ok=correct(text, a), n=(e + 1) if e is not None else len(s) - plen, cut=e is None, text=text))
            res.append(rows)
        return res

    for key, n, sample, max_new, size in (("greedy", 1, False, MAX_NEW, 32), ("greedy512", 1, False, MAX_NEW_LONG, 32),
                                          ("samples", 8, True, MAX_NEW, 10)):
        for i in range(0, len(problems), size):
            chunk = problems[i:i + size]
            plen, out = generate([q for q, _ in chunk], n, sample, max_new)
            for j, rows in enumerate(verdicts(out, plen, chunk, n)):
                items[i + j][key] = rows if sample else rows[0]
    if device == "mps":
        torch.mps.set_rng_state(mps_state)
    torch.set_rng_state(cpu_state)
    model.train()
    smp = [r for it in items for r in it["samples"]]
    fin = [r for r in smp if not r["cut"]]
    summary = dict(greedy=sum(it["greedy"]["ok"] for it in items) / len(items),
                   greedy512=sum(it["greedy512"]["ok"] for it in items) / len(items),
                   pass1=sum(r["ok"] for r in smp) / len(smp),
                   pass8=sum(any(r["ok"] for r in it["samples"]) for it in items) / len(items),
                   truncated=sum(r["cut"] for r in smp) / len(smp),
                   truncated_greedy512=sum(it["greedy512"]["cut"] for it in items) / len(items),
                   finished=sum(r["ok"] for r in fin) / len(fin) if fin else None,
                   cut_right=sum(r["ok"] for r in smp if r["cut"]),  # checks deviation 5's "a cut-off answer is never right"
                   mean_len=sum(r["n"] for r in smp) / len(smp), n_items=len(items))
    return summary, items


def evaluate():
    model.eval()
    good, n_greedy, n_sampled, cut = 0, 150, 50, 0
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
            cut += sum(truncated(s, plen) for s in out[j * 8:(j + 1) * 8])
    model.train()
    return dict(greedy=good / n_greedy, pass1=p1 / n_sampled, pass8=p8 / n_sampled, truncated=cut / (8 * n_sampled))


def token_logps(seqs, plen):
    """Log-probability of every completion token, with a mask that stops after the first EOS."""
    attn = (seqs != tok.pad_token_id).long()
    logits = model(input_ids=seqs, attention_mask=attn).logits[:, plen - 1:-1]
    target = seqs[:, plen:]
    lp = torch.log_softmax(logits, -1).gather(2, target.unsqueeze(-1)).squeeze(-1)
    mask = token_mask(target) if C7 else (target != tok.pad_token_id).float()
    return lp, mask


def token_mask(target):
    """--c7: 1 up to and including the first stop token, 0 after it (deviation 18 (d))."""
    stop = torch.isin(target, torch.tensor(STOP, device=target.device)).long()
    before = torch.cumsum(stop, 1) - stop  # stop tokens strictly before each position
    return (before == 0).float()


if PILOT:
    if C7:
        s, items = evaluate_c7(PILOT_SET[:EVAL_N], 0)
        os.makedirs(f"results/{TAG}", exist_ok=True)
        with gzip.open(f"results/{TAG}/pilot.items.jsonl.gz", "wt") as f:
            f.write("\n".join(json.dumps(it) for it in items) + "\n")
        print(json.dumps(dict(model=TAG, task=TASK, split="ALL[300:450]", device=device, **s)))
    else:
        print(json.dumps(dict(model=TAG, task=TASK, **evaluate())))
    sys.exit(0)

out_path = f"results/{TAG}/{TASK}/{REWARD}/seed{SEED}.jsonl"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
log = open(out_path, "w")
if C7:
    import transformers
    item_log = gzip.open(out_path.replace(".jsonl", ".items.jsonl.gz"), "wt")
    log.write(json.dumps(dict(step=-1, device=device, c7=True, model=MODEL, revision=REVISION, lr=LR, steps=STEPS, micro=MICRO,
                              stop=STOP, gen_extra=GEN_EXTRA, torch=torch.__version__, transformers=transformers.__version__,
                              eval_n=EVAL_N)) + "\n")

    def log_eval(step):
        s, items = evaluate_c7(TEST[:EVAL_N], step)
        log.write(json.dumps(dict(step=step, **s)) + "\n"); log.flush()
        item_log.write(json.dumps(dict(step=step, items=items)) + "\n"); item_log.flush()
    log_eval(0)
else:
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
    chunks = [slice(i, i + MICRO) for i in range(0, len(seqs), MICRO)]
    with torch.no_grad():
        old_lp = [token_logps(seqs[c], plen)[0] for c in chunks]
    if not all(torch.isfinite(o).all() for o in old_lp):
        raise RuntimeError("non-finite log-probabilities before the update: the weights are already corrupted")
    norms = []
    for _ in range(EPOCHS):
        for attempt in range(RETRIES):
            opt.zero_grad(); loss = 0.0
            try:
                for c, olp in zip(chunks, old_lp):
                    lp, mask = token_logps(seqs[c], plen)
                    ratio = torch.exp(lp - olp)
                    a = adv[c].unsqueeze(1)
                    surr = torch.min(ratio * a, torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a)
                    part = -((surr * mask).sum(1) / mask.sum(1).clamp(min=1)).sum() / len(seqs)
                    part.backward(); loss += part.item()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).item()
            except torch.AcceleratorError:
                norm = float("nan")
            if math.isfinite(norm) and norm < GRAD_SANE:
                break
            retries["update"] += 1
        else:
            raise RuntimeError(f"gradient non-finite or above {GRAD_SANE:g} {RETRIES} times in a row")
        norms.append(norm)
        opt.step()
        if not all(torch.isfinite(q).all() for q in model.parameters()):
            raise RuntimeError("non-finite weights after the update")
    if device == "mps":
        torch.mps.empty_cache()  # the cache grew until Llama 1B ran out of memory after 10 to 60 steps (écart 12)
    if C7:
        cut = [ended(q, plen) is None for q in seqs]
        log.write(json.dumps(dict(step=step, train_right=sum(right) / len(right), truncated=sum(cut) / len(cut), loss=loss,
                                  grad_norms=norms, zero_adv_groups=int((groups.std(1) == 0).sum()), retries=dict(retries),
                                  wall=round(time.time() - t0, 1))) + "\n"); log.flush()
    elif step % 10 == 0:
        log.write(json.dumps(dict(step=step, train_right=sum(right) / len(right), truncated=sum(truncated(q, plen) for q in seqs) / len(seqs), loss=loss, grad_norm=norm, retries=dict(retries), wall=round(time.time() - t0, 1))) + "\n"); log.flush()
    if step % EVAL_EVERY == 0 or step == STEPS:
        if C7:
            log_eval(step)
        else:
            log.write(json.dumps(dict(step=step, **evaluate())) + "\n"); log.flush()
if C7:
    item_log.close()
print(json.dumps(dict(model=TAG, task=TASK, reward=REWARD, seed=SEED, done=True, retries=retries, wall=round(time.time() - t0, 1))))
