# Prompt given to audit-v1-quotes

- description of the Agent call: Verify 89 unmatched v1 quotes in PDFs
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T13:44:51.593Z (main transcript line 2778, by claude-opus-5-5)
- agent id: aef8337582822cbb0
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
Audit the evidence behind a literature survey's codes. Language-model agents read 62 papers and, for each criterion, recorded a value with an exact quote and a page. An automatic check could not find 89 of 682 quotes in the PDFs' text. Your job: decide, for each of those 89, what is going on. This matters: the survey supports a polemical thesis, and a code resting on an invented quote would discredit it.

Inputs:
- The list: `~/pineau-rl/.private/v1_quotes_not_found.json` (fields: file, id, k = criterion, value, page, quote).
- The papers: `~/pineau-rl/study/pdf/<id>.pdf` and, when it exists, `<id>-supp.pdf`. Use `pdftotext -layout -f N -l N` around the cited page, and search the full text. NeurIPS 2018 papers (ids C21 to C26) had supplements published as zip archives on the proceedings site that were never downloaded: if a quote seems to come from a supplement that is missing locally, try to fetch it from the official proceedings page (papers.nips.cc / proceedings.neurips.cc), into a scratch folder of your own outside the repository, and check there.
- The decision rules for each criterion: `~/pineau-rl/study/PROTOCOL.md` (sections "Codage" and "Écarts") and the summary sheet `~/pineau-rl/study/GRILLE.md`.
- The coded file itself (field `file`, under `study/`) if you need context.

For each of the 89 entries, classify:
- `FOUND`: the quote is in the paper (the automatic check missed it: layout, symbols, line breaks, a table, a figure). Give the page where you found it.
- `PARAPHRASE_OK`: not verbatim (translated, reworded, or the reader's description of a table), but the paper does support the recorded value. Give the real passage (verbatim, page) that supports it.
- `UNSUPPORTED`: the paper does not support the recorded value under the protocol's rules. Give what the paper actually says (verbatim, page), and the value the rules give.
- `UNVERIFIABLE`: the source text cannot be obtained (for example a supplement that is nowhere online). Say why.

Do not edit any file under `study/`. Write your results to `~/pineau-rl/.private/v1_quotes_audit.json` (a list, one object per entry: id, k, file, value, class, page, passage, correct_value when UNSUPPORTED, note) and a short French summary to `~/pineau-rl/.private/v1_quotes_audit.md`: counts per class, then every UNSUPPORTED entry with its correction and its effect (does it change a yes/no for a criterion used in the document's verdicts: Q3, Q4, Q5, Q6, Q7, Q8, X2, X3, X4, X7, X1, X6?).

Report back: the counts per class, and the list of UNSUPPORTED entries (id, criterion, recorded value, value per the rules), compactly.
````
