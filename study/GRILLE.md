*English version: [GRILLE-en.md](GRILLE-en.md).*

# Fiche du lecteur : grilles v1 et v2

Cette fiche résume `PROTOCOL.md` pour qui lit un article. En cas de doute, le protocole fait foi
(règles de décision, écarts 1 à 6 pour l'harmonisation, écart 14 pour la grille v2).

## Ce qu'on attend de toi

- Lire l'article entier, annexes comprises (`pdf/<id>.pdf`, et `pdf/<id>-supp.pdf` s'il existe).
- Remplir un fichier JSON par article dans `codes_v2/<lecteur>/<id>.json`, au format ci-dessous.
- Pour chaque critère : la valeur, une **citation exacte** de l'article (copiée du PDF, mot pour mot)
  et la page. Si rien ne justifie un `yes`, la citation est « absent après lecture des sections
  expériences, annexes et liens » et la page est `null`.
- Ne jamais lire les codes d'un autre lecteur (`codes/`, `codes_v2/`), ni les résultats
  (`results_*.json`, `audit_stats.json`), ni le document `docs/`.

## Les critères de la grille v1

| code | critère | valeurs |
|---|---|---|
| Q1 | L'article a des expériences | yes / no |
| Q2 | Il emploie des réseaux de neurones | yes / no / na |
| Q3 | Tous les hyperparamètres de la méthode sont donnés | yes / no / na |
| Q4 | Tous les hyperparamètres des références sont donnés | yes / no / na |
| Q5 | Le code est en lien | yes / no / na |
| Q6 | La façon de choisir les hyperparamètres est décrite | yes / no / na |
| Q7 | L'évaluation se fait sur des conditions tenues à part | yes / no / na |
| Q8 | Un test statistique est appliqué à une comparaison | yes / no / na |
| X1 | Nombre d'entraînements indépendants pour les résultats principaux | entier ou null |
| X2 | Une incertitude est rapportée sur les résultats principaux | yes / no / na |
| X3 | Les meilleurs essais sont sélectionnés (« top-k », « best of N », meilleur point de contrôle choisi sur le test) | yes / no / na |
| X4 | Les références sont réglées avec le même soin, et c'est dit | yes / no / na |
| X5 | Famille : `llm`, `classic` ou `theory` | une des trois |
| X6 | Pour `llm` : nombre de familles de modèles de base distinctes | entier ou null |
| X7 | Le calcul employé est chiffré | yes / no / na |

**Règles v1** (protocole, puis écarts d'harmonisation) :
- Q1 `no` : tous les autres critères valent `na` (écart 3).
- Q3 et Q4 : `yes` si un tableau ou un paragraphe les donne pour toutes les méthodes principales.
  « Valeurs par défaut de [bibliothèque] » sans les lister compte `yes` seulement si la version
  est donnée. Q4 `na` s'il n'y a aucune référence comparée.
- Q5 : un lien vers du code dans l'article. « Sur demande », « sera publié », « will be made public
  at <URL> » : `no`. Une page de projet compte `yes` seulement si elle mène à du code (écart 6).
- Q6 : la méthode de choix est dite (grille, recherche aléatoire, budget, critère). « Tuned » sans
  plus : `no`.
- Q7 : évaluation sur des tâches, environnements, graines aléatoires d'environnement ou jeux de
  données non vus à l'entraînement ni au réglage. Pour `llm`, des bancs d'essai distincts des
  données d'entraînement RL comptent `yes`. Article `theory` à expériences jouets : `no` (écart 4).
- Q8 : un test (t, Welch, Mann-Whitney, bootstrap avec intervalle, IQM de rliable avec intervalles
  stratifiés) appliqué à une comparaison. Des barres d'erreur seules : `no` pour Q8, `yes` pour X2.
- X1 : pour `llm`, compter les entraînements RL indépendants, pas les échantillons d'évaluation
  (pass@k et « 16 samples » ne sont pas des entraînements).
- X3 : `yes` aussi quand les propres tableaux de l'article montrent que le résultat principal est
  le meilleur de plusieurs entraînements identiques, même si le texte ne le dit pas (écart 5).
- X4 : `yes` exige un réglage décrit pour les références, ou un budget de réglage égal annoncé.
  « Même configuration que la méthode », sans réglage décrit pour personne : `no` (écart 1).
- X7 : `yes` exige au moins une quantité (heures, GPU-heures, FLOP, ou un nombre de GPU avec une
  durée). Le seul nom du matériel : `no` (écart 2).

## Les critères de la grille v2 (écart 11, règles de l'écart 14)

| code | critère | valeurs |
|---|---|---|
| Y1 | La mesure de performance est définie | yes / no / na |
| Y2 | Les barres d'erreur sont définies | yes / no / na |
| Y3 | Nombre de tâches de la conclusion principale | entier ou null |
| Y4 | Une tâche où la méthode ne gagne pas est montrée | yes / no / na |
| Y5 | L'implémentation des références est identifiée | yes / no / na |
| Y6 | Les exclusions sont dites (ou « aucune ») | yes / no / na |
| Y7 | La version des environnements ou bancs d'essai est donnée | yes / no / na |
| Y8 | Un test de généralisation hors des conditions d'entraînement | yes / no / na |
| Y9 | La sensibilité à au moins un hyperparamètre est montrée | yes / no / na |
| Y10 | Les dépendances logicielles sont listées avec leurs versions | yes / no / na |
| Y11 | Le type d'incertitude est nommé (avec `kind`) | yes / no / na |
| Y12 | Un outil statistique postérieur à 2018 est employé | yes / no / na |

**Règles v2** : celles de l'écart 14 de `PROTOCOL.md`, à lire en entier avant de commencer. Les
points qui piègent le plus souvent :
- Q1 `no` : Y1 à Y12 valent `na`.
- Y2 et Y11 valent `na` si et seulement si X2 vaut `no`.
- Y4 vaut `na` si Y3 vaut 1. Y5 vaut `na` si et seulement si Q4 vaut `na`.
- Y8 est plus strict que Q7 : pour `llm`, un banc d'essai différent ne compte que s'il est
  présenté comme un test hors distribution.
- Y9 : une ablation de composant n'est pas un balayage d'hyperparamètre.
- Y11 : ajouter le champ `kind` (`std`, `se`, `ci`, `iqr`, `minmax`, `other`).
- Lire aussi l'écart 17 (précisions après le pilote) : Y1 exige le point de mesure, Y3 compte
  les cadres d'entraînement, Y5 accepte des chiffres recopiés avec leur source, Y7 reste strict.

**Conseils pratiques** :
- Pour un article déjà lu en v1, ta liste donne Q1, Q4 et X2 v1 : ils fixent les règles de portée.
- Une citation sur deux pages : `"page": [6, 7]`.
- PDF à deux colonnes : `pdftotext -layout` mélange les colonnes. Découpe une citation qui
  chevauche des lignes en morceaux d'une ligne, joints par « [...] ».
- Lance `python3 check_codes.py codes_v2/<lecteur>` depuis `study/` et corrige jusqu'à 0.

## Le format du fichier

```json
{
 "id": "K001",
 "coder": "H",
 "title": "Titre exact de l'article",
 "criteria": {
  "Q1": {"value": "yes", "quote": "We evaluate on six MuJoCo tasks", "page": 6},
  "X1": {"value": 5, "quote": "averaged over 5 random seeds", "page": 7},
  "Y3": {"value": 6, "quote": "We evaluate on six MuJoCo tasks", "page": 6},
  "Y11": {"value": "yes", "kind": "se", "quote": "shaded areas denote one standard error", "page": 7}
 },
 "doubts": "Les cas où tu as hésité, en une phrase chacun."
}
```

Pour un article déjà lu en v1 (identifiants `LR..`, `ML..`, `MLR..`, `NE..`, `NER..`, `C1..`,
`C2..`), ne remplir que Y1 à Y12 : les valeurs v1 servent seulement aux règles de portée, et
`check_codes.py` les relit dans `codes/`.
