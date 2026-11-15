"""E6 diagnostic (SIM_PROTOCOL.md, Écart 2): is the published RL Zoo recipe worse than the library defaults,
or was our first pass broken? Five groups of 10 runs of PPO-SB3 on Hopper, one million steps:
  default v5 (ppo_sb3, Hopper-v5), zoo v5 (ppo_sb3_zoo, first pass, VecNormalize gamma left at 0.99),
  zoofix v5 (ppo_sb3_zoofix, gamma 0.999 as the Zoo), default v4 and zoofix v4 (the Zoo was tuned on v4).
Three comparisons, Holm-corrected: the bug (zoo v5 vs zoofix v5), the fair test on the Zoo's own version
(zoofix v4 vs default v4), the same on v5 (zoofix v5 vs default v5).
Per group: IQM with a 95% bootstrap interval (rliable). Per comparison: Welch's p, Mann-Whitney's p, and the
probability of improvement P(X > Y) with a 95% bootstrap interval.
Run from sim/: env-an/bin/python analysis/e6_diag.py  -> analysis/e6_diag.json
"""
import csv, glob, json
import numpy as np
from rliable import metrics
from rliable.library import get_interval_estimates
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from scipy import stats
from statsmodels.stats.multitest import multipletests


def finals(tag, task):
    out = []
    for f in sorted(glob.glob(f"results/{tag}/{task}/seed*.csv")):
        r = list(csv.DictReader(open(f)))
        assert int(r[-1]["step"]) == 1_000_000, f
        out.append(float(r[-1]["eval_mean"]))
    assert len(out) == 10, (tag, task, len(out))
    return np.array(out)


G = {"default v5": finals("ppo_sb3", "Hopper-v5"), "zoo v5 (bug)": finals("ppo_sb3_zoo", "Hopper-v5"),
     "zoofix v5": finals("ppo_sb3_zoofix", "Hopper-v5"), "default v4": finals("ppo_sb3", "Hopper-v4"),
     "zoofix v4": finals("ppo_sb3_zoofix", "Hopper-v4")}
iqm = lambda x: np.array([metrics.aggregate_iqm(x)])
pe, ci = get_interval_estimates({k: v[:, None] for k, v in G.items()}, iqm, reps=5000, random_state=RS)
groups = {k: dict(runs=v.tolist(), mean=float(v.mean()), sd=float(v.std(ddof=1)), iqm=float(pe[k][0]),
                  iqm_ci=[float(ci[k][0][0]), float(ci[k][1][0])]) for k, v in G.items()}

rng = np.random.default_rng(2018)


def p_improve(x, y, reps=5000):
    pi = lambda a, b: (a[:, None] > b[None, :]).mean() + 0.5 * (a[:, None] == b[None, :]).mean()
    boots = [pi(rng.choice(x, len(x)), rng.choice(y, len(y))) for _ in range(reps)]
    return float(pi(x, y)), [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]


COMP = [("zoofix v5", "zoo v5 (bug)"), ("zoofix v4", "default v4"), ("zoofix v5", "default v5")]
comps = []
for a, b in COMP:
    x, y = G[a], G[b]
    p, pci = p_improve(x, y)
    comps.append(dict(a=a, b=b, welch_p=float(stats.ttest_ind(x, y, equal_var=False).pvalue),
                      mannwhitney_p=float(stats.mannwhitneyu(x, y).pvalue), p_improve=p, p_improve_ci=pci))
for c, h in zip(comps, multipletests([c["welch_p"] for c in comps], method="holm")[1]):
    c["welch_p_holm"] = float(h)

json.dump(dict(groups=groups, comparisons=comps), open("analysis/e6_diag.json", "w"), indent=1)
for k, g in groups.items():
    print(f"{k:14s} IQM {g['iqm']:7.0f} [{g['iqm_ci'][0]:.0f}, {g['iqm_ci'][1]:.0f}]  mean {g['mean']:.0f} sd {g['sd']:.0f}")
for c in comps:
    print(f"{c['a']} vs {c['b']}: P(improve) {c['p_improve']:.2f} [{c['p_improve_ci'][0]:.2f}, {c['p_improve_ci'][1]:.2f}]"
          f"  Welch p {c['welch_p']:.2g} (Holm {c['welch_p_holm']:.2g})  MW p {c['mannwhitney_p']:.2g}")
