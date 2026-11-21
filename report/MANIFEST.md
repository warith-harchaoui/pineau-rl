# Technical report: the contract between its parts

The technical report is the PDF the blog article links to as « le document complet » / "the full document":
French `report/rapport.pdf`, English `report/report-en.pdf`, published on deraison.ai under
`assets/pdf/`. It must be exhaustive and technical: everything the repository did, how the code does it,
every result with its interval, every deviation. It replaces nothing: `docs/conclusions*.md` stays the
argued essay; the report is the reference document.

## Layout

```
report/
  preamble.tex, titlepage.tex      shared (do not edit without need)
  rapport.tex, report-en.tex       main files: \def\reportlang{fr|en}, \input of every chapter
  fr/NN-*.tex, en/NN-*.tex          chapters (00-resume ... 11-conclusion, A-grille ... D-environnements)
  gen/fr/*.tex, gen/en/*.tex        GENERATED tables, by tools/tables.py from the result JSON files
  figures/<name>-fr.pdf, -en.pdf    figures, by tools/figures.py (PDF converted from house SVGs)
  refs.bib                          bibliography (biblatex, authoryear); add entries as needed
  build.sh                          tables, figures, then latexmk -lualatex twice (fr, en)
```

Chapters are `\chapter{...}` bodies, no preamble. Use `\gentable{name}` for a generated table and
`\fig{name}{caption}` (or a figure environment with `\includegraphics{name-\reportlang}`) for a figure.
Labels: `tab:<name>`, `fig:<name>`, chapters `chap:<file stem>`, sections `sec:<short>`.
Cite with `\textcite{key}` / `\parencite{key}` (keys in refs.bib).

## Numbers

Every number comes from a result file, never from memory: `study/*.json`, `sim/analysis/*.json`,
`sim/llm/results/*.json`, or the already-checked texts `docs/conclusions.md` / `-en.md` and
`article/fr.txt` / `en.txt`. Tables are generated, never typed. In prose, prefer referring to a table;
when a number is written in prose, it must match its JSON exactly (same rounding as the docs).
Ten random seeds are the main, preregistered results; twenty seeds (suffix `_s20`), equal budget
(`_equal`) and replications (`_r10`) are given next to them, every divergence stated.

## Generated tables (gen/<lang>/<name>.tex, each a complete table environment with caption and label tab:<name>)

| name | content | source |
|---|---|---|
| sondage-pineau | Pineau's criteria: share 2018 (k/n, %, Wilson 95%), share 2026 classical RL, Newcombe difference with interval, Fisher p, Holm-adjusted p | study/extension_stats.json, study/results_final.json |
| sondage-pineau-contexte | Pineau's own 2018 figures against our 2018 reading and the first 2026 draw, criteria Q3 to Q8 | study/results_final.json, extension_stats.json |
| sondage-extension | our criteria Y1 to Y12, same columns | study/extension_stats.json |
| sondage-lrl | the large-language-model RL papers of 2026 against classical RL, where the JSON has it | study/extension_stats.json |
| trajectoire | per practice and year (2018, 2019-2024, 2026): share and n; Cochran-Armitage trend p | study/trajectory.json |
| accord | agreement between the blind double readings per criterion (kappa, raw agreement, n) | study/agree_v2.json |
| robustesse | the robustness checks of the survey (each alternative analysis and whether each conclusion survives) | study/robustness.json, extension_stats_sans_opus5.json, extension_stats_falsify_*.json |
| e1 | E1: thirty PPO runs on HalfCheetah: mean, median, min, max, IQM; false-positive rate of a t-test at 5% for random and for sorted groups | sim/analysis/e1.json |
| b1 | B1: share of draws where the average t reaches 9.09, per algorithm (TRPO, PPO) and per way of computing t (seeds, Henderson's script) | sim/analysis/b1_script.json, b1_trpo.json |
| e2 | E2: IQM with stratified-bootstrap 95% interval per program and task, leader per task; 10 seeds, 20 seeds, equal budget | sim/analysis/e2*.json |
| e2-bonferroni | E2 pairwise probability of improvement with Bonferroni intervals | e2_bonferroni*.json |
| e3 | E3: PPO PyTorch against PPO JAX per task: both IQMs, gap, probability of improvement | e3*.json |
| e4 | E4: inflation of the mean when the best three of ten runs are kept, per program and task; reversals among the 24 comparisons; the replication on seeds 10-19 | e4.json, e4_r10.json |
| e5 | E5: how many random seeds recover the ranking, per pair and task | e5*.json |
| e6 | E6: the reference method: default values against the published RL Baselines3 Zoo settings, our pipeline and the official one | e6*.json |
| e7 | E7: share of score kept under modified physics, per program and task, interval and verdict | e7*.json, e7_rank*.json |
| dose | E7 at several strengths: pairs losing per change of masses and friction, 10 and 20 seeds | dose*.json |
| b3 | B3: does the measure (final, best, mean of curve) change the ranking | b3*.json |
| grpo | GRPO: per model, reward, seed: success at start and after 100 steps, device, truncated share | sim/llm/results/summary_5.json, extra_5.json, gains_5.json |
| ecarts | every deviation of the three protocols (study, SIM, LLM): number, date, before/after results, one-line summary | study/PROTOCOL.md, sim/SIM_PROTOCOL.md, sim/llm/LLM_PROTOCOL.md (and -en) |
| env | pinned versions of the key packages per environment | envs/*.lock, envs/*.txt |
| calcul | compute: runs per program and task, steps, median wall time, core-hours | sim/logs, sim/results |
| articles-2026 | longtable of the 2026 papers read (id, title, venue) | study/final_2026.json, sample files |
| articles-2018 | longtable of the 2018 papers read | study/calib_2018*.json, rl_population_2018.json |

## Figures (figures/<name>-fr.pdf and -en.pdf)

Existing, converted from SVG (article/figures/<name>-<lang>.svg, desktop version):
e1-graines, e1-faux-positifs, t-de-neuf, meilleurs-sur-dix, classement-taches, physique-modifiee,
intensites, grpo-graines, grpo-coupure, grille-egale, trajectoire.
Existing, from docs/figures (<name>.svg is French, <name>-en.svg English): e1-henderson, ecarts-classique,
ecarts-pineau, remesure-dumbbell, remesure-ic, grpo-truncation.

New, drawn in the house style (article/figures/draw.py toolkit, Roboto, signature Deraison.ai):
| name | content |
|---|---|
| courbes-apprentissage | 4 x 4 small multiples: evaluation curve of every program on every task, IQM line with its 95% band over the 10 seeds, individual seeds faint |
| forest-criteres | every criterion (Pineau's and Y1-Y12), 2018 against 2026: two dots and the Newcombe interval of the difference, significant ones highlighted |
| accord-lecteurs | agreement between blind readings per criterion (kappa with interval when available) |
| e5-graines | probability of recovering the true ranking as a function of the number of random seeds |
| e7-carte | heatmap: share of score kept under modified physics, 4 programs x 4 tasks, verdict marked |
| dose-carte | heatmap: pairs losing per change of masses and friction, 10 and 20 seeds side by side |
| b1-distribution | distribution of the t statistic over the random draws, seeds-based t against Henderson's script, the 9.09 line |
| grpo-courbes | GRPO evaluation curves per model, reward and seed over the 100 steps |
| flux-sondage | flow diagram of the survey: populations, draws, readers, double readings, harmonisation, final counts |
| frise-ecarts | timeline of the protocols and their dated deviations, 9 to 21 November 2026 |
| architecture | the repository as a pipeline: runs -> results CSV -> analysis scripts -> JSON -> check_numbers / check_article -> documents, with make targets and CI |

## Style

French chapters follow ~/ai_dangers/bien-ecrire.md (section 6, proscribed forms, without exception: no
", et", no em/en dash, no "geste", no "bout", no balancing semicolon in prose) and the reader of
~/ai_dangers/.private/georges-glass.md (no unclear referent, no "donc" without premise, every term defined
before use). English chapters follow ~/ai_dangers/good-writing.md and are native English, not translated
French. Technical register: precise, complete, formulas where they help (amsmath), short sentences.
Vocabulary: "programmes IA"/"modèles IA", "modèles d'IA générative"; RLHF is never called RL; the four
programs of the experiments are "programmes" (PPO PyTorch, PPO JAX, SAC, CrossQ), "algorithme" for the
method; "Joelle" without diaeresis. Name files with \file{...}, algorithms with \algo{...}, tasks
with \task{...}.
