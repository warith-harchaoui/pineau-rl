"""The footer mark of the technical report: figures/src/deraison-wordmark.svg, the same signature as the footer of every
figure (article/figures/draw.py, Fig.finish): the site's mark (fonts/logo-deraison.svg) then "Deraison.ai" in Satoshi
bold (fonts/satoshi-700.woff2), with the same proportions. The name is drawn as outlines, so LaTeX needs no font.

    python tools/wordmark.py    (from report/; run by hand, its SVG is committed)
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "article" / "figures" / "fonts"
OUT = HERE.parent / "figures" / "src" / "deraison-wordmark.svg"

SITE, B = "Deraison.ai", 100.0                         # name and font size (any unit: the PDF is scaled by LaTeX)
logo = (FONTS / "logo-deraison.svg").read_text(encoding="utf-8")
vb = [float(v) for v in logo.split('viewBox="', 1)[1].split('"', 1)[0].split()]
body = logo.split(">", 1)[1].rsplit("</svg>", 1)[0]
lh = B * 1.05                                          # as draw.py: logo height, about a capital and a half
lw = lh * vb[2] / vb[3]
gap = 5 * B / 13                                       # draw.py: 5 px between logo and name at 13 px

try:                                                   # the figures' file; its WOFF2 needs the brotli module
    font = TTFont(FONTS / "satoshi-700.woff2")
except ImportError:                                    # the same face, Satoshi Bold, as installed on the machine
    font = TTFont(Path.home() / "Library" / "Fonts" / "Satoshi-Bold.otf")
glyphs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
k = B / font["head"].unitsPerEm
base = (lh + B * 0.72) / 2                             # draw.py: the logo centred on a capital of 0.72 em
x0 = lw + gap
pen, adv = SVGPathPen(glyphs), 0
for ch in SITE:
    g = cmap[ord(ch)]
    glyphs[g].draw(TransformPen(pen, (k, 0, 0, -k, x0 + adv * k, base)))
    adv += hmtx[g][0]
W, H = x0 + adv * k, lh
OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.2f} {H:.2f}" width="{W:.2f}" height="{H:.2f}">'
               f'<title>{SITE}</title><svg x="0" y="0" width="{lw:.2f}" height="{lh:.2f}" viewBox="0 0 {vb[2]} {vb[3]}">'
               f'{body}</svg><path d="{pen.getCommands()}" fill="#000"/></svg>\n', encoding="utf-8")
print("wrote", OUT.relative_to(HERE.parents[1]))
