"""B3 (SIM_PROTOCOL.md, deviation 8): does the measure change the ranking? No training: on the recorded evaluation
curves, three measures per run (final score, best score along the curve, mean of the curve); per task, IQM of each
measure and ranking of the algorithms; pairs whose order reverses between two measures, and reversals "settled"
when, under each measure, the interval of the probability of improvement excludes 0.5 in opposite directions.
Run from sim/: env-an/bin/python analysis/b3.py  -> analysis/b3.json
"""
import itertools, json, sys
import numpy as np
from pineau_rl.bootstrap import iqm_interval, improvement_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
sys.path.insert(0, "analysis")
from runs import ALGOS, TASKS, SEEDS, out_json, read

MEASURES = {"final": lambda c: c[-1], "best": lambda c: c.max(), "mean": lambda c: c.mean()}


def curves(algo, task):
    out = []
    for s in SEEDS:
        r = read(algo, task, s)
        if r is None:
            return None
        out.append(np.array([float(x["eval_mean"]) for x in r]))
    return out


res, missing = dict(tasks={}), []
for task in TASKS:
    C = {}
    for a in ALGOS:
        c = curves(a, task)
        if c is None:
            missing.append(f"{a}/{task}")
        else:
            C[a] = c
    S = {m: {a: np.array([f(c) for c in C[a]]) for a in C} for m, f in MEASURES.items()}
    I, P = {}, {}
    for m in MEASURES:
        est = iqm_interval(S[m], reps=2000, random_state=RS)
        I[m] = {a: est[a][0] for a in C}
        P[m] = {}
        for a, b in itertools.combinations(sorted(C), 2):
            P[m][f"{a}>{b}"] = list(improvement_interval(S[m][a], S[m][b], reps=2000, random_state=RS)[1:])
    order = {m: sorted(C, key=lambda a: -I[m][a]) for m in MEASURES}
    rev = []
    for m1, m2 in itertools.combinations(MEASURES, 2):
        for a, b in itertools.combinations(sorted(C), 2):
            if np.sign(I[m1][a] - I[m1][b]) != np.sign(I[m2][a] - I[m2][b]):
                (l1, h1), (l2, h2) = P[m1][f"{a}>{b}"], P[m2][f"{a}>{b}"]
                settled = (l1 > .5 and h2 < .5) or (h1 < .5 and l2 > .5)
                rev.append(dict(measures=f"{m1}/{m2}", pair=f"{a} vs {b}", settled=settled))
    res["tasks"][task] = dict(iqm=I, order=order, reversals=rev)
    print(task, {m: " > ".join(o) for m, o in order.items()}, "reversals", len(rev), "settled", sum(r["settled"] for r in rev))
res["missing"] = missing
res["n_reversals"] = sum(len(t["reversals"]) for t in res["tasks"].values())
res["n_settled"] = sum(r["settled"] for t in res["tasks"].values() for r in t["reversals"])
res["leader_changes"] = [t for t, r in res["tasks"].items() if len({o[0] for o in r["order"].values()}) > 1]
print("reversals", res["n_reversals"], "settled", res["n_settled"], "tasks whose leader depends on the measure", res["leader_changes"], "missing", missing)
json.dump(res, open(out_json("b3"), "w"), indent=1)
