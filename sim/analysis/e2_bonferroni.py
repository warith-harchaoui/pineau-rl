"""E2 with simultaneous intervals (SIM_PROTOCOL.md, deviation 18, written before this computation): the 24 probability-
of-improvement intervals of e2.py (6 pairs on 4 tasks) at 1 - 0.05/24 each (Bonferroni), so that all 24 hold together
at 95%. The same calls in the same order as e2.py after the same seed, hence the same bootstrap resamples: only the
percentile level changes. "Settled" when the interval excludes 0.5; a settled change of ranking as in e2.py.
Run from sim/: env-an/bin/python analysis/e2_bonferroni.py  -> analysis/e2_bonferroni.json
"""
import itertools, json, sys
import numpy as np
from pineau_rl.bootstrap import iqm_interval, improvement_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
sys.path.insert(0, "analysis")
from runs import grid, out_json

G, missing = grid()
assert not missing
n_comp = sum(len(list(itertools.combinations(S, 2))) for S in G.values())
level = 1 - 0.05 / n_comp
res = dict(n_comparisons=n_comp, level=level, tasks={})
for task, S in G.items():
    est = iqm_interval(S, reps=2000, random_state=RS)  # as e2.py, so that the pair resamples below are the same
    I = {a: est[a][0] for a in S}
    order = sorted(S, key=lambda a: -I[a])
    pairs = {}
    for a, b in itertools.combinations(order, 2):
        p, lo, hi = improvement_interval(S[a], S[b], reps=2000, random_state=RS, confidence=level)
        pairs[f"{a}>{b}"] = dict(p=p, ci=[lo, hi], settled=not (lo <= .5 <= hi))
    res["tasks"][task] = dict(order=order, pairs=pairs)
    print(task, " settled:", [k for k, v in pairs.items() if v["settled"]])
leaders = {t: r["order"][0] for t, r in res["tasks"].items()}
res["leaders"] = leaders
res["settled_changes"] = [f"{leaders[t]} leads {t} but loses to {k.split('>')[0]} on {u}"
                          for t in leaders for u, r in res["tasks"].items() if u != t
                          for k, v in r["pairs"].items() if v["settled"] and k.split(">")[1] == leaders[t]]
print(f"{n_comp} comparisons at {level:.4f} each; settled changes:", len(res["settled_changes"]))
json.dump(res, open(out_json("e2_bonferroni"), "w"), indent=1)
