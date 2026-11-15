"""E7, as pre-registered (SIM_PROTOCOL.md): held out. For each algorithm and task, the gap between the final
evaluation on the training dynamics (`eval_mean`) and on the modified dynamics (`perturbed_mean`: masses x 1.2,
friction x 0.8), both on the held-out evaluation seeds. Per run: the ratio perturbed / training. Per algorithm and
task: IQM of the ratio over the 10 seeds with its stratified bootstrap 95% interval (rliable, 2,000 resamples).
A loss is declared only when the interval stays below 1. Runs not finished yet are left out and counted.
Run from sim/: env-an/bin/python analysis/e7.py  -> analysis/e7.json
"""
import json, sys
import numpy as np
from pineau_rl.bootstrap import iqm_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from pineau_rl.runs import read_run, run_path
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, SEEDS, TASKS, out_json  # deviation 12: SEEDS=0:20 for twenty random seeds

res = {}
for algo in ALGOS:
    for task in TASKS:
        ratios = []
        for s in SEEDS:
            r = read_run(run_path(ROOT, algo, task, s), FINAL[algo])  # None: missing or not finished
            if r is None or not r[-1]["perturbed_mean"]:
                continue
            ratios.append(float(r[-1]["perturbed_mean"]) / float(r[-1]["eval_mean"]))
        if len(ratios) < len(SEEDS):
            res[f"{algo}/{task}"] = dict(n=len(ratios), done=False)
            continue
        x = np.array(ratios)
        m, lo, hi = iqm_interval({"r": x}, reps=2000, random_state=RS)["r"]
        res[f"{algo}/{task}"] = dict(n=len(SEEDS), done=True, ratios=x.tolist(), iqm=m, ci=[lo, hi],
                                     verdict="loss" if hi < 1 else "gain" if lo > 1 else "no detectable change")
        print(f"{algo:8s} {task:15s} IQM ratio {m:.2f} [{lo:.2f}, {hi:.2f}]  {res[f'{algo}/{task}']['verdict']}")
missing = {k: v["n"] for k, v in res.items() if not v["done"]}
print("not finished:", missing)
json.dump(res, open(out_json("e7"), "w"), indent=1)
