#!/bin/bash
# Builds docs/ from conclusions.md: DOCX and PDF with md2star, then conclusions.tex (biblatex) compiled with LuaLaTeX.
# Figures first: (cd figures && ../../sim/env-llm/bin/python build.py)
set -e
cd "$(dirname "$0")"
md2docx conclusions.md --bib refs.bib -o conclusions.docx
md2pdf conclusions.md --bib refs.bib -o conclusions-md2star.pdf
sed 's/\(figures\/[a-z0-9-]*\)\.svg/\1.pdf/g' conclusions.md |
  pandoc -f markdown -t latex -s --biblatex --template latex/template.tex -o conclusions.tex
latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=build conclusions.tex > build/latexmk.log 2>&1 || { tail -30 build/latexmk.log; exit 1; }
cp build/conclusions.pdf conclusions.pdf
echo "Wrote conclusions.docx, conclusions-md2star.pdf, conclusions.tex, conclusions.pdf"
