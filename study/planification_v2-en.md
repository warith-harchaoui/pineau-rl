*Translation of [planification_v2.md](planification_v2.md), made on 15 November 2026. The French text is the dated original and prevails. It was copied unchanged from `.private/planification.md`, where it was kept, and made public on 15 November 2026.*

# Plan: coding the v2 grid (Y1 to Y12) on the 62 papers

Written on 9 November 2026. Warith's decision: yes, we code the v2 grid. Nothing is coded
as of writing this plan. The grid is preregistered in `study/PROTOCOL.md`, deviation 11.

## Goal

Measure, in the same 50 papers of 2026 and the same 12 calibration papers of 2018,
the Pineau flaws that the v1 grid does not cover. In `docs/conclusions.md`, this moves
the following out of "to measure" or "in progress":

| Flaw | v2 criteria | Current verdict |
|---|---|---|
| F3 infrastructure | Y10 | half (X7 alone) |
| F6 settings that change everything | Y9 | to measure |
| F8 undefined measure | Y1, Y2, Y11 | to measure |
| F12 no test | Y11, Y12 (with Q8, X2) | not listened to |
| F13 best algorithm depends on the task | Y3, Y4 (with E2) | in progress |
| F14 diverging implementations | Y5 (with E3) | in progress |
| F15 test on the training set | Y8 (with Q7, E7) | listened to |
| F16 benchmarks too simple | Y7 (with X6) | to measure |
| checklist v1.2 | Y6 | not measured |

## What does not change

- Sample: `study/final_2026.json` (50) and `study/calib_2018.json` (12). No paper
  added, none removed.
- Split: that of v1 (`study/assignments.json`). Six readers with 10 or 12 papers each
  (A2 to F2, F2 for the 2018 calibration), and a seventh (G2) for the double reading of the same 10
  papers as G in v1.
- Format: `yes` / `no` / `na`, exact quote and page required, or "absent after
  reading the experiments sections, appendices and links".
- Appendices: as in v1 (deviation 8). In 2018, we read the ICML `-supp.pdf` files. In 2026, the
  appendices are in the main PDF.
- The v1 codes (`study/codes/`) are not touched. The v2 goes into `study/codes_v2/<reader>/<id>.json`.

## Step 0: write the decision rules, before any coding

Deviation 11 defines the criteria but not their borderline cases. We add to `PROTOCOL.md` a
deviation 11 bis, dated and written before the pilot. Here is the draft to copy into it.

- **Scope.** If Q1 is `no` in v1 (no experiment), Y1 to Y12 are `na` (same rule as
  deviation 3). For a `theory` paper with toy experiments, we code normally.
- **Y1, measure defined.** `yes` if the paper says what the reported number contains: final
  return, mean over the last N episodes, area under the curve, pass@k with k and the number
  of samples, success rate and on what. "Return" or "accuracy" with nothing more: `no`.
- **Y2, error bars defined.** `yes` if the paper says what the band or the interval
  represents (standard deviation, standard error, 95% CI, min and max). `na` if there is no bar
  or band at all (X2 v1 `no`). Bars present but not defined: `no`.
- **Y3, number of tasks.** An integer: the number of distinct tasks, environments or benchmarks
  that the main conclusion rests on. Two difficulty levels of the same game count as
  one. Derived value for the analysis: `yes` if the integer is at least 2.
- **Y4, losses shown.** `yes` if a task-by-task result is given and at least one
  task where the method does not win is shown or stated. `no` if the paper gives only
  averages, or shows only tasks where the method wins. `na` if Y3 is 1.
- **Y5, baseline implementation.** `yes` if, for each main baseline, the
  paper says where the code comes from: repository, library with its version, or "reimplemented
  by us". `na` if no baseline is compared (same rule as Q4).
- **Y6, exclusions.** `yes` if the paper says which runs, seeds or data were removed,
  or says explicitly that none was. Silence counts as `no`.
- **Y7, version.** `yes` if the version of each main environment or benchmark is
  given: Gym or Gymnasium suffix, suite version, or exact name and date of the test split
  for `llm` benchmarks. "MuJoCo" alone: `no`. "MATH-500" counts as `yes`, because it is
  a fixed, named split. "MATH" alone: `no`.
- **Y8, generalisation.** `yes` if at least one evaluation covers conditions absent
  from training and tuning: other environment seeds announced as such,
  new tasks, modified dynamics, a distinct test distribution. This is stricter
  than Q7: an `llm` benchmark different from the RL training data counts only if the
  paper presents it as an out-of-distribution test.
- **Y9, sensitivity.** `yes` if at least one hyperparameter of the method is swept and the
  result is shown (figure, table or sentence with numbers). A component ablation does not
  count: it is not a hyperparameter.
- **Y10, dependencies.** `yes` if the versions of the main libraries are given in
  the paper, or if an environment file is cited in the linked repository. The repository is not
  visited, unless the paper explicitly points to the file.
- **Y11, type of uncertainty.** Value `yes` / `no` plus a `kind` field (`std`, `se`, `ci`,
  `iqr`, `minmax`, `other`). `na` if X2 v1 is `no`. Y11 is broader than Y2: it is enough
  that the type is named somewhere.
- **Y12, post-2018 tools.** `yes` if the paper uses at least one of these tools: IQM, stratified
  bootstrap CI, rliable, performance profiles, probability of improvement. A simple
  bootstrap on a mean counts as `yes` if it produces a reported interval.

Deliverables: deviation 11 bis in `PROTOCOL.md`, and `study/GRILLE_V2.md`, the sheet that each
reader receives (rules above, JSON format, filled-in example). Commit
"v2 grid: decision rules (before coding)".

## Step 1: tools, before any coding

1. `study/check_v2.py`, a mechanical check of each file:
   - the schema: the 12 criteria present, allowed values, `kind` for Y11, integer or
     `null` for Y3;
   - consistency with v1: `na` everywhere if Q1 v1 is `no`, Y2 and Y11 `na` if and
     only if X2 v1 is `no`, Y5 `na` if and only if Q4 v1 is `na`;
   - the quotes: each quote other than "absent" must be found again in `pdftotext` of the PDF
     (or of its appendix). The match is fuzzy (spaces, hyphenation, ligatures) with a
     threshold of 90%. A quote not found sends the file back to its reader.
2. `study/analyze_v2.py`: same `wilson()` and same `load()` as v1, broken down by `llm` /
   `classic` / `theory` (X5 v1). Output in `study/results_v2.json`.
3. `study/agree_v2.py`: criterion-by-criterion agreement between the main readers and G2 on
   the 10 papers, with Cohen's kappa when both values vary.
4. Test the three scripts on two hand-made files, then delete them.

## Step 2: pilot, two papers

- Pilot papers, chosen by a rule fixed in advance: `random.Random(11)` shuffles the
  40 papers of 2026 outside the double reading, and we keep the first experimental
  `llm` paper and the first `classic` one. Result: **LR08** (`llm`) and **ML15** (`classic`).
- A subagent codes them with the sheet, then `check_v2.py` passes.
- I reread the quotes, criterion by criterion. An ambiguous rule is made precise in a
  deviation 12, dated, before the main coding. A rule moves only to remove an ambiguity,
  never to change a figure.
- The two pilot papers are then recoded by their normal reader (A2 and C2) with the
  final sheet. The pilot coding is not used for the analysis.

## Step 3: main coding, seven subagents in parallel

- A2 to E2 (10 papers of 2026 each), F2 (12 papers of 2018) and G2 (the 10 papers of
  double reading), launched together in the background.
- Each reader receives the sheet `GRILLE_V2.md`, the list of its identifiers, the paths of the
  PDFs in `study/pdf/`, and the folder to write to. The readers **read neither the v1 codes nor
  those of the other v2 readers**: consistency with v1 is checked afterwards, by
  `check_v2.py`. G2 does not know who coded its papers first.
- Each reader reads the whole paper, appendices included. It returns only the list of
  files written and the cases where it hesitated, not the content of the files.
- Cost: of the same order as the v1 coding (seven readers, 72 full-paper readings),
  so clearly more than all the rest of the work on `docs/`. The subagents only
  read and do not use the Mac: they do not interfere with the simulations or the reduced GRPO, which
  run at the same time.

## Step 4: check and reruns

- `check_v2.py` passes on the 72 files.
- Each failing file (quote not found, inconsistency with v1) is sent back to its
  reader, via SendMessage, with the list of defects. A second failure on the same criterion
  is settled by me from the PDF and noted in `study/overrides_v2.json`, with the reason.
- Commit "v2 grid: raw codes".

## Step 5: harmonisation, before any percentage

- Read the quotes criterion by criterion, across readers, without computing any share of
  `yes`. We look for readers who apply the same rule differently, like X4 and X7 in
  v1 (deviations 1 and 2).
- Each harmonisation is a deviation (13, 14, ...) written before aggregation, then applied
  from the quotes in `overrides_v2.json`.
- Commit "v2 grid: harmonisation" **before** the first run of `analyze_v2.py`.

## Step 6: analysis

- `analyze_v2.py` gives the share of `yes` in 2026 with its Wilson interval, broken down by
  family, and the share in 2018 on our 12 papers.
- Verdict per criterion. Pineau did not publish figures for Y1 to Y12, so the only
  2018 reference is our calibration (12 papers, wide intervals). Rule:
  "changed" only if the 2026 interval excludes the 2018 share **and** the 2018 interval
  excludes the 2026 share. Otherwise we report the 2026 level and say that the baseline is missing.
- External comparisons, reported alongside and not mixed into the verdict:
  - Y11 against Gorsane et al. 2022 (about a third without uncertainty, multi-agent RL);
  - Y12 against the adoption of rliable since Agarwal et al. 2021;
  - Y10 against Coakley et al. 2026 (sharing of code and data).
- `agree_v2.py` gives the agreement and the kappa. A criterion where agreement is below 70% is flagged
  in the text as fragile.
- Commit "v2 grid: results".

## Step 7: update `docs/`

- `docs/figures/build.py`: add the Y rows to the dumbbell (2018 calibration against 2026),
  or a second figure if this one becomes unreadable, and `sprezzature-figures check` must
  pass. The flaws table changes verdict for F3, F6, F8, F12, F13, F14, F15 and F16.
- Update the sections Summary, Method, each of the four families of flaws,
  Discussion, Limits (inter-reader agreement) and "What remains to be measured".
- `docs/build.sh` must compile with no warning. Commit.
- Update the memory `pineau-rl-survey-framing`: v2 grid coded.

## What this plan does not do

- It does not touch the blog post or `~/web/deraison`. That is step 4 of
  `.private/plan.md`, and it also waits for E2 to E7.
- It recodes no v1 criterion.
- It publishes nothing.

## Order and dependencies

```
0 règles ─► 1 outils ─► 2 pilote ─► 3 codage (7 en parallèle) ─► 4 contrôle ─► 5 harmonisation ─► 6 analyse ─► 7 docs
```

Steps 0 to 2 are done in one session. Step 3 runs in the background. Steps 4 to 7
wait for the end of step 3. Step 7 can also wait for the E2 to E7 analysis of the simulations,
so that `docs/` is rebuilt only once.
