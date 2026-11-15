# Prompt given to F

- grid: v1
- description of the Agent call: Code 2018 calibration papers
- session: another folder 5c5a3839
- launched: 2026-11-08T08:15:20.857Z (main transcript line 3232, by claude-opus-5-5)
- agent id: afcd3bbbc180ddc82
- subagent transcript: <transcripts of another folder>/5c5a3839-6024-4a3d-97ae-a7b9fa3acb44/subagents/agent-afcd3bbbc180ddc82.jsonl
- model (from the transcript): claude-opus-5-5

The text between the fences is verbatim, except that the absolute home-directory prefix is written "~/".

````text
Tu es le lecteur F d'une étude qui remesure, sur des articles de RL de 2025-2026, la grille que Joelle Pineau a appliquée à 50 articles de RL de 2018. Toi, tu codes l'échantillon de CALIBRATION : 12 articles de RL de 2018 (ICML 2018 et NeurIPS 2018), pour vérifier que la grille, appliquée par nous, retrouve à peu près ses chiffres de 2018. Lis d'abord en entier ~/pineau-rl/study/PROTOCOL.md : il fixe les critères (Q1 à Q8, X1 à X7), les règles de décision et le format. Ne le modifie pas. Ne cherche pas à « retrouver » ses pourcentages : code ce que tu lis.

Tes articles : les identifiants de la clé "F" dans ~/pineau-rl/study/assignments.json ; leurs métadonnées sont dans calib_2018.json et leurs PDF dans ~/pineau-rl/study/pdf/<id>.pdf (les annexes supplémentaires d'ICML 2018 sont parfois un fichier à part, -supp.pdf, sur proceedings.mlr.press/v80 : si l'article y renvoie pour les hyperparamètres, télécharge-la dans ~/pineau-rl/study/pdf/<id>-supp.pdf avec un User-Agent honnête et lis-la). Lis chaque article (pdftotext -layout, puis les sections expériences, annexes, tableaux d'hyperparamètres, liens de code) et écris ~/pineau-rl/study/codes/F/<id>.json :
{"id":..., "coder":"F", "title":..., "criteria": {"Q1":{"value":"yes|no|na","quote":"citation exacte ou 'absent après lecture de …'","page":N}, … "X1":{"value":entier ou null,…}, "X5":{"value":"llm|classic|theory",…}, "X6":{"value":entier ou null,…}, …}, "notes":"…"}
Applique les règles du protocole à la lettre. Ne regarde pas les codages des autres lecteurs. N'écris nulle part ailleurs. Rapport final : une ligne par article (id, X5, Q3, Q4, Q5, Q6, Q7, Q8, X1) et les cas difficiles.
````
