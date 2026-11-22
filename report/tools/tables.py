"""Generated tables of the technical report (report/MANIFEST.md, "Generated tables").

Every number comes from a result file of the repository: study/*.json, sim/analysis/*.json, sim/llm/results/*.json
(and the run files they summarise), the protocols for the deviations, envs/*.txt for the versions, sim/results and
sim/logs for the compute. Nothing is typed by hand except labels, captions and the one-line summaries of the
deviations, whose numbers, dates and order are checked against the protocol files.

Writes gen/fr/<name>.tex and gen/en/<name>.tex, each a complete float (table or longtable) with its caption and the
label tab:<name>. Rounding follows docs/conclusions.md: shares and gaps in percentage points to the unit, IQM to the
unit, probabilities of improvement and ratios to two decimals, p-values as in the documents (two decimals above 0.01,
one significant digit below). Half-up rounding on the decimal representation of each float.

Run from report/: ../sim/env-an/bin/python tools/tables.py   (standard library + numpy only)
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
import statistics
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "report" / "gen"
sys.path.insert(0, str(REPO / "src"))
from pineau_rl.grid import list_readers, load_overrides, load_reads, value  # noqa: E402  (standard library only)

LANGS = ("fr", "en")


def J(rel):
    with open(REPO / rel) as f:
        return json.load(f)


# ----------------------------------------------------------------------------------------------------------------
# Number formatting
# ----------------------------------------------------------------------------------------------------------------
MINUS = "−"  # U+2212, as in the documents


def D(x):
    return x if isinstance(x, Decimal) else Decimal(repr(float(x)))


def q(x, nd=0):
    """Half-up rounding of the decimal representation of x to nd decimals."""
    return D(x).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def num(x, lang, nd=0, sign=False, group=True):
    """x rounded to nd decimals, French or English separators, U+2212 minus, optional explicit plus."""
    v = q(x, nd)
    if v == 0:
        v = abs(v)
    neg = v < 0
    s = f"{abs(v):.{nd}f}"
    ip, _, dp = s.partition(".")
    if group and len(ip) >= 4:
        sep = r"\," if lang == "fr" else ","
        parts = []
        while len(ip) > 3:
            parts.insert(0, ip[-3:])
            ip = ip[:-3]
        parts.insert(0, ip)
        ip = sep.join(parts)
    out = ip + (("," if lang == "fr" else ".") + dp if dp else "")
    if neg:
        out = MINUS + out
    elif sign and v != 0:
        out = "+" + out
    return out


def pc(x, lang, nd=0, sign=False):
    """A share (0 to 1) as a number of percent, without the % sign."""
    return num(D(x) * 100, lang, nd, sign)


def pct(x, lang, nd=0, sign=False):
    return pc(x, lang, nd, sign) + (r"~\%" if lang == "fr" else r"\%")


def pshare(x, lang):
    """Shares of draws: to the unit, one significant digit below 1 %, exact zero as 0 (B1)."""
    if x == 0:
        return "0"
    if x >= 0.01:
        return pc(x, lang)
    return pc(x, lang, -math.floor(math.log10(x * 100)))  # one significant digit below 1 %


def iv(a, b, lang):
    return f"[{a}\\,;\\,{b}]" if lang == "fr" else f"[{a},\\,{b}]"


def to(lang):
    return " à " if lang == "fr" else " to "


def pval(p, lang):
    """p-values as written in the documents."""
    if p is None:
        return ""
    if p == 0:  # a file rounded to six decimals (survey_extra.json): below 5 x 10^-7
        return rf"$<$\,10\textsuperscript{{{MINUS}6}}"
    if p >= 0.995:
        return "1"
    if p >= 0.01:
        return num(p, lang, 2)
    e = math.floor(math.log10(p))
    if p >= 1e-4:
        v = q(p, -e)
        return num(v, lang, -e if v < Decimal(10) ** (e + 1) else -e - 1)
    m = q(Decimal(repr(p)).scaleb(-e), 0)
    if m == 10:
        m, e = Decimal(1), e + 1
    return rf"{m}\,×\,10\textsuperscript{{{MINUS if e < 0 else ''}{abs(e)}}}"


def kn(k, n):
    return f"{k}/{n}"


def bold(s, on=True):
    if not on or s == "":
        return s
    return rf"\textbf{{\boldmath {s}}}" if "$" in s else rf"\textbf{{{s}}}"


def mc(*lines):
    return r"\makecell{" + r"\\{}".join(lines) + "}"


def esc(s):
    """Escapes the LaTeX special characters of a title."""
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    s = "".join(rep.get(c, c) for c in s)
    return s.replace("—", ", ").replace("–", "-")


def L(lang, fr, en):
    return fr if lang == "fr" else en


ALG = {"ppo_sb3": "PPO PyTorch", "ppo_sbx": "PPO JAX", "sac": "SAC", "crossq": "CrossQ"}
ALGS = ["ppo_sb3", "ppo_sbx", "sac", "crossq"]
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
T = lambda t: t.split("-")[0]  # noqa: E731


def write(name, lang, body):
    path = GEN / lang / f"{name}.tex"
    path.parent.mkdir(parents=True, exist_ok=True)
    head = "% Generated by report/tools/tables.py from the result files of the repository. Do not edit.\n"
    # underscores inside \file{...} and \texttt{...} are escaped once, wherever the caption wrote them raw
    def fix(m):
        return "\\" + m.group(1) + "{" + re.sub(r"(?<!\\)_", r"\\_", m.group(2)) + "}"
    body = re.sub(r"\\(file|texttt)\{([^{}]*)\}", fix, body)
    path.write_text(head + body.strip() + "\n")


XCOL = r">{\raggedright\arraybackslash}X"


def floattable(name, lang, caption, short, colspec, head, rows, size=r"\footnotesize", tabcolsep="4pt",
               env="auto", width=None, placement="tbp"):
    """A complete table float: caption on top, booktabs rules. head and rows are lists of LaTeX row strings
    (without the final \\\\); a row equal to "MID" becomes \\midrule.
    env="auto": when the column specification has a ragged-right p{} text column, the first one becomes an X column
    of a tabularx as wide as the text, so that the text column takes all the room the numbers leave (no label wrapped
    over three lines next to wide numeric columns); otherwise a plain tabular at its natural width."""
    if env == "auto":
        m = re.search(r">\{\\raggedright\\arraybackslash\}p\{[^{}]*\}", colspec)
        if m:
            colspec = colspec[:m.start()] + XCOL + colspec[m.end():]
            env, width = "tabularx", width or r"\linewidth"
        else:
            env = "tabular"
    out = [rf"\begin{{table}}[{placement}]", r"\centering", size, rf"\setlength{{\tabcolsep}}{{{tabcolsep}}}",
           rf"\caption[{short}]{{{caption}}}", rf"\label{{tab:{name}}}"]
    open_ = rf"\begin{{tabularx}}{{{width}}}{{{colspec}}}" if env == "tabularx" else rf"\begin{{tabular}}{{{colspec}}}"
    out += [open_, r"\toprule"]
    out += [h + r" \\" if h not in ("MID",) and not h.startswith(r"\cmidrule") else h for h in head]
    out.append(r"\midrule")
    for r in rows:
        if r == "MID":
            out.append(r"\midrule")
        elif r.startswith(r"\cmidrule") or r.startswith(r"\addlinespace"):
            out.append(r)
        else:
            out.append(r + r" \\")
    out += [r"\bottomrule", r"\end{tabularx}" if env == "tabularx" else r"\end{tabular}", r"\end{table}"]
    write(name, lang, "\n".join(out))


def longtable(name, lang, caption, short, colspec, head, rows, ncols, size=r"\footnotesize", tabcolsep="4pt"):
    cont = L(lang, "suite", "continued")
    nxt = L(lang, "suite page suivante", "continued on next page")
    out = [r"\begingroup", size, rf"\setlength{{\tabcolsep}}{{{tabcolsep}}}", r"\setlength{\LTcapwidth}{\textwidth}",
           rf"\begin{{longtable}}{{{colspec}}}",
           rf"\caption[{short}]{{{caption}}}\label{{tab:{name}}}\\",
           r"\toprule"] + [h + r" \\" for h in head] + [r"\midrule", r"\endfirsthead",
           rf"\multicolumn{{{ncols}}}{{l}}{{\emph{{{L(lang, 'Tableau', 'Table')} \thetable, {cont}}}}}\\",
           r"\toprule"] + [h + r" \\" for h in head] + [r"\midrule", r"\endhead",
           rf"\midrule\multicolumn{{{ncols}}}{{r}}{{\emph{{{nxt}}}}}\\", r"\endfoot", r"\bottomrule", r"\endlastfoot"]
    for r in rows:
        out.append(r if r.startswith(r"\midrule") or r.startswith(r"\addlinespace") else r + r" \\")
    out += [r"\end{longtable}", r"\endgroup"]
    write(name, lang, "\n".join(out))


# ----------------------------------------------------------------------------------------------------------------
# Survey: criteria labels
# ----------------------------------------------------------------------------------------------------------------
CRIT = {
    "Q1": ("L'article a des expériences", "The paper has experiments"),
    "Q2": ("Réseaux de neurones employés", "Neural networks used"),
    "Q3": ("Tous les hyperparamètres de la méthode", "All of the method's hyperparameters"),
    "Q4": ("Tous les hyperparamètres des références", "All of the baselines' hyperparameters"),
    "Q5": ("Code en lien", "Code linked"),
    "Q6": ("Choix des hyperparamètres décrit", "Hyperparameter selection described"),
    "Q7": ("Évaluation sur conditions tenues à part", "Evaluation on held-out conditions"),
    "Q8": ("Test statistique appliqué", "Statistical test applied"),
    "X2": ("Incertitude rapportée", "Uncertainty reported"),
    "X3": ("Seuls les meilleurs essais gardés", "Only the best runs kept"),
    "X4": ("Références réglées avec le même soin", "Baselines tuned with the same care"),
    "X5": ("Famille (llm, classic, theory)", "Family (llm, classic, theory)"),
    "X7": ("Calcul chiffré", "Compute quantified"),
    "Y1": ("Mesure de performance définie", "Performance measure defined"),
    "Y2": ("Barres d'erreur définies", "Error bars defined"),
    "Y3": ("Plusieurs tâches (au moins 2)", "Several tasks (at least 2)"),
    "Y4": ("Une tâche perdue montrée", "A task where the method loses shown"),
    "Y5": ("Origine du code des références", "Origin of the baselines' code"),
    "Y6": ("Exclusions dites", "Exclusions stated"),
    "Y7": ("Version des bancs d'essai", "Benchmark versions given"),
    "Y8": ("Test de généralisation", "Generalisation test"),
    "Y9": ("Sensibilité à un hyperparamètre", "Sensitivity to a hyperparameter"),
    "Y10": ("Versions des bibliothèques", "Library versions"),
    "Y11": ("Type d'incertitude nommé", "Type of uncertainty named"),
    "Y12": ("Outil statistique postérieur à 2018", "Post-2018 statistical tool"),
}


def clab(k, lang):
    return f"{k} & {CRIT[k][0 if lang == 'fr' else 1]}"


def share_cell(kn_, w, lang):
    k, n = kn_
    return f"{kn(k, n)} & {pc(k / n, lang)} {iv(pc(w[0], lang), pc(w[1], lang), lang)}"


def diff_cell(c, lang):
    return f"{pc(c['diff'], lang, sign=True)} {iv(pc(c['lo'], lang, sign=True), pc(c['hi'], lang, sign=True), lang)}"


def diff_cells(c, lang):
    """The gap and its interval as two cells (columns r@{\\,}l), so that the gaps align on their units."""
    return [pc(c["diff"], lang, sign=True), iv(pc(c["lo"], lang, sign=True), pc(c["hi"], lang, sign=True), lang)]


def survey_rows(rows, keys, lang):
    out = []
    for k in keys:
        r = rows[k]
        c = r["classic_vs_ours2018"]
        sig = c["p_holm"] < 0.05
        cells = [k, CRIT[k][0 if lang == "fr" else 1],
                 kn(*r["ours2018"]), pc(r['ours2018'][0] / r['ours2018'][1], lang),
                 iv(pc(r["wilson_ours2018"][0], lang), pc(r["wilson_ours2018"][1], lang), lang),
                 kn(*r["classic2026"]), pc(r['classic2026'][0] / r['classic2026'][1], lang),
                 iv(pc(r["wilson_classic2026"][0], lang), pc(r["wilson_classic2026"][1], lang), lang),
                 *diff_cells(c, lang), pval(c["p"], lang), pval(c["p_holm"], lang)]
        out.append(" & ".join(bold(x, sig) for x in cells))
    return out


def survey_head(lang):
    return [
        L(lang, r" & & \multicolumn{3}{c}{\makecell{Notre lecture\\{}de 2018}} & \multicolumn{3}{c}{\makecell{RL classique\\{}2026}} & \multicolumn{2}{c}{Écart} & & ",
          r" & & \multicolumn{3}{c}{\makecell{Our reading\\{}of 2018}} & \multicolumn{3}{c}{\makecell{Classical RL\\{}2026}} & \multicolumn{2}{c}{Gap} & & "),
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
        L(lang, r"Code & Critère & $k/n$ & \multicolumn{2}{c}{\% [Wilson]} & $k/n$ & \multicolumn{2}{c}{\% [Wilson]} & \multicolumn{2}{c}{[Newcombe]} & $p$ & $p$ Holm",
          r"Code & Criterion & $k/n$ & \multicolumn{2}{c}{\% [Wilson]} & $k/n$ & \multicolumn{2}{c}{\% [Wilson]} & \multicolumn{2}{c}{[Newcombe]} & $p$ & Holm $p$"),
    ]


def t_sondage():
    ext = J("study/extension_stats.json")
    rows = {r["k"]: r for r in ext["rows"]}
    s = ext["samples"]
    v1 = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
    v2 = [f"Y{i}" for i in range(1, 13)]
    pin = ["Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    pineau_pct = {r["k"]: r["pineau2018"] for r in J("study/results_final.json") if r.get("pineau2018") is not None}
    for lang in LANGS:
        colspec = r"@{}l>{\raggedright\arraybackslash}p{2.75cm}r r@{\hspace{0.28em}}l r r@{\hspace{0.28em}}l r@{\hspace{0.28em}}l rr@{}"
        # sondage-pineau: the main comparison on grid v1
        body = survey_rows(rows, v1, lang)
        cap = L(lang,
                rf"Grille de Pineau (critères Q2 à Q8) et critères X tirés de sa conférence ICLR 2018, lus avec la même grille et les mêmes lecteurs sur deux échantillons : notre lecture de {s['ours2018']} articles de 2018 (ICML, NeurIPS, ICLR) et {s['classic2026']} articles de RL classique de 2026 ({s['classic2026'] - len(s['a3'])} du premier tirage, {len(s['a3'])} de la file A3). C'est la comparaison principale, la seule qui fonde un verdict (écart 20 de \file{{study/PROTOCOL.md}}). "
                r"$k/n$ : articles qui remplissent le critère sur les articles où il s'applique (articles à expériences, Q1 différent de « non ») ; la part en pourcentage porte son intervalle de Wilson à 95~\%. "
                r"Écart : RL classique 2026 moins 2018, en points de pourcentage, avec l'intervalle de Newcombe à 95~\% ; $p$ : test exact de Fisher bilatéral ; $p$ Holm : correction de Holm sur les onze critères de la grille v1. "
                r"\textbf{En gras}, les critères dont l'écart passe la correction de Holm ($p$ Holm $<$ 0,05). Pour X3, une part plus basse est un progrès ; Q2 (réseaux de neurones) décrit la population étudiée, pas une pratique de reproductibilité. Les chiffres de Pineau elle-même sont au tableau~\ref{tab:sondage-pineau-contexte}. "
                r"Source : \file{study/extension_stats.json} (script \file{study/extension_stats.py}, écrit avant toute lecture des articles ajoutés).",
                rf"Pineau's grid (criteria Q2 to Q8) and the X criteria drawn from her ICLR 2018 talk, read with the same grid and the same readers on two samples: our reading of {s['ours2018']} papers from 2018 (ICML, NeurIPS, ICLR) and {s['classic2026']} classical RL papers from 2026 ({s['classic2026'] - len(s['a3'])} from the first draw, {len(s['a3'])} from the A3 queue). This is the main comparison, the only one a verdict rests on (deviation 20 of \file{{study/PROTOCOL.md}}). "
                r"$k/n$: papers that meet the criterion out of the papers where it applies (papers with experiments, Q1 not `no'); the percentage carries its 95\% Wilson interval. "
                r"Gap: classical RL 2026 minus 2018, in percentage points, with the 95\% Newcombe interval; $p$: two-sided Fisher exact test; Holm $p$: Holm correction over the eleven criteria of grid v1. "
                r"\textbf{In bold}, the criteria whose gap passes the Holm correction (Holm $p < 0.05$). For X3, a lower share is progress; Q2 (neural networks) describes the population studied, not a reproducibility practice. Pineau's own figures are in Table~\ref{tab:sondage-pineau-contexte}. "
                r"Source: \file{study/extension_stats.json} (script \file{study/extension_stats.py}, written before any reading of the added papers).")
        floattable("sondage-pineau", lang, cap,
                   L(lang, "Grille de Pineau : 2018 contre RL classique 2026", "Pineau's grid: 2018 against classical RL 2026"),
                   colspec, survey_head(lang), body, tabcolsep="3pt")
        # sondage-pineau-contexte: Pineau's own figures, as context
        # one group row per criterion (code and label across the table), then its two comparisons: the label keeps
        # one line instead of wrapping over three in a narrow column
        head = [L(lang, r"Code & Critère, puis comparaison & $k/n$ & \% & Pineau 2018 & \multicolumn{2}{c}{Écart [Newcombe]} & $p$ & $p$ Holm",
                  r"Code & Criterion, then comparison & $k/n$ & \% & Pineau 2018 & \multicolumn{2}{c}{Gap [Newcombe]} & $p$ & Holm $p$")]
        body = []
        for k in pin:
            r = rows[k]
            pk, pn = r["pineau2018"]
            body.append(rf"{k} & \multicolumn{{8}}{{@{{}}l}}{{{CRIT[k][0 if lang == 'fr' else 1]}}}")
            for j, (side, cmp_, fr, en) in enumerate((("ours2018", "ours2018_vs_pineau", "notre lecture de 2018", "our reading of 2018"),
                                                     ("all2026", "all2026_vs_pineau", "premier tirage 2026", "first 2026 draw"))):
                c = r[cmp_]
                sig = c["p_holm"] < .05
                cells = ["", r"\quad " + L(lang, fr, en), kn(*r[side]),
                         pc(r[side][0] / r[side][1], lang), f"{pc(pineau_pct[k], lang)} ({kn(pk, pn)})" if j == 0 else "",
                         *diff_cells(c, lang), pval(c["p"], lang), pval(c["p_holm"], lang)]
                body.append(" & ".join(cells[:5] + [bold(x, sig) for x in cells[5:]]))
            if k != pin[-1]:
                body.append(r"\addlinespace")
        cap = L(lang,
                rf"Les chiffres de Pineau (2018), comme contexte et jamais comme verdict : ses parts sur 50 articles de RL de 2018, pour les six critères qu'elle chiffre (pourcentage publié, \file{{study/results_final.json}} ; entre parenthèses le $k/n$ des tests, son pourcentage multiplié par 50 et arrondi, soit {pct(rows['Q5']['pineau2018'][0] / 50, lang)} pour Q5 et {pct(rows['Q8']['pineau2018'][0] / 50, lang)} pour Q8), comparées à notre lecture de {s['ours2018']} articles de 2018 avec notre grille, puis aux {rows['Q3']['all2026'][1]} articles expérimentaux du premier tirage de 2026, grands modèles de langage compris. "
                r"La première ligne de chaque critère mesure l'écart entre notre grille et la sienne sur la même année : notre lecture est plus sévère sur Q3 et plus large sur Q7, ce qui a conduit à ne fonder les verdicts que sur la comparaison avec la même grille (écart 20 de \file{study/PROTOCOL.md}, tableau~\ref{tab:sondage-pineau}). La seconde mêle le changement des pratiques, celui de la grille et celui de la population. "
                r"Écart en points avec l'intervalle de Newcombe à 95~\%, test exact de Fisher, correction de Holm sur Q3 à Q8 dans chaque famille de comparaisons. \textbf{En gras}, ce qui passe la correction de Holm. Le tirage de Pineau reste inconnu. Sources : \file{study/extension_stats.json}, \file{study/results_final.json}.",
                rf"Pineau's figures (2018), as context and never as a verdict: her shares on 50 RL papers from 2018, for the six criteria she quantifies (published percentage, \file{{study/results_final.json}}; in parentheses the $k/n$ used by the tests, her percentage times 50 and rounded, that is {pct(rows['Q5']['pineau2018'][0] / 50, lang)} for Q5 and {pct(rows['Q8']['pineau2018'][0] / 50, lang)} for Q8), set against our reading of {s['ours2018']} papers from 2018 with our grid, then against the {rows['Q3']['all2026'][1]} experimental papers of the first 2026 draw, large language models included. "
                r"The first row of each criterion measures the gap between our grid and hers on the same year: our reading is stricter on Q3 and broader on Q7, which led us to base verdicts only on the same-grid comparison (deviation 20 of \file{study/PROTOCOL.md}, Table~\ref{tab:sondage-pineau}). The second mixes the change in practice, the change of grid and the change of population. "
                r"Gap in points with the 95\% Newcombe interval, Fisher exact test, Holm correction over Q3 to Q8 within each family of comparisons. \textbf{In bold}, what passes the Holm correction. Pineau's draw remains unknown. Sources: \file{study/extension_stats.json}, \file{study/results_final.json}.")
        floattable("sondage-pineau-contexte", lang, cap,
                   L(lang, "Les chiffres de Pineau, comme contexte", "Pineau's figures, as context"),
                   r"@{}l>{\raggedright\arraybackslash}p{4cm}rrr r@{\hspace{0.28em}}l rr@{}", head, body, tabcolsep="4pt")
        body = survey_rows(rows, v2, lang)
        cap = L(lang,
                rf"Grille v2 (critères Y1 à Y12, écarts 11 et 14 de \file{{study/PROTOCOL.md}}, écrite le 9 novembre 2026 avant toute lecture v2), sur les mêmes échantillons que le tableau~\ref{{tab:sondage-pineau}} : {s['ours2018']} articles de 2018 lus par nous et {s['classic2026']} articles de RL classique de 2026. "
                r"Mêmes colonnes : $k/n$ sur les articles où le critère s'applique, part avec intervalle de Wilson à 95~\%, écart en points avec l'intervalle de Newcombe à 95~\%, test exact de Fisher, correction de Holm sur les douze critères de la grille v2 (famille distincte de la grille v1). "
                r"Y3 vaut « oui » quand la conclusion principale porte sur au moins deux tâches ; Y2 et Y11 ne s'appliquent qu'aux articles qui rapportent une incertitude, Y4 qu'aux articles à plusieurs tâches. "
                r"\textbf{En gras}, les critères dont l'écart passe la correction de Holm : seul Y9. Valeurs harmonisées (\file{study/overrides_v2.json}). Source : \file{study/extension_stats.json}.",
                rf"Grid v2 (criteria Y1 to Y12, deviations 11 and 14 of \file{{study/PROTOCOL.md}}, written on 9 November 2026 before any v2 reading), on the same samples as Table~\ref{{tab:sondage-pineau}}: {s['ours2018']} papers from 2018 read by us and {s['classic2026']} classical RL papers from 2026. "
                r"Same columns: $k/n$ over the papers where the criterion applies, share with its 95\% Wilson interval, gap in points with its 95\% Newcombe interval, Fisher exact test, Holm correction over the twelve criteria of grid v2 (a family separate from grid v1). "
                r"Y3 is `yes' when the main conclusion rests on at least two tasks; Y2 and Y11 apply only to papers that report an uncertainty, Y4 only to papers with several tasks. "
                r"\textbf{In bold}, the criteria whose gap passes the Holm correction: Y9 alone. Harmonised values (\file{study/overrides_v2.json}). Source: \file{study/extension_stats.json}.")
        floattable("sondage-extension", lang, cap,
                   L(lang, "Grille v2 : 2018 contre RL classique 2026", "Grid v2: 2018 against classical RL 2026"),
                   colspec, survey_head(lang), body, tabcolsep="3pt")


def t_sondage_lrl():
    au = J("study/audit_stats.json")
    ext = {r["k"]: r for r in J("study/extension_stats.json")["rows"]}
    s = J("study/extension_stats.json")["samples"]
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{4}{c}{Premier tirage 2026 (grille v1)} & \multicolumn{2}{c}{\makecell{RL classique\\{}2026 élargi}}",
                  r" & & \multicolumn{4}{c}{First 2026 draw (grid v1)} & \multicolumn{2}{c}{\makecell{Classical RL\\{}2026, enlarged}}"),
                r"\cmidrule(lr){3-6}\cmidrule(lr){7-8}",
                L(lang, r"Code & Critère & \makecell[r]{RL sur\\{}grands modèles} & \makecell[r]{RL\\{}classique} & Tous & \makecell[r]{\% tous\\{}[Wilson]} & $k/n$ & \%",
                  r"Code & Criterion & \makecell[r]{RL on\\{}large models} & \makecell[r]{Classical\\{}RL} & All & \makecell[r]{\% all\\{}[Wilson]} & $k/n$ & \%")]
        body = []
        for r in au["rows"]:
            k = r["k"]
            e = ext[k]["classic2026"]
            body.append(" & ".join([k, CRIT[k][0 if lang == "fr" else 1],
                                    f"{kn(*r['llm2026'])} ({pc(r['llm2026'][0] / r['llm2026'][1], lang)})",
                                    f"{kn(*r['classic2026'])} ({pc(r['classic2026'][0] / r['classic2026'][1], lang)})",
                                    kn(*r["all2026"]),
                                    f"{pc(r['all2026'][0] / r['all2026'][1], lang)} {iv(pc(r['wilson2026'][0], lang), pc(r['wilson2026'][1], lang), lang)}",
                                    kn(*e), pc(e[0] / e[1], lang)]))
        ap = s["a3_apart"]
        cap = L(lang,
                r"RL appliqué aux grands modèles de langage (famille \texttt{llm} du critère X5) contre RL classique, dans le premier tirage aléatoire de 50 articles de 2026 (ICLR 2026, ICML 2026, NeurIPS 2025) : 27 articles \texttt{llm}, 14 \texttt{classic}, 9 \texttt{theory} (non montrés, comptés dans « Tous »). "
                r"$k/n$ sur les articles à expériences où le critère s'applique, part en pourcentage entre parenthèses ; intervalle de Wilson à 95~\% pour la colonne « Tous », seul calculé par le script. "
                r"Seule la grille v1 a ce découpage par famille dans les résultats (\file{study/audit_stats.json}, harmonisation de \file{study/overrides.json}) : la grille v2 n'est pas ventilée par famille, et aucun test entre familles n'a été préregistré ; le tableau est descriptif. "
                rf"Les deux dernières colonnes rappellent l'échantillon classique élargi à 50 articles (tableau~\ref{{tab:sondage-pineau}}). Les {ap['llm']} articles \texttt{{llm}} et {ap['theory']} articles \texttt{{theory}} lus dans la file A3 restent à part : le tri sur le titre en avait déjà écarté beaucoup, ils ne forment pas un échantillon. "
                r"Sources : \file{study/audit_stats.json}, \file{study/extension_stats.json}.",
                r"RL applied to large language models (family \texttt{llm} of criterion X5) against classical RL, in the first random draw of 50 papers from 2026 (ICLR 2026, ICML 2026, NeurIPS 2025): 27 \texttt{llm} papers, 14 \texttt{classic}, 9 \texttt{theory} (not shown, counted in `All'). "
                r"$k/n$ over the papers with experiments where the criterion applies, share in percent in parentheses; 95\% Wilson interval for the `All' column, the only one the script computes. "
                r"Only grid v1 has this split by family in the results (\file{study/audit_stats.json}, harmonisation of \file{study/overrides.json}): grid v2 is not broken down by family, and no test between families was preregistered; the table is descriptive. "
                rf"The last two columns recall the classical sample enlarged to 50 papers (Table~\ref{{tab:sondage-pineau}}). The {ap['llm']} \texttt{{llm}} papers and {ap['theory']} \texttt{{theory}} papers read in the A3 queue stay apart: the title screen had already removed many of them, so they do not form a sample. "
                r"Sources: \file{study/audit_stats.json}, \file{study/extension_stats.json}.")
        floattable("sondage-lrl", lang, cap,
                   L(lang, "RL sur grands modèles contre RL classique, premier tirage 2026", "RL on large models against classical RL, first 2026 draw"),
                   r"@{}l>{\raggedright\arraybackslash}p{3.1cm}rrrrrr@{}", head, body, tabcolsep="3.5pt")


def t_trajectoire():
    tr = J("study/trajectory.json")
    years = ["2018", "2019", "2020", "2022", "2024", "2026"]
    sizes = tr["sizes"]
    for lang in LANGS:
        head = [L(lang, "Code & Critère & ", "Code & Criterion & ") + " & ".join(years) + L(lang, r" & $p$ tendance & $p$ Holm", r" & trend $p$ & Holm $p$"),
                r" & $n$ & " + " & ".join(str(sizes[y]) for y in years) + " & & "]
        body = []
        for k, r in tr["rows"].items():
            cells = []
            for y in years:
                b = r["by_year"][y]
                c = pc(b["k"] / b["n"], lang)
                if b["n"] != sizes[y]:
                    c += rf"\,{{\scriptsize ({b['n']})}}"
                cells.append(c)
            t = r.get("trend")
            sig = bool(t and t["p_holm"] < .05)
            row = [k, CRIT[k][0 if lang == "fr" else 1]] + cells + ([pval(t["p"], lang), pval(t["p_holm"], lang)] if t else ["", ""])
            body.append(" & ".join(bold(x, sig) for x in row))
        body.append("MID")
        body.append(L(lang, r"\multicolumn{10}{@{}l}{\emph{Écarts entre périodes (Newcombe, Fisher, Holm sur les cinq critères testés)}}",
                      r"\multicolumn{10}{@{}l}{\emph{Gaps between periods (Newcombe, Fisher, Holm over the five tested criteria)}}"))
        body.append(L(lang, r"Code & Critère & \multicolumn{3}{r}{\makecell[r]{2019-2020 contre 2018\\{}écart [IC]}} & $p$ Holm & \multicolumn{3}{r}{\makecell[r]{2022-2024 contre 2019-2020\\{}écart [IC]}} & $p$ Holm",
                      r"Code & Criterion & \multicolumn{3}{r}{\makecell[r]{2019-2020 against 2018\\{}gap [CI]}} & Holm $p$ & \multicolumn{3}{r}{\makecell[r]{2022-2024 against 2019-2020\\{}gap [CI]}} & Holm $p$"))
        body.append(r"\cmidrule(lr){1-10}")
        for k, r in tr["rows"].items():
            if "trend" not in r:
                continue
            im, la = r["immediate"], r["later"]
            body.append(" & ".join([k, CRIT[k][0 if lang == "fr" else 1],
                                    rf"\multicolumn{{3}}{{r}}{{{bold(diff_cell(im, lang), im['p_holm'] < .05)}}}", bold(pval(im["p_holm"], lang), im["p_holm"] < .05),
                                    rf"\multicolumn{{3}}{{r}}{{{bold(diff_cell(la, lang), la['p_holm'] < .05)}}}", bold(pval(la["p_holm"], lang), la["p_holm"] < .05)]))
        cap = L(lang,
                r"Trajectoire du RL classique de 2018 à 2026 (écart 25 de \file{study/PROTOCOL.md}, écrit avant tout tirage) : part des articles qui remplissent chaque critère, en pourcentage, par année. "
                r"2018 : notre lecture des articles à expériences ; 2019, 2020, 2022 et 2024 : les 20 premiers articles expérimentaux de RL classique par année, tirés au hasard dans ICML et NeurIPS (ICLR absente, son site refusant les téléchargements automatiques) ; 2026 : l'échantillon classique de la comparaison principale. "
                r"Le nombre entre parenthèses donne le dénominateur quand il diffère de l'effectif de la colonne (critère sans objet pour certains articles). Avec 20 articles, une part a une incertitude d'environ vingt points de part et d'autre. "
                r"Pour les cinq critères testés (Q5, Y9, X7, X2, Q8) : test de tendance de Cochran-Armitage sur les six années (scores égaux aux années), $p$ bilatéral et $p$ corrigé par Holm sur les cinq ; les six autres lignes sont descriptives. "
                r"Partie basse : écart immédiat (2019 et 2020 réunis contre 2018) et écart tardif (2022 et 2024 contre 2019 et 2020), en points, intervalle de Newcombe à 95~\%, Holm sur les cinq critères dans chaque famille. "
                r"\textbf{En gras}, ce qui passe la correction de Holm. Source : \file{study/trajectory.json} (\file{study/trajectory.py}).",
                r"Trajectory of classical RL from 2018 to 2026 (deviation 25 of \file{study/PROTOCOL.md}, written before any draw): share of papers that meet each criterion, in percent, by year. "
                r"2018: our reading of the papers with experiments; 2019, 2020, 2022 and 2024: the first 20 experimental classical RL papers per year, drawn at random from ICML and NeurIPS (ICLR is missing, its site refusing automated downloads); 2026: the classical sample of the main comparison. "
                r"The number in parentheses gives the denominator when it differs from the column size (criterion not applicable to some papers). With 20 papers, a share carries an uncertainty of about twenty points either way. "
                r"For the five tested criteria (Q5, Y9, X7, X2, Q8): Cochran-Armitage trend test over the six years (scores equal to the years), two-sided $p$ and Holm-corrected $p$ over the five; the six other rows are descriptive. "
                r"Bottom part: immediate gap (2019 and 2020 pooled against 2018) and later gap (2022 and 2024 against 2019 and 2020), in points, 95\% Newcombe interval, Holm over the five criteria within each family. "
                r"\textbf{In bold}, what passes the Holm correction. Source: \file{study/trajectory.json} (\file{study/trajectory.py}).")
        floattable("trajectoire", lang, cap, L(lang, "Trajectoire 2018 à 2026", "Trajectory 2018 to 2026"),
                   r"@{}l>{\raggedright\arraybackslash}p{3.3cm}rrrrrrrr@{}", head, body, tabcolsep="3.5pt")


def t_accord():
    ag = J("study/agree_v2.json")
    a1 = J("study/audit_stats.json")["agreement"]
    order = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X5", "X7"] + [f"Y{i}" for i in range(1, 13)]

    def cell_agree(d, lang):
        if d is None:
            return ["", ""]
        if "same" in d:
            same, n, k = d["same"], d["n"], d["kappa"]
        else:
            n, k = d["n"], d["kappa"]
            same = int(q(d["agree"] * n))
        return [kn(same, n), "" if k is None else num(k, lang, 2)]

    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{2}{c}{\makecell{G\\{}tirage 2026, v1}} & \multicolumn{2}{c}{\makecell{G2\\{}tirage 2026, v2}} & \multicolumn{2}{c}{\makecell{R2\\{}articles ajoutés}} & \multicolumn{2}{c}{\makecell{R3\\{}trajectoire}}",
                  r" & & \multicolumn{2}{c}{\makecell{G\\{}2026 draw, v1}} & \multicolumn{2}{c}{\makecell{G2\\{}2026 draw, v2}} & \multicolumn{2}{c}{\makecell{R2\\{}added papers}} & \multicolumn{2}{c}{\makecell{R3\\{}trajectory}}"),
                r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}",
                L(lang, r"Code & Critère & accord & $\kappa$ & accord & $\kappa$ & accord & $\kappa$ & accord & $\kappa$",
                  r"Code & Criterion & agree & $\kappa$ & agree & $\kappa$ & agree & $\kappa$ & agree & $\kappa$")]
        body = []
        for k in order:
            cells = cell_agree(a1.get(k), lang)
            for g in ("G2", "R2", "R3"):
                cells += cell_agree(ag[g]["criteria"].get(k), lang)
            lowest = [c for c in (a1.get(k), *(ag[g]["criteria"].get(k) for g in ("G2", "R2", "R3"))) if c]
            frag = any((c.get("agree", (c.get("same", 0) / c["n"]) if c.get("n") else 1) < 0.7) for c in lowest)
            row = [k, CRIT[k][0 if lang == "fr" else 1]] + cells
            body.append(" & ".join(bold(x, frag) for x in row))
        tot_same = sum(v["same"] for v in a1.values())
        tot_n = sum(v["n"] for v in a1.values())
        cap = L(lang,
                r"Accord entre deux lectures à l'aveugle d'agents IA, sur les lectures brutes, avant toute harmonisation. "
                rf"G : dix articles du premier tirage de 2026 relus avec la grille v1 ({tot_same} décisions identiques sur {tot_n}, \file{{study/audit_stats.json}}) ; "
                r"G2 : les mêmes dix articles relus avec la grille v2 ; R2 : dix articles tirés au hasard parmi les articles ajoutés (\texttt{random.Random(7)}, écart 12), relus avec les deux grilles ; R3 : dix articles de la trajectoire 2019 à 2024 (\texttt{random.Random(2030)}, écart 26). "
                r"Accord : décisions identiques sur les articles où les deux lecteurs ont répondu oui ou non (Y3 converti en oui à partir de deux tâches) ; $\kappa$ : kappa de Cohen, vide quand un des deux lecteurs ne varie pas (accord trivial). "
                r"Une case vide hors $\kappa$ : critère absent de cette double lecture. \textbf{En gras}, le seul critère sous 70~\% d'accord, signalé comme fragile par le script : Y1, mesure de performance, avant que ses règles soient précisées (écarts 17 et 19). "
                r"Tous les lecteurs sont des copies du même modèle (écart 28) : l'accord mesure la constance de ce modèle, pas celle de deux lecteurs indépendants. Sources : \file{study/agree_v2.json}, \file{study/audit_stats.json}.",
                r"Agreement between two blind readings by AI agents, on the raw readings, before any harmonisation. "
                rf"G: ten papers of the first 2026 draw reread with grid v1 ({tot_same} identical decisions out of {tot_n}, \file{{study/audit_stats.json}}); "
                r"G2: the same ten papers reread with grid v2; R2: ten papers drawn at random from the added papers (\texttt{random.Random(7)}, deviation 12), reread with both grids; R3: ten papers of the 2019 to 2024 trajectory (\texttt{random.Random(2030)}, deviation 26). "
                r"Agree: identical decisions over the papers where both readers answered yes or no (Y3 turned into yes from two tasks); $\kappa$: Cohen's kappa, blank when one of the two readers does not vary (trivial agreement). "
                r"An empty cell outside $\kappa$: criterion absent from that double reading. \textbf{In bold}, the only criterion under 70\% agreement, flagged as fragile by the script: Y1, performance measure, before its rules were made more precise (deviations 17 and 19). "
                r"All readers are copies of the same model (deviation 28): agreement measures that model's stability, not that of two independent readers. Sources: \file{study/agree_v2.json}, \file{study/audit_stats.json}.")
        floattable("accord", lang, cap, L(lang, "Accord entre lectures à l'aveugle", "Agreement between blind readings"),
                   r"@{}l>{\raggedright\arraybackslash}p{5.0cm}rrrrrrrr@{}", head, body, tabcolsep="3.5pt")


def t_robustesse():
    rob = J("study/robustness.json")
    main = {r["k"]: r for r in J("study/extension_stats.json")["rows"]}
    sans = {r["k"]: r for r in J("study/extension_stats_sans_opus5.json")["rows"]}
    turned = {r["k"]: r for r in J("study/extension_stats_falsify_turned.json")["rows"]}
    bound = {r["k"]: r for r in J("study/extension_stats_falsify_bound.json")["rows"]}
    fn = J("study/falsify_no.json")
    K = ["Q5", "Y9", "X7", "X2", "Q6", "Y12"]

    def dcell(c, lang):
        sig = c["lo"] > 0 or c["hi"] < 0
        return bold(mc(pc(c["diff"], lang, sign=True), iv(pc(c["lo"], lang, sign=True), pc(c["hi"], lang, sign=True), lang)), sig)

    def pcell(p, lang, sig=True):
        return bold(pval(p, lang), sig and p < .05)

    for lang in LANGS:
        rows = []

        def add(label, f):
            rows.append(label + " & " + " & ".join(f(k) for k in K))

        add(L(lang, "Comparaison principale : écart [IC]", "Main comparison: gap [CI]"), lambda k: dcell(main[k]["classic_vs_ours2018"], lang))
        add(L(lang, r"\quad $p$ Holm", r"\quad Holm $p$"), lambda k: pcell(main[k]["classic_vs_ours2018"]["p_holm"], lang))
        rows.append("MID")
        add(L(lang, "(a1) premier tirage seul (14)", "(a1) first draw only (14)"), lambda k: dcell(rob["a"][k]["a1_first_only"], lang))
        add(L(lang, "(a1) file A3 seule (36)", "(a1) A3 queue only (36)"), lambda k: dcell(rob["a"][k]["a1_a3_only"], lang))
        add(L(lang, r"(a1) premier tirage contre A3 : $p$", r"(a1) first draw against A3: $p$"), lambda k: pval(rob["a"][k]["a1_first_vs_a3"]["p"], lang))
        add(L(lang, r"(a2) arXiv contre site : $p$", r"(a2) arXiv against site: $p$"), lambda k: pval(rob["a"][k]["a2_arxiv_vs_site"]["p"], lang))
        add(L(lang, r"(a3) Mantel-Haenszel : rapport de cotes", r"(a3) Mantel-Haenszel: odds ratio"), lambda k: num(rob["a"][k]["a3_cmh"]["pooled_odds_ratio"], lang, 1))
        add(r"\quad $p$", lambda k: pcell(rob["a"][k]["a3_cmh"]["p"], lang))

        def a4range(k):
            ds = [c["diff"] for c in rob["a"][k]["a4"].values()]
            return pc(min(ds), lang, sign=True) + to(lang).replace(" à ", " à ").strip().join([" ", " "]) + pc(max(ds), lang, sign=True)
        add(L(lang, "(a4) un lecteur retiré : écarts", "(a4) one reader removed: gaps"), a4range)
        add(L(lang, "(a4) plus basse borne de l'IC", "(a4) lowest CI bound"),
            lambda k: bold(pc(min(c["lo"] for c in rob["a"][k]["a4"].values()), lang, sign=True), min(c["lo"] for c in rob["a"][k]["a4"].values()) > 0))
        add(L(lang, "Fragile selon (a)", "Fragile under (a)"),
            lambda k: (L(lang, "non", "no") if not rob["a"][k]["fragile"] else
                       L(lang, f"oui ({len(rob['a'][k]['fragile'])})", f"yes ({len(rob['a'][k]['fragile'])})")))
        rows.append("MID")
        add(L(lang, "Sans les 13 articles opus-5", "Without the 13 opus-5 papers"), lambda k: dcell(sans[k]["classic_vs_ours2018"], lang))
        add(L(lang, r"\quad $p$ Holm", r"\quad Holm $p$"), lambda k: pcell(sans[k]["classic_vs_ours2018"]["p_holm"], lang))
        add(L(lang, r"« Non » démentis retournés : $p$ Holm", r"Refuted `no' turned: Holm $p$"), lambda k: pcell(turned[k]["classic_vs_ours2018"]["p_holm"], lang))
        add(L(lang, r"\quad et douteux aussi : $p$ Holm", r"\quad doubtful ones too: Holm $p$"), lambda k: pcell(bound[k]["classic_vs_ours2018"]["p_holm"], lang))
        head = [L(lang, "Contrôle", "Check") + " & " + " & ".join(K)]
        b = rob["b"]
        nturn = sum(len(v["turned"]) for v in fn["counts"].values()) if "counts" in fn else None
        nunc = sum(len(v["uncertain"]) for v in fn["counts"].values()) if "counts" in fn else None
        nno = sum(v["no"] for v in fn["counts"].values()) if "counts" in fn else None
        cap = L(lang,
                r"Contrôles de robustesse du sondage, tous exploratoires (écarts 21, 27 et 29 de \file{study/PROTOCOL.md}) : ils disent si un verdict est fragile, sans en changer aucun. Colonnes : les quatre critères qui ont changé (Q5, Y9, X7, X2) et les deux dont l'intervalle évite zéro sans passer Holm (Q6, Y12). "
                r"Écarts en points (RL classique 2026 moins notre lecture de 2018), intervalle de Newcombe à 95~\%, test de Fisher, Holm sur la famille de la grille du critère comme dans la comparaison principale. "
                r"(a1) le RL classique de 2026 coupé selon sa provenance (premier tirage sans tri sur le titre, file A3 avec tri), puis $p$ de Fisher entre les deux provenances au sein de 2026 ; (a2) $p$ de Fisher entre articles de 2026 lus sur arXiv (45) et sur le site d'une conférence (5), une coupe trop déséquilibrée pour trancher (écart 21 c) ; "
                r"(a3) test de Cochran-Mantel-Haenszel stratifié par conférence (correction de Haldane) ; (a4) comparaison refaite sans chaque lecteur principal tour à tour : étendue des écarts et plus basse borne inférieure ; un critère est fragile quand l'écart change de signe ou que l'intervalle contient zéro avec au moins 35 articles de chaque côté. "
                rf"Partie basse : sans les treize articles lus en partie par \texttt{{claude-opus-5}} (écart 29) ; avec les {nturn} décisions « non » qu'un arbitre à l'aveugle a retournées après la recherche par mots-clés, puis avec aussi les {nunc} décisions jugées douteuses, sur {nno} décisions « non » examinées (écart 27). "
                r"\textbf{En gras}, les écarts dont l'intervalle exclut zéro et les $p$ sous 0,05 (sauf les $p$ d'homogénéité de (a1) et (a2), où un $p$ élevé est attendu). "
                rf"La thèse « écoutée là où cela coûtait peu » est rejetée par le test à l'aveugle (b) : corrélation de Spearman entre l'écart observé et le coût médian noté par trois évaluateurs {num(b['C']['rho'], lang, 2, sign=True)} ($p$ par permutation {pval(b['C']['p_two_sided'], lang)}), avec le risque {num(b['R']['rho'], lang, 2, sign=True)} ($p$ = {pval(b['R']['p_two_sided'], lang)}). "
                r"Sources : \file{study/robustness.json}, \file{study/extension_stats_sans_opus5.json}, \file{study/extension_stats_falsify_turned.json}, \file{study/extension_stats_falsify_bound.json}, \file{study/falsify_no.json}.",
                r"Robustness checks of the survey, all exploratory (deviations 21, 27 and 29 of \file{study/PROTOCOL.md}): they say whether a verdict is fragile, without changing any. Columns: the four criteria that changed (Q5, Y9, X7, X2) and the two whose interval avoids zero without passing Holm (Q6, Y12). "
                r"Gaps in points (classical RL 2026 minus our reading of 2018), 95\% Newcombe interval, Fisher test, Holm over the criterion's grid family as in the main comparison. "
                r"(a1) classical RL 2026 split by provenance (first draw with no title screen, A3 queue with the screen), then Fisher $p$ between the two provenances within 2026; (a2) Fisher $p$ between 2026 papers read on arXiv (45) and on a conference site (5), a cut too unbalanced to settle anything (deviation 21 c); "
                r"(a3) Cochran-Mantel-Haenszel test stratified by conference (Haldane correction); (a4) comparison redone without each primary reader in turn: range of the gaps and lowest lower bound; a criterion is fragile when the gap changes sign or the interval contains zero with at least 35 papers on each side. "
                rf"Bottom part: without the thirteen papers read partly by \texttt{{claude-opus-5}} (deviation 29); with the {nturn} `no' decisions a blind arbiter turned after the keyword search, then with the {nunc} decisions judged doubtful as well, out of {nno} `no' decisions examined (deviation 27). "
                r"\textbf{In bold}, gaps whose interval excludes zero and $p$ below 0.05 (except the homogeneity $p$ of (a1) and (a2), where a high $p$ is expected). "
                rf"The thesis `heeded where it cost little' is rejected by the blind test (b): Spearman correlation between the observed gap and the median cost scored by three raters {num(b['C']['rho'], lang, 2, sign=True)} (permutation $p$ {pval(b['C']['p_two_sided'], lang)}), with the risk {num(b['R']['rho'], lang, 2, sign=True)} ($p$ = {pval(b['R']['p_two_sided'], lang)}). "
                r"Sources: \file{study/robustness.json}, \file{study/extension_stats_sans_opus5.json}, \file{study/extension_stats_falsify_turned.json}, \file{study/extension_stats_falsify_bound.json}, \file{study/falsify_no.json}.")
        floattable("robustesse", lang, cap, L(lang, "Robustesse des verdicts du sondage", "Robustness of the survey verdicts"),
                   r"@{}>{\raggedright\arraybackslash}p{4.4cm}cccccc@{}", head, rows, tabcolsep="3pt")


# ----------------------------------------------------------------------------------------------------------------
# Experiments
# ----------------------------------------------------------------------------------------------------------------
def t_e1():
    e = J("sim/analysis/e1.json")
    for lang in LANGS:
        u = lambda x: num(x, lang)  # noqa: E731
        rows = [
            L(lang, r"\multicolumn{4}{@{}l}{\emph{Scores finaux des 30 essais (évaluation à 1 million de pas)}}",
              r"\multicolumn{4}{@{}l}{\emph{Final scores of the 30 runs (evaluation at 1 million steps)}}"),
            L(lang, f"Moyenne ; écart type & {u(e['mean'])} ; {u(e['sd'])} & Coef. de variation & {pct(e['cv'], lang)}",
              f"Mean; standard deviation & {u(e['mean'])}; {u(e['sd'])} & Coef. of variation & {pct(e['cv'], lang)}"),
            L(lang, f"Médiane & {u(e['median'])} & Minimum ; maximum & {u(e['min'])} ; {u(e['max'])}",
              f"Median & {u(e['median'])} & Minimum; maximum & {u(e['min'])}; {u(e['max'])}"),
            L(lang, f"Shapiro-Wilk, $p$ & {pval(e['shapiro_p'], lang)} & IQM & {L(lang, 'voir tableau', 'see Table')}~\\ref{{tab:e2}}",
              f"Shapiro-Wilk, $p$ & {pval(e['shapiro_p'], lang)} & IQM & {L(lang, 'voir tableau', 'see Table')}~\\ref{{tab:e2}}"),
            "MID",
            L(lang, r"Groupes comparés & \makecell[r]{Faux positifs\\{}($p<0{,}05$)} & \makecell[r]{Écart apparent\\{}médian} & \makecell[r]{Écart dépassé\\{}1 fois sur 20}",
              r"Groups compared & \makecell[r]{False positives\\{}($p<0.05$)} & \makecell[r]{Median\\{}apparent gap} & \makecell[r]{Gap exceeded\\{}1 time in 20}"),
            r"\cmidrule(lr){1-4}",
        ]
        for k, fr, en in (("random_3v3", "3 contre 3, au hasard", "3 against 3, at random"),
                          ("random_5v5", "5 contre 5, au hasard", "5 against 5, at random"),
                          ("random_10v10", "10 contre 10, au hasard", "10 against 10, at random")):
            r = e[k]
            rows.append(f"{L(lang, fr, en)} & {pct(r['false_positive'], lang, 1)} & {pct(r['median_gap'], lang)} & {pct(r['p95_gap'], lang)}")
        x = e["extreme_5v5_of_10"]
        rows.append(bold(L(lang, "5 meilleurs contre 5 pires, sur 10", "5 best against 5 worst, out of 10")) + f" & {bold(pct(x['false_positive'], lang, 1))} & {pct(x['median_gap'], lang)} & "
                    + L(lang, r"\makecell[r]{non calculé\\{}($p$ médian " + pval(x["median_p"], lang) + ")}", r"\makecell[r]{not computed\\{}(median $p$ " + pval(x["median_p"], lang) + ")}"))
        rows.append("MID")
        t3 = e["top3_of_10"]
        rows.append(L(lang, r"Garder les 3 meilleurs sur 10 & \makecell[r]{moyenne des 3\\{}" + u(t3['mean_top3']) + r"} & \makecell[r]{moyenne des 10\\{}" + u(t3['mean_all']) + r"} & \makecell[r]{gonflement\\{}" + pct(t3['inflation'], lang) + "}",
                      r"Keeping the best 3 of 10 & \makecell[r]{mean of the 3\\{}" + u(t3['mean_top3']) + r"} & \makecell[r]{mean of the 10\\{}" + u(t3['mean_all']) + r"} & \makecell[r]{inflation\\{}" + pct(t3['inflation'], lang) + "}"))
        cap = L(lang,
                r"Expérience E1 : trente entraînements de PPO PyTorch (Stable-Baselines3) sur HalfCheetah-v5, même code et mêmes hyperparamètres, graines aléatoires 0 à 29 ; score final : moyenne de 10 épisodes d'évaluation sur des graines jamais vues à l'entraînement. "
                r"Partie haute : statistiques des 30 scores ; le test de Shapiro-Wilk rejette la normalité (trois essais décollent au-delà de 3\,000). "
                r"Partie médiane : 10\,000 tirages par ligne (générateur \texttt{default\_rng(2018)}), test de Welch sur les scores finaux de deux groupes du même programme : toute différence déclarée est un faux positif. L'écart apparent divise la différence des deux moyennes par la plus petite des deux. "
                r"Les groupes tirés au hasard trompent le test moins souvent que le seuil de 5~\% ; \textbf{en gras}, les groupes triés (5 meilleurs contre 5 pires sur 10 essais tirés), qui le trompent près d'une fois sur trois. "
                r"Partie basse : moyennes sur 10\,000 tirages de 10 essais. Source : \file{sim/analysis/e1.json} (\file{sim/analysis/e1.py}).",
                r"Experiment E1: thirty training runs of PPO PyTorch (Stable-Baselines3) on HalfCheetah-v5, same code and same hyperparameters, random seeds 0 to 29; final score: mean of 10 evaluation episodes on seeds never seen in training. "
                r"Top part: statistics of the 30 scores; the Shapiro-Wilk test rejects normality (three runs take off beyond 3,000). "
                r"Middle part: 10,000 draws per row (generator \texttt{default\_rng(2018)}), Welch test on the final scores of two groups of the same program: every difference declared is a false positive. The apparent gap divides the difference between the two means by the smaller of the two. "
                r"Groups drawn at random fool the test less often than the 5\% threshold; \textbf{in bold}, sorted groups (5 best against 5 worst of 10 runs drawn), which fool it nearly one time in three. "
                r"Bottom part: means over 10,000 draws of 10 runs. Source: \file{sim/analysis/e1.json} (\file{sim/analysis/e1.py}).")
        floattable("e1", lang, cap, L(lang, "E1 : trente essais du même programme", "E1: thirty runs of the same program"),
                   r"@{}>{\raggedright\arraybackslash}p{5.2cm}rrr@{}", [L(lang, r"\multicolumn{4}{@{}l}{PPO PyTorch, HalfCheetah-v5, $n = " + str(e["n"]) + "$}",
                                                                         r"\multicolumn{4}{@{}l}{PPO PyTorch, HalfCheetah-v5, $n = " + str(e["n"]) + "$}")], rows)


def t_b1():
    sc, tr, cu = J("sim/analysis/b1_script.json"), J("sim/analysis/b1_trpo.json"), J("sim/analysis/e1_curve.json")
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{3}{c}{Groupes tirés au hasard} & \multicolumn{3}{c}{Groupes triés}",
                  r" & & \multicolumn{3}{c}{Groups drawn at random} & \multicolumn{3}{c}{Sorted groups}"),
                r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
                L(lang, r"Algorithme & Calcul du $t$ & \makecell{faux\\{}pos. (\%)} & \makecell{$|t|$,\\{}95\textsuperscript{e} c.} & \makecell{$|t| \geq 9{,}09$\\{}(\%)} & \makecell{faux\\{}pos. (\%)} & \makecell{$|t|$,\\{}95\textsuperscript{e} c.} & \makecell{$|t| \geq 9{,}09$\\{}(\%)}",
                  r"Algorithm & Computing $t$ & \makecell{false\\{}pos. (\%)} & \makecell{$|t|$,\\{}95th pct} & \makecell{$|t| \geq 9.09$\\{}(\%)} & \makecell{false\\{}pos. (\%)} & \makecell{$|t|$,\\{}95th pct} & \makecell{$|t| \geq 9.09$\\{}(\%)}")]
        rows = []
        names = [("mean_t", "$t$ moyen sur la courbe (graines)", "mean $t$ along the curve (seeds)"),
                 ("mean_p", "$p$ moyen sur la courbe (graines)", "mean $p$ along the curve (seeds)"),
                 ("pooled", "points empilés (100 par groupe)", "stacked points (100 per group)"),
                 ("n10", "script de Henderson, $n = 10$ épisodes", "Henderson's script, $n = 10$ episodes"),
                 ("n5", "script de Henderson, $n = 5$", "Henderson's script, $n = 5$")]
        for algo, an in (("ppo_sb3", "PPO"), ("trpo", "TRPO")):
            for i, (key, fr, en) in enumerate(names):
                if key in ("n10", "n5"):
                    rr, ss = sc[algo][key]["random_5v5"], sc[algo][key]["sorted_5v5"]
                    vals = [rr["false_positive"], rr["abs_t_p95"], rr["share_abs_t_ge_henderson"],
                            ss["false_positive"], ss["abs_t_p95"], ss["share_abs_t_ge_henderson"]]
                else:
                    rr, ss = tr[algo]["random_5v5"][key], tr[algo]["sorted_5v5"][key]
                    vals = [rr["false_positive"], rr["abs_t_p95"], rr["share_abs_t_ge_henderson"],
                            ss["false_positive"], ss["abs_t_p95"], ss["share_abs_t_ge_henderson"]]
                hit = vals[2] > 0
                cells = [an if i == 0 else "", L(lang, fr, en), pshare(vals[0], lang), num(vals[1], lang, 1), pshare(vals[2], lang),
                         pshare(vals[3], lang), num(vals[4], lang, 1), pshare(vals[5], lang)]
                rows.append(" & ".join([cells[0]] + [bold(c, hit) for c in cells[1:]]))
            if algo == "ppo_sb3":
                rows.append("MID")
        cap = L(lang,
                r"Expérience B1 : la statistique de la figure de 2018 ($t = -9{,}09$, Henderson et al., TRPO sur HalfCheetah, deux groupes de cinq essais non triés) recalculée sur nos trente essais de PPO (ceux de E1) et nos trente essais de TRPO (sb3-contrib, valeurs par défaut), HalfCheetah-v5, un million de pas, 20 points d'évaluation. "
                r"Chaque ligne : 10\,000 tirages de 10 essais parmi 30, coupés en deux groupes de 5, au hasard ou triés par score final (générateur \texttt{default\_rng(2018)}). "
                r"Trois lectures de « t moyen sur toute la courbe » (écart 4 de \file{sim/SIM_PROTOCOL.md}, écrit avant tout entraînement TRPO) : $t$ de Welch à chaque point puis moyenne, convertie en $p$ avec les degrés de liberté moyens ; moyenne des $p$ ; les 5 essais $\times$ 20 points de chaque groupe empilés comme 100 observations indépendantes. "
                r"Puis le script \texttt{from\_same\_dist.py} publié par Henderson en 2017 (écart 6) : test de Welch à chaque itération sur l'écart type entre épisodes d'un même point, moyenne des $t$ et des $p$ ; la variation entre graines n'y entre pas. "
                r"Colonnes : part des tirages déclarés différents ($p < 0{,}05$, faux positifs puisque les deux groupes exécutent le même code), 95\textsuperscript{e} centile de $|t|$, part des tirages où $|t|$ atteint 9,09. Parts en pourcentage arrondies à l'unité, à un chiffre significatif sous 1~\%. "
                rf"\textbf{{En gras}}, les seules lignes où $|t|$ atteint 9,09 : le script de 2017 appliqué à TRPO, dont l'écart type entre épisodes ne vaut que {pct(sc['trpo']['eval_std_over_between_seed_sd'], lang)} de l'écart type entre graines (PPO : {pct(sc['ppo_sb3']['eval_std_over_between_seed_sd'], lang)}). "
                rf"Coefficient de variation des scores finaux : TRPO {pct(tr['trpo']['cv'], lang)}, PPO {pct(tr['ppo_sb3']['cv'], lang)}. Sources : \file{{sim/analysis/b1\_trpo.json}}, \file{{sim/analysis/b1\_script.json}} (la ligne PPO $t$ moyen reprend le calcul de \file{{sim/analysis/e1\_curve.json}}).",
                r"Experiment B1: the statistic of the 2018 figure ($t = -9.09$, Henderson et al., TRPO on HalfCheetah, two unsorted groups of five runs) recomputed on our thirty PPO runs (those of E1) and our thirty TRPO runs (sb3-contrib, default values), HalfCheetah-v5, one million steps, 20 evaluation points. "
                r"Each row: 10,000 draws of 10 runs out of 30, split into two groups of 5, at random or sorted by final score (generator \texttt{default\_rng(2018)}). "
                r"Three readings of `the average t-test across the entire training curve' (deviation 4 of \file{sim/SIM_PROTOCOL.md}, written before any TRPO run): Welch $t$ at each point then averaged, turned into a $p$ with the mean degrees of freedom; mean of the $p$ values; the 5 runs $\times$ 20 points of each group stacked as 100 independent observations. "
                r"Then the script \texttt{from\_same\_dist.py} Henderson published in 2017 (deviation 6): a Welch test at each iteration on the standard deviation between the episodes of one point, mean of the $t$ and $p$ values; the spread between seeds never enters it. "
                r"Columns: share of draws declared different ($p < 0.05$, false positives since both groups run the same code), 95th percentile of $|t|$, share of draws where $|t|$ reaches 9.09. Shares in percent rounded to the unit, to one significant digit below 1\%. "
                rf"\textbf{{In bold}}, the only rows where $|t|$ reaches 9.09: the 2017 script applied to TRPO, whose standard deviation between episodes is only {pct(sc['trpo']['eval_std_over_between_seed_sd'], lang)} of the standard deviation between seeds (PPO: {pct(sc['ppo_sb3']['eval_std_over_between_seed_sd'], lang)}). "
                rf"Coefficient of variation of the final scores: TRPO {pct(tr['trpo']['cv'], lang)}, PPO {pct(tr['ppo_sb3']['cv'], lang)}. Sources: \file{{sim/analysis/b1\_trpo.json}}, \file{{sim/analysis/b1\_script.json}} (the PPO mean-$t$ row repeats the computation of \file{{sim/analysis/e1\_curve.json}}).")
        floattable("b1", lang, cap, L(lang, "B1 : atteindre le t de 9,09", "B1: reaching the t of 9.09"),
                   r"@{}l>{\raggedright\arraybackslash}p{4.4cm}rrrrrr@{}", head, rows, tabcolsep="3.5pt")
    assert abs(cu["random_5v5"]["abs_mean_t_p95"] - tr["ppo_sb3"]["random_5v5"]["mean_t"]["abs_t_p95"]) < 1e-3


def iqm_cell(v, ci, lang, nd=0, small=False):
    c = iv(num(ci[0], lang, nd), num(ci[1], lang, nd), lang)
    return f"{num(v, lang, nd)} " + (rf"{{\scriptsize {c}}}" if small else c)


def t_e2():
    F = {k: J(f"sim/analysis/e2{k}.json") for k in ("", "_s20", "_equal", "_equal_s20")}
    B = {k: J(f"sim/analysis/e2_bonferroni{k}.json") for k in ("", "_s20")}
    for lang in LANGS:
        head = [L(lang, r"Tâche, programme & 10 graines & 20 graines & \makecell[r]{Budget égal\\10 graines} & \makecell[r]{Budget égal\\20 graines}",
                  r"Task, program & 10 seeds & 20 seeds & \makecell[r]{Equal budget\\10 seeds} & \makecell[r]{Equal budget\\20 seeds}")]
        rows = []
        for t in TASKS:
            rows.append(rf"\multicolumn{{5}}{{@{{}}l}}{{\emph{{{T(t)}}}}}")
            for i, a in enumerate(ALGS):
                cells = [r"\quad " + ALG[a]]
                for k, d in F.items():
                    r = d["tasks"][t]
                    nd = 0
                    ci = r["iqm_ci"][a]  # interval under its IQM: four interval columns side by side overflow the text width
                    cell = rf"\makecell[r]{{{num(r['iqm'][a], lang, nd)}\\{{\scriptsize {iv(num(ci[0], lang, nd), num(ci[1], lang, nd), lang)}}}}}"
                    cells.append(bold(cell, d["leaders"][t] == a))
                rows.append(" & ".join(cells))
            rows.append("MID")
        rows.append(L(lang, r"Changements de chef tranchés & ", r"Settled changes of leader & ")
                    + f"{len(F['']['settled_changes'])} ({len(B['']['settled_changes'])}) & {len(F['_s20']['settled_changes'])} ({len(B['_s20']['settled_changes'])}) & "
                    f"{len(F['_equal']['settled_changes'])} & {len(F['_equal_s20']['settled_changes'])}")
        cap = L(lang,
                r"Expérience E2 : moyenne interquartile (IQM) du score final de chaque programme sur chaque tâche MuJoCo (Gymnasium 1.1.1), avec son intervalle de confiance à 95~\% par bootstrap stratifié (rliable, 2\,000 rééchantillons, \texttt{np.random.seed(2026)}). "
                r"Score final : moyenne de 10 épisodes d'évaluation sur des graines jamais vues à l'entraînement, à 1 million de pas pour PPO et 200\,000 pour SAC et CrossQ (écart 1). "
                r"10 graines (0 à 9) : résultat principal préregistré ; 20 graines (0 à 19) et budget égal (PPO lu à 200\,000 pas sur sa courbe d'évaluation) : consolidation de l'écart 12, calculée le 21 novembre 2026 (écart 20). Les colonnes SAC et CrossQ sont identiques à budget égal et à budget propre. "
                r"\textbf{En gras}, le chef de chaque tâche (plus forte IQM, sans test). Dernière ligne : changements de chef tranchés, quand le chef d'une tâche est battu par un autre programme sur une autre tâche avec un intervalle de probabilité d'amélioration qui exclut 0,5 ; entre parenthèses, avec les 24 intervalles rendus simultanés par Bonferroni (écart 18, tableau~\ref{tab:e2-bonferroni}). "
                r"Sources : \file{sim/analysis/e2.json}, \file{e2\_s20.json}, \file{e2\_equal.json}, \file{e2\_equal\_s20.json}, \file{e2\_bonferroni.json}, \file{e2\_bonferroni\_s20.json}.",
                r"Experiment E2: interquartile mean (IQM) of the final score of each program on each MuJoCo task (Gymnasium 1.1.1), with its 95\% stratified bootstrap confidence interval (rliable, 2,000 resamples, \texttt{np.random.seed(2026)}). "
                r"Final score: mean of 10 evaluation episodes on seeds never seen in training, at 1 million steps for PPO and 200,000 for SAC and CrossQ (deviation 1). "
                r"10 seeds (0 to 9): the main, preregistered result; 20 seeds (0 to 19) and equal budget (PPO read at 200,000 steps on its evaluation curve): the consolidation of deviation 12, computed on 21 November 2026 (deviation 20). The SAC and CrossQ columns are the same at equal and at own budget. "
                r"\textbf{In bold}, the leader of each task (highest IQM, no test). Last row: settled changes of leader, when the leader of one task is beaten by another program on another task with a probability-of-improvement interval that excludes 0.5; in parentheses, with the 24 intervals made simultaneous by Bonferroni (deviation 18, Table~\ref{tab:e2-bonferroni}). "
                r"Sources: \file{sim/analysis/e2.json}, \file{e2\_s20.json}, \file{e2\_equal.json}, \file{e2\_equal\_s20.json}, \file{e2\_bonferroni.json}, \file{e2\_bonferroni\_s20.json}.")
        floattable("e2", lang, cap, L(lang, "E2 : IQM par programme et par tâche", "E2: IQM per program and task"),
                   r"@{}lrrrr@{}", head, rows, tabcolsep="4pt")


def pair_label(key, sep=" > "):
    a, b = re.split(r">| vs ", key)
    return f"{ALG[a.strip()]}{sep}{ALG[b.strip()]}"


def t_e2_bonferroni():
    E = {k: J(f"sim/analysis/e2{k}.json") for k in ("", "_s20")}
    B = {k: J(f"sim/analysis/e2_bonferroni{k}.json") for k in ("", "_s20")}
    for lang in LANGS:
        head = [L(lang, r" & \multicolumn{3}{c}{10 graines} & \multicolumn{3}{c}{20 graines}", r" & \multicolumn{3}{c}{10 seeds} & \multicolumn{3}{c}{20 seeds}"),
                r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
                L(lang, r"Tâche, paire $A > B$ & $P(A > B)$ & IC 95~\% & IC Bonferroni & $P$ & IC 95~\% & IC Bonferroni",
                  r"Task, pair $A > B$ & $P(A > B)$ & 95\% CI & Bonferroni CI & $P$ & 95\% CI & Bonferroni CI")]
        rows = []
        flips = 0
        for t in TASKS:
            for i, key in enumerate(E[""]["tasks"][t]["pairs"]):
                a, b = key.split(">")
                if i == 0:
                    rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\emph{{{T(t)}}}}}")
                cells = [r"\quad " + pair_label(key)]
                for s in ("", "_s20"):
                    pe, pb = E[s]["tasks"][t]["pairs"], B[s]["tasks"][t]["pairs"]
                    k2, dag = key, ""
                    if key not in pe:
                        k2, dag = f"{b}>{a}", r"$^\dagger$"
                        flips += 1
                    e, bb = pe[k2], pb[k2]
                    cells += [num(e["p"], lang, 2) + dag,
                              bold(iv(num(e["ci"][0], lang, 2), num(e["ci"][1], lang, 2), lang), e["settled"]),
                              bold(iv(num(bb["ci"][0], lang, 2), num(bb["ci"][1], lang, 2), lang), bb["settled"])]
                rows.append(" & ".join(cells))
            if t != TASKS[-1]:
                rows.append("MID")
        cap = L(lang,
                r"Expérience E2, comparaisons deux à deux : probabilité d'amélioration $P(A > B)$, la probabilité qu'un essai de $A$ batte un essai de $B$ sur la tâche, avec son intervalle par bootstrap stratifié (rliable, 2\,000 rééchantillons). "
                r"IC 95~\% : intervalle de chaque comparaison seule, celui de la règle préregistrée (écart 7) ; IC Bonferroni : les 24 intervalles (6 paires sur 4 tâches) rendus simultanés au niveau de 95~\%, chacun au niveau $1 - 0{,}05/24$, soit 99,79~\% (écart 18 de \file{sim/SIM_PROTOCOL.md}, écrit après les résultats de E2 et avant ce calcul). "
                r"Les paires sont orientées dans l'ordre du classement à 10 graines ; $^\dagger$ : à 20 graines, le classement s'inverse et le fichier donne $P(B > A)$, reporté tel quel pour la paire inversée. "
                r"\textbf{En gras}, les intervalles qui excluent 0,5 : comparaison tranchée. Sources : \file{sim/analysis/e2.json}, \file{e2\_s20.json}, \file{e2\_bonferroni.json}, \file{e2\_bonferroni\_s20.json}.",
                r"Experiment E2, pairwise comparisons: probability of improvement $P(A > B)$, the probability that a run of $A$ beats a run of $B$ on the task, with its stratified bootstrap interval (rliable, 2,000 resamples). "
                r"95\% CI: the interval of each comparison alone, the one of the preregistered rule (deviation 7); Bonferroni CI: the 24 intervals (6 pairs on 4 tasks) made simultaneous at the 95\% level, each at level $1 - 0.05/24$, that is 99.79\% (deviation 18 of \file{sim/SIM_PROTOCOL.md}, written after the E2 results and before this computation). "
                r"Pairs are oriented in the order of the ten-seed ranking; $^\dagger$: at twenty seeds the ranking flips and the file gives $P(B > A)$, reported as it is for the flipped pair. "
                r"\textbf{In bold}, intervals that exclude 0.5: settled comparison. Sources: \file{sim/analysis/e2.json}, \file{e2\_s20.json}, \file{e2\_bonferroni.json}, \file{e2\_bonferroni\_s20.json}.")
        floattable("e2-bonferroni", lang, cap, L(lang, "E2 : probabilités d'amélioration et Bonferroni", "E2: probabilities of improvement and Bonferroni"),
                   r"@{}lrrrrrr@{}", head, rows, tabcolsep="3.5pt")


def t_e3():
    D3 = {"": J("sim/analysis/e3.json"), "_s20": J("sim/analysis/e3_s20.json")}
    for lang in LANGS:
        head = [L(lang, r"Tâche & \makecell[r]{PPO PyTorch\\{}IQM [IC 95~\%]} & \makecell[r]{PPO JAX\\{}IQM [IC 95~\%]} & \makecell[r]{JAX/PyTorch\\{}$-$ 1} & \makecell[r]{$P(\text{JAX} > \text{PyTorch})$\\{}[IC 95~\%]} & Vainqueur",
                  r"Task & \makecell[r]{PPO PyTorch\\{}IQM [95\% CI]} & \makecell[r]{PPO JAX\\{}IQM [95\% CI]} & \makecell[r]{JAX/PyTorch\\{}$-$ 1} & \makecell[r]{$P(\text{JAX} > \text{PyTorch})$\\{}[95\% CI]} & Winner")]
        rows = []
        for s, fr, en in (("", "10 graines (0 à 9), résultat principal", "10 seeds (0 to 9), main result"),
                          ("_s20", "20 graines (0 à 19), écart 12", "20 seeds (0 to 19), deviation 12")):
            rows.append(rf"\multicolumn{{6}}{{@{{}}l}}{{\emph{{{L(lang, fr, en)}}}}}")
            for t in TASKS:
                r = D3[s][t]
                w = r["winner"]
                win = {None: L(lang, "aucun", "none"), "sb3": "PyTorch", "sbx": "JAX"}[w]
                cells = [T(t), iqm_cell(r["iqm"]["sb3"], r["iqm_ci"]["sb3"], lang), iqm_cell(r["iqm"]["sbx"], r["iqm_ci"]["sbx"], lang),
                         pct(r["iqm_ratio_sbx_over_sb3"] - 1, lang, sign=True),
                         f"{num(r['p_improve'], lang, 2)} {iv(num(r['p_improve_ci'][0], lang, 2), num(r['p_improve_ci'][1], lang, 2), lang)}", win]
                rows.append(" & ".join(bold(c, w is not None) for c in cells))
            if s == "":
                rows.append("MID")
        cap = L(lang,
                r"Expérience E3 : deux implémentations du même algorithme, PPO de Stable-Baselines3 (PyTorch) et PPO de SBX (JAX), mêmes graines, score final à 1 million de pas. "
                r"IQM du score final avec intervalle à 95~\% par bootstrap stratifié (rliable, 2\,000 rééchantillons) ; écart relatif entre les deux IQM ; probabilité qu'un essai JAX batte un essai PyTorch avec son intervalle bootstrap. "
                r"Règle préregistrée : un vainqueur n'est déclaré que si les deux intervalles d'IQM sont disjoints, ou si l'intervalle de la probabilité d'amélioration exclut 0,5. "
                r"\textbf{En gras}, les tâches où un vainqueur est déclaré : aucune à 10 graines, deux à 20 graines, où les écarts ressemblent à ceux de 10 graines avec des intervalles plus étroits. "
                r"Sources : \file{sim/analysis/e3.json}, \file{sim/analysis/e3\_s20.json}.",
                r"Experiment E3: two implementations of the same algorithm, Stable-Baselines3's PPO (PyTorch) and SBX's PPO (JAX), same seeds, final score at 1 million steps. "
                r"IQM of the final score with its 95\% stratified bootstrap interval (rliable, 2,000 resamples); relative gap between the two IQMs; probability that a JAX run beats a PyTorch run, with its bootstrap interval. "
                r"Preregistered rule: a winner is declared only when the two IQM intervals do not overlap, or when the interval of the probability of improvement excludes 0.5. "
                r"\textbf{In bold}, the tasks where a winner is declared: none at ten seeds, two at twenty, where the gaps resemble those at ten seeds with narrower intervals. "
                r"Sources: \file{sim/analysis/e3.json}, \file{sim/analysis/e3\_s20.json}.")
        floattable("e3", lang, cap, L(lang, "E3 : PPO PyTorch contre PPO JAX", "E3: PPO PyTorch against PPO JAX"),
                   r"@{}lrrrrl@{}", head, rows, tabcolsep="3.5pt")


def t_e4():
    E, R = J("sim/analysis/e4.json"), J("sim/analysis/e4_r10.json")
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{5}{c}{Graines 0 à 9 (résultat principal)} & \multicolumn{3}{c}{Graines 10 à 19 (réplication)}",
                  r" & & \multicolumn{5}{c}{Seeds 0 to 9 (main result)} & \multicolumn{3}{c}{Seeds 10 to 19 (replication)}"),
                r"\cmidrule(lr){3-7}\cmidrule(lr){8-10}",
                L(lang, r"Tâche & Programme & moy. 10 & é.-t. 10 & moy. 3 & é.-t. 3 & gonfl. & moy. 10 & moy. 3 & gonfl.",
                  r"Task & Program & mean 10 & sd 10 & mean 3 & sd 3 & infl. & mean 10 & mean 3 & infl.")]
        rows = []
        for t in TASKS:
            for i, a in enumerate(ALGS):
                c, r = E["cells"][f"{a}/{t}"], R["cells"][f"{a}/{t}"]
                rows.append(" & ".join([T(t) if i == 0 else "", ALG[a], num(c["mean10"], lang), num(c["sd10"], lang), num(c["mean3"], lang),
                                        num(c["sd3"], lang), pct(c["inflation"], lang, sign=True), num(r["mean10"], lang), num(r["mean3"], lang),
                                        pct(r["inflation"], lang, sign=True)]))
            rows.append("MID")

        def revs(d):
            return L(lang, " ; ", "; ").join(f"{T(c['task'])}{L(lang, ' : ', ': ')}{pair_label(c['pair'], ' / ')}" for c in d["comparisons"] if c["reversed"])
        rows.append(L(lang, r"\multicolumn{2}{@{}l}{Gonflement médian (étendue)} & \multicolumn{5}{r}{", r"\multicolumn{2}{@{}l}{Median inflation (range)} & \multicolumn{5}{r}{")
                    + f"{pct(E['inflation_median'], lang, sign=True)} ({pct(E['inflation_range'][0], lang, sign=True)}{to(lang)}{pct(E['inflation_range'][1], lang, sign=True)})" + "} & "
                    + r"\multicolumn{3}{r}{" + f"{pct(R['inflation_median'], lang, sign=True)} ({pct(R['inflation_range'][0], lang, sign=True)}{to(lang)}{pct(R['inflation_range'][1], lang, sign=True)})" + "}")
        rows.append(L(lang, r"\multicolumn{2}{@{}l}{Comparaisons inversées} & \multicolumn{5}{r}{", r"\multicolumn{2}{@{}l}{Comparisons reversed} & \multicolumn{5}{r}{")
                    + f"{E['n_reversed']} / {E['n_comparisons']}" + r"} & \multicolumn{3}{r}{" + f"{R['n_reversed']} / {R['n_comparisons']}" + "}")
        cap = L(lang,
                rf"Expérience E4 : garder les 3 meilleurs essais sur 10. Pour chaque programme et chaque tâche, moyenne et écart type des scores finaux des 10 essais, puis des 3 meilleurs, et gonflement de la moyenne (moyenne des 3 meilleurs divisée par celle des 10, moins 1). "
                rf"Une comparaison (paire de programmes sur une tâche, 24 en tout) s'inverse quand le signe de l'écart entre moyennes change une fois que chaque programme ne garde que ses 3 meilleurs essais (écart 7 de \file{{sim/SIM_PROTOCOL.md}}). "
                rf"À droite, la même analyse refaite sur les graines 10 à 19 (écart 12). Comparaisons inversées, graines 0 à 9 : {revs(E)} ; graines 10 à 19 : {revs(R)}. "
                rf"L'écart type des 3 meilleurs tombe en médiane à {pct(E['sd_shrink_median'], lang)} de celui des 10. Sources : \file{{sim/analysis/e4.json}}, \file{{sim/analysis/e4\_r10.json}}.",
                rf"Experiment E4: keeping the best 3 runs out of 10. For each program and task, mean and standard deviation of the final scores of the 10 runs, then of the best 3, and the inflation of the mean (mean of the best 3 divided by that of the 10, minus 1). "
                rf"A comparison (a pair of programs on one task, 24 in all) reverses when the sign of the gap between means changes once each program keeps only its best 3 runs (deviation 7 of \file{{sim/SIM_PROTOCOL.md}}). "
                rf"On the right, the same analysis redone on seeds 10 to 19 (deviation 12). Reversed comparisons, seeds 0 to 9: {revs(E)}; seeds 10 to 19: {revs(R)}. "
                rf"The standard deviation of the best 3 falls at the median to {pct(E['sd_shrink_median'], lang)} of that of the 10. Sources: \file{{sim/analysis/e4.json}}, \file{{sim/analysis/e4\_r10.json}}.")
        floattable("e4", lang, cap, L(lang, "E4 : garder les trois meilleurs essais sur dix", "E4: keeping the best three runs out of ten"),
                   r"@{}llrrrrrrrr@{}", head, rows, tabcolsep="3.2pt")


def t_e5():
    E, S = J("sim/analysis/e5.json"), J("sim/analysis/e5_s20.json")
    sidx = {(c["task"], c["pair"]): c for c in S["comparisons"]}
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{5}{c}{10 graines (résultat principal)} & \multicolumn{5}{c}{20 graines (écarts 12 et 20)}",
                  r" & & \multicolumn{5}{c}{10 seeds (main result)} & \multicolumn{5}{c}{20 seeds (deviations 12 and 20)}"),
                r"\cmidrule(lr){3-7}\cmidrule(lr){8-12}",
                L(lang, r"Tâche & Paire & écart & $n=3$ & 5 & 10 & 20 & écart & $n=3$ & 5 & 10 & 20",
                  r"Task & Pair & gap & $n=3$ & 5 & 10 & 20 & gap & $n=3$ & 5 & 10 & 20")]
        rows = []
        last = None
        for c in E["comparisons"]:
            s = sidx[(c["task"], c["pair"])]
            if last and c["task"] != last:
                rows.append("MID")
            cells = [T(c["task"]) if c["task"] != last else "", pair_label(c["pair"], " / ")]
            for d in (c, s):
                close = d["rel_gap"] < .2
                cells += [bold(pc(d["rel_gap"], lang), close)] + [bold(pc(d["recovered"][str(n)], lang), close) for n in (3, 5, 10, 20)]
            rows.append(" & ".join(cells))
            last = c["task"]
        rows.append("MID")
        for lab, key, ncl in ((L(lang, "Médiane, 24 comparaisons", "Median, 24 comparisons"), "median_all", None),
                              (L(lang, "Médiane, comparaisons serrées", "Median, close comparisons"), "median_close", True)):
            cells = [rf"\multicolumn{{2}}{{@{{}}l}}{{{lab}}}"]
            for d in (E, S):
                cells += [str(d["n_close"]) if ncl else ""] + [pc(d[key][str(n)], lang) for n in (3, 5, 10, 20)]
            rows.append(" & ".join(cells))
        cap = L(lang,
                r"Expérience E5 : combien de graines retrouvent le bon classement ? Pour chaque comparaison de E2, 10\,000 tirages avec remise de $n$ essais par programme parmi ses essais (la distribution observée tient lieu de programme), puis la part des tirages dont les moyennes donnent le bon ordre, en pourcentage. "
                r"Bon ordre : celui des moyennes de tous les essais choisis (10, ou 20 avec l'écart 20) ; à 10 graines, PPO PyTorch sur HalfCheetah tire dans les 30 essais de E1, comme préregistré. "
                r"Écart : différence relative des deux moyennes, divisée par la plus grande en valeur absolue. \textbf{En gras}, les comparaisons serrées (écart sous 20~\%) ; la dernière ligne donne leur nombre et la médiane de leurs parts. "
                r"Sources : \file{sim/analysis/e5.json}, \file{sim/analysis/e5\_s20.json}.",
                r"Experiment E5: how many seeds recover the right ranking? For each E2 comparison, 10,000 draws with replacement of $n$ runs per program from its runs (the observed distribution stands in for the program), then the share of draws whose means give the right order, in percent. "
                r"Right order: that of the means of all the chosen runs (10, or 20 with deviation 20); at ten seeds, PPO PyTorch on HalfCheetah draws from the 30 runs of E1, as preregistered. "
                r"Gap: relative difference of the two means, divided by the larger in absolute value. \textbf{In bold}, close comparisons (gap under 20\%); the last row gives their number and the median of their shares. "
                r"Sources: \file{sim/analysis/e5.json}, \file{sim/analysis/e5\_s20.json}.")
        floattable("e5", lang, cap, L(lang, "E5 : graines nécessaires pour retrouver le classement", "E5: seeds needed to recover the ranking"),
                   r"@{}llrrrrrrrrrr@{}", head, rows, tabcolsep="3pt")


def t_e6():
    e6, dg, of = J("sim/analysis/e6.json"), J("sim/analysis/e6_diag.json"), J("sim/analysis/e6_official.json")
    G = dg["groups"]
    for lang in LANGS:
        lab = {"default v5": L(lang, "Valeurs par défaut, Hopper-v5", "Default values, Hopper-v5"),
               "zoo v5 (bug)": L(lang, "Zoo, première passe (gamma 0,99), v5", "Zoo, first pass (gamma 0.99), v5"),
               "zoofix v5": L(lang, "Zoo corrigé (gamma 0,999), v5", "Zoo corrected (gamma 0.999), v5"),
               "default v4": L(lang, "Valeurs par défaut, Hopper-v4", "Default values, Hopper-v4"),
               "zoofix v4": L(lang, "Zoo corrigé, v4", "Zoo corrected, v4"),
               "official v4": L(lang, "Script officiel du Zoo, v4", "Official Zoo script, v4")}
        head = [L(lang, r"Groupe (PPO PyTorch, 10 graines) & moyenne & écart type & IQM [IC 95~\%] & source",
                  r"Group (PPO PyTorch, 10 seeds) & mean & sd & IQM [95\% CI] & source")]
        rows = []
        for k in ("default v5", "zoo v5 (bug)", "zoofix v5", "default v4", "zoofix v4"):
            g = G[k]
            rows.append(" & ".join([lab[k], num(g["mean"], lang), num(g["sd"], lang), iqm_cell(g["iqm"], g["iqm_ci"], lang), r"\file{e6\_diag}"]))
        o = of["groups"]["official v4"]
        omean = statistics.fmean(o["runs"])
        osd = statistics.stdev(o["runs"])
        rows.append(" & ".join([lab["official v4"], num(omean, lang), num(osd, lang), iqm_cell(o["iqm"], o["iqm_ci"], lang), r"\file{e6\_official}"]))
        for k in ("zoofix v4", "default v4"):
            g = of["groups"][k]
            rows.append(" & ".join([r"\quad " + lab[k], "", "", iqm_cell(g["iqm"], g["iqm_ci"], lang), r"\file{e6\_official}"]))
        for k, kk in (("default", "default v5"), ("zoo", "zoo v5 (bug)")):
            rows.append(" & ".join([r"\quad " + lab[kk] + L(lang, ", préregistré", ", preregistered"), "", "", iqm_cell(e6["iqm"][k], e6["ci"][k], lang), r"\file{e6}"]))
        rows.append("MID")
        rows.append(L(lang, r"Comparaison $A$ contre $B$ & $P(A > B)$ [IC] & $p$ Welch & $p$ Holm & $p$ Mann-Whitney",
                      r"Comparison $A$ against $B$ & $P(A > B)$ [CI] & Welch $p$ & Holm $p$ & Mann-Whitney $p$"))
        rows.append(r"\cmidrule(lr){1-5}")
        for c in dg["comparisons"] + of["comparisons"]:
            sig = c["welch_p_holm"] < .05
            cells = [f"{lab[c['a']]} / {lab[c['b']]}".replace(", Hopper-v", " v").replace("Hopper-", ""),
                     f"{num(c['p_improve'], lang, 2)} {iv(num(c['p_improve_ci'][0], lang, 2), num(c['p_improve_ci'][1], lang, 2), lang)}",
                     pval(c["welch_p"], lang), pval(c["welch_p_holm"], lang), pval(c.get("mannwhitney_p"), lang)]
            rows.append(" & ".join(bold(x, sig) for x in cells))
        cap = L(lang,
                r"Expérience E6, la méthode de référence : PPO PyTorch sur Hopper, un million de pas, 10 graines par groupe, valeurs par défaut de Stable-Baselines3 contre les réglages publiés par RL Baselines3 Zoo. "
                r"La première passe (préregistrée, \file{sim/analysis/e6.json}, bootstrap de 2\,000 rééchantillons) normalisait les observations avec un gamma de 0,99 au lieu de 0,999 ; le diagnostic décidé après ce résultat (écart 2) relance la recette corrigée sur Hopper v5 et v4, la version pour laquelle le Zoo a été réglé (\file{e6\_diag.json}, 5\,000 rééchantillons, Holm sur trois comparaisons) ; "
                r"puis dix agents entraînés avec le script officiel du Zoo, évalués avec notre protocole (écart 5, écrit avant tout entraînement officiel ; \file{e6\_official.json}, 2\,000 rééchantillons, Holm sur deux comparaisons). Les bornes d'un même groupe varient ainsi d'un fichier à l'autre au niveau Monte-Carlo. "
                r"IQM avec intervalle à 95~\% par bootstrap (rliable) ; $P(A > B)$ : probabilité qu'un essai de $A$ batte un essai de $B$, intervalle bootstrap ; test de Welch, correction de Holm, test de Mann-Whitney quand le script le calcule. "
                r"\textbf{En gras}, les comparaisons qui passent la correction de Holm : la recette publiée fait moins bien que les valeurs par défaut, avec notre code comme avec le script officiel. "
                r"Moyenne et écart type des agents officiels calculés ici à partir de leurs dix scores (\file{e6\_official.json}).",
                r"Experiment E6, the baseline: PPO PyTorch on Hopper, one million steps, 10 seeds per group, Stable-Baselines3 default values against the settings published by RL Baselines3 Zoo. "
                r"The first pass (preregistered, \file{sim/analysis/e6.json}, bootstrap with 2,000 resamples) normalised observations with a gamma of 0.99 instead of 0.999; the diagnosis decided after that result (deviation 2) reruns the corrected recipe on Hopper v5 and v4, the version the Zoo was tuned for (\file{e6\_diag.json}, 5,000 resamples, Holm over three comparisons); "
                r"then ten agents trained with the Zoo's official script, evaluated with our protocol (deviation 5, written before any official training; \file{e6\_official.json}, 2,000 resamples, Holm over two comparisons). The bounds of one group therefore vary from one file to the next at the Monte Carlo level. "
                r"IQM with its 95\% bootstrap interval (rliable); $P(A > B)$: probability that a run of $A$ beats a run of $B$, bootstrap interval; Welch test, Holm correction, Mann-Whitney test where the script computes it. "
                r"\textbf{In bold}, comparisons that pass the Holm correction: the published recipe does worse than the default values, with our code as with the official script. "
                r"Mean and standard deviation of the official agents computed here from their ten scores (\file{e6\_official.json}).")
        floattable("e6", lang, cap, L(lang, "E6 : valeurs par défaut contre recette publiée", "E6: default values against the published recipe"),
                   r"@{}>{\raggedright\arraybackslash}p{5.4cm}rrrl@{}", head, rows, tabcolsep="3.5pt")


VERD = {"loss": ("perte", "loss"), "gain": ("gain", "gain"), "no detectable change": ("ns", "n.s.")}


def t_e7():
    E = {"": J("sim/analysis/e7.json"), "_s20": J("sim/analysis/e7_s20.json")}
    R = {"": J("sim/analysis/e7_rank.json"), "_s20": J("sim/analysis/e7_rank_s20.json")}
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{3}{c}{10 graines (résultat principal)} & \multicolumn{3}{c}{20 graines (écart 12)}",
                  r" & & \multicolumn{3}{c}{10 seeds (main result)} & \multicolumn{3}{c}{20 seeds (deviation 12)}"),
                r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
                L(lang, r"Tâche & Programme & ratio [IC 95~\%] & verdict & rang & ratio [IC 95~\%] & verdict & rang",
                  r"Task & Program & ratio [95\% CI] & verdict & rank & ratio [95\% CI] & verdict & rank")]
        rows = []
        cnt = {}
        for t in TASKS:
            for i, a in enumerate(ALGS):
                cells = [T(t) if i == 0 else "", ALG[a]]
                for s in ("", "_s20"):
                    r = E[s][f"{a}/{t}"]
                    rk = R[s][t]
                    v = r["verdict"]
                    cnt.setdefault(s, {}).setdefault(v, 0)
                    cnt[s][v] += 1
                    sig = v != "no detectable change"
                    cells += [bold(f"{num(r['iqm'], lang, 2)} {iv(num(r['ci'][0], lang, 2), num(r['ci'][1], lang, 2), lang)}", sig),
                              bold(VERD[v][0 if lang == "fr" else 1], sig),
                              f"{rk['training'].index(a) + 1}" + r"$\to$" + f"{rk['modified'].index(a) + 1}"]
                rows.append(" & ".join(cells))
            rows.append("MID")
        rows.append(L(lang, r"\multicolumn{2}{@{}l}{Pertes, gains (sur 16)} & ", r"\multicolumn{2}{@{}l}{Losses, gains (out of 16)} & ")
                    + rf"\multicolumn{{3}}{{c}}{{{cnt[''].get('loss', 0)}, {cnt[''].get('gain', 0)}}} & \multicolumn{{3}}{{c}}{{{cnt['_s20'].get('loss', 0)}, {cnt['_s20'].get('gain', 0)}}}")
        lead = [T(t) for t in TASKS if R[""][t]["leader_changes"]]
        lead20 = [T(t) for t in TASKS if R["_s20"][t]["leader_changes"]]
        cap = L(lang,
                rf"Expérience E7, physique modifiée : chaque politique finale évaluée sur les mêmes graines d'évaluation tenues à part, dans la physique d'entraînement puis avec les masses multipliées par 1,2 et le frottement par 0,8. "
                rf"Ratio : score en physique modifiée divisé par le score en physique d'entraînement, par essai ; IQM des ratios sur les graines avec intervalle à 95~\% par bootstrap stratifié (rliable, 2\,000 rééchantillons). "
                rf"Verdict préregistré : perte quand l'intervalle reste sous 1, gain quand il reste au-dessus, ns (aucun changement détectable) sinon ; \textbf{{en gras}}, les pertes et les gains. "
                rf"Rang : place du programme sur la tâche par IQM du score, dans la physique d'entraînement puis dans la physique modifiée (complément descriptif de l'écart 11, décidé après les résultats, sans test). "
                rf"Le chef change sur {', '.join(lead) if lead else L(lang, 'aucune tâche', 'no task')} à 10 graines, sur {', '.join(lead20) if lead20 else L(lang, 'aucune tâche', 'no task')} à 20 graines. "
                r"Sources : \file{sim/analysis/e7.json}, \file{e7\_s20.json}, \file{e7\_rank.json}, \file{e7\_rank\_s20.json}.",
                rf"Experiment E7, modified physics: each final policy evaluated on the same held-out evaluation seeds, in the training physics and then with masses multiplied by 1.2 and friction by 0.8. "
                rf"Ratio: score in the modified physics divided by the score in the training physics, per run; IQM of the ratios over the seeds with its 95\% stratified bootstrap interval (rliable, 2,000 resamples). "
                rf"Preregistered verdict: loss when the interval stays below 1, gain when it stays above, n.s. (no detectable change) otherwise; \textbf{{in bold}}, losses and gains. "
                rf"Rank: the program's place on the task by IQM of the score, in the training physics and then in the modified physics (descriptive complement of deviation 11, decided after the results, no test). "
                rf"The leader changes on {', '.join(lead) if lead else 'no task'} at ten seeds, on {', '.join(lead20) if lead20 else 'no task'} at twenty seeds. "
                r"Sources: \file{sim/analysis/e7.json}, \file{e7\_s20.json}, \file{e7\_rank.json}, \file{e7\_rank\_s20.json}.")
        floattable("e7", lang, cap, L(lang, "E7 : part du score gardée en physique modifiée", "E7: share of score kept under modified physics"),
                   r"@{}llrcrrcr@{}", head, rows, tabcolsep="3pt")


def t_dose():
    Dd = {"": J("sim/analysis/dose.json"), "_s20": J("sim/analysis/dose_s20.json")}
    strengths = [("mass", k) for k in ("0.7", "0.8", "0.9", "1.1", "1.2", "1.3")] + [("friction", k) for k in ("0.6", "0.7", "0.8", "0.9", "1.1", "1.2")]
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{3}{c}{10 graines} & \multicolumn{3}{c}{20 graines}", r" & & \multicolumn{3}{c}{10 seeds} & \multicolumn{3}{c}{20 seeds}"),
                r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
                L(lang, r"Grandeur & Facteur & pertes & gains & chef sur Hopper & pertes & gains & chef sur Hopper",
                  r"Quantity & Factor & losses & gains & leader on Hopper & losses & gains & leader on Hopper")]
        rows = []
        notfirst = {}
        for qty, k in strengths:
            cells = [L(lang, {"mass": "masses", "friction": "frottement"}[qty], {"mass": "masses", "friction": "friction"}[qty]) if (qty, k) in (("mass", "0.7"), ("friction", "0.6")) else "",
                     num(float(k), lang, 1)]
            for s in ("", "_s20"):
                d = Dd[s]
                vs = [d["ratio"][f"{a}/{t}/{qty}/{k}"]["verdict"] for a in ALGS for t in TASKS]
                lead = d["ranking"][f"Hopper-v5/{qty}/{k}"]["ranking"][0]
                notfirst.setdefault(s, 0)
                notfirst[s] += lead != "ppo_sbx"
                cells += [str(vs.count("loss")), str(vs.count("gain")), ALG[lead]]
            rows.append(" & ".join(cells))
            if (qty, k) == ("mass", "1.3"):
                rows.append("MID")
        cap = L(lang,
                rf"Expérience E7 à plusieurs intensités (écart 12 (ii) de \file{{sim/SIM_PROTOCOL.md}}, règle écrite avant tout calcul ; écart 14 (a) sur la date du script) : chaque politique finale réévaluée sur les mêmes dix graines d'évaluation en changeant une seule grandeur à la fois. "
                rf"Pour chaque intensité, nombre de paires programme et tâche, sur 16, qui perdent (IQM du ratio au score en physique d'origine, intervalle à 95~\% par bootstrap stratifié rliable de 2\,000 rééchantillons, entièrement sous 1) ou qui gagnent (intervalle au-dessus de 1). "
                rf"Chef sur Hopper : programme de plus forte IQM du score, sans test ; dans la physique d'origine, PPO JAX y mène. Il perd la première place à {notfirst['']} intensités sur 12 à 10 graines, {notfirst['_s20']} sur 12 à 20 graines. "
                rf"Contrôle : à 1,0, les réévaluations retrouvent le score final de \file{{run.py}} (plus grand écart relatif {num(Dd['']['control_max_rel_gap'], lang, 1)} à 10 graines, {num(Dd['_s20']['control_max_rel_gap'], lang, 1)} à 20). "
                r"Sources : \file{sim/analysis/dose.json}, \file{sim/analysis/dose\_s20.json}.",
                rf"Experiment E7 at several strengths (deviation 12 (ii) of \file{{sim/SIM_PROTOCOL.md}}, rule written before any computation; deviation 14 (a) on the date of the script): each final policy re-evaluated on the same ten evaluation seeds, changing a single quantity at a time. "
                rf"For each strength, number of program and task pairs, out of 16, that lose (IQM of the ratio to the score in the original physics, 95\% stratified rliable bootstrap interval with 2,000 resamples, entirely below 1) or that gain (interval above 1). "
                rf"Leader on Hopper: the program with the highest IQM of the score, no test; in the original physics, PPO JAX leads there. It loses first place at {notfirst['']} strengths out of 12 at ten seeds, {notfirst['_s20']} out of 12 at twenty seeds. "
                rf"Control: at 1.0, the re-evaluations recover the final score of \file{{run.py}} (largest relative gap {num(Dd['']['control_max_rel_gap'], lang, 1)} at ten seeds, {num(Dd['_s20']['control_max_rel_gap'], lang, 1)} at twenty). "
                r"Sources: \file{sim/analysis/dose.json}, \file{sim/analysis/dose\_s20.json}.")
        floattable("dose", lang, cap, L(lang, "E7 à plusieurs intensités", "E7 at several strengths"),
                   r"@{}lrrrlrrl@{}", head, rows, tabcolsep="4pt")


def t_b3():
    F = {k: J(f"sim/analysis/b3{k}.json") for k in ("", "_s20", "_equal", "_equal_s20")}
    M = {"final": ("final", "final"), "best": ("meilleur", "best"), "mean": ("moyenne", "mean")}
    for lang in LANGS:
        head = [L(lang, r"Tâche & chef, final & chef, meilleur & chef, moyenne & paires inversées (mesures)",
                  r"Task & leader, final & leader, best & leader, mean & reversed pairs (measures)")]
        rows = []
        conf = {"": ("10 graines, budgets propres (résultat principal)", "10 seeds, own budgets (main result)"),
                "_s20": ("20 graines, budgets propres", "20 seeds, own budgets"),
                "_equal": ("10 graines, budget égal (200\\,000 pas)", "10 seeds, equal budget (200,000 steps)"),
                "_equal_s20": ("20 graines, budget égal", "20 seeds, equal budget")}
        for s, d in F.items():
            if lang == "fr":
                tail = f" : {d['n_reversals']} inversions, {d['n_settled']} tranchée{'s' if d['n_settled'] > 1 else ''}"
            else:
                tail = f": {d['n_reversals']} reversals, {d['n_settled']} settled"
            rows.append(rf"\multicolumn{{5}}{{@{{}}l}}{{\emph{{{L(lang, *conf[s])}}}{tail}}}")
            for t in TASKS:
                r = d["tasks"][t]
                o = r["order"]
                lch = len({o[m][0] for m in M}) > 1
                byp = {}
                for x in r["reversals"]:
                    byp.setdefault(x["pair"], []).append((x["measures"], x["settled"]))
                rev = "; ".join(pair_label(p, ", ") + " (" + ", ".join(bold("/".join(M[m][0 if lang == "fr" else 1] for m in ms.split("/")), st) for ms, st in v) + ")"
                                for p, v in byp.items())
                rows.append(" & ".join([T(t)] + [bold(ALG[o[m][0]], lch) for m in M] + [rev]))
            if s != "_equal_s20":
                rows.append("MID")
        cap = L(lang,
                r"Expérience B3, la mesure change-t-elle le classement ? (écart 8 de \file{sim/SIM_PROTOCOL.md}, sans entraînement). Sur les courbes d'évaluation enregistrées (un point tous les 50\,000 pas), trois mesures par essai : le score final, le meilleur score atteint le long de la courbe, la moyenne de la courbe. "
                r"Par tâche, IQM de chaque mesure et classement des programmes ; chef : plus forte IQM. Une paire s'inverse quand son ordre par IQM change d'une mesure à l'autre ; l'inversion est tranchée quand, sous chacune des deux mesures, l'intervalle de la probabilité d'amélioration (bootstrap stratifié rliable, 2\,000 rééchantillons) exclut 0,5 dans des sens opposés. "
                r"\textbf{En gras}, les chefs qui changent avec la mesure et les inversions tranchées. La moyenne de la courbe couvre un million de pas pour PPO et 200\,000 pour SAC et CrossQ, sauf à budget égal (écart 12 (iii)). "
                r"Sources : \file{sim/analysis/b3.json}, \file{b3\_s20.json}, \file{b3\_equal.json}, \file{b3\_equal\_s20.json}.",
                r"Experiment B3, does the measure change the ranking? (deviation 8 of \file{sim/SIM_PROTOCOL.md}, no training). On the recorded evaluation curves (one point every 50,000 steps), three measures per run: the final score, the best score reached along the curve, the mean of the curve. "
                r"Per task, IQM of each measure and ranking of the programs; leader: highest IQM. A pair reverses when its IQM order changes from one measure to another; the reversal is settled when, under each of the two measures, the interval of the probability of improvement (stratified rliable bootstrap, 2,000 resamples) excludes 0.5 in opposite directions. "
                r"\textbf{In bold}, leaders that change with the measure and settled reversals. The mean of the curve covers a million steps for PPO and 200,000 for SAC and CrossQ, except at equal budget (deviation 12 (iii)). "
                r"Sources: \file{sim/analysis/b3.json}, \file{b3\_s20.json}, \file{b3\_equal.json}, \file{b3\_equal\_s20.json}.")
        floattable("b3", lang, cap, L(lang, "B3 : la mesure et le classement", "B3: the measure and the ranking"),
                   r"@{}llll>{\raggedright\arraybackslash}p{6.2cm}@{}", head, rows, tabcolsep="3.5pt")


def t_grpo():
    summ = J("sim/llm/results/summary_5.json")
    gains = J("sim/llm/results/gains_5.json")
    extra = J("sim/llm/results/extra_5.json")
    MOD = {"qwen05": "Qwen2.5 0,5B", "llama1": "Llama 3.2 1B"}
    MODEN = {"qwen05": "Qwen2.5 0.5B", "llama1": "Llama 3.2 1B"}
    first = {}
    for r in summ:
        f = REPO / f"sim/llm/results/{r['model']}/mul2/{r['reward']}/seed{r['seed']}.jsonl"
        ev = [json.loads(x) for x in open(f) if '"pass1"' in x]
        assert ev[0]["step"] == 0 and abs(ev[0]["pass1"] - r["pass1_0"]) < 1e-12, f
        first[(r["model"], r["reward"], r["seed"])] = ev[0].get("truncated")
    failed = {(x["model"], x["reward"], x["seed"]) for x in extra["failed"]}
    for lang in LANGS:
        mod = MOD if lang == "fr" else MODEN
        rw = {"true": L(lang, "vraie", "true"), "random": L(lang, "au hasard", "random")}
        head = [L(lang, r" & & & & \multicolumn{3}{c}{Réussite au premier essai (\%)} & \multicolumn{2}{c}{Réponses coupées (\%)}",
                  r" & & & & \multicolumn{3}{c}{First-attempt success (\%)} & \multicolumn{2}{c}{Cut-off answers (\%)}"),
                r"\cmidrule(lr){5-7}\cmidrule(lr){8-9}",
                L(lang, r"Modèle & Récompense & Graine & Matériel & pas 0 & pas 100 & gain (pts) & pas 0 & pas 100",
                  r"Model & Reward & Seed & Device & step 0 & step 100 & gain (pts) & step 0 & step 100")]
        rows = []
        idx = {(r["model"], r["reward"], r["seed"]): r for r in summ}
        for m in ("qwen05", "llama1"):
            for rew in ("true", "random"):
                for sd in range(5):
                    lead = [mod[m] if (rew == "true" and sd == 0) else "", rw[rew] if sd == 0 else "", str(sd)]
                    r = idx.get((m, rew, sd))
                    if r is None:
                        assert (m, rew, sd) in failed
                        rows.append(" & ".join(lead + [r"GPU (MPS)", rf"\multicolumn{{5}}{{l}}{{{L(lang, 'échec deux fois (écart 16)', 'failed twice (deviation 16)')}}}"]))
                        continue
                    dev = {"mps": "GPU (MPS)", "cpu": "CPU"}[r["device"]]
                    g = r["pass1_100"] - r["pass1_0"]
                    rows.append(" & ".join(lead + [dev, pc(r["pass1_0"], lang), pc(r["pass1_100"], lang), gpts(g, lang),
                                                   pc(first[(m, rew, sd)], lang), pc(r["truncated_100"], lang)]))
                rows.append(r"\addlinespace")
        rows = rows[:-1]
        rows.append("MID")
        rows.append(L(lang, r"\multicolumn{7}{@{}l}{Gain moyen en points [IC bootstrap 95~\%]} & \multicolumn{2}{r}{}", r"\multicolumn{7}{@{}l}{Mean gain in points [95\% bootstrap CI]} & \multicolumn{2}{r}{}"))
        for key in ("qwen05 true", "qwen05 random", "llama1 true", "llama1 random"):
            m, rew = key.split()
            g = gains[key]
            sig = g["ci"][0] > 0 or g["ci"][1] < 0
            rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\quad {mod[m]}, {rw[rew]}, {len(g['gains'])} {L(lang, 'graines', 'seeds')}}} & \multicolumn{{2}}{{r}}{{{bold(gpts(g['mean'], lang) + ' ' + iv(gpts(g['ci'][0], lang), gpts(g['ci'][1], lang), lang), sig)}}}")
        for key, g in extra["cpu"].items():
            m, rew = key.split()
            rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\quad {mod[m]}, {rw[rew]}, CPU {L(lang, 'seul, graines', 'only, seeds')} {', '.join(map(str, g['seeds']))}}} & \multicolumn{{2}}{{r}}{{{bold(gpts(g['mean'], lang) + ' ' + iv(gpts(g['ci'][0], lang), gpts(g['ci'][1], lang), lang), g['ci'][0] > 0 or g['ci'][1] < 0)}}}")
        for x in extra["missing"]:
            lab = L(lang, {"smallest": "plus petit", "largest": "plus grand"}[x["filled_with"]], x["filled_with"])
            rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\quad {mod[x['model']]}, {rw[x['reward']]}, {L(lang, 'graine 4 = ' + lab + ' gain, ', 'seed 4 = ' + lab + ' gain, ') + gpts(x['value'], lang)} }} & \multicolumn{{2}}{{r}}{{{gpts(x['mean'], lang)} {iv(gpts(x['ci'][0], lang), gpts(x['ci'][1], lang), lang)}}}")
        cap = L(lang,
                r"Volet GRPO (\file{sim/llm/LLM_PROTOCOL.md}) : deux petits modèles ouverts, Qwen2.5 à 0,5 milliard de paramètres et Llama 3.2 à 1 milliard, entraînés 100 pas sur la tâche \texttt{mul2} (produit de deux nombres de 12 à 99), avec la vraie récompense puis une récompense tirée à pile ou face, cinq graines (0 à 2 puis 3 et 4, écart 14). "
                r"Réussite au premier essai : pass@1 échantillonné sur les problèmes de test, en pourcentage ; gain : pas 100 moins pas 0, en points ; réponses coupées : part des réponses qui atteignent la limite de 160 jetons sans donner de résultat, toutes comptées fausses. "
                r"Matériel : GPU Apple (MPS) ou CPU ; trois essais Qwen sont passés sur CPU après des gradients non finis sur MPS (écarts 10 et 11), si bien que matériel et graine se confondent pour Qwen. "
                r"Partie basse : statistique préregistrée, moyenne des gains par graine et intervalle bootstrap percentile à 95~\% (10\,000 tirages, \texttt{random.Random(0)}), très grossier avec cinq graines ; \textbf{en gras}, les intervalles qui excluent zéro. "
                r"La configuration Llama, récompense au hasard, est résumée sur ses quatre essais finis (écart 16), avec la sensibilité au gain manquant. "
                r"Sources : \file{sim/llm/results/summary\_5.json}, \file{gains\_5.json}, \file{extra\_5.json} ; part coupée au pas 0 : première évaluation de chaque fichier \file{sim/llm/results/<modèle>/mul2/<récompense>/seed<g>.jsonl}.",
                r"GRPO strand (\file{sim/llm/LLM_PROTOCOL.md}): two small open models, Qwen2.5 with 0.5 billion parameters and Llama 3.2 with 1 billion, trained for 100 steps on the \texttt{mul2} task (product of two numbers from 12 to 99), with the true reward and then with a reward decided by a coin toss, five seeds (0 to 2 then 3 and 4, deviation 14). "
                r"First-attempt success: sampled pass@1 on the test problems, in percent; gain: step 100 minus step 0, in points; cut-off answers: share of answers that hit the 160-token limit before giving a result, all scored as wrong. "
                r"Device: Apple GPU (MPS) or CPU; three Qwen runs moved to CPU after non-finite gradients on MPS (deviations 10 and 11), so device and seed are confounded for Qwen. "
                r"Bottom part: the preregistered statistic, mean of the per-seed gains with a 95\% percentile bootstrap interval (10,000 draws, \texttt{random.Random(0)}), very rough with five seeds; \textbf{in bold}, intervals that exclude zero. "
                r"The Llama configuration with the random reward is summarised over its four finished runs (deviation 16), with the sensitivity to the missing gain. "
                r"Sources: \file{sim/llm/results/summary\_5.json}, \file{gains\_5.json}, \file{extra\_5.json}; cut-off share at step 0: first evaluation of each file \file{sim/llm/results/<model>/mul2/<reward>/seed<s>.jsonl}.")
        floattable("grpo", lang, cap, L(lang, "GRPO : modèles, récompenses, graines", "GRPO: models, rewards, seeds"),
                   r"@{}lllrrrrrr@{}", head, rows, tabcolsep="3.2pt")


def gpts(g, lang):
    """A gain in percentage points: to the unit, one decimal when it rounds to less than one point."""
    v = D(g) * 100
    return num(v, lang, 1 if abs(q(v, 0)) < 1 and v != 0 else 0, sign=True)


# ----------------------------------------------------------------------------------------------------------------
# Deviations
# ----------------------------------------------------------------------------------------------------------------
MOM = {
    "cod": ("pendant le codage, avant l'agrégation", "during coding, before aggregation"),
    "av": ("avant les résultats", "before the results"),
    "ap": ("après les résultats", "after the results"),
    "apav": ("après les résultats, avant ce calcul", "after the results, before this computation"),
    "ne": ("sans effet sur les résultats", "no effect on the results"),
    "fait": ("constat, sans résultat retenu", "report, no retained result"),
}

# (number, date (day of November 2026, or None, or a "d1-d2" night), moment, French summary, English summary)
DEV_STUDY = [
    (1, None, "cod", r"X4 harmonisé : \texttt{yes} exige un réglage décrit des références ; « même configuration » sans réglage devient \texttt{no}.",
     r"X4 harmonised: \texttt{yes} requires a described tuning of the baselines; `same configuration' with no tuning becomes \texttt{no}."),
    (2, None, "cod", r"X7 harmonisé : \texttt{yes} exige une quantité de calcul (heures, GPU-heures, FLOP) ; le nom du matériel seul vaut \texttt{no}.",
     r"X7 harmonised: \texttt{yes} requires a quantity of compute (hours, GPU-hours, FLOP); the hardware name alone is \texttt{no}."),
    (3, None, "cod", r"Articles sans expérience (Q1 \texttt{no}) : Q2 à Q8 et X1 à X4 en \texttt{na}, hors des dénominateurs.",
     r"Papers with no experiment (Q1 \texttt{no}): Q2 to Q8 and X1 to X4 set to \texttt{na}, out of the denominators."),
    (4, None, "cod", r"Q7 pour un article théorique à expériences jouets : \texttt{no}, pas \texttt{na}.",
     r"Q7 for a theory paper with toy experiments: \texttt{no}, not \texttt{na}."),
    (5, None, "cod", r"X3 : une sélection non dite mais visible dans les tableaux de l'article (LR10) vaut \texttt{yes}.",
     r"X3: a selection unstated but visible in the paper's own tables (LR10) counts as \texttt{yes}."),
    (6, None, "cod", r"Q5 : un code « rendu public plus tard » vaut \texttt{no} ; une page de projet vaut \texttt{yes} seulement si elle mène au code.",
     r"Q5: code `to be made public' is \texttt{no}; a project page is \texttt{yes} only if it leads to the code."),
    (7, None, "cod", r"Calibration sur 12 articles de 2018 : notre grille plus sévère que Pineau sur Q3, plus indulgente sur Q7 ; un changement doit tenir contre les deux références.",
     r"Calibration on 12 papers from 2018: our grid stricter than Pineau's on Q3, more lenient on Q7; a change must hold against both references."),
    (8, None, "cod", r"Annexes séparées de 2018 lues (ICML, NeurIPS) ; en 2026 elles sont dans le PDF ; C21 n'a pas d'annexe publiée.",
     r"Separate 2018 appendices read (ICML, NeurIPS); in 2026 they are inside the PDF; C21 has no published appendix."),
    (9, None, "cod", r"Adresse de contact retirée de l'en-tête User-Agent des téléchargements ; sans effet sur les données.",
     r"Contact address removed from the User-Agent header of the downloads; no effect on the data."),
    (10, None, "cod", r"Scripts de travail écrasés dans l'espace partagé des lecteurs ; les codages, dans des dossiers séparés, sont intacts.",
     r"Working scripts overwritten in the readers' shared space; the codings, in separate folders, are untouched."),
    (11, 9, "av", r"Grille v2 (Y1 à Y12) pour les failles que la v1 ne mesure pas ; Y11 et Y12 ajoutés le même jour, avant tout codage.",
     r"Grid v2 (Y1 to Y12) for the flaws grid v1 leaves unmeasured; Y11 and Y12 added the same day, before any coding."),
    (12, 9, "av", r"Élargissement : 2018 porté à 50 articles (A2), RL classique de 2026 à 50 (A3, tri sur le titre) ; analyse fixée (Newcombe, Fisher, Holm) ; double lecture de 10 articles.",
     r"Enlargement: 2018 brought to 50 papers (A2), classical RL 2026 to 50 (A3, title screen); analysis fixed (Newcombe, Fisher, Holm); double reading of 10 papers."),
    (13, 9, "av", r"Relecture humaine à l'aveugle de 10 articles prévue (A1), abandonnée à l'écart 23.",
     r"Blind human review of 10 papers planned (A1), abandoned in deviation 23."),
    (14, 9, "av", r"Règles de décision de la grille v2 (portée, cas limites de Y1 à Y12) ; fiche \file{GRILLE.md}, contrôle \file{check\_codes.py}.",
     r"Decision rules of grid v2 (scope, edge cases of Y1 to Y12); sheet \file{GRILLE.md}, check \file{check\_codes.py}."),
    (15, 9, "ap", r"Règles des écarts 1, 2 et 4 appliquées aussi aux 12 articles de 2018, oubliés jusque-là ; aucune règle nouvelle.",
     r"Rules of deviations 1, 2 and 4 applied to the 12 papers from 2018 as well, left out until then; no new rule."),
    (16, 9, "av", r"Pilote de trois articles (LR08, ML15, C218) pour repérer les règles ambiguës ; ses lectures n'entrent dans aucune analyse.",
     r"Pilot of three papers (LR08, ML15, C218) to find ambiguous rules; its readings enter no analysis."),
    (17, 9, "av", r"Règles précisées après le pilote (annexes de 2018, Y1, Y3, Y5 à Y9, Y11, format) ; 9 articles d'ICLR 2026 injoignables sautés dans la file A3.",
     r"Rules clarified after the pilot (2018 appendices, Y1, Y3, Y5 to Y9, Y11, format); 9 unreachable ICLR 2026 papers skipped in the A3 queue."),
    (18, 9, ("après la lecture de A3, avant tout pourcentage", "after reading A3, before any percentage"),
     r"X5 (famille) lu sur le modèle que le RL entraîne, pour décider l'entrée des articles de A3 dans l'échantillon classique.",
     r"X5 (family) read on the model the RL trains, to decide which A3 papers enter the classical sample."),
    (19, 9, ("après l'audit des lectures, avant tout pourcentage", "after the audit of the readings, before any percentage"),
     r"Harmonisation de la grille v2 : 80 codes changés, chacun motivé dans \file{overrides\_v2.json}, pour les deux années.",
     r"Harmonisation of grid v2: 80 codes changed, each with its reason in \file{overrides\_v2.json}, for both years."),
    (20, 9, "ap", r"Règle de verdict : seule la comparaison avec la même grille (RL classique 2026 contre notre lecture de 2018) tranche ; les chiffres de Pineau restent un contexte.",
     r"Verdict rule: only the same-grid comparison (classical RL 2026 against our reading of 2018) decides; Pineau's figures remain context."),
    (21, 10, "apav", r"Contrôles exploratoires (provenance, source du PDF, Mantel-Haenszel, lecteur retiré) et test à l'aveugle de la thèse du coût et du risque.",
     r"Exploratory checks (provenance, PDF source, Mantel-Haenszel, reader removed) and blind test of the cost and risk thesis."),
    (22, 10, "av", r"Listes de contrôle des 30 articles NeurIPS 2025 lus, extraites et confrontées à nos codes (A5).",
     r"Checklists of the 30 NeurIPS 2025 papers read, extracted and set against our codes (A5)."),
    (23, 10, "av", r"Relecture humaine (A1) abandonnée, décision de Warith Harchaoui ; dite parmi les limites.",
     r"Human review (A1) abandoned, decision of Warith Harchaoui; stated among the limitations."),
    (24, 10, "av", r"Sensibilité au filtre de titre (A6) : 400 articles hors filtre, résumés lus, puis 20 articles de RL caché lus avec les deux grilles.",
     r"Sensitivity to the title filter (A6): 400 papers outside the filter, abstracts read, then 20 hidden RL papers read with both grids."),
    (25, 10, "av", r"Trajectoire de 2018 à 2026 (A4) : 20 articles de RL classique par année d'ICML et NeurIPS 2019, 2020, 2022 et 2024 ; Cochran-Armitage.",
     r"Trajectory from 2018 to 2026 (A4): 20 classical RL papers per year from ICML and NeurIPS 2019, 2020, 2022 and 2024; Cochran-Armitage."),
    (26, 11, "av", r"Seconde lecture à l'aveugle de 10 articles de A4 (lecteur R3).",
     r"Blind second reading of 10 A4 papers (reader R3)."),
    (27, 15, ("après les résultats, avant toute recherche", "after the results, before any search"),
     r"Recherche par mots-clés contre les « non » de la comparaison principale, arbitre à l'aveugle ; décisions retournées, puis douteuses.",
     r"Keyword search against the `no' decisions of the main comparison, blind arbiter; decisions turned, then doubtful ones."),
    (28, 15, "ap", r"Provenance des lecteurs publiée (\file{readers/}) : deux lecteurs ont fini sur \texttt{claude-opus-5} (13 articles) ; les lectures ne changent pas.",
     r"Provenance of the readers published (\file{readers/}): two readers finished on \texttt{claude-opus-5} (13 papers); the readings do not change."),
    (29, 15, "apav", r"Comparaison principale et trajectoire refaites sans les 13 articles lus en partie par \texttt{claude-opus-5}.",
     r"Main comparison and trajectory redone without the 13 papers read partly by \texttt{claude-opus-5}."),
    (30, 21, "apav", r"Analyses complémentaires sans lecture nouvelle : intervalles de l'accord, plus petite différence détectable, règle de verdict d'origine, lecteurs et année confondus.",
     r"Further analyses with no new reading: intervals of the agreement, minimum detectable difference, original verdict rule, readers and year confounded."),
    (31, 21, ("après les résultats, avant tout téléchargement", "after the results, before any download"), r"Q5 relu sur la dernière version arXiv (2018) et sur les actes (2026), arbitre à l'aveugle, dates de création des dépôts.",
     r"Q5 reread on the latest arXiv version (2018) and on the proceedings (2026), blind arbiter, creation dates of the repositories."),
    (32, 21, ("après les résultats, avant toute lecture", "after the results, before any reading"), r"Nouveau critère X8 : incertitude calculée sur des graines, lue par huit agents neufs sur les deux années.",
     r"New criterion X8: uncertainty computed over seeds, read by eight fresh agents across both years."),
    (33, 21, ("après les résultats, avant toute lecture", "after the results, before any reading"), r"Lecteur d'une autre famille de modèles (\texttt{gemma3:12b}, local) sur les 98 articles de la comparaison principale.",
     r"A reader from another model family (\texttt{gemma3:12b}, local) on the 98 papers of the main comparison."),
]

DEV_SIM = [
    (1, None, ("avant le premier entraînement", "before the first training run"), r"SAC et CrossQ : 200\,000 pas au lieu de 300\,000, faute de calcul ; TD3 non lancé.",
     r"SAC and CrossQ: 200,000 steps instead of 300,000, for lack of compute; TD3 not launched."),
    (2, None, "ap", r"E6 : erreur de notre côté (gamma de normalisation 0,99 au lieu de 0,999) ; recette corrigée relancée, diagnostic sur Hopper v4 et v5.",
     r"E6: an error on our side (normalisation gamma 0.99 instead of 0.999); corrected recipe rerun, diagnosis on Hopper v4 and v5."),
    (3, 9, "ap", r"E1 : seconde statistique, le $t$ moyen le long de la courbe comme Henderson et al. (\file{e1\_curve.py}).",
     r"E1: a second statistic, the mean $t$ along the curve as in Henderson et al. (\file{e1\_curve.py})."),
    (4, 9, ("avant tout entraînement TRPO", "before any TRPO run"), r"B1 : 30 entraînements de TRPO sur HalfCheetah et trois lectures de la statistique de Henderson et al.",
     r"B1: 30 TRPO runs on HalfCheetah and three readings of Henderson et al.'s statistic."),
    (5, 9, ("après \\file{e6\\_diag}, avant tout entraînement officiel", "after \\file{e6\\_diag}, before any official run"), r"E6 : dix agents entraînés avec le script officiel du Zoo, évalués avec notre protocole.",
     r"E6: ten agents trained with the Zoo's official script, evaluated with our protocol."),
    (6, 9, ("après \\file{b1\\_trpo}, avant ce calcul", "after \\file{b1\\_trpo}, before this computation"), r"B1 : le script publié par Henderson en 2017 (\file{from\_same\_dist.py}) appliqué à nos courbes.",
     r"B1: the script Henderson published in 2017 (\file{from\_same\_dist.py}) applied to our curves."),
    (7, 10, ("après PPO et SAC, avant de regarder CrossQ", "after PPO and SAC, before looking at CrossQ"), r"Détails d'analyse de E2, E4 et E5 (score final, IQM, probabilité d'amélioration, inversions, tirages).",
     r"Analysis details of E2, E4 and E5 (final score, IQM, probability of improvement, reversals, draws)."),
    (8, 10, ("après PPO et SAC, avant de regarder CrossQ", "after PPO and SAC, before looking at CrossQ"), r"B3 : trois mesures (score final, meilleur score, moyenne de la courbe) et inversions de classement.",
     r"B3: three measures (final score, best score, mean of the curve) and ranking reversals."),
    (9, 11, "ne", r"Organisation : le second worker prend la file CrossQ par l'autre bout.",
     r"Organisation: the second worker takes the CrossQ queue from the other end."),
    (10, 12, "ne", r"Arrêt par le surveillant (swap) ; deux entraînements CrossQ relancés depuis zéro.",
     r"Stop by the watchdog (swap); two CrossQ runs relaunched from scratch."),
    (11, 13, "ap", r"Fin des simulations ; complément descriptif de E7 (classement par IQM dans les deux physiques, sans test).",
     r"End of the simulations; descriptive complement to E7 (ranking by IQM in both physics, no test)."),
    (12, 15, ("avant tout nouvel entraînement", "before any new run"), r"Consolidation : graines 10 à 19 (160 entraînements), E7 à plusieurs intensités, lecture à budget égal (200\,000 pas).",
     r"Consolidation: seeds 10 to 19 (160 runs), E7 at several strengths, reading at equal budget (200,000 steps)."),
    (13, 15, "ap", r"Intervalles rendus reproductibles : rliable ignore \texttt{random\_state}, le générateur global de NumPy est fixé ; verdicts inchangés.",
     r"Intervals made reproducible: rliable ignores \texttt{random\_state}, NumPy's global generator is seeded; verdicts unchanged."),
    (14, 15, "ap", r"Corrections après relecture critique : date du script \file{dose.py}, comptes des écarts 7 et 8, SB3 2.9.2, pas réels, relances non déclarées, graines lues, registre.",
     r"Corrections after a critical review: date of \file{dose.py}, counts in deviations 7 and 8, SB3 2.9.2, actual steps, undeclared relaunches, seeds read, ledger."),
    (15, 15, "ne", r"Jusqu'à huit cœurs accordés au projet selon la charge de la machine.",
     r"Up to eight cores granted to the project depending on the machine's load."),
    (16, 16, "ne", r"Nuit du 15 au 16 novembre : arrêt par le surveillant, worker survivant corrigé, règle de batterie.",
     r"Night of 15 to 16 November: stop by the watchdog, surviving worker fixed, battery rule."),
    (17, 16, "ne", r"Condition de batterie levée.", r"Battery condition lifted."),
    (18, 16, "apav", r"E2 : les 24 intervalles de probabilité d'amélioration rendus simultanés par Bonferroni (99,79~\%).",
     r"E2: the 24 probability-of-improvement intervals made simultaneous by Bonferroni (99.79\%)."),
    (19, 19, "ne", r"Plafond de deux cœurs pour tout le projet ; surveillant relancé.",
     r"Cap of two cores for the whole project; watchdog restarted."),
    (20, 21, ("après les entraînements, avant tout calcul sur les graines 10 à 19", "after the runs, before any computation on seeds 10 to 19"),
     r"Calcul des ajouts de l'écart 12 ; défaut de \file{e5.py} corrigé (bon ordre sur toutes les graines choisies).",
     r"Computation of the additions of deviation 12; defect of \file{e5.py} fixed (right order over all the chosen seeds)."),
    (21, 21, "apav", r"E2 : décompte strict, une paire ne compte que si chacun bat l'autre de façon tranchée sur une tâche (défaut corrigé).",
     r"E2: strict count, a pair counts only if each beats the other, settled, on some task (defect fixed)."),
    (22, 21, "apav", r"E1 refait sur les seize couples (programme, tâche), graines 0 à 19.",
     r"E1 redone on the sixteen (program, task) pairs, seeds 0 to 19."),
    (23, 21, "apav", r"E3 avec la correction de Holm sur quatre tâches, écart en points et puissance.",
     r"E3 with Holm's correction over four tasks, gap in points and power."),
    (24, 21, "apav", r"E7 : le renversement sur Hopper en physique modifiée, testé paire par paire.",
     r"E7: the Hopper reversal under modified physics, tested pair by pair."),
    (25, 21, "apav", r"E5 vérifié hors échantillon : graines 0 à 9 jugées sur les graines 10 à 19, et l'inverse.",
     r"E5 checked out of sample: seeds 0 to 9 judged on seeds 10 to 19, and the reverse."),
    (26, 21, "apav", r"La règle « tranché » calibrée sur de vraies hypothèses nulles (deux groupes du même programme).",
     r"The `settled' rule calibrated on true null hypotheses (two groups of the same program)."),
    (27, 21, "apav", r"B1 : le facteur entre le $t$ du script et celui des graines vaut $\sqrt{n/5}/\rho$ (défaut corrigé).",
     r"B1: the factor between the script's $t$ and the seeds' $t$ is $\sqrt{n/5}/\rho$ (defect fixed)."),
    (28, 21, ("relevé, sans calcul statistique", "a record, no statistical computation"), r"Les hyperparamètres effectivement utilisés, lus dans les programmes construits et les modèles sauvegardés.",
     r"The hyperparameters actually used, read from the built programs and the saved models."),
    (29, 21, "apav", r"Courbes d'apprentissage : classement au fil de l'entraînement, score final contre meilleur point, autocorrélation.",
     r"Learning curves: ranking during training, final score against best point, autocorrelation."),
    (30, 21, ("avant ce calcul", "before this computation"), r"Tailles d'effet en points de score (Hodges-Lehmann) pour E2, E3 et E6.",
     r"Effect sizes in score points (Hodges-Lehmann) for E2, E3 and E6."),
    (31, 21, "apav", r"E6 : vitesse des agents officiels lue dans leurs journaux d'entraînement.",
     r"E6: speed of the official agents read from their training logs."),
    (32, 21, ("avant tout entraînement", "before any training run"), r"Déterminisme de SAC et CrossQ : trois entraînements refaits à l'identique.",
     r"Determinism of SAC and CrossQ: three training runs redone identically."),
    (33, 21, ("avant ces évaluations et cet entraînement", "before these evaluations and this training"), r"E6 : agents officiels rejoués (vitesse, vidéos), agent publié par le Zoo évalué, recette avec $\gamma = 0{,}99$.",
     r"E6: official agents replayed (speed, videos), the agent published by the Zoo evaluated, recipe with $\gamma = 0.99$."),
    (34, 21, ("avant tout entraînement", "before any training run"), r"Pourquoi les deux PPO divergent : graines 20 à 39 et initialisation orthogonale échangée.",
     r"Why the two PPOs diverge: seeds 20 to 39 and orthogonal initialisation swapped."),
]

DEV_LLM = [
    (1, None, ("après lecture de sorties, avant tout entraînement", "after reading outputs, before any training"), r"Limite de longueur portée de 64 à 160 jetons.",
     r"Length limit raised from 64 to 160 tokens."),
    (2, None, ("avant tout entraînement", "before any training"), r"Mesures réduites à 150 problèmes en glouton et 50 en échantillonnage, pour le coût.",
     r"Measures reduced to 150 problems for greedy decoding and 50 for sampling, for cost."),
    (3, None, ("après le pilote, avant tout entraînement", "after the pilot, before any training"), r"Tâche \texttt{mul2} retenue ; mesure principale : pass@1 échantillonné.",
     r"Task \texttt{mul2} chosen; main measure: sampled pass@1."),
    (4, 8, "fait", r"Le pilote du taux d'apprentissage sature la mémoire (swap) ; arrêté, aucun résultat utilisable.",
     r"The learning-rate pilot saturates memory (swap); killed, no usable result."),
    (5, 9, "fait", r"Diagnostic sans entraînement : 23 réponses sur 32 coupées à 160 jetons au pas 10 du pilote.",
     r"Diagnosis without training: 23 answers out of 32 cut off at 160 tokens at step 10 of the pilot."),
    (6, 9, ("avant tout essai retenu", "before any retained run"), r"Version réduite : 100 pas, graines 0 à 2, taux 3e-6, mises à jour par lots de 8 réponses, plafond mémoire.",
     r"Reduced version: 100 steps, seeds 0 to 2, learning rate 3e-6, updates in batches of 8 answers, memory cap."),
    (7, 9, ("règle fixée avant tout résultat de la graine", "rule fixed before any result for the seed"), r"Pause à la demande de Warith ; plantage \texttt{nan} d'un essai Qwen ; une seule relance prévue.",
     r"Pause at Warith's request; \texttt{nan} crash of a Qwen run; a single relaunch planned."),
    (8, 9, "fait", r"Reprise : aucun des neuf essais restants n'aboutit (\texttt{nan}, coupure par macOS, mémoire MPS).",
     r"Resumption: none of the nine remaining runs completes (\texttt{nan}, macOS cut-off, MPS memory)."),
    (9, 9, ("avant tout résultat de ces essais", "before any result of these runs"), r"Relance de nuit (\file{night.sh}) avec un essai de contrôle en tête.",
     r"Night relaunch (\file{night.sh}) with a control run first."),
    (10, 10, "fait", r"Cause des \texttt{nan} trouvée : gradients non finis sur MPS, propres sur CPU ; garde-fous de recalcul.",
     r"Cause of the \texttt{nan} found: non-finite gradients on MPS, clean on CPU; recomputation safeguards."),
    (11, 10, ("avant tout essai retenu avec ce code", "before any retained run with this code"), r"Les essais Qwen restants passent sur CPU ; Llama reste sur GPU la nuit.",
     r"The remaining Qwen runs move to CPU; Llama stays on GPU at night."),
    (12, "10-11", ("corrections avant toute relance", "corrections before any relaunch"), r"Qwen fini sur CPU ; les six essais Llama manquent de mémoire MPS ; cache vidé à chaque pas, plafond relevé.",
     r"Qwen finished on CPU; the six Llama runs run out of MPS memory; cache emptied at every step, cap raised."),
    (13, "11-12", ("détails de la statistique fixés après les résultats", "statistic details set after the results"), r"Les douze essais finis ; bootstrap percentile sur les graines, 10\,000 tirages.",
     r"All twelve runs finished; percentile bootstrap over the seeds, 10,000 draws."),
    (14, 15, ("avant tout nouvel essai", "before any new run"), r"Cinq graines : graines 3 et 4 ajoutées pour les deux modèles et les deux récompenses.",
     r"Five seeds: seeds 3 and 4 added for both models and both rewards."),
    (15, 15, "ap", r"Corrections après relecture critique (comptes de l'écart 8, dates) ; aucun résultat ne change.",
     r"Corrections after a critical review (counts of deviation 8, dates); no result changes."),
    (16, 17, ("après les valeurs au pas 100, avant tout gain", "after the step-100 values, before any gain"), r"Llama, récompense au hasard, graine 4 échoue deux fois : compté comme résultat ; statistique sur les essais finis, sensibilité au gain manquant.",
     r"Llama, random reward, seed 4 fails twice: counted as a result; statistic over the finished runs, sensitivity to the missing gain."),
    (17, 19, "ne", r"L'essai Llama sur CPU part après la file, sous le plafond de deux cœurs.",
     r"The Llama CPU run starts after the queue, under the two-core cap."),
    (18, 21, "ap", r"Défauts constatés : pénalité de répétition 1,1 chez Qwen, pilote lu sur le jeu de test, matériel et graine mêlés.",
     r"Defects found: repetition penalty of 1.1 for Qwen, pilot read on the test set, device and seed mixed."),
    (19, 21, ("avant le script", "before the script"), r"Analyses tirées des journaux : justesse gloutonne, pass@8, intervalles de Student, vraie récompense contre hasard, coupure.",
     r"Analyses from the logs: greedy accuracy, pass@8, Student intervals, true reward against coin flip, truncation."),
    (20, 22, ("avant tout essai de la relance", "before any run of the rerun"), r"Relance planifiée : 10 graines, sans pénalité de répétition, pilote hors du jeu de test ; rien n'est lancé.",
     r"Rerun planned: 10 seeds, no repetition penalty, pilot off the test set; nothing is started."),
]


def protocol_items(rel):
    """{number: text} of the numbered deviations of a protocol file (after its deviations heading)."""
    text = (REPO / rel).read_text()
    head = re.search(r"^## (Écarts|Deviations)\s*$", text, re.M)
    assert head, rel
    items, cur = {}, None
    for line in text[head.end():].splitlines():
        m = re.match(r"^(\d+)\. (.*)", line)
        if m:
            cur = int(m.group(1))
            items[cur] = m.group(2)
        elif cur is not None:
            items[cur] += " " + line.strip()
    return items


def t_ecarts():
    sets = [("study/PROTOCOL.md", "study/PROTOCOL-en.md", DEV_STUDY, ("Sondage", "Survey")),
            ("sim/SIM_PROTOCOL.md", "sim/SIM_PROTOCOL-en.md", DEV_SIM, ("Expériences", "Experiments")),
            ("sim/llm/LLM_PROTOCOL.md", "sim/llm/LLM_PROTOCOL-en.md", DEV_LLM, ("GRPO", "GRPO"))]
    # checks: same numbers as the protocols, and each date found in the deviation's own text in both languages
    for fr, en, devs, _ in sets:
        ifr, ien = protocol_items(fr), protocol_items(en)
        assert sorted(ifr) == sorted(ien) == [d[0] for d in devs], (fr, sorted(ifr), [d[0] for d in devs])
        for n, date, mom, *_ in devs:
            if date is None:
                continue
            days = str(date).split("-")
            for d in days:
                assert re.search(rf"\b{d}\b[^.]*novembre", ifr[n]) or re.search(rf"\b{d} (au \d+ )?novembre", ifr[n]), (fr, n, d)
                assert re.search(rf"\b{d}\b", ien[n]) and "November" in ien[n], (en, n, d)
            if mom == "av":
                assert re.search(r"AVANT|avant", ifr[n]), (fr, n)
            if mom in ("ap", "apav"):
                assert re.search(r"APRÈS|après", ifr[n]), (fr, n)
    total = sum(len(s[2]) for s in sets)
    for lang in LANGS:
        head = [L(lang, r"N\textsuperscript{o} & Date & Moment & Résumé", r"No. & Date & Timing & Summary")]
        rows = []
        for fr, en, devs, title in sets:
            rows.append(rf"\multicolumn{{4}}{{@{{}}l}}{{\textbf{{{L(lang, *title)}}} (\file{{{(fr if lang == 'fr' else en).replace('_', chr(92) + '_')}}}, {len(devs)} {L(lang, 'écarts', 'deviations')})}}")
            for n, date, mom, sfr, sen in devs:
                if date is None:
                    ds = L(lang, "n. d.", "undated")
                elif isinstance(date, str):
                    a, b = date.split("-")
                    ds = L(lang, f"{a}-{b} nov.", f"{a}-{b} Nov.")
                else:
                    ds = L(lang, f"{date} nov.", f"{date} Nov.")
                m = mom if isinstance(mom, tuple) else MOM[mom]
                rows.append(f"{n} & {ds} & {m[0] if lang == 'fr' else m[1]} & {sfr if lang == 'fr' else sen}")
            rows.append(r"\addlinespace")
        rows = rows[:-1]
        cap = L(lang,
                rf"Les {total} écarts aux trois protocoles, dans l'ordre de leurs listes : sondage (\file{{study/PROTOCOL.md}}), expériences (\file{{sim/SIM\_PROTOCOL.md}}), volet GRPO (\file{{sim/llm/LLM\_PROTOCOL.md}}). "
                r"Date : jour de novembre 2026 donné par le protocole (« n. d. » quand l'écart n'est pas daté ; les écarts 1 à 10 du sondage ont été notés pendant le codage, avant l'agrégation). "
                r"Moment : ce que le protocole déclare avoir déjà vu quand l'écart a été écrit (avant ou après les résultats concernés, ou sans effet sur les résultats pour l'organisation du calcul). "
                r"Le résumé tient en une ligne ; le texte complet, qui fait foi, est dans le protocole (version anglaise : fichiers \file{-en.md}). Le nombre des écarts, leur numérotation et leurs dates sont vérifiés contre les fichiers par \file{report/tools/tables.py}.",
                rf"The {total} deviations from the three protocols, in the order of their lists: survey (\file{{study/PROTOCOL-en.md}}), experiments (\file{{sim/SIM\_PROTOCOL-en.md}}), GRPO strand (\file{{sim/llm/LLM\_PROTOCOL-en.md}}). "
                r"Date: day of November 2026 given by the protocol (`undated' when the deviation carries no date; survey deviations 1 to 10 were noted during coding, before aggregation). "
                r"Timing: what the protocol declares had already been seen when the deviation was written (before or after the results concerned, or no effect on the results for the organisation of the computation). "
                r"The summary takes one line; the full text, which prevails, is in the protocol (the French files are the dated originals). The number of deviations, their numbering and their dates are checked against the files by \file{report/tools/tables.py}.")
        longtable("ecarts", lang, cap, L(lang, "Écarts aux trois protocoles", "Deviations from the three protocols"),
                  r"@{}r>{\raggedright\arraybackslash}p{1.25cm}>{\raggedright\arraybackslash}p{3.1cm}>{\raggedright\arraybackslash}p{9.6cm}@{}",
                  head, rows, 4, tabcolsep="3.5pt")


# ----------------------------------------------------------------------------------------------------------------
# Environments and compute
# ----------------------------------------------------------------------------------------------------------------
def t_env():
    files = [("train", "sim/env"), ("analysis", "sim/env-an"), ("zoo", "sim/env-zoo"), ("llm", "sim/env-llm")]
    pins, meta = {}, {}
    for f, _ in files:
        lines = (REPO / f"envs/{f}.txt").read_text().splitlines()
        meta[f] = [l for l in lines if l.startswith("#")]
        pins[f] = {}
        for l in lines:
            m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)", l)
            if m:
                pins[f][m.group(1).lower().replace("_", "-")] = m.group(2)
    py = {f: re.search(r"Python (\d+\.\d+\.\d+)", "\n".join(meta[f])).group(1) for f, _ in files}
    test = {}
    for l in (REPO / "envs/test.txt").read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)==(\S+)", l)
        if m:
            test[m.group(1).lower()] = m.group(2)
    pkgs = [("python", "Python"), ("stable-baselines3", "Stable-Baselines3"), ("sb3-contrib", "sb3-contrib"), ("sbx-rl", "SBX"),
            ("rl-zoo3", "RL Baselines3 Zoo"), ("gymnasium", "Gymnasium"), ("mujoco", "MuJoCo"), ("torch", "PyTorch"),
            ("jax", "JAX"), ("jaxlib", "jaxlib"), ("flax", "Flax"), ("optax", "Optax"), ("transformers", "Transformers"),
            ("accelerate", "Accelerate"), ("numpy", "NumPy"), ("scipy", "SciPy"), ("statsmodels", "statsmodels"),
            ("rliable", "rliable"), ("pandas", "pandas"), ("matplotlib", "Matplotlib")]
    for lang in LANGS:
        head = [L(lang, "Paquet & ", "Package & ") + " & ".join(rf"\file{{{f}.txt}}" for f, _ in files),
                L(lang, r"\emph{environnement} & ", r"\emph{environment} & ") + " & ".join(rf"\file{{{e}}}" for _, e in files)]
        rows = []
        for key, lab in pkgs:
            cells = [py[f] if key == "python" else pins[f].get(key, "") for f, _ in files]
            if not any(cells):
                continue
            rows.append(lab + " & " + " & ".join(c if c else r"\textcolor{muted}{·}" for c in cells))
        nlines = {f: len(pins[f]) for f, _ in files}
        rows.append("MID")
        rows.append(L(lang, "Paquets épinglés & ", "Pinned packages & ") + " & ".join(str(nlines[f]) for f, _ in files))
        cap = L(lang,
                rf"Versions épinglées des paquets principaux dans les quatre environnements Python du projet, toutes sur Python {py['train']}, macOS 27.2 sur puce Apple M2 Max (arm64). "
                r"Chaque fichier \file{envs/<nom>.txt} est le \texttt{pip freeze} de l'environnement, relevé le 15 novembre 2026 ; \file{envs/<nom>.lock} en est le jumeau verrouillé par empreintes SHA-256 (mêmes versions). "
                r"\file{train} : entraînements (\file{sim/run.py}, \file{sim/dose.py}) ; \file{analysis} : tous les scripts d'analyse et l'intégration continue ; \file{zoo} : le pipeline officiel de RL Baselines3 Zoo (E6) ; \file{llm} : GRPO (\file{sim/llm/grpo.py}). "
                rf"Un point : paquet absent de l'environnement. Les tests unitaires ajoutent pytest {test.get('pytest', '')} (\file{{envs/test.txt}}). "
                r"Le protocole annonçait Stable-Baselines3 2.6.0 ; tous les entraînements ont tourné avec 2.9.2 (écart 14 (c) de \file{sim/SIM_PROTOCOL.md}). Les révisions des modèles de langue téléchargés ne sont pas épinglées. Source : \file{envs/*.txt}.",
                rf"Pinned versions of the key packages in the project's four Python environments, all on Python {py['train']}, macOS 27.2 on an Apple M2 Max chip (arm64). "
                r"Each file \file{envs/<name>.txt} is the environment's \texttt{pip freeze}, taken on 15 November 2026; \file{envs/<name>.lock} is its twin locked by SHA-256 hashes (same versions). "
                r"\file{train}: training (\file{sim/run.py}, \file{sim/dose.py}); \file{analysis}: every analysis script and the continuous integration; \file{zoo}: the official RL Baselines3 Zoo pipeline (E6); \file{llm}: GRPO (\file{sim/llm/grpo.py}). "
                rf"A dot: package absent from the environment. The unit tests add pytest {test.get('pytest', '')} (\file{{envs/test.txt}}). "
                r"The protocol announced Stable-Baselines3 2.6.0; every training run used 2.9.2 (deviation 14 (c) of \file{sim/SIM_PROTOCOL.md}). The revisions of the downloaded language models are not pinned. Source: \file{envs/*.txt}.")
        floattable("env", lang, cap, L(lang, "Versions épinglées par environnement", "Pinned versions per environment"),
                   r"@{}lllll@{}", head, rows, tabcolsep="6pt")


def t_calcul():
    groups = []
    for algo in ["ppo_sb3", "ppo_sbx", "sac", "crossq", "trpo", "ppo_sb3_zoo", "ppo_sb3_zoofix"]:
        for d in sorted(glob.glob(str(REPO / f"sim/results/{algo}/*"))):
            task = os.path.basename(d)
            walls, steps = [], set()
            for f in sorted(glob.glob(f"{d}/seed*.csv")):
                with open(f) as fh:
                    rows = list(csv.DictReader(fh))
                walls.append(float(rows[-1]["wall"]))
                steps.add(int(rows[-1]["step"]))
            groups.append((algo, task, len(walls), steps, walls))
    grpo = []
    for m in ("qwen05", "llama1"):
        for rew in ("true", "random"):
            walls, n = [], 0
            for f in sorted(glob.glob(str(REPO / f"sim/llm/results/{m}/mul2/{rew}/seed*.jsonl"))):
                recs = [json.loads(x) for x in open(f)]
                w = [r["wall"] for r in recs if "wall" in r]
                done = any(r.get("step") == 100 and "pass1" in r for r in recs)
                if done and w:
                    walls.append(w[-1])
            grpo.append((m, rew, len(walls), walls))
    with open(REPO / "sim/logs/attempts_reconstructed.csv") as fh:
        att = list(csv.DictReader(fh))
    train_kinds = ("grid", "b1_trpo", "e6_diag")
    launches = [a for a in att if a["kind"] in train_kinds]
    ok = [a for a in launches if a["outcome"].startswith("success")]
    names = {"ppo_sb3": "PPO PyTorch", "ppo_sbx": "PPO JAX", "sac": "SAC", "crossq": "CrossQ", "trpo": "TRPO",
             "ppo_sb3_zoo": "PPO PyTorch, Zoo (gamma 0,99)", "ppo_sb3_zoofix": "PPO PyTorch, Zoo corrigé"}
    names_en = dict(names, ppo_sb3_zoo="PPO PyTorch, Zoo (gamma 0.99)", ppo_sb3_zoofix="PPO PyTorch, Zoo corrected")
    for lang in LANGS:
        nm = names if lang == "fr" else names_en
        head = [L(lang, r"Programme & Tâche & essais & \makecell[r]{pas\\{}par essai} & \makecell[r]{durée\\{}médiane (h)} & \makecell[r]{total\\{}(h)}",
                  r"Program & Task & runs & \makecell[r]{steps\\{}per run} & \makecell[r]{median\\{}time (h)} & \makecell[r]{total\\{}(h)}")]
        rows = []
        tot_h, tot_n = 0.0, 0
        last = None
        for algo, task, n, steps, walls in groups:
            st = "/".join(num(s, lang) for s in sorted(steps))
            h = sum(walls) / 3600
            tot_h += h
            tot_n += n
            rows.append(" & ".join([nm[algo] if algo != last else "", task, str(n), st, num(statistics.median(walls) / 3600, lang, 2), num(h, lang, 1)]))
            last = algo
        rows.append(L(lang, r"\multicolumn{2}{@{}l}{\emph{Total des entraînements MuJoCo}}", r"\multicolumn{2}{@{}l}{\emph{Total MuJoCo training}}")
                    + f" & {tot_n} & & & {num(tot_h, lang, 1)}")
        rows.append("MID")
        g_h, g_n = 0.0, 0
        for m, rew, n, walls in grpo:
            h = sum(walls) / 3600
            g_h += h
            g_n += n
            rows.append(" & ".join([("GRPO, " + {"qwen05": "Qwen2.5 0,5B" if lang == "fr" else "Qwen2.5 0.5B", "llama1": "Llama 3.2 1B"}[m]) if rew == "true" else "",
                                    L(lang, f"mul2, récompense {'vraie' if rew == 'true' else 'au hasard'}", f"mul2, {rew} reward"),
                                    str(n), "100", num(statistics.median(walls) / 3600, lang, 2), num(h, lang, 1)]))
        rows.append(L(lang, r"\multicolumn{2}{@{}l}{\emph{Total GRPO (essais finis)}}", r"\multicolumn{2}{@{}l}{\emph{Total GRPO (finished runs)}}")
                    + f" & {g_n} & & & {num(g_h, lang, 1)}")
        cap = L(lang,
                r"Calcul des expériences, relevé dans les fichiers de résultats : pour chaque programme et chaque tâche, nombre d'essais finis, pas d'entraînement par essai (colonne \texttt{step} de la dernière ligne), durée murale médiane d'un essai et somme des durées, en heures. "
                r"La durée murale est la colonne \texttt{wall} de \file{sim/results/<programme>/<tâche>/seed<g>.csv} à la dernière évaluation (secondes depuis le lancement, évaluations comprises), et pour GRPO le dernier \texttt{wall} des pas d'entraînement de \file{sim/llm/results/<modèle>/mul2/<récompense>/seed<g>.jsonl}. "
                r"Ce ne sont pas des heures-cœurs : chaque entraînement tournait sur un fil, PPO JAX sur deux au début (écart 4), GRPO sur le GPU Apple ou sur deux fils CPU, sur une machine partagée dont la charge variait ; les réévaluations de E7 à plusieurs intensités et les dix agents officiels du Zoo (E6) n'enregistrent pas leur durée et manquent ici. "
                rf"Les modèles PPO et TRPO comptent en vérité 1\,024\,000 pas (blocs de 51\,200, écart 14 (d)). Le registre reconstruit \file{{sim/logs/attempts\_reconstructed.csv}} compte {len(launches)} lancements pour les entraînements de la grille, de B1 et du diagnostic de E6, dont {len(ok)} aboutis (écart 14 (e)).",
                r"Compute of the experiments, read from the result files: for each program and task, number of finished runs, training steps per run (column \texttt{step} of the last row), median wall-clock time of one run and sum of the times, in hours. "
                r"Wall-clock time is the column \texttt{wall} of \file{sim/results/<program>/<task>/seed<s>.csv} at the last evaluation (seconds since launch, evaluations included), and for GRPO the last \texttt{wall} of the training steps of \file{sim/llm/results/<model>/mul2/<reward>/seed<s>.jsonl}. "
                r"These are not core-hours: each training run ran on one thread, PPO JAX on two at first (deviation 4), GRPO on the Apple GPU or on two CPU threads, on a shared machine whose load varied; the re-evaluations of E7 at several strengths and the ten official Zoo agents (E6) do not record their duration and are missing here. "
                rf"The PPO and TRPO models actually count 1,024,000 steps (blocks of 51,200, deviation 14 (d)). The reconstructed ledger \file{{sim/logs/attempts\_reconstructed.csv}} counts {len(launches)} launches for the training runs of the grid, of B1 and of the E6 diagnosis, {len(ok)} of them successful (deviation 14 (e)).")
        floattable("calcul", lang, cap, L(lang, "Calcul des expériences", "Compute of the experiments"),
                   r"@{}>{\raggedright\arraybackslash}p{4.2cm}lrrrr@{}", head, rows, tabcolsep="4pt")


# ----------------------------------------------------------------------------------------------------------------
# Paper lists
# ----------------------------------------------------------------------------------------------------------------
def survey_values():
    st = REPO / "study"
    ov1 = load_overrides(str(st / "overrides.json"), missing_ok=True)
    ov2 = load_overrides(str(st / "overrides_v2.json"), missing_ok=True)
    old = load_reads(str(st / "codes"), "ABCDEF")
    primary = ["A2", "B2", "C2", "D2", "E2", "F2", "H1", "H2", "H3", "H4"]
    v2 = load_reads(str(st / "codes_v2"), primary + list_readers(str(st / "codes_v2"), "K*"))
    return (lambda pid, k: value(pid, k, v2, old, ov2, ov1)), v2


FAM = {"llm": ("grands modèles", "large models"), "classic": ("classique", "classical"), "theory": ("théorie", "theory")}


def t_articles():
    val, v2 = survey_values()
    ext = J("study/extension_stats.json")["samples"]
    a3 = set(ext["a3"])
    first = J("study/final_2026.json")
    queue = J("study/classic_queue_2026.json")
    read_a3 = [x for x in queue if x["id"] in v2]
    last = max(i for i, x in enumerate(read_a3) if x["id"] in a3)
    calib = J("study/calib_2018_v2.json")
    pop18 = J("study/rl_population_2018.json")
    for lang in LANGS:
        ex = lambda pid: val(pid, "Q1") != "no"  # noqa: E731
        rows = [rf"\multicolumn{{4}}{{@{{}}l}}{{\textbf{{{L(lang, 'Premier tirage aléatoire', 'First random draw')}}} ({len(first)} {L(lang, 'articles', 'papers')}, \file{{study/final\_2026.json}})}}"]
        for x in first:
            fam = val(x["id"], "X5")
            role = L(lang, *FAM[fam]) if fam in FAM else ""
            if not ex(x["id"]):
                role += L(lang, ", sans expérience", ", no experiment")
            rows.append(f"{x['id']} & {esc(x['title'])} & {x['venue']} & {role}")
        rows.append(r"\addlinespace")
        rows.append(rf"\multicolumn{{4}}{{@{{}}l}}{{\textbf{{{L(lang, 'File A3, articles lus', 'A3 queue, papers read')}}} ({len(read_a3)} {L(lang, 'articles', 'papers')}, \file{{study/classic\_queue\_2026.json}})}}")
        for i, x in enumerate(read_a3):
            fam = val(x["id"], "X5")
            if x["id"] in a3:
                role = L(lang, "échantillon classique", "classical sample")
            elif i <= last and fam in ("llm", "theory"):
                role = L(lang, f"à part ({L(lang, *FAM[fam])})", f"apart ({L(lang, *FAM[fam])})")
            else:
                role = L(lang, f"lu après le 36\\textsuperscript{{e}} ({L(lang, *FAM[fam]) if fam in FAM else '?'})",
                         f"read after the 36th ({L(lang, *FAM[fam]) if fam in FAM else '?'})")
            rows.append(f"{x['id']} & {esc(x['title'])} & {x['venue']} & {role}")
        n_after = sum(1 for i, x in enumerate(read_a3) if x["id"] not in a3 and not (i <= last and val(x['id'], 'X5') in ('llm', 'theory')))
        cap = L(lang,
                rf"Les articles de 2026 lus pour le sondage. Premier tirage : 50 articles tirés au hasard parmi les 1\,252 dont le titre parle d'apprentissage par renforcement (ICLR 2026, ICML 2026, NeurIPS 2025). "
                rf"File A3 : les autres articles de la population dans l'ordre d'un mélange \texttt{{random.Random(2026)}}, après un tri sur le titre qui écarte les grands modèles de langage (écart 12) ; {len(read_a3)} articles lus, dont les {len(a3)} premiers articles de RL classique forment, avec les 14 articles classiques du premier tirage, l'échantillon de 50 de la comparaison principale. "
                rf"Les articles de grands modèles et de théorie lus avant le dernier article retenu restent à part ({ext['a3_apart']['llm']} et {ext['a3_apart']['theory']}) ; {n_after} articles lus après lui n'entrent dans aucune analyse. "
                r"Famille : critère X5 harmonisé (écart 18), lu sur le modèle que le RL entraîne. Identifiants : ceux des fichiers de lecture \file{study/codes/} et \file{study/codes\_v2/}, où chaque décision cite l'article avec sa page. Les 80 articles de la trajectoire 2019 à 2024 sont listés dans \file{study/trajectory\_queue.json}.",
                rf"The 2026 papers read for the survey. First draw: 50 papers drawn at random from the 1,252 whose title mentions reinforcement learning (ICLR 2026, ICML 2026, NeurIPS 2025). "
                rf"A3 queue: the other papers of the population in the order of a \texttt{{random.Random(2026)}} shuffle, after a title screen that sets aside large language models (deviation 12); {len(read_a3)} papers read, of which the first {len(a3)} classical RL papers form, with the 14 classical papers of the first draw, the sample of 50 of the main comparison. "
                rf"Large-model and theory papers read before the last paper retained stay apart ({ext['a3_apart']['llm']} and {ext['a3_apart']['theory']}); {n_after} papers read after it enter no analysis. "
                r"Family: criterion X5 harmonised (deviation 18), read on the model the RL trains. Identifiers: those of the reading files \file{study/codes/} and \file{study/codes\_v2/}, where each decision quotes the paper with its page. The 80 papers of the 2019 to 2024 trajectory are listed in \file{study/trajectory\_queue.json}.")
        longtable("articles-2026", lang, cap, L(lang, "Articles de 2026 lus", "2026 papers read"),
                  r"@{}l>{\raggedright\arraybackslash}p{9.0cm}l>{\raggedright\arraybackslash}p{2.6cm}@{}",
                  [L(lang, "Id. & Titre & Conférence & Famille, rôle", "Id & Title & Venue & Family, role")], rows, 4, size=r"\scriptsize", tabcolsep="3pt")
        rows = []
        for i, x in enumerate(calib):
            role = L(lang, "calibration (12)", "calibration (12)") if i < 12 else "A2"
            if not ex(x["id"]):
                role += L(lang, ", sans expérience", ", no experiment")
            rows.append(f"{x['id']} & {esc(x['title'])} & {x['venue']} & {role}")
        nexp = sum(ex(x["id"]) for x in calib)
        cap = L(lang,
                rf"Les {len(calib)} articles de 2018 lus avec les deux grilles. Les 12 premiers forment la calibration de la première version ; les 38 autres (A2, écart 12) sont tirés dans l'ordre d'un mélange \texttt{{random.Random(2018)}} de la population des articles de RL d'ICML, NeurIPS et ICLR 2018 repérés par leur titre ({len(pop18)} articles, \file{{study/rl\_population\_2018.json}}), les trois conférences que Pineau nomme. "
                rf"{nexp} des {len(calib)} articles ont des expériences (Q1) ; les deux autres sortent des dénominateurs. Annexes de 2018 lues à part (ICML, NeurIPS). Source : \file{{study/calib\_2018\_v2.json}}.",
                rf"The {len(calib)} papers from 2018 read with both grids. The first 12 form the calibration of the first version; the other 38 (A2, deviation 12) are drawn in the order of a \texttt{{random.Random(2018)}} shuffle of the population of RL papers of ICML, NeurIPS and ICLR 2018 found by their title ({len(pop18)} papers, \file{{study/rl\_population\_2018.json}}), the three conferences Pineau names. "
                rf"{nexp} of the {len(calib)} papers have experiments (Q1); the other two leave the denominators. 2018 appendices read separately (ICML, NeurIPS). Source: \file{{study/calib\_2018\_v2.json}}.")
        longtable("articles-2018", lang, cap, L(lang, "Articles de 2018 lus", "2018 papers read"),
                  r"@{}l>{\raggedright\arraybackslash}p{9.6cm}l>{\raggedright\arraybackslash}p{2.2cm}@{}",
                  [L(lang, "Id. & Titre & Conférence & Rôle", "Id & Title & Venue & Role")], rows, 4, size=r"\scriptsize", tabcolsep="3pt")


# ----------------------------------------------------------------------------------------------------------------
# Analyses of 22 November 2026 (deviations 21 to 33 of sim/SIM_PROTOCOL.md, 30 to 32 of study/PROTOCOL.md, 18 and 19
# of sim/llm/LLM_PROTOCOL.md), each decided and pushed before its computation
# ----------------------------------------------------------------------------------------------------------------
def ci2(c, lang, nd=2):
    return iv(num(c[0], lang, nd), num(c[1], lang, nd), lang)


def pr_cell(p, c, lang):
    """A probability of improvement and its interval."""
    return f"{num(p, lang, 2)} {ci2(c, lang)}"


def t_e2_strict():
    F = {k: J(f"sim/analysis/e2_strict{k}.json") for k in ("", "_s20", "_equal", "_equal_s20")}
    for lang in LANGS:
        sep = r" \newline "

        def pairs(d, strict_bonf):
            keep = {r["pair"] for r in strict_bonf["reversing_pairs"]}
            out = []
            for r in d["reversing_pairs"]:
                a, b = r["pair"].split("/")
                txt = (f"{ALG[a]} > {ALG[b]} ({', '.join(T(w['task']) for w in r['a_wins'])}){L(lang, ', ', ', ')}"
                       f"{ALG[b]} > {ALG[a]} ({', '.join(T(w['task']) for w in r['b_wins'])})")
                out.append(bold(txt, r["pair"] in keep))
            return sep.join(out)
        head = [L(lang, r" & \multicolumn{2}{c}{\makecell{Décompte\\{}strict}} & \multicolumn{2}{c}{\makecell{Décompte\\{}préenregistré}} & ",
                  r" & \multicolumn{2}{c}{\makecell{Strict\\{}count}} & \multicolumn{2}{c}{\makecell{Preregistered\\{}count}} & "),
                r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
                L(lang, r"Analyse & 95~\% & Bonf. & 95~\% & Bonf. & Paires qui s'inversent, tranchées à 95~\% (en gras : aussi avec Bonferroni)",
                  r"Analysis & 95\% & Bonf. & 95\% & Bonf. & Pairs that reverse, settled at 95\% (in bold: also with Bonferroni)")]
        rows = []
        for k, fr, en in (("", "10 graines", "10 seeds"), ("_s20", "20 graines", "20 seeds"),
                          ("_equal", "Budget égal, 10 graines", "Equal budget, 10 seeds"),
                          ("_equal_s20", "Budget égal, 20 graines", "Equal budget, 20 seeds")):
            d = F[k]
            rows.append(" & ".join([L(lang, fr, en), str(d["ci95"]["n_reversing_pairs"]), str(d["bonferroni"]["n_reversing_pairs"]),
                                    str(d["ci95"]["n_settled_changes_preregistered"]), str(d["bonferroni"]["n_settled_changes_preregistered"]),
                                    pairs(d["ci95"], d["bonferroni"])]))
        cap = L(lang,
                r"Expérience E2, changements de classement tranchés comptés de deux façons. Décompte préregistré (écart 7 de \file{sim/SIM_PROTOCOL.md}) : chaque triplet (tâche où $X$ mène par IQM, autre tâche, programme $Y$ qui y bat $X$ de façon tranchée), sans demander si $X$ bat $Y$ sur la première tâche. "
                r"Décompte strict (écart 21, défaut corrigé, écrit avant ce calcul) : une paire $(A, B)$ s'inverse si $A$ bat $B$ de façon tranchée sur une tâche et $B$ bat $A$ de façon tranchée sur une autre, chaque fois avec un intervalle de probabilité d'amélioration qui exclut 0,5. "
                r"95~\% : intervalles de chaque comparaison seule ; Bonf. : les 24 intervalles rendus simultanés (écart 18, niveau $1 - 0{,}05/24$). Entre parenthèses, les tâches où chaque programme bat l'autre ; une ligne par paire. "
                r"Le script relit les intervalles déjà publiés et ne tire aucun nouveau rééchantillon. Sources : \file{sim/analysis/e2_strict.json}, \file{e2_strict_s20.json}, \file{e2_strict_equal.json}, \file{e2_strict_equal_s20.json} (\file{sim/analysis/e2_strict.py}).",
                r"Experiment E2, settled changes of ranking counted two ways. Preregistered count (deviation 7 of \file{sim/SIM_PROTOCOL.md}): every triple (task where $X$ leads by IQM, another task, program $Y$ that beats $X$ there, settled), without asking whether $X$ beats $Y$ on the first task. "
                r"Strict count (deviation 21, defect fixed, written before this computation): a pair $(A, B)$ reverses if $A$ beats $B$, settled, on one task and $B$ beats $A$, settled, on another, each time with a probability-of-improvement interval that excludes 0.5. "
                r"95\%: the interval of each comparison alone; Bonf.: the 24 intervals made simultaneous (deviation 18, level $1 - 0.05/24$). In parentheses, the tasks where each program beats the other; one line per pair. "
                r"The script rereads the intervals already published and draws no new resample. Sources: \file{sim/analysis/e2_strict.json}, \file{e2_strict_s20.json}, \file{e2_strict_equal.json}, \file{e2_strict_equal_s20.json} (\file{sim/analysis/e2_strict.py}).")
        floattable("e2-strict", lang, cap, L(lang, "E2 : décompte strict des changements de classement", "E2: strict count of ranking changes"),
                   r"@{}lrrrr>{\raggedright\arraybackslash}p{6cm}@{}", head, rows, tabcolsep="3.5pt")


def t_e1_grille():
    g = J("sim/analysis/e1_grid.json")
    sm = g["summary"]
    for lang in LANGS:
        head = [L(lang, r"Tâche & Programme & $n$ & \makecell[r]{Coef. de\\{}variation} & Asymétrie & \makecell[r]{5 contre 5\\{}au hasard (\%)} & \makecell[r]{5 meilleurs contre\\{}5 pires (\%)}",
                  r"Task & Program & $n$ & \makecell[r]{Coef. of\\{}variation} & Skewness & \makecell[r]{5 against 5\\{}at random (\%)} & \makecell[r]{5 best against\\{}5 worst (\%)}")]
        rows = []
        for t in TASKS:
            for i, a in enumerate(ALGS):
                c = g["cells"][f"{a}/{t}"]
                lo = c["sorted_5v5"] == sm["sorted_min"]
                rows.append(" & ".join([T(t) if i == 0 else "", ALG[a], str(c["n"]), pct(c["cv"], lang), num(c["skew"], lang, 2),
                                        pc(c["random_5v5"], lang, 1), bold(pc(c["sorted_5v5"], lang, 1), lo)]))
            rows.append("MID")
        p = g["e1_preregistered_30_runs"]
        rows.append(" & ".join([L(lang, r"\multicolumn{2}{@{}l}{E1 préenregistré (PPO PyTorch, HalfCheetah)}", r"\multicolumn{2}{@{}l}{E1 preregistered (PPO PyTorch, HalfCheetah)}"),
                                str(p["n"]), pct(p["cv"], lang), num(p["skew"], lang, 2), pc(p["random_5v5"], lang, 1), pc(p["sorted_5v5"], lang, 1)]))
        rows.append(" & ".join([L(lang, r"\multicolumn{5}{@{}l}{Médiane (étendue) sur les 16 couples}", r"\multicolumn{5}{@{}l}{Median (range) over the 16 pairs}"),
                                f"{pc(sm['random_median'], lang, 1)} ({pc(sm['random_min'], lang, 1)}{to(lang)}{pc(sm['random_max'], lang, 1)})",
                                f"{pc(sm['sorted_median'], lang, 1)} ({pc(sm['sorted_min'], lang, 1)}{to(lang)}{pc(sm['sorted_max'], lang, 1)})"]))
        cap = L(lang,
                r"Expérience E1 refaite sur les seize couples (programme, tâche) de E2, graines 0 à 19 (écart 22 de \file{sim/SIM_PROTOCOL.md}, analyse exploratoire décidée après les résultats, écrite avant ce calcul). "
                r"Pour chaque couple, 10\,000 tirages de deux groupes disjoints de 5 essais au hasard, puis 10\,000 tirages de 10 essais coupés en 5 meilleurs contre 5 pires ; part des tirages où le test de Welch donne $p < 0{,}05$ alors que les deux groupes exécutent le même programme (générateur \texttt{default\_rng(2018)}). "
                r"Le coefficient de variation et l'asymétrie décrivent les vingt scores finaux. \textbf{En gras}, le taux trié le plus bas : celui du couple préenregistré, PPO PyTorch sur HalfCheetah. "
                r"Les intervalles par rééchantillonnage des populations que donne le fichier ne sont pas reportés : tirer avec remise crée des essais en double, ce qui les élargit et biaise vers le haut le taux trié. "
                r"Sources : \file{sim/analysis/e1_grid.json} (\file{sim/analysis/e1_grid.py}) ; le résultat préenregistré reste celui de \file{sim/analysis/e1.json} (tableau~\ref{tab:e1}).",
                r"Experiment E1 redone on the sixteen (program, task) pairs of E2, seeds 0 to 19 (deviation 22 of \file{sim/SIM_PROTOCOL.md}, exploratory analysis decided after the results, written before this computation). "
                r"For each pair, 10,000 draws of two disjoint groups of 5 runs at random, then 10,000 draws of 10 runs cut into the 5 best against the 5 worst; share of draws where Welch's test gives $p < 0.05$ although both groups run the same program (generator \texttt{default\_rng(2018)}). "
                r"Coefficient of variation and skewness describe the twenty final scores. \textbf{In bold}, the lowest sorted rate: that of the preregistered pair, PPO PyTorch on HalfCheetah. "
                r"The population-resampling intervals in the file are not reported: drawing with replacement creates duplicate runs, which widens them and biases the sorted rate upward. "
                r"Sources: \file{sim/analysis/e1_grid.json} (\file{sim/analysis/e1_grid.py}); the preregistered result remains that of \file{sim/analysis/e1.json} (Table~\ref{tab:e1}).")
        floattable("e1-grille", lang, cap, L(lang, "E1 sur les seize couples", "E1 on the sixteen pairs"),
                   r"@{}llrrrrr@{}", head, rows, tabcolsep="3.5pt")


def t_e3_holm():
    e = J("sim/analysis/e3_holm.json")
    for lang in LANGS:
        head = [L(lang, r"Tâche & \makecell[r]{IQM\\{}PyTorch} & \makecell[r]{IQM\\{}JAX} & \makecell[r]{$P(\text{JAX} > \text{PyTorch})$\\{}[IC 98,75~\%]} & \makecell[r]{Écart JAX $-$ PyTorch\\{}(Hodges-Lehmann) [IC 95~\%]} & \makecell[r]{$p$ Mann-\\{}Whitney} & $p$ Holm",
                  r"Task & \makecell[r]{IQM\\{}PyTorch} & \makecell[r]{IQM\\{}JAX} & \makecell[r]{$P(\text{JAX} > \text{PyTorch})$\\{}[98.75\% CI]} & \makecell[r]{Gap JAX $-$ PyTorch\\{}(Hodges-Lehmann) [95\% CI]} & \makecell[r]{Mann-\\{}Whitney $p$} & Holm $p$")]
        rows = []
        for s, fr, en in (("s10", "10 graines (0 à 9)", "10 seeds (0 to 9)"), ("s20", "20 graines (0 à 19)", "20 seeds (0 to 19)")):
            rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\emph{{{L(lang, fr, en)}}}}}")
            for t in TASKS:
                r = e[s][t]
                hl = r["hodges_lehmann_ci"]
                cells = [r"\quad " + T(t), num(r["iqm"]["sb3"], lang), num(r["iqm"]["sbx"], lang),
                         pr_cell(r["p_improve_sbx"], r["p_improve_ci_bonferroni"], lang),
                         f"{num(r['hodges_lehmann_sbx_minus_sb3'], lang, sign=True)} {iv(num(hl[0], lang, sign=True), num(hl[1], lang, sign=True), lang)}",
                         pval(r["mw_p"], lang), pval(r["mw_p_holm"], lang)]
                rows.append(" & ".join(bold(c, r["settled_holm"]) for c in cells))
        cap = L(lang,
                r"Expérience E3 corrigée pour ses quatre tâches (écart 23 de \file{sim/SIM_PROTOCOL.md}, écrit avant ce calcul). Test de Mann-Whitney bilatéral par tâche puis correction de Holm sur les quatre tâches ; "
                r"probabilité d'amélioration avec son intervalle au niveau simultané $1 - 0{,}05/4$ (rliable, 2\,000 rééchantillons) ; écart en points de score par l'estimateur de Hodges-Lehmann (médiane des différences deux à deux), intervalle percentile à 95~\% (5\,000 rééchantillons, \texttt{default\_rng(2026)}). "
                r"Règle : une différence entre les deux PPO n'est dite tranchée que si elle passe Holm ; \textbf{en gras}, la seule qui passe, Swimmer à 20 graines. "
                r"Puissance de ces tests au tableau~\ref{tab:e3-puissance}. "
                r"Le résultat préenregistré reste celui de \file{sim/analysis/e3.json} (tableau~\ref{tab:e3}). Source : \file{sim/analysis/e3_holm.json} (\file{sim/analysis/e3_holm.py}).",
                r"Experiment E3 corrected for its four tasks (deviation 23 of \file{sim/SIM_PROTOCOL.md}, written before this computation). Two-sided Mann-Whitney test per task, then Holm's correction over the four tasks; "
                r"probability of improvement with its interval at the simultaneous level $1 - 0.05/4$ (rliable, 2,000 resamples); gap in score points by the Hodges-Lehmann estimator (median of pairwise differences), 95\% percentile interval (5,000 resamples, \texttt{default\_rng(2026)}). "
                r"Rule: a difference between the two PPOs is called settled only if it passes Holm; \textbf{in bold}, the only one that does, Swimmer at twenty seeds. "
                r"Power of these tests in Table~\ref{tab:e3-puissance}. "
                r"The preregistered result remains that of \file{sim/analysis/e3.json} (Table~\ref{tab:e3}). Source: \file{sim/analysis/e3_holm.json} (\file{sim/analysis/e3_holm.py}).")
        floattable("e3-holm", lang, cap, L(lang, "E3 avec la correction de Holm, et sa puissance", "E3 with Holm's correction, and its power"),
                   r"@{}lrrrrrr@{}", head, rows, tabcolsep="3.5pt")


def t_e3_puissance():
    e = J("sim/analysis/e3_holm.json")
    NS = (10, 20, 30, 40, 60)
    md = e["min_detectable_p_improve_80pct_alpha_0_0125"]
    for lang in LANGS:
        head = [L(lang, r" & \multicolumn{5}{c}{Essais par programme} \\ \cmidrule(lr){2-6}", r" & \multicolumn{5}{c}{Runs per program} \\ \cmidrule(lr){2-6}")
                + "\n" + L(lang, "Tâche", "Task") + " & " + " & ".join(f"$n = {n}$" for n in NS)]
        rows = []
        for t in TASKS:
            pw = e["power"][t]
            rows.append(" & ".join([T(t)] + [f"{pc(pw[str(n)]['alpha_0_0125'], lang)} ({pc(pw[str(n)]['alpha_0_05'], lang)})" for n in NS]))
        rows.append("MID")
        rows.append(" & ".join([L(lang, r"\makecell[l]{$P(\text{JAX} > \text{PyTorch})$ détectable\\{}à 80~\% de puissance}", r"\makecell[l]{$P(\text{JAX} > \text{PyTorch})$ detectable\\{}with 80\% power}")]
                               + [num(md[str(n)], lang, 2) if str(n) in md else "" for n in NS]))
        cap = L(lang,
                r"Expérience E3, puissance du test de Mann-Whitney au niveau corrigé $0{,}05/4$ (entre parenthèses, au niveau $0{,}05$), en pourcentage : part des 2\,000 tirages où le test rejette, chaque tirage prenant avec remise $n$ essais par programme parmi les vingt observés, si bien que la différence vraie est celle des vingt graines (écart 23 de \file{sim/SIM_PROTOCOL.md}, écrit avant ce calcul). "
                r"Dernière ligne : plus petite probabilité d'amélioration détectable avec 80~\% de puissance au niveau $0{,}05/4$ (approximation normale de la statistique $U$). Sur Walker2d, il faudrait environ soixante graines par programme pour voir à coup presque sûr l'écart observé à vingt. "
                r"Source : \file{sim/analysis/e3_holm.json} (\file{sim/analysis/e3_holm.py}).",
                r"Experiment E3, power of the Mann-Whitney test at the corrected level $0.05/4$ (in parentheses, at the $0.05$ level), in percent: share of 2,000 draws where the test rejects, each draw taking $n$ runs per program with replacement from the twenty observed, so that the true difference is that of the twenty seeds (deviation 23 of \file{sim/SIM_PROTOCOL.md}, written before this computation). "
                r"Last row: smallest probability of improvement detectable with 80\% power at level $0.05/4$ (normal approximation of the $U$ statistic). On Walker2d, about sixty seeds per program would be needed to see the gap observed at twenty almost surely. "
                r"Source: \file{sim/analysis/e3_holm.json} (\file{sim/analysis/e3_holm.py}).")
        floattable("e3-puissance", lang, cap, L(lang, "E3 : puissance du test", "E3: power of the test"),
                   r"@{}lrrrrr@{}", head, rows, tabcolsep="5pt")


def t_e7_test():
    E = {"": J("sim/analysis/e7_test.json")["tasks"], "_s20": J("sim/analysis/e7_test_s20.json")["tasks"]}
    for lang in LANGS:
        head = [L(lang, r" & \multicolumn{2}{c}{10 graines (0 à 9)} & \multicolumn{2}{c}{20 graines (0 à 19)}",
                  r" & \multicolumn{2}{c}{10 seeds (0 to 9)} & \multicolumn{2}{c}{20 seeds (0 to 19)}"),
                r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
                L(lang, r"Paire $A > B$ & \makecell[r]{physique\\{}d'entraînement} & \makecell[r]{physique\\{}modifiée} & \makecell[r]{physique\\{}d'entraînement} & \makecell[r]{physique\\{}modifiée}",
                  r"Pair $A > B$ & \makecell[r]{training\\{}physics} & \makecell[r]{modified\\{}physics} & \makecell[r]{training\\{}physics} & \makecell[r]{modified\\{}physics}")]
        hq = L(lang, r", question principale fixée d’avance : $P(A > B)$ [IC 95~\%]", r", main question fixed in advance: $P(A > B)$ [95\% CI]")
        rows = [rf"\multicolumn{{5}}{{@{{}}l}}{{\emph{{Hopper{hq}}}}}"]
        for key in E[""]["Hopper-v5"]["training"]["pairs"]:
            cells = [r"\quad " + pair_label(key)]
            for sfx in ("", "_s20"):
                h = E[sfx]["Hopper-v5"]
                tr, mo = h["training"]["pairs"][key], h["modified"]["pairs"][key]
                sm = lambda d: rf"{num(d['p'], lang, 2)} {{\scriptsize {ci2(d['ci'], lang)}}}"  # noqa: E731
                cells += [bold(sm(tr), tr["settled"]), bold(sm(mo), mo["settled"]) + (r"$^\dagger$" if key in h["settled_reversals"] else r"$^{\phantom{\dagger}}$")]
            rows.append(" & ".join(cells))
        lead = [L(lang, r"\quad Chef (IQM)", r"\quad Leader (IQM)")]
        for sfx in ("", "_s20"):
            h = E[sfx]["Hopper-v5"]
            lead += [f"{ALG[h[ph]['leader']]}, {num(h[ph]['iqm'][h[ph]['leader']], lang)}" for ph in ("training", "modified")]
        rows.append(" & ".join(lead))
        rows.append("MID")
        rows.append(rf"\multicolumn{{5}}{{@{{}}l}}{{\emph{{{L(lang, 'Renversements tranchés, toutes tâches', 'Settled reversals, all tasks')}}}}}")
        for t in TASKS:
            cells = [r"\quad " + T(t)]
            for sfx in ("", "_s20"):
                sr = E[sfx][t]["settled_reversals"]
                cells.append(rf"\multicolumn{{2}}{{c}}{{{len(sr)}}}")
            rows.append(" & ".join(cells))
        def revs(sfx):
            return L(lang, " ; ", "; ").join(f"{T(t)}{L(lang, ' : ', ': ')}{', '.join(pair_label(k) for k in E[sfx][t]['settled_reversals'])}"
                                             for t in TASKS if E[sfx][t]["settled_reversals"])
        rv = L(lang, f"Renversements tranchés à 10 graines : {revs('')} ; à 20 graines : {revs('_s20')}. ",
               f"Settled reversals at ten seeds: {revs('')}; at twenty seeds: {revs('_s20')}. ")
        cap = L(lang,
                r"Expérience E7, le renversement de classement en physique modifiée (masses $\times$ 1,2, frottement $\times$ 0,8), testé (écart 24 de \file{sim/SIM_PROTOCOL.md}, écrit avant ce calcul ; le complément de l'écart 11 classait sans test). "
                r"Pour chaque paire, la probabilité qu'un essai de $A$ batte un essai de $B$, avec son intervalle à 95~\% (rliable, 2\,000 rééchantillons, générateur global à 2026), sur le score final dans la physique d'entraînement puis dans la physique modifiée ; à 10 graines (résultat de l'écart) et à 20 graines. "
                r"\textbf{En gras}, les comparaisons tranchées (intervalle qui exclut 0,5). $^\dagger$ : une paire qui se renverse de façon tranchée, c'est-à-dire tranchée dans un sens dans la physique d'entraînement et dans l'autre sens dans la physique modifiée. "
                r"Les $p$ de Mann-Whitney et les mêmes comparaisons à chaque intensité de la dose sont dans les fichiers. " + rv + r"Sources : \file{sim/analysis/e7_test.json}, \file{sim/analysis/e7_test_s20.json} (\file{sim/analysis/e7_test.py}).",
                r"Experiment E7, the change of ranking under modified physics (masses $\times$ 1.2, friction $\times$ 0.8), tested (deviation 24 of \file{sim/SIM_PROTOCOL.md}, written before this computation; the complement of deviation 11 ranked without a test). "
                r"For each pair, the probability that a run of $A$ beats a run of $B$, with its 95\% interval (rliable, 2,000 resamples, global generator seeded with 2026), on the final score in the training physics and then in the modified physics; at ten seeds (the deviation's result) and at twenty. "
                r"\textbf{In bold}, settled comparisons (interval that excludes 0.5). $^\dagger$: a pair that reverses, settled, that is, settled one way in the training physics and the other way in the modified physics. "
                r"The Mann-Whitney $p$ values and the same comparisons at each strength of the dose are in the files. " + rv + r"Sources: \file{sim/analysis/e7_test.json}, \file{sim/analysis/e7_test_s20.json} (\file{sim/analysis/e7_test.py}).")
        floattable("e7-test", lang, cap, L(lang, "E7 : le renversement sur Hopper, testé", "E7: the Hopper reversal, tested"),
                   r"@{}lrrrr@{}", head, rows, tabcolsep="4pt")


def t_e5_holdout():
    h = J("sim/analysis/e5_holdout.json")
    pre = h["e5_preregistered"]
    A, B = "p_n_from_0_9_judged_on_10_19", "p_n_from_10_19_judged_on_0_9"
    NS = ("3", "5", "10")
    for lang in LANGS:
        head = [L(lang, r"Mesure (part des tirages qui retrouvent l'ordre, \%) & $n = 3$ & $n = 5$ & $n = 10$",
                  r"Measure (share of draws that recover the order, \%) & $n = 3$ & $n = 5$ & $n = 10$")]
        rows = [rf"\multicolumn{{4}}{{@{{}}l}}{{\emph{{{L(lang, 'E5 préenregistré, ordre jugé sur le même échantillon', 'E5 preregistered, order judged on the same sample')}}}}}"]
        rows.append(L(lang, r"\quad Médiane, 24 comparaisons", r"\quad Median, 24 comparisons") + " & " + " & ".join(pc(pre["median_all"][n], lang) for n in NS))
        rows.append(L(lang, rf"\quad Médiane, {pre['n_close']} comparaisons serrées", rf"\quad Median, {pre['n_close']} close comparisons") + " & " + " & ".join(pc(pre["median_close"][n], lang) for n in NS))
        for key, fr, en in ((A, "Tirés dans les graines 0 à 9, jugés sur les graines 10 à 19", "Drawn from seeds 0 to 9, judged on seeds 10 to 19"),
                            (B, "Tirés dans les graines 10 à 19, jugés sur les graines 0 à 9", "Drawn from seeds 10 to 19, judged on seeds 0 to 9")):
            rows.append(rf"\multicolumn{{4}}{{@{{}}l}}{{\emph{{{L(lang, fr, en)}}}}}")
            rows.append(L(lang, r"\quad Médiane, 24 comparaisons", r"\quad Median, 24 comparisons") + " & " + " & ".join(pc(h["median_all"][key][n], lang) for n in NS))
            rows.append(L(lang, rf"\quad Médiane, {h['n_close']} comparaisons serrées", rf"\quad Median, {h['n_close']} close comparisons") + " & " + " & ".join(pc(h["median_close"][key][n], lang) for n in NS))
            rows.append(bold(L(lang, rf"\quad Moyenne, {h['n_close']} comparaisons serrées", rf"\quad Mean, {h['n_close']} close comparisons")) + " & " + " & ".join(bold(pc(h["mean_close"][key][n], lang)) for n in NS))
        fl = L(lang, " ; ", "; ").join(f"{T(x.split()[0])}{L(lang, ' : ', ': ')}{ALG[x.split()[1]]} / {ALG[x.split()[3]]}" for x in h["flipped"])
        signs = L(lang, f"Signe de l'écart des graines 0 à 9 retrouvé sur les graines 10 à 19 : {h['signs_kept']} comparaisons sur {h['n']}, {h['signs_kept_close']} serrées sur {h['n_close']} ; signes qui changent : {fl}. ",
                  f"Sign of the gap on seeds 0 to 9 found again on seeds 10 to 19: {h['signs_kept']} comparisons out of {h['n']}, {h['signs_kept_close']} close ones out of {h['n_close']}; signs that change: {fl}. ")
        cap = L(lang,
                r"Expérience E5 vérifiée hors échantillon (écart 25 de \file{sim/SIM_PROTOCOL.md}, écrit avant ce calcul). E5 prend pour bon ordre le signe des moyennes de l'échantillon même où il tire avec remise : sa part mesure la stabilité du signe observé, pas la probabilité de retrouver le vrai ordre. "
                + signs + r"Ici, $n$ essais par programme tirés sans remise dans une moitié des graines (10\,000 tirages, \texttt{default\_rng(2026)}), comptés justes quand ils retrouvent l'ordre des moyennes de l'autre moitié, dans les deux sens. Comparaison serrée : écart relatif sous 20~\% sur les graines 0 à 9. "
                r"À $n = 10$, le tirage prend toute la moitié, d'où 100 ou 0~\% par comparaison : la moyenne des serrées donne alors la part des signes retrouvés. \textbf{En gras}, la moyenne des comparaisons serrées, la mesure sans circularité. "
                r"Sources : \file{sim/analysis/e5_holdout.json} (\file{sim/analysis/e5_holdout.py}), \file{sim/analysis/e5.json} (tableau~\ref{tab:e5}).",
                r"Experiment E5 checked out of sample (deviation 25 of \file{sim/SIM_PROTOCOL.md}, written before this computation). E5 takes as the right order the sign of the means of the very sample it draws from with replacement: its share measures the stability of the observed sign, not the probability of recovering the true order. "
                + signs + r"Here, $n$ runs per program drawn without replacement from one half of the seeds (10,000 draws, \texttt{default\_rng(2026)}), counted right when they recover the order of the means of the other half, both ways. Close comparison: relative gap under 20\% on seeds 0 to 9. "
                r"At $n = 10$ the draw takes the whole half, hence 100 or 0\% per comparison: the mean over close comparisons then gives the share of signs recovered. \textbf{In bold}, the mean over close comparisons, the measure without circularity. "
                r"Sources: \file{sim/analysis/e5_holdout.json} (\file{sim/analysis/e5_holdout.py}), \file{sim/analysis/e5.json} (Table~\ref{tab:e5}).")
        floattable("e5-hors-echantillon", lang, cap, L(lang, "E5 hors échantillon", "E5 out of sample"),
                   r"@{}>{\raggedright\arraybackslash}p{6cm}rrr@{}", head, rows, tabcolsep="4pt")


def t_regle_tranche():
    r = J("sim/analysis/rule_calibration.json")
    for lang in LANGS:
        head = [L(lang, r"Groupes du même programme & \makecell[r]{IC de $P$\\{}exclut 0,5} & \makecell[r]{IC des IQM\\{}disjoints} & \makecell[r]{L'un ou l'autre\\{}(la règle)} & ",
                  r"Groups of the same program & \makecell[r]{CI of $P$\\{}excludes 0.5} & \makecell[r]{IQM CIs\\{}disjoint} & \makecell[r]{Either\\{}(the rule)} & ")]
        t30 = L(lang, r"Les 30 essais de HalfCheetah (E1 et B1), 2\,000 tirages", "The 30 runs on HalfCheetah (E1 and B1), 2,000 draws")
        tgrid = L(lang, r"La règle à 5 contre 5 sur les seize couples de E2 (graines 0 à 19), 2\,000 tirages", "The rule at 5 against 5 on the sixteen pairs of E2 (seeds 0 to 19), 2,000 draws")
        rows = [rf"\multicolumn{{5}}{{@{{}}l}}{{\emph{{{t30}}}}}"]
        for a, an in (("ppo_sb3", "PPO PyTorch"), ("trpo", "TRPO")):
            for k, fr, en in (("10v10", "10 contre 10", "10 against 10"), ("5v5", "5 contre 5", "5 against 5")):
                c = r["halfcheetah_30_runs"][a][k]
                rows.append(" & ".join([rf"\quad {an}, {L(lang, fr, en)}", pct(c["poi_excludes_half"], lang, 1), pct(c["iqm_disjoint"], lang, 1),
                                        bold(pct(c["either"], lang, 1)), ""]))
        rows.append("MID")
        rows.append(rf"\multicolumn{{5}}{{@{{}}l}}{{\emph{{{tgrid}}}}}")
        rows.append(L(lang, "Programme", "Program") + " & " + " & ".join(T(t) for t in TASKS))
        rows.append(r"\cmidrule(lr){1-5}")
        for a in ALGS:
            rows.append(" & ".join([r"\quad " + ALG[a]] + [pct(r["grid_5v5"][f"{a}/{t}"]["either"], lang, 1) for t in TASKS]))
        s = r["grid_5v5_summary"]
        rows.append(L(lang, r"\multicolumn{5}{@{}l}{Médiane ", r"\multicolumn{5}{@{}l}{Median ") + f"{pct(s['median'], lang, 1)} ({pct(s['min'], lang, 1)}{to(lang)}{pct(s['max'], lang, 1)})" + "}")
        cap = L(lang,
                r"La règle « tranché » mise à l'épreuve sur de vraies hypothèses nulles (écart 26 de \file{sim/SIM_PROTOCOL.md}, écrit avant ce calcul) : deux groupes disjoints du même programme, où aucune différence n'existe. "
                r"Sur chaque tirage, intervalle bootstrap percentile de la probabilité d'amélioration et intervalles des deux IQM (2\,000 rééchantillons, chaque groupe rééchantillonné à part, méthode de rliable réécrite en NumPy, \texttt{default\_rng(2026)}). "
                r"Colonnes : part des tirages où l'intervalle de la probabilité d'amélioration exclut 0,5, où les intervalles des IQM sont disjoints, où l'un ou l'autre se produit (la règle du protocole, \textbf{en gras}). "
                r"Une règle exacte au niveau de 95~\% se tromperait dans 5~\% des tirages : la règle est un peu libérale à 10 contre 10, nettement à 5 contre 5, et c'est la condition sur la probabilité d'amélioration qui la porte. "
                r"Source : \file{sim/analysis/rule_calibration.json} (\file{sim/analysis/rule_calibration.py}).",
                r"The ``settled'' rule tested on true null hypotheses (deviation 26 of \file{sim/SIM_PROTOCOL.md}, written before this computation): two disjoint groups of the same program, where no difference exists. "
                r"In each draw, the percentile bootstrap interval of the probability of improvement and the intervals of the two IQMs (2,000 resamples, each group resampled separately, rliable's method rewritten in NumPy, \texttt{default\_rng(2026)}). "
                r"Columns: share of draws where the probability-of-improvement interval excludes 0.5, where the IQM intervals are disjoint, where either holds (the protocol's rule, \textbf{in bold}). "
                r"An exact rule at the 95\% level would err in 5\% of the draws: the rule is slightly liberal at 10 against 10, clearly so at 5 against 5, and the probability-of-improvement condition carries it. "
                r"Source: \file{sim/analysis/rule_calibration.json} (\file{sim/analysis/rule_calibration.py}).")
        floattable("regle-tranche", lang, cap, L(lang, "La règle « tranché » sur des hypothèses nulles", "The settled rule on null hypotheses"),
                   r"@{}lrrrr@{}", head, rows, tabcolsep="5pt")


def sci(x):
    """A learning rate as siunitx writes it: 3e-4."""
    m, e = f"{x:.0e}".split("e")
    return rf"\num{{{m}e{int(e)}}}"


def t_hyperparametres():
    H = J("sim/analysis/hyperparams.json")["programs"]
    P = ["ppo_sb3", "ppo_sbx", "sac", "crossq", "trpo"]
    for lang in LANGS:
        yes, no, auto = L(lang, "oui", "yes"), L(lang, "non", "no"), L(lang, "automatique", "automatic")

        def dec(x):
            return num(x, lang, len(repr(float(x)).split(".")[1].rstrip("0")))

        def arch(l, act):
            return ", ".join(str(v) for v in l) + ", " + {"tanh": "tanh", "Tanh": "tanh", "relu": "ReLU"}[act]

        def clip(v):
            return dec(float(re.search(r"val=([\d.]+)", v).group(1)) if isinstance(v, str) else v)
        R = []

        def row(fr, en, f):
            R.append((L(lang, fr, en), [f(p, H[p]) for p in P]))
        on = lambda *ks: lambda f: (lambda p, h: f(p, h) if p in ks else "")  # noqa: E731
        ppo, off = ("ppo_sb3", "ppo_sbx"), ("sac", "crossq")
        row("Taux d'apprentissage", "Learning rate",
            lambda p, h: sci(h["learning_rate"]) + (L(lang, " (critique)", " (critic)") if p == "trpo" else ""))
        row(r"Facteur d'actualisation $\gamma$", r"Discount factor $\gamma$", lambda p, h: dec(h["gamma"]))
        row("Pas collectés par mise à jour", "Steps collected per update",
            lambda p, h: num(h["n_steps"], lang) if p not in off else str(h["train_freq"][0]))
        row("Taille des lots", "Batch size", lambda p, h: str(h["batch_size"]))
        row("Passes sur chaque paquet", "Epochs over each rollout", on(*ppo)(lambda p, h: str(h["n_epochs"])))
        row(r"Paramètre $\lambda$ de GAE", r"GAE parameter $\lambda$", on(*ppo, "trpo")(lambda p, h: dec(h["gae_lambda"])))
        row(r"Troncature $\epsilon$", r"Clipping $\epsilon$", on(*ppo)(lambda p, h: clip(h["clip_range"])))
        row("Avantages normalisés", "Normalised advantages", on(*ppo, "trpo")(lambda p, h: yes if h["normalize_advantage"] else no))
        row("Coefficient de la perte de valeur", "Value-loss coefficient", on(*ppo)(lambda p, h: dec(h["vf_coef"])))
        row("Norme maximale du gradient", "Maximum gradient norm", on(*ppo)(lambda p, h: dec(h["max_grad_norm"])))
        row(r"Contrainte de divergence $\delta$", r"Divergence constraint $\delta$", on("trpo")(lambda p, h: dec(h["target_kl"])))
        row("Gradient conjugué : pas, amortissement", "Conjugate gradient: steps, damping",
            on("trpo")(lambda p, h: f"{h['cg_max_steps']}{L(lang, ' ; ', '; ')}{dec(h['cg_damping'])}"))
        row("Recherche linéaire : facteur, essais", "Line search: factor, tries",
            on("trpo")(lambda p, h: f"{dec(h['line_search_shrinking_factor'])}{L(lang, ' ; ', '; ')}{h['line_search_max_iter']}"))
        row("Mises à jour du critique par itération", "Critic updates per iteration", on("trpo")(lambda p, h: str(h["n_critic_updates"])))
        row("Coefficient d'entropie", "Entropy coefficient",
            lambda p, h: (dec(h["ent_coef"]) if p in ppo else auto if h.get("ent_coef_init") == "auto" else ""))
        row("Entropie cible", "Target entropy", on(*off)(lambda p, h: num(h["target_entropy"], lang)))
        row("Mémoire de rejeu", "Replay buffer", on(*off)(lambda p, h: num(h["buffer_size"], lang)))
        row("Pas avant d'apprendre", "Steps before learning", on(*off)(lambda p, h: str(h["learning_starts"])))
        row("Pas de gradient par pas", "Gradient steps per step", on(*off)(lambda p, h: str(h["gradient_steps"])))
        row(r"Mise à jour des réseaux cibles $\tau$", r"Target network update $\tau$",
            on(*off)(lambda p, h: dec(h["tau"]) if p == "sac" else L(lang, "sans réseau cible", "no target network")))
        row("Mises à jour du critique par mise à jour de l'acteur", "Critic updates per actor update",
            on(*off)(lambda p, h: str(h["policy_delay"])))
        row("Réseau de la politique", "Policy network",
            lambda p, h: arch(h["policy"]["net_arch"]["pi"], h["policy"]["activation_fn"]) if p in ("ppo_sb3", "trpo")
            else arch(h["policy"]["actor"]["net_arch"], h["policy"]["activation_fn"]))
        row("Réseau de valeur ou critique", "Value or critic network",
            lambda p, h: arch(h["policy"]["net_arch"]["vf"], h["policy"]["activation_fn"]) if p in ("ppo_sb3", "trpo")
            else arch(h["policy"]["actor"]["net_arch"], h["policy"]["activation_fn"]) if p == "ppo_sbx"
            else f"{h['policy']['n_critics']} {L(lang, 'fois', 'times')} " + arch(h["policy"]["qf"]["net_arch"], h["policy"]["activation_fn"]))
        row("Renormalisation par lots : élan, préchauffage", "Batch renormalisation: momentum, warm-up",
            on("crossq")(lambda p, h: f"{dec(h['policy']['batch_norm_momentum'])}{L(lang, ' ; ', '; ')}{num(h['policy']['renorm_warmup_steps'], lang)}"
                         + L(lang, ", acteur et critique", ", actor and critic") * bool(h["policy"]["batch_norm_actor"] and h["policy"]["qf"]["use_batch_norm"])))
        row("Initialisation orthogonale", "Orthogonal initialisation",
            on(*ppo, "trpo")(lambda p, h: yes if h["policy"]["ortho_init"] else no))
        row(r"$\log \sigma$ initial", r"Initial $\log \sigma$", on(*ppo, "trpo")(lambda p, h: dec(h["policy"]["log_std_init"])))

        def opt(p, h):
            if "optimizer" in h:  # PyTorch: read from the optimiser itself
                o = h["optimizer"]
                bs = L(lang, r"\,;\,", r",\,")
                return rf"Adam, $\beta = ({dec(o['betas'][0])}{bs}{dec(o['betas'][1])})$, $\varepsilon = $ \num{{{o['eps']:.0e}}}"
            kw = h["policy"]["optimizer_kwargs"]
            s = L(lang, "Adam d'optax", "optax Adam")
            if "b1" in kw:
                s += rf", $\beta_1 = {dec(kw['b1'])}$"
            if "eps" in kw:
                s += rf", $\varepsilon = $ \num{{{kw['eps']:.0e}}}"
            return s if kw else s + L(lang, ", par défaut", ", defaults")
        row("Optimiseur", "Optimiser", opt)
        head = [L(lang, "Réglage", "Setting") + " & " + " & ".join(["PPO PyTorch", "PPO JAX", "SAC", "CrossQ", "TRPO"])]
        rows = [" & ".join([lab] + vals) for lab, vals in R]
        cap = L(lang,
                r"Les réglages des cinq programmes, tels qu'ils ont servi : \file{sim/analysis/hyperparams.py} (écart 28 de \file{sim/SIM_PROTOCOL.md}) construit chaque programme sur Hopper-v5 exactement comme \file{sim/run.py} (TRPO sur HalfCheetah-v5), lit les attributs de l'algorithme, de la politique et de l'optimiseur, puis les compare aux paramètres rangés dans un modèle sauvegardé par programme. "
                r"Ce sont les valeurs par défaut des bibliothèques installées (versions au tableau~\ref{tab:env}) : aucun programme n'a été réglé. Une case vide : le réglage n'existe pas pour cet algorithme, ou il est désactivé. "
                r"Les réseaux sont des perceptrons multicouches, dont on donne les largeurs des couches cachées et l'activation. CrossQ n'a pas de réseau cible : son $\tau$ existe dans la bibliothèque sans servir. "
                r"Les deux PPO ont les mêmes réglages d'algorithme, mais pas la même initialisation : dans SBX, l'option orthogonale ne toucherait que la couche de sortie de l'action, dans Stable-Baselines3 elle couvre aussi les couches cachées et la sortie de valeur (écart 34). "
                r"Source : \file{sim/analysis/hyperparams.json} (\texttt{make hyperparams}).",
                r"The settings of the five programs as they ran: \file{sim/analysis/hyperparams.py} (deviation 28 of \file{sim/SIM_PROTOCOL.md}) builds each program on Hopper-v5 exactly as \file{sim/run.py} does (TRPO on HalfCheetah-v5), reads the attributes of the algorithm, the policy and the optimiser, then compares them with the parameters stored in one saved model per program. "
                r"These are the default values of the installed libraries (versions in Table~\ref{tab:env}): no program was tuned. An empty cell: the setting does not exist for that algorithm, or it is switched off. "
                r"The networks are multilayer perceptrons, given by the widths of their hidden layers and their activation. CrossQ has no target network: its $\tau$ exists in the library but is not used. "
                r"The two PPOs share the same algorithm settings but not the same initialisation: in SBX the orthogonal option would touch only the action output layer, in Stable-Baselines3 it also covers the hidden layers and the value output (deviation 34). "
                r"Source: \file{sim/analysis/hyperparams.json} (\texttt{make hyperparams}).")
        floattable("hyperparametres", lang, cap, L(lang, "Réglages des cinq programmes", "Settings of the five programs"),
                   r"@{}>{\raggedright\arraybackslash}p{4cm}>{\raggedright\arraybackslash}p{1.95cm}>{\raggedright\arraybackslash}p{1.95cm}"
                   r">{\raggedright\arraybackslash}p{1.95cm}>{\raggedright\arraybackslash}p{2.05cm}>{\raggedright\arraybackslash}p{1.95cm}@{}",
                   head, rows, tabcolsep="3.5pt")


def t_e6_vitesse():
    en, hub, sp = J("sim/analysis/e6_enjoy.json"), J("sim/analysis/e6_hub.json"), J("sim/analysis/e6_speed.json")
    for lang in LANGS:
        head = [L(lang, r"Agents (Hopper-v4, notre protocole) & \makecell[r]{Retour\\{}médian} & \makecell[r]{Vitesse médiane\\{}(m/s)} & \makecell[r]{Vitesses extrêmes\\{}(m/s)} & \makecell[r]{Agents sans\\{}chute}",
                  r"Agents (Hopper-v4, our protocol) & \makecell[r]{Median\\{}return} & \makecell[r]{Median speed\\{}(m/s)} & \makecell[r]{Extreme speeds\\{}(m/s)} & \makecell[r]{Agents that\\{}never fall}")]
        rows = []
        lab = {"official": L(lang, "Script officiel du Zoo, 10 graines", "Official Zoo script, 10 seeds"),
               "zoofix": L(lang, "Zoo corrigé, notre code, 10 graines", "Zoo corrected, our code, 10 seeds"),
               "default": L(lang, "Valeurs par défaut, 10 graines", "Default values, 10 seeds")}
        for g in ("official", "zoofix", "default"):
            d = en["groups"][g]
            runs = d["runs"].values()
            assert d["all_controls_equal"]
            rows.append(" & ".join([lab[g], num(statistics.median(r["mean_return"] for r in runs), lang),
                                    num(d["median_speed"], lang, 2), f"{num(d['min_speed'], lang, 2)}{to(lang)}{num(d['max_speed'], lang, 2)}",
                                    f"{sum(r['share_full_length'] == 1 for r in runs)}/{len(d['runs'])}"]))
        rows.append(" & ".join([L(lang, r"\texttt{sb3/ppo-Hopper-v3} publié par le Zoo, 100 épisodes", r"\texttt{sb3/ppo-Hopper-v3} published by the Zoo, 100 episodes"),
                                f"{num(hub['score_100_episodes'], lang)} ± {num(hub['sd_100'], lang)}", num(hub["mean_x_velocity_100"], lang, 2), "",
                                L(lang, "1/1", "1/1") if hub["share_full_length_100"] == 1 else ""]))
        mc = hub["model_card_results"]
        s = sp["summary"]
        cap = L(lang,
                r"Expérience E6, ce que font les agents de la recette publiée (écarts 31 et 33 de \file{sim/SIM_PROTOCOL.md}, écrits avant ces calculs). Sur Hopper, la récompense d'un pas est la vitesse vers l'avant, plus 1 tant que le robot reste debout, moins un petit coût d'action : un retour d'environ 1\,000 sur 1\,000 pas est celui d'un robot debout qui n'avance pas. "
                rf"Les politiques finales rejouées avec notre protocole (10 épisodes déterministes, graines d'évaluation 10\,000 à 10\,009, normalisation figée) ; les retours redonnent exactement ceux de \file{{e6\_official\_eval.json}} (contrôle). Vitesse : moyenne de \texttt{{x\_velocity}} sur l'épisode, puis moyenne des épisodes ; agents sans chute : les dix épisodes vont aux 1\,000 pas. "
                rf"Dernière ligne : l'agent que le Zoo a publié sur Hugging Face, entraîné en 2022 avec Stable-Baselines3 1.5.1a8 et Gym 0.21, avec nos réglages ; sa fiche annonce {num(mc['mean_reward'], lang)} ± {num(mc['std_reward'], lang)} sur 10 épisodes, notre protocole donne {num(hub['score_10_episodes'], lang)} sur 10 épisodes. "
                rf"Les journaux d'entraînement officiels disent la même chose : retour par pas des épisodes complets, médiane des graines {num(s['return_per_step_median_of_seeds'], lang, 3)} (de {num(s['range'][0], lang, 3)}{to(lang)}{num(s['range'][1], lang, 3)}). "
                r"Sources : \file{sim/analysis/e6_enjoy.json}, \file{e6_hub.json}, \file{e6_speed.json}.",
                r"Experiment E6, what the agents of the published recipe do (deviations 31 and 33 of \file{sim/SIM_PROTOCOL.md}, written before these computations). On Hopper, the reward of a step is the forward velocity, plus 1 while the robot stays upright, minus a small action cost: a return of about 1,000 over 1,000 steps is that of a robot standing still. "
                rf"The final policies replayed with our protocol (10 deterministic episodes, evaluation seeds 10,000 to 10,009, frozen normalisation); the returns match those of \file{{e6\_official\_eval.json}} exactly (control). Speed: mean of \texttt{{x\_velocity}} over the episode, then mean of the episodes; agents that never fall: all ten episodes reach 1,000 steps. "
                rf"Last row: the agent the Zoo published on Hugging Face, trained in 2022 with Stable-Baselines3 1.5.1a8 and Gym 0.21, with our settings; its model card states {num(mc['mean_reward'], lang)} ± {num(mc['std_reward'], lang)} over 10 episodes, our protocol gives {num(hub['score_10_episodes'], lang)} over 10 episodes. "
                rf"The official training logs say the same: return per step of the full-length episodes, median over seeds {num(s['return_per_step_median_of_seeds'], lang, 3)} (from {num(s['range'][0], lang, 3)}{to(lang)}{num(s['range'][1], lang, 3)}). "
                r"Sources: \file{sim/analysis/e6_enjoy.json}, \file{e6_hub.json}, \file{e6_speed.json}.")
        floattable("e6-vitesse", lang, cap, L(lang, "E6 : la vitesse des agents", "E6: the agents' speed"),
                   r"@{}>{\raggedright\arraybackslash}p{5.6cm}rrrr@{}", head, rows, tabcolsep="4pt")


CRIT_ALL = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"] + [f"Y{i}" for i in range(1, 13)]


def t_accord_intervalles():
    dr = J("study/survey_extra.json")["double_readings"]
    po = dr["pooled"]
    for lang in LANGS:
        head = [L(lang, r"Code & Critère & accord & \% [Wilson 95~\%] & $\kappa$ [IC 95~\%]",
                  r"Code & Criterion & agree & \% [95\% Wilson] & $\kappa$ [95\% CI]")]
        rows = []
        for k in CRIT_ALL:
            c = po[k]
            weak = c["kappa"] is not None and c["kappa"] < 0.7
            kap = "" if c["kappa"] is None else f"{num(c['kappa'], lang, 2)} {ci2(c['kappa_boot95'], lang)}"
            cells = [k, CRIT[k][0 if lang == "fr" else 1], kn(c["same"], c["n"]),
                     f"{pc(c['agree'], lang)} {iv(pc(c['wilson'][0], lang), pc(c['wilson'][1], lang), lang)}", kap]
            rows.append(" & ".join(bold(x, weak) for x in cells))
            if k in ("Q8", "X7"):
                rows.append("MID")
        verdict = ["Q5", "Y9", "X7", "X2"]
        vs, vn = sum(po[k]["same"] for k in verdict), sum(po[k]["n"] for k in verdict)
        pairs = {g: len(v["papers"]) for g, v in dr["pairs"].items()}
        cap = L(lang,
                rf"Accord des doubles lectures à l'aveugle, toutes paires réunies, avec ses intervalles (écart 30 (a) de \file{{study/PROTOCOL.md}}, écrit avant ce calcul). {dr['papers']} articles relus : G et G2, les mêmes {pairs['G']} articles de 2026 avec les deux grilles ; R2, {pairs['R2']} articles ajoutés (5 de 2018, 5 de 2026) ; R3, {pairs['R3']} articles de la trajectoire. "
                rf"Accord : décisions identiques sur les articles où les deux lecteurs ont répondu ; intervalle de Wilson à 95~\% ; kappa de Cohen avec un intervalle bootstrap percentile (vide quand un lecteur ne varie pas). "
                rf"Sur les quatre critères qui portent un verdict (Q5, Y9, X7, X2), {vs} décisions identiques sur {vn}. \textbf{{En gras}}, les critères dont le kappa reste sous 0,70. "
                r"Avec dix articles par paire, 9 sur 10 a pour intervalle [60\,;\,98]~\% : l'accord d'une paire seule borne mal la fiabilité. Source : \file{study/survey_extra.json} (\file{study/survey_extra.py}).",
                rf"Agreement of the blind double readings, all pairs pooled, with its intervals (deviation 30 (a) of \file{{study/PROTOCOL.md}}, written before this computation). {dr['papers']} papers reread: G and G2, the same {pairs['G']} papers of 2026 with both grids; R2, {pairs['R2']} added papers (5 from 2018, 5 from 2026); R3, {pairs['R3']} papers of the trajectory. "
                rf"Agree: identical decisions over the papers where both readers answered; 95\% Wilson interval; Cohen's kappa with a percentile bootstrap interval (blank when one reader does not vary). "
                rf"On the four criteria that carry a verdict (Q5, Y9, X7, X2), {vs} identical decisions out of {vn}. \textbf{{In bold}}, the criteria whose kappa stays under 0.70. "
                r"With ten papers per pair, 9 out of 10 has the interval [60,\,98]\%: one pair's agreement bounds reliability poorly. Source: \file{study/survey_extra.json} (\file{study/survey_extra.py}).")
        floattable("accord-intervalles", lang, cap, L(lang, "Accord des doubles lectures, avec intervalles", "Agreement of the double readings, with intervals"),
                   r"@{}l>{\raggedright\arraybackslash}p{5.5cm}rrr@{}", head, rows, tabcolsep="4pt")


def t_difference_detectable():
    m = J("study/survey_extra.json")["mde"]
    ext = {r["k"]: r for r in J("study/extension_stats.json")["rows"]}
    for lang in LANGS:
        none = L(lang, "aucune", "none")

        def md(x, sgn):
            return none if x is None else pc(sgn * x, lang, sign=True)
        head = [L(lang, r" & & & & \multicolumn{2}{c}{Au seuil de 5~\%} & \multicolumn{2}{c}{\makecell{Bonferroni\\{}(5~\%/11)}} & \multicolumn{2}{c}{\makecell{Puissance de\\{}l'écart vu}}",
                  r" & & & & \multicolumn{2}{c}{\makecell{At the\\{}5\% level}} & \multicolumn{2}{c}{\makecell{Bonferroni\\{}(5\%/11)}} & \multicolumn{2}{c}{\makecell{Power of\\{}the gap seen}}"),
                r"\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}",
                L(lang, r"Code & Critère & 2018 (\%) & écart vu & hausse & baisse & hausse & baisse & 5~\% & Bonf.",
                  r"Code & Criterion & 2018 (\%) & gap seen & rise & fall & rise & fall & 5\% & Bonf.")]
        rows = []
        for k in CRIT_ALL:
            c = m[k]
            hit = ext[k]["classic_vs_ours2018"]["p_holm"] < 0.05 and k != "Q2"
            cells = [k, CRIT[k][0 if lang == "fr" else 1], pc(c["base"], lang), pc(c["observed"], lang, sign=True),
                     md(c["up_5"], 1), md(c["down_5"], -1), md(c["up_bonf"], 1), md(c["down_bonf"], -1),
                     pc(c["power_observed_5"], lang), pc(c["power_observed_bonf"], lang)]
            rows.append(" & ".join(bold(x, hit) for x in cells))
            if k in ("Q8", "X7"):
                rows.append("MID")
        q7 = m["Q7"]
        cap = L(lang,
                r"Plus petite différence que le sondage pouvait détecter (écart 30 (b) de \file{study/PROTOCOL.md}, écrit avant ce calcul) : pour chaque critère, partant de la part de 2018 et des effectifs réels, la plus petite hausse et la plus petite baisse, en points, que le test exact de Fisher bilatéral détecte avec 80~\% de puissance, au seuil de 5~\% puis de 5~\%/11 (Bonferroni sur les onze critères v1) ; « aucune » : aucune variation possible n'atteint cette puissance. "
                rf"À droite, la puissance qu'avait le test pour l'écart effectivement vu. \textbf{{En gras}}, les quatre critères dont l'écart passe la correction de Holm (tableau~\ref{{tab:sondage-pineau}}) : tous dépassent la différence détectable. "
                rf"Ailleurs, l'absence de changement détecté n'est pas une preuve d'absence : la hausse de Q7 ({pc(q7['observed'], lang, sign=True)} points) n'avait que {pct(q7['power_observed_5'], lang)} de chances d'être vue au seuil de 5~\%. "
                r"Source : \file{study/survey_extra.json} (\file{study/survey_extra.py}).",
                r"Smallest difference the survey could detect (deviation 30 (b) of \file{study/PROTOCOL.md}, written before this computation): for each criterion, starting from the 2018 share and the real sample sizes, the smallest rise and the smallest fall, in points, that the two-sided exact Fisher test detects with 80\% power, at the 5\% level then at 5\%/11 (Bonferroni over the eleven v1 criteria); ``none'': no possible change reaches that power. "
                rf"On the right, the power the test had for the gap actually seen. \textbf{{In bold}}, the four criteria whose gap passes the Holm correction (Table~\ref{{tab:sondage-pineau}}): all exceed the detectable difference. "
                rf"Elsewhere, no change detected is no proof of no change: the rise of Q7 ({pc(q7['observed'], lang, sign=True)} points) had only a {pct(q7['power_observed_5'], lang)} chance of being seen at the 5\% level. "
                r"Source: \file{study/survey_extra.json} (\file{study/survey_extra.py}).")
        floattable("difference-detectable", lang, cap, L(lang, "Plus petite différence détectable", "Minimum detectable difference"),
                   r"@{}l>{\raggedright\arraybackslash}p{4.2cm}rrrrrrrr@{}", head, rows, tabcolsep="3.2pt")


RULE = {"none": ("aucun changement", "no change"), "ambiguous": ("ambigu", "ambiguous"),
        "changed, not confirmed": ("changé, non confirmé", "changed, not confirmed"),
        "changed and confirmed": ("changé et confirmé", "changed and confirmed")}


def t_regle_origine():
    o = J("study/survey_extra.json")["original_rule"]
    for lang in LANGS:
        head = [L(lang, r" & & \multicolumn{2}{c}{Contre Pineau (2018)} & \multicolumn{2}{c}{Contre notre lecture de 2018} & ",
                  r" & & \multicolumn{2}{c}{Against Pineau (2018)} & \multicolumn{2}{c}{Against our reading of 2018} & "),
                r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
                L(lang, r"Critère & 2026 & écart [Newcombe] & $p$ Holm & écart [Newcombe] & $p$ Holm & Verdict",
                  r"Criterion & 2026 & gap [Newcombe] & Holm $p$ & gap [Newcombe] & Holm $p$ & Verdict")]
        rows = []
        for s, fr, en in (("classic2026", "RL classique 2026 (échantillon des verdicts)", "Classical RL 2026 (the verdicts' sample)"),
                          ("all2026", "Premier tirage 2026, grands modèles compris", "First 2026 draw, large models included")):
            rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\emph{{{L(lang, fr, en)}}}}}")
            for k, c in o[s].items():
                cells = [rf"\quad {k}", kn(*c["share"]), diff_cell(c["vs_pineau"], lang), pval(c["vs_pineau"]["p_holm"], lang),
                         diff_cell(c["vs_ours2018"], lang), pval(c["vs_ours2018"]["p_holm"], lang), RULE[c["rule"]][0 if lang == "fr" else 1]]
                rows.append(" & ".join(bold(x, c["rule"] != "none") for x in cells))
            if s == "classic2026":
                rows.append("MID")
        cap = L(lang,
                r"Ce qu'aurait donné la règle de verdict d'origine (écart 7 de \file{study/PROTOCOL.md}), remplacée ensuite par la comparaison à grille égale (écart 20) ; calcul de l'écart 30 (c), écrit avant lui. "
                r"La règle compare chaque critère de Pineau à ses chiffres de 2018 et à notre lecture de 2018 : « changé et confirmé » quand les deux écarts passent Holm dans le même sens, « changé, non confirmé » quand seul l'écart à Pineau passe, « ambigu » quand seul l'écart à notre lecture passe, « aucun changement » sinon. "
                r"Écarts en points, 2026 moins 2018, intervalle de Newcombe à 95~\%, test exact de Fisher, Holm sur les six critères. \textbf{En gras}, les critères qui reçoivent un autre verdict qu'« aucun changement ». "
                r"Source : \file{study/survey_extra.json} (\file{study/survey_extra.py}).",
                r"What the original verdict rule (deviation 7 of \file{study/PROTOCOL.md}), later replaced by the same-grid comparison (deviation 20), would have given; computation of deviation 30 (c), written before it. "
                r"The rule compares each of Pineau's criteria with her 2018 figures and with our reading of 2018: ``changed and confirmed'' when both gaps pass Holm in the same direction, ``changed, not confirmed'' when only the gap to Pineau passes, ``ambiguous'' when only the gap to our reading passes, ``no change'' otherwise. "
                r"Gaps in points, 2026 minus 2018, 95\% Newcombe interval, Fisher's exact test, Holm over the six criteria. \textbf{In bold}, the criteria that receive a verdict other than ``no change''. "
                r"Source: \file{study/survey_extra.json} (\file{study/survey_extra.py}).")
        floattable("regle-origine", lang, cap, L(lang, "La règle de verdict d'origine", "The original verdict rule"),
                   r"@{}lrrrrrl@{}", head, rows, tabcolsep="3.5pt")


Q5R = {"P0": ("Lecture publiée", "As published"),
       "P1": ("Les deux années sur les actes", "Both years on the proceedings"),
       "P1_bound": ("\\quad borne : incertains comptés oui", "\\quad bound: uncertain counted yes"),
       "P2": ("Les deux années sur la dernière version arXiv", "Both years on the latest arXiv version"),
       "P2_bound": ("\\quad borne : incertains comptés oui", "\\quad bound: uncertain counted yes"),
       "P3": ("Code disponible à la conférence", "Code available at the conference"),
       "P3_bound": ("\\quad borne : incertains oui, dépôts sans date non", "\\quad bound: uncertain yes, undated repositories no")}


def t_q5_versions():
    q = J("study/q5_versions.json")
    for lang in LANGS:
        head = [L(lang, r"Lecture de Q5 & 2018 & 2026 & écart [Newcombe] & $p$ & $p$ Holm & Articles qui changent",
                  r"Reading of Q5 & 2018 & 2026 & gap [Newcombe] & $p$ & Holm $p$ & Papers that change")]
        rows = []
        for k, (fr, en) in Q5R.items():
            r = q["readings"][k]
            ch = r["changed"]
            chs = L(lang, " ; ", "; ").join(f"{y} : {', '.join(v)}" if lang == "fr" else f"{y}: {', '.join(v)}" for y, v in ch.items() if v)
            cells = [L(lang, fr, en), kn(*r["ours2018"]), kn(*r["classic2026"]), diff_cell(r, lang), pval(r["p"], lang), pval(r["p_holm"], lang), chs]
            rows.append(" & ".join(cells))
        cv, rp = q["coverage"], q["repositories"]
        cap = L(lang,
                rf"Q5 (code en lien) selon la version de l'article lue (écart 31 de \file{{study/PROTOCOL.md}}, écrit avant ce calcul). {len(cv['2018_arxiv_found'])} des {cv['2018_no']} « non » de 2018 retrouvés sur arXiv (dernière version), {len(cv['2026_proc_found'])} articles de 2026 retrouvés dans les actes ; les occurrences douteuses tranchées par un arbitre neuf à l'aveugle, l'incertain compté non puis, pour la borne, oui. "
                rf"Code disponible à la conférence : un « oui » dont tous les dépôts GitHub ont été créés après le dernier jour de la conférence devient « non » ({rp['n']} dépôts datés ; un seul créé après, {', '.join(rp['created_after']['2018'])}). "
                r"Écart en points, 2026 moins 2018, intervalle de Newcombe à 95~\%, test exact de Fisher, Holm sur les onze critères v1. Le verdict de Q5 tient dans chaque lecture, la plus défavorable comprise. "
                r"Source : \file{study/q5_versions.json} (\file{study/q5_versions_stats.py}).",
                rf"Q5 (code linked) according to the version of the paper read (deviation 31 of \file{{study/PROTOCOL.md}}, written before this computation). {len(cv['2018_arxiv_found'])} of the {cv['2018_no']} 2018 ``no'' found on arXiv (latest version), {len(cv['2026_proc_found'])} papers of 2026 found in the proceedings; doubtful occurrences settled by a fresh blind arbiter, uncertain counted no and, for the bound, yes. "
                rf"Code available at the conference: a ``yes'' whose GitHub repositories were all created after the conference's last day turns ``no'' ({rp['n']} repositories dated; only one created after, {', '.join(rp['created_after']['2018'])}). "
                r"Gap in points, 2026 minus 2018, 95\% Newcombe interval, Fisher's exact test, Holm over the eleven v1 criteria. The Q5 verdict holds in every reading, the least favourable included. "
                r"Source: \file{study/q5_versions.json} (\file{study/q5_versions_stats.py}).")
        floattable("q5-versions", lang, cap, L(lang, "Q5 selon la version lue", "Q5 by version read"),
                   r"@{}>{\raggedright\arraybackslash}p{4.6cm}rrrrr>{\raggedright\arraybackslash}p{3.3cm}@{}", head, rows, tabcolsep="3.2pt")


SRC_X8 = {"seeds": ("graines", "seeds"), "unstated": ("non dit", "not stated"), "items": ("éléments de test", "test items"),
          "other": ("autre", "other"), "pooled": ("graines et épisodes mêlés", "seeds and episodes pooled"),
          "episodes": ("épisodes", "episodes")}


def t_x8():
    x = J("study/x8_stats.json")
    ext = {r["k"]: r for r in J("study/extension_stats.json")["rows"]}
    lb = J("study/survey_extra.json")["seeds_lower_bound"]
    for lang in LANGS:
        def share(k, n, w):
            return f"{kn(k, n)} & {pc(k / n, lang)} {iv(pc(w[0], lang), pc(w[1], lang), lang)}"
        head = [L(lang, r" & \multicolumn{2}{c}{2018} & \multicolumn{2}{c}{2026} & & ", r" & \multicolumn{2}{c}{2018} & \multicolumn{2}{c}{2026} & & "),
                r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
                L(lang, r"Mesure & $k/n$ & \% [Wilson] & $k/n$ & \% [Wilson] & écart [Newcombe] & $p$",
                  r"Measure & $k/n$ & \% [Wilson] & $k/n$ & \% [Wilson] & gap [Newcombe] & $p$")]
        rows = []
        r2 = ext["X2"]
        rows.append(" & ".join([L(lang, "X2, incertitude rapportée", "X2, uncertainty reported"),
                                share(*r2["ours2018"], r2["wilson_ours2018"]), share(*r2["classic2026"], r2["wilson_classic2026"]),
                                diff_cell(r2["classic_vs_ours2018"], lang), pval(r2["classic_vs_ours2018"]["p"], lang)]))
        m = x["main"]
        c18, c26 = m["counts"]["2018"], m["counts"]["2026"]
        rows.append(" & ".join([bold(L(lang, "X8, incertitude calculée sur des graines", "X8, uncertainty computed over seeds")),
                                share(c18["yes"], c18["n"], c18["wilson"]), share(c26["yes"], c26["n"], c26["wilson"]),
                                bold(diff_cell(m["diff"], lang)), bold(pval(m["diff"]["p"], lang))]))
        rows.append(" & ".join([L(lang, r"\quad parmi les articles X2 oui", r"\quad among X2 yes papers"),
                                share(c18["yes"], c18["x2_yes"], c18["wilson_of_x2"]), share(c26["yes"], c26["x2_yes"], c26["wilson_of_x2"]),
                                diff_cell(m["diff_among_x2"], lang), pval(m["diff_among_x2"]["p"], lang)]))
        pq = x["pooled_yes"]
        p18, p26 = pq["counts"]["2018"], pq["counts"]["2026"]
        rows.append(" & ".join([L(lang, r"\quad graines et épisodes mêlés comptés oui", r"\quad seeds and episodes pooled counted yes"),
                                share(p18["yes"], p18["n"], p18["wilson"]), share(p26["yes"], p26["n"], p26["wilson"]),
                                diff_cell(pq["diff"], lang), pval(pq["diff"]["p"], lang)]))
        l18, l26 = lb["2018"], lb["2026"]
        rows.append(" & ".join([L(lang, r"\quad borne mécanique (citation qui nomme des graines)", r"\quad mechanical bound (a quote naming seeds)"),
                                share(l18["seeds"], l18["experimental"], l18["wilson_of_experimental"]),
                                share(l26["seeds"], l26["experimental"], l26["wilson_of_experimental"]),
                                diff_cell(lb["diff_experimental"], lang), pval(lb["diff_experimental"]["p"], lang)]))
        rows.append("MID")
        rows.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\emph{{{L(lang, 'Sur quoi porte l’incertitude des articles X2 oui', 'What the uncertainty of the X2 yes papers is computed over')}}}}}")
        so = x["sources"]
        for k in sorted(SRC_X8, key=lambda k: -so["2026"].get(k, 0)):
            rows.append(" & ".join([r"\quad " + SRC_X8[k][0 if lang == "fr" else 1], str(so["2018"].get(k, 0)), "", str(so["2026"].get(k, 0)), "", "", ""]))
        dd = x["double_reading"]["all"]
        cap = L(lang,
                rf"Nouveau critère X8 (écart 32 de \file{{study/PROTOCOL.md}}, écrit avant toute lecture) : parmi les articles expérimentaux, ceux dont l'incertitude rapportée est calculée sur des graines (des entraînements indépendants). Les {c18['x2_yes'] + c26['x2_yes']} articles X2 oui lus par huit agents neufs, chacun lecteur principal sur les deux années, ce qui défait la confusion entre lecteur et année pour ce critère ; {dd['n']} articles lus deux fois, {dd['same']} accords (kappa {num(dd['kappa'], lang, 2)}). "
                rf"Écart en points, 2026 moins 2018, intervalle de Newcombe à 95~\%, test exact de Fisher ; $p$ Holm sur douze critères : {pval(m['p_holm_12'], lang)}. \textbf{{En gras}}, la mesure principale. "
                r"La borne mécanique de l'écart 30 (e) compte les articles dont une citation nomme des graines : plus large que X8, car une citation qui nomme des graines ne rattache pas la barre d'erreur à elles. "
                r"Partie basse : la source de l'incertitude des articles X2 oui, par année ; « non dit » : l'article ne dit pas sur quoi porte sa barre. "
                r"Sources : \file{study/x8_stats.json} (\file{study/x8_stats.py}), \file{study/extension_stats.json}, \file{study/survey_extra.json}.",
                rf"New criterion X8 (deviation 32 of \file{{study/PROTOCOL.md}}, written before any reading): among the experimental papers, those whose reported uncertainty is computed over seeds (independent training runs). The {c18['x2_yes'] + c26['x2_yes']} X2 yes papers read by eight fresh agents, each a primary reader on both years, which undoes the confound between reader and year for this criterion; {dd['n']} papers read twice, {dd['same']} agreements (kappa {num(dd['kappa'], lang, 2)}). "
                rf"Gap in points, 2026 minus 2018, 95\% Newcombe interval, Fisher's exact test; Holm $p$ over twelve criteria: {pval(m['p_holm_12'], lang)}. \textbf{{In bold}}, the main measure. "
                r"The mechanical bound of deviation 30 (e) counts the papers where a quote names seeds: wider than X8, since a quote that names seeds does not tie the error bar to them. "
                r"Bottom part: the source of the uncertainty of the X2 yes papers, per year; ``not stated'': the paper does not say what its bar is computed over. "
                r"Sources: \file{study/x8_stats.json} (\file{study/x8_stats.py}), \file{study/extension_stats.json}, \file{study/survey_extra.json}.")
        floattable("x8", lang, cap, L(lang, "X8 : l'incertitude calculée sur des graines", "X8: uncertainty computed over seeds"),
                   r"@{}>{\raggedright\arraybackslash}p{4.6cm}rrrrrr@{}", head, rows, tabcolsep="3.2pt")


GMOD = {"qwen05": ("Qwen2.5 0,5B", "Qwen2.5 0.5B"), "llama1": ("Llama 3.2 1B", "Llama 3.2 1B")}
GMEAS = {"pass1": ("pass@1 (échantillonné)", "pass@1 (sampled)"), "greedy": ("justesse gloutonne", "greedy accuracy"),
         "pass8": ("pass@8", "pass@8"), "truncated": ("part coupée", "cut-off share"),
         "finished": ("justesse des réponses finies", "accuracy of finished answers")}


def t_grpo_mesures():
    g = J("sim/llm/results/logs_stats_5.json")["gains"]
    for lang in LANGS:
        head = [L(lang, r"Mesure & \makecell[r]{pas 0\\{}(\%)} & \makecell[r]{pas 100\\{}(\%)} & \makecell[r]{gain\\{}(pts)} & \makecell[r]{IC percentile\\{}(bootstrap)} & IC de Student & \makecell[r]{graines\\{}en hausse} & \makecell[r]{$p$\\{}signe}",
                  r"Measure & \makecell[r]{step 0\\{}(\%)} & \makecell[r]{step 100\\{}(\%)} & \makecell[r]{gain\\{}(pts)} & \makecell[r]{percentile CI\\{}(bootstrap)} & Student CI & \makecell[r]{seeds\\{}going up} & \makecell[r]{sign\\{}$p$}")]
        rows = []
        for m in ("qwen05", "llama1"):
            for rew in ("true", "random"):
                n = len(g[f"{m} {rew} pass1"]["gains"])
                rows.append(rf"\multicolumn{{8}}{{@{{}}l}}{{\emph{{{GMOD[m][0 if lang == 'fr' else 1]}, {L(lang, 'vraie récompense' if rew == 'true' else 'récompense à pile ou face', 'true reward' if rew == 'true' else 'coin-flip reward')}, {n} {L(lang, 'graines', 'seeds')}}}}}")
                for meas in GMEAS:
                    d = g[f"{m} {rew} {meas}"]
                    t_ex = d["ci_t"][0] > 0 or d["ci_t"][1] < 0
                    cells = [r"\quad " + GMEAS[meas][0 if lang == "fr" else 1], pc(d["start"], lang, 1), pc(d["end"], lang, 1), gpts(d["mean"], lang),
                             iv(gpts(d["ci_boot"][0], lang), gpts(d["ci_boot"][1], lang), lang),
                             bold(iv(gpts(d["ci_t"][0], lang), gpts(d["ci_t"][1], lang), lang), t_ex),
                             f"{d['positive']}/{len(d['gains'])}", pval(d["p_sign"], lang)]
                    rows.append(" & ".join(cells))
                if (m, rew) != ("llama1", "random"):
                    rows.append(r"\addlinespace")
        cap = L(lang,
                r"Volet GRPO, cinq mesures tirées des journaux des essais déjà faits (écart 19 de \file{sim/llm/LLM_PROTOCOL.md}, écrit avant ce calcul) : pass@1 échantillonné (la mesure préregistrée), justesse gloutonne, pass@8, part des réponses coupées à 160 jetons, justesse parmi les réponses finies (pass@1 divisé par la part non coupée, une réponse coupée n'étant jamais juste). "
                r"Niveaux moyens au pas 0 et au pas 100, en pourcentage ; gain moyen par graine en points, avec l'intervalle bootstrap percentile du protocole et l'intervalle de Student, plus large et plus honnête avec cinq graines ; graines dont le gain est positif ; $p$ du test exact du signe. "
                r"\textbf{En gras}, les intervalles de Student qui excluent zéro. Règle fixée d'avance : un gain n'est établi que si l'intervalle de Student exclut zéro et si le $p$ exact corrigé par Holm passe 0,05 ; avec cinq graines, le test du signe ne descend jamais sous $2/32 = 0{,}0625$, si bien qu'aucun gain dans une configuration ne peut être établi. "
                r"Source : \file{sim/llm/results/logs_stats_5.json} (\file{sim/llm/logs_stats.py}).",
                r"GRPO strand, five measures drawn from the logs of the runs already made (deviation 19 of \file{sim/llm/LLM_PROTOCOL.md}, written before this computation): sampled pass@1 (the preregistered measure), greedy accuracy, pass@8, share of answers cut off at 160 tokens, accuracy among finished answers (pass@1 divided by the share not cut off, a cut-off answer never being right). "
                r"Mean levels at step 0 and step 100, in percent; mean gain per seed in points, with the protocol's percentile bootstrap interval and the Student interval, wider and more honest with five seeds; seeds whose gain is positive; $p$ of the exact sign test. "
                r"\textbf{In bold}, Student intervals that exclude zero. Rule fixed in advance: a gain is established only if the Student interval excludes zero and the Holm-corrected exact $p$ passes 0.05; with five seeds the sign test never goes below $2/32 = 0.0625$, so no gain within a configuration can be established. "
                r"Source: \file{sim/llm/results/logs_stats_5.json} (\file{sim/llm/logs_stats.py}).")
        floattable("grpo-mesures", lang, cap, L(lang, "GRPO : cinq mesures par configuration", "GRPO: five measures per configuration"),
                   r"@{}lrrrrrrr@{}", head, rows, tabcolsep="3.2pt")


def t_grpo_contraste():
    c = J("sim/llm/results/logs_stats_5.json")["contrasts"]
    for lang in LANGS:
        head = [L(lang, r"Mesure & \makecell[r]{vraie $-$ hasard\\{}(pts)} & IC de Welch 95~\% & \makecell[r]{$p$ permutation\\{}exacte} & $p$ Holm & Statut",
                  r"Measure & \makecell[r]{true $-$ random\\{}(pts)} & 95\% Welch CI & \makecell[r]{exact\\{}permutation $p$} & Holm $p$ & Status")]
        rows = []
        for m in ("qwen05", "llama1"):
            d0 = c[f"{m} pass1"]
            rows.append(rf"\multicolumn{{6}}{{@{{}}l}}{{\emph{{{GMOD[m][0 if lang == 'fr' else 1]}, {d0['n_true']} {L(lang, 'graines contre', 'seeds against')} {d0['n_random']}}}}}")
            for meas in GMEAS:
                d = c[f"{m} {meas}"]
                ph = d.get("p_holm_main", d.get("p_holm_finished", d.get("p_holm_secondary")))
                est = d.get("established")
                status = "" if est is None else (L(lang, "établi", "established") if est else L(lang, "non établi", "not established"))
                star = "$^*$" if "p_holm_main" in d else ""
                cells = [r"\quad " + GMEAS[meas][0 if lang == "fr" else 1] + star, gpts(d["diff"], lang),
                         iv(gpts(d["ci_welch"][0], lang), gpts(d["ci_welch"][1], lang), lang), pval(d["p_perm"], lang), pval(ph, lang), status]
                rows.append(" & ".join(bold(x, bool(est)) for x in cells))
            if m == "qwen05":
                rows.append("MID")
        cap = L(lang,
                r"Volet GRPO, la comparaison que le protocole demande : gain moyen sous la vraie récompense moins gain moyen sous la récompense tirée à pile ou face, par modèle et par mesure (écart 19 de \file{sim/llm/LLM_PROTOCOL.md}). "
                r"Intervalle de Welch à 95~\%, $p$ de la permutation exacte des graines entre les deux récompenses (toutes les partitions), correction de Holm : sur les deux modèles pour pass@1 (contraste principal, $^*$) et pour la justesse des réponses finies, sur les huit contrastes secondaires pour les autres mesures. "
                r"Établi : intervalle qui exclut zéro et $p$ Holm sous 0,05 ; \textbf{en gras}. Pour Llama, la vraie récompense fait mieux que le hasard parce que la récompense à pile ou face détruit le modèle, pas parce que la vraie récompense le fait progresser (tableau~\ref{tab:grpo-mesures}). "
                r"Source : \file{sim/llm/results/logs_stats_5.json} (\file{sim/llm/logs_stats.py}).",
                r"GRPO strand, the comparison the protocol asks for: mean gain under the true reward minus mean gain under the coin-flip reward, per model and per measure (deviation 19 of \file{sim/llm/LLM_PROTOCOL.md}). "
                r"95\% Welch interval, $p$ of the exact permutation of seeds between the two rewards (every split), Holm correction: over the two models for pass@1 (the main contrast, $^*$) and for the accuracy of finished answers, over the eight secondary contrasts for the other measures. "
                r"Established: interval that excludes zero and Holm $p$ under 0.05; \textbf{in bold}. For Llama, the true reward beats the coin flip because the coin-flip reward destroys the model, not because the true reward makes it progress (Table~\ref{tab:grpo-mesures}). "
                r"Source: \file{sim/llm/results/logs_stats_5.json} (\file{sim/llm/logs_stats.py}).")
        floattable("grpo-contraste", lang, cap, L(lang, "GRPO : vraie récompense contre pile ou face", "GRPO: true reward against coin flip"),
                   r"@{}lrrrrl@{}", head, rows, tabcolsep="3.5pt")


def main():
    for f in (t_sondage, t_sondage_lrl, t_trajectoire, t_accord, t_robustesse, t_e1, t_b1, t_e2, t_e2_bonferroni, t_e3,
              t_e4, t_e5, t_e6, t_e7, t_dose, t_b3, t_grpo, t_ecarts, t_env, t_calcul, t_articles,
              t_e2_strict, t_e1_grille, t_e3_holm, t_e3_puissance, t_e7_test, t_e5_holdout, t_regle_tranche, t_hyperparametres,
              t_e6_vitesse, t_accord_intervalles, t_difference_detectable, t_regle_origine, t_q5_versions, t_x8,
              t_grpo_mesures, t_grpo_contraste):
        f()
    names = sorted(p.stem for p in (GEN / "fr").glob("*.tex"))
    print(f"Wrote {len(names)} tables in gen/fr and gen/en: {', '.join(names)}")


if __name__ == "__main__":
    main()
