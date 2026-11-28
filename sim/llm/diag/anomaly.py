"""Which backward operation first returns NaN on MPS? A short forward and backward with anomaly detection."""
import os, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
M, R = "Qwen/Qwen2.5-0.5B-Instruct", "7ae557604adf67be50417f59c2c2f167def9a775"
dev = os.environ.get("DEVICE", "mps")
tok = AutoTokenizer.from_pretrained(M, revision=R)
m = AutoModelForCausalLM.from_pretrained(M, revision=R, dtype=torch.float32).to(dev); m.train()
ids = tok(["What is 23 * 47? Think step by step."] * 2, return_tensors="pt").input_ids.to(dev)
tests = {
    "sum of logits": lambda lg: lg.sum() * 1e-6,
    "log_softmax.gather": lambda lg: torch.log_softmax(lg, -1).gather(2, ids[:, 1:].unsqueeze(-1)).sum(),
}
for name, f in tests.items():
    m.zero_grad()
    lg = m(input_ids=ids).logits[:, :-1]
    loss = f(lg)
    loss.backward()
    bad = [n for n, p in m.named_parameters() if p.grad is not None and not torch.isfinite(p.grad).all()]
    print(name, "loss", float(loss), "non-finite grads:", len(bad), bad[:2], flush=True)
# a pure tensor test, no model: is MPS backward itself broken?
x = torch.randn(64, 64, device=dev, requires_grad=True)
(x @ x).sum().backward()
print("matmul backward finite:", bool(torch.isfinite(x.grad).all()))
w = torch.randn(1000, 64, device=dev, requires_grad=True)
torch.nn.functional.embedding(torch.tensor([1, 2, 3], device=dev), w).sum().backward()
print("embedding backward finite:", bool(torch.isfinite(w.grad).all()))
