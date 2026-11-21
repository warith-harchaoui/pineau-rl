"""Analysis of the GRPO rerun (LLM_PROTOCOL.md, deviation 20), fixed BEFORE any of its runs.

Reads results/{qwen05_c7,llama1_c7}/mul2/{true,random}/seed{0..9}.jsonl and their .items.jsonl.gz (grpo.py --c7).
Gain = measure at step 100 - measure at step 0, per run.
Main: true minus random gain in pass1 (300 test problems x 8 samples, 160 tokens), per model: Welch interval
  (Welch-Satterthwaite df) and the exact two-sided permutation test over every split of the gains between the labels;
  Holm over the two models.
Co-primary: the same for greedy512 (greedy answer with 512 tokens: length-independent) and pass8; Holm over the six.
Within a configuration: Student interval and the exact sign-flip test (2^n signs), Holm over the four configurations.
Item uncertainty: a seeds x problems bootstrap of the main and co-primary contrasts (2,000 draws, numpy
  default_rng(0)): seeds resampled within each arm, the same resampled problems in both arms.
Also: accuracy among finished answers (finished), cut-off share, cut-off answers that are right (deviation 5),
  groups with zero advantage, step-0 equality of the true and random runs of a seed (device determinism).
Established = interval excludes 0 AND Holm-adjusted exact p < 0.05. A run that failed twice is listed, not filled.
Run from sim/llm/: python3 c7_stats.py  -> results/c7_stats.json
"""
import gzip, itertools, json, math, os, statistics as st

import numpy as np
from scipy import stats

from pineau_rl.stats import holm

TAGS, REWARDS, SEEDS = ("qwen05_c7", "llama1_c7"), ("true", "random"), range(10)
MAIN, CO = ("pass1",), ("pass1", "greedy512", "pass8")
MEASURES = ("pass1", "greedy512", "pass8", "greedy", "truncated", "finished")


def item_scores(items):
    """Per-problem pass1, greedy512 and pass8 (problem order of the test set)."""
    return dict(pass1=[sum(r["ok"] for r in it["samples"]) / len(it["samples"]) for it in items],
                greedy512=[float(it["greedy512"]["ok"]) for it in items],
                pass8=[float(any(r["ok"] for r in it["samples"])) for it in items])


def load(tag, reward, seed):
    path = f"results/{tag}/mul2/{reward}/seed{seed}.jsonl"
    if not os.path.exists(path):
        return None
    rows = [json.loads(line) for line in open(path)]
    ev = {d["step"]: d for d in rows if "pass1" in d}
    if 100 not in ev:
        return None
    head = rows[0]
    with gzip.open(path.replace(".jsonl", ".items.jsonl.gz"), "rt") as f:
        items = {d["step"]: item_scores(d["items"]) for d in map(json.loads, f)}
    tr = [d for d in rows if "train_right" in d]
    return dict(tag=tag, reward=reward, seed=seed, device=head.get("device"),
                step0={k: ev[0][k] for k in MEASURES}, step100={k: ev[100][k] for k in MEASURES},
                gain={k: None if None in (ev[0][k], ev[100][k]) else ev[100][k] - ev[0][k] for k in MEASURES},
                cut_right=[ev[0]["cut_right"], ev[100]["cut_right"]],
                zero_adv_share=sum(d["zero_adv_groups"] for d in tr) / (4 * len(tr)),
                zero_norm_steps=sum(any(n == 0 for n in d["grad_norms"]) for d in tr), steps=len(tr),
                retries=tr[-1]["retries"], items0=items[0], items100=items[100])


def student(g):
    m, h = st.mean(g), stats.t.ppf(0.975, len(g) - 1) * st.stdev(g) / math.sqrt(len(g))
    return [m - h, m + h]


def sign_flip(g):
    obs = abs(sum(g))
    return sum(abs(sum(s * x for s, x in zip(signs, g))) >= obs - 1e-12
               for signs in itertools.product((1, -1), repeat=len(g))) / 2 ** len(g)


def welch(a, b):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    d, h = st.mean(a) - st.mean(b), stats.t.ppf(0.975, df) * math.sqrt(va + vb)
    return d, [d - h, d + h], df


def permutation(a, b):
    pool, total, n = np.array(a + b), sum(a) + sum(b), len(a)
    obs, hits, count = abs(st.mean(a) - st.mean(b)), 0, 0
    for idx in itertools.combinations(range(len(pool)), n):
        sa = pool[list(idx)].sum()
        hits += abs(sa / n - (total - sa) / (len(pool) - n)) >= obs - 1e-12
        count += 1
    return hits / count, count


def two_level(ta, tb, k, rng, reps=2000):
    """Seeds x problems bootstrap of the true - random gain in measure k: 95% percentile interval."""
    ga = np.array([np.array(r["items100"][k]) - np.array(r["items0"][k]) for r in ta])  # runs x problems
    gb = np.array([np.array(r["items100"][k]) - np.array(r["items0"][k]) for r in tb])
    n_items, out = ga.shape[1], []
    for _ in range(reps):
        items = rng.integers(0, n_items, n_items)
        sa, sb = rng.integers(0, len(ga), len(ga)), rng.integers(0, len(gb), len(gb))
        out.append(ga[np.ix_(sa, items)].mean() - gb[np.ix_(sb, items)].mean())
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


runs = {(t, w, s): r for t in TAGS for w in REWARDS for s in SEEDS if (r := load(t, w, s))}
fails = [line.split()[1:] for line in open("logs/c7.fails")] if os.path.exists("logs/c7.fails") else []
out = dict(n_runs=len(runs), fails=fails, gains={}, contrasts={}, diagnostics={})
for t in TAGS:
    for w in REWARDS:
        conf = [runs[(t, w, s)] for s in SEEDS if (t, w, s) in runs]
        for k in MEASURES:
            g = [r["gain"][k] for r in conf if r["gain"][k] is not None]
            if len(g) >= 2:
                out["gains"][f"{t} {w} {k}"] = dict(seeds=[r["seed"] for r in conf if r["gain"][k] is not None], gains=g,
                                                   mean=st.mean(g), ci_t=student(g), p_sign=sign_flip(g),
                                                   positive=sum(x > 0 for x in g))
for k in MEASURES:
    keys = [key for key in (f"{t} {w} {k}" for t in TAGS for w in REWARDS) if key in out["gains"]]
    for key, p in zip(keys, holm([out["gains"][key]["p_sign"] for key in keys])):
        x = out["gains"][key]
        x["p_sign_holm"], x["established"] = p, bool((x["ci_t"][0] > 0 or x["ci_t"][1] < 0) and p < 0.05)
rng = np.random.default_rng(0)
for t in TAGS:
    for k in MEASURES:
        if f"{t} true {k}" not in out["gains"] or f"{t} random {k}" not in out["gains"]:
            continue
        a, b = out["gains"][f"{t} true {k}"]["gains"], out["gains"][f"{t} random {k}"]["gains"]
        d, ci, df = welch(a, b)
        p, n = permutation(a, b)
        x = dict(diff=d, ci_welch=ci, df=df, p_perm=p, splits=n, n_true=len(a), n_random=len(b))
        if k in CO:
            x["ci_seeds_items"] = two_level([r for r in runs.values() if (r["tag"], r["reward"]) == (t, "true")],
                                            [r for r in runs.values() if (r["tag"], r["reward"]) == (t, "random")], k, rng)
        out["contrasts"][f"{t} {k}"] = x
for family, ks in (("main", MAIN), ("co", CO)):
    keys = [key for key in (f"{t} {k}" for k in ks for t in TAGS) if key in out["contrasts"]]
    for key, p in zip(keys, holm([out["contrasts"][key]["p_perm"] for key in keys])):
        x = out["contrasts"][key]
        x[f"p_holm_{family}"] = p
        x[f"established_{family}"] = bool((x["ci_welch"][0] > 0 or x["ci_welch"][1] < 0) and p < 0.05)
for t in TAGS:
    pairs = {s: runs[(t, "true", s)]["step0"] == runs[(t, "random", s)]["step0"]
             for s in SEEDS if (t, "true", s) in runs and (t, "random", s) in runs}
    rs = [r for r in runs.values() if r["tag"] == t]
    out["diagnostics"][t] = dict(same_seed_step0_identical=pairs, devices=sorted({r["device"] for r in rs}),
                                 cut_right=sum(sum(r["cut_right"]) for r in rs),
                                 zero_adv_share={f"{r['reward']} {r['seed']}": r["zero_adv_share"] for r in rs},
                                 zero_norm_steps={f"{r['reward']} {r['seed']}": r["zero_norm_steps"] for r in rs})
json.dump(out, open("results/c7_stats.json", "w"), indent=1)
for key, x in out["contrasts"].items():
    print(f"true - random {key:22s} {x['diff']:+.3f}  Welch [{x['ci_welch'][0]:+.3f}, {x['ci_welch'][1]:+.3f}]  perm p {x['p_perm']:.4f}")
