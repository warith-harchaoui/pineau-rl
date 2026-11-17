"""Summary of the finished GRPO runs: first-attempt success (pass1) and share of cut-off answers at steps 0 and 100,
per model, reward and random seed, with the device each run used (LLM_PROTOCOL.md, deviations 10 to 12).
Then the preregistered statistic (LLM_PROTOCOL.md, Statistics): gain = pass1 at step 100 - pass1 at step 0, per random
seed; mean and 95% percentile bootstrap interval over the seeds (10,000 draws, random.Random(0)). With three seeds the
bootstrap has only ten distinct resamples: the interval is reported, and read as very rough.
Deviation 16: a run that failed twice is declared in FAILED and the configuration is summarized over its finished runs;
results/extra{SUFFIX}.json adds the sensitivity to the missing gain (replaced by the smallest, then the largest gain of
the finished runs) and Qwen's gains over its CPU runs alone (deviation 15 (e)). Each part draws from its own
random.Random(0), so summary.json and gains.json are unchanged.
Run from sim/llm/: python3 summary.py  -> results/summary.json, results/gains.json, results/extra.json
"""
import glob, json, os, random

SEEDS = range(*map(int, os.environ.get("SEEDS", "0:3").split(":")))  # deviation 14: SEEDS=0:5
SUFFIX = os.environ.get("SUFFIX", "")  # results/summary{SUFFIX}.json, results/gains{SUFFIX}.json

DEVICE = {("qwen05", "true", 0): "mps", ("qwen05", "true", 1): "mps", ("qwen05", "random", 0): "mps",
          ("qwen05", "random", 1): "cpu", ("qwen05", "random", 2): "cpu", ("qwen05", "true", 2): "cpu",  # deviation 11
          **{("qwen05", r, s): "cpu" for r in ("true", "random") for s in (3, 4)}}  # deviation 14
FAILED = {("llama1", "random", 4)}  # deviation 16: stopped on two nights by the safeguard of deviation 10
out = []
for f in sorted(glob.glob("results/*/mul2/*/seed*.jsonl")):
    model, _, reward, s = f.split("/")[1:]
    seed = int(s[4:-6])
    if model not in ("qwen05", "llama1") or seed not in SEEDS:
        continue
    ev = [json.loads(l) for l in open(f) if '"pass1"' in l]
    if not ev or ev[-1]["step"] != 100:
        continue
    out.append(dict(model=model, reward=reward, seed=seed, device=DEVICE.get((model, reward, seed), "mps"),
                    pass1_0=ev[0]["pass1"], pass1_100=ev[-1]["pass1"], truncated_100=ev[-1].get("truncated")))
    print(out[-1])
for conf in sorted({(r["model"], r["reward"]) for r in out}):  # every configuration has every seed, or nothing is written
    n = sum((r["model"], r["reward"]) == conf for r in out)
    failed = sum(conf + (s,) in FAILED for s in SEEDS)
    assert n + failed == len(SEEDS), f"{conf}: {n} finished runs and {failed} declared failures out of {len(SEEDS)}"
json.dump(out, open(f"results/summary{SUFFIX}.json", "w"), indent=1)

gains, rng = {}, random.Random(0)
for model in sorted({r["model"] for r in out}):
    for reward in ("true", "random"):
        g = [r["pass1_100"] - r["pass1_0"] for r in sorted(out, key=lambda r: r["seed"]) if (r["model"], r["reward"]) == (model, reward)]
        boot = sorted(sum(rng.choice(g) for _ in g) / len(g) for _ in range(10000))
        gains[f"{model} {reward}"] = dict(gains=g, mean=sum(g) / len(g), ci=[boot[249], boot[9749]])
        print(f"{model} {reward}: gains {', '.join(f'{x:+.3f}' for x in g)}  mean {sum(g) / len(g):+.3f}  95% CI [{boot[249]:+.3f}, {boot[9749]:+.3f}]")
json.dump(gains, open(f"results/gains{SUFFIX}.json", "w"), indent=1)


def interval(g, rng):
    boot = sorted(sum(rng.choice(g) for _ in g) / len(g) for _ in range(10000))
    return dict(gains=g, mean=sum(g) / len(g), ci=[boot[249], boot[9749]])


extra = dict(failed=[dict(model=m, reward=r, seed=s) for m, r, s in sorted(FAILED) if s in SEEDS], missing=[], cpu={})
gain = {(r["model"], r["reward"], r["seed"]): r["pass1_100"] - r["pass1_0"] for r in out}
for m, r, s in sorted(FAILED):  # (c) the missing gain replaced by the smallest, then the largest gain of the finished runs
    if s not in SEEDS:
        continue
    g = [gain[(m, r, t)] for t in SEEDS if (m, r, t) in gain]
    for name, fill in (("smallest", min(gain.values())), ("largest", max(gain.values()))):
        x = dict(model=m, reward=r, seed=s, filled_with=name, value=fill, **interval(g + [fill], random.Random(0)))
        extra["missing"].append(x)
        print(f"{m} {r}, seed {s} filled with the {name} gain {fill:+.3f}: mean {x['mean']:+.3f}  "
              f"95% CI [{x['ci'][0]:+.3f}, {x['ci'][1]:+.3f}]")
rng = random.Random(0)
for reward in ("true", "random"):  # (d) Qwen on CPU alone
    rows = sorted((r for r in out if (r["model"], r["reward"], r["device"]) == ("qwen05", reward, "cpu")), key=lambda r: r["seed"])
    if rows:
        x = dict(seeds=[r["seed"] for r in rows], **interval([r["pass1_100"] - r["pass1_0"] for r in rows], rng))
        extra["cpu"][f"qwen05 {reward}"] = x
        print(f"qwen05 {reward}, CPU runs only (seeds {x['seeds']}): mean {x['mean']:+.3f}  "
              f"95% CI [{x['ci'][0]:+.3f}, {x['ci'][1]:+.3f}]")
json.dump(extra, open(f"results/extra{SUFFIX}.json", "w"), indent=1)
