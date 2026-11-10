"""Follows the NaN of nan_step.py inside the backward pass: which tensor first holds a non-finite gradient (logits,
final hidden states, the input of the final norm), on MPS, for the first chunk of step 1. No result is kept.
Usage, from sim/llm/: ../env-llm/bin/python diag/nan_where.py
"""
import os, sys
sys.argv = [sys.argv[0], "Qwen/Qwen2.5-0.5B-Instruct", "diag", "mul2", "random", "1", "1", "3e-6"]
exec(open(os.path.join(os.path.dirname(__file__), "..", "grpo.py")).read().split("if PILOT:")[0])
batch = rng.sample(TRAIN, B)
model.eval()
plen, seqs = generate([q for q, _ in batch], G, True)
model.train()
seen = {}
def keep(name):
    def hook(mod, inp, out):
        o = out[0] if isinstance(out, tuple) else out
        if not o.requires_grad:
            return
        seen[name + " out"] = o; o.retain_grad()
        if isinstance(inp, tuple) and inp and torch.is_tensor(inp[0]) and inp[0].requires_grad:
            seen[name + " in"] = inp[0]; inp[0].retain_grad()
    return hook
if not os.environ.get("NOHOOK"):
    model.model.norm.register_forward_hook(keep("final norm"))
if not os.environ.get("NOHOOK"):
    model.lm_head.register_forward_hook(keep("lm_head"))
if not os.environ.get("NOHOOK"):
    model.model.layers[-1].register_forward_hook(keep("last layer"))
right = [correct(tok.decode(s[plen:], skip_special_tokens=True), a) for s, a in zip(seqs, [a for _, a in batch for _ in range(G)])]
rewards = torch.tensor([float(rng.random() < 0.5) for _ in right], device=device)
groups = rewards.view(B, G)
adv = ((groups - groups.mean(1, keepdim=True)) / (groups.std(1, keepdim=True) + 1e-4)).view(-1)
fin = lambda x: "finite" if torch.isfinite(x).all() else f"NON-FINITE ({(~torch.isfinite(x)).sum().item()})"
for i in range(0, len(seqs), MICRO):
    c = slice(i, i + MICRO)
    with torch.no_grad():
        olp = token_logps(seqs[c], plen)[0]
    model.zero_grad() if os.environ.get("ZERO") else None
    lp, mask = token_logps(seqs[c], plen)
    ratio = torch.exp(lp - olp)
    a = adv[c].unsqueeze(1)
    surr = torch.min(ratio * a, torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a)
    part = -((surr * mask).sum(1) / mask.sum(1).clamp(min=1)).sum() / len(seqs)
    part.backward()
    eos = [(s[plen:] == tok.eos_token_id).any().item() for s in seqs[c]]
    print(f"chunk {i // MICRO}: max|lp-olp| {(lp - olp).abs().max().item():.3g}, finished {sum(eos)}/{MICRO}, mask sums {mask.sum(1).tolist()}")
    for k, v in seen.items():
        print(f"   {k:18s} grad {fin(v.grad) if v.grad is not None else 'none'}")
    print("   lm_head weight grad", fin(model.lm_head.weight.grad))
    bad = [n for n, q in model.named_parameters() if q.grad is not None and not torch.isfinite(q.grad).all()]
    print("   non-finite parameter gradients:", len(bad), bad[:4])
    if seen:
        gw = model.model.norm.weight.grad
        ref = (seen["final norm out"].grad * (seen["final norm out"] / model.model.norm.weight).detach()).sum((0, 1))
        print("   final norm weight grad", fin(gw), " recomputed by hand", fin(ref))
