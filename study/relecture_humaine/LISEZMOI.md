*English version: [README.md](README.md).*

# Relecture humaine à l'aveugle (expérience A1)

**Abandonnée le 10 novembre 2026 avant toute relecture (écart 23 de `study/PROTOCOL.md`).** Ce dossier garde le plan.

Depuis le 22 novembre 2026, ce dossier sert aussi à deux relectures humaines demandées par Warith Harchaoui : sa
relecture passée, s'il en retrouve la trace (`warith_v0.csv`, section suivante ; écart 34 réservé, écrit seulement
quand les faits seront fournis), puis une relecture à l'aveugle préenregistrée des deux années (écart 35, section
« Relecture de l'écart 35 » plus bas). Le plan A1 ci-dessous reste tel quel ; son script s'appelle désormais
`compare_a1.py`.

## `warith_v0.csv` : la relecture passée de Warith

Une ligne par article et par critère, colonnes `id, critere, decision, date, aveugle, citation, page, source` :

- `id` : l'identifiant de l'article dans le sondage (`C11`, `K015`, `LR11`…) ;
- `critere` : le code du critère (`Q5`, `X2`, `Y9`…) ;
- `decision` : `yes`, `no` ou `na` ; un entier pour X1, X6 et Y3 ;
- `date` : le jour de la lecture (`AAAA-MM-JJ`), ou le mois (`AAAA-MM`), ou l'année si c'est tout ce que la trace dit ;
- `aveugle` : `oui` si Warith ne voyait pas la lecture des agents au moment de lire, `non` s'il la voyait ;
- `citation` et `page` : le passage de l'article qui fonde la décision avec sa page, si la trace les donne ;
- `source` : d'où vient la ligne (un fichier, un carnet, un courriel, avec sa date), pour qu'on puisse la retrouver.

Rien n'est déduit ni reconstruit : une ligne dont la trace manque reste absente. Quand le fichier a au moins une ligne,
`../sim/env-an/bin/python relecture_humaine/accord_v0.py` (depuis `study/`) écrit `accord_v0.json` : pour chaque
critère, la part d'accord avec la lecture des agents et son intervalle de Wilson, le kappa de Cohen avec un intervalle
bootstrap (10 000 tirages, `default_rng(2037)`), comme `agree_v2.py`. Les « oui » des agents sont comptés à part de
leurs « non » : une relecture qui voyait la lecture des agents vérifie surtout leurs « oui ». Tout est donné pour les
lignes `aveugle = oui`, pour les lignes `aveugle = non`, contre les valeurs finales harmonisées et contre les lectures
brutes. Tant que le fichier n'a aucune ligne, le script s'arrête.

Le script n'est pas encore dans le `Makefile`, pour que `make verify` passe avec un fichier vide. Une fois le fichier
rempli : ajouter `relecture_humaine/accord_v0` à la fin de la liste `STUDY` et `study/relecture_humaine/accord_v0.json`
à `OUTPUTS`, lancer le script une fois, valider `accord_v0.json`, puis écrire l'écart 34 dans les deux protocoles.

Écart 13 de `study/PROTOCOL.md`. But : mesurer l'accord entre une lecture humaine et la lecture des
agents, sur les critères qui fondent les verdicts du document. C'est la réponse à l'objection « des
machines ont lu les articles ».

## La règle d'or : ne rien regarder des agents avant d'avoir fini

N'ouvre ni `study/codes/`, ni `study/results_*.json`, ni `study/audit_stats.json`, ni le document
`docs/conclusions.md` pour ces 10 articles avant d'avoir rempli toute la grille. La comparaison se
fait ensuite, par script.

## Ce qu'il faut faire

1. Ouvre `grille.csv` (dans un tableur). Une ligne par article. Le PDF se trouve dans
   `study/pdf/<id>.pdf` (dépôt local ; `study/fetch.py` le retélécharge au besoin).
2. Pour chaque critère, écris `yes`, `no` ou `na` dans la colonne du critère, une citation exacte
   de l'article dans la colonne `_citation`, et la page dans la colonne `_page`. Si rien ne
   justifie un `yes` après lecture des expériences, des annexes et des liens, écris `no` et
   « absent » en citation.
3. Pour X1, écris un nombre entier (le plus petit nombre d'entraînements indépendants annoncé pour
   un résultat principal), ou laisse vide si l'article ne le dit pas.
4. Compte environ 20 à 25 minutes par article.
5. Quand c'est fini : `python3 study/relecture_humaine/compare_a1.py`. Le script donne l'accord et le
   kappa de Cohen, critère par critère, et liste les désaccords avec les deux citations.

## Les sept critères et leurs règles (celles des agents, `study/PROTOCOL.md`)

- **Q4, tous les hyperparamètres des références sont donnés.** `yes` si un tableau ou un paragraphe
  les donne pour toutes les méthodes comparées. « Valeurs par défaut de [bibliothèque] » sans les
  lister compte `yes` seulement si la version de la bibliothèque est donnée. `na` s'il n'y a pas de
  référence comparée. `no` si une référence n'est réglée que par « même configuration » sans
  réglage décrit (écart 1).
- **Q5, le code est en lien.** Un lien vers du code (GitHub, site du projet) dans l'article.
  « Code disponible sur demande » ou « sera publié » : `no`. Une page de projet compte `yes`
  seulement si elle mène à du code.
- **Q6, la façon de choisir les hyperparamètres est décrite.** Grille, recherche aléatoire,
  budget, critère de choix. « Réglés » sans plus : `no`.
- **Q7, l'évaluation se fait sur des conditions tenues à part.** Tâches, environnements, graines
  aléatoires d'environnement ou jeux de données non vus à l'entraînement ni au réglage. Pour un
  article sur les grands modèles de langue, des bancs d'essai distincts des données
  d'entraînement RL comptent `yes`. Un article de théorie à expériences jouets : `no`.
- **Q8, un test statistique est appliqué à une comparaison.** Test t, Welch, Mann-Whitney,
  bootstrap avec intervalle, IQM de rliable avec intervalles. Des barres d'erreur seules : `no`.
- **X1, nombre d'essais.** Pour un article sur les grands modèles de langue, on compte les
  entraînements RL indépendants, pas les échantillons d'évaluation (pass@k, « 16 samples »).
- **X2, une incertitude est rapportée** sur les résultats principaux : écart type, erreur type,
  intervalle de confiance, bande sur la courbe.
