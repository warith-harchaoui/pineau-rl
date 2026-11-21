"""Further analyses of the finished GRPO runs, from the logs on disk (LLM_PROTOCOL.md, deviation 19).

Scope: the nineteen finished runs of deviation 16 (five random seeds per configuration, four for Llama `random`). The
Llama CPU run of deviation 16 (e) is copied apart under "llama1_cpu" and enters no computation.
(a) Every measure (greedy, pass1, pass8, truncated, and finished = accuracy among finished answers): gain per seed
    (step 100 - step 0), mean, the percentile bootstrap of deviation 13 (10,000 draws, random.Random(0), one generator
    per measure and configuration), a Student interval (n - 1 df), the exact two-sided sign-flip test over the 2^n signs
    of the gains, and the number of positive gains. With five seeds the sign-flip p is at least 2/32 = 0.0625.
(b) True minus random gain, per model and measure: Welch interval (Welch-Satterthwaite df) and the exact two-sided
    permutation test over every split of the gains between the labels. Holm over the two pass1 contrasts (main
    family), then over the eight contrasts of greedy, pass1, pass8 and truncated (secondary family).
(c) Per run, change in the cut-off share against change in pass1 (Pearson, Spearman, per model). finished =
    pass1 / (1 - truncated): accuracy among finished answers if a cut-off answer is never right (deviation 5: 0 of 23).
(d) Diagnostics: zero gradient norms among the logged steps; step-0 spread of pass1 against the binomial standard
    error of 400 answers; step-0 equality of the true and random runs of the same seed.
Reading rule: established = Student interval excludes 0 AND Holm-adjusted exact p < 0.05 within its family.
Run from sim/llm/: python3 logs_stats.py  -> results/logs_stats_5.json
"""
import glob, itertools, json, math, random, statistics as st

from scipy import stats

from pineau_rl.stats import holm

SEEDS = range(5)
MODELS, REWARDS = ("qwen05", "llama1"), ("true", "random")
MEASURES = ("greedy", "pass1", "pass8", "truncated", "finished")
# Same table as summary.py (deviations 11, 14, 15 (e)): the device of every Qwen run; every Llama run used MPS.
DEVICE = {("qwen05", "true", 0): "mps", ("qwen05", "true", 1): "mps", ("qwen05", "random", 0): "mps",
          ("qwen05", "random", 1): "cpu", ("qwen05", "random", 2): "cpu", ("qwen05", "true", 2): "cpu",
          **{("qwen05", r, s): "cpu" for r in REWARDS for s in (3, 4)}}
N_SAMPLED = 400  # 50 test problems x 8 sampled answers per evaluation (deviation 2)


def finished(ev):
    """Accuracy among finished answers, if a cut-off answer is never right; None when every answer is cut off."""
    return ev["pass1"] / (1 - ev["truncated"]) if ev["truncated"] < 1 else None


def load(tag, reward, seed):
    f = f"results/{tag}/mul2/{reward}/seed{seed}.jsonl"
    try:
        rows = [json.loads(line) for line in open(f)]
    except FileNotFoundError:
        return None
    ev = [d for d in rows if "pass1" in d]
    if not ev or ev[-1]["step"] != 100:
        return None
    tr = [d for d in rows if "train_right" in d]
    norms = [d["grad_norm"] for d in tr if "grad_norm" in d]
    first, last = ev[0], ev[-1]
    run = dict(model=tag, reward=reward, seed=seed, device=DEVICE.get((tag, reward, seed), "cpu" if tag.endswith("_cpu") else "mps"),
               step0={k: first[k] for k in ("greedy", "pass1", "pass8", "truncated")},
               step100={k: last[k] for k in ("greedy", "pass1", "pass8", "truncated")},
               logged_norms=len(norms), zero_norms=sum(x == 0 for x in norms))
    run["step0"]["finished"], run["step100"]["finished"] = finished(first), finished(last)
    run["gain"] = {k: (run["step100"][k] - run["step0"][k]) if None not in (run["step0"][k], run["step100"][k]) else None
                   for k in MEASURES}
    return run


def boot(g, rng):
    b = sorted(sum(rng.choice(g) for _ in g) / len(g) for _ in range(10000))
    return [b[249], b[9749]]


def student(g):
    n, m = len(g), sum(g) / len(g)
    h = stats.t.ppf(0.975, n - 1) * st.stdev(g) / math.sqrt(n)
    return [m - h, m + h]


def sign_flip(g):
    obs, n = abs(sum(g)), 0
    for signs in itertools.product((1, -1), repeat=len(g)):
        n += abs(sum(s * x for s, x in zip(signs, g))) >= obs - 1e-12
    return n / 2 ** len(g)


def welch(a, b):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    d, h = st.mean(a) - st.mean(b), stats.t.ppf(0.975, df) * math.sqrt(va + vb)
    return d, [d - h, d + h], df


def permutation(a, b):
    pool, obs, hits, total = a + b, abs(st.mean(a) - st.mean(b)), 0, 0
    for idx in itertools.combinations(range(len(pool)), len(a)):
        x = [pool[i] for i in idx]
        y = [pool[i] for i in range(len(pool)) if i not in idx]
        hits += abs(st.mean(x) - st.mean(y)) >= obs - 1e-12
        total += 1
    return hits / total, total


runs = [r for m in MODELS for w in REWARDS for s in SEEDS if (r := load(m, w, s))]
cpu_run = load("llama1_cpu", "random", 4)
out = dict(runs=runs, llama1_cpu=cpu_run, gains={}, contrasts={}, length={}, diagnostics={})

# (a) every measure, per configuration
for m in MODELS:
    for w in REWARDS:
        conf = sorted((r for r in runs if (r["model"], r["reward"]) == (m, w)), key=lambda r: r["seed"])
        for k in MEASURES:
            g = [r["gain"][k] for r in conf if r["gain"][k] is not None]
            out["gains"][f"{m} {w} {k}"] = dict(seeds=[r["seed"] for r in conf if r["gain"][k] is not None], gains=g,
                                               mean=sum(g) / len(g), ci_boot=boot(g, random.Random(0)), ci_t=student(g),
                                               p_sign=sign_flip(g), positive=sum(x > 0 for x in g),
                                               start=st.mean(r["step0"][k] for r in conf if r["step0"][k] is not None),
                                               end=st.mean(r["step100"][k] for r in conf if r["step100"][k] is not None))
# Holm over the four within-configuration gains of each measure
for k in MEASURES:
    keys = [f"{m} {w} {k}" for m in MODELS for w in REWARDS]
    for key, p in zip(keys, holm([out["gains"][key]["p_sign"] for key in keys])):
        x = out["gains"][key]
        x["p_sign_holm"] = p
        x["established"] = bool((x["ci_t"][0] > 0 or x["ci_t"][1] < 0) and p < 0.05)

# (b) true minus random, per model and measure
for m in MODELS:
    for k in MEASURES:
        a, b = out["gains"][f"{m} true {k}"]["gains"], out["gains"][f"{m} random {k}"]["gains"]
        d, ci, df = welch(a, b)
        p, n = permutation(a, b)
        out["contrasts"][f"{m} {k}"] = dict(diff=d, ci_welch=ci, df=df, p_perm=p, splits=n, n_true=len(a), n_random=len(b))
for family, ks in (("main", ("pass1",)), ("secondary", ("greedy", "pass1", "pass8", "truncated")), ("finished", ("finished",))):
    keys = [f"{m} {k}" for k in ks for m in MODELS]
    for key, p in zip(keys, holm([out["contrasts"][key]["p_perm"] for key in keys])):
        x = out["contrasts"][key]
        x[f"p_holm_{family}"] = p
        if family != "secondary":
            x["established"] = bool((x["ci_welch"][0] > 0 or x["ci_welch"][1] < 0) and p < 0.05)

# (c) length against correctness: change in cut-off share against change in pass1, per model and per configuration
for m in MODELS:
    for w in (None,) + REWARDS:
        conf = [r for r in runs if r["model"] == m and w in (None, r["reward"])]
        dt, dp = [r["gain"]["truncated"] for r in conf], [r["gain"]["pass1"] for r in conf]
        out["length"][f"{m} {w or 'both'}"] = dict(n=len(conf), d_truncated=dt, d_pass1=dp,
                                                   pearson=stats.pearsonr(dt, dp)[0], spearman=stats.spearmanr(dt, dp)[0])

# (d) diagnostics
for m in MODELS:
    p0 = [r["step0"]["pass1"] for r in runs if r["model"] == m]
    p = st.mean(p0)
    pairs = {}
    for s in SEEDS:
        t = next((r for r in runs if (r["model"], r["reward"], r["seed"]) == (m, "true", s)), None)
        q = next((r for r in runs if (r["model"], r["reward"], r["seed"]) == (m, "random", s)), None)
        if t and q:
            pairs[s] = dict(identical=t["step0"] == q["step0"], devices=[t["device"], q["device"]],
                            greedy=[t["step0"]["greedy"], q["step0"]["greedy"]])
    out["diagnostics"][m] = dict(step0_pass1_sd=st.stdev(p0), binomial_se=math.sqrt(p * (1 - p) / N_SAMPLED),
                                 step0_greedy=sorted({r["step0"]["greedy"] for r in runs if r["model"] == m}),
                                 same_seed_pairs=pairs,
                                 zero_norms={f"{r['reward']} {r['seed']}": [r["zero_norms"], r["logged_norms"]]
                                             for r in runs if r["model"] == m})
json.dump(out, open("results/logs_stats_5.json", "w"), indent=1)

for key, x in out["gains"].items():
    print(f"{key:24s} mean {x['mean']:+.3f}  boot [{x['ci_boot'][0]:+.3f}, {x['ci_boot'][1]:+.3f}]  t [{x['ci_t'][0]:+.3f}, "
          f"{x['ci_t'][1]:+.3f}]  sign p {x['p_sign']:.3f}  >0 {x['positive']}/{len(x['gains'])}")
for key, x in out["contrasts"].items():
    print(f"true - random {key:16s} {x['diff']:+.3f}  Welch [{x['ci_welch'][0]:+.3f}, {x['ci_welch'][1]:+.3f}]  "
          f"perm p {x['p_perm']:.4f}  Holm(main/sec) {x.get('p_holm_main', x.get('p_holm_finished', float('nan'))):.4f}"
          f" / {x.get('p_holm_secondary', float('nan')):.4f}")
for key, x in out["length"].items():
    print(f"length {key:16s} n={x['n']}  Pearson {x['pearson']:+.2f}  Spearman {x['spearman']:+.2f}")
print(json.dumps(out["diagnostics"], indent=1))
