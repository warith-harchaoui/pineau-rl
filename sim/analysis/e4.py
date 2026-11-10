"""E4, as pre-registered (SIM_PROTOCOL.md, écart 7): keeping the 3 best runs out of 10. For each algorithm and task,
mean and standard deviation of the 10 runs, then of the 3 best; a comparison (pair of algorithms on one task)
"reverses" when the sign of the gap between means changes once each algorithm keeps only its 3 best.
Run from sim/: env-an/bin/python analysis/e4.py  -> analysis/e4.json
"""
import itertools, json, sys
import numpy as np
sys.path.insert(0, "analysis")
from runs import grid

G, missing = grid()
cells, comps = {}, []
for task, S in G.items():
    for a, x in S.items():
        top = np.sort(x)[-3:]
        cells[f"{a}/{task}"] = dict(mean10=float(x.mean()), sd10=float(x.std(ddof=1)), mean3=float(top.mean()),
                                    sd3=float(top.std(ddof=1)), inflation=float(top.mean() / x.mean() - 1))
    for a, b in itertools.combinations(sorted(S), 2):
        d10, d3 = S[a].mean() - S[b].mean(), np.sort(S[a])[-3:].mean() - np.sort(S[b])[-3:].mean()
        comps.append(dict(task=task, pair=f"{a} vs {b}", gap10=float(d10), gap3=float(d3), reversed=bool(np.sign(d10) != np.sign(d3))))
inf = [c["inflation"] for c in cells.values()]
res = dict(missing=missing, cells=cells, comparisons=comps, n_comparisons=len(comps),
           n_reversed=sum(c["reversed"] for c in comps), inflation_median=float(np.median(inf)),
           inflation_range=[float(min(inf)), float(max(inf))],
           sd_shrink_median=float(np.median([c["sd3"] / c["sd10"] for c in cells.values()])))
print(f"{res['n_reversed']} of {res['n_comparisons']} comparisons reverse; mean inflated by {res['inflation_median']:.0%} "
      f"(median, range {min(inf):.0%} to {max(inf):.0%}); sd shrinks to {res['sd_shrink_median']:.0%}; missing {missing}")
json.dump(res, open("analysis/e4.json", "w"), indent=1)
