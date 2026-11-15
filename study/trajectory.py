"""A4 (PROTOCOL.md, deviation 25): the trajectory from 2018 to 2026 on classical RL.

Samples: our reading of 2018 (48 experimental papers, as extension_stats.py), the first 20 experimental `classic`
papers of each A4 year in queue order (codes_v2/M*), classical RL 2026 (50, as extension_stats.py). Harmonised values
(overrides.json, overrides_v2.json). Per criterion and year: share with Wilson interval. For Q5, Y9, X7, X2 and Q8:
Cochran-Armitage trend test over the six years (scores = the years), then Newcombe differences with Fisher's test,
2019-2020 pooled against 2018 (immediate effect) and 2022-2024 pooled against 2019-2020 (later effect), Holm over the
five criteria within each family.
Run from study/: ../sim/env-an/bin/python trajectory.py  -> trajectory.json
"""
import json, os
from pineau_rl.grid import list_readers, load_overrides, load_reads, tally, value
from pineau_rl.stats import cochran_armitage, compare as newcombe_fisher, holm, wilson_ci
from load import load

TESTED = ["Q5", "Y9", "X7", "X2", "Q8"]
SHOWN = TESTED + ["Q3", "Q4", "Q6", "Q7", "X4", "Y7"]
PER_YEAR = 20
ov1, ov2 = load_overrides("overrides.json"), load_overrides("overrides_v2.json")
OLD = load("ABCDEF")
# second readings and pilot left out, as extension_stats.py
V2 = load_reads("codes_v2", [d for d in list_readers("codes_v2") if d not in ("G2", "R2", "R3", "pilot")])


def val(pid, k):  # as extension_stats.py
    return value(pid, k, V2, OLD, ov2, ov1)


def count(ids, k):  # the samples are already experimental papers
    return tally(val(p, k) for p in ids)


EXCLUDE = set(os.environ.get("EXCLUDE", "").split(",")) - {""}  # deviation 29: papers left out, e.g. EXCLUDE=ML14,ML15
SUFFIX = os.environ.get("SUFFIX", "")  # deviation 29: the output becomes <name><SUFFIX>.json
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
S = {y: [p for p in s if p not in EXCLUDE] for y, s in S.items()}
YEARS = sorted(S)


def compare(a, b):
    return dict(a=list(a), b=list(b), **newcombe_fisher(a, b))


pool = lambda *ys: sum((S[y] for y in ys), [])
out = dict(sizes={y: len(S[y]) for y in YEARS}, rows={})
for k in SHOWN:
    c = {y: count(S[y], k) for y in YEARS}
    r = dict(by_year={y: dict(k=c[y][0], n=c[y][1], wilson=[float(x) for x in wilson_ci(*c[y])] if c[y][1] else None) for y in YEARS})
    if k in TESTED:
        z, p = cochran_armitage([c[y][0] for y in YEARS], [c[y][1] for y in YEARS], YEARS)
        r["trend"] = dict(z=z, p=p)
        r["immediate"] = compare(count(pool(2019, 2020), k), c[2018])
        r["later"] = compare(count(pool(2022, 2024), k), count(pool(2019, 2020), k))
    out["rows"][k] = r
for fam in ("trend", "immediate", "later"):
    for k, h in zip(TESTED, holm([out["rows"][k][fam]["p"] for k in TESTED])):
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
json.dump(out, open(f"trajectory{SUFFIX}.json", "w"), indent=1)
