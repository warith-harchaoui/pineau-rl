"""Complementary analyses of the data already read (PROTOCOL.md, deviation 30), written before this computation.

(a) double readings: the 30 papers re-read (G and G2 on the same 10 of 2026, R2 on 5 + 5, R3 on 10 of A4); per pair and
    criterion, on raw reads: agreement with Wilson's interval, Cohen's kappa with a percentile bootstrap over papers
    (10,000 resamples, default_rng(2030), resamples with an undefined kappa dropped and counted); pooled agreement of the
    three pairs (G for v1 criteria, G2 for v2, plus R2 and R3); R2 split by year.
(b) minimum detectable difference: for the 23 criteria of the main comparison, smallest increase and decrease (1-point
    steps) from our 2018 share at which the exact power of two-sided Fisher reaches 80%, at 5% and at 5%/m (m = 11, 12).
(c) the original verdict rule (deviation 7) on Q3-Q8: classical 2026 against Pineau (Holm over six) and against our 2018.
(d) readers and year: the readers behind each year's values; for Q5, Y9, X7, X2, within each year, the range of reader
    shares (readers of at least 5 papers) and a permutation test of reader heterogeneity (chi-square, 10,000
    permutations, default_rng(2031)); on R2's 10 papers, the 2026 - 2018 difference read by R2 and by the primary readers.
(e) lower bound for uncertainty over seeds: among final X2 yes, the share whose X2, Y2 or Y11 quote names seeds or runs.
Run from study/: ../sim/env-an/bin/python survey_extra.py  -> survey_extra.json
"""
import json, re
import numpy as np
from scipy.stats import binom, fisher_exact
from pineau_rl.grid import iter_reads, list_readers, y3_yes_no
from pineau_rl.stats import cohen_kappa, compare, holm, wilson_ci
from samples import OLD, PRIMARY, V2READ, classic26, experimental, ours18, val

V1 = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
V2 = ["Y%d" % i for i in range(1, 13)]
CRIT_G = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
VERDICT = ["Q5", "Y9", "X7", "X2"]
PINEAU = {"Q3": .90, "Q4": .60, "Q5": .55, "Q6": .20, "Q7": .10, "Q8": .05}
B = 10_000
ext = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}


def r6(x):
    return None if x is None else round(float(x), 6)


def raw(rec, k):  # raw read, no harmonisation, Y3 as yes/no (as agree_v2.py)
    v = rec["criteria"].get(k, {}).get("value")
    if k == "Y3" and v is not None:
        return y3_yes_no(v)
    return v if v in ("yes", "no") else None


# ---------------------------------------------------------------- (a) double readings
def kappa_boot(a, b, rng):
    a, b, n = np.array(a), np.array(b), len(a)
    ks, undefined = [], 0
    for _ in range(B):
        i = rng.integers(0, n, n)
        k = cohen_kappa(list(a[i]), list(b[i]))
        if k is None:
            undefined += 1
        else:
            ks.append(k)
    return [r6(np.percentile(ks, 2.5)), r6(np.percentile(ks, 97.5))] if ks else None, undefined


def agreement(pairs, rng):
    n, same = len(pairs), sum(x == y for x, y in pairs)
    a, b = zip(*pairs)
    k = cohen_kappa(list(a), list(b)) if len(set(a)) > 1 and len(set(b)) > 1 else None
    ci, und = kappa_boot(a, b, rng) if k is not None else (None, None)
    return dict(n=n, same=same, agree=r6(same / n), wilson=[r6(x) for x in wilson_ci(same, n)], kappa=r6(k),
                kappa_boot95=ci, boot_undefined=und)


rng = np.random.default_rng(2030)
prim_v1 = {r["id"]: r for _, r in iter_reads("codes", "ABCDE")}
prim_v2 = {}
for d in list_readers("codes_v2"):
    if d not in ("G2", "R2", "R3", "pilot"):
        prim_v2.update({r["id"]: r for _, r in iter_reads("codes_v2", [d])})
second = {"G": ({r["id"]: r for _, r in iter_reads("codes", ["G"])}, prim_v1, CRIT_G)}
for s in ("G2", "R2", "R3"):
    second[s] = ({r["id"]: r for _, r in iter_reads("codes_v2", [s])}, prim_v2, V1 + V2)
dbl, pooled_pairs = {}, {}
for s, (sec, prim, crit) in second.items():
    rows = {}
    for k in crit:
        pairs = [(raw(prim[p], k), raw(c, k)) for p, c in sec.items() if p in prim]
        pairs = [(x, y) for x, y in pairs if x and y]
        if not pairs:
            continue
        rows[k] = agreement(pairs, rng)
        if (s == "G" and k in V1) or (s == "G2" and k in V2) or s in ("R2", "R3"):
            pooled_pairs.setdefault(k, []).extend(pairs)
    dbl[s] = dict(papers=sorted(sec), criteria=rows)
pooled = {k: agreement(v, rng) for k, v in pooled_pairs.items()}
r2_year = {}
for y, pref in (("2018", "C"), ("2026", "K")):
    sec = {p: c for p, c in second["R2"][0].items() if p.startswith(pref)}
    r2_year[y] = {}
    for k in V1 + V2:
        pairs = [(raw(prim_v2[p], k), raw(c, k)) for p, c in sec.items()]
        pairs = [(x, y_) for x, y_ in pairs if x and y_]
        if pairs:
            r2_year[y][k] = dict(n=len(pairs), same=sum(x == y_ for x, y_ in pairs),
                                 wilson=[r6(x) for x in wilson_ci(sum(x == y_ for x, y_ in pairs), len(pairs))])
papers_double = sorted(set().union(*[set(v["papers"]) for v in dbl.values()]))


# ---------------------------------------------------------------- (b) minimum detectable difference
_pmat = {}


def pmatrix(n1, n2):
    if (n1, n2) not in _pmat:
        P = np.ones((n1 + 1, n2 + 1))
        for k1 in range(n1 + 1):
            for k2 in range(n2 + 1):
                P[k1, k2] = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1]
        _pmat[(n1, n2)] = P
    return _pmat[(n1, n2)]


def power(p1, n1, p2, n2, alpha):
    R = pmatrix(n1, n2) < alpha
    return float(binom.pmf(np.arange(n1 + 1), n1, p1) @ R @ binom.pmf(np.arange(n2 + 1), n2, p2))


def mdd(p0, n1, n2, alpha, sign):
    for d in range(1, 101):
        p1 = p0 + sign * d / 100
        if not 0 <= p1 <= 1:
            return None
        if power(p1, n1, p0, n2, alpha) >= 0.8:
            return d / 100
    return None


mde = {}
for k in V1 + V2:
    (ko, no), (kc, nc) = ext[k]["ours2018"], ext[k]["classic2026"]
    p0, m = ko / no, (11 if k in V1 else 12)
    obs = kc / nc - p0
    mde[k] = dict(base=r6(p0), n2018=no, n2026=nc, observed=r6(obs),
                  up_5=mdd(p0, nc, no, .05, 1), down_5=mdd(p0, nc, no, .05, -1),
                  up_bonf=mdd(p0, nc, no, .05 / m, 1), down_bonf=mdd(p0, nc, no, .05 / m, -1),
                  power_observed_5=r6(power(kc / nc, nc, p0, no, .05)), power_observed_bonf=r6(power(kc / nc, nc, p0, no, .05 / m)))


# ---------------------------------------------------------------- (c) original verdict rule
def classify(vs_p, vs_o):
    sp, so = vs_p["p_holm"] < .05, vs_o["p_holm"] < .05
    if sp and so and np.sign(vs_p["diff"]) == np.sign(vs_o["diff"]):
        return "changed and confirmed"
    if sp:
        return "changed, not confirmed"
    if so:
        return "ambiguous"
    return "none"


def counts(ids, k):
    v = [val(p, k) for p in ids if val(p, "Q1") != "no"]
    v = [x for x in v if x in ("yes", "no")]
    return sum(x == "yes" for x in v), len(v)


all26 = sorted(p for p in OLD if not p.startswith("C"))
orig = {}
for label, ids in (("classic2026", classic26), ("all2026", all26)):
    vs_p = {k: compare(counts(ids, k), (round(PINEAU[k] * 50), 50)) for k in PINEAU}
    for k, h in zip(PINEAU, holm([vs_p[k]["p"] for k in PINEAU])):
        vs_p[k]["p_holm"] = h
    vs_o = {k: compare(counts(ids, k), tuple(ext[k]["ours2018"])) for k in V1}
    for k, h in zip(V1, holm([vs_o[k]["p"] for k in V1])):
        vs_o[k]["p_holm"] = h
    orig[label] = {k: dict(share=list(counts(ids, k)), vs_pineau={a: r6(b) for a, b in vs_p[k].items()},
                           vs_ours2018={a: r6(b) for a, b in vs_o[k].items()}, rule=classify(vs_p[k], vs_o[k]))
                   for k in PINEAU}
assert all(abs(orig["classic2026"][k]["vs_ours2018"]["p_holm"] - ext[k]["classic_vs_ours2018"]["p_holm"]) < 1e-6 for k in PINEAU)


# ---------------------------------------------------------------- (d) readers and year
src_v2 = {r["id"]: d for d, r in iter_reads("codes_v2", PRIMARY + list_readers("codes_v2", "K*"))}
src_v1 = {r["id"]: d for d, r in iter_reads("codes", "ABCDEF")}


def reader(pid, k):
    return src_v2[pid] if pid in V2READ and k in V2READ[pid]["criteria"] else src_v1[pid]


def chi2(labels, y):
    s = 0.0
    p = y.mean()
    if p in (0, 1):
        return 0.0
    for r in set(labels):
        m = labels == r
        n, o = m.sum(), y[m].sum()
        s += (o - n * p) ** 2 / (n * p) + ((n - o) - n * (1 - p)) ** 2 / (n * (1 - p))
    return s


rng = np.random.default_rng(2031)
conf = {}
for year, ids in (("2018", experimental(ours18)), ("2026", experimental(classic26))):
    conf[year] = dict(readers={})
    for k in VERDICT:
        rows = [(reader(p, k), val(p, k)) for p in ids if val(p, k) in ("yes", "no")]
        labels, y = np.array([r for r, _ in rows]), np.array([v == "yes" for _, v in rows], float)
        per = {r: [int(y[labels == r].sum()), int((labels == r).sum())] for r in sorted(set(labels))}
        big = {r: c[0] / c[1] for r, c in per.items() if c[1] >= 5}
        obs = chi2(labels, y)
        perm = sum(chi2(rng.permutation(labels), y) >= obs - 1e-12 for _ in range(B))
        conf[year][k] = dict(per_reader=per, range_readers_5plus=[r6(min(big.values())), r6(max(big.values()))] if big else None,
                             chi2=r6(obs), p_perm=r6((perm + 1) / (B + 1)))
        for r, c in per.items():
            conf[year]["readers"][r] = max(conf[year]["readers"].get(r, 0), c[1])
overlap = sorted(set(conf["2018"]["readers"]) & set(conf["2026"]["readers"]))
r2 = second["R2"][0]
r2_diff = {}
for k in VERDICT:
    out = {}
    for who, get in (("R2", lambda p: raw(r2[p], k)), ("primary_raw", lambda p: raw(prim_v2[p] if k in prim_v2[p]["criteria"] else prim_v1.get(p, prim_v2[p]), k)),
                     ("final", lambda p: val(p, k))):
        c18 = [get(p) for p in r2 if p.startswith("C")]
        c26 = [get(p) for p in r2 if p.startswith("K")]
        a = (sum(x == "yes" for x in c26), sum(x in ("yes", "no") for x in c26))
        b = (sum(x == "yes" for x in c18), sum(x in ("yes", "no") for x in c18))
        out[who] = dict(y2026=list(a), y2018=list(b), diff=r6(a[0] / a[1] - b[0] / b[1]) if a[1] and b[1] else None)
    r2_diff[k] = out


# ---------------------------------------------------------------- (e) lower bound, seeds
SEEDS = re.compile(r"seeds?|independent (runs?|trials?|trainings?)|random (runs?|trials?|initiali[sz]ations?)|\bruns\b|\btrials\b|repetitions?", re.I)
EPIS = re.compile(r"episodes?|rollouts?", re.I)


def quotes(pid):
    out = []
    for k in ("X2", "Y2", "Y11"):
        rec = V2READ[pid] if pid in V2READ and k in V2READ[pid]["criteria"] else OLD.get(pid)
        if rec and k in rec["criteria"]:
            out.append(rec["criteria"][k].get("quote") or "")
    return out


lower = {}
for year, ids in (("2018", experimental(ours18)), ("2026", experimental(classic26))):
    x2 = [p for p in ids if val(p, "X2") == "yes"]
    s = [p for p in x2 if any(SEEDS.search(q) for q in quotes(p))]
    e = [p for p in x2 if p not in s and any(EPIS.search(q) for q in quotes(p))]
    lower[year] = dict(x2_yes=len(x2), experimental=len(ids), seeds=len(s), episodes_only=len(e), seeds_ids=s, episodes_ids=e,
                       share_of_x2=r6(len(s) / len(x2)), wilson_of_x2=[r6(v) for v in wilson_ci(len(s), len(x2))],
                       share_of_experimental=r6(len(s) / len(ids)), wilson_of_experimental=[r6(v) for v in wilson_ci(len(s), len(ids))])
lower["diff_experimental"] = {a: r6(b) for a, b in compare((lower["2026"]["seeds"], lower["2026"]["experimental"]),
                                                            (lower["2018"]["seeds"], lower["2018"]["experimental"])).items()}

out = dict(double_readings=dict(papers=len(papers_double), ids=papers_double, pairs=dbl, pooled=pooled, r2_by_year=r2_year),
           mde=mde, original_rule=orig,
           readers_year=dict(confound=conf, readers_in_both_years=overlap, r2_difference=r2_diff),
           seeds_lower_bound=lower)
json.dump(out, open("survey_extra.json", "w"), indent=1)
print("double readings:", len(papers_double), "papers")
for k in VERDICT:
    p = pooled[k]
    print(f"  pooled {k}: {p['same']}/{p['n']} [{p['wilson'][0]:.2f}, {p['wilson'][1]:.2f}] kappa {p['kappa']} {p['kappa_boot95']}")
for k, m in mde.items():
    print(f"MDE {k}: base {m['base']:.2f} obs {m['observed']:+.2f}  up {m['up_5']} / {m['up_bonf']}  down {m['down_5']} / {m['down_bonf']}")
for k in PINEAU:
    print("original rule", k, orig["classic2026"][k]["rule"], "| all2026:", orig["all2026"][k]["rule"])
for y in ("2018", "2026"):
    print(y, "readers", conf[y]["readers"], {k: (conf[y][k]["range_readers_5plus"], conf[y][k]["p_perm"]) for k in VERDICT})
print("readers in both years:", overlap)
print("R2 diff:", {k: {w: v["diff"] for w, v in d.items()} for k, d in r2_diff.items()})
print("lower bound:", {y: (lower[y]["seeds"], lower[y]["x2_yes"], lower[y]["experimental"]) for y in ("2018", "2026")}, lower["diff_experimental"])
