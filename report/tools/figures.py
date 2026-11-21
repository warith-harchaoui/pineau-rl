"""Figures of the technical report: figures/<name>-<lang>.pdf, converted from the house SVGs.

Run by build.sh from report/ (with ../sim/env-an/bin/python). Two sources:
  1. the article's figures, desktop version: ../article/figures/<name>-<lang>.svg;
  2. the report's own SVGs in figures/src/<name>-<lang>.svg, written first by tools/new_figures.py (data
     figures, when that script exists), tools/docs_figures.py (the six figures of docs/, redrawn in the house
     style under their docs names, from docs/figures/data/) and tools/diagrams.py (the three diagrams).
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


def run_script(name):
    """Run a figure script of tools/ that writes SVGs into figures/src/, when it exists. A non-zero exit (such a
    script may report its own lint findings that way) is reported, not fatal: a missing SVG stops the build below."""
    script = HERE / name
    if script.exists():
        r = subprocess.run([sys.executable, str(script)], cwd=REPORT, capture_output=True, text=True)
        if r.returncode:
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            print(f"figures: tools/{name} exited with status {r.returncode}: " + " / ".join(tail)[:400])


def pairs():
    """(source SVG, target PDF) for every figure of the report."""
    out = []
    for name in ARTICLE:
        for lang in LANGS:
            out.append((ROOT / "article" / "figures" / f"{name}-{lang}.svg", OUT / f"{name}-{lang}.pdf"))
    for src in sorted(SRC.glob("*.svg")):
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
    run_script("new_figures.py")
    run_script("docs_figures.py")
    run_script("diagrams.py")
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


if __name__ == "__main__":
    main()
