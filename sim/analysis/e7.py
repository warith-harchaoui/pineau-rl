"""E7, as pre-registered (SIM_PROTOCOL.md): held out. For each algorithm and task, the gap between the final
evaluation on the training dynamics (`eval_mean`) and on the modified dynamics (`perturbed_mean`: masses x 1.2,
friction x 0.8), both on the held-out evaluation seeds. Per run: the ratio perturbed / training. Per algorithm and
task: IQM of the ratio over the 10 seeds with its stratified bootstrap 95% interval (rliable, 2,000 resamples).
A loss is declared only when the interval stays below 1. Runs not finished yet are left out and counted.
Run from sim/: env-an/bin/python analysis/e7.py  -> analysis/e7.json
"""
import csv, glob, json, sys
import numpy as np
from rliable import metrics
from rliable.library import get_interval_estimates
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)

ALGOS = ["ppo_sb3", "ppo_sbx", "sac", "crossq"]
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
FINAL = {"ppo_sb3": 1_000_000, "ppo_sbx": 1_000_000, "sac": 200_000, "crossq": 200_000}  # écart 1
sys.path.insert(0, "analysis")
from runs import SEEDS, out_json  # deviation 12: SEEDS=0:20 for twenty random seeds

iqm = lambda x: np.array([metrics.aggregate_iqm(x)])
res = {}
for algo in ALGOS:
    for task in TASKS:
        ratios = []
        for s in SEEDS:
            f = f"results/{algo}/{task}/seed{s}.csv"
            if not glob.glob(f):
                continue
            r = list(csv.DictReader(open(f)))
            if int(r[-1]["step"]) != FINAL[algo] or not r[-1]["perturbed_mean"]:
                continue
            ratios.append(float(r[-1]["perturbed_mean"]) / float(r[-1]["eval_mean"]))
        if len(ratios) < len(SEEDS):
            res[f"{algo}/{task}"] = dict(n=len(ratios), done=False)
            continue
        x = np.array(ratios)
        pe, ci = get_interval_estimates({"r": x[:, None]}, iqm, reps=2000, random_state=RS)
        lo, hi = float(ci["r"][0][0]), float(ci["r"][1][0])
        res[f"{algo}/{task}"] = dict(n=len(SEEDS), done=True, ratios=x.tolist(), iqm=float(pe["r"][0]), ci=[lo, hi],
                                     verdict="loss" if hi < 1 else "gain" if lo > 1 else "no detectable change")
        print(f"{algo:8s} {task:15s} IQM ratio {pe['r'][0]:.2f} [{lo:.2f}, {hi:.2f}]  {res[f'{algo}/{task}']['verdict']}")
missing = {k: v["n"] for k, v in res.items() if not v["done"]}
print("not finished:", missing)
json.dump(res, open(out_json("e7"), "w"), indent=1)
