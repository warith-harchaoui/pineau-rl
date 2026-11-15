"""Analysis of the extended survey (PROTOCOL.md, écart 12), written on 9 November 2026 before any reading of the
extension was aggregated.

Samples, all restricted to experimental papers (Q1 not "no"):
  - ours 2018: the 12 calibration papers (v1 in codes/F, v2 in codes_v2/F2) and the 38 of A2 (codes_v2/H*);
  - classic 2026: the 14 classic papers of the first sample (v1 in codes/A-E, v2 in codes_v2/A2-E2) and the
    first 36 papers of the A3 queue that the reader codes `classic`, in queue order (codes_v2/K*);
  - all 2026: the 50 papers of the first sample.
The A3 papers coded `llm` or `theory` are counted apart: the title screen filtered them, so they are not a sample.
Values: raw reads of the primary reader, then the harmonisation of overrides.json (v1, first sample) and of
overrides_v2.json (everything read in codes_v2), as in audit_stats.py. Y3 is turned into yes when at least 2.

Tests, as in audit_stats.py: difference with Newcombe's interval, Fisher's exact test, Holm's correction.
Main comparison: classic 2026 against ours 2018, Holm over the v1 criteria and, separately, over the v2 criteria.
Secondary: all 2026 against Pineau, and ours 2018 against Pineau (how far our grid is from hers), Holm over
Q3 to Q8 within each.
Run from study/: ../sim/env-an/bin/python extension_stats.py  -> extension_stats.json
"""
import json, os
from pineau_rl.grid import list_readers, load_overrides, load_reads, tally, value
from pineau_rl.stats import compare as newcombe_fisher, holm, wilson_ci
from load import load

PINEAU = {"Q3": .90, "Q4": .60, "Q5": .55, "Q6": .20, "Q7": .10, "Q8": .05}
V1 = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
V2 = ["Y%d" % i for i in range(1, 13)]
PRIMARY = ["A2", "B2", "C2", "D2", "E2", "F2", "H1", "H2", "H3", "H4"]  # K* added below; G2, R2, pilot excluded
N_A3 = 36
EXCLUDE = set(os.environ.get("EXCLUDE", "").split(",")) - {""}  # deviation 29: papers left out, e.g. EXCLUDE=ML14,ML15
SUFFIX = os.environ.get("SUFFIX", "")  # deviation 29: the output becomes <name><SUFFIX>.json

ov1, ov2 = load_overrides("overrides.json", missing_ok=True), load_overrides("overrides_v2.json", missing_ok=True)
OLD = load("ABCDEF")
V2READ = load_reads("codes_v2", PRIMARY + list_readers("codes_v2", "K*"))


def val(pid, k):  # the v2 reading when it has k, else v1; harmonised; Y3 as yes/no; None for an unknown paper
    return value(pid, k, V2READ, OLD, ov2, ov1)


def count(ids, k):
    return tally(val(p, k) for p in ids if val(p, "Q1") != "no")


def compare(a, b):  # {diff, lo, hi, p}: Newcombe's interval and Fisher's p; None when a side is empty
    return newcombe_fisher(a, b) if a[1] and b[1] else None


ours18 = sorted(p for p in OLD if p.startswith("C")) + [x["id"] for x in json.load(open("calib_2018_v2.json"))[12:]]
all26 = sorted(p for p in OLD if not p.startswith("C"))
queue = [x["id"] for x in json.load(open("classic_queue_2026.json"))]
read_a3 = [p for p in queue if p in V2READ]
a3 = [p for p in read_a3 if val(p, "X5") == "classic"][:N_A3]
apart = {f: [p for p in read_a3[:read_a3.index(a3[-1]) + 1] if val(p, "X5") == f] for f in ("llm", "theory")} if a3 else {}
classic26 = sorted(p for p in all26 if val(p, "X5") == "classic") + a3
ours18, classic26, all26 = ([p for p in s if p not in EXCLUDE] for s in (ours18, classic26, all26))
missing = [p for p in ours18 + classic26 if val(p, "Q1") is None]

rows = []
for k in V1 + V2:
    o, c, a = count(ours18, k), count(classic26, k), count(all26, k)
    r = dict(k=k, ours2018=o, classic2026=c, all2026=a,
             wilson_classic2026=[float(x) for x in wilson_ci(*c)] if c[1] else None,
             wilson_ours2018=[float(x) for x in wilson_ci(*o)] if o[1] else None,
             classic_vs_ours2018=compare(c, o))
    if k in PINEAU:
        pin = (round(PINEAU[k] * 50), 50)
        r["pineau2018"] = pin
        r["all2026_vs_pineau"] = compare(a, pin)
        r["ours2018_vs_pineau"] = compare(o, pin)
    rows.append(r)
for key, crit in (("classic_vs_ours2018", V1), ("classic_vs_ours2018", V2),
                  ("all2026_vs_pineau", list(PINEAU)), ("ours2018_vs_pineau", list(PINEAU))):
    sel = [r for r in rows if r["k"] in crit and r.get(key)]
    for r, h in zip(sel, holm([r[key]["p"] for r in sel])):
        r[key]["p_holm"] = float(h)

out = dict(samples=dict(ours2018=len(ours18), classic2026=len(classic26), a3=a3, a3_read=len(read_a3),
                        a3_apart={f: len(v) for f, v in apart.items()}, missing=missing), rows=rows)
json.dump(out, open(f"extension_stats{SUFFIX}.json", "w"), indent=1)
print(f"ours 2018: {len(ours18)}  classic 2026: {len(classic26)} ({len(a3)} from A3, {len(read_a3)} read)  "
      f"apart: {out['samples']['a3_apart']}  missing: {missing}")
for r in rows:
    c = r["classic_vs_ours2018"]
    print(f"{r['k']:4s} 2018 {r['ours2018'][0]}/{r['ours2018'][1]}  classic 2026 {r['classic2026'][0]}/{r['classic2026'][1]}"
          + (f"  diff {c['diff']*100:+.0f} [{c['lo']*100:+.0f}, {c['hi']*100:+.0f}] Holm p {c.get('p_holm', float('nan')):.3g}" if c else ""))
