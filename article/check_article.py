"""Every number of the blog article (fr.txt, en.txt), asserted against its source.

The spirit of docs/check_numbers.py, turned into a coverage check:
  1. each claim builds, from a result file, the phrase that both texts write (French and English formatting);
     the phrase must appear in the text;
  2. a few numbers have no result file (a slide, a cited paper, a sample size): their claim says so, and the
     number must then appear in the survey document itself, docs/conclusions.md or docs/conclusions-en.md;
  3. every numeric token left in the body after removing the claimed phrases is a failure: no number of the
     article escapes a source. Bibliography lines are checked against docs/refs.bib (or the survey document).
Exit code 1 on any failure.  Run: python3 article/check_article.py
"""
import csv, json, re, sys
Q = "'"  # an apostrophe for f-string expressions (Python 3.11 allows no backslash there)
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
J = lambda p: json.load(open(ROOT / p))
NB = str.maketrans({" ": " ", " ": " "})
norm = lambda t: re.sub(r"\s+", " ", t.translate(NB))

TEXT = {l: norm((HERE / f"{l}.txt").read_text()) for l in ("fr", "en")}
DOC = {"fr": norm((ROOT / "docs/conclusions.md").read_text()), "en": norm((ROOT / "docs/conclusions-en.md").read_text())}
BIB = norm((ROOT / "docs/refs.bib").read_text())


def hu(x, nd=0):
    q = Decimal(1).scaleb(-nd)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def num(x, lang, nd=0):
    v = hu(x, nd)
    if nd:
        s = str(v)
        return s.replace(".", ",") if lang == "fr" else s
    s = f"{int(v):,}"
    return s.replace(",", " ") if lang == "fr" else s


def pct(x, lang, nd=0):
    """x is a fraction: 0.31 -> '31 %' / '31%'."""
    s = num(Decimal(str(x)) * 100, lang, nd)
    return s + (" %" if lang == "fr" else "%")


def sg(v):
    v = int(hu(v))
    return f"+{v}" if v > 0 else (f"−{abs(v)}" if v < 0 else "0")


C = []  # (label, {lang: phrase}, kind) with kind "json" or "doc"


def claim(label, fr, en, kind="json"):
    C.append((label, {"fr": fr, "en": en}, kind))


both = lambda f: (f("fr"), f("en"))
de_a = lambda a, b, l: f"de {a} à {b}" if l == "fr" else f"from {a} to {b}"

# Survey with the same grid (study/extension_stats.json): classical RL 2026 against our reading of 2018.
X = {r["k"]: r for r in J("study/extension_stats.json")["rows"]}
sh = lambda k, s: Decimal(X[k][s][0]) / Decimal(X[k][s][1])
for k in ("Q5", "X7", "Y9", "X2", "Q4", "Q7", "Y7", "Q8"):
    claim(f"{k} 2018 to 2026", *both(lambda l: de_a(pct(sh(k, "ours2018"), l), pct(sh(k, "classic2026"), l), l)))
claim("Q8 then", *both(lambda l: f"{pct(sh('Q8', 'ours2018'), l)} {'puis' if l == 'fr' else 'then'} {pct(sh('Q8', 'classic2026'), l)}"))
for k in ("Q5", "Y9", "X7", "X2", "Q7", "Q8", "Y7", "Q4"):
    t = X[k]["classic_vs_ours2018"]
    if k == "Q5":
        claim("Q5 gap", f"{sg(t['diff'] * 100)} points, intervalle de {sg(t['lo'] * 100)} à {sg(t['hi'] * 100)}",
              f"{sg(t['diff'] * 100)} points, interval from {sg(t['lo'] * 100)} to {sg(t['hi'] * 100)}")
    else:
        claim(f"{k} gap", f"{sg(t['diff'] * 100)}, de {sg(t['lo'] * 100)} à {sg(t['hi'] * 100)}",
              f"{sg(t['diff'] * 100)}, from {sg(t['lo'] * 100)} to {sg(t['hi'] * 100)}")
n18 = X["Q5"]["ours2018"][1]
claim("2018 sample: 48 experimental papers", *both(lambda l: f"{n18} {'articles de 2018' if l == 'fr' else 'papers from 2018'}"))
claim("2026 classical sample", *both(lambda l: f"{X['Q5']['classic2026'][1]} {'articles de RL classique de 2026' if l == 'fr' else 'classical RL papers from 2026'}"))

# How far to trust the survey: the readers' models (study/readers/readers.csv), the search against the "no"
# decisions (study/falsify_no.json) and the cut without the papers read by the neighbouring model
# (study/extension_stats_sans_opus5.json).
RD = list(csv.DictReader(open(ROOT / "study/readers/readers.csv")))
other = set()
for r_ in RD:
    if r_["model_id"] != "claude-opus-5-5":
        assert "claude-opus-5 (" in r_["model_id"]
        other |= set(re.search(r"last writer of ([^)]*)\)", r_["model_id"])[1].split())
assert len(other) == 13 and sum(r_["model_id"] != "claude-opus-5-5" for r_ in RD) == 2
claim("thirteen papers on the neighbouring model", "pour treize articles", "for thirteen papers")
claim("thirteen papers (cut)", "Sans les treize articles lus en partie par le modèle voisin", "Without the thirteen papers read in part by the neighbouring model")
FN = J("study/falsify_no.json")
cnt = FN["counts"]
n_no = sum(v["no"] for v in cnt.values())
turned = {y: sum(len(v["turned"]) for k, v in cnt.items() if k.startswith(y)) for y in ("2018", "2026")}
doubt = sum(len(v["uncertain"]) for v in cnt.values())
assert len({k.split()[1] for k in cnt}) == 7 and FN["verdict_changes"]["turned"] == []
claim("seven of eight practices", "sur sept des huit pratiques comparées", "on seven of the eight practices compared")
claim("falsify no", *both(lambda l: (f"Sur {n_no} décisions « non », {sum(turned.values())} passent à « oui », {turned['2018']} en 2018 et {turned['2026']} en 2026" if l == "fr" else
                                    f"Of {n_no} \"no\" decisions, {sum(turned.values())} turn into \"yes\", {turned['2018']} in 2018 and {turned['2026']} in 2026")))
claim("falsify doubtful", *both(lambda l: f"{'juge' if l == 'fr' else 'finds'} {doubt} {'autres décisions douteuses' if l == 'fr' else 'other decisions doubtful'}"))
SO = {r_["k"]: r_["classic_vs_ours2018"]["p_holm"] for r_ in J("study/extension_stats_sans_opus5.json")["rows"]}
BD = FN["comparison"]
assert SO["X2"] > 0.05 and all(SO[k] < 0.05 for k in ("Q5", "Y9", "X7"))           # without the thirteen papers
assert BD["X2"]["bound"]["p_holm"] > 0.05 and BD["Y9"]["bound"]["p_holm"] > 0.05      # doubtful decisions turned
assert all(BD[k]["bound"]["p_holm"] < 0.05 for k in ("Q5", "X7")) and FN["verdict_changes"]["bound"] == ["X2", "Y9"]
assert all(X[k]["classic_vs_ours2018"]["p_holm"] < 0.05 for k in ("Q5", "Y9", "X7", "X2"))
claim("X2 without the thirteen", *both(lambda l: f"{'ne passe plus la correction' if l == 'fr' else 'no longer passes the correction'} (p = {num(SO['X2'], l, 2)})"))
claim("X2 doubtful turned", *both(lambda l: (f"les {doubt} décisions douteuses passent à « oui » (p = {num(BD['X2']['bound']['p_holm'], l, 2)})" if l == "fr" else
                                             f"the {doubt} doubtful decisions turn into \"yes\" (p = {num(BD['X2']['bound']['p_holm'], l, 2)})")))

# Trajectory (study/trajectory.json).
T = J("study/trajectory.json")
ty = lambda k, y: Decimal(T["rows"][k]["by_year"][y]["k"]) / Decimal(T["rows"][k]["by_year"][y]["n"])
claim("X2 in 2024", *both(lambda l: f"{pct(ty('X2', '2024'), l)} {'en' if l == 'fr' else 'in'} 2024"))
claim("Q8 in 2024", *both(lambda l: f"{pct(ty('Q8', '2024'), l)} {'en' if l == 'fr' else 'in'} 2024"))
claim("20 papers per year", "20 par année de 2019 à 2024, 50 de 2026", "20 per year from 2019 to 2024, 50 from 2026")
assert {T["sizes"][y] for y in ("2019", "2020", "2022", "2024")} == {20} and T["sizes"]["2026"] == 50
claim("20 per year read", "20 articles de RL classique par année d'ICML et de NeurIPS, en 2019, 2020, 2022 et 2024",
      "20 classical RL papers per year from ICML and NeurIPS, in 2019, 2020, 2022 and 2024")
y9 = lambda ys: sum(T["rows"]["Y9"]["by_year"][y]["k"] for y in ys) / sum(T["rows"]["Y9"]["by_year"][y]["n"] for y in ys)
claim("Y9 later", f"de {pct(y9(['2019', '2020']), 'fr')} sur 2019 et 2020 à {pct(y9(['2022', '2024']), 'fr')} sur 2022 et 2024",
      f"from {pct(y9(['2019', '2020']), 'en')} over 2019 and 2020 to {pct(y9(['2022', '2024']), 'en')} over 2022 and 2024")

# E1: thirty PPO runs (sim/analysis/e1.json).
e1 = J("sim/analysis/e1.json")
s = e1["seeds_sorted"]
inner = [v for v in s if v < 3000]
claim("E1 mean, sd, cv", *both(lambda l: f"{num(e1['mean'], l)}, {('l' + Q + 'écart type') if l == 'fr' else 'the standard deviation'} {num(e1['sd'], l)}, {'soit' if l == 'fr' else 'or'} {pct(e1['cv'], l)}"))
claim("E1 mean, median", *both(lambda l: f"{'Moyenne' if l == 'fr' else 'Mean'} {num(e1['mean'], l)}, {'médiane' if l == 'fr' else 'median'} {num(e1['median'], l)}"))
claim("E1 27 runs range", *both(lambda l: de_a(num(min(s), l), num(max(inner), l), l).replace("de ", "entre ").replace(" à ", " et ").replace("from ", "between ").replace(" to ", " and ")))
assert len(inner) == 27 and len(s) - len(inner) == 3 and min(v for v in s if v >= 3000) > 3000
claim("E1 beyond 3000", *both(lambda l: f"{'au-delà de' if l == 'fr' else 'beyond'} {num(3000, l)}"))
claim("E1 alt", *both(lambda l: (f"{pct(e1['extreme_5v5_of_10']['false_positive'], l)} de faux positifs. Dix contre dix au hasard : {pct(e1['random_10v10']['false_positive'], l, 1)}. Trois contre trois au hasard : {pct(e1['random_3v3']['false_positive'], l, 1)}. Cinq contre cinq au hasard : {pct(e1['random_5v5']['false_positive'], l, 1)}" if l == "fr" else
                                  f"{pct(e1['extreme_5v5_of_10']['false_positive'], l)} false positives. Ten against ten at random: {pct(e1['random_10v10']['false_positive'], l, 1)}. Three against three at random: {pct(e1['random_3v3']['false_positive'], l, 1)}. Five against five at random: {pct(e1['random_5v5']['false_positive'], l, 1)}")))
claim("E1 random 5v5", *both(lambda l: f"{'dans' if l == 'fr' else 'in'} {pct(e1['random_5v5']['false_positive'], l, 1)} {'des tirages' if l == 'fr' else 'of the draws'}"))
claim("E1 gaps", *both(lambda l: f"{pct(e1['random_5v5']['median_gap'], l)} {'en médiane et de' if l == 'fr' else 'at the median and by'} {pct(e1['random_5v5']['p95_gap'], l)}"))
claim("E1 sorted 31%", *both(lambda l: f"{pct(e1['extreme_5v5_of_10']['false_positive'], l)} {'de faux positifs' if l == 'fr' else 'false positives'}"))
claim("E1 near one in three (brief)", *both(lambda l: "près d'une fois sur trois" if l == "fr" else "nearly one time in three"))
claim("E1 draws", *both(lambda l: f"{num(10000, l)} {'tirages' if l == 'fr' else 'draws'}"))
claim("E1 draws (verb)", *both(lambda l: f"{num(10000, l)} {'fois' if l == 'fr' else 'times'}"))
claim("E1 top3", *both(lambda l: f"{pct(e1['top3_of_10']['inflation'], l)} : {num(e1['top3_of_10']['mean_top3'], l)} au lieu de {num(e1['top3_of_10']['mean_all'], l)}" if l == "fr"
                       else f"{pct(e1['top3_of_10']['inflation'], l)}: {num(e1['top3_of_10']['mean_top3'], l)} instead of {num(e1['top3_of_10']['mean_all'], l)}"))
claim("5% threshold", "seuil habituel de 5 %", "usual 5% threshold", "doc")

# E1 curve and B1 (sim/analysis/e1_curve.json, b1_trpo.json, b1_script.json).
cu, b1, b1s = J("sim/analysis/e1_curve.json"), J("sim/analysis/b1_trpo.json"), J("sim/analysis/b1_script.json")
claim("E1 curve p95", *both(lambda l: f"{num(cu['random_5v5']['abs_mean_t_p95'], l, 1)} {'quand les groupes sont tirés au hasard,' if l == 'fr' else 'when the groups are drawn at random,'} {num(cu['sorted_5v5']['abs_mean_t_p95'], l, 1)}"))
assert cu["random_5v5"]["share_abs_mean_t_ge_9"] == cu["sorted_5v5"]["share_abs_mean_t_ge_9"] == 0
claim("E1 curve none of 20000 reaches 9", "Aucun de nos 20 000 tirages n'atteint 9", "None of our 20,000 draws reaches 9")
tr = b1["trpo"]
claim("B1 TRPO cv", *both(lambda l: f"{pct(tr['cv'], l)} {'de sa moyenne' if l == 'fr' else 'of its mean'}"))
claim("B1 mean t", *both(lambda l: f"{num(tr['random_5v5']['mean_t']['abs_t_p95'], l, 1)} {('qu' + Q + 'une fois sur vingt au hasard,') if l == 'fr' else 'only one time in twenty at random,'} {num(tr['sorted_5v5']['mean_t']['abs_t_p95'], l, 1)}"))
claim("B1 pooled", *both(lambda l: f"{num(tr['random_5v5']['pooled']['abs_t_p95'], l, 1)} {'au hasard et à' if l == 'fr' else 'at random and'} {num(tr['sorted_5v5']['pooled']['abs_t_p95'], l, 1)}"))
claim("B1 pooled false positives", *both(lambda l: f"{pct(tr['random_5v5']['pooled']['false_positive'], l)} {'des tirages au hasard' if l == 'fr' else 'of the random draws'}"))
assert all(tr[g][m]["share_abs_t_ge_henderson"] == 0 for g in ("random_5v5", "sorted_5v5") for m in ("mean_t", "pooled"))
hs = b1s["trpo"]["n10"]["random_5v5"]
claim("Henderson script share >= 9.09", *both(lambda l: f"{'dépasse' if l == 'fr' else 'exceeds'} {num(9.09, l, 2)} {'dans' if l == 'fr' else 'in'} {pct(hs['share_abs_t_ge_henderson'], l)}"))
claim("Henderson script false positives", *both(lambda l: f"{pct(hs['false_positive'], l)} {'des cas' if l == 'fr' else 'of the cases'}"))
claim("TRPO episode/agent sd", *both(lambda l: f"{pct(b1s['trpo']['eval_std_over_between_seed_sd'], l)} {('de l' + Q + 'écart type entre agents') if l == 'fr' else 'of the standard deviation between agents'}"))
assert b1s["ppo_sb3"]["n10"]["random_5v5"]["share_abs_t_ge_henderson"] == 0
claim("PPO with the script never reaches 9", "le même calcul n'atteint jamais 9", "the same computation never reaches 9")
claim("B1 no reading reaches 9", "Aucune lecture n'atteint 9", "No reading reaches 9")
claim("t-de-neuf alt", *both(lambda l: f"{'TRPO avec le script de 2017 :' if l == 'fr' else 'TRPO with the 2017 script:'} {pct(hs['share_abs_t_ge_henderson'], l)} {'des tirages atteignent' if l == 'fr' else 'of draws reach'} {num(9.09, l, 2)}"))
claim("t-de-neuf alt zeros", *both(lambda l: "script de 2017 : 0 %" if l == "fr" else "2017 script: 0%"))

# E4, E5 (sim/analysis/e4.json, e5.json).
e4 = J("sim/analysis/e4.json")
claim("E4 median range", *both(lambda l: f"{pct(e4['inflation_median'], l)} {'en médiane, de' if l == 'fr' else 'at the median, from'} {pct(e4['inflation_range'][0], l)} {'à' if l == 'fr' else 'to'} {pct(e4['inflation_range'][1], l)}"))
claim("E4 reversals", *both(lambda l: f"{'Sur' if l == 'fr' else 'Of'} {e4['n_comparisons']} {'comparaisons entre deux algorithmes,' if l == 'fr' else 'comparisons between two algorithms,'} {e4['n_reversed']}"))
ALG = ["sac", "crossq", "ppo_sb3", "ppo_sbx"]
TK = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
inf = lambda a, t: int(hu(e4["cells"][f"{a}/{t}"]["inflation"] * 100))
first = TK[0]
claim("E4 alt", *both(lambda l: (f"HalfCheetah{' :' if l == 'fr' else ':'} SAC {pct(inf('sac', first) / 100, l)}, CrossQ {pct(inf('crossq', first) / 100, l)}, PPO PyTorch {pct(inf('ppo_sb3', first) / 100, l)}, PPO JAX {pct(inf('ppo_sbx', first) / 100, l)}. "
                                  + ". ".join(f"{t[:-3]}{' :' if l == 'fr' else ':'} " + ", ".join(str(inf(a, t)) for a in ALG) for t in TK[1:]))))
e5 = J("sim/analysis/e5.json")
claim("E5 close comparisons", *both(lambda l: f"{'moins de' if l == 'fr' else 'less than'} {pct(0.2, l)}, {'cinq graines aléatoires ne retrouvent le bon ordre que' if l == 'fr' else 'five random seeds recover the right order only'} {int(hu(e5['median_close']['5'] * 100))}"))
assert e5["n_close"] == 7

# E2, E3 (sim/analysis/e2.json, e3.json).
e2 = J("sim/analysis/e2.json")["tasks"]
rel = lambda a, t: int(hu(e2[t]["iqm"][a] / max(e2[t]["iqm"].values()) * 100))
claim("E2 alt", *both(lambda l: ". ".join(f"{t[:-3]}{' :' if l == 'fr' else ':'} " + ", ".join(f"{n} {rel(a, t)}" for a, n in zip(ALG, ["SAC", "CrossQ", "PPO PyTorch", "PPO JAX"])) for t in TK)))
assert [e2[t]["order"][0] for t in TK] == ["sac", "ppo_sbx", "crossq", "ppo_sbx"]
e3 = J("sim/analysis/e3.json")["Walker2d-v5"]
claim("E3 Walker2d", *both(lambda l: f"{num(e3['iqm']['sb3'], l)}, PPO {'écrit en JAX' if l == 'fr' else 'written in JAX'} {num(e3['iqm']['sbx'], l)}, {'soit' if l == 'fr' else 'or'} {pct(1 - e3['iqm_ratio_sbx_over_sb3'], l)}"))
assert e3["intervals_overlap"]
claim("budgets", *both(lambda l: f"{'SAC et CrossQ' if l == 'fr' else 'SAC and CrossQ for'} {num(200000, l)}"), "doc")

# E7 (sim/analysis/e7.json, e7_rank.json).
e7, rk = J("sim/analysis/e7.json"), J("sim/analysis/e7_rank.json")
loss = sum(v["verdict"] == "loss" for v in e7.values())
assert loss == 12 and len(e7) == 16
claim("E7 masses and friction", *both(lambda l: f"{'masses alourdies de' if l == 'fr' else 'masses'} {pct(0.2, l)} {'et des frottements réduits de' if l == 'fr' else 'heavier and friction'} {pct(0.2, l)}"), "doc")
ret = lambda a, t: e7[f"{a}/{t}"]["iqm"]
claim("E7 Hopper retention", *both(lambda l: f"{pct(ret('ppo_sb3', 'Hopper-v5'), l)} {'de son score dans sa version PyTorch et' if l == 'fr' else 'of its score in its PyTorch version and'} {pct(ret('ppo_sbx', 'Hopper-v5'), l)} {'dans sa version JAX, quand SAC en garde' if l == 'fr' else 'in its JAX version, while SAC keeps'} {pct(ret('sac', 'Hopper-v5'), l)} {'et CrossQ' if l == 'fr' else 'and CrossQ'} {pct(ret('crossq', 'Hopper-v5'), l)}"))
claim("E7 SAC Swimmer gain", *both(lambda l: f"SAC {'y gagne même' if l == 'fr' else 'even gains'} {pct(ret('sac', 'Swimmer-v5') - 1, l)}"))
hp = rk["Hopper-v5"]
pm = lambda a: num(hp["iqm"]["perturbed_mean"][a], "x")
claim("E7 alt", *both(lambda l: (f"CrossQ premier avec {num(hp['iqm']['perturbed_mean']['crossq'], l)}, SAC deuxième avec {num(hp['iqm']['perturbed_mean']['sac'], l)}, PPO PyTorch troisième avec {num(hp['iqm']['perturbed_mean']['ppo_sb3'], l)}, PPO JAX dernier avec {num(hp['iqm']['perturbed_mean']['ppo_sbx'], l)}" if l == "fr" else
                                  f"CrossQ first with {num(hp['iqm']['perturbed_mean']['crossq'], l)}, SAC second with {num(hp['iqm']['perturbed_mean']['sac'], l)}, PPO PyTorch third with {num(hp['iqm']['perturbed_mean']['ppo_sb3'], l)}, PPO JAX last with {num(hp['iqm']['perturbed_mean']['ppo_sbx'], l)}")))
assert hp["training"] == ["ppo_sbx", "ppo_sb3", "crossq", "sac"] and hp["modified"] == ["crossq", "sac", "ppo_sb3", "ppo_sbx"]

# E7 at several strengths, one quantity at a time (sim/analysis/dose.json, SIM deviation 12 (ii)).
ds = J("sim/analysis/dose.json")
assert ds["missing"] == {} and ds["control_max_rel_gap"] == 0 and ds["seeds"] == [0, 10]
dl = {}
for k, v in ds["ratio"].items():
    a, t, qn, st = k.split("/")
    assert (v["verdict"] == "loss") == (v["ci"][1] < 1)  # a loss is an interval that stays below 1
    dl.setdefault((qn, st), []).append(v["verdict"] == "loss")
assert all(len(v) == 16 for v in dl.values())
nl = lambda qn, st: sum(dl[(qn, st)])
chg = lambda st: int(hu((Decimal(st) - 1) * 100))              # 1.2 -> 20, 0.7 -> -30
STR = {qn: sorted((st for (q2, st) in dl if q2 == qn), key=Decimal) for qn in ("mass", "friction")}
claim("dose range", *both(lambda l: (f"les masses de {pct(-chg(STR['mass'][0]) / 100, l)} plus légères à {pct(chg(STR['mass'][-1]) / 100, l)} plus lourdes, les frottements de {pct(-chg(STR['friction'][0]) / 100, l)} plus faibles à {pct(chg(STR['friction'][-1]) / 100, l)} plus forts" if l == "fr" else
                                 f"masses from {pct(-chg(STR['mass'][0]) / 100, l)} lighter to {pct(chg(STR['mass'][-1]) / 100, l)} heavier, friction from {pct(-chg(STR['friction'][0]) / 100, l)} lower to {pct(chg(STR['friction'][-1]) / 100, l)} higher")))
claim("dose loss rule", "l'intervalle à 95 % de son score rapporté à celui de la physique d'entraînement reste sous 1",
      "the 95% interval of its score relative to the training physics stays below 1", "doc")
claim("dose lighter masses", *both(lambda l: (f"Des masses allégées de {pct(0.1, l)} coûtent une part détectable de leur score à {nl('mass', '0.9')} couples sur 16, allégées de {pct(0.3, l)}, à {nl('mass', '0.7')}" if l == "fr" else
                                          f"Masses {pct(0.1, l)} lighter cost {nl('mass', '0.9')} pairs out of 16 a detectable share of their score, {pct(0.3, l)} lighter cost {nl('mass', '0.7')}")))
claim("dose heavier masses", *both(lambda l: (f"Alourdies de {pct(0.1, l)}, elles en font perdre {nl('mass', '1.1')} ; alourdies de {pct(0.2, l)}, {nl('mass', '1.2')}" if l == "fr" else
                                          f"Masses {pct(0.1, l)} heavier cost {nl('mass', '1.1')} pairs; {pct(0.2, l)} heavier, {nl('mass', '1.2')}")))
assert nl("friction", "1.2") == max(nl("friction", s) for s in STR["friction"])  # "friction matters less, except +20%"
assert all(nl("friction", s) <= nl("mass", s) for s in STR["friction"] if s in STR["mass"] and s != "1.2")
claim("dose friction +20%", *both(lambda l: (f"sauf augmentés de {pct(0.2, l)} : {nl('friction', '1.2')} couples y perdent" if l == "fr" else
                                         f"except {pct(0.2, l)} higher: {nl('friction', '1.2')} pairs lose there")))
hk = {k.split("/", 1)[1]: v["ranking"] for k, v in ds["ranking"].items() if k.startswith("Hopper-v5/")}
assert hk["mass/1.0"][0] == "ppo_sbx"  # the leader in the training physics
hs_ = [k for k in hk if not k.endswith("/1.0")]
claim("dose Hopper leader", *both(lambda l: (f"n'est plus premier à {sum(hk[k][0] != 'ppo_sbx' for k in hs_)} intensités sur {len(hs_)}" if l == "fr" else
                                         f"no longer first at {sum(hk[k][0] != 'ppo_sbx' for k in hs_)} strengths out of {len(hs_)}")))
claim("dose reference at 0%", *both(lambda l: f"{'À' if l == 'fr' else 'At'} {pct(chg('1.0'), l)}{', la physique d' + Q + 'entraînement sert de référence' if l == 'fr' else ', the training physics serves as the reference'}"))
claim("dose 16 pairs", "soit 16 couples d'algorithme et de tâche", "or 16 pairs of algorithm and task")
assert len(ALG) * len(TK) == 16


def dose_alt(l):
    sgp = lambda x: (f"+{x}" if x > 0 else (f"−{-x}" if x < 0 else "0")) + (" %" if l == "fr" else "%")
    out = []
    for qn, name in (("mass", "Masses"), ("friction", "Frottements" if l == "fr" else "Friction")):
        pts = sorted([(chg(s), nl(qn, s)) for s in STR[qn]] + [(0, 0)])
        verb = {"fr": "couples perdent à", "en": "pairs lose at"}[l] if qn == "mass" else ("à" if l == "fr" else "at")
        out.append(f"{name}{' :' if l == 'fr' else ':'} " + ", ".join(f"{n} {verb if i == 0 else ('à' if l == 'fr' else 'at')} {sgp(x)}" for i, (x, n) in enumerate(pts)))
    return ". ".join(out)


claim("dose alt", dose_alt("fr"), dose_alt("en"))

# E6 (sim/analysis/e6.json, e6_official.json, e6_diag.json).
e6, e6o, e6d = J("sim/analysis/e6.json"), J("sim/analysis/e6_official.json"), J("sim/analysis/e6_diag.json")
claim("E6 first pass", *both(lambda l: f"{num(e6['iqm']['default'], l)} {'pour les valeurs par défaut,' if l == 'fr' else 'for the default values,'} {num(e6['iqm']['zoo'], l)}"))
claim("E6 official", *both(lambda l: f"{'obtiennent' if l == 'fr' else 'score'} {num(e6o['groups']['official v4']['iqm'], l)}, {'contre' if l == 'fr' else 'against'} {num(e6o['groups']['default v4']['iqm'], l)}"))
claim("E6 fixed recipe", "1 012 sur la version 5 de la tâche, 984 sur la version 4", "1,012 on version 5 of the task and 984 on version 4", "doc")
claim("E6 discount", *both(lambda l: f"{num(0.99, l, 2)}, {'là où le recueil emploie' if l == 'fr' else 'where the collection uses'} {num(0.999, l, 3)}"), "doc")

# GRPO (sim/llm/results/summary.json, gains.json; docs/figures/data/grpo_truncation_*.csv).
sm, gn = J("sim/llm/results/summary.json"), J("sim/llm/results/gains.json")
run = lambda m, r: [x for x in sorted(sm, key=lambda x: x["seed"]) if x["model"] == m and x["reward"] == r]
fin = lambda m, r, l: [pct(hu(x["pass1_100"], 2), l) for x in run(m, r)]
q, ll = fin("qwen05", "true", "fr"), fin("llama1", "true", "fr")
claim("GRPO Qwen true", *both(lambda l: ("finit à {}, {} et {}" if l == "fr" else "ends at {}, {} and {}").format(*fin("qwen05", "true", l))))
claim("GRPO Llama true", *both(lambda l: ("finit à {}, {} et {}" if l == "fr" else "ends at {}, {} and {}").format(*fin("llama1", "true", l))))
claim("GRPO alt", *both(lambda l: (("Qwen avec la vraie récompense : {}, {} et {} selon la graine aléatoire. Qwen à pile ou face : {}, {}, {}. Llama avec la vraie récompense : {}, {}, {}. Llama à pile ou face : {}, {}, {}") if l == "fr" else
                                   ("Qwen with the true reward: {}, {} and {} depending on the random seed. Qwen with a coin flip: {}, {}, {}. Llama with the true reward: {}, {}, {}. Llama with a coin flip: {}, {}, {}")).format(
    *fin("qwen05", "true", l), *fin("qwen05", "random", l), *fin("llama1", "true", l), *fin("llama1", "random", l))))
claim("GRPO 13% run on CPU", *both(lambda l: f"{('L' + Q + 'essai à') if l == 'fr' else 'The run at'} {pct(hu(run('qwen05', 'true')[2]['pass1_100'], 2), l)}"))
assert run("qwen05", "true")[2]["device"] == "cpu"
q0 = sorted({int(hu(x["pass1_0"] * 100)) for x in sm if x["model"] == "qwen05"})
l0 = sorted({int(hu(x["pass1_0"] * 100)) for x in sm if x["model"] == "llama1"})
claim("GRPO Qwen start", *both(lambda l: f"{'environ' if l == 'fr' else 'about'} {pct(q0[0] / 100, l)}"))
claim("GRPO Llama start", *both(lambda l: f"{de_a(pct(l0[0] / 100, l), pct(l0[-1] / 100, l), l).replace('from', 'at')}"))
g = lambda k: (sg(gn[k]["mean"] * 100), sg(gn[k]["ci"][0] * 100), sg(gn[k]["ci"][1] * 100))
claim("GRPO gains", *both(lambda l: ("{} points sur Qwen, avec un intervalle de {} à {}, contre {} points sur Llama, de {} à {}" if l == "fr" else
                                     "{} points on Qwen, with an interval from {} to {}, against {} points on Llama, from {} to {}").format(*g("qwen05 true"), *g("llama1 true"))))
assert gn["llama1 true"]["ci"][0] < 0 < gn["llama1 true"]["ci"][1]
assert max(x["pass1_100"] for x in sm if x["reward"] == "random") <= 0.0125
claim("GRPO coin flip <= 1%", *both(lambda l: f"{pct(0.01, l)} {'ou moins' if l == 'fr' else 'or less'}"))
cut = lambda m, r: [x["truncated_100"] for x in sm if x["model"] == m and x["reward"] == r]
claim("GRPO cut shares", *both(lambda l: (f"entre {pct(min(cut('qwen05', 'random')), l)} et {pct(max(cut('qwen05', 'random')), l)} à pile ou face, entre {pct(min(cut('qwen05', 'true')), l)} et {pct(max(cut('qwen05', 'true')), l)}" if l == "fr" else
                                          f"between {pct(min(cut('qwen05', 'random')), l)} and {pct(max(cut('qwen05', 'random')), l)} with a coin flip, between {pct(min(cut('qwen05', 'true')), l)} and {pct(max(cut('qwen05', 'true')), l)}")))
TRC = {l: list(csv.DictReader(open(ROOT / f"docs/figures/data/grpo_truncation_{l}.csv"))) for l in ("fr", "en")}
cutn = sum(int(x["share"]) for x in TRC["fr"] if x["type"].startswith("Coupée"))
tot = sum(int(x["share"]) for x in TRC["fr"])
claim("GRPO base model cut", f"{cutn} réponses sur {tot}", f"{cutn} answers out of {tot}")


def trunc_alt(l):
    out = []
    names = {"fr": ["juste", "fausse", "coupée"], "en": ["right", "wrong", "cut"]}[l]
    for qn in dict.fromkeys(x["quarter"] for x in TRC[l]):
        cells = [int(x["share"]) for x in TRC[l] if x["quarter"] == qn]
        parts = [f"{c} {names[i]}{'s' if (l == 'fr' and c > 1) else ''}" for i, c in enumerate(cells) if c]
        out.append(f"{qn}{' :' if l == 'fr' else ':'} " + ", ".join(parts))
    return ". ".join(out)


claim("GRPO truncation alt", trunc_alt("fr"), trunc_alt("en"))
claim("160 tokens", "160 jetons", "160 tokens", "doc")
claim("160-token limit", "limite de 160 jetons", "160-token limit", "doc")

# Numbers with no result file: the survey document holds them (slides, cited papers, sample sizes).
D = lambda label, fr, en: claim(label, fr, en, "doc")
D("t and p of 2018", "t = −9,09, p = 0,0016", "t = −9.09, p = 0.0016")
D("published t", "9,09 avec p = 0,0016", "9.09 with p = 0.0016")
D("degrees of freedom", "3,4 degrés de liberté", "3.4 degrees of freedom")
D("Nature survey", "1 576 chercheurs", "1,576 researchers")
D("Nature 70%", "plus de 70 %", "more than 70%")
D("Buckheit Donoho", "1995", "1995")
D("p threshold", "0,05", "0.05")
D("checklist 2019", "en 2019", "in 2019")
D("population 2026", "1 252 sur 17 836", "1,252 out of 17,836")
D("first draw", "27 appliquent le RL à de grands modèles de langue, 14 relèvent du RL classique", "27 apply RL to large language models, 14 belong to classical RL")
D("theory", "et 9 sont théoriques", "and 9 are theoretical")
D("agreement", "127 décisions sur 130 (98 %)", "127 decisions out of 130 (98%)")
D("Pineau 55 vs 90", "55 % d'articles qui donnent tous les réglages de leur méthode, quand Pineau en comptait 90 %", "55% of papers giving all the settings of their method, where Pineau counted 90%")
D("Pineau read 50", "Pineau avait lu 50 articles", "Pineau had read 50")
D("we reread 50 from 2018", "50 articles de 2018", "50 papers from 2018")
D("topped up to 50", "jusqu'à 50", "up to 50")
D("50 per side", "Avec 50 articles de chaque côté", "With 50 papers on each side")
D("NeurIPS 2025 checklist", "Sur les 30 articles de NeurIPS 2025", "Of the 30 NeurIPS 2025 papers")
D("checklist yes no test", "Les 18 articles", "The 18 papers")
D("checklist code", "5 articles sur 22", "5 papers out of 22")
D("40% to 73%", "40 %", "40%")
D("runs silent", "Sur 41 articles de RL expérimentaux", "Of 41 experimental RL papers")
D("runs silent 2", "20 ne disent pas combien", "20 do not say how many")
D("runs single", "4 n'en ont qu'un", "4 have only one")
D("best of N in papers", "14 % des articles de RL classique de 2026 la laissent voir, contre 19 % en 2018", "14% of classical RL papers from 2026 let it show, against 19% in 2018")
D("CrossQ 2024", "paru en 2024", "published in 2024")
D("TRPO script date", "En juin 2017", "In June 2017")
D("script name", "script de 2017", "2017 script")
D("Shao gains", "29,1 points de pourcentage, une récompense tirée au hasard 21,4", "29.1 percentage points, a reward drawn at random 21.4")
D("Shao model", "Qwen2.5-Math-7B et le banc d'essai MATH-500", "Qwen2.5-Math-7B and the MATH-500 benchmark")
D("Shao year", "En 2025, une équipe", "In 2025, a team")
D("models", "Qwen2.5 de 0,5 milliard de paramètres", "Qwen2.5 with 0.5 billion parameters")
D("Llama size", "Llama 3.2 de 1 milliard", "Llama 3.2 with 1 billion")
D("slide page", "page 22", "page 22")
D("95% interval", "intervalle de confiance à 95 %", "95% confidence interval")
D("NeurIPS 2025 / ICLR ICML 2026", "NeurIPS 2025", "NeurIPS 2025")
D("ICLR 2026", "ICLR 2026", "ICLR 2026")
D("ICML 2026", "ICML 2026", "ICML 2026")
D("NeurIPS 2018", "NeurIPS 2018", "NeurIPS 2018")
D("seeds 20 instead of 10, the consolidation", "2026", "2026")
D("t of 9", "t de 9", "t of 9")
D("first draw of 50", "en a retenu 50", "kept 50")
D("20 papers uncertainty", "Avec 20 articles", "With 20 papers")
D("t-de-neuf caption", "atteint 9,09", "reaches 9.09")
D("model size, caption", "de 0,5 milliard de paramètres", "with 0.5 billion parameters")
assert max(rel(a, t) for a in ALG for t in TK) == 100
claim("normalised leader", "la barre à 100", "the bar at 100")
D("years", "2018", "2018")
D("year 2017", "2017", "2017")
D("year 2019", "2019", "2019")
D("year 2020", "2020", "2020")
D("year 2022", "2022", "2022")
D("year 2024", "2024", "2024")
D("year 2025", "2025", "2025")


def number_ok_in_doc(phrase, lang):
    """A 'doc' claim: every number of the phrase appears in the survey document of that language."""
    for n in re.findall(r"\d+(?:[ ,.]\d+)*", phrase):
        if n not in DOC[lang]:
            return n
    return None


NUM = r"(?<![\w.])[−+]?\d+(?:[ ,.]\d{1,3})*(?:\s?%)?"
NAMES = ["CC BY 3.0", "Qwen2.5-Math-7B", "Qwen2.5", "Llama 3.2", "MATH-500", "Walker2d", "Baselines3", "HalfCheetah-v5"]


def body_of(lang):
    t = TEXT[lang]
    body, _, bib = t.partition(" BIBLIO ")
    body = re.sub(r"\]\([^)]*\)", "]", body)                      # link targets
    body = re.sub(r"FIG \w+ \| \S+", "FIG", body)                   # figure file names
    body = re.sub(r"## \S+ \|", "##", body)                         # section anchors
    body = re.sub(r"\[\[\d+\]\]", "", body)                         # note calls
    body = re.sub(r"META [^|]*\|[^|]*\|[^|]*\|", "META |", body)    # chip, ISO date, written date
    return body, bib


fails = 0
for lang in ("fr", "en"):
    body, bib = body_of(lang)
    work = body
    for label, ph, kind in sorted(C, key=lambda c: -len(c[1][lang])):
        p = norm(ph[lang])
        if p not in body:
            print(f"[{lang}] MISSING ({kind}) {label}: «{p}»")
            fails += 1
            continue
        if kind == "doc":
            bad = number_ok_in_doc(p, lang)
            if bad:
                print(f"[{lang}] NOT IN DOCUMENT {label}: {bad}")
                fails += 1
        work = work.replace(p, " ")
    for n in NAMES:
        work = work.replace(n, " ")
    left = re.findall(NUM, work)
    for n in left:
        i = work.find(n)
        print(f"[{lang}] UNSOURCED number «{n}» near «{work[max(0, i - 60):i + 30]}»")
    fails += len(left)
    # Bibliography: every number outside the links is in refs.bib or in the survey document.
    for line in re.split(r" REF ", bib)[1:]:
        line = re.sub(r"\]\([^)]*\)", "]", line)
        line = re.sub(r"^\d+ \|", "", line)
        for n in re.findall(r"\d+(?:[ ,.]\d+)*", line):
            if n not in BIB and n not in DOC[lang] and n.replace(" ", ",") not in BIB:
                print(f"[{lang}] bibliography number «{n}» found neither in refs.bib nor in the document: {line[:80]}")
                fails += 1
    print(f"[{lang}] {len(C)} claims checked, {len(re.findall(NUM, body))} numeric tokens in the body")

print("OK: every number of the article has a source" if not fails else f"{fails} failure(s)")
sys.exit(1 if fails else 0)
