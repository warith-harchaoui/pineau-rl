# Prompt given to A

- grid: v1
- description of the Agent call: Code RL papers group A
- session: another folder 5c5a3839
- launched: 2026-11-08T08:14:53.304Z (main transcript line 3227, by claude-opus-5-5)
- agent id: ae799398ee19374d2
- subagent transcript: <transcripts of another folder>/5c5a3839-6024-4a3d-97ae-a7b9fa3acb44/subagents/agent-ae799398ee19374d2.jsonl
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
Tu es le lecteur A d'une étude qui remesure, sur des articles de RL de 2025-2026, la grille que Joelle Pineau a appliquée à 50 articles de RL de 2018. Lis d'abord en entier ~/pineau-rl/study/PROTOCOL.md : il fixe les critères (Q1 à Q8, X1 à X7), les règles de décision et le format. Ne le modifie pas.

Tes articles : les identifiants de la clé "A" dans ~/pineau-rl/study/assignments.json ; leurs métadonnées sont dans final_2026.json (ou calib_2018.json pour un identifiant en C) et leurs PDF dans ~/pineau-rl/study/pdf/<id>.pdf. Lis chaque article (pdftotext -layout, puis les sections expériences, annexes, tableaux d'hyperparamètres, liens de code, notes de bas de page ; regarde les figures si besoin) et écris un fichier ~/pineau-rl/study/codes/A/<id>.json :
{"id":..., "coder":"A", "title":..., "criteria": {"Q1":{"value":"yes|no|na","quote":"citation exacte ou 'absent après lecture de …'","page":N}, … "X1":{"value":entier ou null,…}, "X5":{"value":"llm|classic|theory",…}, "X6":{"value":entier ou null,…}, …}, "notes":"une ou deux phrases sur ce qui était difficile à trancher"}
Applique les règles du protocole à la lettre ; en cas de doute, choisis la valeur la plus défendable et explique-le dans notes. Ne regarde pas les codages des autres lecteurs (dossiers codes/ autres que le tien). N'écris nulle part ailleurs. Rapport final : une ligne par article (id, X5, Q5, Q8, X1) et les cas difficiles.
````
