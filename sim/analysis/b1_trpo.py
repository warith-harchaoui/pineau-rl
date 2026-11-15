"""Experiment B1 (SIM_PROTOCOL.md, Écart 4, written before any TRPO run): Henderson et al.'s statistic with
their algorithm. Same draws as e1_curve.py, on 30 TRPO runs and, for comparison, on the 30 PPO runs of E1.

Three readings of "the average 2-sample t-test across entire training distribution" (their figure 5):
  - mean_t: Welch t at each of the 20 evaluation points, averaged, turned into a p with the mean df;
  - mean_p: the 20 Welch p-values, averaged;
  - pooled: the 5 runs x 20 points of each group stacked as 100 independent observations, one Welch test.
Each reading: share of draws with p < 0.05, 95th percentile of |t|, share of draws with |t| >= 9.09, for
groups drawn at random and for groups sorted by final score.
Run from sim/: env-an/bin/python analysis/b1_trpo.py  -> analysis/b1_trpo.json
"""
import json
import numpy as np
from pineau_rl.runs import read_run, run_path
from pineau_rl.stats import welch_curve, welch_pooled

HENDERSON_T = 9.0916  # |t| of their figure 5 (arXiv 1709.06560v3)


def curves(algo):
    runs = [read_run(run_path("results", algo, "HalfCheetah-v5", s)) for s in range(30)]  # explicit seeds 0 to 29
    C = np.array([[float(r["eval_mean"]) for r in rows] for rows in runs])
    assert C.shape == (30, 20), (algo, C.shape)
    return C


def readings(a, b):
    w = welch_curve(a, b)
    return dict(mean_t=(w["mean_t"], w["p_mean_t"]), mean_p=(w["mean_t"], w["mean_p"]), pooled=welch_pooled(a, b))


def run(C, sort, rng, N=10000):
    out = {k: ([], []) for k in ("mean_t", "mean_p", "pooled")}
    for _ in range(N):
        idx = rng.choice(30, 10, replace=False)
        idx = idx[np.argsort(C[idx, -1])] if sort else rng.permutation(idx)
        for k, (tv, pv) in readings(C[idx[5:]], C[idx[:5]]).items():
            out[k][0].append(abs(tv)); out[k][1].append(pv)
    return {k: dict(false_positive=float((np.array(p) < .05).mean()),
                    abs_t_p95=float(np.percentile(t, 95)),
                    share_abs_t_ge_henderson=float((np.array(t) >= HENDERSON_T).mean()))
            for k, (t, p) in out.items()}


res = {}
for algo in ("ppo_sb3", "trpo"):
    C = curves(algo)
    rng = np.random.default_rng(2018)
    res[algo] = dict(final_mean=float(C[:, -1].mean()), final_sd=float(C[:, -1].std(ddof=1)),
                     cv=float(C[:, -1].std(ddof=1) / C[:, -1].mean()),
                     random_5v5=run(C, False, rng), sorted_5v5=run(C, True, rng))
json.dump(res, open("analysis/b1_trpo.json", "w"), indent=1)
print(json.dumps(res, indent=1))
