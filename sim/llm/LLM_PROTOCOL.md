# GRPO avec les moyens du bord : vraie récompense contre récompense tirée au sort

Écrit le 2026-11-08 AVANT le premier entraînement. Ce qui change ensuite est noté dans « Écarts ».
**Portée annoncée d'avance : une illustration à petite échelle**, sur un portable Apple (GPU MPS),
pas une réplication de Shao et al. 2025 (Qwen2.5-Math-7B, MATH-500, grappes de GPU).

## Question

Sur de petits modèles et une tâche d'arithmétique vérifiable, une récompense tirée au sort
améliore-t-elle la justesse autant que la vraie récompense ? L'effet dépend-il de la famille de
modèles ? Et que voit-on selon qu'on mesure pass@1 ou pass@8 (Yue et al. 2025) ?

## Modèles (deux familles, au moins)

- Llama-3.2-1B-Instruct (Meta, copie `unsloth`) ;
- un petit Qwen Instruct (le plus petit disponible, version exacte notée ici après téléchargement).

## Tâche

Problèmes d'arithmétique générés, réponse entière ; on compare le **dernier entier** de la réponse
à la bonne valeur (pas d'exigence de format, pour ne pas récompenser le format). Population
énumérée puis mélangée avec une graine fixe ; 300 problèmes de **test**, jamais vus à
l'entraînement. Un **pilote** sur des problèmes hors test, sans récompense, fixe la difficulté :
on prend la famille de problèmes où les deux modèles sont entre 15 % et 70 % de justesse. Le pilote
fixe aussi le taux d'apprentissage, parmi 3 valeurs, avec la vraie récompense seulement et une
graine (9) qui n'entre pas dans les résultats ; même valeur ensuite pour toutes les conditions.

## Algorithme

GRPO écrit à la main (PyTorch), pour tout contrôler : par pas, 4 problèmes × 8 réponses
échantillonnées (température 1, 64 jetons au plus) ; avantage = (r − moyenne du groupe) / (écart
type du groupe + 10⁻⁴) ; 2 passes de mise à jour avec coupure (clip) à 0,2 du rapport de
probabilités par jeton, comme PPO et GRPO ; Adam ; norme du gradient coupée à 1 ; pas de terme KL.

## Conditions

- `true` : r = 1 si la réponse est juste, 0 sinon.
- `random` : r ~ Bernoulli(0,5), tirée pour chaque réponse, sans regarder la réponse.
- Point de départ (0 pas) : le modèle de base, mesuré avec chaque graine.

5 graines (0 à 4) par couple (modèle, condition), fixées d'avance, aucune retirée. 200 pas (réduits
si le calcul l'exige ; noté en écart, décidé avant de voir les résultats de la condition concernée).

## Mesures (sur les 300 problèmes de test)

- Justesse gloutonne (une réponse sans hasard).
- Sur 100 problèmes de test, 8 réponses échantillonnées : pass@1 (justesse moyenne d'une réponse
  échantillonnée) et pass@8 (au moins une juste sur 8).
- Au pas 0, tous les 50 pas, à la fin.

## Statistiques

Gain = mesure finale − mesure au pas 0, par graine. Moyenne et IC bootstrap à 95 % (5 graines,
intervalles larges : dit tel quel). Aucune conclusion sans intervalle.

## Publication

Code, journaux et analyse restent dans `~/pineau-rl/sim/llm/` tant que Warith n'a pas décidé.

## Écarts

1. Pilote : 64 jetons coupaient les réponses (Qwen écrit 100 à 160 jetons), d'où 0,7 % de justesse apparente. Passage à 160 jetons, décidé après avoir lu de vraies sorties, avant tout entraînement.
2. Coût de calcul : mesures réduites à 150 problèmes de test en glouton et 50 en échantillonnage (au lieu de 300 et 100). Décidé avant tout entraînement.
3. Tâche retenue : `mul2` (produit de deux nombres de 12 à 99). Aucune tâche ne place les deux modèles entre 15 % et 70 % en glouton : `add3` est trop facile pour Llama (91 %) ; `mul2` donne en glouton 7 % (Qwen) et 73 % (Llama), en pass@1 échantillonné 11 % et 23 %. La mesure principale devient pass@1 échantillonné, celle que GRPO entraîne. Décidé après le pilote sans entraînement, avant tout entraînement.
4. Incident du 8 novembre : le pilote du taux d'apprentissage (Qwen, lr 3e-6) a atteint 65 Go de mémoire d'après une autre session et poussé la machine en swap (29 Go, 11 Go de disque libre). Tué au pas 10-20, aucun résultat exploitable. Pas de relance sans plafond mémoire. À élucider avant toute relance : `train_right` = 0,91 au pas 10 alors que pass@1 de test vaut 0,11 (quatre problèmes seulement, ou erreur de mesure).
