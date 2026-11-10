*Translation of [GRILLE.md](GRILLE.md), made on 10 November 2026. The French text is the original.*

# Reader's sheet: grids v1 and v2

This sheet summarises `PROTOCOL.md` for anyone reading a paper. When in doubt, the protocol
prevails (decision rules, deviations 1 to 6 for the harmonisation, deviation 14 for grid v2).

## What we expect of you

- Read the whole paper, appendices included (`pdf/<id>.pdf`, plus `pdf/<id>-supp.pdf` if it exists).
- Fill in one JSON file per paper in `codes_v2/<lecteur>/<id>.json`, in the format below.
- For each criterion: the value, an **exact quotation** from the paper (copied from the PDF, word
  for word) and the page. If nothing justifies a `yes`, the quotation is "absent après lecture
  des sections expériences, annexes et liens" (absent after reading the experiments, appendices
  and links sections) and the page is `null`.
- Never read another reader's codes (`codes/`, `codes_v2/`), the results (`results_*.json`,
  `audit_stats.json`) or the `docs/` document.

## The criteria of grid v1

| code | criterion | values |
|---|---|---|
| Q1 | The paper has experiments | yes / no |
| Q2 | It uses neural networks | yes / no / na |
| Q3 | All the hyperparameters of the method are given | yes / no / na |
| Q4 | All the hyperparameters of the baselines are given | yes / no / na |
| Q5 | The code is linked | yes / no / na |
| Q6 | The way the hyperparameters are chosen is described | yes / no / na |
| Q7 | Evaluation runs on held-out conditions | yes / no / na |
| Q8 | A statistical test is applied to a comparison | yes / no / na |
| X1 | Number of independent training runs behind the main results | integer or null |
| X2 | An uncertainty is reported on the main results | yes / no / na |
| X3 | The best runs are selected ("top-k", "best of N", best checkpoint chosen on the test set) | yes / no / na |
| X4 | The baselines are tuned with the same care and the paper says so | yes / no / na |
| X5 | Family: `llm`, `classic` or `theory` | one of the three |
| X6 | For `llm`: number of distinct base-model families | integer or null |
| X7 | The compute used is quantified | yes / no / na |

**Rules v1** (protocol, then harmonisation deviations):
- Q1 `no`: all other criteria are `na` (deviation 3).
- Q3 and Q4: `yes` if a table or a paragraph gives them for all the main methods.
  "Default values of [library]" without listing them counts `yes` only if the version
  is given. Q4 is `na` if no baseline is compared.
- Q5: a link to code in the paper. "On request", "will be released", "will be made public
  at <URL>": `no`. A project page counts `yes` only if it leads to code (deviation 6).
- Q6: the selection method is stated (grid, random search, budget, criterion). "Tuned" and
  nothing more: `no`.
- Q7: evaluation on tasks, environments, environment random seeds or datasets seen neither in
  training nor in tuning. For `llm`, benchmarks distinct from the RL training data count `yes`.
  A `theory` paper with toy experiments: `no` (deviation 4).
- Q8: a test (t, Welch, Mann-Whitney, bootstrap with interval, rliable IQM with stratified
  intervals) applied to a comparison. Error bars alone: `no` for Q8, `yes` for X2.
- X1: for `llm`, count the independent RL training runs, not the evaluation samples
  (pass@k and "16 samples" are not training runs).
- X3: `yes` also when the paper's own tables show that the main result is the best of several
  identical training runs, even if the text does not say so (deviation 5).
- X4: `yes` requires a tuning procedure described for the baselines, or an equal tuning budget
  announced. "Same configuration as the method", with no tuning described for anyone: `no`
  (deviation 1).
- X7: `yes` requires at least one quantity (hours, GPU-hours, FLOP, or a number of GPUs with a
  duration). The name of the hardware alone: `no` (deviation 2).

## The criteria of grid v2 (deviation 11, rules from deviation 14)

| code | criterion | values |
|---|---|---|
| Y1 | The performance measure is defined | yes / no / na |
| Y2 | The error bars are defined | yes / no / na |
| Y3 | Number of tasks behind the main conclusion | integer or null |
| Y4 | A task where the method does not win is shown | yes / no / na |
| Y5 | The implementation of the baselines is identified | yes / no / na |
| Y6 | Exclusions are stated (or "none") | yes / no / na |
| Y7 | The version of the environments or benchmarks is given | yes / no / na |
| Y8 | A generalisation test outside the training conditions | yes / no / na |
| Y9 | The sensitivity to at least one hyperparameter is shown | yes / no / na |
| Y10 | The software dependencies are listed with their versions | yes / no / na |
| Y11 | The type of uncertainty is named (with `kind`) | yes / no / na |
| Y12 | A statistical tool from after 2018 is used | yes / no / na |

**Rules v2**: those of deviation 14 in `PROTOCOL.md`, to be read in full before starting. The
points that trip readers up most often:
- Q1 `no`: Y1 to Y12 are `na`.
- Y2 and Y11 are `na` if and only if X2 is `no`.
- Y4 is `na` if Y3 is 1. Y5 is `na` if and only if Q4 is `na`.
- Y8 is stricter than Q7: for `llm`, a different benchmark counts only if it is
  presented as an out-of-distribution test.
- Y9: a component ablation is not a hyperparameter sweep.
- Y11: add the `kind` field (`std`, `se`, `ci`, `iqr`, `minmax`, `other`).
- Also read deviation 17 (clarifications after the pilot): Y1 requires the point of measurement,
  Y3 counts the training setups, Y5 accepts figures copied with their source, Y7 stays strict.

**Practical tips**:
- For a paper already read in v1, your list gives Q1, Q4 and X2 v1: they set the scope rules.
- A quotation spread over two pages: `"page": [6, 7]`.
- Two-column PDF: `pdftotext -layout` mixes up the columns. Split a quotation that runs across
  lines into one-line pieces, joined by "[...]".
- Run `python3 check_codes.py codes_v2/<lecteur>` from `study/` and fix until it reports 0.

## The file format

```json
{
 "id": "K001",
 "coder": "H",
 "title": "Exact title of the paper",
 "criteria": {
  "Q1": {"value": "yes", "quote": "We evaluate on six MuJoCo tasks", "page": 6},
  "X1": {"value": 5, "quote": "averaged over 5 random seeds", "page": 7},
  "Y3": {"value": 6, "quote": "We evaluate on six MuJoCo tasks", "page": 6},
  "Y11": {"value": "yes", "kind": "se", "quote": "shaded areas denote one standard error", "page": 7}
 },
 "doubts": "The cases where you hesitated, one sentence each."
}
```

For a paper already read in v1 (identifiers `LR..`, `ML..`, `MLR..`, `NE..`, `NER..`, `C1..`,
`C2..`), fill in only Y1 to Y12: the v1 values serve only for the scope rules;
`check_codes.py` rereads them in `codes/`.
