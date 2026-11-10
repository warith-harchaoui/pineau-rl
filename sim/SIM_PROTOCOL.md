*English version: [SIM_PROTOCOL-en.md](SIM_PROTOCOL-en.md).*

# Refaire les expériences de 2018 avec les règles de Pineau, en 2026

Écrit le 2026-11-08 AVANT tout entraînement. Ce qui change ensuite est noté dans « Écarts ».

## Pourquoi

Henderson, Islam, Bachman, Pineau, Precup, Meger (AAAI 2018) ont montré sur MuJoCo : (1) deux
groupes de cinq graines du même code ressemblent à deux algorithmes ; (2) le classement des
algorithmes change d'une tâche à l'autre ; (3) deux implémentations du même algorithme diffèrent ;
(4) publier les meilleurs essais gonfle et resserre les résultats. Huit ans plus tard, on refait ces
expériences avec les algorithmes de 2026 et, cette fois, avec les règles qu'elle demandait : assez
de graines, intervalles de confiance, références réglées avec le même soin, évaluation tenue à
part, code et données publiés.

## Outils (versions figées)

Python 3.11 ; Gymnasium 1.1.1 (successeur d'OpenAI Gym, Farama) ; MuJoCo 4.0.0 (gratuit et ouvert
depuis 2022 ; il fallait une licence en 2018) ; tâches `-v5` ; Stable-Baselines3 2.6.0 (PyTorch) ;
sbx 0.28 (Stable-Baselines en JAX) ; rliable pour les statistiques (Agarwal et al., NeurIPS 2021).
Environnement : `~/pineau-rl/sim/env`, `pip freeze` dans `requirements.lock`.

## Algorithmes (choix éclairé, 2026)

- **PPO** (Schulman 2017) : la référence de 2018, toujours la plus utilisée en 2026, et l'ancêtre
  direct de GRPO, l'algorithme du RL sur grands modèles. Deux implémentations : Stable-Baselines3
  (PyTorch) et sbx (JAX), réglages par défaut identiques autant que possible.
- **SAC** (Haarnoja 2018) : le standard « off-policy » pour le contrôle continu depuis 2019.
- **CrossQ** (Bhatt et al., ICLR 2024) : l'une des méthodes récentes les plus citées pour
  l'efficacité en données (sans réseau cible, normalisation par lots).
- **TD3** (Fujimoto 2018) : seulement si le budget le permet (sinon noté en écart).

## Tâches

HalfCheetah-v5, Hopper-v5, Walker2d-v5, Swimmer-v5 (les tâches de Henderson et al. 2018).

## Budget et graines

- On-policy (PPO, deux implémentations) : 1 000 000 de pas. Off-policy (SAC, CrossQ) : 300 000 pas
  (régime « peu de données », celui où ces méthodes se comparent en 2024-2026).
- 10 graines par couple (algorithme, tâche) ; 30 graines pour PPO-SB3 sur HalfCheetah (E1).
- Graines 0 à 29, fixées avant de lancer ; AUCUN essai n'est retiré ni relancé ; un essai qui
  plante est relancé une fois avec la même graine et l'incident est noté.

## Évaluation (tenue à part)

Toutes les 50 000 pas et à la fin : 10 épisodes, politique déterministe, sur un environnement
d'évaluation dont les graines (10 000 + i) ne servent jamais à l'entraînement. À la fin, en plus :
10 épisodes sur des dynamiques modifiées (masses × 1,2, frottement × 0,8), pour la généralisation.
Mesure principale : retour moyen d'évaluation final.

## Expériences

- **E1 Même code, autre graine** : PPO-SB3 sur HalfCheetah, 30 graines. On tire 10 000 fois deux
  groupes disjoints de 5 graines au hasard ; part des tirages où un test de Welch donne p < 0,05
  (devrait être environ 5 % si tout va bien) ; puis la coupe « la pire » (5 meilleures contre 5 pires
  parmi 10), qui reproduit la figure de 2018. Même chose avec 10 graines par groupe.
- **E2 Le classement change de tâche en tâche** : PPO-SB3, PPO-sbx, SAC, CrossQ sur 4 tâches,
  10 graines. Classement par tâche par IQM (moyenne interquartile) avec IC bootstrap stratifié à
  95 % (rliable) ; probabilité d'amélioration entre paires ; profils de performance.
- **E3 Deux implémentations du même algorithme** : PPO-SB3 contre PPO-sbx, mêmes tâches, mêmes
  graines ; écart et IC.
- **E4 Les trois meilleurs sur dix** : sur les données de E2, ce que deviennent moyenne et dispersion
  quand on ne garde que les 3 meilleurs essais sur 10 ; combien de comparaisons de E2 s'inversent.
- **E5 Combien de graines ?** : à partir de E1 et E2, par rééchantillonnage, probabilité de
  retrouver le bon classement de deux algorithmes avec n = 3, 5, 10, 20 graines.
- **E6 La référence mal réglée** : PPO-SB3 sur Hopper avec les réglages par défaut contre les
  réglages publiés de RL Baselines3 Zoo, 10 graines chacun : l'écart qu'une « nouvelle méthode »
  peut s'attribuer en ne réglant que la sienne.
- **E7 Tenu à part** : écart entre l'évaluation sur les dynamiques d'entraînement et sur les
  dynamiques modifiées, par algorithme.

## Statistiques

IQM et IC bootstrap stratifié (rliable, 2 000 rééchantillonnages) ; Welch pour E1 (c'est le test
qu'on critique) ; aucune comparaison n'est déclarée gagnante sans IC qui ne se chevauchent pas ou
probabilité d'amélioration avec IC au-dessus de 0,5.

## Publication

Code, `requirements.lock`, journaux d'évaluation (CSV), scripts d'analyse et figures, publiés avec
l'article. Les vidéos (« En 2018 », « En 2026 ») montrent des politiques réellement entraînées ici.

## Écarts

1. Off-policy (SAC, CrossQ) : 200 000 pas au lieu de 300 000, pour tenir le calcul sur une machine partagée très chargée (19 ms par pas mesurés). TD3 non lancé. Décidé avant le premier entraînement.
2. E6 : erreur de notre côté, la normalisation du Zoo utilise le gamma de l'algorithme (0,999) et le premier passage a laissé 0,99. Premier passage conservé (`ppo_sb3_zoo`), recette corrigée relancée (`ppo_sb3_zoofix`). Le résultat surprenant (Zoo 994 contre défaut 2 776, plateau à 1 000 dès 50 000 pas) a déclenché ce diagnostic, ajouté APRÈS avoir vu ce résultat : Zoo corrigé sur Hopper-v5 et v4, défaut sur v4, 10 graines chacun.
3. E1, seconde statistique (9 novembre 2026, APRÈS avoir vu les résultats de `analysis/e1.py`) : `e1.py` teste les scores finaux, alors que Henderson et al. rapportent « le test t moyen sur toute la distribution d'entraînement » (légende de leur figure 5). `analysis/e1_curve.py` refait cette statistique sur nos 30 courbes (test de Welch à chacun des 20 points d'évaluation, puis moyenne des t ou moyenne des p), pour des coupes de 10 essais en deux groupes de 5, au hasard ou triées par score final. Ajoutée parce que la comparaison avec leur figure l'exige ; elle ne remplace pas l'analyse préenregistrée, elle la complète.
4. Expérience B1, la statistique de Henderson avec leur algorithme (écrit le 9 novembre 2026, AVANT tout entraînement TRPO). Question : nos 30 essais de PPO n'approchent pas le t = −9,09 de Henderson et al. (figure 5, TRPO sur HalfCheetah, deux groupes de 5 non triés d'après Pineau). TRPO dispersait-il davantage, ou leur calcul différait-il ? Plan : 30 entraînements de TRPO (sb3-contrib 2.9.2, hyperparamètres par défaut, sans aucun réglage) sur HalfCheetah-v5, graines aléatoires 0 à 29, un million de pas, évaluation tous les 50 000 pas comme E1. Analyse fixée d'avance (`analysis/b1_trpo.py`) : les mêmes statistiques que `e1_curve.py` (moyenne des t, moyenne des p, au hasard et trié) et une troisième lecture, où les points de toutes les courbes d'un groupe sont empilés comme des observations indépendantes (5 essais × 20 points = 100 par groupe). Lecture des résultats : si le 95e centile de |t moyen| au hasard approche 9 avec TRPO, la dispersion de l'algorithme explique leur chiffre ; si seule la lecture empilée l'approche, leur calcul l'explique ; sinon, ni l'un ni l'autre, et nous le disons. DDPG reste hors de ce plan (trop coûteux à 4 cœurs). Ordre : en parallèle de la file principale, 2 entraînements TRPO à la fois (1 cœur chacun) et la file principale ramenée à 1 entraînement JAX (2 cœurs), pour rester à 4 cœurs.
5. E6, le pipeline officiel du Zoo (écrit le 9 novembre 2026, APRÈS l'analyse `analysis/e6_diag.py` et AVANT tout entraînement officiel). Constat : corriger notre erreur de gamma ne change rien (Zoo corrigé v5 : IQM 1 012 [902, 1 138] contre 1 003 avec l'erreur ; probabilité d'amélioration 0,47). La recette publiée, telle que nous l'appliquons, plafonne autour de 1 000 sur v4 comme sur v5, contre 2 423 et 2 877 avec les valeurs par défaut. Les hyperparamètres de `rl_zoo3/hyperparams/ppo.yml` (version 2.9.2) pour Hopper-v4 sont identiques aux nôtres. Question : le plafond vient-il de la recette publiée elle-même, ou de notre façon de l'appliquer ? Plan : 10 entraînements avec le script officiel (`python -m rl_zoo3.train --algo ppo --env Hopper-v4 --seed i`, i = 0 à 9, rl_zoo3 2.9.2, environnement séparé `env-zoo` aux mêmes versions que `requirements.lock`, un fil), puis évaluation des politiques finales avec NOTRE protocole (`analysis/e6_official.py` : 10 épisodes déterministes, graines aléatoires d'évaluation 10 000 à 10 009, normalisation des observations figée, sans normalisation de la récompense). Comparaison fixée d'avance : officiel contre notre Zoo corrigé v4 et contre défaut v4 (IQM avec intervalle bootstrap, probabilité d'amélioration, Holm sur les deux). Lecture : si l'officiel dépasse nettement 1 000, notre application de la recette était fautive, et nous cherchons où ; s'il plafonne aussi, la recette publiée fait moins bien que les valeurs par défaut dans cette version des bibliothèques, et le document le dit sans parler de « référence mal réglée par nous ».
6. B1, le script de Henderson (écrit le 9 novembre 2026 à 23 h 55, APRÈS les résultats de `analysis/b1_trpo.py` et AVANT tout calcul avec ce script). Deux faits trouvés ce soir. (a) Le couple publié, t = −9,09 et p = 0,0016, impose environ 3,4 degrés de liberté (test bilatéral) : il exclut la lecture « points empilés » (environ 198 degrés de liberté, p de l'ordre de 10⁻¹⁶) et la lecture « t moyen converti en p » (un test de Welch sur 5 contre 5 a au moins 4 degrés de liberté) ; seule la moyenne des p reste compatible. (b) Henderson a publié le 17 juin 2017 le script `from_same_dist.py` (dépôt `Breakend/ReproducibilityInContinuousPolicyGradientMethods`, compagnon d'Islam, Henderson et al. 2017). Ce script moyenne, colonne par colonne, les fichiers de progression des graines d'un groupe (`ave_results.py`), puis applique à chaque itération un test de Welch construit à partir de la moyenne des retours, de leur écart-type ENTRE ÉPISODES d'une même itération et du nombre d'épisodes (`ttest_ind_from_stats`), et rapporte la moyenne des t et la moyenne des p. La variabilité entre graines n'y entre pas. Rien ne prouve que ce script a produit leur figure 5 ; son nom (« de la même distribution ») et sa sortie (« t=…, p=… ») le rendent probable. Analyse fixée avant de la lancer (`analysis/b1_script.py`) : sur nos 30 courbes TRPO et nos 30 courbes PPO, les mêmes tirages que `b1_trpo.py` (graine 2018, 10 000 tirages de 10 essais coupés en 5 contre 5, au hasard puis triés), le calcul du script appliqué à nos évaluations (moyenne des `eval_mean` et des `eval_std` des 5 graines, n = 10 épisodes d'évaluation), avec n = 5 (leur nombre de trajectoires par itération : 5 000 pas, épisodes de 1 000 pas) en sensibilité. Différences avec leur cas, dites d'avance : nos épisodes d'évaluation suivent une politique déterministe et non la politique stochastique d'entraînement, et nous avons 20 points d'évaluation au lieu de leurs itérations. Lecture : si ce calcul donne au hasard des |t moyen| de l'ordre de 9 et une majorité de faux positifs, leur chiffre s'explique par un test qui ignore la variabilité entre graines ; sinon, il reste inexpliqué.
7. Détails d'analyse de E2, E4 et E5 (écrits le 10 novembre 2026, APRÈS les résultats de PPO et SAC et AVANT tout résultat de CrossQ, dont 3 essais sur 40 sont finis ; scripts `analysis/e2.py`, `analysis/e4.py`, `analysis/e5.py`). Score de chaque essai : `eval_mean` au dernier pas (1 million pour PPO, 200 000 pour SAC et CrossQ, écart 1 : la comparaison se fait donc à budgets différents, et le document le dit). Graines 0 à 9 pour tous, y compris PPO-SB3 sur HalfCheetah. **E2** : par tâche, IQM et intervalle bootstrap stratifié (rliable, 2 000 rééchantillonnages), rang par IQM ; pour chaque paire d'algorithmes et chaque tâche, probabilité d'amélioration avec intervalle ; une paire est « tranchée » si cet intervalle exclut 0,5. Le classement change de tâche en tâche si l'algorithme en tête par IQM n'est pas le même partout ; nous disons aussi si ce changement est tranché (le meneur d'une tâche battu de façon tranchée par un autre sur une autre tâche). Profils de performance : part des essais au-dessus de chaque seuil, scores divisés par le meilleur IQM de la tâche. **E4** : pour chaque algorithme et tâche, moyenne et écart type des 10 essais, puis des 3 meilleurs ; une comparaison (paire d'algorithmes sur une tâche, 24 en tout) « s'inverse » si le signe de l'écart des moyennes change quand chaque algorithme ne garde que ses 3 meilleurs. **E5** : pour chaque comparaison de E2, le « bon » classement est celui des moyennes des 10 essais ; pour n = 3, 5, 10 et 20, 10 000 tirages avec remise de n essais par algorithme parmi ses 10 (la distribution observée tient lieu de l'algorithme), part des tirages qui retrouvent le bon classement ; pour PPO-SB3 sur HalfCheetah, les 30 essais de E1 servent de distribution. Résultat rapporté : la part médiane sur les 24 comparaisons, et sur celles dont l'écart relatif des moyennes est inférieur à 20 %.
