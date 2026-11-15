"""E2, as pre-registered (SIM_PROTOCOL.md, écart 7 for the details): does the ranking change from task to task?
Per task: IQM of each algorithm with its stratified bootstrap 95% interval (rliable, 2,000 resamples), rank by IQM;
for each pair, probability of improvement with its interval, "settled" when the interval excludes 0.5.
Performance profiles: share of runs above each threshold, scores divided by the task's best IQM.
Run from sim/: env-an/bin/python analysis/e2.py  -> analysis/e2.json
"""
import itertools, json, sys
import numpy as np
from pineau_rl.bootstrap import iqm_interval, improvement_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
sys.path.insert(0, "analysis")
from runs import grid, out_json

G, missing = grid()
res = dict(missing=missing, tasks={})
for task, S in G.items():
    est = iqm_interval(S, reps=2000, random_state=RS)
    I = {a: est[a][0] for a in S}
    order = sorted(S, key=lambda a: -I[a])
    pairs = {}
    for a, b in itertools.combinations(order, 2):
        p, lo, hi = improvement_interval(S[a], S[b], reps=2000, random_state=RS)
        pairs[f"{a}>{b}"] = dict(p=p, ci=[lo, hi], settled=not (lo <= .5 <= hi))
    best = max(I.values())
    taus = np.linspace(0, 1.2, 25)
    res["tasks"][task] = dict(iqm=I, iqm_ci={a: list(est[a][1:]) for a in S}, order=order,
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
json.dump(res, open(out_json("e2"), "w"), indent=1)
