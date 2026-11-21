"""Bounding-box check of the report's figures: every text, measured with the metrics of the face it is drawn in,
must fit inside the canvas and inside the smallest panel (a rect at least 40 x 20 px) that holds its anchor point,
and keep at least 4 px from any text beside it on the same line.

Run by tools/figures.py after the SVGs are drawn (DRAW_FONTS=latex, so the widths are Latin Modern's); prints one
line per finding and exits with status 1 when there is one. sprezzature-figures check looks for overlaps between
labels; this looks for text past an edge. A text's box: its advance width (draw.width, the size actually printed,
plus any letter-spacing), from 0.75 size above the baseline to 0.25 size below it.
    python3 report/tools/check_bounds.py figures/src/*.svg
"""
import html
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("draw", ROOT / "article" / "figures" / "draw.py")
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)
FACE_OF = {}
for key, (_, fam, wt) in D.FACE.items():
    FACE_OF.setdefault((fam, wt), key)

NUM = r'="(-?[\d.]+)"'
TOL = 0.5  # px: rounding of the coordinates written with one decimal
GAP = 4    # px: the least white between two texts side by side


def attr(tag, name, default=None):
    m = re.search(rf'\s{name}="([^"]*)"', tag)
    return m[1] if m else default


def check(path):
    svg = path.read_text(encoding="utf-8")
    head = svg[: svg.index(">") + 1]
    W, H = float(attr(head, "width")), float(attr(head, "height"))
    body = re.sub(r"<svg x=.*?</svg>", "", svg[len(head):], flags=re.S)  # the footer's logo, a nested svg
    rects = []
    for tag in re.findall(r"<rect [^>]*>", body):
        w, h = float(attr(tag, "width", 0)), float(attr(tag, "height", 0))
        if w >= 40 and h >= 20 and not (w >= W - 1 and h >= H - 1):
            x, y = float(attr(tag, "x", 0)), float(attr(tag, "y", 0))
            rects.append((x, y, x + w, y + h))
    out, boxes = [], []
    for tag, txt in re.findall(r"(<text [^>]*>)(.*?)</text>", body, flags=re.S):
        s = html.unescape(re.sub(r"<[^>]+>", "", txt))
        if not s.strip():
            continue
        face = FACE_OF[(attr(tag, "font-family"), int(attr(tag, "font-weight")))]
        size = float(attr(tag, "font-size"))
        w = D.width(s, face, size) + float(attr(tag, "letter-spacing", 0)) * len(s)
        x, y = float(attr(tag, "x")), float(attr(tag, "y"))
        anchor = attr(tag, "text-anchor", "start")
        x0 = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
        box = (x0, y - 0.75 * size, x0 + w, y + 0.25 * size)
        if box[0] < -TOL or box[2] > W + TOL or box[1] < -TOL or box[3] > H + TOL:
            out.append(f"{path.name}: past the canvas ({W:.0f} x {H:.0f}): {s!r} spans x {box[0]:.1f} to {box[2]:.1f}")
            continue
        boxes.append((box, s))
        holders = [r for r in rects if r[0] <= x <= r[2] and r[1] <= y <= r[3]]
        if holders:
            r = min(holders, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
            if box[0] < r[0] - TOL or box[2] > r[2] + TOL or box[1] < r[1] - TOL or box[3] > r[3] + TOL:
                out.append(f"{path.name}: past its panel ({r[0]:.0f},{r[1]:.0f})-({r[2]:.0f},{r[3]:.0f}): {s!r} "
                           f"box ({box[0]:.1f},{box[1]:.1f})-({box[2]:.1f},{box[3]:.1f})")
    # two texts on the same line closer than GAP px (or overlapping): they read as one
    for i, (a, sa) in enumerate(boxes):
        for b, sb in boxes[i + 1:]:
            v = min(a[3], b[3]) - max(a[1], b[1])
            if v < 0.5 * min(a[3] - a[1], b[3] - b[1]):
                continue
            gap = max(a[0], b[0]) - min(a[2], b[2])
            if gap < GAP:
                out.append(f"{path.name}: {'overlap' if gap < 0 else 'too close'} ({gap:.1f} px): {sa!r} / {sb!r}")
    return out


def main(paths):
    bad = [ln for p in paths for ln in check(Path(p))]
    print("\n".join(bad) if bad else f"check_bounds: {len(paths)} SVG, every text inside its canvas and its panel")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
