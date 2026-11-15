# Prompt given to harmonisation-ecart19

- description of the Agent call: Apply harmonisation écart 19
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T19:01:26.099Z (main transcript line 4182, by claude-opus-5-5)
- agent id: a29e8dc38e0060441
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You apply a written harmonisation to the raw readings of a reproducibility survey of RL papers, in ~/pineau-rl/study/. This happens BEFORE any percentage: you must NOT compute or report any share or count of "yes" per criterion, per year or per sample, and must not run extension_stats.py, analyze*.py or audit_stats.py. Do not read docs/, .private/, results_*.json, audit_stats.json, extension_stats*.

Read first, in full: PROTOCOL.md écarts 14, 17, 18 and 19 (19 is the harmonisation you apply), GRILLE.md, and harmonisation_audit.md (the audit that flagged items and rule gaps). Then read overrides_v2.json (it already holds X5 K006).

Scope: the primary reading files in codes_v2/{A2,B2,C2,D2,E2,F2,H1,H2,H3,H4,K1,K2,K3,K4,K5,K6,K7}/. Never edit these files and never touch codes_v2/G2, codes_v2/R2 or codes_v2/pilot (raw reads stay raw).

Task: for each criterion that écart 19 decides (Y1, Y3, Y5, Y6, Y7, Y8, Y9, Q5), go through EVERY primary file (not only the flagged ones) and decide the value under écart 19 from the quote, the doubts, and the PDF (study/pdf/<id>.pdf and -supp.pdf; use pdftotext) when the quote is not enough. Where the harmonised value differs from the reader's value, add it to overrides_v2.json as criterion -> paper id -> value, and add a reason in a parallel "_reasons" object: "_reasons": {criterion: {paper id: "one sentence: rule point + evidence"}}. Keep the existing X5 entry. Values: yes/no/na, or an integer for Y3. When a change of Y3 crosses 1 vs 2, also apply the scope rule (Y4 na iff Y3 is 1; if Y3 goes from 1 to >=2, set Y4 from the paper). For Y5 apply the "chaque" rule to main baselines. For Y8 conflicts with v1 Q7 (C12, ML07), set Y8 from your reading; do not change Q7.

Q5 (écart 6 and 19): for every primary file with Q5 yes whose link is a project page, Google Sites, github.io or anonymous page (the audit lists C19, C120, K038, K056, K064, K090; check others too), visit the URL with curl (follow redirects, 30 s timeout) and decide: yes if the page leads to code (a repository link or code archive on the page), no if not or if it does not answer. Record the evidence (what you found, date 2026-11-09) in the reason. Also for papers in the first sample (v1 codes in codes/, harmonised by overrides.json), do NOT change Q5: only codes_v2 files are in scope.

Write overrides_v2.json as valid JSON with indent 1, ensure_ascii False. Then validate: every key in overrides refers to an existing primary file and an existing criterion. Report back only: number of changes per criterion, the Q5 link results (paper, URL, verdict), and any case you could not decide (paper, criterion, why). Do not paste the JSON.
````
