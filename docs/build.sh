#!/bin/bash
# Builds docs/ in both languages: conclusions.md (French) and conclusions-en.md (English).
# For each: DOCX and PDF with md2star, then a .tex (biblatex) compiled with LuaLaTeX.
# Figures first: (cd figures && ../../sim/env-llm/bin/python build.py)
set -e
cd "$(dirname "$0")"
build() {  # build <source stem> <babel language> <pdf language> <bibliography title>
  md2docx "$1.md" --bib refs.bib -o "$1.docx"
  md2pdf "$1.md" --bib refs.bib -o "$1-md2star.pdf"
  sed 's/\(figures\/[a-z0-9-]*\)\.svg/\1.pdf/g' "$1.md" |
    pandoc -f markdown -t latex -s --biblatex --template latex/template.tex \
      -V babel="$2" -V pdflang="$3" -V bibtitle="$4" -o "$1.tex"
  latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=build "$1.tex" > "build/$1.latexmk.log" 2>&1 ||
    { tail -30 "build/$1.latexmk.log"; exit 1; }
  cp "build/$1.pdf" "$1.pdf"
  echo "Wrote $1.docx, $1-md2star.pdf, $1.tex, $1.pdf"
}
mkdir -p build
build conclusions french fr "Références"
[ -f conclusions-en.md ] && build conclusions-en british en-GB "References"
