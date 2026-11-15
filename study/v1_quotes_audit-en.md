*Translation of [v1_quotes_audit.md](v1_quotes_audit.md), made on 15 November 2026. The French text is the dated original and prevails. It was copied unchanged from `.private/v1_quotes_audit.md`, where it was kept, and made public on 15 November 2026.*

# Audit of the 89 quotes not found (v1 grid)

Entry-by-entry detail: `v1_quotes_audit.json` (same folder).

## Summary

| Class | Count |
|---|---:|
| FOUND (quote present in the paper) | 83 |
| PARAPHRASE_OK (faithful rewording) | 1 |
| UNSUPPORTED (value contrary to the rules) | 5 |
| UNVERIFIABLE | 0 |

**No quote is invented.** The 89 failures of the automatic check have three causes:

- the reader added a comment in French, in parentheses or after a dash, to an exact English quote (most cases);
- the two-column layout: pdftotext interleaves the columns, captions and tables; there are also footnote markers stuck to words ("WGANTPP3") and badly extracted symbols (ε, ϵ, γ);
- the NeurIPS 2018 appendices of C24, C25 and C26 are missing from `study/pdf/`. The network was down during the audit, but the PDFs of these appendices, taken from the zip files of the proceedings site (archives dated 18 February 2019), were still in the scratchpad of calibration reader F. All the quotes of C24, C25 and C26 are in them.

Only one entry is a paraphrase. It is LR03 Q4: the reader's description of table 11 (p. 24), which is accurate.

Some cited pages are wrong or incomplete: C11, C15 and C16, where the page is in fact that of the -supp appendix; LR12 Q4, cited at p. 20 instead of p. 36. The right pages are in the JSON.

## The 5 values contrary to the rules

| Paper | Criterion | Coded value | Value according to the rules | Reason |
|---|---|---|---|---|
| C13 | X4 | yes | **no** | Deviation 1: the baselines (V MAX initialisations, Q*avg) share the learner and its fixed hyperparameters (ε = 0.1, α = 0.1, p. 7). No tuning is described. |
| C16 | X4 | yes | **no** | Deviation 1: "All neural networks are trained using RMSprop with learning rate 5 × 10−4" (supp. p. 3). The configuration is shared and no tuning is described. |
| C14 | X4 | na | **no** | A baseline is compared (Gurobi 7.5, p. 7; Q4 is coded yes), so `na` does not apply. No tuning is described, hence `no`. |
| C14 | Q7 | na | **no** | Deviation 4: a `theory` paper with toy experiments takes `no`, not `na`. |
| ML16 (reader G) | Q7 | yes | **no** | Each agent is trained offline, then evaluated on the same OGBench task. Tasks 2 to 5 were not used for tuning, but they were used for training. The first reader (C) already codes `no`. |

## Effect on the verdicts

- **X4, our reading of 2018** (table of `docs/conclusions.md`, "4 out of 10"): the share becomes **2 out of 11 (18%)**. The 2026 figure (5%, CI [1, 15]) stays below this point, and the verdict "ambiguous" does not change, since Pineau does not have this criterion. The gap between our 2018 and 2026 shrinks a lot.
- **To check, outside the 89**: C11 X4 is coded `yes` on "The same hyperparameters were used in all experiments." This quote was found, so it is not in the list. Yet it is the case of deviation 1. If C11 also becomes `no`, we fall to **1 out of 11 (9%)**, inside the 2026 interval: there would be no visible decline left against our own reading of 2018.
- **Q7, our reading of 2018**: the share goes from 4 out of 10 to **4 out of 11 (36%)**. The verdict "improved" (70%, CI [56, 82]) does not change. Deviation 7 of the protocol ("40% against 10%") becomes 36%.
- **ML16 Q7**: ML16 is part of the double reading, and G is the second reader. The main figures do not move, because the C reading (`no`) is the one that counts. Inter-reader agreement on Q7 gains one agreement.
- No change for Q3, Q4, Q5, Q6, Q8, X1, X2, X3, X6 or X7.

## Borderline cases kept (FOUND, defensible value)

- C12 Q7 no: the teleporter and the reward inversion modify the environment, but the agent keeps learning in it. This is adaptation, not an evaluation held apart.
- C14 Q3 and Q6 na: the written rules do not provide for this `na`. It stays defensible, because the exact method has no hyperparameter.
- ML17 Q6 no: a selection rule is given for T only. This is the same treatment as C22 Q6.
