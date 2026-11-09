"""Answers to a reviewer (PROTOCOL.md, écart 21), written before this computation. Exploratory: no verdict of
écart 20 changes; this says only whether a verdict is fragile.

(a) The four "changed" verdicts (Q5, Y9, X7, X2) and the two intervals that avoid zero without passing Holm
(Q6, Y12), cut four ways: (a1) classic 2026 by provenance, first draw against the A3 queue; (a2) by the source
of the 2026 PDF, arXiv against the conference site; (a3) Cochran-Mantel-Haenszel stratified by conference;
(a4) the main comparison redone without each primary reader in turn. Fragile: the gap changes sign in a cut, or
the redone Newcombe interval contains zero while each side keeps at least 35 papers.
(b) The thesis "heeded where it cost little": three blind raters (blind_cost/) score the 17 criteria of the main
comparison on cost C and risk to the conclusion R; median of three; Spearman with the observed gap (X3
reversed), p by permutation (10,000, seed 2026).
Run from study/: ../sim/env-an/bin/python robustness.py  -> robustness.json
"""
import glob, json, os
import numpy as np
from scipy.stats import fisher_exact, spearmanr
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.proportion import confint_proportions_2indep
from load import load

TARGETS = ["Q5", "Y9", "X7", "X2", "Q6", "Y12"]
MAIN17 = ["Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7", "Y1", "Y5", "Y7", "Y8", "Y9", "Y10", "Y12"]
PRIMARY = ["A2", "B2", "C2", "D2", "E2", "F2", "H1", "H2", "H3", "H4"]

ld = lambda f: {k: v for k, v in json.load(open(f)).items() if not k.startswith("_")}
ov1, ov2 = ld("overrides.json"), ld("overrides_v2.json")
OLD, WHO = load("ABCDEF"), {}
for d in "ABCDEF":
    for f in glob.glob(f"codes/{d}/*.json"):
        WHO[(json.load(open(f))["id"], "v1")] = d
V2READ = {}
for d in PRIMARY + sorted(os.path.basename(x) for x in glob.glob("codes_v2/K*")):
    for f in glob.glob(f"codes_v2/{d}/*.json"):
        r = json.load(open(f))
        V2READ[r["id"]] = r
        WHO[(r["id"], "v2")] = d


def val(pid, k):  # as in extension_stats.py
    if pid in V2READ and k in V2READ[pid]["criteria"]:
        v = ov2.get(k, {}).get(pid, V2READ[pid]["criteria"][k].get("value"))
    elif pid in OLD:
        v = ov1.get(k, {}).get(pid, OLD[pid]["criteria"].get(k, {}).get("value"))
    else:
        return None
    if k == "Y3" and v is not None:
        return "yes" if v >= 2 else "no"
    return v


def reader(pid, k):
    return WHO[(pid, "v2")] if pid in V2READ and k in V2READ[pid]["criteria"] else WHO.get((pid, "v1"))


def count(ids, k):
    vs = [val(p, k) for p in ids if val(p, "Q1") != "no"]
    vs = [v for v in vs if v in ("yes", "no")]
    return sum(v == "yes" for v in vs), len(vs)


def compare(c, o):
    (kc, nc), (ko, no) = c, o
    lo, hi = confint_proportions_2indep(kc, nc, ko, no, method="newcomb", compare="diff")
    return dict(classic2026=[kc, nc], ours2018=[ko, no], diff=kc / nc - ko / no, lo=float(lo), hi=float(hi),
                p=float(fisher_exact([[kc, nc - kc], [ko, no - ko]])[1]))


ext = json.load(open("extension_stats.json"))
meta = {x["id"]: x for f in ("calib_2018_v2.json", "final_2026.json", "classic_queue_2026.json") for x in json.load(open(f))}
ours18 = sorted(p for p in OLD if p.startswith("C")) + [x["id"] for x in json.load(open("calib_2018_v2.json"))[12:]]
a3 = ext["samples"]["a3"]
first = sorted(p for p in OLD if not p.startswith("C") and val(p, "X5") == "classic")
classic26 = first + a3
assert len(ours18) == ext["samples"]["ours2018"] and len(classic26) == ext["samples"]["classic2026"]
conf = lambda p: meta[p]["venue"].split()[0]
arxiv = lambda p: "arxiv.org" in (meta[p].get("pdf_src") or "")

out = dict(a={}, b={})
for k in TARGETS:
    r, fragile = {}, []
    # (a1) provenance
    f, q = count(first, k), count(a3, k)
    r["a1_first_vs_a3"] = dict(first=f, a3=q, p=float(fisher_exact([[f[0], f[1] - f[0]], [q[0], q[1] - q[0]]])[1]))
    for name, ids in (("first_only", first), ("a3_only", a3)):
        r[f"a1_{name}"] = compare(count(ids, k), count(ours18, k))
    # (a2) PDF source in 2026
    ax, nx = count([p for p in classic26 if arxiv(p)], k), count([p for p in classic26 if not arxiv(p)], k)
    r["a2_arxiv_vs_site"] = dict(arxiv=ax, site=nx, p=float(fisher_exact([[ax[0], ax[1] - ax[0]], [nx[0], nx[1] - nx[0]]])[1]))
    # (a3) Cochran-Mantel-Haenszel by conference
    tables = []
    for c in ("ICML", "NeurIPS", "ICLR"):
        (kc, nc), (ko, no) = count([p for p in classic26 if conf(p) == c], k), count([p for p in ours18 if conf(p) == c], k)
        tables.append(np.array([[kc, nc - kc], [ko, no - ko]]) + 0.5)  # Haldane correction for empty cells
    st = StratifiedTable(tables)
    r["a3_cmh"] = dict(pooled_odds_ratio=float(st.oddsratio_pooled), p=float(st.test_null_odds(correction=True).pvalue))
    # (a4) leave one reader out
    r["a4"] = {}
    for d in sorted({reader(p, k) for p in ours18 + classic26} - {None}):
        c = compare(count([p for p in classic26 if reader(p, k) != d], k), count([p for p in ours18 if reader(p, k) != d], k))
        r["a4"][d] = c
        if c["diff"] <= 0 or (c["lo"] <= 0 and min(c["classic2026"][1], c["ours2018"][1]) >= 35):
            fragile.append(f"a4 without {d}")
    for name in ("a1_first_only", "a1_a3_only"):
        if r[name]["diff"] <= 0:
            fragile.append(name)
    r["fragile"] = fragile
    out["a"][k] = r
    print(k, "fragile:", fragile or "no", " first", f, "A3", q, " arXiv", ax, "site", nx, f" CMH p {r['a3_cmh']['p']:.3g}")

# (b) the thesis against blind ratings
R = [json.load(open(f)) for f in sorted(glob.glob("blind_cost/rater*.json"))]
assert len(R) == 3
rows = {r["k"]: r for r in ext["rows"]}
gap = np.array([(-1 if k == "X3" else 1) * rows[k]["classic_vs_ours2018"]["diff"] for k in MAIN17])
rng = np.random.default_rng(2026)
for scale in ("C", "R"):
    s = np.array([np.median([r[k][scale] for r in R]) for k in MAIN17])
    rho = spearmanr(s, gap).statistic
    perm = np.array([spearmanr(s, rng.permutation(gap)).statistic for _ in range(10000)])
    out["b"][scale] = dict(median=dict(zip(MAIN17, s.tolist())), rho=float(rho),
                           p_two_sided=float((np.abs(perm) >= abs(rho) - 1e-12).mean()),
                           p_negative=float((perm <= rho + 1e-12).mean()))
    print(f"{scale}: Spearman {rho:+.2f}, permutation p (two-sided) {out['b'][scale]['p_two_sided']:.3f}")
# agreement between raters: Spearman between each pair, per scale
out["b"]["rater_agreement"] = {s: [float(spearmanr([R[i][k][s] for k in MAIN17], [R[j][k][s] for k in MAIN17]).statistic)
                                   for i, j in ((0, 1), (0, 2), (1, 2))] for s in ("C", "R")}
out["b"]["gap"] = dict(zip(MAIN17, gap.tolist()))
json.dump(out, open("robustness.json", "w"), indent=1)
