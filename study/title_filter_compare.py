"""A6, step 2 (PROTOCOL.md, deviation 24): the 20 hidden RL papers, read with both grids by L1 and L2, against our
2026 samples, on the four criteria that changed (Q5, Y9, X7, X2). Descriptive: shares with Wilson intervals, among
experimental papers, for the hidden papers, then for the first 2026 draw (all families) and for classic RL 2026.
Run from study/: ../sim/env-an/bin/python title_filter_compare.py  -> title_filter_compare.json
"""
import json
from pineau_rl.grid import iter_reads, load_overrides, value_v1
from pineau_rl.stats import wilson_ci

CRIT = ["Q5", "Y9", "X7", "X2"]
ext = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}
hidden = [r for _, r in iter_reads("codes_v2", ("L1", "L2"))]
assert len(hidden) == 20, len(hidden)
ov = load_overrides("overrides_v2.json")
v = lambda r, k: value_v1(r, k, ov, strict=True)  # this reading, harmonised by overrides_v2.json (KeyError if k is absent)
exp = [r for r in hidden if v(r, "Q1") != "no"]
fam = {f: sum(v(r, "X5") == f for r in hidden) for f in ("llm", "classic", "theory")}
ci = lambda k, n: [float(x) for x in wilson_ci(k, n)] if n else None
out = dict(n=len(hidden), experimental=len(exp), families=fam, rows={})
for k in CRIT:
    vs = [v(r, k) for r in exp if v(r, k) in ("yes", "no")]
    h = (sum(x == "yes" for x in vs), len(vs))
    out["rows"][k] = dict(hidden=h, hidden_wilson=ci(*h), all2026=ext[k]["all2026"], classic2026=ext[k]["classic2026"])
    a, c = ext[k]["all2026"], ext[k]["classic2026"]
    print(f"{k}: hidden {h[0]}/{h[1]} ({h[0] / h[1]:.0%})  first 2026 draw {a[0]}/{a[1]} ({a[0] / a[1]:.0%})  classic 2026 {c[0]}/{c[1]} ({c[0] / c[1]:.0%})")
print("families", fam, " experimental", len(exp))
json.dump(out, open("title_filter_compare.json", "w"), indent=1)
