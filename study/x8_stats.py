"""Criterion X8, uncertainty computed over independent training runs (PROTOCOL.md, deviation 32): the result.

Readings in codes_x8/S1..S6 (primary) and S7, S8 (double reading of 20 papers, 5 + 5 each), lists in assignments_x8.json.
Main measure: share of experimental papers whose main uncertainty is over seeds (X2 no counts as no), classical RL 2026
against our 2018, Newcombe and Fisher, alone, then with Holm over the 11 v1 criteria plus X8 (the 11 p-values of
extension_stats.json). Beside it: the share among X2 yes; the same with source "pooled" counted yes; the lower bound of
survey_extra.json (deviation 30 e). Agreement of the double readings (raw reads): Wilson and bootstrap kappa
(10,000 resamples, default_rng(2032)), per year.
Run from study/: ../sim/env-an/bin/python x8_stats.py  -> x8_stats.json
"""
import json
import numpy as np
from pineau_rl.grid import iter_reads
from pineau_rl.stats import cohen_kappa, compare, holm, wilson_ci
from samples import classic26, experimental, ours18, val

V1 = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
asg = json.load(open("assignments_x8.json"))
prim = {r["id"]: r for _, r in iter_reads("codes_x8", [f"S{i}" for i in range(1, 7)])}
sec = {r["id"]: r for _, r in iter_reads("codes_x8", ["S7", "S8"])}
assert set(prim) == set(asg["_years"]["2018"] + asg["_years"]["2026"]), "primary readings incomplete"


def r6(x):
    return None if x is None else round(float(x), 6)


def x8(pid, pooled_yes=False, src=prim):
    if val(pid, "X2") != "yes":
        return "no"
    c = src[pid]["criteria"]["X8"]
    return "yes" if c["value"] == "yes" or (pooled_yes and c["source"] == "pooled") else "no"


res = {}
for name, kw in (("main", {}), ("pooled_yes", dict(pooled_yes=True))):
    cnt = {}
    for year, ids in (("2018", experimental(ours18)), ("2026", experimental(classic26))):
        e = [p for p in ids if val(p, "X2") in ("yes", "no")]
        k = sum(x8(p, **kw) == "yes" for p in e)
        kx2 = sum(val(p, "X2") == "yes" for p in e)
        cnt[year] = dict(yes=k, n=len(e), share=r6(k / len(e)), wilson=[r6(v) for v in wilson_ci(k, len(e))],
                         x2_yes=kx2, share_of_x2=r6(k / kx2), wilson_of_x2=[r6(v) for v in wilson_ci(k, kx2)])
    c = compare((cnt["2026"]["yes"], cnt["2026"]["n"]), (cnt["2018"]["yes"], cnt["2018"]["n"]))
    cx2 = compare((cnt["2026"]["yes"], cnt["2026"]["x2_yes"]), (cnt["2018"]["yes"], cnt["2018"]["x2_yes"]))
    res[name] = dict(counts=cnt, diff={a: r6(b) for a, b in c.items()}, diff_among_x2={a: r6(b) for a, b in cx2.items()})
ext = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}
ps = [ext[k]["classic_vs_ours2018"]["p"] for k in V1] + [res["main"]["diff"]["p"]]
res["main"]["p_holm_12"] = r6(holm(ps)[-1])
res["sources"] = {y: {s: sum(prim[p]["criteria"]["X8"]["source"] == s for p in asg["_years"][y])
                      for s in ("seeds", "pooled", "episodes", "items", "unstated", "other")} for y in ("2018", "2026")}

rng = np.random.default_rng(2032)
agree = {}
for year in ("all", "2018", "2026"):
    ids = sorted(p for p in sec if year == "all" or p in asg["_years"][year])
    a = [prim[p]["criteria"]["X8"]["value"] for p in ids]
    b = [sec[p]["criteria"]["X8"]["value"] for p in ids]
    same = sum(x == y for x, y in zip(a, b))
    k = cohen_kappa(a, b) if len(set(a)) > 1 and len(set(b)) > 1 else None
    boot, und = [], 0
    if k is not None:
        A, Bv = np.array(a), np.array(b)
        for _ in range(10_000):
            i = rng.integers(0, len(ids), len(ids))
            kk = cohen_kappa(list(A[i]), list(Bv[i]))
            if kk is None:
                und += 1
            else:
                boot.append(kk)
    agree[year] = dict(n=len(ids), same=same, agree=r6(same / len(ids)), wilson=[r6(v) for v in wilson_ci(same, len(ids))],
                       kappa=r6(k), kappa_boot95=[r6(np.percentile(boot, 2.5)), r6(np.percentile(boot, 97.5))] if boot else None,
                       boot_undefined=und, disagreements=[p for p, x, y in zip(ids, a, b) if x != y])
res["double_reading"] = agree
res["lower_bound_deviation30e"] = json.load(open("survey_extra.json"))["seeds_lower_bound"]["diff_experimental"]
json.dump(res, open("x8_stats.json", "w"), indent=1)
for name in ("main", "pooled_yes"):
    r = res[name]
    print(name, {y: (r["counts"][y]["yes"], r["counts"][y]["n"], r["counts"][y]["x2_yes"]) for y in ("2018", "2026")},
          "diff", r["diff"], "among X2", r["diff_among_x2"])
print("Holm over 12:", res["main"]["p_holm_12"])
print("sources:", res["sources"])
print("agreement:", agree)
