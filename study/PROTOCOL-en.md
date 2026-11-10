*Translation of [PROTOCOL.md](PROTOCOL.md), made on 10 November 2026. The French text is the dated original and prevails.*

# Remeasuring Pineau: do the RL papers of 2025-2026 have the flaws of 2018?

Written on 2026-11-08, BEFORE any paper was coded. Nothing in this protocol changes after the
results have been seen; every departure is recorded under "Deviations" at the bottom.

## The 2018 measurement we repeat

Joelle Pineau, invited talk at NeurIPS 2018, "Reproducible, Reusable, and Robust Reinforcement
Learning", slides 29-30 (`../slides/neurips2018-pineau.pdf`): "We surveyed 50 RL papers
from 2018 (published at NeurIPS, ICML, ICLR)". Eight criteria, share of "yes":

| code | criterion | 2018 |
|---|---|---|
| Q1 | Paper has experiments | 100% |
| Q2 | Paper uses neural networks | 90% |
| Q3 | All hyperparams for proposed algorithm are provided | 90% |
| Q4 | All hyperparams for baselines are provided | 60% |
| Q5 | Code is linked | 55% |
| Q6 | Method for choosing hyperparams is specified | 20% |
| Q7 | Evaluations on some variation of a hold-out test set | 10% |
| Q8 | Significance testing applied | 5% |

Her sampling method is not described. So we compare orders of magnitude only.

## What we add (drawn from her ICLR 2018 talk and from the 2025 debate)

| code | criterion |
|---|---|
| X1 | number of random seeds (independent runs) for the main results: the smallest number stated for a main table or curve; "not stated" if absent |
| X2 | uncertainty reported on the main results (standard deviation, standard error, confidence interval, band around the curve) |
| X3 | selection of the best runs ("top-k", "best of N", "best checkpoint chosen on the test set") |
| X4 | the baselines are tuned with the same care as the method and the paper says so (same hyperparameter search budget, or tuning described for each one) |
| X5 | paper family: `llm` (RL applied to a large language model or vision-language model: RLHF, RLVR, GRPO…), `classic` (RL agents outside large models: control, games, robotics, offline RL…), `theory` (no experiment, or illustrative toy experiments only) |
| X6 | for `llm` only: number of distinct base model families (Qwen, Llama, Mistral, Gemma, DeepSeek, OLMo…; two sizes of Qwen = one family) |
| X7 | the compute used is reported (GPU, hours or FLOP) |

## Population and sample

- 2026: the papers accepted at ICLR 2026, ICML 2026 and NeurIPS 2025 (the three most recent
  conferences as of 8 November 2026), from the public lists (proceedings.iclr.cc,
  icml.cc/virtual/2026, neurips.cc/virtual/2025). A paper counts as "RL" if its title matches
  `reinforcement learning|\bRL\b|\bRLHF\b|\bRLVR\b|policy optimi[sz]ation|policy gradient|q-learning|actor-critic|\bMDPs?\b`
  (case-insensitive). Population: 1,252 papers (ICLR 420, ICML 494, NeurIPS 338) out of
  17,836.
- Draw: `random.Random(2018)`, 17 ICLR, 17 ICML, 16 NeurIPS (`sample_2026.json`).
- PDFs: official proceedings for ICLR; arXiv (title at least 85% identical) for ICML and
  NeurIPS, since OpenReview refuses automated downloads. Eight papers with no freely
  accessible PDF are replaced, in order, by a `random.Random(2026)` draw from the rest of
  the same conference (`replacements_2026.json`). Possible bias: a paper posted on arXiv is
  perhaps more open than average (more likely to share its code). Final sample: `final_2026.json` (50).
- 2018 calibration: 6 RL papers from ICML 2018 and 6 from NeurIPS 2018, same filter, same random
  seed (`calib_2018.json`). We code them with the same grid to check that our readers recover
  roughly Pineau's figures; if the gap is large, we say so and interpret with caution.

## Coding

- One JSON file per paper in `codes/<reader>/<id>.json`: for each criterion, the value
  (`yes` / `no` / `na`; X1 an integer or `null`), an **exact quotation** from the paper (or
  "absent after reading the experiments sections, appendices and links") and the page.
- Decision rules:
  - Q3/Q4 "all hyperparameters": `yes` if a table or a paragraph gives them for every main
    method; "we keep the default values of [lib]" without listing them counts as `yes` only if
    the library version is given. Q4 is `na` if no baseline is compared.
  - Q5: a link to code (GitHub, project site) in the paper; "code available upon request" or
    "will be released" = `no`.
  - Q6: the selection method is stated (grid, random search, budget, criterion); "tuned" and
    nothing more = `no`.
  - Q7: evaluation on tasks, environments, environment random seeds or datasets not seen during
    training or tuning (for `llm`: benchmarks distinct from the RL training data count as
    `yes`).
  - Q8: a statistical test (t, Welch, Mann-Whitney, bootstrap with an interval, rliable IQM
    with stratified confidence intervals) applied to a comparison; error bars alone = `no` for
    Q8 but `yes` for X2.
  - X1: for `llm`, count the independent RL training runs, not the samples at evaluation
    (pass@k and "16 samples" are not random seeds).
- Double coding: 10 papers from 2026 (the first 10 in identifier order after a
  `random.Random(7)` shuffle) coded by a second reader who does not see the first coding.
  Agreement reported criterion by criterion (percentage agreement; Cohen's kappa where useful).

## Analysis

Share of `yes` per criterion (over the papers where the criterion applies), in 2026, with a
95% Wilson interval, next to the 2018 figure. Broken down by `llm` / `classic` / `theory`.
Each criterion is then sorted into one of three classes: improved (the 2026 interval excludes
the 2018 figure from above), regressed (from below), unchanged (otherwise). Raw data, codes,
scripts and the sample's PDFs (as links) published with the article.

## Deviations

Recorded during coding, BEFORE aggregation; the harmonization rules below are set before any
percentage is computed.

1. X4, shared configuration: some readers code `yes` when the paper says only that the
   baseline reuses the method's configuration, with no tuning described for anyone.
   Harmonization: `yes` requires tuning described for the baselines (or an equal tuning budget
   stated); "same configuration, no tuning described" becomes `no`. Recoded from the
   quotations.
2. X7, compute: `yes` requires at least one quantity (hours, number of GPU-hours, FLOP, or a
   number of GPUs with a duration); the hardware name alone becomes `no`.
3. Papers with no experiment (Q1 `no`): Q2 to Q8 and X1 to X4 are `na` and leave the
   denominators; Pineau 2018 reports 100% with experiments, so her denominators are the
   experimental papers.
4. Q7 for `theory` papers with toy experiments: `no` (not `na`), as coded.
5. X3, selection unstated but visible: when the paper's own tables show that the main result is
   the best of several identical training runs (LR10: 23.00 = best of 19.87, 21.58, 23.00),
   X3 becomes `yes`. Recoded from the quotations.
6. Q5 "will be made public at <URL>": `no`, as the protocol says; a project page that
   announces the code: `yes` only if the link leads to code (checked at analysis).
7. Calibration: on our 12 papers from 2018, our grid is stricter than Pineau's on Q3 (60%
   against 90%) and more lenient on Q7 (40% against 10%). We therefore conclude that something
   changed only if the change holds both against her 2018 figures and against our own 2018
   figures (same grid, same readers); otherwise "ambiguous".
8. Appendices: the calibration reader read the separate 2018 appendices (ICML -supp.pdf,
   NeurIPS zip); in 2026, the appendices are inside the main PDF. C21 (NeurIPS 2018) has no
   published appendix.
9. The first downloads sent a contact address in the User-Agent header; it was removed
   afterwards, with no effect on the data.
10. The scratchpad is shared between readers; some working scripts were overwritten along
   the way. The codings themselves sit in separate folders and were not touched.
11. **Grid v2, written on 9 November 2026 BEFORE any v2 coding.** Grid v1 covers only part of the flaws Pineau showed in 2018 (ICLR, NeurIPS, checklist v1.2, Henderson et al.). We add, for the same 50 + 12 papers, with the same rules (`yes` / `no` / `na`, quotation mandatory):
    - Y1 performance measure defined (final return, average over training, area under the curve, pass@k…) and stated; ICLR slide 27.
    - Y2 error bars defined (what the band or interval represents); checklist v1.2.
    - Y3 number of tasks or environments the main conclusion rests on (integer); ≥ 2 if the conclusion is general; Henderson table 3.
    - Y4 ranking or gain discussed task by task (a task where the method loses is shown or stated); Henderson table 3.
    - Y5 baseline implementation identified (repository, library and version, or reimplementation stated); Henderson figure 6.
    - Y6 excluded runs or data stated (or explicitly "none"); checklist v1.2.
    - Y7 version of the environment or benchmark given (e.g. `HalfCheetah-v4`, version of MATH-500 or of the test set); checklist v1.2.
    - Y8 generalization test beyond the training conditions (other environment random seeds, other tasks, modified dynamics, distinct test distribution); Pineau's roadmap, pages 37 to 51 of her NeurIPS document.
    - Y9 hyperparameter sensitivity shown (sweep or ablation of at least one hyperparameter); ICLR talk, slides 24 to 26.
    - Y10 software dependencies listed (versions or environment file); checklist v1.2.
    - Y11 type of uncertainty named (standard deviation, standard error, CI, interquartile range); comparable to Gorsane et al. 2022.
    - Y12 post-2018 statistical tools used (IQM, bootstrap CI, rliable, performance profiles, probability of improvement); measures the adoption of Agarwal et al. 2021.
    Analysis identical to v1 (Wilson, 2018 calibration as a safeguard). Status: preregistered, coding not started. Y11 and Y12 added the same day, after the search for related work, still before any coding.
12. **Widening of the survey, written on 9 November 2026 BEFORE any draw and before any reading of the added papers.** The audit (`audit_stats.py`) shows that our 2018 calibration (12 papers) and our 2026 classic RL (14 papers) lack power: a 30-point difference goes undetected there. We add two samples, read with grid v1 and grid v2 in a single pass, same rules, quotation mandatory.
    - **A2, 2018 calibration raised to 50 papers.** Population: the RL papers (same title regular expression) of ICML 2018, NeurIPS 2018 and, if its list of accepted papers can be obtained, ICLR 2018, the three conferences Pineau names. The current 12 papers stay. The other 38 are drawn in the order of a `random.Random(2018)` shuffle of the rest of the population, split in proportion to each conference's size in the population. A paper with no freely accessible PDF is replaced by the next one in draw order; the replacement is recorded.
    - **A3, 2026 classic RL raised to 50 papers.** Population: the 1,252 papers of `rl_population_2026.json`, minus the 50 already read. Order: a `random.Random(2026)` shuffle. Prior screening on the title alone, fixed here: a title that contains `LLM`, `language model`, `reasoning`, `RLHF`, `RLVR`, `GRPO`, `preference`, `alignment`, `reward model`, `chain-of-thought`, `math` or `agentic` (case-insensitive) is presumed `llm` and skipped. The other titles are read in order. The reader codes the family (X5) as before; reading stops once 36 `classic` papers have been coded. The `llm` and `theory` papers read along the way stay coded and are reported separately: they do not join the 2026 random sample, since the title screening filtered them.
    - **Grid v2 (deviation 11)** applied as well, in the same pass, to the 62 papers already read.
    - **Reliability**: 10 papers drawn at random from the new ones (`random.Random(7)`) are reread by a second agent who does not see the first reading. Agreement is computed on the raw readings, before harmonization.
    - **Analysis**, fixed in advance and identical to `audit_stats.py` (Newcombe interval, Fisher's exact test, Holm correction). Main comparison: 2026 classic RL (50 papers) against our reading of 2018 (50 papers). Secondary comparisons: 2026 (all) against Pineau; our reading of 2018 against Pineau, which measures how far our grid differs from hers.
    - **Harmonization**: the rules of deviations 1, 2, 5 and 6 apply. Any new rule is written here before the first percentage.
13. **Blind human review (A1), written on 9 November 2026 before any review.** Warith alone rereads 10 papers from 2026, the first 10 experimental papers outside the double reading in the order of a `random.Random(2027)` shuffle (NE16, LR16, LR05, MLR06, LR02, LR08, ML03, NER06, ML06, ML15), on criteria Q4, Q5, Q6, Q7, Q8, X1 and X2, without seeing the agents' readings. Form and rules: `relecture_humaine/`. Agreement and Cohen's kappa computed on the agents' raw readings (`relecture_humaine/compare.py`). Disagreements are reported one by one, with both quotations; no agent code is modified afterwards on the strength of this review without a dated deviation.
14. **Decision rules for grid v2, written on 9 November 2026 BEFORE any v2 coding** (a complement to deviation 11, which defined the criteria without their edge cases). They apply to the 62 papers already read as well as to those of deviation 12. Sheet handed to the readers: `GRILLE.md`. Mechanical check of each file: `check_codes.py`.
    - **Scope.** If Q1 is `no` in v1 (no experiment), Y1 to Y12 are `na` (same rule as
      deviation 3). For a `theory` paper with toy experiments, code normally.
    - **Y1, measure defined.** `yes` if the paper says what the reported number contains: final
      return, average over the last N episodes, area under the curve, pass@k with k and the
      number of samples, success rate and over what. "Return" or "accuracy" and nothing more: `no`.
    - **Y2, error bars defined.** `yes` if the paper says what the band or interval represents
      (standard deviation, standard error, 95% CI, min and max). `na` if there is no bar and no
      band at all (X2 v1 `no`). Bars present but undefined: `no`.
    - **Y3, number of tasks.** An integer: the number of distinct tasks, environments or
      benchmarks the main conclusion rests on. Two difficulty levels of the same game count as
      one. Derived value for the analysis: `yes` if the integer is at least 2.
    - **Y4, losses shown.** `yes` if a task-by-task result is given and at least one task where
      the method does not win is shown or stated. `no` if the paper gives only averages, or
      shows only tasks where the method wins. `na` if Y3 is 1.
    - **Y5, baseline implementation.** `yes` if, for each main baseline, the paper says where
      the code comes from: repository, library with its version, or "reimplemented by us". `na`
      if no baseline is compared (same rule as Q4).
    - **Y6, exclusions.** `yes` if the paper says which runs, random seeds or data were removed,
      or says explicitly that none were. Silence counts as `no`.
    - **Y7, version.** `yes` if the version of each main environment or benchmark is given:
      Gym or Gymnasium suffix, suite version, or exact name and date of the test split for `llm`
      benchmarks. "MuJoCo" alone: `no`. "MATH-500" counts as `yes`, because it is a fixed, named
      split. "MATH" alone: `no`.
    - **Y8, generalization.** `yes` if at least one evaluation covers conditions absent from
      training and tuning: other environment random seeds announced as such, new tasks,
      modified dynamics, a distinct test distribution. This is stricter than Q7: an `llm`
      benchmark different from the RL training data counts only if the paper presents it as an
      out-of-distribution test.
    - **Y9, sensitivity.** `yes` if at least one hyperparameter of the method is swept and the
      result is shown (figure, table or sentence with numbers). A component ablation does not
      count: a component is not a hyperparameter.
    - **Y10, dependencies.** `yes` if the versions of the main libraries are given in the
      paper, or if an environment file in the linked repository is cited. The repository is not
      visited, unless the paper points explicitly to the file.
    - **Y11, type of uncertainty.** Value `yes` / `no` plus a `kind` field (`std`, `se`, `ci`,
      `iqr`, `minmax`, `other`). `na` if X2 v1 is `no`. Y11 is broader than Y2: the type need
      only be named somewhere.
    - **Y12, post-2018 tools.** `yes` if the paper uses at least one of these tools: IQM,
      stratified bootstrap CI, rliable, performance profiles, probability of improvement. A plain
      bootstrap on a mean counts as `yes` if it produces a reported interval.
15. **Harmonization of the 2018 calibration (9 November 2026, AFTER seeing the percentages).** Checking the quotations that could not be found (`.private/v1_quotes_audit.md`: 89 quotations, none invented, 83 present word for word, 1 faithful paraphrase, 5 values contrary to the rules) showed that the harmonization rules of deviations 1, 2 and 4 had been applied to the 2026 papers only: `overrides.json` held no 2018 paper. The comparison between the two years was therefore made with two slightly different grids. Correction: the same rules, applied from the quotations to the 12 papers from 2018 (X4: C11, C13, C16 and C14 move to `no`; Q7: C14 moves from `na` to `no`; X7: C14 moves to `no`). No new rule. The 2018 percentages and the comparisons are recomputed by `analyze_final.py`, which now regenerates `results_final.json` (until then written without a script). The second reading (reader G) of ML16 on Q7 also contradicts deviation 4; it stays as it is, since inter-reader agreement is computed on the raw readings.
16. **Pilot of the extended reading, written on 9 November 2026 BEFORE any v2 reading and before any reading of the added papers.** Before the main readers, a pilot reader codes three papers: LR08 (`llm`) and ML15 (`classic`), grid v2 only, chosen by the rule in `.private/planification.md` (`random.Random(11)` over the 40 papers from 2026 outside the double reading); C218, grids v1 and v2 in one pass, the first of the 38 new 2018 papers after a `random.Random(11)` shuffle of their sorted identifiers. The pilot serves only to find ambiguous rules and to test `check_codes.py`; its files (`codes_v2/pilot/`) enter no analysis. These three papers are then recoded by their regular reader. A rule clarified after the pilot is written here, dated, before the main coding and only to resolve an ambiguity.
17. **Rules clarified after the pilot, written on 9 November 2026 BEFORE the main coding.** The pilot (deviation 16: LR08, ML15, C218) found cases the rules did not settle. Each clarification resolves an ambiguity; none targets a figure, since no v2 percentage exists.
    - **2018 appendices.** The NeurIPS 2018 appendices are retrieved from the official proceedings page (an Internet Archive copy, the site being unreachable) and stored as `pdf/<id>-supp.pdf`: 9 of the 14 new NeurIPS papers have one (C28, C29, C210, C212, C213, C214, C215, C216, C218); the pages of the other 5 (C27, C211, C217, C219, C220) list none. A paper that refers to an appendix that cannot be found is coded on what exists; the reader notes it in `doubts`.
    - **Y1.** `yes` requires the quantity and the measurement point (final, last N episodes, best point, area under the curve). A normalized score with no statement of the point at which it is taken: `no`. The number of evaluation episodes is not required.
    - **Y3.** A task is a distinct training setting on which the method is trained and compared: an environment, or a training dataset for `llm`. Several evaluation benchmarks for one trained model do not multiply the tasks. Quality variants of a dataset from the same environment (D4RL medium, replay, expert) count as a single task, like difficulty levels.
    - **Y5.** Baseline figures copied from published papers, with the source cited for each, count as `yes`: the origin of the figures is stated.
    - **Y6.** A combination left out of the results (model, dataset, task) with its reason counts as a stated exclusion.
    - **Y7.** "Each" stays strict. A dataset published on a named repository (a Hugging Face link, for example) counts as versioned; a split built by the authors counts only if it is published.
    - **Y8 and Q7.** New training random seeds, used for training, are not held-out conditions: `no` for Y8 and `no` for Q7 under the v1 rule ("not seen during training or tuning").
    - **Y9.** A hyperparameter counts if the paper presents it as one. A variant the paper presents as a component remains an ablation.
    - **Y11.** Percentile bands other than the interquartile range: `kind` = `other`.
    - **Scope.** For papers already read in v1, the reader receives the v1 values of Q1, Q4 and X2, which set the scope rules; the reader does not see the other v1 codes.
    - **Format.** A quotation stitched across two pages may have a list of pages. In a two-column PDF, the reader cuts a quotation that spans lines into one-line pieces joined by "[...]".
    - **A3, PDFs not found.** A paper in the queue with no freely accessible PDF is skipped, as for A2. The 9 ICLR 2026 papers at the head of the queue (K007, K018, K020, K022, K025, K026, K027, K029, K031) were unreachable on 9 November 2026 after two attempts, the proceedings site being down: they are skipped too. The queue is frozen as it stands so that the selection does not depend on the reading date.
18. **X5 clarified, written on 9 November 2026 AFTER reading the A3 queue and BEFORE freezing the sample and computing any percentage.** X5 decides whether a paper from the A3 queue enters the classic sample. The v1 definition ("RL applied to a large language model or vision-language model") is read on the model the RL trains: `llm` if the optimized policy is a pretrained generative model conditioned on language (a language model of any size, a vision-language model, a text-to-image model); `classic` if the RL trains something else, even in the service of a large model (a data selection mask, a reward machine written by an untrained foundation model), or a network of transformer architecture trained from scratch on RL tasks. `theory` remains reserved for papers with no experiment or with toy experiments only; a paper with theoretical results that compares methods on standard benchmarks, even in an appendix, is `classic`. Applied to the X5 quotations of the 120 papers read, the rule changes only one code: K006 moves from `llm` to `classic` (`overrides_v2.json`). The 50 papers of the first sample and the 50 from 2018 already comply with it.
19. **Harmonization of grid v2, written on 9 November 2026 AFTER the audit of the raw readings (`harmonisation_audit.md`) and BEFORE any percentage.** The audit rereads every file criterion by criterion, without counting any `yes`. It finds codes contrary to the rules and ten cases no rule settled. The decisions below apply to both years, from the quotations, in `overrides_v2.json`, each change with its reason. Inter-reader agreement stays computed on the raw readings.
    - **Y1.** A learning curve whose evaluation points are stated counts as a measurement point. "Trained N steps" followed by a single figure for the trained model counts as the final point. For a quantity that is not the score of a trained policy (an estimator's error, computation time, a statistical test, a solver's output), the measurement point does not apply: `yes` if the quantity is defined. Otherwise the rule of deviation 17 applies as written.
    - **Y3.** A single meta-training (in-context RL, meta-RL) counts as one task. A setting present only in an appendix does not count.
    - **Y5.** These count as a stated origin: a named repository, library or software framework, with or without a version (the version belongs to Y10); "reimplemented by us"; figures copied with their source (deviation 17); a published model designated by its exact name and evaluated by the authors; the authors' own training framework, if the paper says the baselines run in it. A reimplementation implied but never stated does not count. "Each" applies to the main baselines: a single one with no origin gives `no`.
    - **Y6.** A stated filtering of the training data, with what it removes, counts as a data exclusion.
    - **Y7.** A benchmark or split designated by a name that fixes a single published set counts like MATH-500. A name that covers several sets or several years without saying which one ("MATH", "AMC", "Minerva") does not count. An environment fully specified in the paper (equations, parameters) counts as versioned.
    - **Y8.** For `llm`, a benchmark presented explicitly as a generalization to a domain or task absent from training counts; a different benchmark without that claim does not count. An i.i.d. test split from the same distribution falls under Q7, not Y8. Y8 `yes` presupposes Q7 `yes`: if a paper's two codes contradict each other, the passage is reread and the value of Y8 follows that reading; Q7 v1 is not recoded.
    - **Y9.** A parameter set at inference counts if it is presented as a hyperparameter; a condition of the environment does not count; the result shown must be a performance measure.
    - **Q5 (deviation 6).** Each link to a project page is visited on 9 November 2026: `yes` if the page leads to code, `no` if it does not or no longer responds. An anonymous mirror that contains the code counts as `yes`.
    - **X3, X4, X7 (v1).** No new rule: a rule added now would apply only to the papers of the extended reading, which deviation 15 forbids. The edge cases the audit found (inference time alone, failed random seeds discarded) stay coded as the reader read them; the text mentions them among the limitations.
    - **Application (9 November 2026, before any percentage).** 80 changes, each with its reason in `overrides_v2.json`: Y1 21, Y3 5 (and Y4 5 through the scope rule), Y5 10, Y6 3, Y7 19, Y8 6, Y9 9, Q5 2. Project pages visited: five lead to code, two do not (K090: anonymous mirror expired, HTTP 410; C19: the page leads to a library published after the paper, without its scripts). Two cases decided by the project lead, Warith Harchaoui: for NE16 and ML14, all of whose experiments are in the appendix, the rule "a setting present only in an appendix does not count" does not apply: Y3 stays as the reader coded it.
20. **The document's verdict rule, decided on 9 November 2026 AFTER the first results of the extended reading.** Until now, a criterion "had changed" when the difference held against Pineau's figures; the change was "confirmed" against our reading of 2018. The secondary comparison of deviation 12 shows that our grid reads 2018 differently from Pineau (Q3: 55% against 90%, Holm p = 0.001; Q7: 33% against 10%, Holm p = 0.03). Comparing 2026 with her figures therefore mixes two changes. From now on, a verdict of the document rests only on the main comparison of deviation 12 (2026 classic RL against our reading of 2018, same grids, same readers), fixed before any reading of the added papers; the comparisons with Pineau are still shown as context. This rule change is decided after seeing these results: we declare it as such.
21. **Analyses answering a reviewer, written on 10 November 2026 AFTER the results of the extended reading and BEFORE computing them** (simulated review method of ScientistTwo, arXiv 2609.19644: look for the limitations, then run the analyses that answer them). All are exploratory; none changes a verdict of deviation 20, they only say whether it is fragile. Script: `robustness.py`, output `robustness.json`.
    (a) **Solidity of the four "changed" verdicts** (Q5, Y9, X7, X2) and of the two intervals that exclude zero without passing Holm (Q6, Y12). Four cuts: (a1) 2026 classic RL split by provenance, first draw (14, no title screening) against the A3 queue (36, with screening), Fisher's test within 2026, then the main comparison redone with each provenance alone; (a2) by the source of the PDF read in 2026, arXiv against proceedings or conference site, Fisher's test; (a3) a Cochran-Mantel-Haenszel test stratified by conference (ICML, NeurIPS, ICLR), to rule out an effect of conference composition; (a4) the main comparison redone leaving out each main reader in turn (A2 to F2, H1 to H4, K1 to K7). Reading: a verdict is called fragile if, in some cut, the difference changes sign or if the Newcombe interval of the redone main comparison contains zero while the sample keeps at least 35 papers on each side.
    (b) **The thesis "listened to where it cost little", put to the test.** Until now, the sorting of practices into "cheap" and "costly" comes from us, after seeing the differences. Three independent raters (language agents, with no access to the results or the repository, who receive only the label and the rule of each criterion) each score the 17 criteria of the main comparison on two scales from 1 to 5: C, the cost in labor or compute for an author who already has their main results; R, the risk that the practice weakens or changes the main conclusion. We take the median of the three. Test: Spearman correlation between each scale and the observed difference (X3 reversed, since a lower share there is progress), with a permutation p-value (10,000 permutations, random seed 2026). Reading: a clear negative correlation supports the thesis; a null or positive correlation contradicts it, which the document will state.
    (c) **Correction of 10 November 2026.** Cut (a2) first read a damaged local copy of `classic_queue_2026.json`, in which 219 papers had lost their `pdf_src` field. Redone on the committed file, it sets 45 papers read on arXiv against 5 read on a conference site: the cut cannot settle anything. The document no longer relies on it and lists this difference of source among the limitations. The other cuts and (b) do not change.
22. **What papers declare, against what they do (A5), written on 10 November 2026 BEFORE any checklist was extracted.** NeurIPS 2025 papers come with the checklist their authors filled in. Sample: the 30 NeurIPS 2025 papers already read (16 from the first draw, those on large language models included, and 14 from the A3 queue), with no new reading. Source: the official proceedings version (proceedings.neurips.cc), found by title in the volume 38 listing, because the arXiv versions we read often leave the checklist out. Mechanical extraction (`pdftotext`, `checklist.py`) of the answer `[Yes]`, `[No]` or `[NA]` and of the justification for four questions: "Open access to data and code", "Experimental setting/details", "Experiment statistical significance", "Experiments compute resources". Comparison fixed in advance with our harmonised codes: code (Q5), settings (Q3), statistical significance (X2 for uncertainty, Q8 for a test), compute (X7). Measure: for each question, the share of papers that declare `[Yes]` while our code is `no`, with its Wilson interval. Two precautions, stated in advance: the NeurIPS checklist accepts code deposited as supplementary material, which our Q5 does not count; and our codes often come from the arXiv version. For each disagreement on code, we therefore look for a link to code in the proceedings version and report both figures. A paper with no readable checklist in the proceedings is counted apart.
23. **Blind human review (A1, deviation 13) abandoned**, decision of Warith Harchaoui on 10 November 2026, before any review. The document says so among its limitations: no human reread the papers; each decision remains checkable through its quotation. The folder `relecture_humaine/` is kept as it is, as a record of the plan.
