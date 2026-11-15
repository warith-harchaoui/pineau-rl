# Prompt given to harmonisation-fork-q5-project-page-link-checks

- description of the Agent call: Q5 project page link checks (fork launched by the agent "Apply harmonisation écart 19", spawn depth 2; a fork inherits its parent's context)
- session: pineau-rl 9cb05a27
- launched: 2026-11-09T19:03:25.931Z (line 67 of subagents/agent-a29e8dc38e0060441.jsonl, by claude-opus-5-5)
- agent id: abeadebc52892563a
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
You are a fork. Handle Q5 ONLY, codes_v2 primary files only (Q5 is present only in files of new papers that have v1 criteria in codes_v2; do not touch first-sample papers whose v1 codes are in codes/). For every primary file with Q5 = yes, look at the quote/link; for every one whose link is a project page, Google Sites, github.io, personal site or anonymous page (not a direct github.com/gitlab/huggingface repo or code archive) — the audit lists C19, C120, K038, K056, K064, K090, check all others too — find the exact URL in the PDF text (txt/<id>.txt) and visit it: curl -sL --max-time 30 (also try once more on failure). Verdict: yes if the page leads to code (repository link or code archive on the page; for anonymous.4open.science, the mirror containing code files counts yes — its pages are JS-rendered, so query its API e.g. https://anonymous.4open.science/api/repo/<id>/files/ if needed), no if not or no answer. Google Sites: grep the HTML for github.com / code links. Date of check 2026-11-09. Write <scratchpad>/9cb05a27-c084-42e0-86b3-926fde3e8d7e/scratchpad/changes_Q5.json as {"Q5": {id: "no"}, "_reasons": {"Q5": {id: "é6/é19: <URL> visited 2026-11-09: <what was found>"}}} with ONLY ids that change; also write scratchpad/q5_checks.txt listing every checked paper, URL, what found, verdict (including those that stay yes). Hand back the table (paper, URL, verdict, evidence in a few words) and any undecidable case.
````
