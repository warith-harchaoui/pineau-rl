# Prompt given to audit-raw-codes

- description of the Agent call: Audit raw codes against rules
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T18:50:27.153Z (main transcript line 4125, by claude-opus-5-5)
- agent id: aa714ac5c16f61a55
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You audit the raw readings of a reproducibility survey of RL papers, in ~/pineau-rl/study/, BEFORE any percentage is computed. Your job: find codes that contradict the written decision rules, so the lead can write harmonisation rules. You must NOT compute or report any share/count of "yes" per criterion or per year/sample, and must not run extension_stats.py, analyze*.py or audit_stats.py. Do not read docs/, .private/, results_*.json, audit_stats.json, extension_stats*.

Rules to apply: study/GRILLE.md, and study/PROTOCOL.md écarts 1 to 6 (v1 harmonisation: X4, X7, Q7 for theory, X3, Q5 project pages), 14 (v2 rules), 17 and 18. Read them in full first.

Files to audit: every JSON in study/codes_v2/{A2,B2,C2,D2,E2,F2,H1,H2,H3,H4,K1,K2,K3,K4,K5,K6,K7}/ (skip G2, R2, pilot). Each has criteria with value, quote, page, and "doubts". Papers already read in v1 (ids not starting with C1x/C2x/C3x of the A2 extension, nor K) only have Y1–Y12; the C1*, C2*, C3* files in H1–H4 and the K* files have v1 too. PDFs are in study/pdf/ if you need to check context (pdftotext).

Work criterion by criterion across ALL readers (not file by file). Priority criteria, where readers are known to diverge:
1. Y1: écart 17 requires the measure AND the point of measurement (final, last N, best, AUC). Find yes codes whose quote gives no point of measurement, and no codes where the paper does give it.
2. Y5: écart 14/17. Readers diverged on llm papers whose baselines are published models named exactly (some coded yes, some no), and on baselines "implicitly" reimplemented but never said. List every Y5 with its basis, grouped by type of basis: (a) repo/library named, (b) "reimplemented" said, (c) numbers copied with source per baseline, (d) published model named/cited and evaluated by the authors, (e) implicit, never said. Do not decide; classify.
3. Y3: écart 17 (training settings, not evaluation benchmarks; dataset-quality variants and difficulty levels count once). Flag values that count evaluation benchmarks, appendix-only tasks, or levels as tasks. Only the yes/no threshold (>=2) matters, so flag only cases where the correct count would cross 1 vs 2.
4. Q5 / écart 6: list every Q5 yes whose link is a project page / Google Sites / github.io / anonymous page rather than a code repository, and every "will be released" coded yes. For each project-page case, say whether the paper text says the page holds code.
5. X4 (écart 1), X7 (écart 2), X3 (écart 5), Q7 (écart 4) on the v1+v2 files (C1*/C2*/C3*, K*): flag values contradicting these rules.
6. Y7 ("chaque" strict; écart 17), Y9 (écart 17: only what the paper presents as a hyperparameter), Y6 (écart 17), Y8 (stricter than Q7): flag clear contradictions only.
7. Scope consistency: Y2/Y11 na iff X2 no; Y4 na iff Y3 is 1; for new papers v1 Q1 no -> all na.

Write your findings to ~/pineau-rl/study/harmonisation_audit.md (in English): one section per criterion; each flagged item as `paper (reader): current value -> proposed value — rule — short quote or reason`. For Y5 give the classification table instead of proposals. End with the list of rule gaps you found (cases no written rule decides). Modify no other file. Report back only a short summary: number of flags per criterion and the rule gaps.
````
