"""Summary of the finished GRPO runs: first-attempt success (pass1) and share of cut-off answers at steps 0 and 100,
per model, reward and random seed, with the device each run used (LLM_PROTOCOL.md, deviations 10 to 12).
Then the preregistered statistic (LLM_PROTOCOL.md, Statistics): gain = pass1 at step 100 - pass1 at step 0, per random
seed; mean and 95% percentile bootstrap interval over the seeds (10,000 draws, random.Random(0)). With three seeds the
bootstrap has only ten distinct resamples: the interval is reported, and read as very rough.
Run from sim/llm/: python3 summary.py  -> results/summary.json, results/gains.json
"""
import glob, json, os, random

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

gains, rng = {}, random.Random(0)
for model in sorted({r["model"] for r in out}):
    for reward in ("true", "random"):
        g = [r["pass1_100"] - r["pass1_0"] for r in sorted(out, key=lambda r: r["seed"]) if (r["model"], r["reward"]) == (model, reward)]
        boot = sorted(sum(rng.choice(g) for _ in g) / len(g) for _ in range(10000))
        gains[f"{model} {reward}"] = dict(gains=g, mean=sum(g) / len(g), ci=[boot[249], boot[9749]])
        print(f"{model} {reward}: gains {', '.join(f'{x:+.3f}' for x in g)}  mean {sum(g) / len(g):+.3f}  95% CI [{boot[249]:+.3f}, {boot[9749]:+.3f}]")
json.dump(gains, open("results/gains.json", "w"), indent=1)
