"""E7, descriptive complement (SIM_PROTOCOL.md, deviation 11, written AFTER the E7 results, no test): per task, the
ranking of the four algorithms by IQM of the final evaluation in the training physics (`eval_mean`) and in the
modified physics (`perturbed_mean`), and whether the leader changes.
Run from sim/: env-an/bin/python analysis/e7_rank.py  -> analysis/e7_rank.json
"""
import json, sys
from pineau_rl.bootstrap import iqm
from pineau_rl.runs import finals
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, SEEDS, TASKS, out_json  # deviation 12: SEEDS=0:20 for twenty random seeds

out = {}
for task in TASKS:
    iq = {}
    for col in ("eval_mean", "perturbed_mean"):
        for algo in ALGOS:
            x = finals(ROOT, algo, task, SEEDS, FINAL[algo], column=col, strict=True)  # the last evaluation, at the budget
            iq.setdefault(col, {})[algo] = float(iqm(x))
    rank = {c: sorted(ALGOS, key=lambda a: -iq[c][a]) for c in iq}
    out[task] = dict(iqm=iq, training=rank["eval_mean"], modified=rank["perturbed_mean"],
                     leader_changes=rank["eval_mean"][0] != rank["perturbed_mean"][0])
    print(f"{task:15s} training {' > '.join(rank['eval_mean'])}  |  modified {' > '.join(rank['perturbed_mean'])}")
print("tasks whose leader changes:", [t for t in TASKS if out[t]["leader_changes"]])
json.dump(out, open(out_json("e7_rank"), "w"), indent=1)
