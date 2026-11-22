"""One sheet of the blind human re-reading of deviation 35 (study/PROTOCOL.md): the template written by feuilles35.py
and the parser used by compare.py. A sheet carries no paper identifier, title, conference, year or agent value.

    render(name)        the empty sheet <name>.md
    parse(text)         {"date", "minutes", "criteria": {k: {"decision", "quote", "page", "source"}}}
    problems(sheet)     what is still missing or contradictory; an empty list means the sheet is complete
"""
import re

CRIT = ["Q5", "Y9", "X7", "X2", "X8"]
SOURCES = ("seeds", "pooled", "episodes", "items", "unstated", "other")

RULES = {
    "Q5": ("Le code est en lien / Code is linked",
           "`yes` si l'article donne un lien vers du code (GitHub, GitLab, site du projet). « Code disponible sur "
           "demande », « sera publié », « will be made public at <URL> » : `no`. Une page de projet compte `yes` "
           "seulement si elle mène à du code ; un miroir anonyme qui contient le code compte `yes` (écarts 6 et 19).",
           "`yes` if the paper gives a link to code (GitHub, GitLab, project site). \"Code available on request\", "
           "\"will be released\", \"will be made public at <URL>\": `no`. A project page counts `yes` only if it "
           "leads to code; an anonymous mirror that contains the code counts `yes` (deviations 6 and 19)."),
    "Y9": ("La sensibilité à au moins un hyperparamètre est montrée / Sensitivity to at least one hyperparameter is "
           "shown",
           "`yes` si au moins un hyperparamètre de la méthode est balayé et que le résultat est montré (figure, "
           "tableau ou phrase chiffrée). Une ablation de composant ne compte pas : ce n'est pas un hyperparamètre. "
           "Compte un hyperparamètre que l'article présente comme tel ; une variante qu'il présente comme un "
           "composant reste une ablation. Un paramètre réglé à l'inférence compte s'il est présenté comme un "
           "hyperparamètre ; une condition de l'environnement ne compte pas ; le résultat montré doit être une "
           "mesure de performance (écarts 14, 17 et 19).",
           "`yes` if at least one hyperparameter of the method is swept and the result is shown (figure, table or "
           "sentence with numbers). A component ablation does not count: it is not a hyperparameter. A "
           "hyperparameter counts if the paper presents it as one; a variant it presents as a component remains an "
           "ablation. A parameter set at inference counts if it is presented as a hyperparameter; a condition of "
           "the environment does not count; the result shown must be a performance measure (deviations 14, 17 "
           "and 19)."),
    "X7": ("Le calcul employé est chiffré / The compute used is quantified",
           "`yes` exige au moins une quantité : heures, GPU-heures, FLOP, ou un nombre de GPU avec une durée. Le "
           "seul nom du matériel : `no` (écart 2).",
           "`yes` requires at least one quantity: hours, GPU-hours, FLOP, or a number of GPUs with a duration. The "
           "name of the hardware alone: `no` (deviation 2)."),
    "X2": ("Une incertitude est rapportée sur les résultats principaux / An uncertainty is reported on the main "
           "results",
           "`yes` si les résultats principaux (le tableau ou la courbe qui porte la conclusion) montrent une "
           "incertitude : écart type, erreur type, intervalle de confiance, bande autour de la courbe, barres "
           "d'erreur. Des barres d'erreur seules suffisent ici.",
           "`yes` if the main results (the table or curve carrying the conclusion) show an uncertainty: standard "
           "deviation, standard error, confidence interval, band around the curve, error bars. Error bars alone "
           "are enough here."),
    "X8": ("L'incertitude est calculée sur des entraînements indépendants / The uncertainty is computed over "
           "independent training runs",
           "`yes` si l'incertitude des résultats principaux est calculée entre au moins deux entraînements "
           "indépendants (graines) et que l'article le dit (« mean ± std over 5 seeds », « shaded area: standard "
           "error across 10 runs ») ; `no` si elle porte sur des épisodes, des déroulements d'évaluation ou des "
           "éléments de test seulement, si elle mêle graines et épisodes dans un même écart, ou si sa source n'est "
           "pas dite ; `na` si et seulement si X2 vaut `no`. Une seule source : `seeds` (entraînements "
           "indépendants), `pooled` (graines et épisodes réunis), `episodes`, `items` (éléments de test), "
           "`unstated` (non dit), `other` (préciser dans la citation). `yes` exige `seeds` (écart 32).",
           "`yes` if the uncertainty of the main results is computed between at least two independent training "
           "runs (seeds) and the paper says so (\"mean ± std over 5 seeds\", \"shaded area: standard error across "
           "10 runs\"); `no` if it is over episodes, evaluation rollouts or test items only, if it mixes seeds and "
           "episodes in one spread, or if its source is not stated; `na` if and only if X2 is `no`. One source: "
           "`seeds` (independent training runs), `pooled` (seeds and episodes together), `episodes`, `items` (test "
           "items), `unstated`, `other` (say what in the quote). `yes` requires `seeds` (deviation 32)."),
}

F_DATE = "date de lecture / reading date (AAAA-MM-JJ)"
F_MIN = "durée en minutes / minutes spent"
F_DEC = "décision / decision (yes, no, na)"
F_QUOTE = "citation / quote"
F_PAGE = "page du fichier PDF / page of the PDF file"
F_SRC = "source (seeds, pooled, episodes, items, unstated, other)"
ABSENT = "absent après lecture des sections expériences, annexes et liens"


def render(name):
    pdf = f"`study/relecture_humaine/feuilles/pdf/{name}.pdf` (annexe comprise / supplement included)"
    out = [f"# Feuille {name} / Sheet {name}", "",
           "Relecture humaine à l'aveugle, écart 35 de `study/PROTOCOL.md`. Mode d'emploi : `../LISEZMOI.md`.",
           "*Blind human re-reading, deviation 35 of `study/PROTOCOL-en.md`. Instructions: `../README.md`.*", "",
           f"- article / paper : {pdf}",
           f"- {F_DATE} : ",
           f"- {F_MIN} : ", "",
           "Écrire après les deux-points, sur la même ligne. Décision : `yes`, `no` ou `na`. Citation : copiée mot "
           f"pour mot du PDF. Si rien ne justifie un `yes` : `no`, la citation « {ABSENT} » et la page vide. "
           "Page : le numéro de page du fichier PDF (celui du lecteur de PDF), pas le numéro imprimé ; "
           "sur deux pages : `6, 7`.",
           "*Write after the colon, on the same line. Decision: `yes`, `no` or `na`. Quote: copied word for word "
           f"from the PDF. If nothing justifies a `yes`: `no`, the quote \"{ABSENT}\" and an empty page. Page: the "
           "page number of the PDF file (as the PDF viewer shows it), not the printed number; over two pages: "
           "`6, 7`.*", ""]
    for k in CRIT:
        title, fr, en = RULES[k]
        out += [f"## {k}. {title}", "", f"Règle : {fr}", "", f"*Rule: {en}*", "",
                f"- {F_DEC} : ", f"- {F_QUOTE} : ", f"- {F_PAGE} : "]
        if k == "X8":
            out.append(f"- {F_SRC} : ")
        out.append("")
    return "\n".join(out)


def _field(block, label):
    m = re.search(r"^- " + re.escape(label) + r" :(.*)$", block, re.M)
    return None if m is None else m.group(1).strip()


def parse(text):
    head, *blocks = re.split(r"^## ", text, flags=re.M)
    sheet = dict(date=_field(head, F_DATE), minutes=_field(head, F_MIN), criteria={})
    for b in blocks:
        k = b.split(".", 1)[0].strip()
        if k in CRIT:
            sheet["criteria"][k] = dict(decision=_field(b, F_DEC), quote=_field(b, F_QUOTE), page=_field(b, F_PAGE),
                                        source=_field(b, F_SRC) if k == "X8" else None)
    return sheet


def started(sheet):
    """Whether anything has been written in the sheet."""
    return bool(sheet["date"] or sheet["minutes"]) or any(v for c in sheet["criteria"].values() for v in c.values())


def problems(sheet):
    out = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", sheet["date"] or ""):
        out.append("date de lecture manquante ou pas au format AAAA-MM-JJ")
    if sheet["minutes"] and not re.fullmatch(r"\d+", sheet["minutes"]):
        out.append("durée : un nombre entier de minutes")
    C = sheet["criteria"]
    for k in CRIT:
        if k not in C:
            out.append(f"{k} : section absente")
            continue
        c = C[k]
        if c["decision"] not in ("yes", "no", "na"):
            out.append(f"{k} : décision {c['decision']!r} (yes, no ou na)")
        if not c["quote"]:
            out.append(f"{k} : citation vide")
        if c["decision"] == "yes" and not c["page"]:
            out.append(f"{k} : page vide pour un yes")
        if c["page"] and not re.fullmatch(r"\d+(\s*,\s*\d+)*", c["page"]):
            out.append(f"{k} : page {c['page']!r} (un nombre, ou deux séparés par une virgule)")
    if "X2" in C and "X8" in C:
        x2, x8 = C["X2"], C["X8"]
        if x2["decision"] == "no" and x8["decision"] != "na":
            out.append("X8 : doit valoir na quand X2 vaut no")
        if x2["decision"] == "yes":
            if x8["decision"] not in ("yes", "no"):
                out.append("X8 : yes ou no quand X2 vaut yes")
            if x8["source"] not in SOURCES:
                out.append(f"X8 : source {x8['source']!r} (une de {', '.join(SOURCES)})")
            if x8["decision"] == "yes" and x8["source"] != "seeds":
                out.append("X8 : yes exige la source seeds")
    return out
