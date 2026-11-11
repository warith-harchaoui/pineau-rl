"""Summary of the finished GRPO runs: first-attempt success (pass1) and share of cut-off answers at steps 0 and 100,
per model, reward and random seed, with the device each run used (LLM_PROTOCOL.md, deviations 10 to 12).
Run from sim/llm/: python3 summary.py  -> results/summary.json
"""
import glob, json, os

DEVICE = {("qwen05", "true", 0): "mps", ("qwen05", "true", 1): "mps", ("qwen05", "random", 0): "mps",
          ("qwen05", "random", 1): "cpu", ("qwen05", "random", 2): "cpu", ("qwen05", "true", 2): "cpu"}  # deviation 11
out = []
for f in sorted(glob.glob("results/*/mul2/*/seed*.jsonl")):
    model, _, reward, s = f.split("/")[1:]
    seed = int(s[4:-6])
    ev = [json.loads(l) for l in open(f) if '"pass1"' in l]
    if not ev or ev[-1]["step"] != 100:
        continue
    out.append(dict(model=model, reward=reward, seed=seed, device=DEVICE.get((model, reward, seed), "mps"),
                    pass1_0=ev[0]["pass1"], pass1_100=ev[-1]["pass1"], truncated_100=ev[-1].get("truncated")))
    print(out[-1])
json.dump(out, open("results/summary.json", "w"), indent=1)
