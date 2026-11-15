# Prompt given to harmonisation-fork-harmonise-y8-and-y9

- description of the Agent call: Harmonise Y8 and Y9 (fork launched by the agent "Apply harmonisation écart 19", spawn depth 2; a fork inherits its parent's context)
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T19:03:18.895Z (line 66 of subagents/agent-a29e8dc38e0060441.jsonl, by claude-opus-5-5)
- agent id: a307987cc70414a58
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You are a fork. Handle criteria Y8 and Y9 ONLY, for every primary file (all 17 reader folders), applying écart 19 (and é14/é17). Y8: for llm, a benchmark explicitly presented as generalisation to a domain/task absent from training counts, a different benchmark without that framing does not; an i.i.d. test split from the same distribution is Q7 not Y8 (so i.i.d. held-out instances/splits -> no, unless presented as new tasks/conditions absent from training, e.g. new environment seeds announced as such per é14); Y8 yes presupposes Q7 yes — for every file compare Y8 with Q7 (Q7 is in the file for new papers, otherwise in codes/<reader other than G>/<id>.json); on conflicts (C12, ML07, any other) re-read the passage and set Y8 from your reading, never change Q7. Resolve K082, LR10, K044, K096, ML03, K081, C219, K086, K110, C32, C33, C114, NER04, K049 and check all other Y8 files. Y9: inference-time parameter counts only if the paper presents it as a hyperparameter; environment conditions (attack budget etc.) do not; the result shown must be a performance measure; component ablation is not a sweep. Resolve LR07, LR14, K068, C24, C26, K095 and check all other Y9 yes files. Use scratchpad dump.py/show.py and txt/<id>.txt. Do not compute any yes counts/shares. Write <scratchpad>/9cb05a27-c084-42e0-86b3-926fde3e8d7e/scratchpad/changes_Y8Y9.json as {"Y8": {...}, "Y9": {...}, "_reasons": {"Y8": {...}, "Y9": {...}}} with ONLY ids whose harmonised value differs from the reader's. Hand back: list of changes (id: old->new) and undecidable cases. Keep it short.
````
