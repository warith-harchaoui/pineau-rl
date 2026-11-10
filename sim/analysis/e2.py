"""E2, as pre-registered (SIM_PROTOCOL.md, écart 7 for the details): does the ranking change from task to task?
Per task: IQM of each algorithm with its stratified bootstrap 95% interval (rliable, 2,000 resamples), rank by IQM;
for each pair, probability of improvement with its interval, "settled" when the interval excludes 0.5.
Performance profiles: share of runs above each threshold, scores divided by the task's best IQM.
Run from sim/: env-an/bin/python analysis/e2.py  -> analysis/e2.json
"""
import itertools, json, sys
import numpy as np
from rliable import metrics
from rliable.library import get_interval_estimates
sys.path.insert(0, "analysis")
from runs import grid

G, missing = grid()
iqm = lambda x: np.array([metrics.aggregate_iqm(x)])
res = dict(missing=missing, tasks={})
for task, S in G.items():
    pe, ci = get_interval_estimates({a: x[:, None] for a, x in S.items()}, iqm, reps=2000)
    I = {a: float(pe[a][0]) for a in S}
    order = sorted(S, key=lambda a: -I[a])
    pairs = {}
    for a, b in itertools.combinations(order, 2):
        ppe, pci = get_interval_estimates({"p": (S[a][:, None], S[b][:, None])}, metrics.probability_of_improvement, reps=2000)
        lo, hi = [float(x) for x in np.ravel(pci["p"])]
        pairs[f"{a}>{b}"] = dict(p=float(ppe["p"]), ci=[lo, hi], settled=not (lo <= .5 <= hi))
    best = max(I.values())
    taus = np.linspace(0, 1.2, 25)
    res["tasks"][task] = dict(iqm=I, iqm_ci={a: [float(ci[a][0][0]), float(ci[a][1][0])] for a in S}, order=order,
                              pairs=pairs, profile=dict(tau=taus.tolist(),
                                                        **{a: [float((S[a] / best > t).mean()) for t in taus] for a in S}))
    print(task, " > ".join(f"{a} {I[a]:.0f}" for a in order), " settled:", [k for k, v in pairs.items() if v["settled"]])
leaders = {t: r["order"][0] for t, r in res["tasks"].items()}
res["leaders"] = leaders
res["leader_changes"] = len(set(leaders.values())) > 1
# a settled change: the leader of one task is beaten, settled, by another algorithm on another task
res["settled_changes"] = [f"{leaders[t]} leads {t} but loses to {k.split('>')[0]} on {u}"
                          for t in leaders for u, r in res["tasks"].items() if u != t
                          for k, v in r["pairs"].items() if v["settled"] and k.split(">")[1] == leaders[t]]
print("leaders", leaders, "\nsettled changes", len(res["settled_changes"]), "\nmissing", missing)
json.dump(res, open("analysis/e2.json", "w"), indent=1)
