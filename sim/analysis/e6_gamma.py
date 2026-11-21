"""E6, the published recipe with gamma = 0.99 (SIM_PROTOCOL.md, deviation 33 (c), written before this training).
ppo_sb3_zoog99: the corrected Zoo recipe of deviation 2 with gamma 0.99 for the algorithm and the normalisation, 10 seeds
on Hopper-v4. Against the corrected recipe (ppo_sb3_zoofix, gamma 0.999) and the defaults (ppo_sb3) on Hopper-v4: IQM
with its stratified bootstrap 95% interval (rliable, 2,000 resamples, global generator seeded with 2026), probability
of improvement with its interval, two-sided Mann-Whitney p with Holm over the two comparisons. Standing still is read
from the final evaluation (eval_mean / 1,000 close to 1 with full-length episodes is a robot upright and still): the
share of runs whose final score lies between 900 and 1,100, and, from analysis/e6_enjoy.json (rerun with env-zoo once
these policies exist), the share of final evaluation episodes of 1,000 steps whose return per step lies within 0.05 of 1
and the median forward speed.
Run from sim/ once the 10 runs are finished: env-an/bin/python analysis/e6_gamma.py  -> analysis/e6_gamma.json
"""
import json
import numpy as np
from scipy import stats
from pineau_rl.bootstrap import iqm_interval, improvement_interval
from pineau_rl.stats import holm
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from pineau_rl.runs import finals

G = {t: finals("results", t, "Hopper-v4", range(10), 1_000_000, strict=True)
     for t in ("ppo_sb3_zoog99", "ppo_sb3_zoofix", "ppo_sb3")}
est = iqm_interval(G, reps=2000, random_state=RS)
comps = []
for b in ("ppo_sb3_zoofix", "ppo_sb3"):
    x, y = G["ppo_sb3_zoog99"], G[b]
    p, lo, hi = improvement_interval(x, y, reps=2000, random_state=RS)
    comps.append(dict(a="ppo_sb3_zoog99", b=b, p_improve=p, ci=[lo, hi], settled=not (lo <= .5 <= hi),
                      mw_p=float(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)))
for c, h in zip(comps, holm([c["mw_p"] for c in comps])):
    c["mw_p_holm"] = h
res = dict(groups={k: dict(runs=v.tolist(), iqm=est[k][0], iqm_ci=list(est[k][1:]),
                           share_900_1100=float(((v > 900) & (v < 1100)).mean())) for k, v in G.items()},
           comparisons=comps)
en = json.load(open("analysis/e6_enjoy.json"))["groups"]
for g, tag in (("zoog99", "ppo_sb3_zoog99"), ("zoofix", "ppo_sb3_zoofix"), ("default", "ppo_sb3")):
    if g in en:
        eps = [e for r in en[g]["runs"].values() for e in r["episodes"]]
        res["groups"][tag]["share_episodes_standing"] = float(np.mean([e["length"] == 1000 and abs(e["return_per_step"] - 1) < .05
                                                                        for e in eps]))
        res["groups"][tag]["median_speed"] = en[g]["median_speed"]
print(json.dumps(res, indent=1))
json.dump(res, open("analysis/e6_gamma.json", "w"), indent=1)
