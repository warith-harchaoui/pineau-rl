"""E3, as pre-registered (SIM_PROTOCOL.md): two implementations of the same algorithm, PPO-SB3 (PyTorch) against
PPO-sbx (JAX), on the four tasks, the same 10 random seeds (0 to 9), final evaluation score at 1M steps.
Per task: IQM of each with its stratified bootstrap 95% interval (rliable, 2,000 resamples), gap between the two
IQMs, probability that a sbx run beats a SB3 run with its interval. As the protocol says, a winner is declared only
when the two IQM intervals do not overlap, or when the interval of the probability of improvement stays clear of 0.5.
Run from sim/: env-an/bin/python analysis/e3.py  -> analysis/e3.json
"""
import json, sys
import numpy as np
from pineau_rl.bootstrap import iqm_interval, improvement_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from pineau_rl.runs import finals as read_finals
sys.path.insert(0, "analysis")
from runs import ROOT, SEEDS, TASKS, out_json  # deviation 12: SEEDS=0:20 for twenty random seeds

finals = lambda algo, task: read_finals(ROOT, algo, task, SEEDS, 1_000_000, strict=True)  # every run at 1M steps
res = {}
for task in TASKS:
    a, b = finals("ppo_sb3", task), finals("ppo_sbx", task)
    est = iqm_interval({"sb3": a, "sbx": b}, reps=2000, random_state=RS)
    p, lo, hi = improvement_interval(b, a, reps=2000, random_state=RS)
    r = dict(sb3=a.tolist(), sbx=b.tolist(),
             iqm={k: v[0] for k, v in est.items()}, iqm_ci={k: list(v[1:]) for k, v in est.items()},
             p_improve=p, p_improve_ci=[lo, hi])
    lo_a, hi_a = r["iqm_ci"]["sb3"]; lo_b, hi_b = r["iqm_ci"]["sbx"]
    r["iqm_ratio_sbx_over_sb3"] = r["iqm"]["sbx"] / r["iqm"]["sb3"]
    r["intervals_overlap"] = not (hi_a < lo_b or hi_b < lo_a)
    r["winner"] = (None if r["intervals_overlap"] and r["p_improve_ci"][0] <= .5 <= r["p_improve_ci"][1]
                   else "sbx" if r["p_improve"] > .5 else "sb3")
    res[task] = r
    print(f"{task:15s} SB3 {r['iqm']['sb3']:7.0f} [{lo_a:.0f}, {hi_a:.0f}]  sbx {r['iqm']['sbx']:7.0f} [{lo_b:.0f}, {hi_b:.0f}]  "
          f"P(sbx>sb3) {r['p_improve']:.2f} [{r['p_improve_ci'][0]:.2f}, {r['p_improve_ci'][1]:.2f}]  winner {r['winner']}")
json.dump(res, open(out_json("e3"), "w"), indent=1)
