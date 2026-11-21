#!/bin/bash
# Builds the technical report in both languages: rapport.tex (French) and report-en.tex (English).
# Tables first (tools/tables.py, from the result JSON files), figures next (tools/figures.py), then LuaLaTeX + biber.
set -e
cd "$(dirname "$0")"
PY=${PY:-../sim/env-an/bin/python}
$PY tools/tables.py
$PY tools/figures.py
mkdir -p build
for f in rapport report-en; do
  latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=build "$f.tex" > "build/$f.latexmk.log" 2>&1 ||
    { tail -40 "build/$f.latexmk.log"; exit 1; }
  # Each figure embeds its own font subsets: Ghostscript merges and compresses them (about 18 MB down to 6 MB)
  gs -q -sDEVICE=pdfwrite -dCompatibilityLevel=1.7 -dPDFSETTINGS=/printer -dNOPAUSE -dBATCH \
    -dSubsetFonts=true -dCompressFonts=true -dDetectDuplicateImages=true -sOutputFile="$f.pdf" "build/$f.pdf"
  echo "Wrote $f.pdf ($(pdfinfo $f.pdf | awk '/Pages/{print $2}') pages)"
done
