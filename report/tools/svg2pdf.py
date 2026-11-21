"""SVG to PDF through headless Chromium (Playwright), one browser for every file.

Why Chromium and not rsvg-convert: the house figures carry their own type as woff2 subsets in @font-face rules.
librsvg ignores @font-face and falls back on whatever fonts the machine has installed (Roboto Serif Bold for the
semibold title, a different face for each weight, nothing at all on a machine without Roboto). Chromium reads
the embedded fonts, so the PDF shows exactly the faces the SVG declares, on any machine.

Usage: python svg2pdf.py SRC.svg DST.pdf [SRC.svg DST.pdf ...]
Needs the playwright package and its Chromium (python -m playwright install chromium).
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def size(svg):
    """Width and height in CSS pixels, from the root element's width and height attributes."""
    head = svg[: svg.index(">", svg.index("<svg")) + 1]
    w = float(re.search(r'\swidth="([\d.]+)', head)[1])
    h = float(re.search(r'\sheight="([\d.]+)', head)[1])
    return w, h


def main(args):
    pairs = list(zip(args[0::2], args[1::2]))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for src, dst in pairs:
            svg = Path(src).read_text(encoding="utf-8")
            w, h = size(svg)
            css = (f"@page{{size:{w}px {h}px;margin:0}}"
                   f"html,body{{margin:0;padding:0;width:{w}px;height:{h}px;overflow:hidden;background:#fff}}"
                   "svg{display:block}"
                   # no ligatures: Ghostscript (build.sh) drops their ToUnicode entry, « chiffré » would read « chiré »
                   "text{font-variant-ligatures:none}")
            page.set_content(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head>'
                             f"<body>{svg}</body></html>")
            page.evaluate("document.fonts.ready.then(() => true)")
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            page.pdf(path=dst, width=f"{w}px", height=f"{h}px", print_background=True, page_ranges="1",
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])
