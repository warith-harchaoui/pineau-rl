"""Three diagrams of the technical report, in French and English: figures/src/<name>-<lang>.svg.

  flux-sondage   the survey as a flow: populations, draws, samples, readers, double readings, harmonisation,
                 checks, final comparisons (counts from study/*.json, study/PROTOCOL.md, docs/conclusions.md)
  frise-ecarts   the three protocols and their dated deviations, day by day from 8 to 21 November 2026 (dates read
                 from the deviation texts of the three protocols)
  architecture   the repository as a pipeline, from training runs to documents, with the make targets and the CI

The survey flow and the repository each take two figures (flux-sondage and flux-sondage-2, architecture and
architecture-2), so that every text prints at 13 px or more on a page no taller than 1.35 times its width.

Hand-written SVG, Python standard library only, drawn with the article's toolkit (article/figures/draw.py, imported
by path): its faces embedded as subsets (Latin Modern when tools/figures.py runs this with DRAW_FONTS=latex,
Roboto otherwise), the house header and footer. Every text goes
through `tx`, which refuses a character missing from the subset of its face. The same input gives the same bytes.
"""
import datetime
import importlib.util
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
ROOT = REPORT.parent
OUT = REPORT / "figures" / "src"

_spec = importlib.util.spec_from_file_location("draw", ROOT / "article" / "figures" / "draw.py")
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)

INK, INK2, MUTED, RULE, GRID, PANEL, PAPER = D.INK, D.INK2, D.MUTED, D.RULE, D.GRID, D.PANEL, D.PAPER
EDGE = "#DADDE2"          # outline of a white card
RAD = 6                   # one corner radius for every card
ARROW = "#9AA0A9"         # every connector
SOFT = "#646A74"          # secondary text: 4.5:1 or more on white, on the grey panels and on a grey chip
# Column and lane colours, from the house palette, the teal and the orange darkened until white text and text on
# white clear 4.5:1
C18, C26, CTR, CSIM = D.ALGO_C["PPO (PyTorch)"], D.ALGO_C["SAC"], "#0B7F6C", "#B0580A"
LANGS = ("fr", "en")


# ---------------------------------------------------------------------------------------------------------------
# Drawing helpers


def shade(hex_, k):
    """Mix a colour with black: k = 0 keeps it, k = 1 gives black."""
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(c * (1 - k)) for c in (r, g, b))


def glue(t):
    return D._GLUE(t)


def tx(s, x, y, t, face="sans", size=12, fill=INK, anchor="start", bg=PAPER, extra=""):
    """A text, after checking that every character exists in the subset of its face."""
    t = glue(t).replace("|", "")
    bad = D.missing(t, face)
    if bad:
        raise ValueError(f"glyphs missing from {face}: {bad!r} in {t!r}")
    s.text(x, y, t, face, size, fill, anchor, extra, halo=bg)


def lines(t, face, size, w):
    return D.wrap(t, face, size, w)


def card(s, x, y, w, h, fill=PAPER, stroke=EDGE, sw=1, rx=RAD):
    extra = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    s.rect(x, y, w, h, fill, rx=rx, extra=extra)


def arrow(s, pts, col=ARROW, sw=1.3, head=6.5):
    """A polyline ending in a drawn triangle (no arrow glyph: Roboto has none)."""
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    d = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    bx, by = x2 - ux * head, y2 - uy * head
    body = [*pts[:-1], (bx, by)]
    s.path("M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in body), col, sw)
    hw = head * 0.58
    s.add(f'<path d="M{x2:.1f},{y2:.1f} L{bx - uy * hw:.1f},{by + ux * hw:.1f} '
          f'L{bx + uy * hw:.1f},{by - ux * hw:.1f} Z" fill="{col}"/>')


# Print sizes: the report sets a 760 px figure at text width, about 442 pt, so 1 px is about 0.58 pt. Every text of
# these diagrams is at least 13 px (7.5 pt), and every figure at most 1.35 times as tall as it is wide, beyond which
# LaTeX would shrink it further to fit the page.
MIN = 13
MAXH = 1.35 * 760

STY = {  # kind: face, size, colour, line height
    "p": ("sans", 13, INK2, 17.5),
    "pb": ("sans5", 13, INK, 17.5),
    "small": ("sans", 13, SOFT, 17.5),
    "mono": ("mono", 13, SOFT, 17.5),
    "code": ("mono", 13, INK, 17.5),
}


def block(s, x, y, w, items, bg=PAPER):
    """Lay out items top-down inside width w; draw them when s is given. Returns the height used.
    Items: (kind, text) for the kinds of STY; ("big", number, label, colour); ("chips", [(label, colour)]);
    ("rows", [(left, right)], colour); ("gap", px)."""
    cy = 0.0
    for it in items:
        k = it[0]
        if k == "gap":
            cy += it[1]
        elif k in STY:
            face, size, col, lh = STY[k]
            for ln in lines(it[1], face, size, w):
                if s:
                    tx(s, x, y + cy + lh * 0.5 + size * 0.36, ln, face, size, col, bg=bg)
                cy += lh
        elif k == "big":
            _, number, label, col = it
            nsize, lsize = 26, 14
            nw = D.width(number, "sans7", nsize)
            ls = lines(label, "sans5", lsize, w - nw - 8)
            base = cy + nsize * 0.95
            if s:
                tx(s, x, y + base, number, "sans7", nsize, col, bg=bg)
            if len(ls) == 1:
                if s:
                    tx(s, x + nw + 7, y + base, ls[0], "sans5", lsize, INK, bg=bg)
                cy = math.ceil((base + 8) / 17.5) * 17.5  # on the line grid of the text, as in a card beside
            else:
                ls = lines(label, "sans5", lsize, w)
                cy = base + 4
                for ln in ls:
                    cy += 18
                    if s:
                        tx(s, x, y + cy - 4, ln, "sans5", lsize, INK, bg=bg)
                cy += 4
        elif k == "chips":
            cx, h, gap = 0.0, 24, 6
            cy += 3
            for label, col in it[1]:
                cw = D.width(glue(label), "sans5", 13) + 18
                if cx and cx + cw > w:
                    cx, cy = 0.0, cy + h + gap
                if s:
                    s.rect(x + cx, y + cy, cw, h, D.tint(col, 0.86), rx=h / 2)
                    tx(s, x + cx + cw / 2, y + cy + 16.5, label, "sans5", 13, shade(col, 0.22), "middle",
                       bg=D.tint(col, 0.86))
                cx += cw + gap
            cy += h + 3
        elif k == "rows":
            _, rows, col = it
            for a, b in rows:
                cy += 20
                if s:
                    tx(s, x, y + cy - 5, a, "tick", 13, SOFT, bg=bg)  # a year: a number, not code
                    tx(s, x + 50, y + cy - 5, b, "sans7", 15, col, bg=bg)
            cy += 3
    return cy


def caps(s, x, y, label, bg=PAPER):
    """A level name in small capitals at baseline y. Returns its width."""
    t = glue(label).upper()
    tx(s, x, y, t, "sans7", MIN, SOFT, bg=bg, extra=' letter-spacing="0.6"')
    return D.width(t, "sans7", MIN) + 0.6 * len(t)


def stage(s, x, y, w, label, bg=PAPER):
    """A stage label in small capitals, followed by a hairline to the right edge."""
    tw = caps(s, x, y, label, bg)
    s.line(x + tw + 10, y - 4.5, x + w, y - 4.5, GRID)


def fill_card(s, x, y, w, items, style="plain", col=INK, pad=12, minh=0):
    """The height of a card holding a block of items."""
    inner = w - 2 * pad - (4 if style == "accent" else 0)
    flat = [it[1:] if it[0] == "foot" else it for it in items]
    return max(block(None, 0, 0, inner, flat) + 2 * pad - 2, minh)


def draw_card(s, x, y, w, h, items, style="plain", col=INK, pad=12):
    if style == "accent":
        card(s, x, y, w, h)
        e = RAD - math.sqrt(RAD ** 2 - (RAD - 4) ** 2)
        s.add(f'<path d="M{x + 4:.2f},{y + e:.2f} A{RAD},{RAD} 0 0 0 {x:.2f},{y + RAD:.2f} V{y + h - RAD:.2f} '
              f'A{RAD},{RAD} 0 0 0 {x + 4:.2f},{y + h - e:.2f} Z" fill="{col}"/>')
        bg = PAPER
    elif style == "sample":
        bg = D.tint(col, 0.9)
        card(s, x, y, w, h, bg, D.tint(col, 0.55), 1.2)
    else:
        card(s, x, y, w, h)
        bg = PAPER
    off = 4 if style == "accent" else 0
    body = [it for it in items if it[0] != "foot"]
    foot = [it[1:] for it in items if it[0] == "foot"]
    block(s, x + pad + off, y + pad - 1, w - 2 * pad - off, body, bg)
    if foot:
        fh = block(None, 0, 0, w - 2 * pad - off, foot)
        block(s, x + pad + off, y + h - pad + 1 - fh, w - 2 * pad - off, foot, bg)


def figure(T, accent=INK):
    f = D.Fig(False, T["title"], T["sub"], accent)
    f.title, f.desc = T["title"].replace("|", ""), T["desc"]
    return f


def finish(f, y, source):
    """The house footer (draw.Fig.finish) with its source line at 13 px instead of 11.5, for print."""
    s, L, W = f.s, f.L, f.W
    y += 26
    s.line(L, y - 17, W - L, y - 17, GRID)
    size = MIN
    site, bsize = "Deraison.ai", size + 1.5
    lh = bsize * 1.05
    lw = lh * D.LOGO_VB[2] / D.LOGO_VB[3]
    sw = D.width(site, "brand", bsize)
    ls = lines(source, "sans", size, W - 2 * L - sw - lw - 26)
    for i, ln in enumerate(ls):
        tx(s, L, y + i * size * 1.35, ln, "sans", size, D.MUTED)
    s.text(W - L, y, site, "brand", bsize, INK, "end")
    lx, ly = W - L - sw - 5 - lw, y - bsize * 0.72 - (lh - bsize * 0.72) / 2
    s.add(f'<svg x="{lx:.1f}" y="{ly:.1f}" width="{lw:.1f}" height="{lh:.1f}" '
          f'viewBox="0 0 {D.LOGO_VB[2]} {D.LOGO_VB[3]}" aria-hidden="true">{D.LOGO_BODY}</svg>')
    h = y + (len(ls) - 1) * size * 1.35 + 16
    assert h <= MAXH, f"{f.title}: {h:.0f} px tall, more than {MAXH:.0f}"
    return s.render(h, f.title, f.desc)


def pill(s, x, y, t):
    """A make target: mono text in a dark capsule whose top is at y. Returns its width."""
    w = D.width(t, "mono", MIN) + 16
    s.rect(x, y, w, 22, INK, rx=11)
    tx(s, x + 8, y + 15.5, t, "mono", MIN, PAPER, bg=INK)
    return w


# ---------------------------------------------------------------------------------------------------------------
# Sources: every count read from a result file of the repository


def survey_counts():
    st = ROOT / "study"
    J = lambda n: json.loads((st / n).read_text(encoding="utf-8"))
    pop26, pop18 = J("rl_population_2026.json"), J("rl_population_2018.json")
    rep18 = J("replacements_2018.json")
    sample26, calib18 = J("sample_2026.json"), J("calib_2018_v2.json")
    queue, screened = J("classic_queue_2026.json"), J("classic_screened_out_2026.json")
    traj, trajq = J("trajectory.json"), J("trajectory_queue.json")
    agree, fal = J("agree_v2.json"), J("falsify_no.json")
    venues = lambda pop: {v: sum(1 for p in pop if p["venue"] == v) for v in sorted({p["venue"] for p in pop})}
    c = {
        "pop26": len(pop26), "pop26_v": venues(pop26), "pop18": len(pop18), "pop18_v": venues(pop18),
        "new18": rep18["new_per_venue"], "sample26_v": venues(sample26), "n18": len(calib18),
        "rest26": len(queue) + len(screened), "screened": len(screened),
        "traj_pop": {y: len(trajq[y]["queue"]) for y in sorted(trajq)}, "traj_sizes": traj["sizes"],
        "no": sum(v["no"] for v in fal["counts"].values()),
        "turned18": sum(len(v["turned"]) for k, v in fal["counts"].items() if k.startswith("2018")),
        "turned26": sum(len(v["turned"]) for k, v in fal["counts"].items() if k.startswith("2026")),
        "doubtful": sum(len(v["uncertain"]) for v in fal["counts"].values()),
        "verdict_changes": len(fal["verdict_changes"]["turned"]),
        "r2_min": min(v["agree"] for v in agree["R2"]["criteria"].values()),
        "r3_min": min(v["agree"] for v in agree["R3"]["criteria"].values()),
        "r2_n": len(agree["R2"]["criteria"]), "g2_y1": agree["G2"]["criteria"]["Y1"]["agree"],
    }
    assert c["n18"] == 50 and c["traj_sizes"]["2018"] == 48 and c["traj_sizes"]["2026"] == 50
    assert c["pop26"] == 1252 and c["pop18"] == 131 and c["rest26"] == 1202 and c["screened"] == 429
    assert c["traj_pop"] == {"2019": 134, "2020": 222, "2022": 301, "2024": 374}
    assert c["no"] == 377 and (c["turned18"], c["turned26"]) == (2, 8) and c["doubtful"] == 24
    assert c["r2_min"] == 0.8 and c["r3_min"] == 0.8 and c["r2_n"] == 23 and c["g2_y1"] == 0.6
    return c


def n(x, lang):
    return D.num(x, lang)


# ---------------------------------------------------------------------------------------------------------------
# 1. The survey as a flow, in two figures: the draws (flux-sondage), then the reading (flux-sondage-2)


def columns(f):
    G_ = 18
    CW = (f.W - 2 * f.L - 2 * G_) / 3
    return CW, G_, [f.L + i * (CW + G_) for i in range(3)]


def column_heads(f, y, fr):
    s = f.s
    CW, _, X = columns(f)
    heads = ("2018", "2026", "2019 à 2024" if fr else "2019 to 2024")
    for i, (a, col) in enumerate(zip(heads, (C18, C26, CTR))):
        s.circle(X[i] + 6, y - 5.5, 6, col)
        tx(s, X[i] + 18, y, a, "sans7", 16, INK)
    return y + 24


def flux_sondage(lang):
    c = survey_counts()
    fr = lang == "fr"
    v18, v26, tp = c["pop18_v"], c["pop26_v"], c["traj_pop"]
    T = {
        "title": ("Chaque article lu vient |d'un tirage au sort écrit d'avance" if fr else
                  "Every paper read comes |from a draw written in advance"),
        "sub": ("Le sondage, première partie : des articles de RL publiés aux trois échantillons" if fr else
                "The survey, part one: from the published RL papers to the three samples"),
        "source": ("Sources : study/PROTOCOL.md (écarts 12 et 25), study/*.json, docs/conclusions.md" if fr else
                   "Sources: study/PROTOCOL-en.md (deviations 12 and 25), study/*.json, docs/conclusions-en.md"),
        "desc": ("Première partie du diagramme de flux du sondage. Trois colonnes, 2018, 2026 et les années 2019 à "
                 "2024, descendent de la population d'articles de RL au tirage au sort puis à l'échantillon : 50 "
                 "articles de 2018, 50 articles de RL classique de 2026, 80 articles de 2019 à 2024." if fr else
                 "Part one of the survey's flow diagram. Three columns, 2018, 2026 and the years 2019 to 2024, go "
                 "down from the population of RL papers to the random draw and the sample: 50 papers from 2018, 50 "
                 "classical RL papers from 2026, 80 papers from 2019 to 2024."),
    }
    f = figure(T)
    s, L, W = f.s, f.L, f.W
    CW, G_, X = columns(f)
    cols = (C18, C26, CTR)
    y = column_heads(f, f.top + 8, fr)

    def row(label, cells, styles, arrows=True):
        nonlocal y
        stage(s, L, y + 10, W - 2 * L, label)
        y += 22
        h = max(fill_card(s, X[i], y, CW, cells[i], styles[i], cols[i]) for i in range(3))
        for i in range(3):
            draw_card(s, X[i], y, CW, h, cells[i], styles[i], cols[i])
        y += h
        if arrows:
            for i in range(3):
                arrow(s, [(X[i] + CW / 2, y + 3), (X[i] + CW / 2, y + 22)])
            y += 26

    sep = " : " if fr else ": "
    row("Population", [
        [("big", n(c["pop18"], lang), "articles de RL" if fr else "RL papers", C18),
         ("p", f"ICML {v18['ICML 2018']}, NeurIPS {v18['NeurIPS 2018']}, |ICLR {v18['ICLR 2018']}"),
         ("small", "titre filtré |par la même expression |qu'en 2026" if fr else
          "title filtered |by the same expression |as in 2026")],
        [("big", n(c["pop26"], lang), f"sur {n(17836, lang)}" if fr else f"of {n(17836, lang)}", C26),
         ("p", f"ICLR {v26['ICLR 2026']}, ICML {v26['ICML 2026']}, |NeurIPS {v26['NeurIPS 2025']}"),
         ("small", "articles de RL, |titre filtré |par une expression régulière" if fr else
          "RL papers, |title filtered |by a regular expression")],
        [("rows", [(y_, n(tp[y_], lang)) for y_ in sorted(tp)], CTR),
         ("small", "articles de RL par année, |titres de modèles de langue |sautés" if fr else
          "RL papers per year, |language-model titles |skipped")],
    ], ("accent", "accent", "accent"))

    row("Tirage au sort" if fr else "Random draw", [
        [("pb", "Les 12 articles du départ |(6 ICML, 6 NeurIPS)" if fr else "The 12 initial papers |(6 ICML, 6 NeurIPS)"),
         ("p", (f"puis 38 tirés au sort |au prorata des congrès" + sep + f"|{c['new18']['ICML 2018']} ICML, "
                f"{c['new18']['NeurIPS 2018']} NeurIPS, |{c['new18']['ICLR 2018']} ICLR") if fr else
          (f"then 38 drawn at random |in proportion to each venue: |{c['new18']['ICML 2018']} ICML, "
           f"{c['new18']['NeurIPS 2018']} NeurIPS, |{c['new18']['ICLR 2018']} ICLR")),
         ("foot", "small", "aucun remplacement |à faire" if fr else "no replacement |needed"),
         ("foot", "gap", 3), ("foot", "mono", "random.Random(2018)")],
        [("pb", (f"50 tirés au sort |({c['sample26_v']['ICLR 2026']} ICLR, {c['sample26_v']['ICML 2026']} ICML, "
                 f"|{c['sample26_v']['NeurIPS 2025']} NeurIPS) ; |8 sans PDF libre remplacés") if fr else
          (f"50 drawn at random |({c['sample26_v']['ICLR 2026']} ICLR, {c['sample26_v']['ICML 2026']} ICML, "
           f"|{c['sample26_v']['NeurIPS 2025']} NeurIPS); |8 without a free PDF replaced")),
         ("chips", [("14 RL classique" if fr else "14 classical RL", C26),
                    ("27 grands modèles" if fr else "27 large models", SOFT),
                    ("9 théoriques" if fr else "9 theoretical", SOFT)]),
         ("gap", 8),
         ("p", (f"Complément : les {n(c['rest26'], lang)} autres |mélangés, {c['screened']} sautés |sur leur titre ; "
                f"|70 lus dans l'ordre ; |les 36 premiers |de RL classique entrent") if fr else
          (f"Top-up: the other {n(c['rest26'], lang)} |shuffled, {c['screened']} skipped |on their title; "
           f"|70 read in order; |the first 36 |classical RL papers enter")),
         ("gap", 3), ("foot", "mono", "random.Random(2026)")],
        [("p", "Par année, |les deux congrès mélangés ; |les 24 premiers articles |qui ont un PDF sont lus ; "
               "|on garde les 20 premiers |de RL classique |à expériences" if fr else
          "Per year, |both venues shuffled; |the first 24 papers |with a PDF are read; "
          "|the first 20 |classical RL papers |with experiments are kept"),
         ("foot", "small", "ICLR manque : |OpenReview refuse |les téléchargements |automatiques" if fr else
          "ICLR is missing: |OpenReview refuses |automated downloads"),
         ("foot", "gap", 3), ("foot", "mono", "random.Random(année)" if fr else "random.Random(year)")],
    ], ("plain", "plain", "plain"))

    row("Échantillon" if fr else "Sample", [
        [("big", "50", "articles" if fr else "papers", C18),
         ("p", "dont 48 |avec expériences" if fr else "48 of them |with experiments")],
        [("big", "50", "RL classique" if fr else "classical RL", C26),
         ("p", "14 du tirage, |36 du complément" if fr else "14 from the draw, |36 from the top-up")],
        [("big", "80", "articles" if fr else "papers", CTR),
         ("p", "20 par année : |2019, 2020, 2022, 2024" if fr else "20 per year: |2019, 2020, 2022, 2024")],
    ], ("sample", "sample", "sample"), arrows=False)
    return finish(f, y, T["source"])


def flux_sondage_2(lang):
    c = survey_counts()
    fr = lang == "fr"
    T = {
        "title": ("Chaque décision cite sa page ; doubles lectures |et contrôles la mettent à l'épreuve" if fr else
                  "Every decision quotes its page; double readings |and checks put it to the test"),
        "sub": ("Le sondage, seconde partie : de la lecture des trois échantillons aux comparaisons finales" if fr
                else "The survey, part two: from the reading of the three samples to the final comparisons"),
        "source": ("Sources : study/PROTOCOL.md (écarts 17 à 29), study/*.json, study/readers/, docs/conclusions.md"
                   if fr else "Sources: study/PROTOCOL-en.md (deviations 17 to 29), study/*.json, study/readers/, "
                              "docs/conclusions-en.md"),
        "desc": ("Seconde partie du diagramme de flux du sondage. Les trois échantillons sont lus par des agents de "
                 "modèle de langue, chaque décision avec une citation et sa page ; trente articles sont relus à "
                 "l'aveugle ; une harmonisation datée précède tout pourcentage ; deux contrôles suivent les "
                 "résultats ; deux comparaisons finales portent les verdicts." if fr else
                 "Part two of the survey's flow diagram. The three samples are read by language-model agents, each "
                 "decision with a quote and its page; thirty papers are read again blind; a dated harmonisation "
                 "comes before any percentage; two checks follow the results; two final comparisons carry the "
                 "verdicts."),
    }
    f = figure(T)
    s, L, W = f.s, f.L, f.W
    CW, G_, X = columns(f)
    mid = W / 2
    y = column_heads(f, f.top + 8, fr)
    for i in range(3):
        arrow(s, [(X[i] + CW / 2, y - 6), (X[i] + CW / 2, y + 10)])
    y += 12

    def band(label, split, last=False):
        """A full-width grey band holding one cell, or equal cells side by side."""
        nonlocal y
        stage(s, L, y + 10, W - 2 * L, label)
        y += 22
        pad, k = 14, len(split)
        cw = (W - 2 * L - 2 * pad - (k - 1) * 18) / k
        h = max(block(None, 0, 0, cw, it) for it in split) + 2 * pad - 2
        card(s, L, y, W - 2 * L, h, PANEL, None)
        for j, it in enumerate(split):
            xx = L + pad + j * (cw + 18)
            if j:
                s.line(xx - 9, y + pad, xx - 9, y + h - pad, RULE)
            block(s, xx, y + pad - 1, cw, it, PANEL)
        y += h
        if not last:
            arrow(s, [(mid, y + 3), (mid, y + 22)])
            y += 26

    band("Lecture" if fr else "Reading", [
        [("big", "38", "agents" if fr else "agents", INK),
         ("p", "de modèle de langue, |claude-opus-5-5 ; |13 articles finis |sur claude-opus-5" if fr else
          "language-model agents, |claude-opus-5-5; |13 papers finished |on claude-opus-5")],
        [("pb", "Le PDF entier, |annexes comprises" if fr else "The whole PDF, |appendices included"),
         ("p", "deux grilles : |Q1 à Q8 et X1 à X7, |puis Y1 à Y12" if fr else
          "two grids: |Q1 to Q8 and X1 to X7, |then Y1 to Y12")],
        [("pb", "Une citation |et sa page" if fr else "A quote |and its page"),
         ("p", "pour chaque décision, |dans study/codes/ |et codes_v2/" if fr else
          "for every decision, |in study/codes/ |and codes_v2/")],
    ])
    band("Double lecture à l'aveugle" if fr else "Blind double reading", [
        [("big", "10", "du 1er tirage" if fr else "first draw", C26),
         ("p", "127 décisions |sur 130 identiques |(grille 1)" if fr else "127 of 130 |decisions identical |(grid 1)")],
        [("big", "10", "ajoutés" if fr else "added", C18),
         ("p", "au moins 80 % |d'accord sur chacun |des 23 critères" if fr else
          "at least 80% |agreement on each |of the 23 criteria")],
        [("big", "10", "de 2019 à 2024" if fr else "2019 to 2024", CTR),
         ("p", "au moins 80 % |d'accord sur chacun |des 23 critères" if fr else
          "at least 80% |agreement on each |of the 23 criteria")],
    ])
    band("Harmonisation, avant tout pourcentage" if fr else "Harmonisation, before any percentage", [
        [("p", ("Des règles datées (écarts 17 à 19) |tranchent les cas ambigus : |80 codes changent, "
                "|chacun avec sa raison |dans study/overrides_v2.json, |pour les deux années.") if fr else
          ("Dated rules (deviations 17 to 19) |settle the ambiguous cases: |80 codes change, "
           "|each with its reason |in study/overrides_v2.json, |for both years."))],
    ])
    band("Contrôles, après les résultats" if fr else "Checks, after the results", [
        [("pb", "Recherche contre les « non »" if fr else "Search against the “no” decisions"),
         ("p", (f"{c['turned18'] + c['turned26']} décisions sur {c['no']} |passent à « oui » ; "
                f"|aucun verdict ne change") if fr else
          (f"{c['turned18'] + c['turned26']} of {c['no']} decisions |turn to “yes”; |no verdict changes"))],
        [("pb", "Sans les 13 articles |de claude-opus-5" if fr else "Without the 13 papers |of claude-opus-5"),
         ("p", "les verdicts tiennent, |sauf l'incertitude (X2), |p de Holm 0,07" if fr else
          "the verdicts hold, |except uncertainty (X2), |Holm p 0.07")],
    ], last=True)

    y0 = y
    y += 28
    w2 = 2 * CW + G_
    for xx in (L + w2 / 2, X[2] + CW / 2):
        arrow(s, [(xx, y0 + 3), (xx, y - 5)])
    stage(s, L, y + 10, W - 2 * L, "Comparaisons finales" if fr else "Final comparisons")
    y += 22
    A = [("pb", "Comparaison principale, à grille égale" if fr else "Main comparison, with the same grid"),
         ("p", ("48 articles expérimentaux de 2018 |contre 50 de RL classique de 2026, |mêmes grilles, mêmes lecteurs ; "
                "|Newcombe, Fisher, Holm.") if fr else
          ("48 experimental papers from 2018 |against 50 classical RL papers of 2026, |same grids, same readers; "
           "|Newcombe, Fisher, Holm."))]
    B = [("pb", "Trajectoire" if fr else "Trajectory"),
         ("p", "48, 4 × 20, 50 articles ; |Cochran-Armitage |sur cinq critères" if fr else
          "48, 4 × 20, 50 papers; |Cochran-Armitage |on five criteria")]
    pad = 14
    h = max(block(None, 0, 0, w2 - 2 * pad, A), block(None, 0, 0, CW - 2 * pad, B)) + 2 * pad - 2
    for xx, ww, it in ((L, w2, A), (X[2], CW, B)):
        card(s, xx, y, ww, h, PAPER, INK, 1.4)
        block(s, xx + pad, y + pad - 1, ww - 2 * pad, it)
    y += h
    return finish(f, y, T["source"])


# ---------------------------------------------------------------------------------------------------------------
# 2. The deviations, day by day


def deviations():
    """(lane, number, day or None) for every deviation of the three protocols, the day read from its own text."""
    out = []
    for lane, path in (("study", "study/PROTOCOL.md"), ("sim", "sim/SIM_PROTOCOL.md"),
                       ("llm", "sim/llm/LLM_PROTOCOL.md")):
        body = (ROOT / path).read_text(encoding="utf-8").split("## Écarts", 1)[1]
        for it in re.split(r"\n(?=\d+\. )", body):
            m = re.match(r"(\d+)\. ", it)
            if not m:
                continue
            d = re.search(r"(\d+)(?:er)? novembre 2026", it)
            out.append((lane, int(m[1]), int(d[1]) if d else None))
    return out


def frise_ecarts(lang):
    fr = lang == "fr"
    devs = deviations()
    lanes = ("study", "sim", "llm")
    lane_c = {"study": C26, "sim": CSIM, "llm": C18}
    lane_n = {"study": ("Sondage", "Survey"), "sim": ("Simulations", "Simulations"), "llm": ("GRPO", "GRPO")}
    counts = {ln: sum(1 for d in devs if d[0] == ln) for ln in lanes}
    total = len(devs)
    first2 = sum(1 for d in devs if d[2] is None or d[2] <= 9)
    assert (counts["study"], counts["sim"], counts["llm"]) == (33, 34, 20)
    last = max(d[2] for d in devs if d[2] is not None)
    assert all(d[2] is None or 8 <= d[2] <= last for d in devs)
    T = {
        "title": (f"{first2} des {total} écarts datent des deux premiers jours" if fr else
                  f"{first2} of the {total} deviations date from the first two days"),
        "sub": (f"Les trois protocoles et leurs écarts, jour par jour, du 8 au {last} novembre 2026" if fr else
                f"The three protocols and their deviations, day by day, from 8 to {last} November 2026"),
        "source": ("Sources : écarts de study/PROTOCOL.md, sim/SIM_PROTOCOL.md, sim/llm/LLM_PROTOCOL.md ; "
                   "historique git ; article de blog sur deraison.ai" if fr else
                   "Sources: deviations of study/PROTOCOL.md, sim/SIM_PROTOCOL.md, sim/llm/LLM_PROTOCOL.md; "
                   "git history; blog article on deraison.ai"),
        "desc": (f"Frise verticale, un jour par ligne du 8 au {last} novembre 2026, une colonne par protocole "
                 "(sondage, simulations, GRPO) et une colonne de jalons. Chaque écart est une pastille numérotée "
                 "sur le jour que son texte indique ; les écarts sans date, notés avant le premier commit, "
                 "sont des pastilles creuses sur la ligne du 8. L'article paraît le 21." if fr else
                 f"Vertical timeline, one day per row from 8 to {last} November 2026, one column per protocol "
                 "(survey, simulations, GRPO) and a column of milestones. Each deviation is a numbered dot on "
                 "the day its text gives; the undated deviations, recorded before the first commit, are hollow "
                 "dots on the row of the 8th. The article is published on the 21st."),
    }
    f = figure(T)
    s, L, W = f.s, f.L, f.W
    DW, LW, LG = 70, 142, 10
    R, P = 12.5, 28                              # dot radius, dot pitch
    lx = [L + DW + i * (LW + LG) for i in range(3)]
    mx = lx[2] + LW + 18
    MW = W - L - mx
    per = int((LW + (P - 2 * R)) // P)           # dots per line
    MS = {  # milestones per day: (French, English); every one from the protocols, README or git history
        8: [("Les trois protocoles, |avant toute lecture |et tout entraînement",
             "The three protocols, |before any reading |or training")],
        9: [("Premier commit, |6 h 07", "First commit, |6:07")],
        12: [("Les 12 essais GRPO |à trois graines finis", "The 12 GRPO runs |with three seeds done")],
        13: [("Les 40 essais CrossQ |finis : fin des |simulations prévues",
              "The 40 CrossQ runs |done: planned |simulations finished")],
        15: [("Dépôt public ; |consolidation écrite |avant tout essai", "Repository public; |consolidation written |before any run")],
        21: [("Fin des entraînements, |consolidation calculée", "Training finished, |consolidation computed"),
             ("Article publié |sur deraison.ai", "Article published |on deraison.ai")],
    }
    y = f.top + 4
    s.circle(L + 9, y - 5, 8, INK2)
    lab1 = "écart daté dans son texte" if fr else "deviation dated in its text"
    tx(s, L + 24, y, lab1, "sans", MIN, INK2)
    x2 = L + 24 + D.width(lab1, "sans", MIN) + 24
    s.circle(x2 + 8, y - 5, 7.3, PAPER, f' stroke="{INK2}" stroke-width="1.5"')
    tx(s, x2 + 23, y, "sans date : noté avant le premier commit, placé au 8" if fr else
       "undated: recorded before the first commit, placed on the 8th", "sans", MIN, INK2)
    y += 34
    for i, ln in enumerate(lanes):
        col = lane_c[ln]
        s.rect(lx[i], y - 15, LW, 4, col, rx=2)
        tx(s, lx[i], y + 6, lane_n[ln][0 if fr else 1], "sans7", 14.5, INK)
        tx(s, lx[i] + LW, y + 6, str(counts[ln]), "sans7", 14.5, col, "end")
    s.rect(mx, y - 15, MW, 4, INK, rx=2)
    tx(s, mx, y + 6, "Jalons" if fr else "Milestones", "sans7", 14.5, INK)
    y += 18
    wd_fr = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
    wd_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for di, day in enumerate(range(8, last + 1)):
        wd = datetime.date(2026, 11, day).weekday()
        cells = {ln: sorted([d for d in devs if d[0] == ln and (d[2] or 8) == day],
                            key=lambda d: (d[2] is not None, d[1])) for ln in lanes}
        nrows = max([math.ceil(len(v) / per) for v in cells.values()] + [0])
        ms = MS.get(day, [])
        mlines = sum(len(lines(m[0 if fr else 1], "sans", MIN, MW)) for m in ms)
        h = max(nrows * P + 8, mlines * 17 + (6 if len(ms) > 1 else 0) + 12, 32)
        if di % 2 == 0:
            s.rect(L - 6, y, W - 2 * L + 12, h, PANEL, rx=4)
        bg = PANEL if di % 2 == 0 else PAPER
        tx(s, L + 20, y + 21, str(day), "sans7", 16, INK, "end", bg=bg)
        tx(s, L + 26, y + 21, (wd_fr if fr else wd_en)[wd], "sans", MIN, SOFT, bg=bg)
        for i, ln in enumerate(lanes):
            col = lane_c[ln]
            for k, d in enumerate(cells[ln]):
                cx = lx[i] + R + (k % per) * P
                cy = y + 4 + R + (k // per) * P
                if d[2] is None:
                    s.circle(cx, cy, R - 0.8, PAPER, f' stroke="{col}" stroke-width="1.6"')
                    tx(s, cx, cy + 4.6, str(d[1]), "sans7", MIN, col, "middle", bg=PAPER)
                else:
                    s.circle(cx, cy, R, col)
                    tx(s, cx, cy + 4.6, str(d[1]), "sans7", MIN, PAPER, "middle", bg=col)
        yy = y + 21
        for j, m in enumerate(ms):
            pub = day == 21 and j == len(ms) - 1          # the publication, the last milestone
            if pub:
                yy += 6
                s.circle(mx - 9, yy - 4.5, 4.5, D.RED)
            for ln_ in lines(m[0 if fr else 1], "sans", MIN, MW):
                tx(s, mx, yy, ln_, "sans7" if pub else "sans5" if day in (15, 21) else "sans", MIN,
                   INK if day in (15, 21) else INK2, bg=bg)
                yy += 17
        y += h + 2
    return finish(f, y, T["source"])


# ---------------------------------------------------------------------------------------------------------------
# 3. The repository as a pipeline, in two figures: producing and analysing (architecture), then checking,
#    writing and rerunning (architecture-2)


def arch_frame(f, fr):
    """Legend and column heads shared by both halves. Returns (X, CW, y)."""
    s, L, W = f.s, f.L, f.W
    G_ = 12
    CW = (W - 2 * L - 2 * G_) / 3
    X = [L + i * (CW + G_) for i in range(3)]
    y = f.top + 4
    s.rect(L, y - 13, 24, 16, PANEL, rx=3)
    x = L + 32
    tx(s, x, y, "fichiers" if fr else "files", "sans", MIN, INK2)
    x += D.width("fichiers" if fr else "files", "sans", MIN) + 24
    s.rect(x, y - 13, 24, 16, PAPER, rx=3, extra=f' stroke="{RULE}" stroke-width="1"')
    tx(s, x + 32, y, "programmes" if fr else "programs", "sans", MIN, INK2)
    x += 32 + D.width("programmes" if fr else "programs", "sans", MIN) + 24
    x += pill(s, x, y - 16, "make") + 8
    tx(s, x, y, "cibles du Makefile" if fr else "Makefile targets", "sans", MIN, INK2)
    y += 32
    heads = (("Sondage", "Survey"), ("Simulations", "Simulations"), ("GRPO", "GRPO"))
    for i, col in enumerate((C26, CSIM, C18)):
        s.rect(X[i], y - 14, CW, 4, col, rx=2)
        tx(s, X[i], y + 7, heads[i][0 if fr else 1], "sans7", 14.5, INK)
    return X, CW, y + 14


class Levels:
    """Stacked levels of three cards, each under a small-capitals name with its make targets."""

    def __init__(self, f, X, CW, y):
        self.f, self.X, self.CW, self.y = f, X, CW, y

    def label(self, name, targets, note=None):
        s, L, W, y = self.f.s, self.f.L, self.f.W, self.y
        x = L + caps(s, L, y + 16, name) + 10
        for tg in targets:
            x += pill(s, x, y, tg) + 6
        right = W - L
        if note:
            tx(s, right, y + 16, note, "sans", MIN, SOFT, "end")
            right -= D.width(glue(note), "sans", MIN) + 10
        s.line(x + 4, y + 11.5, right, y + 11.5, GRID)

    def level(self, name, targets, cells, kind, arrows=True, note=None):
        s, X, CW = self.f.s, self.X, self.CW
        self.label(name, targets, note)
        self.y += 30
        pad = 11
        h = max(block(None, 0, 0, CW - 2 * pad, c) + 2 * pad - 2 for c in cells)
        for i, c in enumerate(cells):
            fill, stroke = (PANEL, None) if kind == "file" else (PAPER, RULE)
            card(s, X[i], self.y, CW, h, fill, stroke)
            block(s, X[i] + pad, self.y + pad - 1, CW - 2 * pad, c, fill)
        self.y += h
        if arrows:
            for i in range(3):
                arrow(s, [(X[i] + CW / 2, self.y + 3), (X[i] + CW / 2, self.y + 21)])
            self.y += 28


ARCH_DESC = ("Schéma du dépôt en six étages, sur deux figures : produire (entraînements et lecteurs), résultats bruts "
             "commités, analyses, fichiers JSON ; puis contrôles et tableaux, documents, et le chemin refait par "
             "make verify et l'intégration continue. Trois colonnes suivent le sondage, les simulations et le GRPO. "
             "Les cibles make sont des pastilles sombres.",
             "Diagram of the repository in six levels, over two figures: produce (training runs and readers), "
             "committed raw results, analyses, JSON files; then checks and tables, documents, and the path rerun by "
             "make verify and the continuous integration. Three columns follow the survey, the simulations and "
             "GRPO. Make targets are dark pills.")


def architecture(lang):
    fr = lang == "fr"
    T = {"title": ("Des essais aux fichiers JSON : |make analysis refait tout sans rien entraîner" if fr else
                   "From runs to JSON files: |make analysis redoes it all without training anything"),
         "sub": ("Le dépôt pineau-rl, première partie : produire les données, puis les analyser" if fr else
                 "The pineau-rl repository, part one: producing the data, then analysing it"),
         "desc": ARCH_DESC[0 if fr else 1]}
    f = figure(T)
    s, L, W = f.s, f.L, f.W
    X, CW, y = arch_frame(f, fr)
    lv = Levels(f, X, CW, y)
    lv.level("Produire" if fr else "Produce", [], [
        [("pb", "Agents lecteurs" if fr else "Reading agents"),
         ("small", "lisent les 521 PDF |de study/pdfs.csv, |chacun vérifié |par son empreinte |SHA-256" if fr else
          "read the 521 PDFs |of study/pdfs.csv, |each checked |by its SHA-256 digest")],
        [("code", "sim/jobs*.txt"), ("code", "sim/drive.sh"), ("code", "sim/queue.sh"), ("code", "sim/run.py"),
         ("small", "une ligne de file, |un entraînement" if fr else "one queue line, |one training run")],
        [("code", "sim/llm/grpo.py"), ("code", "night.sh, cpu.sh"),
         ("small", "GRPO écrit à la main, |un essai par graine" if fr else "hand-written GRPO, |one run per seed")],
    ], "prog", note="aucune cible make n'entraîne" if fr else "no make target trains anything")
    lv.level("Résultats bruts, commités" if fr else "Raw results, committed", [], [
        [("code", "study/codes/"), ("code", "study/codes_v2/"),
         ("small", "un JSON par article |et par lecteur : |décision, citation, page" if fr else
          "one JSON per paper |and per reader: |decision, quote, page")],
        [("code", "sim/results/"), ("code", "sim/logs/"),
         ("small", "une courbe d'évaluation |(CSV) par essai, |journaux, attempts.jsonl" if fr else
          "one evaluation curve |(CSV) per run, |logs, attempts.jsonl")],
        [("code", "sim/llm/results/"),
         ("small", "les mesures de chaque essai, |au départ |et après 100 pas" if fr else
          "the measures of each run, |at the start |and after 100 steps")],
    ], "file")
    lv.level("Analyser" if fr else "Analyse", ["make analysis"], [
        [("code", "study/*.py"),
         ("small", "9 scripts : |Wilson, Newcombe, |Fisher, Holm, |Cochran-Armitage" if fr else
          "9 scripts: |Wilson, Newcombe, |Fisher, Holm, |Cochran-Armitage")],
        [("code", "sim/analysis/*.py"),
         ("small", "16 à dix graines, |13 de plus |pour l'écart 12" if fr else "16 with ten seeds, |13 more |for deviation 12")],
        [("code", "sim/llm/summary.py"),
         ("small", "gains par graine, |intervalle bootstrap" if fr else "gains per seed, |bootstrap interval")],
    ], "prog")
    lv.level("Résultats JSON" if fr else "JSON results", [], [
        [("code", "study/*.json")], [("code", "sim/analysis/*.json")], [("code", "sim/llm/results/*.json")],
    ], "file", arrows=False)
    # the shared package, under the whole pipeline
    y = lv.y + 30
    stage(s, L, y, W - 2 * L, "Le paquet commun" if fr else "The shared package")
    y += 14
    pad = 14
    left = [("code", "src/pineau_rl/"),
            ("p", "importé par chaque analyse |ci-dessus, par les contrôles |et par les tests" if fr else
             "imported by every analysis |above, by the checks |and by the tests")]
    mods = [("stats.py", "Wilson, Newcombe, Fisher, Holm" if fr else "Wilson, Newcombe, Fisher, Holm"),
            ("bootstrap.py", "IQM, intervalles rliable" if fr else "IQM, rliable intervals"),
            ("runs.py", "format des essais" if fr else "run format"),
            ("grid.py", "grille de lecture" if fr else "reading grid"),
            ("fmt.py", "format des nombres" if fr else "number format")]
    lw = 250
    h = max(block(None, 0, 0, lw, left), len(mods) * 20) + 2 * pad - 2
    card(s, L, y, W - 2 * L, h, PAPER, INK, 1.4)
    block(s, L + pad, y + pad - 1, lw, left)
    xm = L + pad + lw + 20
    s.line(xm - 10, y + pad, xm - 10, y + h - pad, RULE)
    for i, (m, d) in enumerate(mods):
        yy = y + pad + 13 + i * 20
        tx(s, xm, yy, m, "mono", MIN, INK)
        tx(s, xm + 120, yy, d, "sans", MIN, SOFT)
    y += h
    return finish(f, y, "Sources : Makefile, README.md, pyproject.toml" if fr else
                  "Sources: Makefile, README.md, pyproject.toml")


def architecture_2(lang):
    fr = lang == "fr"
    T = {"title": ("Des fichiers JSON aux documents, |un chemin refait à chaque push" if fr else
                   "From JSON files to documents, |a path rerun at every push"),
         "sub": ("Le dépôt pineau-rl, seconde partie : vérifier les nombres, écrire les documents, tout refaire" if fr
                 else "The pineau-rl repository, part two: checking the numbers, writing the documents, redoing it all"),
         "desc": ARCH_DESC[0 if fr else 1]}
    f = figure(T)
    s, L, W = f.s, f.L, f.W
    X, CW, y = arch_frame(f, fr)
    lv = Levels(f, X, CW, y)
    lv.level("Résultats JSON, de make analysis" if fr else "JSON results, from make analysis", [], [
        [("code", "study/*.json")], [("code", "sim/analysis/*.json")], [("code", "sim/llm/results/*.json")],
    ], "file", arrows=False)
    # a bus gathers the three JSON families: every checker below reads from all of them
    y = lv.y
    bus = y + 12
    for i in range(3):
        s.line(X[i] + CW / 2, y + 3, X[i] + CW / 2, bus, ARROW, 1.3)
    s.line(X[0] + CW / 2, bus, X[2] + CW / 2, bus, ARROW, 1.3)
    for i in range(3):
        arrow(s, [(X[i] + CW / 2, bus), (X[i] + CW / 2, bus + 16)])
    lv.y = bus + 24
    lv.level("Vérifier, mettre en tableaux" if fr else "Check, tabulate", ["make check"], [
        [("code", "docs/check_numbers.py"),
         ("small", "188 nombres clés |des deux textes" if fr else "188 key numbers |of both texts")],
        [("code", "article/"), ("code", "check_article.py"),
         ("small", "chaque nombre |de l'article de blog" if fr else "every number |of the blog article")],
        [("code", "report/tools/"), ("code", "tables.py"),
         ("small", "les tableaux du rapport, |lancé par make report" if fr else "the report's tables, |run by make report")],
    ], "prog")
    lv.level("Documents", ["make docs", "make report"], [
        [("code", "docs/conclusions.md"), ("code", "conclusions-en.md"),
         ("small", "en PDF et DOCX ; |figures : make figures" if fr else "as PDF and DOCX; |figures: make figures")],
        [("code", "article/fr.txt"), ("code", "article/en.txt"),
         ("small", "la page de deraison.ai" if fr else "the deraison.ai page")],
        [("code", "report/rapport.pdf"), ("code", "report-en.pdf"),
         ("small", "figures : tools/figures.py" if fr else "figures: tools/figures.py")],
    ], "file", arrows=False)
    y = lv.y + 30
    stage(s, L, y, W - 2 * L, "Refaire le chemin" if fr else "Rerun the path")
    y += 14
    pad = 14
    bw = (W - 2 * L - 16) / 2
    entries = [("make verify", ("analysis, check, test, |puis git diff : |chaque JSON revient |à l'octet près" if fr
                                else "analysis, check, test, |then git diff: |every JSON comes back |byte for byte")),
               ("make verify-head", ("la même chose |dans un export neuf |du dernier commit" if fr else
                                     "the same |in a fresh export |of the last commit")),
               ("make test", ("tests/ sur |src/pineau_rl/" if fr else "tests/ on |src/pineau_rl/"))]
    tw = bw - 2 * pad
    hs = [22 + 6 + block(None, 0, 0, tw, [("p", e[1])]) for e in entries]
    left_h = sum(hs) + 10 * (len(entries) - 1) + 2 * pad - 2
    right = [("code", ".github/workflows/"), ("code", "verify.yml"), ("gap", 6),
             ("p", ("À chaque push : |make install, test, |analysis, check, |puis chaque valeur |comparée au commit "
                    "|(tools/compare_results.py).") if fr else
              ("At every push: |make install, test, |analysis, check, |then every value |compared with the commit "
               "|(tools/compare_results.py).")),
             ("gap", 3.4),
             ("p", ("Linux, Python 3.11.18 : |à 1e-12 près ; |macOS : à l'octet près ; |image Docker : |make test check.")
              if fr else ("Linux, Python 3.11.18: |to 1e-12; |macOS: byte for byte; |Docker image: |make test check."))]
    right_h = block(None, 0, 0, tw, right) + 2 * pad - 2
    h = max(left_h, right_h)
    card(s, L, y, bw, h, PANEL, None)
    yy = y + pad
    for (t, d), hh in zip(entries, hs):
        pill(s, L + pad, yy, t)
        block(s, L + pad, yy + 26, tw, [("p", d)], PANEL)
        yy += hh + 10
    xr = L + bw + 16
    card(s, xr, y, bw, h, INK, None)
    yy = y + pad + 2.1           # its first line shares the baseline of the make verify pill
    for it in right:
        if it[0] == "gap":
            yy += it[1]
            continue
        face, size, _, lhh = STY[it[0]]
        for ln in lines(it[1], face, size, tw):
            tx(s, xr + pad, yy + lhh * 0.5 + size * 0.36, ln, face, size,
               PAPER if it[0] == "code" else "#D5D8DD", bg=INK)
            yy += lhh
    y += h
    return finish(f, y, "Sources : Makefile, README.md, .github/workflows/verify.yml" if fr else
                  "Sources: Makefile, README.md, .github/workflows/verify.yml")


# ---------------------------------------------------------------------------------------------------------------

FIGS = (("flux-sondage", flux_sondage), ("flux-sondage-2", flux_sondage_2), ("frise-ecarts", frise_ecarts),
        ("architecture", architecture), ("architecture-2", architecture_2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGS:
        for lang in LANGS:
            (OUT / f"{name}-{lang}.svg").write_text(fn(lang), encoding="utf-8")
    print("diagrams: " + ", ".join(name for name, _ in FIGS) + " (fr, en)")


if __name__ == "__main__":
    main()
