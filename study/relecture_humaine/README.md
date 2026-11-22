*Translation of [LISEZMOI.md](LISEZMOI.md), made on 10 November 2026. The French text is the original.*

# Human re-readings

**The A1 re-reading was abandoned on 10 November 2026 before any review (deviation 23 of `study/PROTOCOL-en.md`).** This folder keeps its plan.

Since 22 November 2026, this folder also serves two human re-readings asked for by Warith Harchaoui: his past
re-reading, if he finds its record (`warith_v0.csv`, next section; deviation 34 reserved, written only once the facts
are supplied), and a blind preregistered re-reading of both years (deviation 35, section "Re-reading of deviation 35"
below). The A1 plan below stays as it is; its script is now called `compare_a1.py`.

## `warith_v0.csv`: Warith's past re-reading

One row per paper and criterion, columns `id, critere, decision, date, aveugle, citation, page, source`:

- `id`: the paper's identifier in the survey (`C11`, `K015`, `LR11`…);
- `critere`: the criterion code (`Q5`, `X2`, `Y9`…);
- `decision`: `yes`, `no` or `na`; an integer for X1, X6 and Y3;
- `date`: the day of the reading (`YYYY-MM-DD`), or the month (`YYYY-MM`), or the year if that is all the record says;
- `aveugle` (blind): `oui` if Warith could not see the agents' reading when he read, `non` if he could;
- `citation` and `page`: the passage of the paper the decision rests on, and its page, if the record gives them;
- `source`: where the row comes from (a file, a notebook, an email, with its date), so that it can be found again.

Nothing is inferred or reconstructed: a row whose record is missing stays out. Once the file has at least one row,
`../sim/env-an/bin/python relecture_humaine/accord_v0.py` (from `study/`) writes `accord_v0.json`: per criterion, the
share of agreement with the agents' reading and its Wilson interval, Cohen's kappa with a bootstrap interval (10,000
resamples, `default_rng(2037)`), as `agree_v2.py` does. The agents' "yes" are counted apart from their "no": a
re-reading that could see the agents' reading mostly checks their "yes". Everything is given for the rows with
`aveugle = oui`, for those with `aveugle = non`, against the final harmonised values and against the raw reads. While
the file has no row, the script stops.

The script is not in the `Makefile` yet, so that `make verify` passes with an empty file. Once the file is filled: add
`relecture_humaine/accord_v0` at the end of the `STUDY` list and `study/relecture_humaine/accord_v0.json` to `OUTPUTS`,
run the script once, commit `accord_v0.json`, then write deviation 34 in both protocols.

## Re-reading of deviation 35: 30 blind sheets, 2018 and 2026

Deviation 35 of `study/PROTOCOL-en.md`, written before the draw. Thirty papers of the main comparison, 15 of 2018 and
15 of 2026, drawn by `tirage35.py`, under opaque names H01 to H30 in a random order.

**Before filling the 30 sheets, do not open** `tirage35.json` (it ties each sheet to its paper), the commit of the
draw, `study/codes*/`, the results files (`*_stats.json`, `results_*.json`, `survey_extra.json`, `compare*.json`), nor
`docs/`, `report/` or `article/` about these papers.

1. If `feuilles/pdf/` is missing (the copies stay out of the repository): `../sim/env-an/bin/python
   relecture_humaine/feuilles35.py` from `study/`. It remakes the renamed copies of the PDFs, supplement appended at
   the end, and never overwrites a started sheet.
2. For each sheet `feuilles/Hxx.md`, open `feuilles/pdf/Hxx.pdf` and fill in, after each colon: the date, the minutes
   spent, then for Q5, Y9, X7, X2 and X8 the decision (`yes`, `no`, `na`), the exact quote and the page of the PDF
   file; for X8, the source. X8 is `na` if and only if X2 is `no`. The rules are written in the sheet.
3. The PDF shows the year (header, references): this cannot be avoided. The blindness covers the agents' reading.
4. Allow 15 to 20 minutes per paper: five criteria, the experiments, the captions and the supplement. That is 8 to 10
   hours for the 30.
5. When the 30 sheets are filled: `../sim/env-an/bin/python relecture_humaine/compare.py` from `study/`. The script
   refuses to run while a sheet is incomplete, and says what to complete. It writes `compare35.json`. Then add
   `relecture_humaine/compare` at the end of `STUDY` and `study/relecture_humaine/compare35.json` to `OUTPUTS` in the
   `Makefile`, and commit the filled sheets with `compare35.json`.

## A1 plan (abandoned)

Deviation 13 of `study/PROTOCOL.md`. Goal: measure the agreement between a human reading and the
agents' reading, on the criteria behind the document's verdicts. This is the answer to the
objection "machines read the papers".

### The golden rule: look at nothing from the agents before you are done

Do not open `study/codes/`, `study/results_*.json`, `study/audit_stats.json` or the document
`docs/conclusions.md` for these 10 papers before you have filled in the whole grid. The
comparison comes afterwards, by script.

### What to do

1. Open `grille.csv` (in a spreadsheet). One row per paper. The PDF is in
   `study/pdf/<id>.pdf` (local repository; `study/fetch.py` downloads it again if needed).
2. For each criterion, write `yes`, `no` or `na` in the criterion's column, an exact quotation
   from the paper in the `_citation` column and the page in the `_page` column. If nothing
   justifies a `yes` after reading the experiments, the appendices and the links, write `no`
   with `absent` as the quotation.
3. For X1, write an integer (the smallest number of independent training runs announced for
   a main result), or leave the cell empty if the paper does not say.
4. Allow about 20 to 25 minutes per paper.
5. When you are done: `python3 study/relecture_humaine/compare_a1.py`. The script gives the
   agreement and Cohen's kappa for each criterion. It also lists the disagreements with both
   quotations.

### The seven criteria and their rules (the agents' rules, `study/PROTOCOL.md`)

- **Q4, all the hyperparameters of the baselines are given.** `yes` if a table or a paragraph
  gives them for all the compared methods. "Default values of [library]" without listing them
  counts `yes` only if the version of the library is given. `na` if no baseline is compared.
  `no` if a baseline's only tuning is "same configuration", with no tuning procedure described
  (deviation 1).
- **Q5, the code is linked.** A link to code (GitHub, project site) in the paper.
  "Code available on request" or "will be released": `no`. A project page counts `yes`
  only if it leads to code.
- **Q6, the way the hyperparameters are chosen is described.** Grid, random search,
  budget, selection criterion. "Tuned" and nothing more: `no`.
- **Q7, evaluation runs on held-out conditions.** Tasks, environments, environment random
  seeds or datasets seen neither in training nor in tuning. For a paper on large language
  models, benchmarks distinct from the RL training data count `yes`. A theory paper with toy
  experiments: `no`.
- **Q8, a statistical test is applied to a comparison.** t-test, Welch, Mann-Whitney,
  bootstrap with interval, rliable IQM with intervals. Error bars alone: `no`.
- **X1, number of trials.** For a paper on large language models, count the independent RL
  training runs, not the evaluation samples (pass@k, "16 samples").
- **X2, an uncertainty is reported** on the main results: standard deviation, standard error,
  confidence interval, band around the curve.
