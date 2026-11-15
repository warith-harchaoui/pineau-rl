*Copié tel quel de `.private/v1_quotes_audit.md`, où il était gardé, et rendu public le 15 novembre 2026 ; le texte qui suit n'est pas modifié. English: [v1_quotes_audit-en.md](v1_quotes_audit-en.md).*

# Audit des 89 citations introuvables (grille v1)

Détail entrée par entrée : `v1_quotes_audit.json` (même dossier).

## Bilan

| Classe | Nombre |
|---|---:|
| FOUND (citation présente dans l'article) | 83 |
| PARAPHRASE_OK (reformulation fidèle) | 1 |
| UNSUPPORTED (valeur contraire aux règles) | 5 |
| UNVERIFIABLE | 0 |

**Aucune citation n'est inventée.** Les 89 échecs du contrôle automatique ont trois causes :

- le lecteur a ajouté un commentaire en français, entre parenthèses ou après un tiret, à une citation anglaise exacte (la majorité des cas) ;
- la mise en page à deux colonnes : pdftotext entrelace les colonnes, les légendes et les tableaux ; il y a aussi les appels de note collés aux mots (« WGANTPP3 ») et les symboles mal extraits (ε, ϵ, γ) ;
- les annexes NeurIPS 2018 de C24, C25 et C26 manquent dans `study/pdf/`. Le réseau était coupé pendant l'audit, mais les PDF de ces annexes, tirés des zip du site des actes (archives datées du 18 février 2019), étaient encore dans le scratchpad du lecteur F de calibration. Toutes les citations de C24, C25 et C26 s'y trouvent.

Une seule entrée est une paraphrase. C'est LR03 Q4 : la description du tableau 11 (p. 24) par le lecteur, qui est exacte.

Des pages citées sont fausses ou incomplètes : C11, C15 et C16, où la page est en fait celle de l'annexe -supp ; LR12 Q4, citée p. 20 au lieu de p. 36. Les bonnes pages sont dans le JSON.

## Les 5 valeurs contraires aux règles

| Article | Critère | Valeur codée | Valeur selon les règles | Motif |
|---|---|---|---|---|
| C13 | X4 | yes | **no** | Écart 1 : les références (initialisations V MAX, Q*avg) partagent l'apprenant et ses hyperparamètres fixés (ε = 0,1, α = 0,1, p. 7). Aucun réglage n'est décrit. |
| C16 | X4 | yes | **no** | Écart 1 : « All neural networks are trained using RMSprop with learning rate 5 × 10−4 » (supp. p. 3). La configuration est commune et aucun réglage n'est décrit. |
| C14 | X4 | na | **no** | Une référence est comparée (Gurobi 7.5, p. 7 ; Q4 est codé yes), donc `na` ne s'applique pas. Aucun réglage n'est décrit, d'où `no`. |
| C14 | Q7 | na | **no** | Écart 4 : un article `theory` à expériences jouets prend `no`, pas `na`. |
| ML16 (lecteur G) | Q7 | yes | **no** | Chaque agent est entraîné hors ligne puis évalué sur la même tâche OGBench. Les tâches 2 à 5 n'ont pas servi au réglage, mais elles ont servi à l'entraînement. Le premier lecteur (C) code déjà `no`. |

## Effet sur les verdicts

- **X4, notre lecture de 2018** (tableau de `docs/conclusions.md`, « 4 sur 10 ») : la part passe à **2 sur 11 (18 %)**. Le chiffre de 2026 (5 %, IC [1, 15]) reste sous ce point, et le verdict « ambigu » ne change pas, puisque Pineau n'a pas ce critère. L'écart entre notre 2018 et 2026 se réduit beaucoup.
- **À vérifier, hors des 89** : C11 X4 est codé `yes` sur « The same hyperparameters were used in all experiments. » Cette citation a été trouvée, donc elle n'est pas dans la liste. C'est pourtant le cas de l'écart 1. Si C11 passe aussi à `no`, on tombe à **1 sur 11 (9 %)**, dans l'intervalle de 2026 : il n'y aurait plus de recul visible contre notre propre lecture de 2018.
- **Q7, notre lecture de 2018** : la part passe de 4 sur 10 à **4 sur 11 (36 %)**. Le verdict « amélioré » (70 %, IC [56, 82]) ne change pas. L'écart 7 du protocole (« 40 % contre 10 % ») devient 36 %.
- **ML16 Q7** : ML16 fait partie de la double lecture, et G est le second lecteur. Les chiffres principaux ne bougent pas, car c'est la lecture C (`no`) qui compte. L'accord inter-lecteurs sur Q7 gagne un accord.
- Aucun changement pour Q3, Q4, Q5, Q6, Q8, X1, X2, X3, X6 ni X7.

## Cas limites gardés (FOUND, valeur défendable)

- C12 Q7 no : le téléporteur et l'inversion des récompenses modifient l'environnement, mais l'agent continue d'y apprendre. C'est de l'adaptation, pas une évaluation tenue à part.
- C14 Q3 et Q6 na : les règles écrites ne prévoient pas ce `na`. Il reste défendable, car la méthode exacte n'a aucun hyperparamètre.
- ML17 Q6 no : une règle de choix est donnée pour T seulement. C'est le même traitement que C22 Q6.
