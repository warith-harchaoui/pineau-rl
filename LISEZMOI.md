# A-t-on écouté Joelle Pineau en 2018 ?

*English version: [README.md](README.md)*

En 2018, Joelle Pineau a montré, à ICLR puis à NeurIPS, seize failles qui rendaient peu crédibles
les résultats de l'apprentissage par renforcement profond (RL). Parmi elles : du code absent, des
réglages tus, des méthodes concurrentes mal réglées, trop peu d'essais, aucun test statistique,
une évaluation sur les conditions d'entraînement. Ce dépôt mesure, faille par faille, ce qui a
changé depuis.

Il contient tout ce qu'il faut pour refaire chaque chiffre et chaque figure du document. C'est
un argument de la thèse : un travail sur la reproductibilité se doit d'être reproductible.

**État au 13 novembre 2026** : toutes les expériences et les lectures annoncées sont faites. Les
limites qui restent sont dites dans le document, dans sa section « Limites ».

## Le document

- Français : [`docs/conclusions.md`](docs/conclusions.md), compilé en
  [`docs/conclusions.pdf`](docs/conclusions.pdf).
- Anglais : [`docs/conclusions-en.md`](docs/conclusions-en.md), compilé en
  [`docs/conclusions-en.pdf`](docs/conclusions-en.pdf).

## Deux instruments

**Un sondage des articles** (`study/`).
- Nous relisons 50 articles de RL tirés au sort parmi les 1 252 d'ICLR 2026, d'ICML 2026 et de
  NeurIPS 2025, avec la grille de lecture de Pineau et une seconde grille (Y1 à Y12). Nous avons
  complété les articles de RL classique jusqu'à 50, puis lu 50 articles de 2018 avec les mêmes grilles. Les
  verdicts comparent le RL classique de 2026 à notre propre lecture de 2018, parce que notre
  grille lit 2018 autrement que celle de Pineau.
- La lecture est faite par des agents de modèle de langue. Chaque décision s'appuie sur une
  citation exacte de l'article, avec sa page. Vingt articles ont été lus deux fois à l'aveugle.
  Aucun humain ne les a relus : les citations permettent à chacun de vérifier chaque décision.
- Le protocole a été écrit avant toute lecture. Les écarts y sont consignés avec leur date.

**Des expériences** (`sim/`). Nous refaisons les expériences de 2018 avec les algorithmes de 2026 :
- PPO en deux implémentations, SAC et CrossQ ;
- quatre tâches MuJoCo, dix graines aléatoires par couple, trente pour l'expérience E1 ;
- une évaluation sur des graines aléatoires jamais vues et sur une physique modifiée ;
- un volet sur les grands modèles de langue : GRPO écrit à la main, vraie récompense contre
  récompense tirée au sort.

Le protocole a été écrit avant le premier entraînement. Aucun essai n'est retiré, et les erreurs
restent dans les résultats, y compris les nôtres.

## Le contenu du dépôt

| Dossier ou fichier | Contenu |
|---|---|
| `study/PROTOCOL.md` (anglais : `PROTOCOL-en.md`) | Le protocole du sondage : population, tirage, grille, règles de décision, écarts. |
| `study/GRILLE.md`, `study/RESULTS.md`, `study/harmonisation_audit-fr.md` | La fiche des lecteurs, les premiers résultats, l'audit des lectures brutes. |
| `study/codes/<lecteur>/<article>.json` | Une décision par critère et par article, avec citation et page. |
| `study/final_2026.json`, `study/calib_2018.json` | Les articles tirés, avec leurs adresses. |
| `study/analyze.py`, `study/audit_stats.py`, `study/extension_stats.py` | Les pourcentages, l'audit des différences (Newcombe, Fisher, Holm), puis le sondage élargi. |
| `sim/SIM_PROTOCOL.md`, `sim/llm/LLM_PROTOCOL.md` (anglais : suffixe `-en`) | Les protocoles des expériences et leurs écarts. |
| `sim/run.py` | Un entraînement : algorithme, tâche, graine aléatoire, nombre de pas. |
| `sim/jobs.txt`, `sim/drive.sh` | La liste complète des entraînements et le lanceur. |
| `sim/results/` | Les courbes d'évaluation de chaque essai (CSV). |
| `sim/models/` | Les politiques finales, pour réévaluer sans réentraîner. |
| `sim/analysis/` | Un script et un fichier JSON par expérience. |
| `sim/llm/` | GRPO, le diagnostic de longueur et les résultats. |
| `slides.md` | Les diapositives de Pineau à ICLR 2018, décrites une à une. |
| `docs/` | Le document en deux langues, la bibliographie et les figures (`docs/figures/build.py`). |

## Refaire les résultats

Matériel utilisé : un Mac à puce Apple M2 Max, Python 3.11.

```bash
# Trois environnements, versions figées
python3.11 -m venv sim/env     && sim/env/bin/pip install -r sim/requirements.lock
python3.11 -m venv sim/env-an  && sim/env-an/bin/pip install -r sim/requirements-analysis.lock
python3.11 -m venv sim/env-llm && sim/env-llm/bin/pip install -r sim/requirements-llm.lock

# Le sondage : pourcentages et audit des différences (quelques secondes)
cd study && ../sim/env-an/bin/python analyze.py && ../sim/env-an/bin/python audit_stats.py && ../sim/env-an/bin/python extension_stats.py && cd ..

# Retélécharger les PDF des articles lus (non redistribués ici)
cd study && python3 fetch.py final_2026.json pdf && cd ..

# Une expérience : un entraînement (PPO, HalfCheetah, graine aléatoire 0, un million de pas)
cd sim && env/bin/python run.py ppo_sb3 HalfCheetah-v5 0 1000000

# Toutes les expériences (P entraînements en parallèle ; environ 250 heures-cœur au total)
P=4 ./drive.sh

# Les analyses, à partir des résultats déjà présents (quelques minutes)
env-an/bin/python analysis/e1.py && env-an/bin/python analysis/e1_curve.py && cd ..

# Les figures puis le document (il faut md2star, pandoc, LuaLaTeX et sprezzature-figures)
cd docs/figures && ../../sim/env-llm/bin/python build.py && cd .. && ./build.sh
```

Les résultats bruts sont déjà dans le dépôt : les analyses et les figures se refont sans
réentraîner. Le chemin complet, entraînements compris, demande quelques jours sur une machine
de bureau.

## Ce qui n'est pas dans ce dépôt

- Les PDF des articles lus, protégés par le droit d'auteur. `study/fetch.py` les retélécharge.
- Les diapositives de Pineau, pour la même raison. Elles se trouvent sur les sites d'ICLR 2018 et
  de NeurIPS 2018.

## Citer ce travail

Warith Harchaoui, « A-t-on écouté Joelle Pineau en 2018 ? », 2026.

## Licence

BSD à trois clauses (BSD-3-Clause), la licence de scikit-learn : voir [LICENSE](LICENSE).
