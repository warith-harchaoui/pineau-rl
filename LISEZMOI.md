# Apprentissage par renforcement : A-t-on écouté Joelle Pineau en 2018 ?

*English version: [README.md](README.md)*

En 2018, Joelle Pineau a montré, à ICLR puis à NeurIPS, seize failles qui rendaient peu crédibles
les résultats de l'apprentissage par renforcement profond (RL). Parmi elles : du code absent, des
réglages tus, des méthodes concurrentes mal réglées, trop peu d'essais, aucun test statistique,
une évaluation sur les conditions d'entraînement. Ses exposés réclamaient une recherche
reproductible, réutilisable et robuste. Ce dépôt mesure, faille par faille, ce qui a changé depuis.
Il s'applique les trois mêmes mots : chaque chiffre du document revient d'une seule commande, chaque
pièce resservira sur d'autres articles ou d'autres essais, des tests gardent les calculs.

**État au 24 novembre 2026.** Les expériences sont finies, consolidation comprise : vingt graines
aléatoires par algorithme et par tâche au lieu de dix, cinq graines aléatoires par configuration de
GRPO au lieu de trois. Les deux extensions sont inscrites dans les protocoles avant tout nouvel essai
(écart 12 de `sim/SIM_PROTOCOL.md`, calculé selon son écart 20 ; écart 14 de `sim/llm/LLM_PROTOCOL.md`,
clos par son écart 16). Comme le protocole l'a fixé d'avance, les résultats à dix graines restent les
résultats principaux. Le document donne à côté ceux de vingt graines et dit chaque divergence. Les
chiffres ci-dessous viennent du document.

**Ce qu'un lecteur peut vérifier, et ce qui repose sur notre parole.** Les protocoles disent, pour chaque
règle, si elle a été écrite avant ou après les résultats ; une relecture critique de ce dépôt a trouvé
plusieurs de ces affirmations fausses dans leurs détails, et les corrections sont datées (écart 14 de
`sim/SIM_PROTOCOL.md`, écart 15 de `sim/llm/LLM_PROTOCOL.md`). Le dépôt est devenu public le 15 novembre
2026, et son premier commit (9 novembre) contient déjà des résultats à côté des protocoles : pour tout ce
qui précède cette date, l'ordre d'écriture repose sur notre parole et sur les dates des commits, que leur
auteur aurait pu falsifier. Chaque tentative d'entraînement, y compris celles arrêtées puis relancées, est
listée dans `sim/logs/attempts_reconstructed.csv` (jusqu'au 15 novembre) et `sim/logs/attempts.jsonl`
(depuis). Ce que chacun peut vérifier sans nous croire : chaque nombre, recalculé à partir des résultats
commités, et chaque décision du sondage, face à la citation et à la page sur lesquelles elle repose.

## Ce que nous avons trouvé

- **Quatre pratiques ont changé.** Face à notre propre lecture de 2018, les articles de RL classique
  de 2026 donnent plus souvent un lien vers leur code (31 % puis 74 %), montrent la sensibilité à un
  réglage (44 % puis 80 %), chiffrent leur calcul (27 % puis 58 %) et rapportent une incertitude (63 % puis 88 %). Cette dernière hausse est fragile : sans les treize articles
  lus en partie par un autre modèle, elle ne passe plus la correction de Holm. Lues sur 20 articles par an entre les deux dates, ces quatre pratiques montent
  lentement, sans saut après la liste de contrôle que NeurIPS impose depuis 2019.
- **D'autres n'ont pas bougé de façon détectable** : le test statistique (6 % puis 12 %), les
  références décrites avec tous leurs réglages (35 % puis 29 %), l'évaluation sur des conditions
  tenues à part (33 % puis 45 %).
- **Les essais eux-mêmes.** Parmi trente essais d'un même programme, deux groupes de cinq tirés au
  hasard trompent un test statistique dans 1,2 % des cas ; triés par score, dans 31 %. Garder les
  meilleurs essais gonfle le score de 33 %. Le t de 9 qui a rendu célèbres les exposés de 2018 trouve
  son explication : le script publié par Peter Henderson mesure l'écart entre épisodes et ignore
  l'écart entre graines aléatoires. Appliqué à nos essais de TRPO, il dépasse 9 dans 38 % des tirages
  au hasard.
- **La robustesse.** Sur quatre algorithmes, le meilleur change avec la tâche. Mais PPO s'entraîne
  cinq fois plus longtemps que SAC et CrossQ : à budget égal et avec vingt graines aléatoires, CrossQ
  mène sur les quatre tâches. Une physique modifiée
  de 20 % bouleverse le classement sur Hopper : le premier y finit dernier (une description choisie
  après avoir vu les résultats, sans test : écart 11).
- **Les modèles de langue.** Dans notre GRPO écrit à la main, une part du gain mesuré vient des
  réponses coupées à 160 jetons, une leçon que la récompense au hasard n'enseigne jamais. Avec cinq
  graines aléatoires, l'intervalle du gain moyen de Qwen avec la vraie récompense contient zéro
  (+14 points, de −3 à +34) : le gain repose sur les deux essais faits sur GPU. Le matériel et la
  graine aléatoire y ont changé ensemble.

L'argument complet, avec chaque source : [`docs/conclusions.md`](docs/conclusions.md)
([PDF](docs/conclusions.pdf)) ; en anglais, [`docs/conclusions-en.md`](docs/conclusions-en.md)
([PDF](docs/conclusions-en.pdf)).

## Deux instruments

**Un sondage des articles** (`study/`). Nous relisons 50 articles de RL tirés au sort parmi les
1 252 d'ICLR 2026, d'ICML 2026 et de NeurIPS 2025, avec la grille de Pineau et une seconde grille
(Y1 à Y12), puis nous complétons les articles de RL classique jusqu'à 50 et lisons 50 articles de
2018 avec les mêmes grilles. Des agents de modèle de langue font la lecture. Chaque décision
s'appuie sur une citation exacte de l'article, avec sa page : chacun confronte n'importe quelle
décision au PDF. Vingt articles ont été lus deux fois, à l'aveugle. Le protocole a été écrit avant
toute lecture ; ses écarts sont datés.

**Des expériences** (`sim/`). Nous refaisons les expériences de 2018 avec les algorithmes de 2026 :
PPO en deux implémentations, SAC et CrossQ, sur quatre tâches MuJoCo, dix graines aléatoires par
couple (trente pour l'expérience E1), avec une évaluation sur des graines aléatoires jamais vues à
l'entraînement et sur une physique modifiée. Un volet sur les grands modèles de langue oppose un GRPO
écrit à la main, entraîné avec la vraie récompense, au même entraînement avec une récompense tirée à
pile ou face. Le protocole a été écrit avant le premier entraînement. Chaque essai reste dans les
résultats, nos propres erreurs comprises.

## L'organisation du dépôt

| Chemin | Contenu |
|---|---|
| `docs/` | Le document en deux langues, sa bibliographie, ses figures (`docs/figures/build.py`) et `check_numbers.py`, qui recalcule 188 chiffres clés des deux textes à partir des fichiers de résultats. |
| `study/PROTOCOL.md`, `study/GRILLE.md` | Le protocole du sondage et la fiche des lecteurs avec les deux grilles (traductions anglaises : suffixe `-en`). |
| `study/codes/`, `study/codes_v2/` | Un fichier JSON par article et par lecteur : une décision par critère, avec citation et page. |
| `study/*.py`, `study/*.json` | Les tirages, les analyses (intervalles de Wilson, différences de Newcombe, Fisher, Holm, Cochran-Armitage) et leurs résultats. |
| `sim/SIM_PROTOCOL.md`, `sim/llm/LLM_PROTOCOL.md` | Les protocoles des expériences et leurs écarts. |
| `sim/run.py`, `sim/jobs*.txt`, `sim/drive.sh`, `sim/queue.sh` | Un entraînement ; les listes d'essais et leurs lanceurs. |
| `sim/results/`, `sim/logs/` | La courbe d'évaluation de chaque essai (CSV) et les journaux d'entraînement. |
| `sim/models/` | Les politiques finales, pour réévaluer sans réentraîner (les poids de SAC et de CrossQ restent en local). |
| `sim/analysis/` | Un script et un fichier JSON par expérience (E1 à E7, B1, B3). |
| `sim/llm/` | GRPO en un seul fichier (`grpo.py`), ses diagnostics, ses résultats et `summary.py`. |
| `envs/` | Les environnements figés, la plateforme et la chaîne du document ([`envs/LISEZMOI.md`](envs/LISEZMOI.md)). |
| `src/pineau_rl/`, `pyproject.toml` | Les morceaux réutilisables en paquet Python : statistiques, format des essais, grille de lecture (voir plus bas). |
| `Makefile`, `tests/`, `.github/workflows/verify.yml` | Le recalcul en une commande, les tests unitaires, l'intégration continue. |
| `slides.md` | Les diapositives de Pineau à ICLR 2018, décrites une à une. |

## Refaire les résultats, à trois niveaux

Les résultats viennent d'un Mac à puce Apple M2 Max, sous Python 3.11.18 (détails dans
[`envs/LISEZMOI.md`](envs/LISEZMOI.md)).

**1. Recalculer chaque chiffre à partir des résultats du dépôt (moins d'une heure, sans entraînement).**

```bash
python3.11 -m venv sim/env-an
sim/env-an/bin/pip install -r envs/analysis.txt -r envs/test.txt
make verify
```

`make verify` relance les neuf analyses du sondage, les analyses des expériences (seize à dix
graines aléatoires, treize de plus pour l'écart 12) et le bilan de GRPO, vérifie les 188 chiffres
des deux textes et les 156 affirmations de l'article de blog (`make check`), passe les tests unitaires
(`make test`), puis demande à git si chaque fichier JSON est revenu octet pour octet. Sur le M2 Max,
saturé en même temps par des entraînements, la séquence entière a pris environ 45 minutes ; E1,
B1, B3 et E2, avec leurs dizaines de milliers de tirages, en prennent l'essentiel.
`make verify-head` fait de même dans un export neuf du dernier commit, ce qui laisse intacte une
copie de travail où tournent des essais. L'intégration continue la relance à chaque envoi.

Les figures et les PDF demandent la chaîne du document (pandoc, md2star, LuaLaTeX,
sprezzature-figures, listés dans `envs/`) :

```bash
python3.11 -m venv sim/env-llm && sim/env-llm/bin/pip install -r envs/llm.txt
make figures docs
```

**2. Réentraîner un essai.**

```bash
python3.11 -m venv sim/env && sim/env/bin/pip install -r envs/train.txt
cd sim && env/bin/python run.py ppo_sb3 HalfCheetah-v5 0 1000000
```

L'essai écrit `results/ppo_sb3/HalfCheetah-v5/seed0.csv`, à confronter au fichier du dépôt,
puis `models/ppo_sb3/HalfCheetah-v5/seed0.zip`. Durée médiane d'un essai sur un cœur, d'après les
journaux du dépôt : PPO (Stable-Baselines3) environ une demi-heure pour un million de pas, PPO (SBX,
JAX) environ une heure, SAC de vingt minutes (Swimmer) à deux heures (HalfCheetah) pour 200 000 pas,
CrossQ d'une heure trois quarts à trois heures et demie, TRPO environ cinq minutes. Un essai de GRPO
(`sim/llm/grpo.py`) prend environ 50 minutes sur le processeur graphique d'Apple pour Qwen2.5 0.5B,
de 70 à 100 minutes pour Llama 3.2 1B, de cinq à six heures sur deux fils de processeur pour Qwen.

**3. Tout réentraîner.**

```bash
cd sim && P=4 ./drive.sh                 # chaque ligne de jobs.txt, quatre à la fois
```

Les 250 entraînements de la première phase totalisent environ 260 heures-cœur, soit un peu moins de trois jours
sur quatre cœurs. Les douze essais de GRPO ajoutent environ 27 heures, les huit ajoutés pour cinq graines aléatoires environ 33 de plus ; la chaîne officielle de
RL Baselines3 Zoo pour E6 (`sim/zoo_official.sh`), dix essais de plus. La consolidation, finie le
21 novembre 2026 (`sim/jobs_seeds20.txt`, `sim/jobs_consolidation.txt`), ajoute 160 entraînements,
environ 200 heures-cœur estimées (dix d'entre eux, PPO-SB3 sur HalfCheetah, existaient déjà pour
E1), puis 320 réévaluations de politiques sauvegardées sous plusieurs modifications de
la physique (`sim/dose.py`). Sur un autre processeur, la même graine aléatoire donne d'autres
courbes : un réentraînement complet éprouve les statistiques.

## Réutiliser les pièces

Les statistiques, le format des essais et la grille de lecture forment un paquet Python, `pineau_rl`
(`src/`), qui ne dépend que de NumPy, SciPy, statsmodels et rliable. Chaque script d'analyse l'importe.

```bash
pip install -e .        # n'importe où ; dans l'environnement d'envs/analysis.lock : make install (rien n'est téléchargé)
```

| Module | Contenu |
|---|---|
| `pineau_rl.stats` | Wilson, différence de Newcombe, Fisher, Holm, Cochran-Armitage, kappa de Cohen, probabilité d'amélioration, statistique de Henderson |
| `pineau_rl.bootstrap` | IQM et probabilité d'amélioration avec les intervalles bootstrap stratifiés de rliable |
| `pineau_rl.runs` | Le format des essais (un CSV par algorithme, tâche et graine aléatoire), son lecteur contrôlé, les scores finaux, une grille |
| `pineau_rl.grid` | Les fichiers de lecture, l'harmonisation, la valeur finale d'un critère, le contrôle d'un fichier de lecture |

Comparer des parts entre deux échantillons, critère par critère, comme le sondage :

```python
from pineau_rl.stats import compare, holm, wilson_ci

wilson_ci(17, 48)                         # intervalle de Wilson à 95 % de 17/48
tests = {k: compare(a, b) for k, (a, b) in {"code": ((31, 48), (19, 50)), "seeds": ((12, 48), (9, 50))}.items()}
holm([t["p"] for t in tests.values()])    # chaque t : {"diff", "lo", "hi", "p"}, Newcombe et Fisher
```

Classer vos propres algorithmes à partir d'essais dans notre format, écrits par n'importe quelle bibliothèque :

```python
import numpy as np
from pineau_rl.bootstrap import iqm_interval
from pineau_rl.runs import load_grid

np.random.seed(2026)  # rliable tire dans le générateur global de NumPy : le fixer une fois, en tête
G, missing = load_grid("results", ["ppo", "sac"], ["Hopper-v5"], range(10), {"ppo": 1_000_000, "sac": 200_000})
iqm_interval(G["Hopper-v5"])              # {algo: (IQM, bas, haut)}, bootstrap stratifié
```

Lire un échantillon d'articles avec notre grille :

```python
from pineau_rl.grid import load_overrides, load_reads, tally, validate, value_v1

reads = load_reads("codes", ["A", "B"])  # codes/<lecteur>/<id de l'article>.json, triés
ov = load_overrides("overrides.json")    # {critère : {id : valeur}}, l'harmonisation
v = lambda r, k: value_v1(r, k, ov)
problems = {i: validate(r, q1=v(r, "Q1"), x2=v(r, "X2"), q4=v(r, "Q4")) for i, r in reads.items()}
tally(v(r, "Q5") for r in reads.values() if v(r, "Q1") != "no")  # (oui, oui ou non) : code en lien
```

Les scripts eux-mêmes se lancent toujours depuis leur dossier (`cd study && python extension_stats.py`) ;
`make` trouve le paquet sans l'installer.

- **La grille de lecture.** `study/GRILLE.md` traduit la liste de Pineau et nos douze critères
  supplémentaires en règles de décision, chaque réponse appuyée sur une citation et une page. Pour
  lire votre propre échantillon, reprenez le format JSON de `study/codes_v2/`, contrôlez vos fichiers
  avec `study/check_codes.py` (schéma, règles de portée, chaque citation confrontée au texte du
  PDF ; `pineau_rl.grid.validate` sans le PDF), puis calculez parts et intervalles avec
  `study/analyze_final.py` ou `study/extension_stats.py`.
- **Les scripts d'analyse sur vos propres essais.** Chaque script d'expérience lit
  `sim/results/<algo>/<tâche>/seed<k>.csv`, une évaluation par ligne, avec les colonnes
  `step,eval_mean,eval_std,perturbed_mean,wall`. Écrivez vos essais dans ce format, depuis n'importe
  quelle bibliothèque, ajoutez l'algorithme et son nombre de pas à `ALGOS` et `FINAL` en tête de
  `sim/analysis/runs.py` : E2 (classement avec intervalles), E4 (gonflement par sélection des
  meilleurs), E5 (combien de graines aléatoires retrouvent un classement) et E7 (perte sous physique
  modifiée) les lisent.
- **La statistique de Henderson.** `pineau_rl.stats.henderson_script` refait le calcul de
  `from_same_dist.py` (Henderson et al., 2018), qu'utilise `sim/analysis/b1_script.py` ; `tests/test_henderson.py` montre sur six graines aléatoires
  inventées pourquoi il atteint un t de 9 là où un test sur les graines aléatoires ne voit rien.
- **GRPO en un seul fichier.** `sim/llm/grpo.py` entraîne un modèle de langue par GRPO en
  156 lignes, avec la vraie récompense ou une récompense à pile ou face ; il note la part de réponses
  coupées à chaque évaluation.

## Ce qui n'est pas dans ce dépôt

- Les PDF des articles lus, protégés par le droit d'auteur. `study/fetch.py` les retélécharge :
  `cd study && python3 fetch.py final_2026.json pdf`.
- Les diapositives de Pineau, pour la même raison. Elles se trouvent sur les sites d'ICLR 2018 et
  de NeurIPS 2018.

## Citer ce travail

Warith Harchaoui, « Apprentissage par renforcement : A-t-on écouté Joelle Pineau en 2018 ? », 2026.
GitHub lit [`CITATION.cff`](CITATION.cff) et propose la référence aux formats APA et BibTeX.

```bibtex
@misc{harchaoui2026pineau,
  author = {Harchaoui, Warith},
  title  = {Apprentissage par renforcement : A-t-on écouté Joelle Pineau en 2018 ?},
  year   = {2026}
}
```

## Licence

Licence BSD à trois clauses (BSD 3-Clause), la licence de scikit-learn : voir [LICENSE](LICENSE).
