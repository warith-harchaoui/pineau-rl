"""Figures of the technical report: figures/<name>-<lang>.pdf, converted from the house SVGs.

Run by build.sh from report/ (with ../sim/env-an/bin/python). Every figure is drawn by the house toolkit
(article/figures/draw.py) in its LaTeX font set, DRAW_FONTS=latex (Latin Modern, the fonts of the report's text),
into figures/src/<name>-<lang>.svg:
  1. the article's eleven figures, desktop width: ../article/figures/build.py --out figures/src, the same drawing
     as the blog's (whose SVGs, in Roboto, stay untouched next to build.py), its CSVs in build/article-data/;
  2. the report's own figures: tools/new_figures.py (data figures), tools/docs_figures.py (the six figures of
     docs/, redrawn in the house style under their docs names, from docs/figures/data/) and tools/diagrams.py
     (the diagrams).
The conversion goes through headless Chromium (tools/svg2pdf.py, see there why not rsvg-convert), run with
the first Python that has Playwright: $PW_PYTHON, this interpreter, then python3 on the PATH.
Every PDF is converted again at each run (a few seconds), so that no PDF made another way survives.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
ROOT = REPORT.parent
OUT = REPORT / "figures"
SRC = OUT / "src"

ARTICLE = ["e1-graines", "e1-faux-positifs", "t-de-neuf", "meilleurs-sur-dix", "classement-taches",
           "physique-modifiee", "intensites", "grpo-graines", "grpo-coupure", "grille-egale", "trajectoire"]
LANGS = ("fr", "en")


LATEX = dict(os.environ, DRAW_FONTS="latex")  # the toolkit's Latin Modern set, for every figure of the report


def run_script(script, *args):
    """Run a figure script that writes SVGs into figures/src/, in the LaTeX font set. A non-zero exit (such a
    script may report its own lint findings that way) is reported, not fatal: a missing SVG stops the build below."""
    if script.exists():
        r = subprocess.run([sys.executable, str(script), *args], cwd=REPORT, capture_output=True, text=True,
                           env=LATEX)
        if r.returncode:
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            print(f"figures: {script.relative_to(ROOT)} exited with status {r.returncode}: " + " / ".join(tail)[:400])


def pairs():
    """(source SVG, target PDF) for every figure of the report."""
    out = [(SRC / f"{name}-{lang}.svg", OUT / f"{name}-{lang}.pdf") for name in ARTICLE for lang in LANGS]
    for src in sorted(SRC.glob("*.svg")):
        if (src, OUT / f"{src.stem}.pdf") not in out:
            out.append((src, OUT / f"{src.stem}.pdf"))
    return out


def playwright_python():
    cands = [os.environ.get("PW_PYTHON"), sys.executable, shutil.which("python3"),
             str(Path.home() / "miniconda3" / "bin" / "python3")]
    for c in cands:
        if c and Path(c).exists() and subprocess.run([c, "-c", "import playwright.sync_api"],
                                                     capture_output=True).returncode == 0:
            return c
    sys.exit("figures.py: no Python with Playwright found (set PW_PYTHON, or pip install playwright and "
             "python -m playwright install chromium)")


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    run_script(ROOT / "article" / "figures" / "build.py", "--out", str(SRC), "--data", str(REPORT / "build" / "article-data"))
    run_script(HERE / "new_figures.py")
    run_script(HERE / "docs_figures.py")
    run_script(HERE / "diagrams.py")
    todo, missing = [], []
    for src, dst in pairs():
        if not src.exists():
            missing.append(src)
        else:
            todo += [str(src), str(dst)]
    if missing:
        sys.exit("figures.py: missing SVG: " + ", ".join(str(m.relative_to(ROOT)) for m in missing))
    if todo:
        subprocess.run([playwright_python(), str(HERE / "svg2pdf.py"), *todo], check=True)
    print(f"figures: {len(todo) // 2} converted to PDF")
    # Every text in Latin Modern, the brand's name aside: a face Chromium could not load would come out in a
    # fallback (Times), silently. pdffonts names the embedded fonts; Satoshi's subset carries no name ("false").
    svgs = [s_ for s_ in todo[0::2] if Path(s_).name != "logo-deraison.svg"]
    stray = {}
    for svg in svgs:
        pdf = OUT / f"{Path(svg).stem}.pdf"
        names = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout.splitlines()[2:]
        bad = {n.split()[0].split("+")[-1] for n in names} - {"false"}
        bad = {n for n in bad if not n.startswith(("LMRoman", "LMMono"))}
        if bad:
            stray[pdf.name] = sorted(bad)
    if stray:
        sys.exit(f"figures.py: fonts other than Latin Modern in {stray}")
    r = subprocess.run([sys.executable, str(HERE / "check_bounds.py"), *svgs], capture_output=True, text=True, env=LATEX)
    print(r.stdout.strip())


if __name__ == "__main__":
    main()
