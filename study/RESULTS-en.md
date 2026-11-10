*Translation of [RESULTS.md](RESULTS.md), made on 10 November 2026. The French text is the original.*

# Results: Pineau's grid (2018) reapplied to 50 RL papers from 2025-2026

Sample: 50 papers drawn at random from the 1,252 RL papers of ICLR 2026, ICML 2026
and NeurIPS 2025 (27 RL on large models, 14 classical RL, 9 theory, 5 of them without experiments).
Calibration: 12 RL papers from ICML and NeurIPS 2018, same grid, same readers.
Agreement between two independent readers on 10 papers: 127 decisions out of 130 (98%).
Percentages over the experimental papers; 95% Wilson interval. Data:
`results_final.json`, `codes/`, `overrides.json`.

| criterion | Pineau 2018 | us, 2018 | us, 2026 [95% CI] | verdict |
|---|---|---|---|---|
| The paper has experiments | 100% | 11/12 | 90% [79, 96] | ambiguous (more theory) |
| Neural networks | 90% | 9/11 | 89% [77, 95] | no change |
| Hyperparameters of the method, all of them | 90% | 6/10 | 67% [52, 79] | ambiguous (our grid is stricter) |
| Hyperparameters of the baselines, all of them | 60% | 6/11 | 18% [10, 32] | **regressed** |
| Code linked | 55% | 6/11 | 67% [52, 79] | no change (upward trend) |
| Method for choosing hyperparameters | 20% | 2/10 | 27% [16, 41] | no change |
| Held-out evaluation | 10% | 4/10 | 70% [56, 82] | **improved** (mostly RL on LLMs: 26/27; classical 5/13) |
| Significance test | 5% | 1/11 | 4% [1, 15] | no change |
| Uncertainty reported | n/a | 8/11 | 47% [33, 61] | drop driven by RL on LLMs (4/27; classical 14/14) |
| Baselines tuned like the method | n/a | 4/10 | 5% [1, 15] | drop (small calibration) |
| Compute reported | n/a | 4/11 | 47% [33, 61] | no change |
| Selection of the best runs visible | n/a | 0/11 | 2/45 | rare, but still there |

Random seeds: of 41 experimental RL papers, 20 do not say how many independent training runs
support their results; 4 have only one; median of the others: 5.
RL on LLMs: 16 papers out of 27 try only one family of base models (corrected on 9 November 2026: 15 before the recount by `docs/check_numbers.py`).
