*Copié tel quel de `.private/planification.md`, où il était gardé, et rendu public le 15 novembre 2026 ; le texte qui suit n'est pas modifié. English: [planification_v2-en.md](planification_v2-en.md).*

# Planification : coder la grille v2 (Y1 à Y12) sur les 62 articles

Écrit le 9 novembre 2026. Décision de Warith : oui, on code la grille v2. Rien n'est codé à
l'heure où ce plan est écrit. La grille est préenregistrée dans `study/PROTOCOL.md`, écart 11.

## But

Mesurer, dans les mêmes 50 articles de 2026 et les mêmes 12 articles de calibration de 2018,
les failles de Pineau que la grille v1 ne couvre pas. Dans `docs/conclusions.md`, cela fait
sortir de « à mesurer » ou de « en cours » :

| Faille | Critères v2 | Verdict actuel |
|---|---|---|
| F3 infrastructure | Y10 | à moitié (X7 seul) |
| F6 réglages qui changent tout | Y9 | à mesurer |
| F8 mesure non définie | Y1, Y2, Y11 | à mesurer |
| F12 pas de test | Y11, Y12 (avec Q8, X2) | pas écoutée |
| F13 meilleur algorithme selon la tâche | Y3, Y4 (avec E2) | en cours |
| F14 implémentations divergentes | Y5 (avec E3) | en cours |
| F15 test sur l'entraînement | Y8 (avec Q7, E7) | écoutée |
| F16 bancs d'essai trop simples | Y7 (avec X6) | à mesurer |
| liste de contrôle v1.2 | Y6 | non mesurée |

## Ce qui ne change pas

- Échantillon : `study/final_2026.json` (50) et `study/calib_2018.json` (12). Aucun article
  ajouté, aucun retiré.
- Répartition : celle de la v1 (`study/assignments.json`). Six lecteurs de 10 ou 12 articles
  (A2 à F2, F2 pour la calibration 2018), et un septième (G2) pour la double lecture des 10
  mêmes articles que G en v1.
- Format : `yes` / `no` / `na`, citation exacte et page obligatoires, ou « absent après
  lecture des sections expériences, annexes et liens ».
- Annexes : comme en v1 (écart 8). En 2018, on lit les `-supp.pdf` d'ICML. En 2026, les
  annexes sont dans le PDF principal.
- Les codes v1 (`study/codes/`) ne sont pas touchés. La v2 va dans `study/codes_v2/<lecteur>/<id>.json`.

## Étape 0 : écrire les règles de décision, avant tout codage

L'écart 11 définit les critères mais pas leurs cas limites. On ajoute à `PROTOCOL.md` un
écart 11 bis, daté et écrit avant le pilote. Voici le brouillon à y copier.

- **Portée.** Si Q1 vaut `no` en v1 (pas d'expérience), Y1 à Y12 valent `na` (même règle que
  l'écart 3). Pour un article `theory` à expériences jouets, on code normalement.
- **Y1, mesure définie.** `yes` si l'article dit ce que contient le nombre rapporté : retour
  final, moyenne sur les N derniers épisodes, aire sous la courbe, pass@k avec k et le nombre
  d'échantillons, taux de réussite et sur quoi. « Return » ou « accuracy » sans plus : `no`.
- **Y2, barres d'erreur définies.** `yes` si l'article dit ce que représentent la bande ou
  l'intervalle (écart type, erreur type, IC à 95 %, min et max). `na` s'il n'y a aucune barre
  ni bande (X2 v1 `no`). Des barres présentes mais non définies : `no`.
- **Y3, nombre de tâches.** Un entier : le nombre de tâches, d'environnements ou de bancs
  d'essai distincts sur lesquels porte la conclusion principale. Deux niveaux de difficulté
  d'un même jeu comptent pour un seul. Valeur dérivée pour l'analyse : `yes` si l'entier est
  au moins 2.
- **Y4, pertes montrées.** `yes` si un résultat tâche par tâche est donné et qu'au moins une
  tâche où la méthode ne gagne pas est montrée ou dite. `no` si l'article ne donne que des
  moyennes, ou ne montre que des tâches où la méthode gagne. `na` si Y3 vaut 1.
- **Y5, implémentation des références.** `yes` si, pour chaque référence principale,
  l'article dit d'où vient le code : dépôt, bibliothèque avec sa version, ou « réimplémenté
  par nous ». `na` s'il n'y a pas de référence comparée (même règle que Q4).
- **Y6, exclusions.** `yes` si l'article dit quels essais, graines ou données ont été retirés,
  ou dit explicitement qu'aucun ne l'a été. Le silence vaut `no`.
- **Y7, version.** `yes` si la version de chaque environnement ou banc d'essai principal est
  donnée : suffixe Gym ou Gymnasium, version de la suite, ou nom exact et date de la séparation
  de test pour les bancs `llm`. « MuJoCo » seul : `no`. « MATH-500 » compte `yes`, car c'est
  une séparation fixe et nommée. « MATH » seul : `no`.
- **Y8, généralisation.** `yes` si au moins une évaluation porte sur des conditions absentes
  de l'entraînement et du réglage : autres graines d'environnement annoncées comme telles,
  tâches nouvelles, dynamiques modifiées, distribution de test distincte. C'est plus strict
  que Q7 : un banc d'essai `llm` différent des données d'entraînement RL ne compte que si
  l'article le présente comme un test hors distribution.
- **Y9, sensibilité.** `yes` si au moins un hyperparamètre de la méthode est balayé et que le
  résultat est montré (figure, tableau ou phrase chiffrée). Une ablation de composant ne
  compte pas : ce n'est pas un hyperparamètre.
- **Y10, dépendances.** `yes` si les versions des bibliothèques principales sont données dans
  l'article, ou si un fichier d'environnement est cité dans le dépôt lié. Le dépôt n'est pas
  visité, sauf si l'article renvoie explicitement au fichier.
- **Y11, type d'incertitude.** Valeur `yes` / `no` plus un champ `kind` (`std`, `se`, `ci`,
  `iqr`, `minmax`, `other`). `na` si X2 v1 vaut `no`. Y11 est plus large que Y2 : il suffit
  que le type soit nommé quelque part.
- **Y12, outils post-2018.** `yes` si l'article emploie au moins un de ces outils : IQM, IC
  bootstrap stratifié, rliable, profils de performance, probabilité d'amélioration. Un simple
  bootstrap sur une moyenne compte `yes` s'il produit un intervalle rapporté.

Livrables : l'écart 11 bis dans `PROTOCOL.md`, et `study/GRILLE_V2.md`, la fiche que chaque
lecteur reçoit (règles ci-dessus, format JSON, exemple rempli). Commit
« grille v2 : règles de décision (avant codage) ».

## Étape 1 : outils, avant tout codage

1. `study/check_v2.py`, contrôle mécanique de chaque fichier :
   - le schéma : les 12 critères présents, valeurs autorisées, `kind` pour Y11, entier ou
     `null` pour Y3 ;
   - la cohérence avec la v1 : `na` partout si Q1 v1 vaut `no`, Y2 et Y11 `na` si et
     seulement si X2 v1 vaut `no`, Y5 `na` si et seulement si Q4 v1 vaut `na` ;
   - les citations : chaque citation non « absent » doit se retrouver dans `pdftotext` du PDF
     (ou de son annexe). La correspondance est floue (espaces, césures, ligatures) avec un
     seuil de 90 %. Une citation introuvable renvoie le fichier à son lecteur.
2. `study/analyze_v2.py` : même `wilson()` et même `load()` que la v1, ventilés `llm` /
   `classic` / `theory` (X5 v1). Sortie dans `study/results_v2.json`.
3. `study/agree_v2.py` : accord critère par critère entre les lecteurs principaux et G2 sur
   les 10 articles, avec le kappa de Cohen quand les deux valeurs varient.
4. Tester les trois scripts sur deux fichiers fabriqués à la main, puis les supprimer.

## Étape 2 : pilote, deux articles

- Articles du pilote, choisis par une règle fixée d'avance : `random.Random(11)` mélange les
  40 articles de 2026 hors double lecture, et on retient le premier article expérimental
  `llm` et le premier `classic`. Résultat : **LR08** (`llm`) et **ML15** (`classic`).
- Un sous-agent les code avec la fiche, puis `check_v2.py` passe.
- Je relis les citations, critère par critère. Une règle ambiguë est précisée dans un
  écart 12, daté, avant le codage principal. Une règle ne bouge que pour lever une ambiguïté,
  jamais pour changer un chiffre.
- Les deux articles du pilote sont ensuite recodés par leur lecteur normal (A2 et C2) avec la
  fiche finale. Le codage du pilote ne sert pas à l'analyse.

## Étape 3 : codage principal, sept sous-agents en parallèle

- A2 à E2 (10 articles de 2026 chacun), F2 (12 articles de 2018) et G2 (les 10 articles de
  double lecture), lancés ensemble en arrière-plan.
- Chaque lecteur reçoit la fiche `GRILLE_V2.md`, la liste de ses identifiants, les chemins des
  PDF dans `study/pdf/`, et le dossier où écrire. Les lecteurs **ne lisent ni les codes v1 ni
  ceux des autres lecteurs v2** : la cohérence avec la v1 est vérifiée après, par
  `check_v2.py`. G2 ne sait pas qui a codé ses articles en premier.
- Chaque lecteur lit l'article entier, annexes comprises. Il renvoie seulement la liste des
  fichiers écrits et les cas où il a hésité, pas le contenu des fichiers.
- Coût : du même ordre que le codage v1 (sept lecteurs, 72 lectures d'articles complets),
  donc nettement plus que tout le reste du travail sur `docs/`. Les sous-agents ne font que
  lire et n'utilisent pas le Mac : ils ne gênent pas les simulations ni GRPO réduit, qui
  tournent en même temps.

## Étape 4 : contrôle et reprises

- `check_v2.py` passe sur les 72 fichiers.
- Chaque fichier en échec (citation introuvable, incohérence avec la v1) est renvoyé à son
  lecteur, via SendMessage, avec la liste des défauts. Un deuxième échec sur le même critère
  est tranché par moi depuis le PDF et noté dans `study/overrides_v2.json`, avec la raison.
- Commit « grille v2 : codes bruts ».

## Étape 5 : harmonisation, avant tout pourcentage

- Lire les citations critère par critère, à travers les lecteurs, sans calculer de part de
  `yes`. On cherche les lecteurs qui appliquent la même règle différemment, comme X4 et X7 en
  v1 (écarts 1 et 2).
- Chaque harmonisation est un écart (13, 14, …) écrit avant l'agrégation, puis appliquée
  depuis les citations dans `overrides_v2.json`.
- Commit « grille v2 : harmonisation » **avant** le premier lancement de `analyze_v2.py`.

## Étape 6 : analyse

- `analyze_v2.py` donne la part de `yes` en 2026 avec son intervalle de Wilson, ventilée par
  famille, et la part en 2018 sur nos 12 articles.
- Verdict par critère. Pineau n'a pas publié de chiffres pour Y1 à Y12, donc la seule
  référence de 2018 est notre calibration (12 articles, intervalles larges). Règle :
  « changé » seulement si l'intervalle 2026 exclut la part 2018 **et** que l'intervalle 2018
  exclut la part 2026. Sinon on rapporte le niveau de 2026 et on dit que le recul manque.
- Comparaisons externes, rapportées à côté et non mêlées au verdict :
  - Y11 face à Gorsane et al. 2022 (environ un tiers sans incertitude, RL multi-agent) ;
  - Y12 face à l'adoption de rliable depuis Agarwal et al. 2021 ;
  - Y10 face à Coakley et al. 2026 (partage du code et des données).
- `agree_v2.py` donne l'accord et le kappa. Un critère où l'accord est sous 70 % est signalé
  dans le texte comme fragile.
- Commit « grille v2 : résultats ».

## Étape 7 : mettre à jour `docs/`

- `docs/figures/build.py` : ajouter les lignes Y au dumbbell (2018 calibration contre 2026),
  ou une seconde figure si celle-ci devient illisible, et `sprezzature-figures check` doit
  passer. Le tableau des failles change de verdict pour F3, F6, F8, F12, F13, F14, F15 et F16.
- Mettre à jour les sections Résumé, Méthode, chacune des quatre familles de failles,
  Discussion, Limites (accord inter-lecteurs) et « Ce qui reste à mesurer ».
- `docs/build.sh` doit compiler sans avertissement. Commit.
- Mettre à jour la mémoire `pineau-rl-survey-framing` : grille v2 codée.

## Ce que ce plan ne fait pas

- Il ne touche pas à l'article de blog ni à `~/web/deraison`. C'est l'étape 4 de
  `.private/plan.md`, et elle attend aussi E2 à E7.
- Il ne recode aucun critère v1.
- Il ne publie rien.

## Ordre et dépendances

```
0 règles ─► 1 outils ─► 2 pilote ─► 3 codage (7 en parallèle) ─► 4 contrôle ─► 5 harmonisation ─► 6 analyse ─► 7 docs
```

Les étapes 0 à 2 se font en une session. L'étape 3 tourne en arrière-plan. Les étapes 4 à 7
attendent la fin de l'étape 3. L'étape 7 peut attendre aussi l'analyse E2 à E7 des simulations,
pour ne reconstruire `docs/` qu'une fois.
