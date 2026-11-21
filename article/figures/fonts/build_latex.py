"""Latin Modern subsets for the LaTeX font set of draw.py (DRAW_FONTS=latex): the report's figures.

Reads the OpenType fonts of TeX Live (Latin Modern, GUST Font License, see GUST-FONT-LICENSE.txt), keeps the
characters of the Roboto subsets that Latin Modern has (the same house character set, so a text that draws in one
set draws in the other), and writes here:
    lm-<face>.woff2       one subset per face, ligatures and kerning kept, as LaTeX sets them
    metrics-latex.json    their advance widths, in the format of metrics.json, for width() and wrap()
Latin Modern has no narrow no-break space (U+202F), the thin space French typography puts in 1 580 or 5 %, and
its U+00A0 is as wide as a figure: each Roman face gets an empty U+202F glyph half as wide as its word space, about
the \\, of LaTeX (draw.py uses it for the house's no-break spaces in the latex set).
Run once, by hand, when a face or the character set changes; the drawing itself needs neither TeX Live nor fontTools.
    python3 article/figures/fonts/build_latex.py [TEXMF-LM-DIR]
"""
import io
import json
import sys
from pathlib import Path

from fontTools import subset
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
LM = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/local/texlive/2026/texmf-dist/fonts/opentype/public/lm")
# metrics key (and woff2 name) -> Latin Modern file
FACES = {"lm-roman10-400": "lmroman10-regular", "lm-roman10-700": "lmroman10-bold",
         "lm-romandemi10-600": "lmromandemi10-regular", "lm-roman12-700": "lmroman12-bold",
         "lm-mono10-400": "lmmono10-regular"}


def add_narrow_space(font):
    """An empty glyph uni202F, half the width of the space, mapped to U+202F (CFF outlines)."""
    cff = font["CFF "].cff
    top = cff.topDictIndex[0]
    adv = round(font["hmtx"][font.getBestCmap()[0x20]][0] / 2)
    cs = T2CharStringPen(adv, None).getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    top.CharStrings.charStrings["uni202F"] = len(top.CharStrings.charStringsIndex)
    top.CharStrings.charStringsIndex.append(cs)
    order = font.getGlyphOrder() + ["uni202F"]
    top.charset = order  # the CFF charset is the font's glyph order
    font.setGlyphOrder(order)
    font["hmtx"]["uni202F"] = (adv, 0)
    font["maxp"].numGlyphs = len(order)
    for t in font["cmap"].tables:
        if t.isUnicode():
            t.cmap[0x202F] = "uni202F"


def main():
    house = json.load(open(HERE / "metrics.json", encoding="utf-8"))
    chars = set()
    for k in ("roboto-400", "roboto-500", "roboto-700", "roboto-mono-400", "roboto-serif-600"):
        chars |= set(house[k]["w"])
    out = {}
    for key, src in FACES.items():
        font = TTFont(LM / f"{src}.otf", recalcTimestamp=False)
        if "roman" in src:
            add_narrow_space(font)
            buf = io.BytesIO()
            font.save(buf)  # compiled and read again, so that every table agrees on the new glyph count
            font = TTFont(io.BytesIO(buf.getvalue()), recalcTimestamp=False)
        cmap = font.getBestCmap()
        keep = sorted(c for c in chars | {"\u202f"} if ord(c) in cmap)
        hmtx = font["hmtx"]
        out[key] = {"upm": font["head"].unitsPerEm, "w": {c: hmtx[cmap[ord(c)]][0] for c in keep}}
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.recalc_timestamp = False
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=[ord(c) for c in keep])
        sub.subset(font)
        font.flavor = "woff2"
        font.save(HERE / f"{key}.woff2")
        missing = "".join(sorted(chars - set(keep)))
        print(f"{key}.woff2 from {src}.otf: {len(keep)} characters, {(HERE / f'{key}.woff2').stat().st_size} bytes"
              + (f", not in Latin Modern: {missing}" if missing else ""))
    with open(HERE / "metrics-latex.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, sort_keys=False)
        fh.write("\n")


if __name__ == "__main__":
    main()
