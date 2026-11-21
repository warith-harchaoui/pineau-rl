"""E1 on the sixteen pairs (SIM_PROTOCOL.md, deviation 22, written before this computation; exploratory).
For each (program, task) pair of E2, seeds 0 to 19: E1's two draws, 10,000 times each. Random: two disjoint groups of 5
at random. Sorted: 10 runs drawn without replacement, the 5 best against the 5 worst. Share of draws where Welch's test
gives p < 0.05. Uncertainty: 1,000 populations resampled with replacement from the runs, 1,000 draws of each kind on
each, 95% percentile interval of each rate. The same uncertainty on the 30 runs of E1's preregistered pair.
Run from sim/: env-an/bin/python analysis/e1_grid.py  -> analysis/e1_grid.json
"""
import json, sys
import numpy as np
from scipy import stats
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, TASKS
from pineau_rl.runs import finals

rng = np.random.default_rng(2018)


def welch_sig(a, b):
    """Welch p < 0.05 for each row of a and b (draws x 5); a draw with no variance on both sides counts as no."""
    p = stats.ttest_ind(a, b, axis=1, equal_var=False).pvalue
    return np.nan_to_num(p, nan=1.0) < .05


def rates(F, N):
    n = len(F)
    idx = rng.permuted(np.tile(np.arange(n), (N, 1)), axis=1)
    rand = welch_sig(F[idx[:, :5]], F[idx[:, 5:10]]).mean()
    idx = rng.permuted(np.tile(np.arange(n), (N, 1)), axis=1)[:, :10]
    x = np.sort(F[idx], axis=1)
    srt = welch_sig(x[:, 5:], x[:, :5]).mean()
    return float(rand), float(srt)


def cell(F, N=10000, B=1000, NB=1000):
    r, s = rates(F, N)
    boot = np.array([rates(F[rng.integers(0, len(F), len(F))], NB) for _ in range(B)])
    return dict(n=len(F), random_5v5=r, random_5v5_ci=np.percentile(boot[:, 0], [2.5, 97.5]).tolist(),
                sorted_5v5=s, sorted_5v5_ci=np.percentile(boot[:, 1], [2.5, 97.5]).tolist(),
                cv=float(F.std(ddof=1) / abs(F.mean())), skew=float(stats.skew(F)))


res = dict(cells={})
for task in TASKS:
    for algo in ALGOS:
        F = finals(ROOT, algo, task, range(20), FINAL[algo], strict=True)
        res["cells"][f"{algo}/{task}"] = c = cell(F)
        print(f"{algo:8s} {task:15s} random {c['random_5v5']:.3f} {np.round(c['random_5v5_ci'], 3)}  "
              f"sorted {c['sorted_5v5']:.3f} {np.round(c['sorted_5v5_ci'], 3)}  skew {c['skew']:+.2f}")
r = np.array([c["random_5v5"] for c in res["cells"].values()])
s = np.array([c["sorted_5v5"] for c in res["cells"].values()])
res["summary"] = dict(random_median=float(np.median(r)), random_min=float(r.min()), random_max=float(r.max()),
                      sorted_median=float(np.median(s)), sorted_min=float(s.min()), sorted_max=float(s.max()),
                      sorted_min_cell=list(res["cells"])[int(s.argmin())], random_min_cell=list(res["cells"])[int(r.argmin())])
F30 = finals(ROOT, "ppo_sb3", "HalfCheetah-v5", range(30), 1_000_000, strict=True)
res["e1_preregistered_30_runs"] = cell(F30)
print("summary", res["summary"], "\nE1, 30 runs", {k: v for k, v in res["e1_preregistered_30_runs"].items()})
json.dump(res, open("analysis/e1_grid.json", "w"), indent=1)
