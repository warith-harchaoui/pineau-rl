*English version: [LLM_PROTOCOL-en.md](LLM_PROTOCOL-en.md).*

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
4. Incident du 8 novembre 2026 : le pilote du taux d'apprentissage (Qwen, lr 3e-6) a atteint 65 Go de mémoire d'après une autre session et poussé la machine en swap (29 Go, 11 Go de disque libre). Tué au pas 10-20, aucun résultat exploitable. Pas de relance sans plafond mémoire. À élucider avant toute relance : `train_right` = 0,91 au pas 10 alors que pass@1 de test vaut 0,11 (quatre problèmes seulement, ou erreur de mesure).
5. Diagnostic du 9 novembre 2026, sans entraînement (`diag/replay_batch.py`, `diag/replay_batch.json`) : le lot exact du pas 10 du pilote (graine 9 : 48×49, 14×36, 21×50, 45×17) donne 5/32 au modèle de base, en ligne avec le test. Mais 23 des 32 réponses échantillonnées atteignent la limite de 160 jetons sans finir, et aucune n'est juste ; parmi les 9 réponses complètes, 5 sont justes. Le 0,91 du pas 10 n'est donc pas une erreur de décompte : la vraie récompense apprend d'abord à finir avant la coupure. Conséquence pour la lecture : avec `true`, une partie du gain est un gain de longueur, pas d'arithmétique ; `random` n'a pas ce levier. On garde 160 jetons (protocole), et on mesure désormais la part de réponses coupées (`truncated`), à l'entraînement et au test. Décidé avant tout entraînement retenu.
6. Version réduite (décision de Warith, 9 novembre 2026, option (a) du plan) : 100 pas au lieu de 200, graines 0 à 2 au lieu de 0 à 4, un seul entraînement à la fois, taux d'apprentissage 3e-6 sans pilote complet (le pilote a été tué au pas 10), mise à jour découpée en lots de 8 réponses (même gradient, mémoire divisée), plafond mémoire MPS et arrêt automatique (disque < 10 Go, swap + 4 Go). Décidé avant tout entraînement retenu.
7. Pause du 9 novembre 2026, 9 h 35, à la demande de Warith (machine trop chargée) ; reprise à 12 h 34 avec un seul fil CPU (`OMP_NUM_THREADS=1`) et en priorité basse. L'essai `qwen05 random` graine 1, interrompu au pas 40 environ, repart de zéro ; à la reprise il plante juste après le pas 0 (`probability tensor contains either inf, nan or element < 0` à l'échantillonnage), alors que la première tentative avait passé le pas 40. Le calcul MPS n'est pas déterministe d'une tentative à l'autre. Règle fixée avant de voir tout résultat de cette graine : on le relance une fois, à l'identique, après les autres essais ; un second plantage est rapporté comme un résultat (instabilité sous récompense aléatoire), pas retiré.
8. Reprise du 9 novembre 2026, 12 h 34 à 13 h 09 : aucun des neuf essais restants n'aboutit. Les quatre essais Qwen (random graines 1 et 2, true graine 2, plus la relance prévue à l'écart 7) plantent au premier pas d'entraînement sur des probabilités `nan`. Un essai Llama plante sur une erreur macOS (`kIOGPUCommandBufferCallbackErrorImpactingInteractivity` : le système coupe le travail GPU qui gêne l'interactivité, Warith travaillant sur la machine). Les cinq autres manquent de mémoire MPS (26,5 Go alloués sur un plafond de 27,2 Go : Llama 1B en fp32 avec l'optimiseur ne tient pas dans le plafond de 0,35). Avant la pause, trois essais Qwen avaient abouti sans `nan`. Ce qui a changé depuis : `OMP_NUM_THREADS=1`, la priorité basse et un usage interactif du GPU en parallèle. Les trois essais finis restent valides. GRPO est suspendu jusqu'à un créneau sans usage interactif (la nuit). Avant toute relance retenue, deux corrections, décidées avant de voir un résultat de ces essais : (i) un essai Qwen de contrôle avec l'environnement d'avant la pause (sans `OMP_NUM_THREADS`), pour séparer les deux causes ; (ii) pour Llama, `MICRO` à 2 (même gradient, moins de mémoire). La règle de l'écart 7 est étendue : chaque essai planté est relancé une fois, et un second plantage est rapporté.
9. Relance de nuit (9 novembre 2026, avant tout résultat de ces essais) : `night.sh`, de 23 h à 7 h, aucun essai lancé après 6 h, la simulation JAX de la file principale mise en pause pendant chaque essai pour rester à 4 cœurs. L'essai de contrôle (`qwen05 random`, graine aléatoire 1, sans `OMP_NUM_THREADS`) passe en premier ; s'il produit encore des `nan`, la nuit s'arrête et la cause se cherche dans `grpo.py`. Llama avec `MICRO=2` (variable d'environnement, même gradient). Un essai planté est retenté la nuit suivante ; deux échecs du même essai sont rapportés comme un résultat.
10. Cause des `nan` trouvée (10 novembre 2026, diagnostic sans résultat retenu : `diag/nan_step.py`, `diag/nan_where.py`, `diag/nan_step.out`). Le premier pas de `qwen05 random` graine 1, rejoué sur MPS, donne des gradients non finis sur les 290 tenseurs du modèle, alors que la perte et les log-probabilités sont finies ; sur CPU, le même pas donne une norme de 14,4 avant écrêtage, sans aucune valeur non finie. Sur MPS, le résultat change d'une tentative à l'autre pour un calcul identique : `nan` une fois, une norme finie mais absurde (6,4 × 10⁷) la suivante. Ni le masque d'attention, ni l'attention `eager`, ni le plafond mémoire, ni l'accumulation des gradients, ni une synchronisation forcée n'y changent rien. Un produit matriciel de test a fini par lever l'erreur que le système renvoie quand il coupe le travail GPU qui gêne l'usage interactif de la machine (`kIOGPUCommandBufferCallbackErrorImpactingInteractivity`, déjà vue à l'écart 8). Lecture retenue : un calcul GPU interrompu par le système revient parfois sans erreur, avec des valeurs corrompues. Elle explique pourquoi les trois essais finis ont tourné tôt le matin, machine au repos, et pourquoi l'essai de contrôle de la nuit a échoué à 23 h 02, pendant une session de travail. Corrections, décidées avant toute relance : (i) `grpo.py` recalcule une mise à jour dont la norme du gradient avant écrêtage est non finie ou dépasse 1 000 (le seuil vient de la norme de 14,4 mesurée sur CPU), jusqu'à cinq fois de suite, puis s'arrête ; (ii) une génération qui lève une erreur GPU est refaite, jusqu'à cinq fois ; (iii) l'essai s'arrête si les log-probabilités de départ ou les poids deviennent non finis ; (iv) le journal compte les recalculs à chaque pas. Conséquence pour les règles des écarts 7 à 9 : les plantages passés venaient de la machine, pas de l'apprentissage. Ils ne comptent donc pas comme des échecs de l'essai, et la règle « deux échecs du même essai sont un résultat » repart de zéro avec ce code. Ce changement de règle est décidé après avoir vu ces plantages ; aucun résultat de ces essais n'existe. Limite pour les trois essais finis : un gradient corrompu mais fini et écrêté à 1 a pu passer sans trace ; leurs journaux ne permettent pas de le vérifier.
11. Les garde-fous de l'écart 10 ne suffisent pas en journée (10 novembre 2026, essai de contrôle `guardtest`, non retenu) : au premier pas, cinq recalculs de suite donnent un gradient corrompu, et l'essai s'arrête comme prévu. Le même pas sur CPU (2 fils) est propre (normes 14,4 puis 6,85, puis 4,71 et 4,2 au pas 2) et prend environ trois minutes, soit environ six heures par essai Qwen. Décision, prise avant tout essai retenu avec ce code : les trois essais Qwen restants (`random` graines 1 et 2, `true` graine 2) tournent sur CPU (`cpu.sh` : `DEVICE=cpu`, 2 fils, priorité basse, un à la fois, deuxième des deux workers à côté de la file principale) ; les six essais Llama, trop lents sur CPU (environ 2,5 fois Qwen), restent sur GPU, la nuit seulement (`night.sh`), avec les garde-fous. Les trois essais Qwen finis ont tourné sur MPS : la différence de matériel change l'arrondi des calculs, pas l'algorithme, et le document le dira. Un essai qui échoue est relancé une fois ; un second échec est rapporté comme un résultat.
12. Nuit du 10 au 11 novembre 2026. Les trois essais Qwen sur CPU ont abouti sans aucun recalcul (`random` graines 1 et 2, `true` graine 2) : les six essais Qwen sont finis. Les six essais Llama ont tous manqué de mémoire MPS entre le pas 10 et le pas 60 (environ 26,3 Go alloués pour un plafond de 27,2 Go) ; les garde-fous de l'écart 10 ont recalculé de 1 à 6 mises à jour par essai avant cela. C'est le premier échec de chaque essai Llama. Corrections, décidées avant toute relance : le cache MPS est vidé à chaque pas (`torch.mps.empty_cache()`), et le plafond de mémoire passe de 0,35 à 0,45 de la mémoire unifiée, la nuit seulement. Les six essais Llama sont relancés la nuit suivante ; un second échec du même essai sera rapporté comme un résultat.
13. Nuit du 11 au 12 novembre 2026. Les six essais Llama, relancés avec les corrections de l'écart 12, ont tous abouti au pas 100, sans manque de mémoire ; les garde-fous de l'écart 10 ont recalculé 0, 2 et 7 mises à jour (`true`, graines 0 à 2) et 5, 4 et 3 (`random`). Les douze essais sont donc finis, aucun n'est retiré. Statistique annoncée (section Statistiques) : gain par graine, moyenne et intervalle à 95 % par bootstrap. Ses détails sont fixés après avoir vu les résultats, sans choix entre plusieurs variantes : bootstrap par percentile sur les graines, 10 000 tirages, `random.Random(0)` (`summary.py`, `results/gains.json`). Avec trois graines, le bootstrap n'a que dix rééchantillons distincts : l'intervalle est donné et lu comme très grossier.
