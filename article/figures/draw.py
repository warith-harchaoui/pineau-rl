"""Hand-drawn SVG for the article's figures: Python's standard library only, no plotting library.

build.py reads every number from the project's result files and writes it to data/*.csv; this module draws those
rows. Three Roboto faces, embedded as subsets in each SVG so the figure carries its own type: Roboto Serif for
titles, Roboto for text, Roboto Mono for numbers. fonts/ holds the subsets and their advance widths (metrics.json),
made once from the variable fonts of sprezzature-figures with fontTools; the drawing itself needs neither.
Each figure exists in two widths: 760 px for a desktop column, 400 px for a phone. The same input always gives the
same bytes.
"""
import base64, json, math
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
METRICS = json.load(open(FONTS / "metrics.json", encoding="utf-8"))

# Faces: (file, CSS family, weight)
FACE = {"sans": ("roboto-400", "Roboto", 400), "sans5": ("roboto-500", "Roboto", 500),
        "sans7": ("roboto-700", "Roboto", 700), "serif": ("roboto-serif-600", "Roboto Serif", 600),
        "mono": ("roboto-mono-400", "Roboto Mono", 400), "brand": ("satoshi-700", "Satoshi", 700)}
# The site's mark (fonts/logo-deraison.svg, the favicon of deraison.ai), drawn before its name in each footer.
_LOGO = (FONTS / "logo-deraison.svg").read_text(encoding="utf-8")
LOGO_VB = tuple(float(v) for v in _LOGO.split('viewBox="', 1)[1].split('"', 1)[0].split())
LOGO_BODY = _LOGO.split(">", 1)[1].rsplit("</svg>", 1)[0]

# Colours. Ink and paper, then one hue per algorithm, the same in every figure, then the colours of a verdict.
INK, INK2, MUTED, RULE, GRID, PANEL, PAPER = "#15171C", "#4A4F58", "#868C96", "#C9CDD3", "#ECEEF1", "#F5F6F8", "#FFFFFF"
ALGO_C = {"SAC": "#2F6FD6", "CrossQ": "#EE8320", "PPO (PyTorch)": "#C23B75", "PPO (JAX)": "#109C86"}
RED, GREEN, GREY = "#D6453D", "#2F9E5B", "#B9BEC6"


def tint(hex_, k):
    """Mix a colour with white: k = 0 keeps it, k = 1 gives white."""
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(c + (255 - c) * k) for c in (r, g, b))


def width(text, face, size):
    m = METRICS[FACE[face][0]]
    w = m["w"]
    return sum(w.get(ch, w.get("n", 500)) for ch in text) * size / m["upm"]


def wrap(text, face, size, maxw):
    """Lines of at most maxw pixels. A '|' in the text marks the only places a line may break (sense groups);
    without one, any space may break."""
    if "|" in text:
        chunks = [c.strip() for c in text.split("|")]
        lines, cur = [], ""
        for c in chunks:
            t = f"{cur} {c}".strip()
            if cur and width(t, face, size) > maxw:
                lines.append(cur)
                cur = c
            else:
                cur = t
        return lines + [cur]
    lines, cur = [], ""
    for wd in text.split(" "):
        t = f"{cur} {wd}".strip()
        if cur and width(t, face, size) > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    return lines + [cur]


def num(x, lang, nd=0, sign=False):
    """A number as the reader's language writes it: thin space for thousands in French, comma in English,
    a true minus sign."""
    s = f"{abs(x):,.{nd}f}"
    s = s.replace(",", " ").replace(".", ",") if lang == "fr" else s
    if x < 0:
        s = "−" + s
    elif sign and x > 0:
        s = "+" + s
    return s


def pct(x, lang, nd=0, sign=False):
    return num(x, lang, nd, sign) + (" %" if lang == "fr" else "%")


class Svg:
    def __init__(self, w):
        self.w, self.parts, self.used = w, [], set()

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, face="sans", size=13, fill=INK, anchor="start", extra="", halo=PAPER):
        self.used.add(face)
        fam, wt = FACE[face][1], FACE[face][2]
        a = "" if anchor == "start" else f' text-anchor="{anchor}"'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{wt}" font-size="{size}" '
                 f'fill="{fill}"{a} stroke="{halo}" stroke-width="3" stroke-linejoin="round" paint-order="stroke"{extra}>'
                 f'{escape(s)}</text>')

    def rect(self, x, y, w, h, fill, rx=0, extra=""):
        r = f' rx="{rx}"' if rx else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{h:.1f}" fill="{fill}"{r}{extra}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1, extra=""):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{extra}/>')

    def circle(self, x, y, r, fill, extra=""):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"{extra}/>')

    def path(self, d, stroke, sw=2, fill="none", extra=""):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" '
                 f'stroke-linecap="round"{extra}/>')

    def render(self, h, title, desc):
        css = "".join(
            f"@font-face{{font-family:'{FACE[f][1]}';font-weight:{FACE[f][2]};font-style:normal;"
            f"src:url(data:font/woff2;base64,"
            f"{base64.b64encode((FONTS / (FACE[f][0] + '.woff2')).read_bytes()).decode()}) format('woff2')}}"
            for f in sorted(self.used))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h:.0f}" '
                f'viewBox="0 0 {self.w} {h:.0f}" role="img" aria-labelledby="t d">'
                f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
                f'<defs><style>{css}text{{font-variant-numeric:tabular-nums}}</style></defs>'
                f'<rect width="{self.w}" height="{h:.0f}" fill="{PAPER}"/>' + "".join(self.parts) + "</svg>\n")


class Fig:
    """A canvas with the house header (accent rule, serif title, subtitle) and footer (source, site)."""

    def __init__(self, mobile, title, subtitle, accent=INK):
        self.m = mobile
        self.W = 400 if mobile else 760
        self.L = 18 if mobile else 32  # outer margin
        self.s = Svg(self.W)
        self.title, self.subtitle = title, subtitle
        s, L = self.s, self.L
        s.rect(L, 22, 36, 4, accent, rx=2)
        tsize, ssize = (20, 13.5) if mobile else (25, 15)
        y = 22 + 4 + tsize + 12
        for ln in wrap(title, "serif", tsize, self.W - 2 * L):
            s.text(L, y, ln, "serif", tsize)
            y += tsize * 1.22
        y += 2
        for ln in wrap(subtitle, "sans", ssize, self.W - 2 * L):
            s.text(L, y - 4, ln, "sans", ssize, INK2)
            y += ssize * 1.4
        self.top = y + (10 if mobile else 14)

    def legend(self, items, y=None):
        """Inline legend, a swatch then its name, wrapping to the canvas width. Returns the y below it."""
        s, L = self.s, self.L
        y = self.top if y is None else y
        x, size = L, 12.5 if self.m else 13
        for name, col in items:
            w = 14 + 6 + width(name, "sans5", size) + 18
            if x + w - 18 > self.W - L:
                x, y = L, y + 22
            s.rect(x, y - 10, 14, 10, col, rx=2)
            s.text(x + 20, y, name, "sans5", size, INK)
            x += w
        return y + 24

    def finish(self, y, source):
        s, L = self.s, self.L
        y += 22
        s.line(L, y - 14, self.W - L, y - 14, GRID)
        size = 10.5 if self.m else 11.5
        site, bsize = "Deraison.ai", size + 1.5
        lh = bsize * 1.05  # logo height, about a capital and a half
        lw = lh * LOGO_VB[2] / LOGO_VB[3]
        sw = width(site, "brand", bsize)
        lines = wrap(source, "sans", size, self.W - 2 * L - sw - lw - 26)
        for i, ln in enumerate(lines):
            s.text(L, y + i * size * 1.35, ln, "sans", size, MUTED)
        s.text(self.W - L, y, site, "brand", bsize, INK, "end")
        lx, ly = self.W - L - sw - 5 - lw, y - bsize * 0.72 - (lh - bsize * 0.72) / 2
        s.add(f'<svg x="{lx:.1f}" y="{ly:.1f}" width="{lw:.1f}" height="{lh:.1f}" viewBox="0 0 {LOGO_VB[2]} {LOGO_VB[3]}" '
              f'aria-hidden="true">{LOGO_BODY}</svg>')
        h = y + (len(lines) - 1) * size * 1.35 + 16
        return s.render(h, self.title, self.desc)


def spread(ys, gap, lo=-math.inf, hi=math.inf):
    """Move label positions apart, keeping their order, so that neighbours stand at least `gap` apart."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    p = [ys[i] for i in order]
    for _ in range(200):
        moved = False
        for i in range(1, len(p)):
            d = p[i] - p[i - 1]
            if d < gap - 1e-6:
                push = (gap - d) / 2
                p[i - 1] -= push
                p[i] += push
                moved = True
        p[0], p[-1] = max(p[0], lo), min(p[-1], hi)
        if not moved:
            break
    out = [0] * len(ys)
    for k, i in enumerate(order):
        out[i] = p[k]
    return out


def ticks(lo, hi, step):
    v, out = math.ceil(lo / step) * step, []
    while v <= hi + 1e-9:
        out.append(round(v, 6))
        v += step
    return out


# ---------------------------------------------------------------------------------------------------------------
# The figures. Each takes (rows, lang, mobile, title, subtitle, T) where T holds its language's strings, and returns
# the SVG text. rows are the CSV rows written by build.py, header excluded.


def e1_graines(rows, lang, mob, title, sub, T):
    v = sorted(float(r[1]) for r in rows)
    f = Fig(mob, title, sub, MUTED)
    f.desc = T["desc"]
    s, L, W = f.s, f.L, f.W
    lo, hi = 1000, 3600
    x0, x1 = L + 4, W - L - 4
    X = lambda u: x0 + (u - lo) / (hi - lo) * (x1 - x0)
    r = 5 if mob else 7
    cy = f.top + (70 if mob else 86)
    # beeswarm: each dot takes the free offset nearest the axis line
    placed = []
    for u in v:
        x = X(u)
        for k in range(0, 40):
            for dy in ((0,) if k == 0 else (k * (r + 0.6), -k * (r + 0.6))):
                if all((x - px) ** 2 + (cy + dy - py) ** 2 >= (2 * r + 1) ** 2 for px, py, _ in placed):
                    placed.append((x, cy + dy, u))
                    break
            else:
                continue
            break
    cut = T["cut"]
    for x, y, u in placed:
        s.circle(x, y, r, RED if u >= cut else "#55637A")
    ax = cy + (52 if mob else 62)
    s.line(x0, ax, x1, ax, RULE)
    for t in ticks(lo, hi, 1000 if mob else 500):
        s.line(X(t), ax, X(t), ax + 4, RULE)
        s.text(X(t), ax + 18, num(t, lang), "mono", 11.5, MUTED, "middle")
    s.text((x0 + x1) / 2, ax + 38, T["axis"], "sans", 12.5, INK2, "middle")
    med = (v[14] + v[15]) / 2
    s.line(X(med), cy - (44 if mob else 54), X(med), ax, INK2, 1, ' stroke-dasharray="3 3"')
    s.text(X(med), cy - (49 if mob else 60), f"{T['median']} {num(med, lang)}", "sans5", 12, INK2, "middle")
    # the three runs above the cut, a bracket and a note
    hiv = [u for u in v if u >= cut]
    bx0, bx1, by = X(min(hiv)) - r - 2, X(max(hiv)) + r + 2, cy - (22 if mob else 28)
    s.path(f"M{bx0:.1f},{by + 6:.1f} V{by:.1f} H{bx1:.1f} V{by + 6:.1f}", RED, 1.5)
    note = wrap(T["note"], "sans5", 12 if mob else 13, (bx1 - bx0) + (60 if mob else 120))
    for i, ln in enumerate(note):
        s.text(bx1, by - 8 - (len(note) - 1 - i) * 16, ln, "sans5", 12 if mob else 13, RED, "end")
    s.text(X(v[0]), ax - 8, num(v[0], lang), "sans5", 11, INK2, "middle")
    s.text(X(v[-1]), ax - 8, num(v[-1], lang), "sans7", 11, RED, "middle")
    return f.finish(ax + 46, T["source"])


def hbars(f, items, lang, vmax, step, fmt, label_w, bar_h=22, gap=14, ref=None):
    """Horizontal bars. items: (label, value, colour, bold). Labels sit left of the bars on desktop, above them on
    a phone. Returns the y below the last bar."""
    s, L, W, mob = f.s, f.L, f.W, f.m
    x0 = L + (0 if mob else label_w)
    x1 = W - L - 48
    X = lambda u: x0 + u / vmax * (x1 - x0)
    y = f.top + 8
    ys = []
    for lab, val, col, bold in items:
        if mob:
            s.text(x0, y + 12, lab, "sans7" if bold else "sans", 12.5, INK if bold else INK2)
            y += 18
        else:
            lines = wrap(lab, "sans7" if bold else "sans", 13, label_w - 14)
            for i, ln in enumerate(lines):
                s.text(x0 - 12, y + bar_h / 2 + 4.5 - (len(lines) - 1 - i) * 8 + i * 8, ln,
                       "sans7" if bold else "sans", 13, INK if bold else INK2, "end")
        ys.append(y)
        if val > 0:
            s.rect(x0, y, X(val) - x0, bar_h, col, rx=3)
        else:
            s.circle(x0 + 3, y + bar_h / 2, 3.5, col)
        s.text(max(X(val), x0 + 6) + 8, y + bar_h / 2 + 4.5, fmt(val), "sans7" if bold else "sans5", 12.5,
               col if bold else INK2)
        y += bar_h + gap
    top, bottom = f.top, y - gap + 6
    for t in ticks(0, vmax, step):
        s.line(X(t), top, X(t), bottom, GRID if t else RULE, 1, "" if t else "")
    # grid lines drawn after the bars would cover them: move them to the back
    grid = s.parts[-len(ticks(0, vmax, step)):]
    del s.parts[-len(grid):]
    s.parts[:0] = grid
    for t in ticks(0, vmax, step):
        s.text(X(t), bottom + 16, fmt(t), "mono", 11, MUTED, "middle")
    if ref:
        val, lab = ref
        s.line(X(val), top - 4, X(val), bottom, INK2, 1.2, ' stroke-dasharray="4 3"')
        s.text(X(val) + 6, top + 2 if not mob else top - 6, lab, "sans5", 12, INK2)
    return bottom + 24, X, ys


def e1_faux_positifs(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, RED)
    f.desc = T["desc"]
    f.top += 18 if mob else 22
    items = [(r[0], float(r[1]), RED if i == len(rows) - 1 else GREY, i == len(rows) - 1) for i, r in enumerate(rows)]
    y, X, ys = hbars(f, items, lang, 35, 10, lambda u: pct(u, lang, 1 if u and u < 10 else 0), 210,
                     ref=(5, T["ref"]))
    return f.finish(y, T["source"])


def t_de_neuf(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, RED)
    f.desc = T["desc"]
    items = [(r[0], float(r[1]), RED if float(r[1]) > 0 else GREY, float(r[1]) > 0) for r in rows]
    y, X, ys = hbars(f, items, lang, 40, 10, lambda u: pct(u, lang), 210)
    i = max(range(len(rows)), key=lambda i: float(rows[i][1]))
    return f.finish(y, T["source"])


def panels(f, n, cols, ph, gapx=28, gapy=22):
    """Top-left corners of n panels on a grid."""
    pw = (f.W - 2 * f.L - (cols - 1) * gapx) / cols
    return pw, [(f.L + (k % cols) * (pw + gapx), f.top + (k // cols) * (ph + gapy)) for k in range(n)]


def classement_taches(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, INK)
    f.desc = T["desc"]
    tasks = list(dict.fromkeys(r[0] for r in rows))
    by = {t: sorted(((r[1], float(r[2])) for r in rows if r[0] == t), key=lambda x: -x[1]) for t in tasks}
    bh, bg = (17, 7) if mob else (19, 8)
    ph = 30 + 4 * (bh + bg)
    pw, corners = panels(f, 4, 1 if mob else 2, ph)
    s = f.s
    for t, (px, py) in zip(tasks, corners):
        s.rect(px, py, pw, ph, PANEL, rx=6)
        s.text(px + 12, py + 21, t, "sans7", 13.5, INK, halo=PANEL)
        lab_w = 92 if mob else 104
        bx0, bx1 = px + 12 + lab_w, px + pw - 44
        for k, (a, val) in enumerate(by[t]):
            y = py + 32 + k * (bh + bg)
            lead = k == 0
            col = ALGO_C[a]
            s.text(bx0 - 8, y + bh / 2 + 4.5, a, "sans7" if lead else "sans", 12, INK if lead else INK2, "end", halo=PANEL)
            s.rect(bx0, y, (bx1 - bx0) * val / 100, bh, col if lead else tint(col, 0.55), rx=3)
            s.text(bx0 + (bx1 - bx0) * val / 100 + 6, y + bh / 2 + 4.5, num(val, lang),
                   "sans7" if lead else "sans5", 12, INK if lead else INK2, halo=PANEL)
            if lead:
                s.text(bx0 + 8, y + bh / 2 + 4.5, T["first"], "sans7", 11.5, PAPER, halo=col)
    y = corners[-1][1] + ph
    return f.finish(y + 4, T["source"])


def meilleurs_sur_dix(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, RED)
    f.desc = T["desc"]
    tasks = list(dict.fromkeys(r[0] for r in rows))
    algos = list(dict.fromkeys(r[1] for r in rows))
    V = {(r[0], r[1]): float(r[2]) for r in rows}
    s, L, W = f.s, f.L, f.W
    lab_w = 84 if mob else 112
    x0, x1 = L + lab_w, W - L - 40
    vmax = 90
    X = lambda u: x0 + u / vmax * (x1 - x0)
    f.top = f.legend([(a, ALGO_C[a]) for a in algos]) + 4
    bh, bg, tg = (9, 3, 16) if mob else (10, 3, 18)
    gh = len(algos) * (bh + bg) - bg
    y = f.top + 6
    top = y
    for t in tasks:
        s.text(x0 - 10, y + gh / 2 + 4.5, t, "sans7", 13, INK, "end")
        for a in algos:
            u = V[(t, a)]
            s.rect(x0, y, X(u) - x0, bh, ALGO_C[a], rx=2)
            s.text(X(u) + 5, y + bh - 1, pct(u, lang, sign=True), "sans5", 10.5, INK2)
            y += bh + bg
        y += tg - bg
    bottom = y - tg + 6
    grid = []
    for t in ticks(0, vmax, 20 if mob else 10):
        grid.append(f'<line x1="{X(t):.1f}" y1="{top - 4:.1f}" x2="{X(t):.1f}" y2="{bottom:.1f}" stroke="{GRID if t else RULE}" stroke-width="1"/>')
        s.text(X(t), bottom + 16, pct(t, lang, sign=True) if t else "0", "mono", 11, MUTED, "middle")
    s.parts[:0] = grid
    med = T["median_value"]
    s.line(X(med), top - 10, X(med), bottom, INK, 1.4, ' stroke-dasharray="4 3"')
    s.text(X(med) + 6, top - 12, f"{T['median']} {pct(med, lang, sign=True)}", "sans7", 12, INK)
    return f.finish(bottom + 24, T["source"])


def physique_modifiee(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, ALGO_C["PPO (JAX)"])
    f.desc = T["desc"]
    phases = list(dict.fromkeys(r[0] for r in rows))
    algos = list(dict.fromkeys(r[1] for r in rows))
    V = {(r[0], r[1]): float(r[2]) for r in rows}
    s, L, W = f.s, f.L, f.W
    lw = 108 if mob else 170
    xa, xb = L + lw, W - L - lw
    top, H = f.top + 34, (230 if mob else 250)
    Y = lambda u: top + H - u / 3200 * H
    s.text(xa, top - 12, phases[0], "sans7", 12.5, INK, "middle")
    s.text(xb, top - 12, phases[1], "sans7", 12.5, INK, "middle")
    s.line(xa, top - 2, xa, top + H, RULE)
    s.line(xb, top - 2, xb, top + H, RULE)
    rank = {p: sorted(algos, key=lambda a: -V[(p, a)]) for p in phases}
    la = spread([Y(V[(phases[0], a)]) for a in algos], 30 if mob else 32, lo=top + 14)
    lb = spread([Y(V[(phases[1], a)]) for a in algos], 30 if mob else 32, lo=top + 14)
    for i, a in enumerate(algos):
        col = ALGO_C[a]
        hot = a in T["hot"]
        ya, yb = Y(V[(phases[0], a)]), Y(V[(phases[1], a)])
        s.line(xa, ya, xb, yb, col if hot else tint(col, 0.35), 3.5 if hot else 2)
        s.circle(xa, ya, 5, col)
        s.circle(xb, yb, 5, col)
        for x, yy, p, anchor, dx in ((xa, la[i], phases[0], "end", -12), (xb, lb[i], phases[1], "start", 12)):
            rk = rank[p].index(a) + 1
            s.text(x + dx, yy - 2, a, "sans7" if hot else "sans5", 12.5 if mob else 13, col, anchor)
            s.text(x + dx, yy + 13, f"{num(V[(p, a)], lang)} · {T['rank'](rk)}", "sans5", 11, INK2, anchor)
    y = top + H + 26
    for ln in wrap(T["note"], "sans", 12, W - 2 * L):
        s.text(L, y, ln, "sans", 12, INK2)
        y += 16
    return f.finish(y - 6, T["source"])


def grille_egale(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, GREEN)
    f.desc = T["desc"]
    s, L, W = f.s, f.L, f.W
    lab_w = 120 if mob else 190
    x0, x1 = L + lab_w, W - L - (44 if mob else 60)
    lo, hi = -30, 60
    X = lambda u: x0 + (u - lo) / (hi - lo) * (x1 - x0)
    rh = 30 if mob else 32
    top = f.top + 22
    s.text(X(0) + 6, top - 10, T["better"], "sans5", 11.5, GREEN)
    s.text(X(0) - 6, top - 10, T["worse"], "sans5", 11.5, MUTED, "end")
    bottom = top + len(rows) * rh
    for t in ticks(lo, hi, 30 if mob else 15):
        s.line(X(t), top - 2, X(t), bottom, RULE if t == 0 else GRID, 1.4 if t == 0 else 1)
        s.text(X(t), bottom + 16, num(t, lang, sign=True), "mono", 11, MUTED, "middle")
    for i, (g, mean, a, b) in enumerate(rows):
        mean, a, b = float(mean), float(a), float(b)
        y = top + i * rh + rh / 2
        clear = a > 0
        col = GREEN if clear else "#9097A1"
        if clear:
            s.rect(L - 4, y - rh / 2 + 2, W - 2 * L + 8, rh - 4, tint(GREEN, 0.9), rx=4)
        bg = tint(GREEN, 0.9) if clear else PAPER
        s.text(x0 - 12, y + 4.5, g, "sans7" if clear else "sans", 12.5 if mob else 13, INK if clear else INK2, "end",
               halo=bg)
        s.line(X(a), y, X(b), y, col, 3, ' stroke-linecap="round"')
        s.circle(X(mean), y, 6.5 if clear else 5.5, col, f' stroke="{PAPER}" stroke-width="2"')
        s.text(X(b) + 8, y + 4.5, num(mean, lang, sign=True), "sans7" if clear else "sans5", 12, col, halo=bg)
    s.text((x0 + x1) / 2, bottom + 36, T["axis"], "sans", 12, INK2, "middle")
    return f.finish(bottom + 44, T["source"])


def lines(f, series, lang, xlo, xhi, xstep, ylo, yhi, ystep, yfmt, colours, H, right, xlabel=None, hot=(),
          xfmt=None):
    """Line chart with direct labels at the right end of each series."""
    s, L, W = f.s, f.L, f.W
    x0, x1 = L + 30, W - L - right
    top = f.top + 12
    X = lambda u: x0 + (u - xlo) / (xhi - xlo) * (x1 - x0)
    Y = lambda u: top + H - (u - ylo) / (yhi - ylo) * H
    for t in ticks(ylo, yhi, ystep):
        s.line(x0, Y(t), x1, Y(t), RULE if t == ylo else GRID)
        s.text(x0 - 8, Y(t) + 4, yfmt(t), "mono", 11, MUTED, "end")
    for t in ticks(xlo, xhi, xstep):
        s.text(X(t), top + H + 18, (xfmt or str)(t), "mono", 11, MUTED, "middle")
    ends = []
    for name, pts in series.items():
        col = colours[name]
        w = 3.2 if name in hot or not hot else 2.2
        d = " ".join(("M" if k == 0 else "L") + f"{X(x):.1f},{Y(y):.1f}" for k, (x, y) in enumerate(pts))
        s.path(d, col, w)
        for x, y in pts:
            s.circle(X(x), Y(y), 3.6, col, f' stroke="{PAPER}" stroke-width="1.5"')
        ends.append((name, Y(pts[-1][1]), col, pts[-1][1]))
    ly = spread([e[1] for e in ends], 17, top, top + H)
    for (name, yy, col, val), y2 in zip(ends, ly):
        s.text(x1 + 10, y2 + 4.5, f"{name} {yfmt(val)}" if f.m is False else name, "sans7", 12.5, col)
    if xlabel:
        s.text((x0 + x1) / 2, top + H + 38, xlabel, "sans", 12, INK2, "middle")
    return top, top + H + (44 if xlabel else 24), X, Y


def trajectoire(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, GREEN)
    f.desc = T["desc"]
    series = {}
    for y, name, v in rows:
        series.setdefault(name, []).append((int(y), float(v)))
    pal = ["#2F6FD6", "#109C86", "#EE8320", "#7B4FC9", "#9097A1"]
    colours = {n: pal[i] for i, n in enumerate(series)}
    colours[T["grey"]] = "#9097A1"
    right = max(width(f"{n} 100 %", "sans7", 12.5) for n in series) + 18 if not mob else \
        max(width(n, "sans7", 12.5) for n in series) + 16
    top, bottom, X, Y = lines(f, series, lang, 2018, 2026, 4 if mob else 2, 0, 100, 25,
                              lambda u: pct(u, lang), colours, 220 if mob else 260, right, T["axis"])
    s = f.s
    xn = X(2019)
    s.line(xn, top - 6, xn, top + (220 if mob else 260), INK2, 1, ' stroke-dasharray="3 3"')
    for i, ln in enumerate(wrap(T["neurips"], "sans5", 11.5, 130 if mob else 170)):
        s.text(xn + 6, top + 4 + i * 15, ln, "sans5", 11.5, INK2)
    return f.finish(bottom, T["source"])


def grpo_graines(rows, lang, mob, title, sub, T):
    """One arrow per run, from its success at the start (hollow dot) to its success after 100 steps. A filled dot
    marks a run on the GPU, a hollow square a run on the CPU; a cross marks the run that never finished."""
    f = Fig(mob, title, sub, RED)
    f.desc = T["desc"]
    groups = list(dict.fromkeys(r[0] for r in rows))
    s, L, W = f.s, f.L, f.W
    top = f.top + 22
    H = 210 if mob else 240
    x0, x1 = L + 36, W - L
    Y = lambda u: top + H - u / 70 * H
    for t in ticks(0, 70, 10 if not mob else 20):
        s.line(x0, Y(t), x1, Y(t), RULE if t == 0 else GRID)
        s.text(x0 - 8, Y(t) + 4, pct(t, lang), "mono", 11, MUTED, "end")
    gw = (x1 - x0) / len(groups)
    lsize = 11.5 if mob else 12.5
    for gi, g in enumerate(groups):
        gx = x0 + gi * gw
        col = GREEN if gi % 2 == 0 else RED
        runs = [r for r in rows if r[0] == g]
        for k, (_, seed, v100, v0, dev) in enumerate(runs):
            x = gx + gw * (k + 0.5) / len(runs)
            if dev == "failed":
                yb = Y(2)
                s.path(f"M{x - 5:.1f},{yb - 5:.1f} L{x + 5:.1f},{yb + 5:.1f} M{x - 5:.1f},{yb + 5:.1f} L{x + 5:.1f},{yb - 5:.1f}",
                       INK2, 2)
                continue
            a, b = Y(float(v0)), Y(float(v100))
            s.line(x, a, x, b, tint(col, 0.4), 2.4)
            dirn = -1 if b < a else 1
            if abs(b - a) > 6:
                s.path(f"M{x - 4.5:.1f},{b - dirn * 6.5:.1f} L{x:.1f},{b:.1f} L{x + 4.5:.1f},{b - dirn * 6.5:.1f}", col, 2.2)
            if dev == "GPU":
                s.circle(x, a, 4.6, INK2, f' stroke="{PAPER}" stroke-width="1.2"')
            else:
                s.rect(x - 4, a - 4, 8, 8, PAPER, 1, f' stroke="{INK2}" stroke-width="1.6"')
            if dirn < 0:
                s.text(x, b - 9, num(float(v100), lang), "sans7", 10.5 if mob else 11, col, "middle")
            elif gi % 2 == 0 and float(v100) >= 3:
                s.text(x + 6, b + 4, num(float(v100), lang), "sans7", 10.5 if mob else 11, col)
        lab = wrap(g, "sans7", lsize, gw - 6)
        for i, ln in enumerate(lab):
            s.text(gx + gw / 2, top + H + 22 + i * 15, ln, "sans7", lsize, col, "middle")
        if gi % 2 == 1 and gi < len(groups) - 1:
            s.line(gx + gw, top - 12, gx + gw, top + H + 44, RULE)
    y = top + H + 22 + 15 * 2 + 14
    # the key
    x = L
    for kind, lab in (("gpu", T["start"] + ", " + T["gpu"]), ("cpu", T["start"] + ", " + T["cpu"]),
                      ("arrow", T["end"]), ("x", T["failed"])):
        if x + 16 + width(lab, "sans", 12) > W - L:
            x, y = L, y + 20
        if kind == "gpu":
            s.circle(x + 5, y, 4.6, INK2)
        elif kind == "cpu":
            s.rect(x + 1, y - 4, 8, 8, PAPER, 1, f' stroke="{INK2}" stroke-width="1.6"')
        elif kind == "arrow":
            s.path(f"M{x + 0.5:.1f},{y + 3:.1f} L{x + 5:.1f},{y - 3.5:.1f} L{x + 9.5:.1f},{y + 3:.1f}", INK2, 2.2)
        else:
            s.path(f"M{x + 1:.1f},{y - 4:.1f} L{x + 9:.1f},{y + 4:.1f} M{x + 1:.1f},{y + 4:.1f} L{x + 9:.1f},{y - 4:.1f}", INK2, 2)
        s.text(x + 16, y + 4.5, lab, "sans", 12, INK2)
        x += 16 + width(lab, "sans", 12) + 22
    s.text(x0 - 8, top - 14, T["axis"], "sans5", 11.5, INK2) if T.get("axis") else None
    return f.finish(y + 6, T["source"])


def grpo_coupure(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, RED)
    f.desc = T["desc"]
    probs = list(dict.fromkeys(r[0] for r in rows))
    kinds = list(dict.fromkeys(r[1] for r in rows))
    cols = {kinds[0]: GREEN, kinds[1]: "#9097A1", kinds[2]: RED}
    f.top = f.legend([(k, cols[k]) for k in kinds]) + 6
    s, L, W = f.s, f.L, f.W
    lab_w = 70 if mob else 96
    sz, gp = (30, 5) if mob else (44, 7)
    y = f.top
    for p in probs:
        s.text(L + lab_w - 14, y + sz / 2 + 5, p, "sans7", 13 if mob else 14, INK, "end")
        x = L + lab_w
        for k in kinds:
            n = int(next(r[2] for r in rows if r[0] == p and r[1] == k))
            for _ in range(n):
                s.rect(x, y, sz, sz, cols[k], rx=4)
                x += sz + gp
        y += sz + (12 if mob else 14)
    return f.finish(y - 4, T["source"])


def intensites(rows, lang, mob, title, sub, T):
    f = Fig(mob, title, sub, ALGO_C["SAC"])
    f.desc = T["desc"]
    series = {}
    for x, name, v in rows:
        series.setdefault(name, []).append((int(x), int(v)))
    names = list(series)
    colours = {names[0]: "#2F6FD6", names[1]: "#EE8320"}
    right = max(width(n, "sans7", 12.5) for n in names) + 18
    H = 220 if mob else 260
    top, bottom, X, Y = lines(f, series, lang, -40, 30, 20 if mob else 10, 0, 16, 4, lambda u: num(u, lang),
                              colours, H, right, T["axis"], xfmt=lambda u: pct(u, lang, sign=True) if u else "0")
    s = f.s
    zl = wrap(T["zero"], "sans5", 11.5, 110 if mob else 150)
    for i, ln in enumerate(zl):
        s.text(X(0), top + 12 + i * 14, ln, "sans5", 11.5, INK2, "middle")
    s.line(X(0), top + 12 + len(zl) * 14 - 6, X(0), top + H, INK2, 1, ' stroke-dasharray="3 3"')
    pk = max(series[names[0]], key=lambda p: p[1])
    s.text(X(pk[0]), Y(pk[1]) - 12, T["peak"](pk), "sans7", 12, colours[names[0]], "middle")
    s.text(f.L, top - 16, T["yaxis"], "sans5", 11.5, INK2)
    return f.finish(bottom, T["source"])


DRAW = {"e1-graines": e1_graines, "e1-faux-positifs": e1_faux_positifs, "t-de-neuf": t_de_neuf,
        "meilleurs-sur-dix": meilleurs_sur_dix, "classement-taches": classement_taches,
        "physique-modifiee": physique_modifiee, "grille-egale": grille_egale, "trajectoire": trajectoire,
        "grpo-graines": grpo_graines, "grpo-coupure": grpo_coupure, "intensites": intensites}
