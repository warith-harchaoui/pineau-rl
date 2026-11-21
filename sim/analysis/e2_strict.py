"""E2, the strict count of settled changes of ranking (SIM_PROTOCOL.md, deviation 21, defect fixed; written before this
computation). The count of deviation 7 (e2.py: "settled_changes") takes every triple (task t led by X, task u, Y beating
X settled on u) without asking whether X beats Y on t. Strict definition: a pair (A, B) reverses, settled, when A beats
B settled on one task and B beats A settled on another. No new resample: the intervals are those already published,
at 95% (analysis/e2<suffix>.json) and at the simultaneous Bonferroni level of deviation 18
(analysis/e2_bonferroni<suffix>.json). The preregistered count is copied beside the strict one.
Run from sim/ after e2.py and e2_bonferroni.py with the same settings:
env-an/bin/python analysis/e2_strict.py  -> analysis/e2_strict.json  (SEEDS, BUDGET, SUFFIX as runs.py)
"""
import itertools, json, sys
sys.path.insert(0, "analysis")
from runs import ALGOS, out_json


def strict(res):
    """The pairs that reverse, settled, with the tasks and intervals on each side."""
    won = {}  # (winner, loser) -> [(task, p, ci)]
    for task, r in res["tasks"].items():
        for k, v in r["pairs"].items():
            if v["settled"]:
                a, b = k.split(">")
                w, l, p = (a, b, v["p"]) if v["p"] > .5 else (b, a, 1 - v["p"])
                ci = v["ci"] if v["p"] > .5 else [1 - v["ci"][1], 1 - v["ci"][0]]
                won.setdefault((w, l), []).append(dict(task=task, p=p, ci=ci))
    out = []
    for a, b in itertools.combinations(ALGOS, 2):
        if (a, b) in won and (b, a) in won:
            out.append(dict(pair=f"{a}/{b}", a_wins=won[(a, b)], b_wins=won[(b, a)]))
    return out


res = {}
for name, f in (("ci95", "e2"), ("bonferroni", "e2_bonferroni")):
    e = json.load(open(out_json(f)))
    pairs = strict(e)
    res[name] = dict(source=out_json(f), n_reversing_pairs=len(pairs), reversing_pairs=pairs,
                     leaders=e["leaders"], leader_changes=len(set(e["leaders"].values())) > 1,
                     n_settled_changes_preregistered=len(e["settled_changes"]))
    print(f"{name:10s} strict: {len(pairs)} pair(s) {[p['pair'] for p in pairs]}; "
          f"preregistered count: {len(e['settled_changes'])}; leaders {e['leaders']}")
json.dump(res, open(out_json("e2_strict"), "w"), indent=1)
