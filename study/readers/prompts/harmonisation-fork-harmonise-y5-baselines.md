# Prompt given to harmonisation-fork-harmonise-y5-baselines

- description of the Agent call: Harmonise Y5 baselines (fork launched by the agent "Apply harmonisation écart 19", spawn depth 2; a fork inherits its parent's context)
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T19:03:05.938Z (line 64 of subagents/agent-a29e8dc38e0060441.jsonl, by claude-opus-5-5)
- agent id: ad5580efb9acaa44c
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You are a fork. Handle criterion Y5 ONLY, for every primary file (all 17 reader folders), applying écart 19's Y5 rule (and é14/é17), including the "chaque" rule on main baselines. Use scratchpad tools dump.py/show.py and txt/<id>.txt (pdftotext of each PDF; -supp too). Check the PDF text whenever the quote/doubts don't settle it (especially audit "?" cases, category (b)-(f), K039, LR08, K106, K110, K044, NE04, NE06, K068, K004, MLR02, K069, K056, K063, LR17, C34, K064, K067, K089, K073, K015, C117, LR04, LR11, ML14, C31, K085, C216, K021, C217, and any non-na file the audit table omitted). Do not compute any yes counts/shares. Write the result to <scratchpad>/9cb05a27-c084-42e0-86b3-926fde3e8d7e/scratchpad/changes_Y5.json as {"Y5": {id: value}, "_reasons": {"Y5": {id: "one sentence: rule point + evidence"}}} containing ONLY ids whose harmonised value differs from the reader's value. Hand back: the list of changes (id: old->new), and undecidable cases (id, why). Keep it short.
````
