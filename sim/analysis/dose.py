"""E7 at several strengths, as pre-registered (SIM_PROTOCOL.md, deviation 12 (ii)), written BEFORE the dose results.
Reads results/dose/<algo>/<task>/seed<s>.json (dose.py): each final policy re-evaluated on the same 10 held-out
evaluation seeds, masses x 0.7 to 1.3, friction x 0.6 to 1.2, one quantity at a time.
Per algorithm, task and strength: the ratio to the score in the original physics (mass x 1.0), IQM over the seeds with
its stratified bootstrap 95% interval (rliable, 2,000 resamples); a loss is declared only when the interval stays below
1, as E7. Per task and strength: the ranking of the four algorithms by IQM of the score, no test.
Control: the score at x 1.0 must equal run.py's final eval_mean (reported as the largest relative gap).
Run from sim/: env-an/bin/python analysis/dose.py  -> analysis/dose.json  (SEEDS=0:20 for twenty random seeds)
"""
import json, os, sys
import numpy as np
from pineau_rl.bootstrap import iqm, iqm_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from pineau_rl.runs import read_run, run_path
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, SEEDS, TASKS, out_json

res, ranks, gaps, missing = {}, {}, [], {}
for task in TASKS:
    scores = {}  # algo -> {(quantity, strength): array over seeds}
    for algo in ALGOS:
        runs = [f"results/dose/{algo}/{task}/seed{s}.json" for s in SEEDS]
        have = [f for f in runs if os.path.exists(f)]
        if len(have) < len(runs):
            missing[f"{algo}/{task}"] = len(have)
            continue
        d = [json.load(open(f)) for f in runs]
        for s, x in zip(SEEDS, d):  # the control
            r = read_run(run_path(ROOT, algo, task, s), FINAL[algo])
            assert r is not None, (algo, task, s)
            last = r[-1]
            gaps.append(abs(x["mass"]["1.0"] / float(last["eval_mean"]) - 1))
        base = np.array([x["mass"]["1.0"] for x in d])
        scores[algo] = {(q, k): np.array([x[q][k] for x in d]) for q in ("mass", "friction") for k in d[0][q]}
        for (q, k), v in scores[algo].items():
            if k == "1.0":
                continue
            r = v / base
            m, lo, hi = iqm_interval({"r": r}, reps=2000, random_state=RS)["r"]
            res[f"{algo}/{task}/{q}/{k}"] = dict(iqm=m, ci=[lo, hi], ratios=r.tolist(),
                                                verdict="loss" if hi < 1 else "gain" if lo > 1 else "no detectable change")
    if len(scores) == len(ALGOS):
        for key in scores[ALGOS[0]]:
            iq = {a: float(iqm(scores[a][key])) for a in ALGOS}
            ranks[f"{task}/{key[0]}/{key[1]}"] = dict(iqm=iq, ranking=sorted(ALGOS, key=lambda a: -iq[a]))

for k, v in res.items():
    print(f"{k:38s} IQM ratio {v['iqm']:.2f} [{v['ci'][0]:.2f}, {v['ci'][1]:.2f}]  {v['verdict']}")
for k, v in ranks.items():
    print(f"{k:28s} {' > '.join(v['ranking'])}")
control = max(gaps) if gaps else None
print("control, largest relative gap between x 1.0 and run.py:", control)
print("not finished (seeds done):", missing)
json.dump(dict(seeds=[SEEDS.start, SEEDS.stop], control_max_rel_gap=control, missing=missing, ratio=res, ranking=ranks),
          open(out_json("dose"), "w"), indent=1)
