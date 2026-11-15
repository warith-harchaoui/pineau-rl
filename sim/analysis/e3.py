"""E3, as pre-registered (SIM_PROTOCOL.md): two implementations of the same algorithm, PPO-SB3 (PyTorch) against
PPO-sbx (JAX), on the four tasks, the same 10 random seeds (0 to 9), final evaluation score at 1M steps.
Per task: IQM of each with its stratified bootstrap 95% interval (rliable, 2,000 resamples), gap between the two
IQMs, probability that a sbx run beats a SB3 run with its interval. As the protocol says, a winner is declared only
when the two IQM intervals do not overlap, or when the interval of the probability of improvement stays clear of 0.5.
Run from sim/: env-an/bin/python analysis/e3.py  -> analysis/e3.json
"""
import csv, json, sys
import numpy as np
from rliable import metrics
from rliable.library import get_interval_estimates
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)

TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
sys.path.insert(0, "analysis")
from runs import SEEDS, out_json  # deviation 12: SEEDS=0:20 for twenty random seeds


def finals(algo, task):
    out = []
    for s in SEEDS:
        r = list(csv.DictReader(open(f"results/{algo}/{task}/seed{s}.csv")))
        assert int(r[-1]["step"]) == 1_000_000, (algo, task, s)
        out.append(float(r[-1]["eval_mean"]))
    return np.array(out)


iqm = lambda x: np.array([metrics.aggregate_iqm(x)])
res = {}
for task in TASKS:
    a, b = finals("ppo_sb3", task), finals("ppo_sbx", task)
    pe, ci = get_interval_estimates({"sb3": a[:, None], "sbx": b[:, None]}, iqm, reps=2000, random_state=RS)
    ppe, pci = get_interval_estimates({"sbx>sb3": (b[:, None], a[:, None])}, metrics.probability_of_improvement, reps=2000, random_state=RS)
    r = dict(sb3=a.tolist(), sbx=b.tolist(),
             iqm={k: float(pe[k][0]) for k in pe}, iqm_ci={k: [float(ci[k][0][0]), float(ci[k][1][0])] for k in pe},
             p_improve=float(ppe["sbx>sb3"]), p_improve_ci=[float(x) for x in np.ravel(pci["sbx>sb3"])])
    lo_a, hi_a = r["iqm_ci"]["sb3"]; lo_b, hi_b = r["iqm_ci"]["sbx"]
    r["iqm_ratio_sbx_over_sb3"] = r["iqm"]["sbx"] / r["iqm"]["sb3"]
    r["intervals_overlap"] = not (hi_a < lo_b or hi_b < lo_a)
    r["winner"] = (None if r["intervals_overlap"] and r["p_improve_ci"][0] <= .5 <= r["p_improve_ci"][1]
                   else "sbx" if r["p_improve"] > .5 else "sb3")
    res[task] = r
    print(f"{task:15s} SB3 {r['iqm']['sb3']:7.0f} [{lo_a:.0f}, {hi_a:.0f}]  sbx {r['iqm']['sbx']:7.0f} [{lo_b:.0f}, {hi_b:.0f}]  "
          f"P(sbx>sb3) {r['p_improve']:.2f} [{r['p_improve_ci'][0]:.2f}, {r['p_improve_ci'][1]:.2f}]  winner {r['winner']}")
json.dump(res, open(out_json("e3"), "w"), indent=1)
