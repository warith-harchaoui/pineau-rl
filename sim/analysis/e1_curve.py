"""E1, second statistic: the test Henderson et al. 2018 actually report (figure 5 of arXiv 1709.06560v3).

Their caption reads "the average 2-sample t-test across entire training distribution": a Welch test at
every evaluation point of the learning curve, then averaged. e1.py tests final scores only, so it does not
measure the same thing. Here, on the same 30 runs, every draw takes 10 runs, splits them into two groups
of 5 (at random, or sorted by final score), runs a Welch test at each of the 20 evaluation points
(50k to 1M steps), and summarises the curve in the two readings the caption allows:
  - mean_t: the t statistics averaged over the curve, turned into a p with the mean Welch degrees of freedom;
  - mean_p: the p-values averaged over the curve.
Added on 9 November 2026 after e1.py's results were known (SIM_PROTOCOL.md, Écarts).
Run from sim/: env-an/bin/python analysis/e1_curve.py  -> analysis/e1_curve.json
"""
import csv, glob, json
import numpy as np
from scipy import stats

files = sorted(glob.glob("results/ppo_sb3/HalfCheetah-v5/seed*.csv"))
C = np.array([[float(r["eval_mean"]) for r in csv.DictReader(open(f))] for f in files])  # 30 x 20
assert C.shape == (30, 20), C.shape
rng = np.random.default_rng(2018)


def curve_test(a, b):
    t = stats.ttest_ind(a, b, axis=0, equal_var=False)
    va, vb = a.var(axis=0, ddof=1) / len(a), b.var(axis=0, ddof=1) / len(b)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    mean_t = t.statistic.mean()
    return dict(mean_t=mean_t, p_mean_t=2 * stats.t.sf(abs(mean_t), df.mean()), mean_p=t.pvalue.mean(),
                final_p=t.pvalue[-1])


def run(sort, N=10000):
    out = {k: [] for k in ("mean_t", "p_mean_t", "mean_p", "final_p")}
    for _ in range(N):
        idx = rng.choice(30, 10, replace=False)
        if sort:
            idx = idx[np.argsort(C[idx, -1])]  # sorted by final score: 5 worst, then 5 best
        else:
            idx = rng.permutation(idx)
        r = curve_test(C[idx[5:]], C[idx[:5]])
        for k in out:
            out[k].append(r[k])
    o = {k: np.array(v) for k, v in out.items()}
    return dict(fp_mean_t=float((o["p_mean_t"] < .05).mean()), fp_mean_p=float((o["mean_p"] < .05).mean()),
                fp_final=float((o["final_p"] < .05).mean()),
                abs_mean_t_p95=float(np.percentile(np.abs(o["mean_t"]), 95)),
                share_abs_mean_t_ge_9=float((np.abs(o["mean_t"]) >= 9.09).mean()),
                share_mean_p_le_0016=float((o["mean_p"] <= .0016).mean()))


res = dict(random_5v5=run(False), sorted_5v5=run(True))
json.dump(res, open("analysis/e1_curve.json", "w"), indent=1)
print(json.dumps(res, indent=1))
