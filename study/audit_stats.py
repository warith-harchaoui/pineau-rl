"""Statistical audit of the grid comparison (2018 against 2026), stricter than analyze.py.

analyze.py compares our 2026 Wilson interval with Pineau's 2018 share taken as exact. Her share also comes
from a sample (50 papers), and our own 2018 reading from 12. This script tests the difference itself:
Newcombe's interval for p2026 - p2018, Fisher's exact test, and a Holm correction over the criteria tested
together. It also splits 2026 by family, because 2018 has no paper of RL on large language models: a change
that exists only through the llm papers is a change of population, not of practice.

Run with the analysis environment: ../sim/env-an/bin/python audit_stats.py  -> audit_stats.json
"""
import json
from scipy.stats import fisher_exact
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint
from statsmodels.stats.multitest import multipletests
from load import load

PINEAU = {"Q3": .90, "Q4": .60, "Q5": .55, "Q6": .20, "Q7": .10, "Q8": .05}  # 50 papers, all experimental
CRIT = ["Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
ov = {k: v for k, v in json.load(open("overrides.json")).items() if not k.startswith("_")}


def val(d, k):
    v = d["criteria"].get(k, {}).get("value")
    return ov.get(k, {}).get(d["id"], v)


def count(D, k):
    """yes / applicable among experimental papers (Q1 yes), as in analyze.py."""
    vs = [val(d, k) for d in D.values() if val(d, "Q1") != "no"]
    vs = [v for v in vs if v in ("yes", "no")]
    return sum(v == "yes" for v in vs), len(vs)


def compare(a, b):
    """a, b = (k, n). Difference a - b with Newcombe's interval and Fisher's exact p."""
    (ka, na), (kb, nb) = a, b
    lo, hi = confint_proportions_2indep(ka, na, kb, nb, method="newcomb", compare="diff")
    p = fisher_exact([[ka, na - ka], [kb, nb - kb]])[1]
    return dict(diff=round(ka / na - kb / nb, 3), lo=round(lo, 3), hi=round(hi, 3), p=p)


D26 = load("ABCDE")
D18 = load("F")
fam = {}
for i, d in D26.items():
    fam.setdefault(val(d, "X5"), {})[i] = d

rows, tests = [], {"vs_pineau": [], "vs_ours2018": [], "classic_vs_pineau": [], "classic_vs_ours2018": []}
for k in CRIT:
    a, c, l, o = count(D26, k), count(fam["classic"], k), count(fam["llm"], k), count(D18, k)
    r = dict(k=k, all2026=a, classic2026=c, llm2026=l, ours2018=o,
             wilson2026=[round(x, 3) for x in proportion_confint(*a, method="wilson")])
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
    adj = multipletests([t["p"] for _, t in ts], method="holm")[1]
    for (k, t), pa in zip(ts, adj):
        t["p_holm"] = round(float(pa), 4); t["p"] = round(float(t["p"]), 4)

# Inter-reader agreement on the 10 double-read papers, criterion by criterion, with Cohen's kappa.
G = load("G")
agree = {}
for k in ["Q1", "Q2"] + CRIT + ["X5"]:
    pairs = [(val(D26[i], k), val(G[i], k)) for i in G if i in D26]
    same = sum(x == y for x, y in pairs)
    cats = sorted({x for p in pairs for x in p if x is not None}, key=str)
    n = len(pairs)
    po = same / n
    pe = sum((sum(x == c for x, _ in pairs) / n) * (sum(y == c for _, y in pairs) / n) for c in cats)
    agree[k] = dict(same=same, n=n, kappa=None if pe == 1 else round((po - pe) / (1 - pe), 2))

json.dump(dict(rows=rows, agreement=agree), open("audit_stats.json", "w"), indent=1, ensure_ascii=False)
for r in rows:
    line = f"{r['k']}: 2026 {r['all2026']} classic {r['classic2026']} llm {r['llm2026']} ours2018 {r['ours2018']}"
    for name in tests:
        if name in r:
            t = r[name]
            line += f" | {name} {t['diff']:+.2f} [{t['lo']:+.2f},{t['hi']:+.2f}] p={t['p']} holm={t['p_holm']}"
    print(line)
print("agreement", {k: (v["same"], v["n"], v["kappa"]) for k, v in agree.items()})
