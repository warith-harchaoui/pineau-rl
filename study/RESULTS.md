# Résultats : la grille de Pineau (2018) réappliquée à 50 articles de RL de 2025-2026

Échantillon : 50 articles tirés au hasard parmi les 1 252 articles de RL d'ICLR 2026, ICML 2026
et NeurIPS 2025 (27 RL sur grands modèles, 14 RL classique, 9 théorie dont 5 sans expérience).
Calibration : 12 articles de RL d'ICML et NeurIPS 2018, même grille, mêmes lecteurs.
Accord entre deux lecteurs indépendants sur 10 articles : 127 décisions sur 130 (98 %).
Pourcentages sur les articles expérimentaux ; intervalle de Wilson à 95 %. Données :
`results_final.json`, `codes/`, `overrides.json`.

| critère | Pineau 2018 | nous, 2018 | nous, 2026 [IC 95 %] | verdict |
|---|---|---|---|---|
| L'article a des expériences | 100 % | 11/12 | 90 % [79, 96] | ambigu (théorie plus présente) |
| Réseaux de neurones | 90 % | 9/11 | 89 % [77, 95] | pas bougé |
| Hyperparamètres de la méthode, tous | 90 % | 6/10 | 67 % [52, 79] | ambigu (notre grille plus sévère) |
| Hyperparamètres des références, tous | 60 % | 6/11 | 18 % [10, 32] | **régressé** |
| Code en lien | 55 % | 6/11 | 67 % [52, 79] | pas bougé (tendance à la hausse) |
| Méthode de choix des hyperparamètres | 20 % | 2/10 | 27 % [16, 41] | pas bougé |
| Évaluation tenue à part | 10 % | 4/10 | 70 % [56, 82] | **amélioré** (surtout RL sur LLM : 26/27 ; classique 5/13) |
| Test de significativité | 5 % | 1/11 | 4 % [1, 15] | pas bougé |
| Incertitude rapportée | n.d. | 8/11 | 47 % [33, 61] | baisse portée par le RL sur LLM (4/27 ; classique 14/14) |
| Références réglées comme la méthode | n.d. | 4/10 | 5 % [1, 15] | baisse (petite calibration) |
| Calcul rapporté | n.d. | 4/11 | 47 % [33, 61] | pas bougé |
| Sélection des meilleurs essais visible | n.d. | 0/11 | 2/45 | rare, mais encore là |

Graines : sur 41 articles RL expérimentaux, 20 ne disent pas combien d'entraînements
indépendants soutiennent leurs résultats ; 4 n'en ont qu'un ; médiane des autres : 5.
RL sur LLM : 16 articles sur 27 n'essaient qu'une famille de modèles de base (corrigé le 9 novembre 2026 : 15 avant recomptage par `docs/check_numbers.py`).
