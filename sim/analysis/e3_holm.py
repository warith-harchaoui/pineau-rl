"""E3 corrected for four tasks, and its power (SIM_PROTOCOL.md, deviation 23, written before this computation).
On the scores of analysis/e3.json (ten seeds) and analysis/e3_s20.json (twenty): per task, two-sided Mann-Whitney test
of PPO-sbx against PPO-SB3, Holm's correction over the four tasks; probability-of-improvement interval at the
simultaneous level 1 - 0.05/4 (rliable, 2,000 resamples, global generator seeded with 2026); Hodges-Lehmann gap
(median of the pairwise differences sbx - sb3) with a 95% percentile interval (5,000 resamples, default_rng(2026)).
Power: 2,000 draws with replacement of n runs per program among the twenty, n = 10 to 60, share with Mann-Whitney
p < 0.05/4 and p < 0.05; smallest probability of improvement detectable with 80% power at level 0.05/4 (normal
approximation of U: var(P) = (n1 + n2 + 1) / (12 n1 n2) under the null).
Run from sim/: env-an/bin/python analysis/e3_holm.py  -> analysis/e3_holm.json
"""
import json
import numpy as np
from scipy import stats
from pineau_rl.bootstrap import improvement_interval
from pineau_rl.stats import holm
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
rng = np.random.default_rng(2026)
LEVEL = 1 - 0.05 / 4


def hodges_lehmann(x, y, reps=5000):
    hl = lambda a, b: float(np.median(a[:, None] - b[None, :]))
    boots = [hl(rng.choice(x, len(x)), rng.choice(y, len(y))) for _ in range(reps)]
    return hl(x, y), np.percentile(boots, [2.5, 97.5]).tolist()


def mde(n, alpha=0.05 / 4, power=0.8):
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return float(0.5 + z * np.sqrt((2 * n + 1) / (12 * n * n)))


res = {}
for name, f in (("s10", "analysis/e3.json"), ("s20", "analysis/e3_s20.json")):
    e3 = json.load(open(f))
    out = {}
    for task, r in e3.items():
        a, b = np.array(r["sb3"]), np.array(r["sbx"])
        p, lo, hi = improvement_interval(b, a, reps=2000, random_state=RS, confidence=LEVEL)
        hl, hl_ci = hodges_lehmann(b, a)
        out[task] = dict(mw_p=float(stats.mannwhitneyu(b, a, alternative="two-sided").pvalue),
                         p_improve_sbx=p, p_improve_ci_bonferroni=[lo, hi], settled_bonferroni=not (lo <= .5 <= hi),
                         hodges_lehmann_sbx_minus_sb3=hl, hodges_lehmann_ci=hl_ci,
                         iqm=r["iqm"], p_improve_ci95=r["p_improve_ci"])
    for t, h in zip(out, holm([v["mw_p"] for v in out.values()])):
        out[t]["mw_p_holm"] = float(h)
        out[t]["settled_holm"] = bool(h < .05)
    res[name] = out
    for t, v in out.items():
        print(f"{name} {t:15s} MW p {v['mw_p']:.4f} Holm {v['mw_p_holm']:.4f}  P(sbx>sb3) {v['p_improve_sbx']:.2f} "
              f"[{v['p_improve_ci_bonferroni'][0]:.2f}, {v['p_improve_ci_bonferroni'][1]:.2f}] (98.75%)  "
              f"HL {v['hodges_lehmann_sbx_minus_sb3']:.0f} [{v['hodges_lehmann_ci'][0]:.0f}, {v['hodges_lehmann_ci'][1]:.0f}]")
e3 = json.load(open("analysis/e3_s20.json"))
res["power"] = {}
for task, r in e3.items():
    a, b = np.array(r["sb3"]), np.array(r["sbx"])
    res["power"][task] = {}
    for n in (10, 20, 30, 40, 60):
        ps = np.array([stats.mannwhitneyu(rng.choice(b, n), rng.choice(a, n), alternative="two-sided").pvalue
                       for _ in range(2000)])
        res["power"][task][n] = dict(alpha_0_0125=float((ps < .05 / 4).mean()), alpha_0_05=float((ps < .05).mean()))
    print("power", task, {n: v["alpha_0_0125"] for n, v in res["power"][task].items()})
res["min_detectable_p_improve_80pct_alpha_0_0125"] = {n: mde(n) for n in (10, 20, 40)}
print("MDE", res["min_detectable_p_improve_80pct_alpha_0_0125"])
json.dump(res, open("analysis/e3_holm.json", "w"), indent=1)
