"""New data figures of the technical report, drawn by hand in the house style (article/figures/draw.py).

Eight figures, French and English, each read from the project's result files and nothing else:
    courbes-apprentissage   sim/results/<algo>/<task>/seed0..9.csv      (evaluation curves, IQM and its band)
    forest-criteres         study/extension_stats.json                  (2018 against 2026, Newcombe intervals)
    accord-lecteurs         study/agree_v2.json, study/audit_stats.json (blind double readings)
    e5-graines              sim/analysis/e5.json, e5_s20.json           (seeds needed to recover the ranking)
    e7-carte                sim/analysis/e7.json, e7_s20.json           (share of score kept, modified physics)
    dose-carte              sim/analysis/dose.json, dose_s20.json       (E7 at twelve strengths)
    b1-distribution         sim/results/{trpo,ppo_sb3}/HalfCheetah-v5   (|t| over the draws of b1_trpo.py and
                                                                         b1_script.py, recomputed, checked against
                                                                         sim/analysis/b1_trpo.json, b1_script.json)
    grpo-courbes            sim/llm/results/<model>/mul2/<reward>/seed<k>.jsonl
Writes report/figures/src/<name>-<lang>.svg, then report/figures/<name>-<lang>.pdf (rsvg-convert), and runs
`sprezzature-figures check` on each SVG. Standard library and numpy only; the same input gives the same bytes.
Run from anywhere:  python3 report/tools/new_figures.py [name ...]
"""
import csv, json, math, re, subprocess, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "article" / "figures"))
import draw  # noqa: E402
from draw import (Fig, INK, INK2, MUTED, RULE, GRID, PANEL, PAPER, RED, GREEN, ALGO_C, tint, width, wrap, num,  # noqa: E402
                  pct, ticks, spread)

SRC = ROOT / "report" / "figures" / "src"
OUT = ROOT / "report" / "figures"
J = lambda p: json.load(open(ROOT / p, encoding="utf-8"))

ALGOS = ["sac", "crossq", "ppo_sb3", "ppo_sbx"]
NAME = {"sac": "SAC", "crossq": "CrossQ", "ppo_sb3": "PPO (PyTorch)", "ppo_sbx": "PPO (JAX)"}
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
TASK = lambda t: t.replace("-v5", "")
FINAL = {"ppo_sb3": 1_000_000, "ppo_sbx": 1_000_000, "sac": 200_000, "crossq": 200_000}
DARK = "#55637A"  # the neutral ink of draw.py's beeswarm


class RFig(Fig):
    """draw.Fig at 760 px, with the title wrapped 7% narrower. rsvg-convert, which makes the report's PDF, ignores the
    embedded woff2 subsets and takes the installed fonts: Roboto Serif 600 then comes out as Roboto Serif Bold, about
    6% wider than the metrics of draw.py. The narrower wrap keeps every title line inside the canvas in the PDF."""

    SLACK = 1.07

    def __init__(self, title, subtitle, accent=INK):
        Fig.__init__(self, False, "", "", accent)  # canvas, margins and the accent rule
        self.s = draw.Svg(self.W)
        self.title, self.subtitle = title.replace("|", " ").replace("  ", " "), subtitle  # '|' only guides the wrap
        s, L = self.s, self.L
        s.rect(L, 22, 36, 4, accent, rx=2)
        tsize, ssize = 25, 15
        y = 22 + 4 + tsize + 12
        for ln in wrap(title, "serif", tsize, (self.W - 2 * L) / self.SLACK):
            assert width(ln, "serif", tsize) * self.SLACK <= self.W - 2 * L, f"title line too wide for the PDF: {ln}"
            s.text(L, y, ln, "serif", tsize)
            y += tsize * 1.22
        y += 2
        for ln in wrap(subtitle, "sans", ssize, self.W - 2 * L):
            s.text(L, y - 4, ln, "sans", ssize, INK2)
            y += ssize * 1.4
        self.top = y + 14


def _finish(self, y, source):
    """draw.Fig.finish with the source line at self.src_size px (draw.py uses 11.5): the same rule, source, logo and
    site name, so that a figure printed at text width keeps every word at 7.5 pt or more."""
    size = getattr(self, "src_size", 11.5)
    if size == 11.5:
        return Fig.finish(self, y, source)
    s, L = self.s, self.L
    y += 24
    s.line(L, y - 15, self.W - L, y - 15, GRID)
    site, bsize = "Deraison.ai", size + 1.5
    lh = bsize * 1.05
    lw = lh * draw.LOGO_VB[2] / draw.LOGO_VB[3]
    sw = width(site, "brand", bsize)
    lines = wrap(source, "sans", size, self.W - 2 * L - sw - lw - 26)
    for i, ln in enumerate(lines):
        s.text(L, y + i * size * 1.35, ln, "sans", size, MUTED)
    s.text(self.W - L, y, site, "brand", bsize, INK, "end")
    lx, ly = self.W - L - sw - 5 - lw, y - bsize * 0.72 - (lh - bsize * 0.72) / 2
    s.add(f'<svg x="{lx:.1f}" y="{ly:.1f}" width="{lw:.1f}" height="{lh:.1f}" viewBox="0 0 {draw.LOGO_VB[2]} '
          f'{draw.LOGO_VB[3]}" aria-hidden="true">{draw.LOGO_BODY}</svg>')
    h = y + (len(lines) - 1) * size * 1.35 + 16
    return s.render(h, self.title, self.desc)


RFig.finish = _finish


def rnd(x):
    """Round half away from zero, as a reader does."""
    return int(math.floor(abs(x) + 0.5)) * (1 if x >= 0 else -1)


def iqm(x):
    """Interquartile mean as scipy's trim_mean(x, 0.25), which rliable uses: cut int(0.25 n) runs at each end."""
    x = np.sort(np.asarray(x, dtype=float), axis=-1)
    k = int(0.25 * x.shape[-1])
    return x[..., k:x.shape[-1] - k].mean(-1)


def text_lines(s, x, y, txt, face, size, fill, maxw, lh=None, anchor="start", halo=PAPER):
    """Wrapped text, one sense group per line where '|' marks them. Returns the y below the last line."""
    lh = lh or size * 1.35
    for i, ln in enumerate(wrap(txt, face, size, maxw)):
        s.text(x, y + i * lh, ln, face, size, fill, anchor, halo=halo)
    return y + len(wrap(txt, face, size, maxw)) * lh


def back(s, n):
    """Move the last n drawn parts to the back of the canvas (under everything drawn before)."""
    moved = s.parts[-n:]
    del s.parts[-n:]
    s.parts[:0] = moved


# ---------------------------------------------------------------------------------------------------------------
# 1. Learning curves: 4 programs x 4 tasks, the ten seeds faint, the IQM bold with its 95% band.

def curves_data():
    rng = np.random.default_rng(2026)
    D = {}
    for a in ALGOS:
        for t in TASKS:
            runs = []
            for s in range(10):
                with open(ROOT / f"sim/results/{a}/{t}/seed{s}.csv", newline="") as f:
                    rows = list(csv.DictReader(f))
                assert int(rows[-1]["step"]) == FINAL[a], (a, t, s)
                runs.append([(int(r["step"]), float(r["eval_mean"])) for r in rows])
            steps = [p[0] for p in runs[0]]
            M = np.array([[p[1] for p in r] for r in runs])  # seeds x points
            idx = rng.integers(0, 10, (2000, 10))
            boot = iqm(M[idx].transpose(2, 0, 1))  # points x draws
            D[(a, t)] = dict(steps=steps, M=M, iqm=iqm(M.T), lo=np.percentile(boot, 2.5, axis=1),
                             hi=np.percentile(boot, 97.5, axis=1))
    e2 = J("sim/analysis/e2.json")["tasks"]
    for a in ALGOS:  # the IQM at the budget is E2's, to the unit
        for t in TASKS:
            assert abs(D[(a, t)]["iqm"][-1] - e2[t]["iqm"][a]) < 1e-6, (a, t)
    return D, {t: e2[t]["order"][0] for t in TASKS}


YMAX = {"HalfCheetah-v5": (8000, 2000), "Hopper-v5": (4000, 1000), "Walker2d-v5": (6000, 2000), "Swimmer-v5": (150, 50)}


def courbes_apprentissage(lang):
    fr = lang == "fr"
    D, lead = curves_data()
    f = RFig("D'une tâche à l'autre, le programme en tête change" if fr else
            "The leading program changes from task to task",
            ("Score d'évaluation au fil de l'entraînement, par programme et par tâche. Trait fin : une graine aléatoire. "
             "Trait épais : moyenne interquartile des dix graines, avec sa bande à 95 %.") if fr else
            ("Evaluation score along training, per program and task. Thin line: one random seed. "
             "Thick line: interquartile mean of the ten seeds, with its 95% band."), INK)
    f.src_size = 13
    s, L, W = f.s, f.L, f.W
    T = 13  # the smallest text: 13 px prints at 7.5 pt at text width
    yl = 44  # room for the vertical scale left of each panel
    gx = 10
    cw = (W - 2 * L - 3 * gx) / 4
    pw = cw - yl
    ph = 124
    top = f.top + 54
    Y0 = [top]
    for i in range(1, 4):  # x labels only under the second and fourth rows, the last of each budget
        Y0.append(Y0[-1] + ph + (66 if i == 2 else 42))
    for j, t in enumerate(TASKS):
        s.text(L + j * (cw + gx) + yl, top - 50, TASK(t), "sans7", 15, INK)
    for i, a in enumerate(ALGOS):
        col = ALGO_C[NAME[a]]
        y0 = Y0[i]
        budget = num(FINAL[a] / 1e6, lang, 1 if FINAL[a] < 1e6 else 0)
        s.text(L, y0 - 26, NAME[a], "sans7", 14, col)
        s.text(L + width(NAME[a], "sans7", 14) + 8, y0 - 26,
               (f"{budget} million de pas" if fr else f"{budget} million steps"), "sans", T, INK2)
        for j, t in enumerate(TASKS):
            d = D[(a, t)]
            x0 = L + j * (cw + gx) + yl
            x1 = x0 + pw
            ymax = YMAX[t][0]
            X = lambda u: x0 + u / FINAL[a] * (x1 - x0)
            Y = lambda u: y0 + ph - max(min(u, ymax), -ymax * 0.06) / ymax * ph
            if lead[t] == a:  # the leader of the task on a tinted ground
                s.rect(x0 - 3, y0 - 2, pw + 6, ph + 4, tint(col, 0.9), rx=4)
            for q in range(5):  # grid at quarters, labels at the half and the top
                tk = ymax * q / 4
                s.line(x0, Y(tk), x1, Y(tk), RULE if q == 0 else (PAPER if lead[t] == a else GRID), 1)
                if q in (2, 4):  # no zero label: every baseline is zero, said in the note
                    s.text(x0 - 5, Y(tk) + 4.5, num(tk, lang), "mono", T, MUTED, "end")
            for frac in (0.5, 1):
                xv = X(FINAL[a] * frac)
                s.line(xv, y0 + ph, xv, y0 + ph + 3, RULE, 1)
                if i in (1, 3) and frac == 1 and j == 0:  # one budget label per pair of rows
                    lab = num(FINAL[a] * frac / 1e6, lang, 1 if FINAL[a] * frac < 1e6 else 0) + " M"
                    s.text(xv, y0 + ph + 18, lab, "mono", T, MUTED, "end" if frac == 1 else "middle")
            st = d["steps"]
            band = (" ".join(f"{'M' if k == 0 else 'L'}{X(u):.1f},{Y(v):.1f}" for k, (u, v) in enumerate(zip(st, d["hi"])))
                    + " " + " ".join(f"L{X(u):.1f},{Y(v):.1f}" for u, v in reversed(list(zip(st, d["lo"])))) + " Z")
            s.add(f'<path d="{band}" fill="{tint(col, 0.78)}" fill-opacity="0.85"/>')
            for row in d["M"]:
                s.path(" ".join(f"{'M' if k == 0 else 'L'}{X(u):.1f},{Y(v):.1f}" for k, (u, v) in enumerate(zip(st, row))),
                       tint(col, 0.45), 0.8, extra=' stroke-opacity="0.9"')
            s.path(" ".join(f"{'M' if k == 0 else 'L'}{X(u):.1f},{Y(v):.1f}" for k, (u, v) in enumerate(zip(st, d["iqm"]))),
                   col, 2.6)
            s.circle(X(st[-1]), Y(d["iqm"][-1]), 3.4, col, f' stroke="{PAPER}" stroke-width="1.2"')
            best = lead[t] == a
            v = d["iqm"][-1]
            label = num(v, lang)
            s.text(x1, y0 - 6, label, "sans7", 14 if best else T, col if best else INK2, "end")
            if best:
                tag = "1er" if fr else "1st"
                tw = width(tag, "sans7", T) + 8
                lx = x1 - width(label, "sans7", 14) - 6 - tw
                s.rect(lx, y0 - 20, tw, 17, col, rx=3)
                s.text(lx + tw / 2, y0 - 6.5, tag, "sans7", T, PAPER, "middle", halo=col)
    y = Y0[3] + ph + 52
    note = ("Nombre au-dessus de chaque panneau : moyenne interquartile au dernier pas, celle du classement ; "
            "fond teinté pour le premier de la tâche. Échelle verticale commune par tâche, partant de zéro. "
            "SAC et CrossQ s'entraînent 0,2 million de pas, PPO un million.") if fr else \
           ("Number above each panel: interquartile mean at the last step, the one the ranking uses; "
            "tinted ground for the leader of the task. One vertical scale per task, starting at zero. "
            "SAC and CrossQ train for 0.2 million steps, PPO for one million.")
    y = text_lines(s, L, y, note, "sans", T, INK2, W - 2 * L, 17.5)
    f.desc = ("Seize panneaux, quatre programmes sur quatre tâches. Les dix graines de chaque programme s'écartent "
              "nettement ; la moyenne interquartile finale classe SAC premier sur HalfCheetah, PPO (JAX) sur Hopper "
              "et Swimmer, CrossQ sur Walker2d.") if fr else \
             ("Sixteen panels, four programs on four tasks. The ten seeds of each program spread widely; the final "
              "interquartile mean ranks SAC first on HalfCheetah, PPO (JAX) on Hopper and Swimmer, CrossQ on Walker2d.")
    src = ("Données : sim/results, graines 0 à 9 ; bande : bootstrap percentile de la moyenne interquartile "
           "(numpy, 2 000 tirages, graine 2026)") if fr else \
          ("Data: sim/results, seeds 0 to 9; band: percentile bootstrap of the interquartile mean "
           "(numpy, 2,000 draws, seed 2026)")
    return f.finish(y - 8, src)


# ---------------------------------------------------------------------------------------------------------------
# 2. Forest plot of the survey: every criterion, our reading of 2018 against classical RL of 2026.

CRIT = {"fr": {"Q2": "Réseaux de neurones (Q2)", "Q3": "Réglages de la méthode (Q3)", "Q4": "Réglages des références (Q4)",
               "Q5": "Code en lien (Q5)", "Q6": "Choix des réglages (Q6)", "Q7": "Évaluation à part (Q7)",
               "Q8": "Test statistique (Q8)", "X2": "Incertitude (X2)", "X3": "Meilleurs sur N (X3)",
               "X4": "Références réglées (X4)", "X7": "Calcul chiffré (X7)", "Y1": "Mesure définie (Y1)",
               "Y2": "Barres d'erreur définies (Y2)", "Y3": "Plusieurs tâches (Y3)", "Y4": "Tâche perdue montrée (Y4)",
               "Y5": "Code des références (Y5)", "Y6": "Exclusions dites (Y6)", "Y7": "Versions des bancs (Y7)",
               "Y8": "Généralisation (Y8)", "Y9": "Balayage montré (Y9)", "Y10": "Dépendances (Y10)",
               "Y11": "Type d'incertitude (Y11)", "Y12": "Outils récents (Y12)"},
        "en": {"Q2": "Neural networks (Q2)", "Q3": "Method settings (Q3)", "Q4": "Baseline settings (Q4)",
               "Q5": "Code linked (Q5)", "Q6": "Tuning method (Q6)", "Q7": "Held-out evaluation (Q7)",
               "Q8": "Statistical test (Q8)", "X2": "Uncertainty (X2)", "X3": "Best of N (X3)",
               "X4": "Baselines tuned (X4)", "X7": "Compute quantified (X7)", "Y1": "Measure defined (Y1)",
               "Y2": "Error bars defined (Y2)", "Y3": "Several tasks (Y3)", "Y4": "A lost task shown (Y4)",
               "Y5": "Baseline code (Y5)", "Y6": "Exclusions stated (Y6)", "Y7": "Benchmark versions (Y7)",
               "Y8": "Generalisation (Y8)", "Y9": "Sweep shown (Y9)", "Y10": "Dependencies (Y10)",
               "Y11": "Uncertainty type (Y11)", "Y12": "Recent tools (Y12)"}}


def forest_criteres(lang):
    fr = lang == "fr"
    rows = J("study/extension_stats.json")["rows"]
    rows = sorted(rows, key=lambda r: -r["classic_vs_ours2018"]["diff"])
    holm = [r["k"] for r in rows if r["classic_vs_ours2018"]["p_holm"] < 0.05 and r["k"] != "Q2"]
    assert len(holm) == 4, holm
    f = RFig("À grille égale, quatre pratiques progressent nettement entre 2018 et 2026" if fr else
            "Read with the same grid, four practices clearly rose between 2018 and 2026",
            ("Part des articles qui satisfont chaque critère, lus avec les mêmes grilles par les mêmes lecteurs : "
             "48\u00a0articles de 2018, 50\u00a0de RL classique en 2026. À droite, l'écart et son intervalle de Newcombe à 95 %.")
            if fr else
            ("Share of papers meeting each criterion, read with the same grids by the same readers: "
             "48\u00a0papers of 2018, 50\u00a0of classical RL in 2026. On the right, the gap and its 95% Newcombe interval."),
            GREEN)
    s, L, W = f.s, f.L, f.W
    lab_w = 196
    xa0, xa1 = L + lab_w, L + lab_w + 210
    xb0, xb1 = xa1 + 44, W - L - 40
    dlo, dhi = -30, 60
    XA = lambda u: xa0 + u * (xa1 - xa0)
    XB = lambda u: xb0 + (u * 100 - dlo) / (dhi - dlo) * (xb1 - xb0)
    rh = 23
    top = f.top + 44
    # column heads and the key
    s.text(xa0, top - 40, "Part des articles" if fr else "Share of papers", "sans7", 12.5, INK)
    kx = xa0
    s.circle(kx + 5, top - 22, 4.5, PAPER, f' stroke="{INK2}" stroke-width="1.6"')
    s.text(kx + 14, top - 18, "2018", "sans5", 11.5, INK2)
    kx += 14 + width("2018", "sans5", 11.5) + 14
    s.circle(kx + 5, top - 22, 5, INK)
    s.text(kx + 14, top - 18, "2026", "sans5", 11.5, INK2)
    s.text(xb0, top - 40, "Écart 2026 moins 2018, en points" if fr else "Gap, 2026 minus 2018, in points", "sans7", 12.5, INK)
    s.rect(xb0, top - 28, 14, 10, tint(GREEN, 0.82), rx=2)
    s.text(xb0 + 20, top - 18, "passe la correction de Holm" if fr else "passes the Holm correction", "sans5", 11.5, INK2)
    bottom = top + len(rows) * rh
    for i, r in enumerate(rows):
        k = r["k"]
        if k in holm:
            s.rect(L - 6, top + i * rh + 1, W - 2 * L + 12, rh - 2, tint(GREEN, 0.86), rx=4)
    for tk in ticks(0, 1, 0.25):
        s.line(XA(tk), top - 4, XA(tk), bottom, RULE if tk == 0 else GRID)
        s.text(XA(tk), bottom + 15, pct(tk * 100, lang), "mono", 10.5, MUTED, "middle")
    for tk in ticks(dlo, dhi, 15):
        s.line(XB(tk / 100), top - 4, XB(tk / 100), bottom, INK2 if tk == 0 else GRID, 1.3 if tk == 0 else 1)
        s.text(XB(tk / 100), bottom + 15, num(tk, lang, sign=True) if tk else "0", "mono", 10.5, MUTED, "middle")
    for i, r in enumerate(rows):
        k, c = r["k"], r["classic_vs_ours2018"]
        y = top + i * rh + rh / 2
        hot = k in holm
        half = (not hot) and k != "Q2" and c["lo"] > 0
        bg = tint(GREEN, 0.86) if hot else PAPER
        s.text(xa0 - 12, y + 4.3, CRIT[lang][k], "sans7" if hot else "sans", 12.5, INK if hot else INK2, "end", halo=bg)
        p18 = r["ours2018"][0] / r["ours2018"][1]
        p26 = r["classic2026"][0] / r["classic2026"][1]
        lc = GREEN if hot else (tint(GREEN, 0.35) if half else RULE)
        s.line(XA(p18), y, XA(p26), y, lc, 3 if hot else 2.2)
        s.circle(XA(p18), y, 4.3, PAPER, f' stroke="{INK2}" stroke-width="1.6"')
        s.circle(XA(p26), y, 5, INK if hot else INK2)
        col = GREEN if hot else ("#5FA77D" if half else "#8E959F")
        s.line(XB(c["lo"]), y, XB(c["hi"]), y, col, 3 if hot else 2.2, ' stroke-linecap="round"')
        s.circle(XB(c["diff"]), y, 5.5 if hot else 4.5, col, f' stroke="{bg}" stroke-width="1.6"')
        v = rnd(c["diff"] * 100)
        s.text(XB(c["hi"]) + 7, y + 4, num(v, lang, sign=True), "sans7" if hot else "sans5", 11.5,
               INK if hot else INK2, halo=bg)
    y = bottom + 34
    note = ("Intervalle qui évite zéro sans passer la correction de Holm : Q6 et Y12 (vert pâle). "
            "Pour X3, une baisse est un progrès. Q2 décrit la méthode, pas le compte rendu.") if fr else \
           ("Interval clear of zero without passing the Holm correction: Q6 and Y12 (pale green). "
            "For X3, a fall is progress. Q2 describes the method, not the reporting.")
    y = text_lines(s, L, y, note, "sans", 12, INK2, W - 2 * L, 16)
    f.desc = ("Vingt-trois critères classés par écart. Le code en lien, le balayage montré, le calcul chiffré et "
              "l'incertitude rapportée progressent et passent la correction de Holm ; les autres intervalles "
              "croisent zéro ou l'évitent de justesse.") if fr else \
             ("Twenty-three criteria sorted by gap. Code linked, sweep shown, compute quantified and uncertainty "
              "reported rise and pass the Holm correction; the other intervals cross zero or barely avoid it.")
    return f.finish(y - 8, "Données : study/extension_stats.json, différence de Newcombe, test exact de Fisher, correction de Holm"
                    if fr else "Data: study/extension_stats.json, Newcombe difference, Fisher's exact test, Holm correction")


# ---------------------------------------------------------------------------------------------------------------
# 3. Agreement between the blind double readings.

def accord_lecteurs(lang):
    fr = lang == "fr"
    a = J("study/agree_v2.json")
    g = J("study/audit_stats.json")["agreement"]
    crit = ["Q%d" % i for i in range(2, 9)] + ["X2", "X3", "X4", "X7"] + ["Y%d" % i for i in range(1, 13)]
    G = {k: dict(n=v["n"], same=v["same"], kappa=v["kappa"]) for k, v in g.items() if k in crit}
    groups = [("G", G)] + [(k, {c: dict(n=v["n"], same=rnd(v["n"] * v["agree"]), kappa=v["kappa"])
                                for c, v in a[k]["criteria"].items()}) for k in ("G2", "R2", "R3")]
    tot = sum(v["n"] for _, d in groups for v in d.values())
    same = sum(v["same"] for _, d in groups for v in d.values())
    heads = {"fr": [("Grille 1", "10 articles de 2026"), ("Grille 2", "les mêmes 10"),
                    ("Deux grilles", "10 articles ajoutés"), ("Deux grilles", "10 articles, 2019 à 2024")],
             "en": [("Grid 1", "10 papers of 2026"), ("Grid 2", "the same 10"),
                    ("Both grids", "10 added papers"), ("Both grids", "10 papers, 2019 to 2024")]}[lang]
    f = RFig((f"Lues deux fois à l'aveugle,|{num(same, lang)} décisions sur {num(tot, lang)} concordent" if fr else
                    f"Read twice blind, {num(same, lang)} decisions out of {num(tot, lang)} agree"),
            ("Quatre fois, un second agent relit dix articles sans voir la première lecture. "
             "Un carré par article lu deux fois : gris si les deux lectures concordent, rouge sinon. "
             "Le nombre est le kappa de Cohen.") if fr else
            ("Four times, a second agent rereads ten papers without seeing the first reading. "
             "One square per paper read twice: grey when the two readings agree, red when they differ. "
             "The number is Cohen's kappa."), RED)
    s, L, W = f.s, f.L, f.W
    lab_w = 190
    cw = (W - 2 * L - lab_w) / 4
    cell, gap = 7, 1.6
    rh = 19
    top = f.top + 38
    for j, (h1, h2) in enumerate(heads):
        x = L + lab_w + j * cw
        s.text(x, top - 26, h1, "sans7", 12, INK)
        s.text(x, top - 11, h2, "sans", 11, INK2)
    bottom = top + len(crit) * rh
    for i, k in enumerate(crit):
        y = top + i * rh
        if i in (7, 11):
            s.line(L, y, W - L, y, RULE)
        fragile = any(d.get(k) and d[k]["same"] / d[k]["n"] < 0.7 for _, d in groups)
        s.text(L + lab_w - 16, y + rh / 2 + 4.2, CRIT[lang][k], "sans7" if fragile else "sans", 12,
               RED if fragile else INK2, "end")
        for j, (_, d) in enumerate(groups):
            x = L + lab_w + j * cw
            if k not in d:
                s.line(x, y + rh / 2, x + 10 * (cell + gap) - gap, y + rh / 2, RULE, 1, ' stroke-dasharray="1 3"')
                continue
            v = d[k]
            for q in range(v["n"]):
                s.rect(x + q * (cell + gap), y + (rh - cell * 1.6) / 2, cell, cell * 1.6,
                       RED if q >= v["same"] else "#A3A9B2", rx=1.2)
            kap = v["kappa"]
            if v["same"] < v["n"]:  # with full agreement kappa is 1, or undefined: only the rows that differ carry it
                s.text(x + 10 * (cell + gap) + 5, y + rh / 2 + 4, num(kap, lang, 2), "sans7", 11,
                       RED if kap < 0.7 else INK2)
    s.line(L, bottom + 6, W - L, bottom + 6, RULE)
    s.text(L + lab_w - 16, bottom + 26, "désaccords" if fr else "disagreements", "sans7", 12, INK, "end")
    for j, (_, d) in enumerate(groups):
        x = L + lab_w + j * cw
        n = sum(v["n"] for v in d.values())
        dd = n - sum(v["same"] for v in d.values())
        s.text(x, bottom + 26, f"{dd}", "sans7", 16, RED)
        s.text(x + width(str(dd), "sans7", 16) + 5, bottom + 26, (f"sur {n}" if fr else f"out of {n}"), "sans5", 12, INK2)
    y = bottom + 56
    note = ("Pointillé : critère absent de cette grille. Moins de dix carrés : le critère ne s'applique pas à tous "
            "les articles. Kappa en rouge : sous\u00a00,70. Nom en rouge : la seule rangée sous\u00a070 % d'accord, "
            "la mesure de performance (Y1) lue avec la grille 2.") if fr else \
           ("Dotted: criterion absent from that grid. Fewer than ten squares: the criterion does not apply to every "
            "paper. Kappa in red: under 0.70. Name in red: the only row under 70% agreement, the performance measure (Y1) "
            "read with grid 2.")
    y = text_lines(s, L, y, note, "sans", 12, INK2, W - 2 * L, 16)
    f.desc = (f"Grille de carrés, vingt-trois critères sur quatre doubles lectures. {num(tot - same, lang)} carrés rouges "
              f"sur {num(tot, lang)} ; Y1 avec la grille 2 descend à 60 % d'accord, kappa 0,31.") if fr else \
             (f"Grid of squares, twenty-three criteria across four double readings. {tot - same} red squares out of "
              f"{tot}; Y1 with grid 2 falls to 60% agreement, kappa 0.31.")
    return f.finish(y - 8, ("Données : study/audit_stats.json (grille 1), study/agree_v2.json (grille 2), lectures brutes "
                            "avant harmonisation ; intervalles du kappa non calculés" if fr else
                            "Data: study/audit_stats.json (grid 1), study/agree_v2.json (grid 2), raw readings before "
                            "harmonisation; kappa intervals not computed"))


# ---------------------------------------------------------------------------------------------------------------
# 4. E5: how many seeds recover the ranking.

def e5_graines(lang):
    fr = lang == "fr"
    sets = [("e5", "Classement de référence : 10 graines" if fr else "Reference ranking: 10 seeds"),
            ("e5_s20", "Classement de référence : 20 graines" if fr else "Reference ranking: 20 seeds")]
    data = [J(f"sim/analysis/{k}.json") for k, _ in sets]
    mc = data[0]["median_close"]["20"]
    f = RFig((f"Entre programmes proches, vingt graines|se trompent d'ordre "
                    f"{num(rnd((1 - mc) * 100), lang)} fois sur 100") if fr else
            (f"Between close programs, twenty seeds|still get the order wrong "
             f"{rnd((1 - mc) * 100)} times in 100"),
            ("Part des tirages qui retrouvent le bon classement d'une paire, selon le nombre de graines par "
             "programme. Une ligne par paire et par tâche (24). En rouge, les paires à moins de 20 % d'écart relatif.") if fr else
            ("Share of draws that recover the right ranking of a pair of programs, by the number of seeds per "
             "program. One line per pair and task (24). In red, the pairs whose relative gap is under 20%."), RED)
    s, L, W = f.s, f.L, f.W
    NS = ["3", "5", "10", "20"]
    gx = 58
    pw = (W - 2 * L - 36 - gx - 2 * 92) / 2
    H = 290
    top = f.top + 32
    for p, ((key, head), d) in enumerate(zip(sets, data)):
        x0 = L + 36 + p * (pw + 92 + gx)
        x1 = x0 + pw
        X = lambda n: x0 + (math.log(int(n)) - math.log(3)) / (math.log(20) - math.log(3)) * (x1 - x0)
        Y = lambda v: top + H - (v - 0.4) / 0.6 * H
        s.text(x0, top - 22, head, "sans7", 13, INK)
        for tk in ticks(0.4, 1, 0.1):
            s.line(x0, Y(tk), x1, Y(tk), RULE if tk == 0.4 else GRID)
            s.text(x0 - 7, Y(tk) + 4, pct(tk * 100, lang), "mono", 10.5, MUTED, "end")
        s.line(x0, Y(0.5), x1, Y(0.5), INK2, 1.2, ' stroke-dasharray="4 3"')
        s.text(x1 + 9, Y(0.5) + 4, "pile ou face" if fr else "coin flip", "sans5", 11.5, INK2)
        for n in NS:
            s.text(X(n), top + H + 16, n, "mono", 11, MUTED, "middle")
        s.text((x0 + x1) / 2, top + H + 34, "graines par programme" if fr else "seeds per program", "sans", 11.5, INK2,
               "middle")
        comps = d["comparisons"]
        close = [c for c in comps if c["rel_gap"] < 0.2]
        far = [c for c in comps if c["rel_gap"] >= 0.2]
        P = lambda c: " ".join(f"{'M' if i == 0 else 'L'}{X(n):.1f},{Y(c['recovered'][n]):.1f}" for i, n in enumerate(NS))
        for c in far:
            s.path(P(c), "#B9BEC6", 1.2)
        for c in close:
            s.path(P(c), tint(RED, 0.5), 1.4)
        ma, mcl = d["median_all"], d["median_close"]
        s.path(" ".join(f"{'M' if i == 0 else 'L'}{X(n):.1f},{Y(ma[n]):.1f}" for i, n in enumerate(NS)), INK, 3)
        s.path(" ".join(f"{'M' if i == 0 else 'L'}{X(n):.1f},{Y(mcl[n]):.1f}" for i, n in enumerate(NS)), RED, 3.4)
        for n in NS:
            s.circle(X(n), Y(ma[n]), 3.6, INK, f' stroke="{PAPER}" stroke-width="1.3"')
            s.circle(X(n), Y(mcl[n]), 4, RED, f' stroke="{PAPER}" stroke-width="1.3"')
        # direct labels at the right end
        ys = spread([Y(ma["20"]), Y(mcl["20"])], 34, top, top + H)
        s.text(x1 + 9, ys[0] - 1, ("médiane, toutes" if fr else "median, all"), "sans7", 11.5, INK)
        s.text(x1 + 9, ys[0] + 13, pct(ma["20"] * 100, lang), "sans7", 12.5, INK)
        s.text(x1 + 9, ys[1] - 1, (f"médiane, {d['n_close']} proches" if fr else f"median, {d['n_close']} close"),
               "sans7", 11.5, RED)
        s.text(x1 + 9, ys[1] + 13, pct(rnd(mcl["20"] * 100), lang), "sans7", 12.5, RED)
    y = top + H + 62
    note = ("Pour chaque nombre de graines, 10 000 tirages avec remise parmi les essais de chaque programme. "
            "Le bon classement est celui des moyennes des dix (à gauche) ou des vingt graines (à droite).") if fr else \
           ("For each number of seeds, 10,000 draws with replacement among each program's runs. "
            "The right ranking is that of the means of the ten (left) or twenty seeds (right).")
    y = text_lines(s, L, y, note, "sans", 12, INK2, W - 2 * L, 16)
    f.desc = (f"Deux panneaux de 24 lignes. Les paires éloignées atteignent 100 % dès dix graines ; la médiane des paires "
              f"proches n'atteint que {pct(rnd(mc * 100), lang)} à vingt graines, "
              f"{pct(rnd(data[1]['median_close']['20'] * 100), lang)} avec la référence à vingt graines.") if fr else \
             (f"Two panels of 24 lines. Distant pairs reach 100% from ten seeds; the median of close pairs reaches only "
              f"{rnd(mc * 100)}% at twenty seeds, {rnd(data[1]['median_close']['20'] * 100)}% with the twenty-seed reference.")
    return f.finish(y - 8, "Données : sim/analysis/e5.json et e5_s20.json" if fr else
                    "Data: sim/analysis/e5.json and e5_s20.json")


# ---------------------------------------------------------------------------------------------------------------
# 5. E7 heat map: share of score kept under modified physics.

def verdict_col(v, ratio):
    if v == "loss":
        k = max(0.0, min(1.0, (1 - ratio) / 0.85))
        return tint(RED, 0.88 - 0.6 * k)
    if v == "gain":
        return tint(GREEN, 0.55)
    return PANEL


def e7_carte(lang):
    fr = lang == "fr"
    e7, e20 = J("sim/analysis/e7.json"), J("sim/analysis/e7_s20.json")
    n_loss = sum(e7[f"{a}/{t}"]["verdict"] == "loss" for a in ALGOS for t in TASKS)
    words = {12: ("douze", "twelve")}
    f = RFig((f"Sous une physique modifiée, {words[n_loss][0]} combinaisons sur seize perdent du score" if fr else
                    f"Under modified physics, {words[n_loss][1]} program-task pairs out of sixteen lose score"),
            ("Part du score gardée quand les masses passent à 120 % et le frottement à 80 %, "
             "moyenne interquartile sur dix graines avec son intervalle à 95 %. "
             "Perte déclarée seulement si l'intervalle reste sous 100 %.") if fr else
            ("Share of the score kept when masses go to 120% and friction to 80%, interquartile mean over ten seeds "
             "with its 95% interval. A loss is declared only when the interval stays below 100%."), RED)
    s, L, W = f.s, f.L, f.W
    lab_w = 118
    cw = (W - 2 * L - lab_w) / 4
    ch = 102
    top = f.top + 30
    for j, t in enumerate(TASKS):
        s.text(L + lab_w + j * cw + cw / 2, top - 12, TASK(t), "sans7", 13.5, INK, "middle")
    changed = []
    for i, a in enumerate(ALGOS):
        y = top + i * ch
        nm = NAME[a].split(" ")
        for k, part in enumerate(nm):
            s.text(L + lab_w - 14, y + ch / 2 + 5 - (len(nm) - 1) * 8 + k * 16, part, "sans7", 13.5, ALGO_C[NAME[a]], "end")
        for j, t in enumerate(TASKS):
            r, r20 = e7[f"{a}/{t}"], e20[f"{a}/{t}"]
            x = L + lab_w + j * cw
            bg = verdict_col(r["verdict"], r["iqm"])
            s.rect(x + 2, y + 2, cw - 4, ch - 4, bg, rx=5)
            s.text(x + 14, y + 33, pct(rnd(r["iqm"] * 100), lang), "sans7", 24, INK, halo=bg)
            vtxt = {"loss": ("perte", "loss"), "gain": ("gain", "gain"),
                    "no detectable change": ("rien de détectable", "no detectable change")}[r["verdict"]][0 if fr else 1]
            ci = (f"[{num(rnd(r['ci'][0] * 100), lang)} ; {num(rnd(r['ci'][1] * 100), lang)}]" if fr else
                  f"[{rnd(r['ci'][0] * 100)}, {rnd(r['ci'][1] * 100)}]")
            s.text(x + 14, y + 51, ci, "sans5", 11.5, INK, halo=bg)
            s.text(x + 14, y + 68, vtxt, "sans7", 11.5, INK, halo=bg)
            # gauge: 0 to 115%, the IQM as a bar, its interval as a whisker, 100% as a tick
            gx0, gx1, gy = x + 14, x + cw - 16, y + ch - 22
            G = lambda u: gx0 + min(u, 1.15) / 1.15 * (gx1 - gx0)
            s.rect(gx0, gy, gx1 - gx0, 6, tint(INK, 0.86) if r["verdict"] != "no detectable change" else "#E2E5E9", rx=3)
            s.rect(gx0, gy, G(r["iqm"]) - gx0, 6, INK, rx=3)
            s.line(G(r["ci"][0]), gy + 3, G(r["ci"][1]), gy + 3, PAPER, 1.6)
            s.line(G(1), gy - 4, G(1), gy + 10, INK, 1.4)
            if r20["verdict"] != r["verdict"]:
                changed.append((a, t))
                s.circle(x + cw - 16, y + 16, 6.5, PAPER, f' stroke="{INK}" stroke-width="1.5"')
                s.text(x + cw - 16, y + 20, "*", "sans7", 12, INK, "middle")
    y = top + 4 * ch + 14
    # scale key
    kx = L
    for lab, colr in (((("perte forte", "strong loss")), verdict_col("loss", 0.2)),
                      ((("perte légère", "slight loss")), verdict_col("loss", 0.9)),
                      ((("rien de détectable", "no detectable change")), PANEL),
                      ((("gain", "gain")), verdict_col("gain", 1.07))):
        t_ = lab[0 if fr else 1]
        s.rect(kx, y, 16, 12, colr, rx=2)
        s.text(kx + 22, y + 10.5, t_, "sans5", 12, INK2)
        kx += 22 + width(t_, "sans5", 12) + 20
    y += 34
    parts = []
    for a, t in changed:
        r20 = e20[f"{a}/{t}"]
        v = {"loss": ("perte", "loss"), "gain": ("gain", "gain"),
             "no detectable change": ("rien de détectable", "no detectable change")}[r20["verdict"]][0 if fr else 1]
        parts.append(f"{NAME[a]} sur {TASK(t)} : {v}\u00a0({pct(rnd(r20['iqm'] * 100), lang)})" if fr else
                     f"{NAME[a]} on {TASK(t)}: {v}\u00a0({rnd(r20['iqm'] * 100)}%)")
    note = (("Jauge : part gardée de 0 à 115 %, son intervalle en trait blanc, un repère à 100 %. "
             "Astérisque : le verdict change avec vingt graines. " + ", ".join(parts[:-1]) + " ; " + parts[-1] + ".")
            if fr else
            ("Gauge: share kept from 0 to 115%, its interval as a white line, a tick at 100%. "
             "Asterisk: the verdict changes with twenty seeds. " + "; ".join(parts) + "."))
    y = text_lines(s, L, y, note, "sans", 12, INK2, W - 2 * L, 16)
    f.desc = ("Carte de chaleur 4 sur 4. Hopper coûte le plus : PPO (PyTorch) garde 22 %, PPO (JAX) 18 %. "
              "Sur Swimmer, aucune perte, SAC gagne 7 %.") if fr else \
             ("Four-by-four heat map. Hopper costs most: PPO (PyTorch) keeps 22%, PPO (JAX) 18%. "
              "On Swimmer, no loss, SAC gains 7%.")
    return f.finish(y - 8, "Données : sim/analysis/e7.json et e7_s20.json, intervalles bootstrap stratifiés (rliable, 2 000 tirages)"
                    if fr else "Data: sim/analysis/e7.json and e7_s20.json, stratified bootstrap intervals (rliable, 2,000 draws)")


# ---------------------------------------------------------------------------------------------------------------
# 6. Dose: E7 at twelve strengths, ten and twenty seeds.

def dose_col(v, ratio):
    if v == "loss":
        k = max(0.0, min(1.0, (1 - ratio) / 0.7))
        return tint(RED, 0.8 - 0.75 * k)
    if v == "gain":
        k = max(0.0, min(1.0, (ratio - 1) / 0.3))
        return tint(GREEN, 0.75 - 0.6 * k)
    return "#EEF0F3"


def dose_carte(lang):
    fr = lang == "fr"
    D = [J("sim/analysis/dose.json"), J("sim/analysis/dose_s20.json")]
    Q = [("mass", k) for k in ("0.7", "0.8", "0.9", "1.1", "1.2", "1.3")] + \
        [("friction", k) for k in ("0.6", "0.7", "0.8", "0.9", "1.1", "1.2")]
    loss = [sum(v["verdict"] == "loss" for v in d["ratio"].values()) for d in D]
    m12 = sum(D[0]["ratio"][f"{a}/{t}/mass/1.2"]["verdict"] == "loss" for a in ALGOS for t in TASKS)
    f = RFig((f"Loin de la physique d'entraînement,|les pertes s'accumulent :|{m12} sur 16 à 120 % des masses" if fr else
              f"Away from the training physics,|losses pile up:|{m12} of 16 at 120% of the masses"),
             ("Part du score gardée, une quantité changée à la fois : masses de 70 à 130 %, frottement de 60 à 120 %. "
              "Une case par programme, tâche et intensité, colorée quand l'intervalle à 95 % évite\u00a0100 %.") if fr else
             ("Share of the score kept, one quantity changed at a time: masses from 70 to 130%, friction from 60 to "
              "120%. One cell per program, task and strength, coloured when the 95% interval avoids\u00a0100%."), RED)
    f.src_size = 13
    s, L, W = f.s, f.L, f.W
    T = 13  # the smallest text: 13 px prints at 7.5 pt at text width
    lab_w = 184
    cgap = 10
    cw = (W - 2 * L - lab_w - cgap) / 12
    rh, tg = 14.5, 6
    heads = ["Dix graines" if fr else "Ten seeds", "Vingt graines" if fr else "Twenty seeds"]
    rows = [(t, a) for t in TASKS for a in ALGOS]
    x0 = L + lab_w
    CX = lambda c: x0 + c * cw + (cgap if c >= 6 else 0)
    y = f.top + 10
    for p, d in enumerate(D):  # the two maps stacked, sharing their columns
        s.text(L, y + 4, heads[p], "sans7", 15, INK)
        s.text(L + width(heads[p], "sans7", 15) + 10, y + 4,
               (f"{loss[p]} pertes sur 192" if fr else f"{loss[p]} losses out of 192"), "sans7", T, RED)
        for g, lab in enumerate(("masses", "frottement" if fr else "friction")):
            gx0 = x0 + g * (6 * cw + cgap)
            s.text(gx0 + 3 * cw, y + 4, lab, "sans5", T, INK2, "middle")
            s.line(gx0 + 2, y + 10, gx0 + 6 * cw - 2, y + 10, RULE)
        for c, (qn, k) in enumerate(Q):
            s.text(CX(c) + cw / 2, y + 28, num(float(k) * 100, lang), "mono", T, MUTED, "middle")
        top = y + 38
        Yr = lambda i: top + i * rh + (i // 4) * tg
        for i, (t, a) in enumerate(rows):
            yy = Yr(i)
            if i % 4 == 1:
                s.text(L, yy + rh / 2 + 10, TASK(t), "sans7", T, INK)
            s.text(x0 - 8, yy + rh / 2 + 4.5, NAME[a], "sans5", T, ALGO_C[NAME[a]], "end")
        bottom = Yr(15) + rh
        for c, (qn, k) in enumerate(Q):
            n = 0
            for i, (t, a) in enumerate(rows):
                r = d["ratio"][f"{a}/{t}/{qn}/{k}"]
                s.rect(CX(c) + 1, Yr(i) + 0.8, cw - 2, rh - 1.6, dose_col(r["verdict"], r["iqm"]), rx=1.5)
                n += r["verdict"] == "loss"
            s.text(CX(c) + cw / 2, bottom + 20, str(n), "sans7", 14, RED if n else INK2, "middle")
        s.line(x0, bottom + 5, W - L, bottom + 5, RULE)
        s.text(x0 - 8, bottom + 20, "pertes sur 16" if fr else "losses of 16", "sans7", T, RED, "end")
        y = bottom + 56
    y -= 6
    kx = L
    for lab, colr in ((("perte de plus de moitié", "more than half lost"), dose_col("loss", 0.4)),
                      (("perte légère", "slight loss"), dose_col("loss", 0.93)),
                      (("rien de détectable", "no detectable change"), dose_col("x", 1)),
                      (("gain", "gain"), dose_col("gain", 1.08))):
        t_ = lab[0 if fr else 1]
        s.rect(kx, y - 11, 16, 13, colr, rx=2)
        s.text(kx + 22, y, t_, "sans5", T, INK2)
        kx += 22 + width(t_, "sans5", T) + 20
    y += 26
    note = ("En haut des colonnes, l'intensité en pour cent de la valeur d'entraînement. "
            "Vingt graines rétrécissent les intervalles : plus de pertes deviennent détectables.") if fr else \
           ("Above the columns, the strength in percent of the training value. "
            "Twenty seeds narrow the intervals: more losses become detectable.")
    y = text_lines(s, L, y, note, "sans", T, INK2, W - 2 * L, 17.5)
    f.desc = (f"Deux cartes de 16 rangées sur 12 colonnes. Les pertes se concentrent aux intensités extrêmes, "
              f"surtout pour les masses alourdies ; {loss[0]} cases perdent avec dix graines, {loss[1]} avec vingt.") if fr else \
             (f"Two maps of 16 rows by 12 columns. Losses gather at the extreme strengths, above all for heavier masses; "
              f"{loss[0]} cells lose with ten seeds, {loss[1]} with twenty.")
    return f.finish(y - 8, "Données : sim/analysis/dose.json et dose_s20.json, intervalles bootstrap stratifiés (rliable, 2 000 tirages)"
                    if fr else "Data: sim/analysis/dose.json and dose_s20.json, stratified bootstrap intervals (rliable, 2,000 draws)")


# ---------------------------------------------------------------------------------------------------------------
# 7. B1: the distribution of |t| over the draws, seed-based against Henderson's script.

HENDERSON_T = 9.0916


def _welch_t(a, b):
    va, vb = a.var(axis=0, ddof=1) / len(a), b.var(axis=0, ddof=1) / len(b)
    return (a.mean(0) - b.mean(0)) / np.sqrt(va + vb)


def b1_data():
    """|t| of the 10,000 random draws of b1_trpo.py (mean_t reading) and of b1_script.py (n = 10), same generator,
    same order. scipy's Welch t is written out with numpy; the summaries are checked against the JSON files."""
    out = {}
    jt, js = J("sim/analysis/b1_trpo.json"), J("sim/analysis/b1_script.json")
    for algo in ("trpo", "ppo_sb3"):
        M, S = [], []
        for s in range(30):
            with open(ROOT / f"sim/results/{algo}/HalfCheetah-v5/seed{s}.csv", newline="") as f:
                rows = list(csv.DictReader(f))
            M.append([float(r["eval_mean"]) for r in rows])
            S.append([float(r["eval_std"]) for r in rows])
        M, S = np.array(M), np.array(S)
        assert M.shape == (30, 20)
        seeds, script = [], []
        rng = np.random.default_rng(2018)  # b1_trpo.py: random draws first
        for _ in range(10000):
            idx = rng.choice(30, 10, replace=False)
            idx = rng.permutation(idx)
            seeds.append(abs(_welch_t(M[idx[5:]], M[idx[:5]]).mean()))
        rng = np.random.default_rng(2018)  # b1_script.py, n = 10: random draws first
        for _ in range(10000):
            idx = rng.choice(30, 10, replace=False)
            idx = rng.permutation(idx)
            a, b = idx[5:], idx[:5]
            t = (M[a].mean(0) - M[b].mean(0)) / np.sqrt(S[a].mean(0) ** 2 / 10 + S[b].mean(0) ** 2 / 10)
            script.append(abs(t.mean()))
        seeds, script = np.array(seeds), np.array(script)
        assert abs(np.percentile(seeds, 95) - jt[algo]["random_5v5"]["mean_t"]["abs_t_p95"]) < 1e-9
        assert abs((seeds >= HENDERSON_T).mean() - jt[algo]["random_5v5"]["mean_t"]["share_abs_t_ge_henderson"]) < 1e-12
        r = js[algo]["n10"]["random_5v5"]
        assert abs(np.median(script) - r["abs_t_median"]) < 1e-9 and abs(np.percentile(script, 95) - r["abs_t_p95"]) < 1e-9
        assert abs((script >= HENDERSON_T).mean() - r["share_abs_t_ge_henderson"]) < 1e-12
        out[algo] = (seeds, script)
    return out


def b1_distribution(lang):
    fr = lang == "fr"
    B = b1_data()
    share = (B["trpo"][1] >= HENDERSON_T).mean()
    f = RFig(("Un t de 9,09 ne sort que du script de 2017,|jamais de l'écart entre graines" if fr else
              "A t of 9.09 comes only from the 2017 script,|never from the spread between seeds"),
             ("Valeur absolue de t sur 10 000 tirages de deux groupes de cinq essais du même programme, sur "
              "HalfCheetah. Gris : t de Welch entre graines, moyenné sur la courbe. Rouge : le calcul du script de "
              "Henderson et al., qui n'emploie que l'écart entre épisodes.") if fr else
             ("Absolute value of t over 10,000 draws of two groups of five runs of the same program, on HalfCheetah. "
              "Grey: Welch t between seeds, averaged over the curve. Red: the computation of Henderson et al.'s "
              "script, which uses only the spread between episodes."), RED)
    s, L, W = f.s, f.L, f.W
    lab_w = 74
    x0, x1 = L + lab_w, W - L - 6
    lo, hi = math.log10(0.01), math.log10(100)
    X = lambda v: x0 + (math.log10(max(v, 10 ** lo)) - lo) / (hi - lo) * (x1 - x0)
    edges = np.linspace(lo, hi, 61)
    H, room = 140, 40  # room: the top of each row, kept for the labels
    gap = 40
    top = f.top + 40
    xh = X(HENDERSON_T)
    s.text(xh, top - 18, ("Henderson et al. publient t = 9,09" if fr else "Henderson et al. publish t = 9.09"),
           "sans7", 12.5, INK, "middle")
    rowsdef = [("trpo", "TRPO"), ("ppo_sb3", "PPO")]
    for i, (algo, name) in enumerate(rowsdef):
        y0 = top + i * (H + gap)
        yb = y0 + H
        s.text(L, yb - 46, name, "sans7", 16, INK)
        s.text(L, yb - 29, "30 essais" if fr else "30 runs", "sans", 11.5, INK2)
        s.text(L, yb - 14, "HalfCheetah", "sans", 11.5, INK2)
        seeds, script = B[algo]
        hs = [np.histogram(np.log10(np.clip(v, 10 ** lo, 10 ** hi)), edges)[0] / len(v) for v in (seeds, script)]
        hmax = max(h.max() for h in hs)
        for h, colr in ((hs[0], "#7D8694"), (hs[1], RED)):
            pts = [(x0, yb)]
            for k in range(len(h)):
                xa, xb = X(10 ** edges[k]), X(10 ** edges[k + 1])
                yy = yb - h[k] / hmax * (H - room)
                pts += [(xa, yy), (xb, yy)]
            pts.append((x1, yb))
            d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
            s.add(f'<path d="{d}" fill="{colr}" fill-opacity="0.5" stroke="{colr}" stroke-width="1.2" '
                  f'stroke-linejoin="round"/>')
        # the script's draws at or beyond Henderson's t, in full red
        for k in range(len(hs[1])):
            xa, xb = max(X(10 ** edges[k]), xh), X(10 ** edges[k + 1])
            if xb > xa and hs[1][k] > 0:
                hh = hs[1][k] / hmax * (H - room)
                s.rect(xa, yb - hh, xb - xa, hh, RED, extra=' fill-opacity="0.85"')
        s.line(x0, yb, x1, yb, RULE)
        # the medians, labelled at the top of the row: the seeds to the left of theirs, the script to the right of
        # its own unless Henderson's line stands there
        for v, colr, lab, side in ((seeds, "#4A4F58", "entre graines" if fr else "between seeds", "end"),
                                   (script, RED, "script de 2017" if fr else "2017 script",
                                    "end" if np.median(script) > 3 else "start")):
            m = float(np.median(v))
            s.line(X(m), y0 + 4, X(m), yb, colr, 1.2, ' stroke-dasharray="2 2"')
            dx = -5 if side == "end" else 5
            s.text(X(m) + dx, y0 + 12, lab, "sans7", 11.5, colr, side)
            s.text(X(m) + dx, y0 + 26, (f"médiane {num(m, lang, 2)}" if fr else f"median {num(m, lang, 2)}"),
                   "sans5", 11, colr, side)
        s.line(xh, y0 - 6, xh, yb, INK, 1.8)
        sh_seed, sh_scr = (seeds >= HENDERSON_T).mean(), (script >= HENDERSON_T).mean()
        s.text(xh + 7, y0 + 12, (f"au-delà : {pct(sh_scr * 100, lang, 1 if sh_scr else 0)} du script" if fr else
                                 f"beyond: {pct(sh_scr * 100, lang, 1 if sh_scr else 0)} of the script"),
               "sans7", 11.5, RED if sh_scr else INK2)
        s.text(xh + 7, y0 + 26, (f"et {pct(sh_seed * 100, lang)} entre graines" if fr else
                                 f"and {pct(sh_seed * 100, lang)} between seeds"), "sans7", 11.5, INK2)
        for v in (0.01, 0.1, 1, 10, 100):
            s.line(X(v), yb, X(v), yb + 4, RULE)
            lab = num(v, lang, 2 if v < 0.1 else 1 if v < 1 else 0)
            if v == 0.01:
                lab = ("0,01 ou moins" if fr else "0.01 or less")
            s.text(X(v), yb + 16, lab, "mono", 10.5, MUTED, "start" if v == 0.01 else "end" if v == 100 else "middle")
    y = top + 2 * H + gap + 40
    s.text((x0 + x1) / 2, y, "|t| moyen sur la courbe, échelle logarithmique" if fr else
           "|t| averaged over the curve, logarithmic scale", "sans", 12, INK2, "middle")
    y += 26
    f.desc = (f"Deux rangées d'histogrammes. Sur TRPO, le script de 2017 dépasse 9,09 dans {pct(share * 100, lang, 1)} des "
              f"tirages, le t entre graines jamais. Sur PPO, aucun des deux n'approche 9,09.") if fr else \
             (f"Two rows of histograms. On TRPO, the 2017 script exceeds 9.09 in {share * 100:.1f}% of draws, the "
              f"between-seed t never. On PPO, neither comes near 9.09.")
    return f.finish(y - 8, ("Données : sim/results/trpo et ppo_sb3, HalfCheetah, graines 0 à 29 ; mêmes tirages que "
                            "b1_trpo.py et b1_script.py (générateur 2018), recalculés et vérifiés contre leurs JSON") if fr else
                    ("Data: sim/results/trpo and ppo_sb3, HalfCheetah, seeds 0 to 29; the same draws as b1_trpo.py and "
                     "b1_script.py (generator 2018), recomputed and checked against their JSON"))


# ---------------------------------------------------------------------------------------------------------------
# 8. GRPO curves, per model, reward and seed.

def grpo_data():
    out = {}
    for m in ("qwen05", "llama1"):
        for rw in ("true", "random"):
            for sd in range(5):
                p = ROOT / f"sim/llm/results/{m}/mul2/{rw}/seed{sd}.jsonl"
                L_ = [json.loads(x) for x in open(p, encoding="utf-8")]
                ev = [(j["step"], j["pass1"]) for j in L_ if "pass1" in j]
                tr = [(j["step"], j["train_right"]) for j in L_ if "train_right" in j]
                out[(m, rw, sd)] = (ev, tr)
    summ = {(r["model"], r["reward"], r["seed"]): r for r in J("sim/llm/results/summary_5.json")}
    for k, (ev, tr) in out.items():
        if k in summ:
            assert ev[0][1] == summ[k]["pass1_0"] and ev[-1] == (100, summ[k]["pass1_100"]), k
    return out, summ


def grpo_courbes(lang):
    fr = lang == "fr"
    G, summ = grpo_data()
    f = RFig(("Vraie récompense : à chaque graine son résultat.|Pile ou face : la réussite s'éteint." if fr else
              "True reward: each seed its own result.|Coin flip: success dies out."),
            ("Part des problèmes résolus à la première tentative pendant les cent pas de GRPO, une ligne par graine "
             "aléatoire (cinq par configuration). Trait épais : évaluation sur les problèmes tenus à part, aux pas 0, "
             "50 et 100. Trait fin : réussite sur le lot d'entraînement, tous les dix pas.") if fr else
            ("Share of problems solved at the first attempt during the hundred GRPO steps, one line per random seed "
             "(five per configuration). Thick line: evaluation on the held-out problems, at steps 0, 50 and 100. "
             "Thin line: success on the training batch, every ten steps."), GREEN)
    f.src_size = 13
    s, L, W = f.s, f.L, f.W
    yl, el = 44, 52  # room for the vertical scale, then for the end labels
    pw = (W - 2 * L - 2 * yl - 2 * el) / 2
    ph, gy = 180, 84
    top = f.top + 62
    models = [("qwen05", "Qwen2.5", "0,5 milliard de paramètres" if fr else "0.5 billion parameters"),
              ("llama1", "Llama 3.2", "1 milliard de paramètres" if fr else "1 billion parameters")]
    rewards = [("true", "Vraie récompense" if fr else "True reward", GREEN),
               ("random", "Pile ou face" if fr else "Coin flip", RED)]
    X0 = lambda j: L + yl + j * (pw + el + yl)
    for j, (_, head, col) in enumerate(rewards):
        s.rect(X0(j), top - 62, pw, 4, col, rx=2)
        s.text(X0(j), top - 40, head, "sans7", 15, col)
    for i, (m, mname, msize) in enumerate(models):
        y0 = top + i * (ph + gy)
        for j, (rw, _, col) in enumerate(rewards):
            x0 = X0(j)
            x1 = x0 + pw
            s.text(x0, y0 - 14, mname, "sans7", 13.5, INK)
            s.text(x0 + width(mname, "sans7", 13.5) + 7, y0 - 14, msize, "sans", 13, INK2)
            X = lambda u: x0 + u / 100 * (x1 - x0)
            Y = lambda v: y0 + ph - v * ph
            for tk in ticks(0, 1, 0.25):
                s.line(x0, Y(tk), x1, Y(tk), RULE if tk == 0 else GRID)
                if j == 0:  # the two columns share their scale
                    s.text(x0 - 6, Y(tk) + 4, pct(tk * 100, lang), "mono", 13, MUTED, "end")
            for tk in (0, 50, 100):
                s.text(X(tk), y0 + ph + 18, str(tk), "mono", 13, MUTED, "start" if tk == 0 else "end" if tk == 100 else "middle")
            if i == 1:
                s.text((x0 + x1) / 2, y0 + ph + 38, "pas d'entraînement" if fr else "training steps", "sans", 13, INK2,
                       "middle")
            ends, failed = [], None
            for sd in range(5):  # the thin training lines first, under every thick one
                ev, tr = G[(m, rw, sd)]
                if (m, rw, sd) in summ:
                    trp = [(0, ev[0][1])] + tr
                    s.path(" ".join(f"{'M' if k == 0 else 'L'}{X(u):.1f},{Y(v):.1f}" for k, (u, v) in enumerate(trp)),
                           tint(col, 0.62), 0.8)
            for sd in range(5):
                ev, tr = G[(m, rw, sd)]
                if (m, rw, sd) not in summ:
                    failed = ev[0][1]
                    continue
                s.path(" ".join(f"{'M' if k == 0 else 'L'}{X(u):.1f},{Y(v):.1f}" for k, (u, v) in enumerate(ev)),
                       col, 2.6)
                for u, v in ev:
                    s.circle(X(u), Y(v), 3.4, col, f' stroke="{PAPER}" stroke-width="1.3"')
                ends.append((Y(ev[-1][1]), ev[-1][1]))
            if rw == "true":
                ly = spread([e[0] for e in ends], 16, y0 + 4, y0 + ph + 4)
                for (yy, v), l2 in zip(ends, ly):
                    s.text(x1 + 7, l2 + 4.5, pct(rnd(v * 100), lang), "sans7", 13, col)
            else:
                worst = max(v for _, v in ends)
                n = len(ends)
                txt = ((f"les {n} essais tombent" if n == 5 else f"les {n} essais finis tombent") if fr else
                       (f"all {n} runs fall" if n == 5 else f"the {n} finished runs fall"))
                txt2 = (f"à {pct(rnd(worst * 100), lang)} ou moins" if fr else f"to {rnd(worst * 100)}% or less")
                s.text(x1, Y(0.62), txt, "sans7", 13.5, col, "end")
                s.text(x1, Y(0.62) + 17, txt2, "sans7", 13.5, col, "end")
            if failed is not None:
                yb, xc = Y(failed), X(0)
                s.path(f"M{xc - 5:.1f},{yb - 5:.1f} L{xc + 5:.1f},{yb + 5:.1f} M{xc - 5:.1f},{yb + 5:.1f} "
                       f"L{xc + 5:.1f},{yb - 5:.1f}", INK, 2.2)
                ty = Y(0.86)
                s.path(f"M{xc + 2:.1f},{yb - 8:.1f} L{xc + 10:.1f},{ty + 4:.1f}", INK2, 1)
                s.text(xc + 14, ty, ("graine 4 : arrêtée deux fois" if fr else "seed 4: stopped twice"), "sans5", 13, INK)
                s.text(xc + 14, ty + 16, ("au premier pas, sans résultat" if fr else "at the first step, no result"),
                       "sans5", 13, INK)
    y = top + 2 * (ph + gy) - gy + 66
    note = ("Nombre à droite : réussite au pas 100, arrondie. Croix : essai sans résultat. Le lot d'entraînement compte 32 réponses : "
            "son trait fin saute d'un pas à l'autre.") if fr else \
           ("Number on the right: success at step 100, rounded. Cross: run with no result. The training batch holds 32 answers: "
            "its thin line jumps from one step to the next.")
    y = text_lines(s, L, y, note, "sans", 13, INK2, W - 2 * L, 17.5)
    f.desc = ("Quatre panneaux. Vraie récompense : Qwen finit entre 0 et 61 %, Llama entre 20 et 48 %. "
              "Pile ou face : les neuf essais finis tombent à 1 % ou moins.") if fr else \
             ("Four panels. True reward: Qwen ends between 0 and 61%, Llama between 20 and 48%. "
              "Coin flip: the nine finished runs fall to 1% or less.")
    return f.finish(y - 8, "Données : sim/llm/results/<modèle>/mul2/<récompense>/seed<k>.jsonl, summary_5.json" if fr else
                    "Data: sim/llm/results/<model>/mul2/<reward>/seed<k>.jsonl, summary_5.json")


FIGS = {"courbes-apprentissage": courbes_apprentissage, "forest-criteres": forest_criteres,
        "accord-lecteurs": accord_lecteurs, "e5-graines": e5_graines, "e7-carte": e7_carte, "dose-carte": dose_carte,
        "b1-distribution": b1_distribution, "grpo-courbes": grpo_courbes}


def main(names):
    SRC.mkdir(parents=True, exist_ok=True)
    bad = 0
    for name in names:
        for lang in ("fr", "en"):
            svg = FIGS[name](lang)
            assert " " not in svg and "—" not in svg and "–" not in svg, name
            p = SRC / f"{name}-{lang}.svg"
            p.write_text(svg, encoding="utf-8")
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(OUT / f"{name}-{lang}.pdf"), str(p)], check=True)
            # the title's first drawn line: a wrapped title is no single text element, so the whole of it is not found
            title = re.search(r'font-family="Roboto Serif"[^>]*>([^<]*)</text>', svg).group(1)
            r = subprocess.run(["sprezzature-figures", "check", str(p), "--expect-title",
                                title.replace("&amp;", "&").replace("&#x27;", "'")], capture_output=True, text=True)
            msg = (r.stdout + r.stderr).strip()
            print(f"{p.name}: {'ok' if r.returncode == 0 else 'CHECK'}  {msg[:600]}")
            kinds = {ln.split(":")[0].strip() for ln in msg.splitlines() if ln.startswith("  ") and not ln.startswith("    ")}
            bad += bool(kinds - {"text_low_contrast"})  # the house palette's contrast notes are known and accepted
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:] or list(FIGS)) else 0)
