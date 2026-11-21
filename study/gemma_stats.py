"""A reader from another model family (PROTOCOL.md, deviation 33): the result, on the papers gemma_reader.py has read.

Per criterion (Q5, X2, X7, Y9) and year: agreement of Gemma's valid decisions with the final codes (harmonised), Wilson
interval, Cohen's kappa with a percentile bootstrap over papers (10,000 resamples, default_rng(2033)); the year x reader
interaction, agreement in 2018 against agreement in 2026, Fisher's exact test; the 2026 - 2018 difference read by Gemma,
Newcombe and Fisher, Holm over the four criteria, next to our readers' on the same papers. Reading: same sign and
overlapping intervals "reproduced"; same sign and Gemma's interval containing zero "same direction, not settled";
opposite sign "not reproduced". Invalid decisions (quote not found after one retry) leave the denominators and are counted.
Run from study/: ../sim/env-an/bin/python gemma_stats.py  -> gemma_stats.json
(INVALID_NO=1 -> gemma_stats_invalid_no.json, invalid decisions counted "no": precision after the pilot)
"""
import glob, json, os
import numpy as np
from pineau_rl.stats import cohen_kappa, compare, fisher, holm, wilson_ci
from samples import classic26, experimental, ours18, val

CRIT = ["Q5", "X2", "X7", "Y9"]
years = {p: "2018" for p in experimental(ours18)} | {p: "2026" for p in experimental(classic26)}
G = {r["id"]: r for r in (json.load(open(f)) for f in sorted(glob.glob("codes_gemma/*.json")))}
rng = np.random.default_rng(2033)
INVALID_NO = os.environ.get("INVALID_NO") == "1"  # precision after the pilot: invalid decisions counted "no"
SUFFIX = "_invalid_no" if INVALID_NO else ""


def r6(x):
    return None if x is None else round(float(x), 6)


def kappa_ci(a, b):
    k = cohen_kappa(a, b) if len(set(a)) > 1 and len(set(b)) > 1 else None
    if k is None:
        return None, None
    A, B, ks = np.array(a), np.array(b), []
    for _ in range(10_000):
        i = rng.integers(0, len(a), len(a))
        kk = cohen_kappa(list(A[i]), list(B[i]))
        if kk is not None:
            ks.append(kk)
    return r6(k), [r6(np.percentile(ks, 2.5)), r6(np.percentile(ks, 97.5))]


out = dict(read=dict(total=len(G), by_year={y: sum(years[p] == y for p in G) for y in ("2018", "2026")},
                     truncated=sorted(p for p, r in G.items() if r["truncated"])), criteria={})
diffs = {}
for k in CRIT:
    row, agree_counts = dict(invalid=sorted(p for p, r in G.items() if r["criteria"][k]["invalid"])), {}
    for y in ("2018", "2026"):
        pairs = [("no" if G[p]["criteria"][k]["invalid"] else G[p]["criteria"][k]["value"], val(p, k)) for p in G
                 if years[p] == y and (INVALID_NO or not G[p]["criteria"][k]["invalid"]) and val(p, k) in ("yes", "no")]
        if not pairs:
            continue
        g, c = [a for a, _ in pairs], [b for _, b in pairs]
        same = sum(a == b for a, b in pairs)
        kap, ci = kappa_ci(g, c)
        agree_counts[y] = (same, len(pairs))
        row[y] = dict(n=len(pairs), same=same, agree=r6(same / len(pairs)), wilson=[r6(v) for v in wilson_ci(same, len(pairs))],
                      kappa=kap, kappa_boot95=ci, gemma_yes=g.count("yes"), claude_yes=c.count("yes"),
                      gemma_yes_claude_no=sorted(p for p in G if years[p] == y and not G[p]["criteria"][k]["invalid"]
                                                 and G[p]["criteria"][k]["value"] == "yes" and val(p, k) == "no"),
                      gemma_no_claude_yes=sorted(p for p in G if years[p] == y and not G[p]["criteria"][k]["invalid"]
                                                 and G[p]["criteria"][k]["value"] == "no" and val(p, k) == "yes"))
    if len(agree_counts) == 2:
        (a1, n1), (a2, n2) = agree_counts["2018"], agree_counts["2026"]
        row["year_interaction_fisher_p"] = r6(fisher(a2, n2, a1, n1))
        g = {y: (row[y]["gemma_yes"], row[y]["n"]) for y in ("2018", "2026")}
        c = {y: (row[y]["claude_yes"], row[y]["n"]) for y in ("2018", "2026")}
        diffs[k] = (compare(g["2026"], g["2018"]), compare(c["2026"], c["2018"]))
    out["criteria"][k] = row
if diffs:
    hg, hc = holm([diffs[k][0]["p"] for k in diffs]), holm([diffs[k][1]["p"] for k in diffs])
    for (k, (dg, dc)), pg, pc in zip(diffs.items(), hg, hc):
        if np.sign(dg["diff"]) != np.sign(dc["diff"]):
            verdict = "not reproduced"
        elif dg["lo"] <= 0 <= dg["hi"]:
            verdict = "same direction, not settled"
        elif dg["lo"] <= dc["hi"] and dc["lo"] <= dg["hi"]:
            verdict = "reproduced"
        else:
            verdict = "same direction, intervals apart"
        out["criteria"][k]["difference"] = dict(gemma={a: r6(b) for a, b in dg.items()} | dict(p_holm=r6(pg)),
                                                claude_same_papers={a: r6(b) for a, b in dc.items()} | dict(p_holm=r6(pc)),
                                                reading=verdict)
json.dump(out, open(f"gemma_stats{SUFFIX}.json", "w"), indent=1)
print("read:", out["read"])
for k, r in out["criteria"].items():
    print(k, {y: (r[y]["same"], r[y]["n"], r[y]["kappa"]) for y in ("2018", "2026") if y in r},
          "interaction p", r.get("year_interaction_fisher_p"), "invalid", len(r["invalid"]),
          r.get("difference", {}).get("reading"),
          {w: (d["diff"], d["lo"], d["hi"]) for w, d in r.get("difference", {}).items() if w != "reading"})
