"""Deviation 36 (PROTOCOL.md): the year and the readers disentangled, the result.

Readings in codes_r36/T1..T8 (eight fresh readers, each reading both years), lists in assignments_r36.json.
Values: the reader's raw value; Q5 with link_kind project_page is settled by the page check of deviation 36
(r36_project_pages.json, written by r36_pages.py, which needs the PDFs: the original reading's final value when it cites the same address, else one visit); a
decision whose quote fails the check of r36_check.py after its reader's correction is "invalid" (left out; a second
reading counts it "no"); a third reading counts every Q5 project page yes (precision after the reading, deviation 36).
1. The main comparison redone with these readings only: per criterion (Q5, Y9, X7, X2), classical RL 2026 against
   our 2018, shares with Wilson, difference with Newcombe's interval, Fisher's p, Holm over the four.
2. A logistic mixed model per criterion: logit P(yes) = b0 + b1 [year = 2026] + u_reader, u ~ N(0, s^2), fitted by
   maximum likelihood with the reader integrated out by Gauss-Hermite quadrature (40 nodes). Year effect b1 (odds
   ratio, Wald 95% interval from the numerical Hessian), likelihood-ratio test of b1 = 0 (chi-square, 1 df), Holm
   over the four; reader SD s and its likelihood-ratio test of s = 0 (half chi-square, boundary).
3. Verdict rule: a verdict of extension_stats.json (all four "changed") holds if the difference is positive with
   Holm p < 0.05 and b1 is positive with Holm p < 0.05; "same direction, not established" if both are positive but
   one test fails; "not reproduced" otherwise.
4. Beside it: agreement of the new readings with the final codes (harmonised) per criterion and year, Wilson and
   Cohen's kappa, Fisher's test of agreement 2018 against 2026; yes shares per reader and year.
Run from study/: ../sim/env-an/bin/python r36_stats.py  -> r36_stats.json
"""
import json
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logsumexp
from scipy.stats import chi2, norm
from pineau_rl.grid import iter_reads
from pineau_rl.stats import cohen_kappa, compare, fisher, holm, wilson_ci
from samples import val

CRIT = ["Q5", "Y9", "X7", "X2"]
R = [f"T{i}" for i in range(1, 9)]
asg = json.load(open("assignments_r36.json"))
Y18, Y26 = asg["_years"]["2018"], asg["_years"]["2026"]
reads = {r["id"]: (rd, r) for rd, r in iter_reads("codes_r36", R)}
assert set(reads) == set(Y18 + Y26), "readings incomplete"
assert all(reads[p][0] == r for r in R for p in asg[r]), "a paper read by a reader it was not assigned to"
pages = json.load(open("r36_project_pages.json"))
qc = json.load(open("r36_quote_check.json"))  # written by r36_check.py --json (needs the PDFs)
bad = {p: qc[f"codes_r36/{rd}/{p}.json"] for p, (rd, _) in reads.items()}
NODES, WEIGHTS = np.polynomial.hermite.hermgauss(40)
LOGW = np.log(WEIGHTS / np.sqrt(np.pi))


def r6(x):
    return None if x is None else round(float(x), 6)


def r4(x):
    return None if x is None else round(float(x), 4)



def value(pid, k, invalid_no=False, pages_yes=False):
    rd, rec = reads[pid]
    if any(e.startswith(k + " ") for e in bad[pid]):
        return "no" if invalid_no else "invalid"
    c = rec["criteria"][k]
    if k == "Q5" and c["value"] == "yes" and c["link_kind"] == "project_page":
        return "yes" if pages_yes else pages[pid]["value"]
    return c["value"]


def nll(theta, y, x, g):
    b0, b1, ls = theta
    u = np.sqrt(2) * np.exp(ls) * NODES                      # quadrature points of the reader effect
    eta = b0 + b1 * x[:, None] + u[None, :]                   # paper x node
    ll = y[:, None] * -np.logaddexp(0, -eta) + (1 - y[:, None]) * -np.logaddexp(0, eta)
    return -sum(logsumexp(LOGW + ll[g == j].sum(0)) for j in np.unique(g))


def fit(y, x, g, b1_free=True):
    f = (lambda t: nll(t, y, x, g)) if b1_free else (lambda t: nll((t[0], 0.0, t[2]), y, x, g))
    best = None
    for ls0 in (-2.0, 0.0):                                   # two starts for the reader SD, the best kept
        r = minimize(f, np.array([0.0, 0.0, ls0]), method="L-BFGS-B", bounds=[(-10, 10), (-10, 10), (-8, 3)],
                     options=dict(ftol=1e-15, gtol=1e-10, maxiter=10000))  # converged to the maximum, not to the stopping rule
        if best is None or r.fun < best.fun:
            best = r
    return polish(f, best, [0, 1, 2] if b1_free else [0, 2])


def polish(f, r, free):
    """Newton steps on the free coordinates from the L-BFGS-B point: its finite-difference gradient stops it about
    1e-5 from the maximum, differently on Linux and macOS; Newton reaches the maximum itself, so both platforms agree.
    The reader SD at its lower bound (zero) stays there."""
    x = r.x.copy()
    if x[2] <= -7.9:  # reader SD at zero: pinned exactly on the bound, so every platform starts Newton from the same point
        x[2] = -8.0
    free = [i for i in free if not (i == 2 and x[2] <= -7.9)]
    for _ in range(50):
        def fs(v):
            t = x.copy()
            t[free] = v
            return f(t)
        v, h = x[free], 1e-5
        g = np.array([(fs(v + h * e) - fs(v - h * e)) / (2 * h) for e in np.eye(len(free))])
        step = np.linalg.solve(hessian(fs, v), g)
        x[free] = v - step
        if np.max(np.abs(step)) < 1e-12:
            break
    r.x, r.fun = x, f(x)
    return r


def hessian(f, t, h=1e-4):
    n = len(t)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            e_i, e_j = np.eye(n)[i] * h, np.eye(n)[j] * h
            H[i, j] = (f(t + e_i + e_j) - f(t + e_i - e_j) - f(t - e_i + e_j) + f(t - e_i - e_j)) / (4 * h * h)
    return H


def glmm(ids, k):
    ids = [p for p in ids if value(p, k) in ("yes", "no")]
    y = np.array([value(p, k) == "yes" for p in ids], float)
    x = np.array([p in Y26 for p in ids], float)
    g = np.array([R.index(reads[p][0]) for p in ids])
    full, null = fit(y, x, g), fit(y, x, g, b1_free=False)
    b0, b1, ls = full.x
    boundary = ls <= -7.9                                     # reader SD at zero: Hessian on (b0, b1) only
    if boundary:
        H = hessian(lambda t: nll((t[0], t[1], ls), y, x, g), full.x[:2])
    else:
        H = hessian(lambda t: nll(t, y, x, g), full.x)
    se = float(np.sqrt(np.linalg.inv(H)[1, 1]))
    lr = max(0.0, 2 * (null.fun - full.fun))
    # reader SD = 0: plain logistic regression (the model at the lower bound of log s)
    lr0 = max(0.0, 2 * (nll((b0, b1, -50.0), y, x, g) - full.fun)) if not boundary else 0.0
    lo, hi = b1 - norm.ppf(.975) * se, b1 + norm.ppf(.975) * se
    return dict(n=len(ids), b0=r4(b0), b1=r4(b1), se_b1=r4(se), odds_ratio=r4(np.exp(b1)),
                or_wald95=[r4(np.exp(lo)), r4(np.exp(hi))], b1_wald95=[r4(lo), r4(hi)], p_lrt=r6(chi2.sf(lr, 1)),
                reader_sd=r4(0.0 if boundary else np.exp(ls)), p_reader_sd=r6(0.5 * chi2.sf(lr0, 1) if lr0 else 1.0),
                converged=bool(full.success and null.success))


res = {"readers": {r: dict(n=len(asg[r]), n2018=sum(p in Y18 for p in asg[r])) for r in R}}
for name, kw in (("main", {}), ("invalid_as_no", dict(invalid_no=True)), ("project_pages_yes", dict(pages_yes=True))):
    rows = {}
    for k in CRIT:
        cnt = {}
        for year, ids in (("2018", Y18), ("2026", Y26)):
            vs = [value(p, k, **kw) for p in ids]
            yes, n = sum(v == "yes" for v in vs), sum(v in ("yes", "no") for v in vs)
            cnt[year] = dict(yes=yes, n=n, invalid=sum(v == "invalid" for v in vs), share=r6(yes / n),
                             wilson=[r6(v) for v in wilson_ci(yes, n)])
        c = compare((cnt["2026"]["yes"], cnt["2026"]["n"]), (cnt["2018"]["yes"], cnt["2018"]["n"]))
        rows[k] = dict(counts=cnt, diff={a: r6(b) for a, b in c.items()})
    for k, p in zip(CRIT, holm([rows[k]["diff"]["p"] for k in CRIT])):
        rows[k]["diff"]["p_holm4"] = r6(p)
    res[name] = rows

ext = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}
models, verdicts = {}, {}
for k in CRIT:
    models[k] = glmm(Y18 + Y26, k)
for k, p in zip(CRIT, holm([models[k]["p_lrt"] for k in CRIT])):
    models[k]["p_lrt_holm4"] = r6(p)
for k in CRIT:
    d, m, o = res["main"][k]["diff"], models[k], ext[k]["classic_vs_ours2018"]
    pos, ok = d["diff"] > 0 and m["b1"] > 0, d["p_holm4"] < .05 and m["p_lrt_holm4"] < .05
    verdicts[k] = dict(original=dict(diff=r6(o["diff"]), lo=r6(o["lo"]), hi=r6(o["hi"]), p_holm=r6(o["p_holm"]),
                                     changed=bool(o["diff"] > 0 and o["p_holm"] < .05)),
                       verdict="holds" if pos and ok else "same direction, not established" if pos else "not reproduced",
                       intervals_overlap=bool(d["lo"] <= o["hi"] and o["lo"] <= d["hi"]))
res["mixed_model"], res["verdicts"] = models, verdicts

agree = {}
for k in CRIT:
    a = {}
    for year, ids in (("all", Y18 + Y26), ("2018", Y18), ("2026", Y26)):
        pairs = [(value(p, k), val(p, k)) for p in ids if value(p, k) in ("yes", "no") and val(p, k) in ("yes", "no")]
        same = sum(x == y for x, y in pairs)
        a[year] = dict(n=len(pairs), same=same, agree=r6(same / len(pairs)),
                       wilson=[r6(v) for v in wilson_ci(same, len(pairs))],
                       kappa=r6(cohen_kappa([x for x, _ in pairs], [y for _, y in pairs])),
                       new_yes_orig_no=sum(x == "yes" and y == "no" for x, y in pairs),
                       new_no_orig_yes=sum(x == "no" and y == "yes" for x, y in pairs))
    a["p_fisher_2018_vs_2026"] = r6(fisher(a["2026"]["same"], a["2026"]["n"], a["2018"]["same"], a["2018"]["n"]))
    agree[k] = a
res["agreement_with_final_codes"] = agree
res["per_reader"] = {k: {r: {y: [sum(value(p, k) == "yes" for p in asg[r] if p in ids),
                                  sum(value(p, k) in ("yes", "no") for p in asg[r] if p in ids)]
                              for y, ids in (("2018", Y18), ("2026", Y26))} for r in R} for k in CRIT}
res["q5_project_pages"] = {p: pages[p] for p in sorted(pages)}
res["quote_check_failures"] = {p: e for p, e in sorted(bad.items()) if e}
json.dump(res, open("r36_stats.json", "w"), indent=1, ensure_ascii=False)
for k in CRIT:
    c, d, m = res["main"][k]["counts"], res["main"][k]["diff"], models[k]
    print(k, f"2018 {c['2018']['yes']}/{c['2018']['n']}", f"2026 {c['2026']['yes']}/{c['2026']['n']}",
          f"diff {d['diff']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}] p_holm {d['p_holm4']:.4g}",
          f"| OR {m['odds_ratio']} {m['or_wald95']} p_holm {m['p_lrt_holm4']:.4g} sd {m['reader_sd']}",
          "|", verdicts[k]["verdict"])
print("quote-check failures:", res["quote_check_failures"] or "none")
