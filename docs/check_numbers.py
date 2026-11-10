"""Every key number of conclusions.md and conclusions-en.md, recomputed from the result files.

Each claim recomputes a value from study/ or sim/analysis/, formats it the way each text writes it, and
checks that the formatted string appears in that text (whitespace and line breaks normalised). A claim that
no file supports (a figure from a slide or a cited paper) does not belong here: its source is the
bibliography. Exit code 1 on the first missing number, so docs/build.sh stops before compiling.

Run from docs/: python3 check_numbers.py
"""
import json, re, statistics, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "study"))
J = lambda p: json.load(open(ROOT / p))

res = {r["k"]: r for r in J("study/results_final.json")}
audit = {r["k"]: r for r in J("study/audit_stats.json")["rows"]}
agree = J("study/audit_stats.json")["agreement"]
e1, curve = J("sim/analysis/e1.json"), J("sim/analysis/e1_curve.json")
b1 = J("sim/analysis/b1_trpo.json")

# Survey counts that analyze.py does not write out: recount them from the codes, with the same rules.
import os
os.chdir(ROOT / "study")
from load import load
ov = {k: v for k, v in json.load(open("overrides.json")).items() if not k.startswith("_")}
val = lambda d, k: ov.get(k, {}).get(d["id"], d["criteria"].get(k, {}).get("value"))
D = load("ABCDE")
exp = [d for d in D.values() if val(d, "Q1") != "no"]
rl = [d for d in exp if val(d, "X5") != "theory"]
seeds = [val(d, "X1") for d in rl]
llm = [d for d in exp if val(d, "X5") == "llm"]
classic = [d for d in exp if val(d, "X5") == "classic"]
yes = lambda ds, k: sum(val(d, k) == "yes" for d in ds)
applicable = lambda ds, k: sum(val(d, k) in ("yes", "no") for d in ds)


def half_up(x, nd=0):
    """Round half away from zero, as a reader does: 1.15 -> 1.2, -66.5 -> -67 (Python's round is to even)."""
    q = Decimal(1).scaleb(-nd)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def pct(x, nd=0, lang="fr"):
    s = str(half_up(Decimal(str(x)) * 100, nd))
    return (s.replace(".", ",") + " %") if lang == "fr" else s + "%"


def num(x, lang="fr"):
    s = f"{int(half_up(x)):,}"
    return s.replace(",", " ") if lang == "fr" else s


def ci(lo, hi, lang="fr"):
    return f"[{int(half_up(Decimal(str(lo)) * 100))}, {int(half_up(Decimal(str(hi)) * 100))}]"


def pts(t, lang="fr"):
    lo, hi = int(half_up(Decimal(str(t["lo"])) * 100)), int(half_up(Decimal(str(t["hi"])) * 100))
    m = "−" if lang == "fr" else "−"
    f = lambda v: f"{m}{abs(v)}" if v < 0 else (f"+{v}" if lang == "fr" else f"+{v}")
    return f(lo), f(hi)


# (description, French string, English string). Each string is built from the data, never typed by hand.
C = []
add = lambda d, fr, en: C.append((d, fr, en))
FR_WORDS = {1: "Un", 2: "Deux", 3: "Trois", 4: "Quatre", 5: "Cinq", 15: "Quinze", 16: "Seize", 17: "Dix-sept"}
EN_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen"}
fr_low = {3: "trois", 4: "quatre", 5: "cinq", 6: "six"}
add("experimental papers 2026", f"{len(exp)} articles expérimentaux", f"{len(exp)} experimental papers")
silent, single = sum(s is None for s in seeds), sum(s == 1 for s in seeds)
med = int(statistics.median([s for s in seeds if s]))
add("RL papers silent on runs", f"Sur {len(rl)} articles de RL expérimentaux de 2026, {silent} ne disent pas",
    f"{len(rl)} experimental RL papers from 2026, {silent}")
add("papers with a single run", f"{FR_WORDS[single]} n'en ont qu'un", f"{EN_WORDS[single]} have only one")
add("median runs", f"médiane des autres est {fr_low[med]}", f"median among the others is {['zero','one','two','three','four','five','six'][med]}")
add("Q7 llm", f"{yes(llm, 'Q7')} articles sur {applicable(llm, 'Q7')}", f"{yes(llm, 'Q7')} papers out of {applicable(llm, 'Q7')}")
add("X2 llm", f"({yes(llm, 'X2')} sur {applicable(llm, 'X2')})", f"({yes(llm, 'X2')} out of {applicable(llm, 'X2')})")
add("X3 visible", f"{yes(exp, 'X3')} articles sur {applicable(exp, 'X3')}", f"{yes(exp, 'X3')} papers out of {applicable(exp, 'X3')}")
one_family = sum(val(d, "X6") == 1 for d in llm)
add("llm papers with one model family", f"{FR_WORDS[one_family]} articles sur {len(llm)} n'essaient",
    f"{EN_WORDS[one_family]} papers out of {len(llm)} try")
CRIT13 = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7", "X5")
same, total = sum(agree[k]["same"] for k in CRIT13), sum(agree[k]["n"] for k in CRIT13)
add("agreement", f"{same} décisions sur {total} ({pct(same / total)})", f"{same} decisions out of {total} ({pct(same / total, lang='en')})")
kap = [a["kappa"] for a in agree.values() if a["kappa"] is not None]
add("kappa range", f"de {min(kap):.2f} à {max(kap):.0f}".replace(".", ","), f"from {min(kap):.2f} to {max(kap):.0f}")
# Audit: differences with Newcombe intervals.
t = audit["Q7"]["vs_pineau"]; d = pts(t)
add("Q7 vs Pineau", f"écart de {int(half_up(Decimal(str(t['diff'])) * 100))} points, de {d[0].lstrip('+')} à {d[1].lstrip('+')}",
    f"gap of {int(half_up(Decimal(str(t['diff'])) * 100))} points, from {d[0].lstrip('+')} to {d[1].lstrip('+')}")
# The extended survey (study/extension_stats.py, PROTOCOL.md deviation 12): classic RL of 2026 (50 papers) against our
# own reading of 2018 (50 papers), same grids; ours 2018 against Pineau; agreement on raw reads (study/agree_v2.py).
ext_all = J("study/extension_stats.json")
X, smp = {r["k"]: r for r in ext_all["rows"]}, ext_all["samples"]
G = J("study/agree_v2.json")
sh = lambda r, s_: Decimal(r[s_][0]) / Decimal(r[s_][1])  # exact share k/n
P = lambda k, s_, lang="fr": pct(sh(X[k], s_), lang=lang)  # "31 %" / "31%"
o, c, a26 = (lambda k, lang="fr": P(k, "ours2018", lang)), (lambda k, lang="fr": P(k, "classic2026", lang)), \
    (lambda k, lang="fr": P(k, "all2026", lang))
hp = lambda v: int(half_up(Decimal(str(v)) * 100))
sgn = lambda v: f"+{v}" if v > 0 else (f"−{abs(v)}" if v < 0 else "0")


def gap(t, signed=True):
    d, lo, hi = hp(t["diff"]), hp(t["lo"]), hp(t["hi"])
    return (sgn(d), sgn(lo), sgn(hi)) if signed else (str(d), str(lo), str(hi))


def pv(p, lang="fr"):
    """A Holm-adjusted p as the texts write it: two decimals from 0.1 up, one significant digit below."""
    d = Decimal(str(p))
    q = Decimal("0.01") if d >= Decimal("0.1") else Decimal(1).scaleb(d.adjusted())
    s_ = str(d.quantize(q, rounding=ROUND_HALF_UP))
    return s_.replace(".", ",") if lang == "fr" else s_


main = lambda k: X[k]["classic_vs_ours2018"]
vsP = lambda k: X[k]["ours2018_vs_pineau"]
cnt = lambda k, s_: X[k][s_]  # [k, n]
WFR = {9: "neuf", 12: "douze", 17: "dix-sept"}
WEN = {9: "nine", 12: "twelve", 17: "seventeen"}

# Which gaps pass Holm, and what the texts say about them.
holm = [k for k in X if main(k) and main(k).get("p_holm", 1) < 0.05 and k != "Q2"]
FIG = ["Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7", "Y1", "Y5", "Y7", "Y8", "Y9", "Y10", "Y12"]
assert sorted(holm) == sorted(["Q5", "Y9", "X7", "X2"]), holm  # "Quatre pratiques ont changé"
assert sorted(FIG, key=lambda k: -main(k)["diff"])[:4] == ["Q5", "Y9", "X7", "X2"]  # "Les quatre critères de gauche"
assert sorted(k for k in FIG if main(k)["lo"] > 0 and k not in holm) == ["Q6", "Y12"]  # "Deux autres intervalles"
assert len(FIG) - 4 - 2 == 11  # "les onze autres critères"
v1 = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
assert len(v1) == 11 and all("p_holm" in main(k) for k in v1)  # "onze critères à la fois"
assert vsP("Q4")["p_holm"] == vsP("Q5")["p_holm"]  # "p = 0,06 chacun"
ov2 = {k: v for k, v in J("study/overrides_v2.json").items() if not k.startswith("_")}
assert sum(len(v) for k, v in ov2.items() if k != "X5") == 80  # écart 19: 80 changes (X5 belongs to écart 18)

# Summary.
add("ours 2018 Q3", f"Elle trouve {o('Q3')}", f"It finds {o('Q3', 'en')}")

add("first draw classic", f"Ce premier tirage compte {len(classic)} articles de RL classique", f"That first draw holds {len(classic)} papers on classical RL")
for k in ("Q5", "Y9", "X7", "X2"):
    add(f"summary {k}", f"de {o(k)} à {c(k)}", f"from {o(k, 'en')} to {c(k, 'en')}")
for k in ("Q8", "Q4", "Q7", "Y7"):
    add(f"summary {k}", f"({o(k)} puis {c(k)})", f"({o(k, 'en')} then {c(k, 'en')})")
# How we measure: the samples.
n18, ncl, read, a3 = smp["ours2018"], smp["classic2026"], smp["a3_read"], len(smp["a3"])
n12 = len(J("study/calib_2018.json"))
exp18 = cnt("Q2", "ours2018")[1]
add("ours 2018 size", f"Notre lecture de 2018 passe à {n18} articles : aux {n12} du départ s'ajoutent {n18 - n12} articles",
    f"Our reading of 2018 grows to {n18} papers: {n18 - n12} papers drawn")
add("ours 2018 size en", "", f"join the original {n12}")
add("ours 2018 experimental", f"Parmi ces {n18} articles, {exp18} ont des expériences", f"Of these {n18} papers, {exp18} have experiments")
add("classic 2026 size", f"Le RL classique de 2026 passe lui aussi à {ncl} articles : aux {len(classic)} du premier tirage s'ajoutent {a3} articles",
    f"Classical RL in 2026 grows to {ncl} papers as well: {a3} papers taken from a queue")
add("classic 2026 size en", "", f"join the {len(classic)} of the first draw")
add("A3 read", f"Nous avons lu {read} articles de cette file. Les {a3} premiers articles de RL classique",
    f"We read {read} papers from this queue. The first {a3} classical RL papers")
add("A3 apart", f"Les {smp['a3_apart']['llm']} articles sur les modèles de langue et les {smp['a3_apart']['theory']} articles théoriques",
    f"The {smp['a3_apart']['llm']} papers on language models and the {smp['a3_apart']['theory']} theoretical papers")
# Agreement, second grid (G2: same ten papers as before) and both grids on ten new papers (R2).
g2, r2 = G["G2"]["criteria"], G["R2"]["criteria"]
full = sum(v["agree"] == 1 for v in g2.values())
add("G2 complete", f"l'accord est complet sur {WFR[full]} critères sur {WFR[len(g2)]}", f"agreement is complete on {WEN[full]} criteria out of {WEN[len(g2)]}")
kf = lambda x, lang: f"{x:.2f}".replace(".", ",") if lang == "fr" else f"{x:.2f}"
add("G2 Y6", f"{pct(g2['Y6']['agree'])} sur les essais exclus (Y6)", f"{pct(g2['Y6']['agree'], lang='en')} on excluded runs (Y6)")
add("G2 Y5", f"{pct(g2['Y5']['agree'])} sur l'implémentation des références (Y5, kappa {kf(g2['Y5']['kappa'], 'fr')})",
    f"{pct(g2['Y5']['agree'], lang='en')} on the implementation of the baselines (Y5, kappa {kf(g2['Y5']['kappa'], 'en')})")
add("G2 Y1", f"{pct(g2['Y1']['agree'])} sur la mesure de performance (Y1, kappa {kf(g2['Y1']['kappa'], 'fr')})",
    f"{pct(g2['Y1']['agree'], lang='en')} on the performance measure (Y1, kappa {kf(g2['Y1']['kappa'], 'en')})")
add("Y1 agreement F8", f"ne s'accordaient que sur {pct(g2['Y1']['agree'])} des articles", f"agreed on only {pct(g2['Y1']['agree'], lang='en')} of papers")
add("Y1 agreement limits", f"{pct(g2['Y1']['agree'])} d'accord sur le premier tirage", f"{pct(g2['Y1']['agree'], lang='en')} agreement on the first draw")
rmin, rfull = min(v["agree"] for v in r2.values()), sum(v["agree"] == 1 for v in r2.values())
add("R2", f"au moins {pct(rmin)} sur chacun des {len(r2)} critères. Il est complet sur {WFR[rfull]} d'entre eux",
    f"at least {pct(rmin, lang='en')} on each of the {len(r2)} criteria. It is complete on {WEN[rfull]} of them")
floor = min([rmin] + [v["agree"] for k, v in g2.items() if k != "Y1"] + [a_["same"] / a_["n"] for a_ in agree.values()])
add("agreement floor", f"au moins {pct(floor)} des articles pour chaque critère, à une exception près",
    f"at least {pct(floor, lang='en')} of papers for each criterion, with one exception")
add("harmonisation", "change 80 codes", "changes 80 codes")
# Our grid against Pineau's, on her own year.
t = vsP("Q3"); d = gap(t)
PIN = eval(re.search(r"PINEAU = (\{.*?\})", (ROOT / "study/extension_stats.py").read_text())[1])  # her published shares
pin = lambda k, lang="fr": pct(PIN[k], lang=lang)
add("Pineau Q3", f"quand Pineau en comptait {pin('Q3')}", f"where Pineau counted {pin('Q3', 'en')}")
add("Q3 ours vs Pineau", f"dans {o('Q3')} des articles chez nous, contre {pin('Q3')} chez elle : un écart de {d[0]} points, de {d[1]} à {d[2]}",
    f"in {o('Q3', 'en')} of papers by our reading, against {pin('Q3', 'en')} by hers: a gap of {d[0]} points, from {d[1]} to {d[2]}")
add("Q3 ours vs Pineau p", f"qui résiste à la correction (p = {pv(t['p_holm'])})", f"which survives the correction (p = {pv(t['p_holm'], 'en')})")
t = vsP("Q7"); d = gap(t)
add("Q7 ours vs Pineau", f"{o('Q7')} chez nous, contre {pin('Q7')} chez elle, soit {d[0]} points, de {d[1]} à {d[2]} (p = {pv(t['p_holm'])})",
    f"{o('Q7', 'en')} by our reading, against {pin('Q7', 'en')} by hers, a gap of {d[0]} points, from {d[1]} to {d[2]} (p = {pv(t['p_holm'], 'en')})")
add("Q4 Q5 ours vs Pineau", f"{o('Q4')} contre {pin('Q4')} et {o('Q5')} contre {pin('Q5')}, sans passer la correction (p = {pv(vsP('Q4')['p_holm'])} chacun)",
    f"{o('Q4', 'en')} against {pin('Q4', 'en')} and {o('Q5', 'en')} against {pin('Q5', 'en')}, without passing the correction (p = {pv(vsP('Q4')['p_holm'], 'en')} each)")
add("dumbbell caption", f"trouve par exemple {o('Q3')} pour les hyperparamètres de la méthode, là où Pineau trouvait {pin('Q3')}",
    f"finds, for instance, {o('Q3', 'en')} for the method's hyperparameters where Pineau found {pin('Q3', 'en')}")
# The main table: one row per criterion, with the gap in bold exactly when it passes Holm.
for k in FIG:
    (ka, na), (kb, nb) = cnt(k, "ours2018"), cnt(k, "classic2026")
    d = gap(main(k)); g = f"{d[0]} [{d[1]}, {d[2]}]"
    g = f"**{g}**" if k in holm else g
    add(f"table {k}", f"| {o(k)} ({ka} sur {na}) | {c(k)} ({kb} sur {nb}) | {g} |",
        f"| {o(k, 'en')} ({ka} of {na}) | {c(k, 'en')} ({kb} of {nb}) | {g} |")
# Flaw by flaw.
t = main("Q5"); d = gap(t, signed=False)
add("F1", f"{o('Q5')} des articles de 2018 à {c('Q5')} en 2026 : un écart de {d[0]} points, de {d[1]} à {d[2]}",
    f"{o('Q5', 'en')} of papers in 2018 to {c('Q5', 'en')} in 2026: a gap of {d[0]} points, from {d[1]} to {d[2]}")
add("F1 p", f"(p = {pv(t['p_holm'])}). La faille est écoutée", f"(p = {pv(t['p_holm'], 'en')}). The flaw is heeded")
add("F1 all 2026", f"la part vaut {a26('Q5')}", f"the share is {a26('Q5', 'en')}")
t = main("X7"); d = gap(t)
add("F2 X7", f"chiffré dans {c('X7')} des articles de RL classique de 2026, contre {o('X7')} en 2018 : {d[0]} points, de {d[1]} à {d[2]}, un écart qui résiste à la correction (p = {pv(t['p_holm'])})",
    f"quantified in {c('X7', 'en')} of classical RL papers from 2026, against {o('X7', 'en')} in 2018: {d[0]} points, from {d[1]} to {d[2]}, a gap that survives the correction (p = {pv(t['p_holm'], 'en')})")
add("F2 Q3", f"tous donnés dans {c('Q3')} des articles, contre {o('Q3')} en 2018 : nous ne détectons aucun changement (p = {pv(main('Q3')['p_holm'])})",
    f"given in {c('Q3', 'en')} of papers, against {o('Q3', 'en')} in 2018: we detect no change (p = {pv(main('Q3')['p_holm'], 'en')})")
add("F2 Pineau", f"contre les {pin('Q3')} de Pineau vient de notre grille", f"against Pineau's {pin('Q3', 'en')} comes from our grid")
(k10, n10), (o10, m10), (a10, b10) = cnt("Y10", "classic2026"), cnt("Y10", "ours2018"), cnt("Y10", "all2026")
assert a10 == 1
add("F3 Y10", f"{k10} articles de RL classique sur {n10} les donnent en 2026, contre {o10} sur {m10} en 2018 (critère Y10)",
    f"{k10} classical RL papers out of {n10} give them in 2026, against {o10} out of {m10} in 2018 (criterion Y10)")
add("F3 Y10 all", f"un seul article sur {b10} les donne", f"a single paper out of {b10} gives them")
t = main("Q6"); d = gap(t, signed=False)
add("F4 Q3", f"tous donnés dans {c('Q3')} des articles de 2026, contre {o('Q3')} en 2018, sans changement",
    f"given in {c('Q3', 'en')} of 2026 papers, against {o('Q3', 'en')} in 2018, with no detectable change")
add("F5 Q6", f"décrite dans {c('Q6')} des articles de 2026, contre {o('Q6')} en 2018 : un écart de {d[0]} points, de {d[1]} à {d[2]}",
    f"described in {c('Q6', 'en')} of 2026 papers, against {o('Q6', 'en')} in 2018: a gap of {d[0]} points, from {d[1]} to {d[2]}")
add("F5 p", f"l'écart ne passe plus le seuil (p = {pv(t['p_holm'])})", f"the gap no longer clears the threshold (p = {pv(t['p_holm'], 'en')})")
t = main("Y9"); d = gap(t, signed=False); y9a = cnt("Y9", "all2026")
add("F6", f"{c('Y9')} des articles de 2026, contre {o('Y9')} en 2018 : un écart de {d[0]} points, de {d[1]} à {d[2]}, qui résiste à la correction (p = {pv(t['p_holm'])})",
    f"{c('Y9', 'en')} of 2026 papers do so, against {o('Y9', 'en')} in 2018: a gap of {d[0]} points, from {d[1]} to {d[2]}, which survives the correction (p = {pv(t['p_holm'], 'en')})")
add("F6 all", f"{y9a[0]} articles sur {y9a[1]}", f"{y9a[0]} papers out of {y9a[1]}")
add("F7 Q4", f"donnés dans {c('Q4')} des articles de RL classique de 2026, contre {o('Q4')} dans notre lecture de 2018",
    f"given in {c('Q4', 'en')} of classical RL papers from 2026, against {o('Q4', 'en')} in our reading of 2018")
add("F7 X4", f"passent de {o('X4')} à {c('X4')}", f"go from {o('X4', 'en')} to {c('X4', 'en')}")
add("F7 Pineau", f"Contre les {pin('Q4')} de Pineau", f"Against Pineau's {pin('Q4', 'en')}")
add("F7 grid", f"qui trouve {o('Q4')} en 2018", f"which finds {o('Q4', 'en')} in 2018")
add("F7 all", f"tout le premier tirage tombe à {a26('Q4')}", f"the whole first draw falls to {a26('Q4', 'en')}")
y2c, y2o = cnt("Y2", "classic2026"), cnt("Y2", "ours2018")
add("F8 Y1", f"{c('Y1')} des articles de 2026 le disent, contre {o('Y1')} en 2018", f"{c('Y1', 'en')} of 2026 papers say so, against {o('Y1', 'en')} in 2018")
add("F8 Y2", f"{y2c[0]} articles sur {y2c[1]} en 2026, contre {y2o[0]} sur {y2o[1]} en 2018 (critère Y2)",
    f"{y2c[0]} papers out of {y2c[1]} in 2026, against {y2o[0]} out of {y2o[1]} in 2018 (criterion Y2)")
add("F10 X3", f"{c('X3')} des articles de RL classique de 2026 la laissent voir, contre {o('X3')} en 2018",
    f"{c('X3', 'en')} of classical RL papers from 2026 let it show, against {o('X3', 'en')} in 2018")
t = main("X2"); d = gap(t, signed=False); y11c, y11o = cnt("Y11", "classic2026"), cnt("Y11", "ours2018")
assert y11c[1] == cnt("X2", "classic2026")[0]  # "des 44 articles de 2026 qui en rapportent une"
add("F12 X2", f"{c('X2')} des articles de 2026 le font, contre {o('X2')} en 2018, un écart de {d[0]} points, de {d[1]} à {d[2]}, qui résiste à la correction (p = {pv(t['p_holm'])})",
    f"{c('X2', 'en')} of 2026 papers do it, against {o('X2', 'en')} in 2018, a gap of {d[0]} points, from {d[1]} to {d[2]}, which survives the correction (p = {pv(t['p_holm'], 'en')})")
add("F12 Y11", f"nommé dans {y11c[0]} des {y11c[1]} articles de 2026 qui en rapportent une, contre {y11o[0]} sur {y11o[1]} en 2018",
    f"named in {y11c[0]} of the {y11c[1]} papers from 2026 that report one, against {y11o[0]} out of {y11o[1]} in 2018")
add("F12 Q8", f"{c('Q8')} des articles de 2026, contre {o('Q8')} en 2018", f"{c('Q8', 'en')} of 2026 papers, against {o('Q8', 'en')} in 2018")
t = main("Y12"); d = gap(t)
add("F12 Y12", f"passent de {o('Y12')} à {c('Y12')} des articles", f"go from {o('Y12', 'en')} to {c('Y12', 'en')} of papers")
add("F12 Y12 gap", f"de {d[1]} à {d[2]} points, sans passer la correction (p = {pv(t['p_holm'])})",
    f"from {d[1]} to {d[2]} points, without passing the correction (p = {pv(t['p_holm'], 'en')})")
y3c, y3o, y4c, y4o, y3a = cnt("Y3", "classic2026"), cnt("Y3", "ours2018"), cnt("Y4", "classic2026"), cnt("Y4", "ours2018"), cnt("Y3", "all2026")
assert y4c[1] == y3c[0] and y4o[1] == y3o[0]  # Y4 is asked of the papers with several tasks
add("F13 Y3", f"plusieurs tâches dans {y3c[0]} articles sur {y3c[1]} en 2026, contre {y3o[0]} sur {y3o[1]} en 2018 (critère Y3)",
    f"several tasks in {y3c[0]} papers out of {y3c[1]} in 2026, against {y3o[0]} out of {y3o[1]} in 2018 (criterion Y3)")
add("F13 Y4", f"{y4c[0]} sur {y4c[1]} montrent", f"{y4c[0]} out of {y4c[1]} show")
add("F13 Y4 2018", f"contre {y4o[0]} sur {y4o[1]} en 2018 (critère Y4)", f"against {y4o[0]} out of {y4o[1]} in 2018 (criterion Y4)")
add("F14 Y5", f"dite dans {c('Y5')} des articles de 2026, contre {o('Y5')} en 2018 (critère Y5)",
    f"stated in {c('Y5', 'en')} of 2026 papers, against {o('Y5', 'en')} in 2018 (criterion Y5)")
add("F13 all", f"{y3a[0]} articles sur {y3a[1]} seulement", f"only {y3a[0]} papers out of {y3a[1]}")
add("F15 grid", f"notre lecture de 2018 trouve déjà {o('Q7')}", f"our reading of 2018 already finds {o('Q7', 'en')}")
add("F15 Q7", f"le RL classique passe de {o('Q7')} à {c('Q7')}", f"classical RL goes from {o('Q7', 'en')} to {c('Q7', 'en')}")
add("F15 Y8", f"Il passe de {o('Y8')} à {c('Y8')} des articles", f"It goes from {o('Y8', 'en')} to {c('Y8', 'en')} of papers")
add("F16 Y7", f"{c('Y7')} des articles de 2026 la donnent pour tous leurs bancs d'essai, contre {o('Y7')} en 2018 (critère Y7)",
    f"{c('Y7', 'en')} of 2026 papers give it for all their benchmarks, against {o('Y7', 'en')} in 2018 (criterion Y7)")
add("limits llm", f"{len(llm)} articles du premier tirage de 2026 sur 50", f"{len(llm)} of the 50 papers of the first 2026 draw")

# E6 diagnostic (analysis/e6_diag.py): IQM with bootstrap interval per group, probability of improvement.
e6 = J("sim/analysis/e6_diag.json")
iv = lambda g, lang="fr": f"{num(g['iqm'], lang)} [{num(g['iqm_ci'][0], lang)}, {num(g['iqm_ci'][1], lang)}]"
for k in ("default v5", "zoo v5 (bug)", "zoofix v5", "zoofix v4", "default v4"):
    add(f"E6 {k}", iv(e6["groups"][k]), "")
pb = next(c for c in e6["comparisons"] if c["b"] == "zoo v5 (bug)")
add("E6 bug vs fix", f"vaut {pb['p_improve']:.2f}".replace(".", ","), "")
# E1, final scores.
add("E1 mean, sd, median", f"Moyenne {num(e1['mean'])}, écart type {num(e1['sd'])}, médiane {num(e1['median'])}",
    f"Mean {num(e1['mean'], 'en')}, standard deviation {num(e1['sd'], 'en')}, median {num(e1['median'], 'en')}")
add("E1 cv", f"L'écart type vaut {pct(e1['cv'])} de la moyenne", f"The standard deviation equals {pct(e1['cv'], lang='en')} of the mean")
sh = f"{e1['shapiro_p']:.0e}"; mant, ex = sh.split("e-")
add("E1 shapiro", f"p = {mant} × 10^−{int(ex)}^", f"p = {mant} × 10^−{int(ex)}^")
s27 = sorted(e1["seeds_sorted"])
add("E1 27 runs range", f"entre {num(s27[0])} et {num(s27[26])}", f"between {num(s27[0], 'en')} and {num(s27[26], 'en')}")
for k, fr_lab, en_lab in (("random_3v3", "3 essais contre 3", "3 runs against 3"), ("random_5v5", "5 essais contre 5", "5 runs against 5"),
                          ("random_10v10", "10 essais contre 10", "10 runs against 10")):
    r = e1[k]
    add(f"E1 {k}", f"{fr_lab}, tirés au hasard | {pct(r['false_positive'], 1)} | {pct(r['median_gap'])} | {pct(r['p95_gap'])}",
        f"{en_lab}, drawn at random | {pct(r['false_positive'], 1, 'en')} | {pct(r['median_gap'], lang='en')} | {pct(r['p95_gap'], lang='en')}")
r = e1["extreme_5v5_of_10"]
add("E1 sorted cut", f"{pct(r['false_positive'], 1)} | {pct(r['median_gap'])}", f"{pct(r['false_positive'], 1, 'en')} | {pct(r['median_gap'], lang='en')}")
r = e1["top3_of_10"]
add("E1 top-3 inflation", f"{pct(r['inflation'])} ({num(r['mean_top3'])} contre {num(r['mean_all'])})",
    f"{pct(r['inflation'], lang='en')} ({num(r['mean_top3'], 'en')} against {num(r['mean_all'], 'en')})")
# E1, Henderson's statistic (e1_curve.py).
q_r, q_s = curve["random_5v5"]["abs_mean_t_p95"], curve["sorted_5v5"]["abs_mean_t_p95"]
add("curve p95", f"dépasse {half_up(q_r, 1)} quand les groupes sont tirés au hasard, {half_up(q_s, 1)} quand on les trie".replace(".", ","),
    f"exceeds {half_up(q_r, 1)} when the groups are drawn at random, {half_up(q_s, 1)} when")
assert curve["random_5v5"]["share_abs_mean_t_ge_9"] == 0 and curve["sorted_5v5"]["share_abs_mean_t_ge_9"] == 0
# B1, Henderson's statistic with TRPO (b1_trpo.py).
tr, pp = b1["trpo"], b1["ppo_sb3"]
fr1 = lambda x: str(half_up(x, 1)).replace(".", ",")
add("B1 spread", f"son écart type vaut {pct(tr['cv'])} de sa moyenne, contre {pct(pp['cv'])} pour PPO",
    f"its standard deviation is {pct(tr['cv'], lang='en')} of its mean, against {pct(pp['cv'], lang='en')} for PPO")
add("B1 mean t", f"le t moyen ne dépasse {fr1(tr['random_5v5']['mean_t']['abs_t_p95'])} qu'une fois sur vingt, comme pour PPO ; triés, {fr1(tr['sorted_5v5']['mean_t']['abs_t_p95'])}",
    f"the average t exceeds {half_up(tr['random_5v5']['mean_t']['abs_t_p95'], 1)} only one time in twenty, as with PPO; sorted, {half_up(tr['sorted_5v5']['mean_t']['abs_t_p95'], 1)}")
add("B1 pooled", f"Elle monte à {fr1(tr['random_5v5']['pooled']['abs_t_p95'])} au hasard et à {fr1(tr['sorted_5v5']['pooled']['abs_t_p95'])} triés",
    f"It rises to {half_up(tr['random_5v5']['pooled']['abs_t_p95'], 1)} at random and {half_up(tr['sorted_5v5']['pooled']['abs_t_p95'], 1)} sorted")
add("B1 pooled FP", f"elle déclare une différence dans {pct(tr['random_5v5']['pooled']['false_positive'])} des tirages au hasard",
    f"it declares a difference in {pct(tr['random_5v5']['pooled']['false_positive'], lang='en')} of random draws")
assert half_up(tr["random_5v5"]["mean_t"]["abs_t_p95"], 1) == half_up(curve["random_5v5"]["abs_mean_t_p95"], 1)  # "comme pour PPO"
assert all(r[m]["share_abs_t_ge_henderson"] == 0 for a in b1.values() if isinstance(a, dict) and "cv" in a
           for s in ("random_5v5", "sorted_5v5") for r in [a[s]] for m in r)  # "Aucun tirage, dans aucune lecture"

# B1, Henderson's own script (b1_script.py).
bs = J("sim/analysis/b1_script.json")
st, sp = bs["trpo"]["n10"]["random_5v5"], bs["ppo_sb3"]
add("B1 script", f"le t moyen dépasse 9,09 dans {pct(st['share_abs_t_ge_henderson'])} des tirages au hasard, et le test déclare une différence dans {pct(st['false_positive'])} d'entre eux",
    f"the average t exceeds 9.09 in {pct(st['share_abs_t_ge_henderson'], lang='en')} of random draws, and the test declares a difference in {pct(st['false_positive'], lang='en')} of them")
add("B1 script ratio", f"ne vaut que {pct(bs['trpo']['eval_std_over_between_seed_sd'])} de l'écart type entre agents",
    f"is only {pct(bs['trpo']['eval_std_over_between_seed_sd'], lang='en')} of the standard deviation between agents")
add("B1 script summary", f"il dépasse 9 dans {pct(st['share_abs_t_ge_henderson'])} des tirages au hasard",
    f"it exceeds 9 in {pct(st['share_abs_t_ge_henderson'], lang='en')} of random draws")
assert all(sp[n][s]["share_abs_t_ge_henderson"] == 0 for n in ("n10", "n5") for s in ("random_5v5", "sorted_5v5"))  # "n'atteint jamais 9"

# Écart 21, the thesis against blind ratings (robustness.py).
rb = J("study/robustness.json")
assert not any(rb["a"][k]["fragile"] for k in ("Q5", "Y9", "X7", "X2"))  # "Ces quatre hausses résistent à toutes les coupes"
sg = lambda x, lang: ("+" if x >= 0 else "−") + (f"{abs(x):.2f}".replace(".", ",") if lang == "fr" else f"{abs(x):.2f}")
add("thesis rho", f"vaut {sg(rb['b']['C']['rho'], 'fr')} pour le coût et {sg(rb['b']['R']['rho'], 'fr')} pour le risque",
    f"is {sg(rb['b']['C']['rho'], 'en')} for cost and {sg(rb['b']['R']['rho'], 'en')} for risk")
assert rb["b"]["C"]["p_two_sided"] > .2 and rb["b"]["R"]["p_two_sided"] > .2  # "rien qui se distingue du hasard"

# E3, two implementations of PPO (e3.py).
e3 = J("sim/analysis/e3.json")
assert all(r["winner"] is None for r in e3.values())  # "sur aucune des quatre tâches, l'une des deux versions ne l'emporte"
w = e3["Walker2d-v5"]
add("E3 walker", f"vaut {num(w['iqm']['sb3'], 'fr')} avec PyTorch et {num(w['iqm']['sbx'], 'fr')} avec JAX, {pct(1 - w['iqm_ratio_sbx_over_sb3'])} de moins",
    f"is {num(w['iqm']['sb3'], 'en')} with PyTorch and {num(w['iqm']['sbx'], 'en')} with JAX, {pct(1 - w['iqm_ratio_sbx_over_sb3'], lang='en')} lower")
assert w["intervals_overlap"]

# E7, held out (e7.py), three algorithms while CrossQ runs.
e7 = {k: v for k, v in J("sim/analysis/e7.json").items() if v["done"]}
assert len(e7) == 12 and sum(v["verdict"] == "loss" for v in e7.values()) == 9  # "9 couples ... sur 12"
assert all(v["verdict"] != "loss" for k, v in e7.items() if k.endswith("Swimmer-v5"))  # "Sur Swimmer, aucun ne perd"
add("E7 hopper", f"PPO ne garde que {pct(e7['ppo_sb3/Hopper-v5']['iqm'])} de son score dans sa version PyTorch et {pct(e7['ppo_sbx/Hopper-v5']['iqm'])} dans sa version JAX, quand SAC en garde {pct(e7['sac/Hopper-v5']['iqm'])}",
    f"PPO keeps only {pct(e7['ppo_sb3/Hopper-v5']['iqm'], lang='en')} of its score in its PyTorch version and {pct(e7['ppo_sbx/Hopper-v5']['iqm'], lang='en')} in its JAX version, while SAC keeps {pct(e7['sac/Hopper-v5']['iqm'], lang='en')}")

# E6, the official Zoo pipeline (e6_official.py).
e6o = J("sim/analysis/e6_official.json")
g = e6o["groups"]
ci = lambda k, lang: f"{num(g[k]['iqm'], lang)} [{num(g[k]['iqm_ci'][0], lang)}, {num(g[k]['iqm_ci'][1], lang)}]"
cmp_def = [c for c in e6o["comparisons"] if c["b"] == "default v4"][0]
add("E6 official", f"Les dix agents officiels obtiennent {ci('official v4', 'fr')}, autant que notre recette corrigée ({ci('zoofix v4', 'fr')})",
    f"The ten official agents score {ci('official v4', 'en')}, as much as our corrected recipe ({ci('zoofix v4', 'en')})")
add("E6 default", f"obtiennent {ci('default v4', 'fr')}. Un agent officiel ne bat un agent par défaut qu'avec une probabilité de {str(half_up(cmp_def['p_improve'], 2)).replace('.', ',')}",
    f"score {ci('default v4', 'en')}. An official agent beats a default agent with a probability of only {half_up(cmp_def['p_improve'], 2)}")
assert half_up(cmp_def["welch_p_holm"], 3) == half_up(0.001, 3)

norm = lambda s: re.sub(r"\s+", " ", s)
bad = 0
for name, lang in (("conclusions.md", 0), ("conclusions-en.md", 1)):
    p = ROOT / "docs" / name
    if not p.exists():
        continue
    text = norm(p.read_text())
    for c in C:
        want = norm(c[1 + lang])
        if want and want not in text:
            print(f"{name}: missing [{c[0]}] {want!r}")
            bad += 1
print(f"{len(C)} claims checked, {bad} missing")
sys.exit(1 if bad else 0)
