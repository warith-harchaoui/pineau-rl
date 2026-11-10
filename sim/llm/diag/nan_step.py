"""Where does the NaN of the crashed GRPO runs come from (LLM_PROTOCOL.md, écarts 7 to 9)? No result is kept.

Replays the first training steps of `grpo.py` (Qwen 0.5B, mul2, random reward, seed 1) and, at each step, checks
for non-finite values in: the sampling logits, the old and new log-probabilities, the loss, every gradient, the
weights after the update. Stops at the first non-finite value and says where.
Usage, from sim/llm/: ../env-llm/bin/python diag/nan_step.py [STEPS] [DEVICE]  -> diag/nan_step.out
"""
import math, os, sys
sys.argv = [sys.argv[0], "Qwen/Qwen2.5-0.5B-Instruct", "diag", "mul2", "random", "1", sys.argv[1] if len(sys.argv) > 1 else "5",
            "3e-6"] + sys.argv[2:3]
src = open(os.path.join(os.path.dirname(__file__), "..", "grpo.py")).read()
head = src.split("if PILOT:")[0]  # everything up to the training loop: problems, model, helpers
if len(sys.argv) > 8:
    head = head.replace('device = "mps" if torch.backends.mps.is_available() else "cpu"', f'device = "{sys.argv[8]}"')
if os.environ.get("NOMASK"):  # same logits on every scored token: the model is causal, padding only follows them
    head = head.replace("logits = model(input_ids=seqs, attention_mask=attn).logits", "logits = model(input_ids=seqs).logits")
if os.environ.get("EAGER"):  # plain attention instead of scaled_dot_product_attention
    head = head.replace("torch_dtype=torch.float32)", "torch_dtype=torch.float32, attn_implementation='eager')")
exec(head)
if os.environ.get("ANOMALY"):
    torch.autograd.set_detect_anomaly(True, check_nan=True)


def finite(name, x):
    bad = (~torch.isfinite(x)).sum().item()
    if bad:
        print(f"  NON-FINITE {name}: {bad} of {x.numel()}")
    return bad == 0


print("device", device)
for step in range(1, STEPS + 1):
    batch = rng.sample(TRAIN, B)
    model.eval()
    plen, seqs = generate([q for q, _ in batch], G, True)
    model.train()
    right = [correct(tok.decode(s[plen:], skip_special_tokens=True), a) for s, a in zip(seqs, [a for _, a in batch for _ in range(G)])]
    rewards = torch.tensor([float(rng.random() < 0.5) for _ in right], device=device)
    groups = rewards.view(B, G)
    adv = ((groups - groups.mean(1, keepdim=True)) / (groups.std(1, keepdim=True) + 1e-4)).view(-1)
    eos_in = [(s[plen:] == tok.eos_token_id).any().item() for s in seqs]
    print(f"step {step}: seqs {tuple(seqs.shape)}, finished {sum(eos_in)}/{len(seqs)}, adv max |{adv.abs().max().item():.1f}|")
    chunks = [slice(i, i + MICRO) for i in range(0, len(seqs), MICRO)]
    with torch.no_grad():
        old_lp = [token_logps(seqs[c], plen)[0] for c in chunks]
    ok = all(finite(f"old_lp chunk {i}", o) for i, o in enumerate(old_lp))
    for ep in range(EPOCHS):
        opt.zero_grad()
        for i, (c, olp) in enumerate(zip(chunks, old_lp)):
            lp, mask = token_logps(seqs[c], plen)
            ok &= finite(f"lp ep{ep} chunk {i}", lp)
            ok &= finite(f"old_lp at use ep{ep} chunk {i}", olp)
            print(f"    ep{ep} chunk {i}: max|lp-olp| {(lp - olp).abs().max().item():.3g}, max ratio {torch.exp(lp - olp).max().item():.3g}")
            ratio = torch.exp(lp - olp)
            a = adv[c].unsqueeze(1)
            surr = torch.min(ratio * a, torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a)
            part = -((surr * mask).sum(1) / mask.sum(1).clamp(min=1)).sum() / len(seqs)
            ok &= finite(f"loss ep{ep} chunk {i}", part.detach())
            part.backward()
            if os.environ.get("SYNC"):
                torch.mps.synchronize()
            nb = [n for n, q in model.named_parameters() if q.grad is not None and not torch.isfinite(q.grad).all()]
            print(f"    after backward chunk {i}: {len(nb)} non-finite gradients {nb[:2]}")
        badg = [n for n, p in model.named_parameters() if p.grad is not None and not torch.isfinite(p.grad).all()]
        if badg:
            print(f"  NON-FINITE gradients ep{ep}: {len(badg)} tensors, first {badg[:3]}"); ok = False
        top = sorted(((q.grad.norm().item(), n) for n, q in model.named_parameters() if q.grad is not None), reverse=True)[:5]
        print("  largest gradient norms:", [(n, f"{g:.3g}") for g, n in top])
        gn = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        print(f"  ep{ep} grad norm {gn.item():.3g}")
        opt.step()
        badw = [n for n, p in model.named_parameters() if not torch.isfinite(p).all()]
        if badw:
            print(f"  NON-FINITE weights after ep{ep}: {len(badw)} tensors, first {badw[:3]}"); ok = False
    if not ok:
        print("stop: first non-finite value found"); break
else:
    print("no non-finite value in", STEPS, "steps")
