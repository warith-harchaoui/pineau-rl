"""The 30 empty sheets of deviation 35 (PROTOCOL.md) and the renamed copies of their PDFs.

For each sheet name of tirage35.json: feuilles/<name>.md (feuille.render) and feuilles/pdf/<name>.pdf, a copy of
study/pdf/<id>.pdf, the version the agents read, with study/pdf/<id>-supp.pdf appended when it exists (separate
supplements exist only for 2018 papers: a second file would give the year away). qpdf --empty --pages rebuilds the
file without the document's metadata (title, creation date). The copies are local only (.gitignore), like study/pdf/.
A sheet already started is never overwritten; an empty one is rewritten identically.
Not part of make verify: it needs the local PDFs.
Run from study/: ../sim/env-an/bin/python relecture_humaine/feuilles35.py
"""
import json
import subprocess
import sys
from pathlib import Path

from feuille import parse, render, started

HERE = Path(__file__).resolve().parent
PDF = HERE.parent / "pdf"
OUT = HERE / "feuilles"

sheets = json.load(open(HERE / "tirage35.json"))["sheets"]
(OUT / "pdf").mkdir(parents=True, exist_ok=True)
missing, kept = [], []
for name, pid in sheets.items():
    src, supp = PDF / f"{pid}.pdf", PDF / f"{pid}-supp.pdf"
    if not src.exists():
        missing.append(name)
        continue
    parts = [str(src)] + ([str(supp)] if supp.exists() else [])
    subprocess.run(["qpdf", "--empty", "--pages", *parts, "--", str(OUT / "pdf" / f"{name}.pdf")], check=True)
    md = OUT / f"{name}.md"
    if md.exists() and started(parse(md.read_text(encoding="utf-8"))):
        kept.append(name)
        continue
    md.write_text(render(name) + "\n", encoding="utf-8")
print(f"{len(sheets) - len(missing) - len(kept)} sheets written, {len(kept)} started sheets kept: {' '.join(kept)}")
if missing:
    sys.exit("missing local PDF for sheets " + " ".join(missing) + " (study/fetch.py downloads them again)")
