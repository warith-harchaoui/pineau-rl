"""Inference only: base model on the exact step-10 batch of the killed pilot (seed 9), same sampling as grpo.py; saves every completion."""
import json, re, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
M = "Qwen/Qwen2.5-0.5B-Instruct"
batch = [(48, 49), (14, 36), (21, 50), (45, 17)]
INSTR = " Think step by step, then finish with the final answer as an integer."
tok = AutoTokenizer.from_pretrained(M); tok.pad_token = tok.pad_token or tok.eos_token; tok.padding_side = "left"
model = AutoModelForCausalLM.from_pretrained(M, torch_dtype=torch.float32).to("mps").eval()
def correct(text, ans):
    nums = re.findall(r"-?\d[\d,]*", text)
    return bool(nums) and nums[-1].replace(",", "").lstrip("-").isdigit() and int(nums[-1].replace(",", "")) == ans
torch.manual_seed(9)
qs = [f"What is {a} * {b}?" for a, b in batch]
enc = tok([tok.apply_chat_template([{"role": "user", "content": q + INSTR}], tokenize=False, add_generation_prompt=True) for q in qs], return_tensors="pt", padding=True).to("mps")
with torch.no_grad():
    out = model.generate(**enc, max_new_tokens=160, do_sample=True, temperature=1.0, top_p=None, top_k=None, num_return_sequences=8, pad_token_id=tok.pad_token_id)
plen = enc["input_ids"].shape[1]
rows = []
for i, s in enumerate(out):
    a, b = batch[i // 8]; text = tok.decode(s[plen:], skip_special_tokens=True)
    rows.append(dict(q=f"{a}*{b}", ans=a * b, right=correct(text, a * b), last=(re.findall(r"-?\d[\d,]*", text) or [None])[-1], text=text))
json.dump(rows, open("diag/replay_batch.json", "w"), indent=1)
print("train_right on this batch (base model):", sum(r["right"] for r in rows) / len(rows))
for r in rows[:3]: print(r["q"], r["ans"], r["right"], repr(r["text"][-120:]))
