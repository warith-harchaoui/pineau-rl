"""Agreement between readers on the v2 grid (and on v1 for papers read with both), on raw reads, before any
harmonisation (PROTOCOL.md, écart 12, as in audit_stats.py for v1).

Pairs: G2 against the primary reader of the 10 first-sample papers it re-read; R2 (if present) against the
primary reader of the 10 new papers drawn by random.Random(7). Per criterion: share of identical values among
papers where both readers gave yes/no (Y3 turned into yes when at least 2), and Cohen's kappa when both
readers vary. A criterion under 70% agreement is flagged as fragile.
Run from study/: ../sim/env-an/bin/python agree_v2.py  -> agree_v2.json
"""
import json
from pineau_rl.grid import list_readers, load_reads, y3_yes_no
from pineau_rl.stats import cohen_kappa

CRIT = ["Q%d" % i for i in range(2, 9)] + ["X2", "X3", "X4", "X7"] + ["Y%d" % i for i in range(1, 13)]
SECOND = ["G2", "R2", "R3"]  # R3: A4 (deviation 26)


def reads(d):
    return {i: r["criteria"] for i, r in load_reads("codes_v2", [d]).items()}


def yn(c, k):  # raw read, no harmonisation
    v = c.get(k, {}).get("value")
    if k == "Y3" and v is not None:
        return y3_yes_no(v)
    return v if v in ("yes", "no") else None


primary = {}
for d in list_readers("codes_v2"):
    if d not in SECOND and d != "pilot":
        primary.update(reads(d))
out = {}
for s in SECOND:
    sec = reads(s)
    if not sec:
        continue
    rows = {}
    for k in CRIT:
        pairs = [(yn(primary[p], k), yn(c, k)) for p, c in sec.items() if p in primary]
        pairs = [(a, b) for a, b in pairs if a and b]
        if not pairs:
            continue
        agree = sum(a == b for a, b in pairs) / len(pairs)
        a, b = zip(*pairs)
        kappa = cohen_kappa(list(a), list(b)) if len(set(a)) > 1 and len(set(b)) > 1 else None
        rows[k] = dict(n=len(pairs), agree=agree, kappa=kappa, fragile=agree < .7)
    out[s] = dict(papers=sorted(sec), criteria=rows)
    print(s, len(sec), "papers")
    for k, r in rows.items():
        print(f"  {k:4s} {r['agree']*100:5.0f}% of {r['n']}" + (f"  kappa {r['kappa']:.2f}" if r["kappa"] is not None else "")
              + ("  FRAGILE" if r["fragile"] else ""))
json.dump(out, open("agree_v2.json", "w"), indent=1)
