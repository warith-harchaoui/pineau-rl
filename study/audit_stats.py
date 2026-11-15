"""Statistical audit of the grid comparison (2018 against 2026), stricter than analyze.py.

analyze.py compares our 2026 Wilson interval with Pineau's 2018 share taken as exact. Her share also comes
from a sample (50 papers), and our own 2018 reading from 12. This script tests the difference itself:
Newcombe's interval for p2026 - p2018, Fisher's exact test, and a Holm correction over the criteria tested
together. It also splits 2026 by family, because 2018 has no paper of RL on large language models: a change
that exists only through the llm papers is a change of population, not of practice.

Run with the analysis environment: ../sim/env-an/bin/python audit_stats.py  -> audit_stats.json
"""
import json
from pineau_rl.grid import load_overrides, tally, value_v1
from pineau_rl.stats import cohen_kappa, compare, holm, wilson_ci
from load import load

PINEAU = {"Q3": .90, "Q4": .60, "Q5": .55, "Q6": .20, "Q7": .10, "Q8": .05}  # 50 papers, all experimental
CRIT = ["Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
ov = load_overrides("overrides.json")


def val(d, k):  # v1 only: this reading and overrides.json
    return value_v1(d, k, ov)


def count(D, k):
    """yes / applicable among experimental papers (Q1 yes), as in analyze.py."""
    return tally(val(d, k) for d in D.values() if val(d, "Q1") != "no")


# compare(a, b) of pineau_rl.stats, a, b = (k, n): difference a - b with Newcombe's interval and Fisher's exact p,
# at full precision (round only when printing)


D26 = load("ABCDE")
D18 = load("F")
fam = {}
for i, d in D26.items():
    fam.setdefault(val(d, "X5"), {})[i] = d

rows, tests = [], {"vs_pineau": [], "vs_ours2018": [], "classic_vs_pineau": [], "classic_vs_ours2018": []}
for k in CRIT:
    a, c, l, o = count(D26, k), count(fam["classic"], k), count(fam["llm"], k), count(D18, k)
    r = dict(k=k, all2026=a, classic2026=c, llm2026=l, ours2018=o,
             wilson2026=[float(x) for x in wilson_ci(*a)])
    if k in PINEAU:
        pin = (round(PINEAU[k] * 50), 50)
        r["pineau2018"] = pin
        r["vs_pineau"] = compare(a, pin); tests["vs_pineau"].append((k, r["vs_pineau"]))
        r["classic_vs_pineau"] = compare(c, pin); tests["classic_vs_pineau"].append((k, r["classic_vs_pineau"]))
    if o[1]:
        r["vs_ours2018"] = compare(a, o); tests["vs_ours2018"].append((k, r["vs_ours2018"]))
        r["classic_vs_ours2018"] = compare(c, o); tests["classic_vs_ours2018"].append((k, r["classic_vs_ours2018"]))
    rows.append(r)

# Holm within each family of comparisons.
for name, ts in tests.items():
    adj = holm([t["p"] for _, t in ts])
    for (k, t), pa in zip(ts, adj):
        t["p_holm"] = round(float(pa), 4); t["p"] = round(float(t["p"]), 4)

# Inter-reader agreement on the 10 double-read papers, criterion by criterion, with Cohen's kappa, on the raw
# reads: the harmonisation of overrides.json applies to both reads and would inflate agreement.
G = load("G")
agree = {}
for k in ["Q1", "Q2"] + CRIT + ["X5"]:
    raw = lambda d: d["criteria"].get(k, {}).get("value")  # before harmonisation: overrides would equalise both reads
    pairs = [(raw(D26[i]), raw(G[i])) for i in G if i in D26]
    same = sum(x == y for x, y in pairs)
    cats = sorted({x for p in pairs for x in p if x is not None}, key=str)  # chance agreement summed without None
    kappa = cohen_kappa([x for x, _ in pairs], [y for _, y in pairs], categories=cats)
    agree[k] = dict(same=same, n=len(pairs), kappa=None if kappa is None else round(kappa, 2))

json.dump(dict(rows=rows, agreement=agree), open("audit_stats.json", "w"), indent=1, ensure_ascii=False)
for r in rows:
    line = f"{r['k']}: 2026 {r['all2026']} classic {r['classic2026']} llm {r['llm2026']} ours2018 {r['ours2018']}"
    for name in tests:
        if name in r:
            t = r[name]
            line += f" | {name} {t['diff']:+.2f} [{t['lo']:+.2f},{t['hi']:+.2f}] p={t['p']} holm={t['p_holm']}"
    print(line)
print("agreement", {k: (v["same"], v["n"], v["kappa"]) for k, v in agree.items()})
