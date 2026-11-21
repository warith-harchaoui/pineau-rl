"""Calibrating the "settled" rule on true null hypotheses (SIM_PROTOCOL.md, deviation 26, written before this computation).
Two disjoint groups of the SAME program, where no difference exists. On the 30 runs of PPO-SB3 (E1) and of TRPO (B1) on
HalfCheetah: 2,000 draws of two disjoint groups of 10, then of 5; on each, the percentile bootstrap interval of the
probability of improvement and the intervals of the two interquartile means (2,000 resamples, each group resampled
separately with replacement: rliable's stratified bootstrap for one task, written in NumPy for speed; default_rng(2026)).
Shares of draws where the probability interval excludes 0.5, where the IQM intervals are disjoint, where either holds
(the protocol's rule). The same at 5 against 5 on the sixteen pairs of E2 (seeds 0 to 19).
Run from sim/: env-an/bin/python analysis/rule_calibration.py  -> analysis/rule_calibration.json
"""
import json, sys
import numpy as np
from scipy import stats
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, TASKS
from pineau_rl.runs import finals

rng = np.random.default_rng(2026)
B = 2000


def poi(X, Y):  # rows: resamples; P(X > Y) + P(X = Y) / 2, as rliable
    return (X[:, :, None] > Y[:, None, :]).mean((1, 2)) + .5 * (X[:, :, None] == Y[:, None, :]).mean((1, 2))


def iqm_ci(x):
    xs = x[rng.integers(0, len(x), (B, len(x)))]
    return np.percentile(stats.trim_mean(xs, .25, axis=1), [2.5, 97.5])


def calibrate(F, k, draws=2000):
    n_poi = n_iqm = n_either = 0
    for _ in range(draws):
        i = rng.permutation(len(F))
        a, b = F[i[:k]], F[i[k:2 * k]]
        lo, hi = np.percentile(poi(a[rng.integers(0, k, (B, k))], b[rng.integers(0, k, (B, k))]), [2.5, 97.5])
        sp = not (lo <= .5 <= hi)
        (l1, h1), (l2, h2) = iqm_ci(a), iqm_ci(b)
        si = h1 < l2 or h2 < l1
        n_poi += sp; n_iqm += si; n_either += sp or si
    return dict(k=k, draws=draws, poi_excludes_half=n_poi / draws, iqm_disjoint=n_iqm / draws, either=n_either / draws)


res = dict(halfcheetah_30_runs={}, grid_5v5={})
for algo in ("ppo_sb3", "trpo"):
    F = finals(ROOT, algo, "HalfCheetah-v5", range(30), 1_000_000, strict=True)
    res["halfcheetah_30_runs"][algo] = {f"{k}v{k}": calibrate(F, k) for k in (10, 5)}
    print(algo, res["halfcheetah_30_runs"][algo])
for task in TASKS:
    for algo in ALGOS:
        F = finals(ROOT, algo, task, range(20), FINAL[algo], strict=True)
        res["grid_5v5"][f"{algo}/{task}"] = c = calibrate(F, 5)
        print(algo, task, c)
g = np.array([c["either"] for c in res["grid_5v5"].values()])
res["grid_5v5_summary"] = dict(median=float(np.median(g)), min=float(g.min()), max=float(g.max()))
print(res["grid_5v5_summary"])
json.dump(res, open("analysis/rule_calibration.json", "w"), indent=1)
