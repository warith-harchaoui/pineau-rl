"""A4 (PROTOCOL.md, deviation 25): the trajectory from 2018 to 2026 on classical RL.

Samples: our reading of 2018 (48 experimental papers, as extension_stats.py), the first 20 experimental `classic`
papers of each A4 year in queue order (codes_v2/M*), classical RL 2026 (50, as extension_stats.py). Harmonised values
(overrides.json, overrides_v2.json). Per criterion and year: share with Wilson interval. For Q5, Y9, X7, X2 and Q8:
Cochran-Armitage trend test over the six years (scores = the years), then Newcombe differences with Fisher's test,
2019-2020 pooled against 2018 (immediate effect) and 2022-2024 pooled against 2019-2020 (later effect), Holm over the
five criteria within each family.
Run from study/: ../sim/env-an/bin/python trajectory.py  -> trajectory.json
"""
import glob, json, math, os
from scipy.stats import fisher_exact, norm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint
from load import load

TESTED = ["Q5", "Y9", "X7", "X2", "Q8"]
SHOWN = TESTED + ["Q3", "Q4", "Q6", "Q7", "X4", "Y7"]
PER_YEAR = 20
ld = lambda f: {k: v for k, v in json.load(open(f)).items() if not k.startswith("_")}
ov1, ov2 = ld("overrides.json"), ld("overrides_v2.json")
OLD = load("ABCDEF")
V2 = {}
for d in sorted(os.path.basename(x) for x in glob.glob("codes_v2/*")):
    if d in ("G2", "R2", "R3", "pilot"):
        continue  # second readings and pilot, as extension_stats.py
    for f in glob.glob(f"codes_v2/{d}/*.json"):
        r = json.load(open(f)); V2[r["id"]] = r


def val(pid, k):  # as extension_stats.py
    if pid in V2 and k in V2[pid]["criteria"]:
        v = ov2.get(k, {}).get(pid, V2[pid]["criteria"][k].get("value"))
    elif pid in OLD:
        v = ov1.get(k, {}).get(pid, OLD[pid]["criteria"].get(k, {}).get("value"))
    else:
        return None
    if k == "Y3" and v is not None:
        return "yes" if v >= 2 else "no"
    return v


def count(ids, k):
    vs = [val(p, k) for p in ids]
    vs = [v for v in vs if v in ("yes", "no")]
    return sum(v == "yes" for v in vs), len(vs)


ext = json.load(open("extension_stats.json"))["samples"]
ours18 = sorted(p for p in OLD if p.startswith("C")) + [x["id"] for x in json.load(open("calib_2018_v2.json"))[12:]]
ours18 = [p for p in ours18 if val(p, "Q1") != "no"]
classic26 = sorted(p for p in OLD if not p.startswith("C") and val(p, "X5") == "classic") + ext["a3"]
queue = json.load(open("trajectory_queue.json"))
S = {2018: ours18}
for y, d in queue.items():
    coded = [p["id"] for p in d["queue"] if p["id"] in V2]
    S[int(y)] = [p for p in coded if val(p, "X5") == "classic" and val(p, "Q1") != "no"][:PER_YEAR]
S[2026] = classic26
YEARS = sorted(S)


def cochran_armitage(k, n, x):
    N, K = sum(n), sum(k)
    p = K / N
    xbar = sum(xi * ni for xi, ni in zip(x, n)) / N
    t = sum(xi * (ki - ni * p) for xi, ki, ni in zip(x, k, n))
    v = p * (1 - p) * sum(ni * (xi - xbar) ** 2 for xi, ni in zip(x, n))
    z = t / math.sqrt(v) if v else 0.0
    return z, 2 * norm.sf(abs(z))


def compare(a, b):
    (ka, na), (kb, nb) = a, b
    lo, hi = confint_proportions_2indep(ka, na, kb, nb, method="newcomb", compare="diff")
    return dict(a=[ka, na], b=[kb, nb], diff=ka / na - kb / nb, lo=float(lo), hi=float(hi),
                p=float(fisher_exact([[ka, na - ka], [kb, nb - kb]])[1]))


pool = lambda *ys: sum((S[y] for y in ys), [])
out = dict(sizes={y: len(S[y]) for y in YEARS}, rows={})
for k in SHOWN:
    c = {y: count(S[y], k) for y in YEARS}
    r = dict(by_year={y: dict(k=c[y][0], n=c[y][1], wilson=[float(x) for x in proportion_confint(*c[y], method="wilson")] if c[y][1] else None) for y in YEARS})
    if k in TESTED:
        z, p = cochran_armitage([c[y][0] for y in YEARS], [c[y][1] for y in YEARS], YEARS)
        r["trend"] = dict(z=z, p=p)
        r["immediate"] = compare(count(pool(2019, 2020), k), c[2018])
        r["later"] = compare(count(pool(2022, 2024), k), count(pool(2019, 2020), k))
    out["rows"][k] = r
for fam in ("trend", "immediate", "later"):
    for k, h in zip(TESTED, multipletests([out["rows"][k][fam]["p"] for k in TESTED], method="holm")[1]):
        out["rows"][k][fam]["p_holm"] = float(h)
print("sizes", out["sizes"])
for k in SHOWN:
    r = out["rows"][k]
    line = "  ".join(f"{y}: {r['by_year'][y]['k']}/{r['by_year'][y]['n']}" for y in YEARS)
    if k in TESTED:
        line += (f" | trend z {r['trend']['z']:+.2f} Holm p {r['trend']['p_holm']:.3g}"
                 f" | 19-20 vs 18 {r['immediate']['diff']:+.0%} Holm p {r['immediate']['p_holm']:.3g}"
                 f" | 22-24 vs 19-20 {r['later']['diff']:+.0%} Holm p {r['later']['p_holm']:.3g}")
    print(k, line)
json.dump(out, open("trajectory.json", "w"), indent=1)
