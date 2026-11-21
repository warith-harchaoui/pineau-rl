"""E5 checked out of sample (SIM_PROTOCOL.md, deviation 25, written before this computation).
E5's "right" order is the sign of the means of the very sample it draws from, with replacement. Here the order comes
from other runs. For the 24 comparisons of E2 (each program at its budget): the sign of the gap between means on seeds
0 to 9 against seeds 10 to 19 (kept or flipped; "close" when the relative gap on seeds 0 to 9 is under 20%, E5's
definition). Then P_n without circularity: n = 3, 5, 10 runs drawn WITHOUT replacement among seeds 0 to 9 (10,000
draws, default_rng(2026)), right when they give the order of the means of seeds 10 to 19; and the reverse direction.
Run from sim/: env-an/bin/python analysis/e5_holdout.py  -> analysis/e5_holdout.json
"""
import itertools, json, sys
import numpy as np
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, TASKS
from pineau_rl.runs import finals

rng = np.random.default_rng(2026)
NS, N = (3, 5, 10), 10000


def p_n(x, y, right, n):
    ix = rng.permuted(np.tile(np.arange(len(x)), (N, 1)), axis=1)[:, :n]
    iy = rng.permuted(np.tile(np.arange(len(y)), (N, 1)), axis=1)[:, :n]
    return float((np.sign(x[ix].mean(1) - y[iy].mean(1)) == right).mean())


comps = []
for task in TASKS:
    G = {a: finals(ROOT, a, task, range(20), FINAL[a], strict=True) for a in ALGOS}
    for a, b in itertools.combinations(sorted(ALGOS), 2):  # e5.py's order of the pairs
        x, y = G[a], G[b]
        s1 = np.sign(x[:10].mean() - y[:10].mean()); s2 = np.sign(x[10:].mean() - y[10:].mean())
        rel = abs(x[:10].mean() - y[:10].mean()) / max(abs(x[:10].mean()), abs(y[:10].mean()))
        comps.append(dict(task=task, pair=f"{a} vs {b}", rel_gap_0_9=float(rel), close=bool(rel < .2),
                          sign_kept=bool(s1 == s2),
                          p_n_from_0_9_judged_on_10_19={n: p_n(x[:10], y[:10], s2, n) for n in NS},
                          p_n_from_10_19_judged_on_0_9={n: p_n(x[10:], y[10:], s1, n) for n in NS}))
close = [c for c in comps if c["close"]]
med = lambda cs, k: {n: float(np.median([c[k][n] for c in cs])) for n in NS}
e5 = json.load(open("analysis/e5.json"))
res = dict(comparisons=comps, n=len(comps), signs_kept=sum(c["sign_kept"] for c in comps), n_close=len(close),
           signs_kept_close=sum(c["sign_kept"] for c in close),
           flipped=[f"{c['task']} {c['pair']}" for c in comps if not c["sign_kept"]],
           median_all={k: med(comps, k) for k in ("p_n_from_0_9_judged_on_10_19", "p_n_from_10_19_judged_on_0_9")},
           median_close={k: med(close, k) for k in ("p_n_from_0_9_judged_on_10_19", "p_n_from_10_19_judged_on_0_9")},
           mean_close={k: {n: float(np.mean([c[k][n] for c in close])) for n in NS}
                       for k in ("p_n_from_0_9_judged_on_10_19", "p_n_from_10_19_judged_on_0_9")},  # n = 10: share kept
           e5_preregistered=dict(median_all=e5["median_all"], median_close=e5["median_close"], n_close=e5["n_close"]))
print(f"signs kept {res['signs_kept']}/{res['n']}, close {res['signs_kept_close']}/{res['n_close']}; flipped {res['flipped']}")
print("median all", res["median_all"], "\nmedian close", res["median_close"], "\nmean close", res["mean_close"], "\nE5", res["e5_preregistered"])
json.dump(res, open("analysis/e5_holdout.json", "w"), indent=1)
