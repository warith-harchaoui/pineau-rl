*Translation of [LISEZMOI.md](LISEZMOI.md), made on 10 November 2026. The French text is the original.*

# Blind human rereading (experiment A1)

**Abandoned on 10 November 2026 before any review (deviation 23 of `study/PROTOCOL-en.md`).** This folder keeps the plan.

Deviation 13 of `study/PROTOCOL.md`. Goal: measure the agreement between a human reading and the
agents' reading, on the criteria behind the document's verdicts. This is the answer to the
objection "machines read the papers".

## The golden rule: look at nothing from the agents before you are done

Do not open `study/codes/`, `study/results_*.json`, `study/audit_stats.json` or the document
`docs/conclusions.md` for these 10 papers before you have filled in the whole grid. The
comparison comes afterwards, by script.

## What to do

1. Open `grille.csv` (in a spreadsheet). One row per paper. The PDF is in
   `study/pdf/<id>.pdf` (local repository; `study/fetch.py` downloads it again if needed).
2. For each criterion, write `yes`, `no` or `na` in the criterion's column, an exact quotation
   from the paper in the `_citation` column and the page in the `_page` column. If nothing
   justifies a `yes` after reading the experiments, the appendices and the links, write `no`
   with `absent` as the quotation.
3. For X1, write an integer (the smallest number of independent training runs announced for
   a main result), or leave the cell empty if the paper does not say.
4. Allow about 20 to 25 minutes per paper.
5. When you are done: `python3 study/relecture_humaine/compare.py`. The script gives the
   agreement and Cohen's kappa for each criterion. It also lists the disagreements with both
   quotations.

## The seven criteria and their rules (the agents' rules, `study/PROTOCOL.md`)

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
