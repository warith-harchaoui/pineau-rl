"""E7, descriptive complement (SIM_PROTOCOL.md, deviation 11, written AFTER the E7 results, no test): per task, the
ranking of the four algorithms by IQM of the final evaluation in the training physics (`eval_mean`) and in the
modified physics (`perturbed_mean`), and whether the leader changes.
Run from sim/: env-an/bin/python analysis/e7_rank.py  -> analysis/e7_rank.json
"""
import csv, json
import numpy as np
from rliable import metrics

ALGOS = ["ppo_sb3", "ppo_sbx", "sac", "crossq"]
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
FINAL = {"ppo_sb3": 1_000_000, "ppo_sbx": 1_000_000, "sac": 200_000, "crossq": 200_000}  # écart 1

out = {}
for task in TASKS:
    iq = {}
    for col in ("eval_mean", "perturbed_mean"):
        for algo in ALGOS:
            rows = [list(csv.DictReader(open(f"results/{algo}/{task}/seed{s}.csv")))[-1] for s in range(10)]
            assert all(int(r["step"]) == FINAL[algo] for r in rows)
            iq.setdefault(col, {})[algo] = float(metrics.aggregate_iqm(np.array([float(r[col]) for r in rows])))
    rank = {c: sorted(ALGOS, key=lambda a: -iq[c][a]) for c in iq}
    out[task] = dict(iqm=iq, training=rank["eval_mean"], modified=rank["perturbed_mean"],
                     leader_changes=rank["eval_mean"][0] != rank["perturbed_mean"][0])
    print(f"{task:15s} training {' > '.join(rank['eval_mean'])}  |  modified {' > '.join(rank['perturbed_mean'])}")
print("tasks whose leader changes:", [t for t in TASKS if out[t]["leader_changes"]])
json.dump(out, open("analysis/e7_rank.json", "w"), indent=1)
