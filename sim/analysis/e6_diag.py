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
import json
import numpy as np
from pineau_rl.bootstrap import iqm_interval, probability_of_improvement_bootstrap
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from scipy import stats
from pineau_rl.runs import finals as read_finals
from pineau_rl.stats import holm

finals = lambda tag, task: read_finals("results", tag, task, range(10), 1_000_000, strict=True)  # explicit seeds 0 to 9


G = {"default v5": finals("ppo_sb3", "Hopper-v5"), "zoo v5 (bug)": finals("ppo_sb3_zoo", "Hopper-v5"),
     "zoofix v5": finals("ppo_sb3_zoofix", "Hopper-v5"), "default v4": finals("ppo_sb3", "Hopper-v4"),
     "zoofix v4": finals("ppo_sb3_zoofix", "Hopper-v4")}
est = iqm_interval(G, reps=5000, random_state=RS)
groups = {k: dict(runs=v.tolist(), mean=float(v.mean()), sd=float(v.std(ddof=1)), iqm=est[k][0],
                  iqm_ci=list(est[k][1:])) for k, v in G.items()}

rng = np.random.default_rng(2018)
p_improve = lambda x, y: probability_of_improvement_bootstrap(x, y, rng, reps=5000)


COMP = [("zoofix v5", "zoo v5 (bug)"), ("zoofix v4", "default v4"), ("zoofix v5", "default v5")]
comps = []
for a, b in COMP:
    x, y = G[a], G[b]
    p, pci = p_improve(x, y)
    comps.append(dict(a=a, b=b, welch_p=float(stats.ttest_ind(x, y, equal_var=False).pvalue),
                      mannwhitney_p=float(stats.mannwhitneyu(x, y).pvalue), p_improve=p, p_improve_ci=pci))
for c, h in zip(comps, holm([c["welch_p"] for c in comps])):
    c["welch_p_holm"] = float(h)

json.dump(dict(groups=groups, comparisons=comps), open("analysis/e6_diag.json", "w"), indent=1)
for k, g in groups.items():
    print(f"{k:14s} IQM {g['iqm']:7.0f} [{g['iqm_ci'][0]:.0f}, {g['iqm_ci'][1]:.0f}]  mean {g['mean']:.0f} sd {g['sd']:.0f}")
for c in comps:
    print(f"{c['a']} vs {c['b']}: P(improve) {c['p_improve']:.2f} [{c['p_improve_ci'][0]:.2f}, {c['p_improve_ci'][1]:.2f}]"
          f"  Welch p {c['welch_p']:.2g} (Holm {c['welch_p_holm']:.2g})  MW p {c['mannwhitney_p']:.2g}")
