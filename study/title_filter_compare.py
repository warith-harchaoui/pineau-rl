"""A6, step 2 (PROTOCOL.md, deviation 24): the 20 hidden RL papers, read with both grids by L1 and L2, against our
2026 samples, on the four criteria that changed (Q5, Y9, X7, X2). Descriptive: shares with Wilson intervals, among
experimental papers, for the hidden papers, then for the first 2026 draw (all families) and for classic RL 2026.
Run from study/: ../sim/env-an/bin/python title_filter_compare.py  -> title_filter_compare.json
"""
import glob, json
from statsmodels.stats.proportion import proportion_confint

CRIT = ["Q5", "Y9", "X7", "X2"]
ext = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}
hidden = [json.load(open(f)) for d in ("L1", "L2") for f in sorted(glob.glob(f"codes_v2/{d}/*.json"))]
assert len(hidden) == 20, len(hidden)
ov = {k: x for k, x in json.load(open("overrides_v2.json")).items() if not k.startswith("_")}
v = lambda r, k: ov.get(k, {}).get(r["id"], r["criteria"][k]["value"])  # harmonised, as extension_stats.py
exp = [r for r in hidden if v(r, "Q1") != "no"]
fam = {f: sum(v(r, "X5") == f for r in hidden) for f in ("llm", "classic", "theory")}
ci = lambda k, n: [float(x) for x in proportion_confint(k, n, method="wilson")] if n else None
out = dict(n=len(hidden), experimental=len(exp), families=fam, rows={})
for k in CRIT:
    vs = [v(r, k) for r in exp if v(r, k) in ("yes", "no")]
    h = (sum(x == "yes" for x in vs), len(vs))
    out["rows"][k] = dict(hidden=h, hidden_wilson=ci(*h), all2026=ext[k]["all2026"], classic2026=ext[k]["classic2026"])
    a, c = ext[k]["all2026"], ext[k]["classic2026"]
    print(f"{k}: hidden {h[0]}/{h[1]} ({h[0] / h[1]:.0%})  first 2026 draw {a[0]}/{a[1]} ({a[0] / a[1]:.0%})  classic 2026 {c[0]}/{c[1]} ({c[0] / c[1]:.0%})")
print("families", fam, " experimental", len(exp))
json.dump(out, open("title_filter_compare.json", "w"), indent=1)
