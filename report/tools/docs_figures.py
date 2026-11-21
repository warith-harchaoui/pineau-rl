"""The six figures of docs/, redrawn in the house style for the report: figures/src/<name>-<lang>.svg.

  e1-henderson       the t statistic of Henderson et al. (2018): which way of computing it reaches 9
  ecarts-classique   classical RL 2026 against our reading of 2018, seventeen criteria, Newcombe intervals
  ecarts-pineau      the first 2026 draw against Pineau's figures of 2018, six criteria
  remesure-dumbbell  Pineau's grid, 2018 against 2026, five criteria
  remesure-ic        what the 2026 papers report, eight criteria with their Wilson interval
  grpo-truncation    the base model's answers on the pilot's step-10 batch: right, wrong, cut at 160 tokens

Same names as docs/figures/<name>.svg, same data: the numbers come from docs/figures/data/*.csv (written by
docs/figures/build.py from the result files), the Holm-adjusted p-values that pick the highlighted rows from
study/extension_stats.json and study/audit_stats.json, the files those CSVs come from. docs/ stays untouched.
Drawn with the article's toolkit (article/figures/draw.py) through the helpers of tools/diagrams.py.
"""
import csv
import json
from pathlib import Path

import diagrams as G

D, tx, glue = G.D, G.tx, G.glue
INK, INK2, RULE, GRID, PANEL, PAPER, SOFT = G.INK, G.INK2, G.RULE, G.GRID, G.PANEL, G.PAPER, G.SOFT
RED, GREEN = D.RED, D.GREEN
C18, C26 = G.C18, G.C26
NEUTRAL = "#7D8694"
ROOT, OUT = G.ROOT, G.OUT
DATA = ROOT / "docs" / "figures" / "data"
REDT, GREENT = "#B8352E", "#237A45"   # red and green text, darkened to clear 4.5:1 on white and on their tints


def rows(name, lang):
    with open(DATA / f"{name}_{lang}.csv", encoding="utf-8") as fh:
        return list(csv.reader(fh))[1:]


def fig(T):
    return G.figure(T, T.get("accent", INK))


def pts(v, lang, sign=True):
    return D.num(v, lang, 0, sign)


# ---------------------------------------------------------------------------------------------------------------
# Intervals: one row per criterion, a dot and its 95% interval, the gap labelled at the right


def interval_rows(f, items, lang, lo, hi, step, label_w, unit, zero=True, head=None, legend=None):
    """items: (label, value, low, high, colour, strong). Returns the y below the axis."""
    s, L, W = f.s, f.L, f.W
    x0, x1 = L + label_w, W - L - 40
    X = lambda u: x0 + (u - lo) / (hi - lo) * (x1 - x0)
    y = f.top + 4
    if legend:
        y = f.legend(legend, y + 8) - 6
    if head:
        left, right = head
        if left:
            tx(s, X(0) - 8, y + 8, left, "sans5", 13, SOFT, "end")
        tx(s, X(0) + 8, y + 8, right, "sans5", 13, GREENT)
        y += 18
    rh, top = 26, y
    for i, (lab, v, a, b, col, strong) in enumerate(items):
        if strong:
            yc = top + i * rh + rh / 2
            s.rect(L - 6, yc - rh / 2 + 2, W - 2 * L + 12, rh - 4, D.tint(col, 0.88), rx=4)
    under = len(s.parts)      # the grid goes here: over the bands, under the rows
    for i, (lab, v, a, b, col, strong) in enumerate(items):
        yc = top + i * rh + rh / 2
        bg = D.tint(col, 0.88) if strong else PAPER
        tx(s, x0 - 14, yc + 4.3, lab, "sans7" if strong else "sans", 13, INK if strong else INK2, "end", bg=bg)
        s.line(X(a), yc, X(b), yc, col, 2.4 if strong else 1.8, ' stroke-linecap="round"')
        for e in (a, b):
            s.line(X(e), yc - 5, X(e), yc + 5, col, 1.6)
        s.circle(X(v), yc, 6 if strong else 4.8, col, f' stroke="{bg}" stroke-width="1.5"')
        tcol = {RED: REDT, GREEN: GREENT}.get(col, INK2)
        tx(s, X(b) + 9, yc + 4.3, pts(v, lang, zero) + ("" if zero else unit), "sans7" if strong else "sans5",
           13, tcol, bg=bg)
    bottom = top + len(items) * rh
    grid = []
    for t in D.ticks(lo, hi, step):
        grid.append(f'<line x1="{X(t):.1f}" y1="{top:.1f}" x2="{X(t):.1f}" y2="{bottom:.1f}" '
                    f'stroke="{RULE if (zero and t == 0) else GRID}" stroke-width="{1.4 if (zero and t == 0) else 1}"/>')
        lab = (pts(t, lang, True) if zero else D.num(t, lang)) + ("" if zero else unit)
        tx(s, X(t), bottom + 17, lab, "mono", 13, SOFT, "middle")
    s.parts[under:under] = grid
    return bottom + 22, X


# ---------------------------------------------------------------------------------------------------------------


def ecarts_classique(lang):
    fr = lang == "fr"
    ext = {r["k"]: r["classic_vs_ours2018"] for r in json.load(open(ROOT / "study/extension_stats.json"))["rows"]}
    items = []
    for lab, v, a, b in rows("ecarts_classique", lang):
        k = lab.rsplit("(", 1)[1].rstrip(")")
        ok = ext[k]["p_holm"] < 0.05
        assert round(ext[k]["diff"] * 100) == int(v)
        items.append((lab, int(v), int(a), int(b), GREEN if ok else NEUTRAL, ok))
    n_ok = sum(it[5] for it in items)
    assert n_ok == 4 and len(items) == 17
    T = {"title": ("À grille égale, quatre pratiques sur dix-sept |progressent nettement entre 2018 et 2026" if fr else
                   "With the same grid, four practices out of seventeen |clearly rise between 2018 and 2026"),
         "sub": ("RL classique : 50 articles de 2026 contre nos 50 de 2018, mêmes grilles, mêmes lecteurs ; "
                 "écart en points avec son intervalle de Newcombe à 95 %" if fr else
                 "Classical RL: 50 papers from 2026 against our 50 from 2018, same grids, same readers; "
                 "gap in points with its 95% Newcombe interval"),
         "accent": GREEN,
         "desc": ("Pour dix-sept critères de lecture, l'écart en points entre la part des articles de RL classique de "
                  "2026 et celle de nos articles de 2018, avec son intervalle à 95 %. Quatre critères, surlignés en "
                  "vert, passent la correction de Holm : code en lien, balayage montré, calcul chiffré, incertitude."
                  if fr else
                  "For seventeen reading criteria, the gap in points between the share of classical RL papers of 2026 "
                  "and that of our 2018 papers, with its 95% interval. Four criteria, highlighted in green, pass "
                  "Holm's correction: code linked, sweep shown, compute quantified, uncertainty.")}
    f = fig(T)
    y, _ = interval_rows(f, items, lang, -30, 60, 15, 214, "", head=(
        "moins fréquent en 2026" if fr else "less common in 2026",
        "plus fréquent en 2026" if fr else "more common in 2026"),
        legend=[("passe la correction de Holm (p < 0,05)" if fr else "passes Holm's correction (p < 0.05)", GREEN),
                ("ne la passe pas" if fr else "does not pass it", NEUTRAL)])
    return G.finish(f, y, "Données : study/extension_stats.json ; "
                       "test exact de Fisher, correction de Holm par grille" if fr else
                    "Data: study/extension_stats.json; "
                    "Fisher's exact test, Holm's correction per grid")


PINEAU_KEYS = ("Q3", "Q4", "Q5", "Q6", "Q7", "Q8")   # the order of build.py
PINEAU_LAB = {"fr": ["Hyperparamètres de la méthode (Q3)", "Hyperparamètres des références (Q4)", "Code en lien (Q5)",
                     "Choix des hyperparamètres (Q6)", "Évaluation tenue à part (Q7)", "Test statistique (Q8)"],
              "en": ["Method hyperparameters (Q3)", "Baseline hyperparameters (Q4)", "Code linked (Q5)",
                     "Tuning method (Q6)", "Held-out evaluation (Q7)", "Statistical test (Q8)"]}


def ecarts_pineau(lang):
    fr = lang == "fr"
    audit = {r["k"]: r["vs_pineau"] for r in json.load(open(ROOT / "study/audit_stats.json"))["rows"] if "vs_pineau" in r}
    items = []
    for k, lab, (_, v, a, b) in zip(PINEAU_KEYS, PINEAU_LAB[lang], rows("ecarts_pineau", lang)):
        v, a, b = int(v), int(a), int(b)
        assert round(audit[k]["diff"] * 100) == v
        sig = audit[k]["p_holm"] < 0.05
        col = (GREEN if v > 0 else RED) if sig else NEUTRAL
        items.append((v, (lab, v, a, b, col, sig)))
    items = [it for _, it in sorted(items, key=lambda t: -t[0])]
    T = {"title": ("Face aux chiffres de Pineau, l'évaluation tenue à part |gagne 60 points, "
                   "les hyperparamètres en perdent" if fr else
                   "Against Pineau's figures, held-out evaluation |gains 60 points, hyperparameters lose ground"),
         "sub": ("45 articles expérimentaux de 2026 contre ses 50 de 2018 ; écart en points, intervalle de "
                 "Newcombe à 95 %. Les grilles diffèrent : un contexte, pas un verdict" if fr else
                 "45 experimental papers from 2026 against her 50 from 2018; gap in points, 95% Newcombe interval. "
                 "The grids differ: context, not a verdict"),
         "accent": GREEN,
         "desc": ("Six critères de la grille de Pineau : écart entre la part des 45 articles expérimentaux de notre "
                  "premier tirage de 2026 et celle de ses 50 articles de 2018. L'évaluation tenue à part gagne 60 "
                  "points ; les hyperparamètres des références et de la méthode reculent ; code, choix des "
                  "hyperparamètres et test statistique ne bougent pas de façon détectable." if fr else
                  "Six criteria of Pineau's grid: gap between the share of the 45 experimental papers of our first "
                  "2026 draw and that of her 50 papers from 2018. Held-out evaluation gains 60 points; baseline and "
                  "method hyperparameters fall; code, tuning method and statistical test do not move detectably.")}
    f = fig(T)
    y, _ = interval_rows(f, items, lang, -60, 80, 20, 250, "", head=(
        "moins fréquent en 2026" if fr else "less common in 2026",
        "plus fréquent en 2026" if fr else "more common in 2026"),
        legend=[("hausse après correction de Holm" if fr else "rise after Holm's correction", GREEN),
                ("baisse après correction de Holm" if fr else "fall after Holm's correction", RED),
                ("rien de détectable" if fr else "nothing detectable", NEUTRAL)])
    return G.finish(f, y, "Données : study/audit_stats.json ; "
                       "Pineau, NeurIPS 2018, diapositives 29 et 30" if fr else
                    "Data: study/audit_stats.json; "
                    "Pineau, NeurIPS 2018, slides 29 and 30")


IC_LAB = {"fr": ["Références réglées comme la méthode", "Test statistique", "Hyperparamètres des références",
                 "Choix des hyperparamètres décrit", "Incertitude rapportée", "Calcul chiffré", "Code en lien",
                 "Évaluation tenue à part"],
          "en": ["Baselines tuned like the method", "Statistical test", "Baseline hyperparameters",
                 "Tuning method described", "Uncertainty reported", "Compute stated", "Code linked",
                 "Held-out evaluation"]}


def remesure_ic(lang):
    fr = lang == "fr"
    src = rows("remesure_ic", lang)
    assert len(src) == 8
    items = []
    for lab, (_, v, a, b) in zip(IC_LAB[lang], src):
        v, a, b = int(v), int(a), int(b)
        col = RED if v < 10 else C26
        items.append((lab, v, a, b, col, v < 10 or v > 60))
    items.sort(key=lambda it: -it[1])
    T = {"title": ("En 2026, deux articles sur trois lient leur code, |4 % font un test statistique" if fr else
                   "In 2026, two papers in three link their code, |4% run a statistical test"),
         "sub": ("Part des 45 articles expérimentaux du premier tirage de 2026 (44 pour trois critères), "
                 "intervalle de Wilson à 95 %" if fr else
                 "Share of the 45 experimental papers of the first 2026 draw (44 for three criteria), "
                 "95% Wilson interval"),
         "accent": C26,
         "desc": ("Huit critères de la grille de Pineau, part des articles expérimentaux de 2026 qui les "
                  "remplissent, avec l'intervalle de Wilson. En tête l'évaluation tenue à part (70 %) et le code en "
                  "lien (67 %) ; en bas les références réglées comme la méthode (5 %) et le test statistique (4 %)."
                  if fr else
                  "Eight criteria of Pineau's grid, share of the experimental papers of 2026 that meet them, with "
                  "the Wilson interval. At the top held-out evaluation (70%) and code linked (67%); at the bottom "
                  "baselines tuned like the method (5%) and statistical test (4%).")}
    f = fig(T)
    unit = " %" if fr else "%"
    y, _ = interval_rows(f, items, lang, 0, 100, 25, 250, unit, zero=False)
    return G.finish(f, y, "Données : study/RESULTS.md, "
                       "codes de study/codes/" if fr else
                    "Data: study/RESULTS.md, readings in study/codes/")


def remesure_dumbbell(lang):
    fr = lang == "fr"
    src = [(lab, int(a), int(b)) for lab, a, b in rows("remesure_dumbbell", lang)]
    src.sort(key=lambda r: -(r[2] - r[1]))
    T = {"title": ("De 2018 à 2026, l'évaluation tenue à part |passe de 10 % à 70 % des articles" if fr else
                   "From 2018 to 2026, held-out evaluation |goes from 10% to 70% of papers"),
         "sub": ("Part des articles expérimentaux : les 50 de Pineau en 2018, nos 45 du premier tirage de 2026. "
                 "Les grilles diffèrent : un contexte" if fr else
                 "Share of experimental papers: Pineau's 50 in 2018, our 45 of the first 2026 draw. "
                 "The grids differ: context"),
         "accent": C26,
         "desc": ("Cinq critères de la grille de Pineau, deux points par critère : sa part en 2018, la nôtre en "
                  "2026, reliés par un trait vert quand la part monte, rouge quand elle descend. L'évaluation tenue "
                  "à part passe de 10 % à 70 % ; les hyperparamètres des références de 60 % à 18 %." if fr else
                  "Five criteria of Pineau's grid, two dots per criterion: her share in 2018, ours in 2026, joined "
                  "by a green line when the share rises, red when it falls. Held-out evaluation goes from 10% to "
                  "70%; baseline hyperparameters from 60% to 18%.")}
    f = fig(T)
    s, L, W = f.s, f.L, f.W
    unit = " %" if fr else "%"
    lw = 236
    x0, x1 = L + lw, W - L - 64
    X = lambda u: x0 + u / 100 * (x1 - x0)
    y = f.legend([("2018, Pineau" if fr else "2018, Pineau", C18), ("2026, nous" if fr else "2026, us", C26)],
                 f.top + 12) + 2
    tx(s, W - L, y - 26, "écart" if fr else "gap", "sans7", 13, SOFT, "end")
    rh, top = 46, y
    for i in range(0, len(src), 2):
        s.rect(L - 6, top + i * rh + 3, W - 2 * L + 12, rh - 6, PANEL, rx=4)
    under = len(s.parts)
    for i, (lab, a, b) in enumerate(src):
        yc = top + i * rh + rh / 2
        up = b > a
        col = GREEN if up else RED
        bg = PANEL if i % 2 == 0 else PAPER
        tx(s, x0 - 16, yc + 4.5, lab, "sans5", 13, INK, "end", bg=bg)
        s.line(X(a), yc, X(b), yc, col, 4, ' stroke-linecap="round" opacity="0.55"')
        for v, c in ((a, C18), (b, C26)):
            s.circle(X(v), yc, 7.5, c, f' stroke="{bg}" stroke-width="2"')
        # each value outside its own dot: the smaller to the left, the larger to the right
        lo_v, hi_v = (a, b) if a < b else (b, a)
        lo_c, hi_c = (C18, C26) if a < b else (C26, C18)
        tx(s, X(lo_v) - 13, yc + 4.5, D.num(lo_v, lang) + unit, "sans7", 13, shade_txt(lo_c), "end", bg=bg)
        tx(s, X(hi_v) + 13, yc + 4.5, D.num(hi_v, lang) + unit, "sans7", 13, shade_txt(hi_c), bg=bg)
        tx(s, W - L, yc + 4.5, pts(b - a, lang), "sans7", 13, REDT if not up else GREENT, "end", bg=bg)
    bottom = top + len(src) * rh
    grid = []
    for t in D.ticks(0, 100, 25):
        grid.append(f'<line x1="{X(t):.1f}" y1="{top:.1f}" x2="{X(t):.1f}" y2="{bottom:.1f}" stroke="{GRID}" '
                    f'stroke-width="1"/>')
        tx(s, X(t), bottom + 17, D.num(t, lang) + unit, "mono", 13, SOFT, "middle")
    s.parts[under:under] = grid
    return G.finish(f, bottom + 22, "Données : study/RESULTS.md ; "
                                 "Pineau, NeurIPS 2018, diapositives 29 et 30" if fr else
                    "Data: study/RESULTS.md; "
                    "Pineau, NeurIPS 2018, slides 29 and 30")


def shade_txt(c):
    return G.shade(c, 0.12)


def e1_henderson(lang):
    fr = lang == "fr"
    src = [(lab, float(v)) for lab, v in rows("e1_henderson", lang)]
    ref = [v for lab, v in src if lab.startswith("Henderson")]
    bars = [(lab, v) for lab, v in src if not lab.startswith("Henderson")]
    assert len(ref) == 1 and len(bars) == 6
    ref = ref[0]
    script = max(bars, key=lambda b: b[1])
    T = {"title": ("Seul le script de Henderson dépasse le t de 2018 : |la dispersion des graines n'y suffit pas" if fr
                   else "Only Henderson's script exceeds the 2018 t: |the spread between seeds cannot reach it"),
         "sub": ("HalfCheetah, deux groupes de cinq essais parmi trente : 95e centile, sur 10 000 tirages, de la "
                 "valeur absolue du t moyen le long de la courbe" if fr else
                 "HalfCheetah, two groups of five runs out of thirty: 95th percentile, over 10,000 draws, of the "
                 "absolute mean t along the learning curve"),
         "accent": RED,
         "desc": ("Six façons de calculer la statistique de Henderson et al. sur nos essais de PPO et de TRPO. "
                  "Groupes au hasard ou triés, la statistique reste sous 3 ; empiler les points la porte à 5. Seul "
                  "le script publié par Henderson, qui mesure la dispersion des épisodes, atteint 22,3, au-delà du "
                  "t de 9,1 publié en 2018." if fr else
                  "Six ways of computing the statistic of Henderson et al. on our PPO and TRPO runs. Random or "
                  "sorted groups keep it under 3; stacking the points takes it to 5. Only the script Henderson "
                  "published, which measures the spread between episodes, reaches 22.3, beyond the t of 9.1 "
                  "published in 2018.")}
    f = fig(T)
    s, L, W = f.s, f.L, f.W
    lw = 200
    x0, x1 = L + lw, W - L - 50
    X = lambda u: x0 + u / 25 * (x1 - x0)
    bh, gap = 26, 12
    top = f.top + 20
    bottom = top + len(bars) * (bh + gap) - gap
    for t_ in D.ticks(0, 25, 5):
        s.line(X(t_), top - 4, X(t_), bottom + 4, RULE if t_ == 0 else GRID)
        tx(s, X(t_), bottom + 20, D.num(t_, lang), "mono", 13, SOFT, "middle")
    for i, (lab, v) in enumerate(bars):
        yy = top + i * (bh + gap)
        hit = (lab, v) == script
        col = REDT if hit else NEUTRAL
        tx(s, x0 - 12, yy + bh / 2 + 4.5, lab, "sans7" if hit else "sans", 13, INK if hit else INK2, "end")
        s.rect(x0, yy, X(v) - x0, bh, col if hit else D.tint(NEUTRAL, 0.25), rx=3)
        tx(s, X(v) + 8, yy + bh / 2 + 4.5, D.num(v, lang, 1), "sans7" if hit else "sans5", 14 if hit else 13,
           REDT if hit else INK2)
    # the published t, as a dashed line across every bar
    s.line(X(ref), top - 14, X(ref), bottom + 4, INK, 1.4, ' stroke-dasharray="5 3"')
    tx(s, X(ref) + 6, top - 10, (f"t publié en 2018 : {D.num(ref, lang, 1)}" if fr else
                               f"t published in 2018: {D.num(ref, lang, 1)}"), "sans7", 13, INK)
    y = bottom + 34
    return G.finish(f, y, "Données : sim/analysis/e1_curve.json, b1_trpo.json, b1_script.json "
                       "(docs/figures/data/e1_henderson_fr.csv)" if fr else
                    "Data: sim/analysis/e1_curve.json, b1_trpo.json, b1_script.json "
                    "(docs/figures/data/e1_henderson_en.csv)")


def grpo_truncation(lang):
    fr = lang == "fr"
    src = rows("grpo_truncation", lang)
    probs = list(dict.fromkeys(r[0] for r in src))
    kinds = list(dict.fromkeys(r[1] for r in src))
    cnt = {(r[0], r[1]): int(r[2]) for r in src}
    assert len(probs) == 4 and len(kinds) == 3 and all(sum(cnt[p, k] for k in kinds) == 8 for p in probs)
    cut = sum(cnt[p, kinds[2]] for p in probs)
    total = 8 * len(probs)
    cols = [GREEN, NEUTRAL, RED]
    T = {"title": (f"Avant tout entraînement, {cut} réponses sur {total} |sont coupées à 160 jetons" if fr else
                   f"Before any training, {cut} answers out of {total} |are cut at 160 tokens"),
         "sub": ("Qwen2.5 de 0,5 milliard de paramètres, lot du pas 10 du pilote : 8 réponses tirées par problème "
                 "de multiplication" if fr else
                 "Qwen2.5 with 0.5 billion parameters, the pilot's step-10 batch: 8 sampled answers per "
                 "multiplication problem"),
         "accent": RED,
         "desc": (f"Quatre problèmes de multiplication, huit réponses du modèle de départ pour chacun, une case par "
                  f"réponse : verte si complète et juste, grise si complète et fausse, rouge si coupée à 160 jetons "
                  f"avant d'avoir donné un résultat. {cut} cases sur {total} sont rouges." if fr else
                  f"Four multiplication problems, eight answers of the base model for each, one square per answer: "
                  f"green if complete and right, grey if complete and wrong, red if cut at 160 tokens before giving "
                  f"a result. {cut} squares out of {total} are red.")}
    f = fig(T)
    s, L, W = f.s, f.L, f.W
    y = f.legend(list(zip(kinds, cols)), f.top + 12) + 6
    cell, gap, lw = 40, 6, 74
    top = y
    for i, p in enumerate(probs):
        yy = top + i * (cell + gap)
        tx(s, L + lw - 14, yy + cell / 2 + 5, p, "sans7", 14, INK, "end")
        k = 0
        for kind, col in zip(kinds, cols):
            for _ in range(cnt[p, kind]):
                s.rect(L + lw + k * (cell + gap), yy, cell, cell, col, rx=4)
                k += 1
        nc = cnt[p, kinds[2]]
        tx(s, L + lw + 8 * (cell + gap) + 6, yy + cell / 2 + 5, f"{nc}/8", "mono", 13, REDT)
    bx = L + lw + 8 * (cell + gap) + 64
    base = lambda i: top + i * (cell + gap) + cell / 2 + 5    # the baseline of row i's "n/8"
    yb = base(2)
    tx(s, bx, base(1) + 6, f"{cut} sur {total}" if fr else f"{cut} of {total}", "serif", 38, REDT)
    for j, ln in enumerate(D.wrap("réponses coupées |avant leur résultat, |toutes comptées fausses" if fr else
                                  "answers cut |before their result, |all counted wrong", "sans5", 13, W - L - bx)):
        tx(s, bx, yb + j * 17, ln, "sans5", 13, INK2)
    y = top + len(probs) * (cell + gap) - gap
    return G.finish(f, y + 10, "Données : sim/llm/diag/replay_batch.json, "
                            "jetons comptés par le tokenizer de Qwen" if fr else
                    "Data: sim/llm/diag/replay_batch.json, "
                    "tokens counted by Qwen's tokenizer")


FIGS = {"e1-henderson": e1_henderson, "ecarts-classique": ecarts_classique, "ecarts-pineau": ecarts_pineau,
        "remesure-dumbbell": remesure_dumbbell, "remesure-ic": remesure_ic, "grpo-truncation": grpo_truncation}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGS.items():
        for lang in G.LANGS:
            (OUT / f"{name}-{lang}.svg").write_text(fn(lang), encoding="utf-8")
    print("docs figures redrawn: " + ", ".join(FIGS))


if __name__ == "__main__":
    main()
