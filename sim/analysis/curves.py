"""Learning-curve analyses (SIM_PROTOCOL.md, deviation 29, written before these computations; exploratory).
At ten and twenty seeds: (i) ranking of the four programs by IQM at 50,000 to 200,000 steps and Kendall's tau with the
final ranking (each program at its budget); per pair (program, task), Spearman correlation between a seed's score at a
step and its final score; (ii) final against best point of the curve: share of runs whose final score is below their
best, median relative gap (best - final) / |best|, IQM inflation when the best point is reported; (iii) lag-1
autocorrelation of each curve's deviations from the mean curve (30 curves of PPO-SB3 and of TRPO on HalfCheetah), and
the effective number of independent points of a 20-point curve, 20 (1 - r) / (1 + r).
Run from sim/: env-an/bin/python analysis/curves.py  -> analysis/curves.json
"""
import json, sys
import numpy as np
from scipy import stats
from pineau_rl.bootstrap import iqm
from pineau_rl.runs import read_run, run_path
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, TASKS

STEPS = (50_000, 100_000, 150_000, 200_000)


def curve(algo, task, s):
    r = read_run(run_path(ROOT, algo, task, s), FINAL.get(algo, 1_000_000))  # TRPO (B1): 1M steps
    assert r is not None, (algo, task, s)
    return {int(x["step"]): float(x["eval_mean"]) for x in r}


res = {}
for name, seeds in (("s10", range(10)), ("s20", range(20))):
    out = dict(ranking={}, seed_rank_spearman={}, final_vs_best={})
    for task in TASKS:
        C = {a: [curve(a, task, s) for s in seeds] for a in ALGOS}
        final = {a: float(iqm(np.array([c[FINAL[a]] for c in C[a]]))) for a in ALGOS}
        order_final = sorted(ALGOS, key=lambda a: -final[a])
        out["ranking"][task] = dict(final=order_final, at={})
        for k in STEPS:
            I = {a: float(iqm(np.array([c[k] for c in C[a]]))) for a in ALGOS}
            order = sorted(ALGOS, key=lambda a: -I[a])
            tau = stats.kendalltau([order_final.index(a) for a in ALGOS], [order.index(a) for a in ALGOS]).statistic
            out["ranking"][task]["at"][k] = dict(order=order, kendall_tau_with_final=float(tau), leader_same=order[0] == order_final[0])
        for a in ALGOS:
            fin = np.array([c[FINAL[a]] for c in C[a]])
            ks = [k for k in sorted(C[a][0]) if k < FINAL[a] and (k in STEPS or k % 250_000 == 0)]
            out["seed_rank_spearman"][f"{a}/{task}"] = {k: float(stats.spearmanr([c[k] for c in C[a]], fin).statistic) for k in ks}
            best = np.array([max(c.values()) for c in C[a]])
            out["final_vs_best"][f"{a}/{task}"] = dict(
                points=len(C[a][0]), share_final_below_best=float((fin < best).mean()),
                median_relative_gap=float(np.median((best - fin) / np.abs(best))),
                iqm_final=float(iqm(fin)), iqm_best=float(iqm(best)), iqm_inflation=float(iqm(best) / iqm(fin) - 1))
    taus = [v["kendall_tau_with_final"] for t in out["ranking"].values() for k, v in t["at"].items()]
    out["summary"] = {k: dict(median_tau=float(np.median([out["ranking"][t]["at"][k]["kendall_tau_with_final"] for t in TASKS])),
                              leaders_same=sum(out["ranking"][t]["at"][k]["leader_same"] for t in TASKS)) for k in STEPS}
    res[name] = out
    print(name, "tau with final ranking by step:", out["summary"])
    for a in ALGOS:
        print("  ", a, "share final < best:", [round(out["final_vs_best"][f"{a}/{t}"]["share_final_below_best"], 2) for t in TASKS],
              "IQM inflation:", [round(out["final_vs_best"][f"{a}/{t}"]["iqm_inflation"], 3) for t in TASKS])
res["autocorrelation"] = {}
for algo in ("ppo_sb3", "trpo"):
    M = np.array([[v for _, v in sorted(curve(algo, "HalfCheetah-v5", s).items())] for s in range(30)])
    R = M - M.mean(0)
    r1 = np.array([np.corrcoef(r[:-1], r[1:])[0, 1] for r in R])
    across = [float(stats.pearsonr(M[:, k], M[:, k + 1]).statistic) for k in range(M.shape[1] - 1)]
    med = float(np.median(r1))
    res["autocorrelation"][algo] = dict(points=M.shape[1], lag1_median=med, lag1_q25_q75=np.percentile(r1, [25, 75]).tolist(),
                                        across_seed_corr_consecutive_median=float(np.median(across)),
                                        effective_points_of_20=float(M.shape[1] * (1 - med) / (1 + med)))
    print(algo, res["autocorrelation"][algo])
json.dump(res, open("analysis/curves.json", "w"), indent=1)
