# Prompt given to pilot

- grid: v2
- description of the Agent call: Pilot reader, grid v2
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T15:16:08.192Z (main transcript line 3388, by claude-opus-5-5)
- agent id: ab7c655b77929d932
- subagent transcript: <transcripts of pineau-rl>/9cb05a27-c084-42e0-86b3-926fde3e8d7e/subagents/agent-ab7c655b77929d932.jsonl
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You are the pilot reader for a reproducibility survey of reinforcement-learning papers in ~/pineau-rl/study/. You code papers against a fixed reading grid, with an exact quote for every value.

Read first, in full:
- ~/pineau-rl/study/GRILLE.md (the reader sheet, in French: criteria, rules, JSON format)
- ~/pineau-rl/study/PROTOCOL.md, the harmonisation écarts 1 to 6 and écart 14 (the v2 decision rules), and écart 16 (this pilot).

Code three papers:
- LR08 (pdf/LR08.pdf) and ML15 (pdf/ML15.pdf): grid v2 only (Y1 to Y12). These were already read in v1; do NOT open codes/ — the checker reads their v1 values itself.
- C218 (pdf/C218.pdf, plus pdf/C218-supp.pdf if it exists): grid v1 (Q1–Q8, X1–X7) AND grid v2 (Y1–Y12), in one pass.

Write one JSON file per paper to ~/pineau-rl/study/codes_v2/pilot/<id>.json, with "coder": "P", in the exact format of GRILLE.md. Read each paper in full, appendices included (use `pdftotext -layout`). Every quote must be copied verbatim from the PDF text; if nothing justifies a yes, use the "absent après lecture des sections expériences, annexes et liens" note with page null. Put every hesitation in "doubts", one sentence each, naming the criterion.

Forbidden: reading anything in study/codes/, study/codes_v2/ other than your own files, results_*.json, audit_stats.json, overrides.json, or anything under docs/ or .private/. Do not modify any other file.

When the three files are written, run from study/: `python3 check_codes.py codes_v2/pilot` and fix every problem it reports in your own files (a quote not found means re-copying it exactly from pdftotext output). Rerun until it passes.

Report back: the files written, the check_codes.py result, and — most important — every rule in GRILLE.md / écart 14 you found ambiguous on these papers, with the paper, criterion, the two readings you hesitated between, and which you chose. Do not paste the file contents.
````
