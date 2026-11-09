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
