# Prompt given to harmonisation-fork-harmonise-y6-and-y7

- description of the Agent call: Harmonise Y6 and Y7 (fork launched by the agent "Apply harmonisation écart 19", spawn depth 2; a fork inherits its parent's context)
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T19:03:12.189Z (line 65 of subagents/agent-a29e8dc38e0060441.jsonl, by claude-opus-5-5)
- agent id: a48154d8db511fcc0
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You are a fork. Handle criteria Y6 and Y7 ONLY, for every primary file (all 17 reader folders), applying écart 19 (and é14/é17). Y6: training-data filtering stated WITH what it removes counts yes — check the 15 audit yes codes actually say what is removed, and check every Y6 `no` llm/dataset paper for a stated training-data filter (grep txt for filter/remove/discard/exclude/deduplicate/decontaminat). Y7: a name fixing a single published set counts (like MATH-500); a name covering several sets/years without saying which ("MATH", "AMC", "Minerva") does not; an environment fully specified in the paper counts; "chaque" strict; authors' split counts only if published. Resolve audit cases LR08, LR10, K106, K037, K014, MLR02, NE02, NE08, MLR07, K065, K072, C115, and check all other Y7 yes/no files for consistency (e.g. "AMC 2023" is one set; "AIME 2024" one set; "Minerva Math" no). Use scratchpad dump.py/show.py and txt/<id>.txt. Do not compute any yes counts/shares. Write <scratchpad>/9cb05a27-c084-42e0-86b3-926fde3e8d7e/scratchpad/changes_Y6Y7.json as {"Y6": {...}, "Y7": {...}, "_reasons": {"Y6": {...}, "Y7": {...}}} with ONLY ids whose harmonised value differs from the reader's. Hand back: list of changes (id: old->new) and undecidable cases. Keep it short.
````
