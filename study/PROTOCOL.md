# Remesurer Pineau : les articles de RL de 2025-2026 ont-ils les défauts de 2018 ?

Écrit le 2026-11-08, AVANT tout codage d'article. Rien de ce protocole ne change après avoir vu
les résultats ; toute entorse est notée dans « Écarts » en bas.

## La mesure de 2018 qu'on refait

Joelle Pineau, conférence invitée NeurIPS 2018, « Reproducible, Reusable, and Robust Reinforcement
Learning », diapositives 29-30 (`../slides/neurips2018-pineau.pdf`) : « We surveyed 50 RL papers
from 2018 (published at NeurIPS, ICML, ICLR) ». Huit critères, part des « oui » :

| code | critère | 2018 |
|---|---|---|
| Q1 | Paper has experiments | 100 % |
| Q2 | Paper uses neural networks | 90 % |
| Q3 | All hyperparams for proposed algorithm are provided | 90 % |
| Q4 | All hyperparams for baselines are provided | 60 % |
| Q5 | Code is linked | 55 % |
| Q6 | Method for choosing hyperparams is specified | 20 % |
| Q7 | Evaluations on some variation of a hold-out test set | 10 % |
| Q8 | Significance testing applied | 5 % |

Sa méthode de tirage n'est pas décrite. Nous ne pouvons donc comparer que des ordres de grandeur.

## Ce qu'on ajoute (tiré de sa conférence ICLR 2018 et du débat de 2025)

| code | critère |
|---|---|
| X1 | nombre de graines (essais indépendants) pour les résultats principaux : le plus petit nombre annoncé pour un tableau ou une courbe principale ; « non dit » si absent |
| X2 | incertitude rapportée sur les résultats principaux (écart type, erreur type, intervalle de confiance, bande sur la courbe) |
| X3 | sélection des meilleurs essais (« top-k », « best of N », « meilleur point de contrôle choisi sur le test ») |
| X4 | les références sont réglées avec le même soin que la méthode, et c'est dit (même budget de recherche d'hyperparamètres, ou réglage décrit pour chacune) |
| X5 | famille du papier : `llm` (RL appliqué à un grand modèle de langage ou de vision-langage : RLHF, RLVR, GRPO…), `classic` (agents RL hors grands modèles : contrôle, jeux, robotique, offline RL…), `theory` (pas d'expérience ou expériences jouets illustratives seulement) |
| X6 | pour `llm` seulement : nombre de familles de modèles de base distinctes (Qwen, Llama, Mistral, Gemma, DeepSeek, OLMo… ; deux tailles de Qwen = une famille) |
| X7 | le calcul utilisé est rapporté (GPU, heures ou FLOP) |

## Population et échantillon

- 2026 : les articles acceptés à ICLR 2026, ICML 2026 et NeurIPS 2025 (les trois conférences les
  plus récentes au 8 novembre 2026), listes publiques (proceedings.iclr.cc, icml.cc/virtual/2026,
  neurips.cc/virtual/2025). Un article est « de RL » si son titre correspond à
  `reinforcement learning|\bRL\b|\bRLHF\b|\bRLVR\b|policy optimi[sz]ation|policy gradient|q-learning|actor-critic|\bMDPs?\b`
  (insensible à la casse). Population : 1 252 articles (ICLR 420, ICML 494, NeurIPS 338) sur
  17 836.
- Tirage : `random.Random(2018)`, 17 ICLR, 17 ICML, 16 NeurIPS (`sample_2026.json`).
- PDF : proceedings officiels pour ICLR ; arXiv (titre identique à 85 % au moins) pour ICML et
  NeurIPS, OpenReview refusant les téléchargements automatisés. Huit articles sans PDF librement
  accessible sont remplacés, dans l'ordre, par un tirage `random.Random(2026)` dans le reste de
  la même conférence (`replacements_2026.json`). Biais possible : un article déposé sur arXiv est
  peut-être plus ouvert que la moyenne. Échantillon final : `final_2026.json` (50).
- Calibration 2018 : 6 articles de RL d'ICML 2018 et 6 de NeurIPS 2018, même filtre, même graine
  (`calib_2018.json`). On les code avec la même grille pour vérifier que nos lecteurs retrouvent
  à peu près les chiffres de Pineau ; si l'écart est grand, on le dit et on interprète avec
  prudence.

## Codage

- Un fichier JSON par article dans `codes/<lecteur>/<id>.json` : pour chaque critère, la valeur
  (`yes` / `no` / `na` ; X1 un entier ou `null`), une **citation exacte** de l'article (ou
  « absent après lecture des sections expériences, annexes et liens ») et la page.
- Règles de décision :
  - Q3/Q4 « tous les hyperparamètres » : `yes` si un tableau ou un paragraphe les donne pour
    toutes les méthodes principales ; « on garde les valeurs par défaut de [lib] » sans les lister
    compte `yes` seulement si la version de la bibliothèque est donnée. Q4 `na` s'il n'y a pas de
    référence comparée.
  - Q5 : un lien vers du code (GitHub, site du projet) dans l'article ; « code available upon
    request » ou « will be released » = `no`.
  - Q6 : la méthode de choix est dite (grille, recherche aléatoire, budget, critère) ; « tuned »
    sans plus = `no`.
  - Q7 : évaluation sur des tâches, environnements, graines d'environnement ou jeux de données
    non vus à l'entraînement ou au réglage (pour `llm` : bancs d'essai distincts des données
    d'entraînement RL compte `yes`).
  - Q8 : un test statistique (t, Welch, Mann-Whitney, bootstrap avec intervalle, IQM de rliable
    avec intervalles de confiance stratifiés) appliqué à une comparaison ; des barres d'erreur
    seules = `no` pour Q8 mais `yes` pour X2.
  - X1 : pour `llm`, compter les entraînements RL indépendants, pas les échantillons à
    l'évaluation (pass@k et « 16 samples » ne sont pas des graines).
- Double codage : 10 articles de 2026 (les 10 premiers par ordre d'identifiant après mélange
  `random.Random(7)`) codés par un second lecteur qui ne voit pas le premier codage. Accord
  rapporté critère par critère (pourcentage d'accord ; kappa de Cohen si utile).

## Analyse

Part des `yes` par critère (sur les articles où le critère s'applique), en 2026, avec un
intervalle de Wilson à 95 %, à côté du chiffre de 2018. Ventilé `llm` / `classic` / `theory`.
On classe ensuite chaque critère en trois : amélioré (l'intervalle 2026 exclut le chiffre de
2018 par le haut), régressé (par le bas), pas bougé (sinon). Données brutes, codes, scripts et
PDF de l'échantillon (liens) publiés avec l'article.

## Écarts

Notés pendant le codage, AVANT l'agrégation ; les règles d'harmonisation ci-dessous sont fixées
avant de calculer le moindre pourcentage.

1. X4, configuration partagée : certains lecteurs codent `yes` quand l'article dit seulement que
   la référence reprend la configuration de la méthode, sans réglage décrit pour personne.
   Harmonisation : `yes` exige un réglage décrit pour les références (ou un budget de réglage
   égal annoncé) ; « même configuration, aucun réglage décrit » devient `no`. Recodé depuis les
   citations.
2. X7, calcul : `yes` exige au moins une quantité (heures, nombre de GPU-heures, FLOP, ou un
   nombre de GPU avec une durée) ; le seul nom du matériel devient `no`.
3. Articles sans expérience (Q1 `no`) : Q2 à Q8 et X1 à X4 sont `na` et sortent des
   dénominateurs ; Pineau 2018 annonce 100 % d'expériences, donc ses dénominateurs sont les
   articles expérimentaux.
4. Q7 pour les articles `theory` à expériences jouets : `no` (pas de `na`), comme codé.
5. X3, sélection non énoncée mais visible : quand les propres tableaux de l'article montrent que
   le résultat principal est le meilleur de plusieurs entraînements identiques (LR10 : 23,00 =
   meilleur de 19,87, 21,58, 23,00), X3 devient `yes`. Recodé depuis les citations.
6. Q5 « will be made public at <URL> » : `no`, comme le protocole le dit ; page de projet qui
   annonce le code : `yes` seulement si le lien mène à du code (vérifié à l'analyse).
7. Calibration : sur nos 12 articles de 2018, notre grille est plus sévère que celle de Pineau
   sur Q3 (60 % contre 90 %) et plus indulgente sur Q7 (40 % contre 10 %). On ne conclut donc
   à un changement que s'il tient à la fois contre ses chiffres de 2018 et contre nos propres
   chiffres de 2018 (même grille, mêmes lecteurs) ; sinon « ambigu ».
8. Annexes : le lecteur de calibration a lu les annexes séparées de 2018 (ICML -supp.pdf,
   zip NeurIPS) ; en 2026, les annexes sont dans le PDF principal. C21 (NeurIPS 2018) n'a pas
   d'annexe publiée.
9. Les premiers téléchargements envoyaient une adresse de contact dans l'en-tête User-Agent ;
   retirée ensuite, sans effet sur les données.
10. Le scratchpad est partagé entre lecteurs ; des scripts de travail ont été écrasés en cours de
   route. Les codages, eux, sont dans des dossiers séparés et n'ont pas été touchés.
11. **Grille v2, écrite le 9 novembre 2026 AVANT tout codage v2.** La grille v1 ne couvre qu'une partie des failles montrées par Pineau en 2018 (ICLR, NeurIPS, liste de contrôle v1.2, Henderson et al.). On ajoute, pour les mêmes 50 + 12 articles, mêmes règles (`yes` / `no` / `na`, citation obligatoire) :
    - Y1 mesure de performance définie (retour final, moyenne sur l'entraînement, aire sous la courbe, pass@k…) et dite ; diapositive 27 de l'ICLR.
    - Y2 barres d'erreur définies (ce que la bande ou l'intervalle représente) ; liste de contrôle v1.2.
    - Y3 nombre de tâches ou d'environnements sur lesquels porte la conclusion principale (entier) ; ≥ 2 si la conclusion est générale ; Henderson tableau 3.
    - Y4 classement ou gain discuté tâche par tâche (une tâche où la méthode perd est montrée ou dite) ; Henderson tableau 3.
    - Y5 implémentation des références identifiée (dépôt, bibliothèque et version, ou réimplémentation dite) ; Henderson figure 6.
    - Y6 essais ou données exclus dits (ou explicitement « aucun ») ; liste de contrôle v1.2.
    - Y7 version de l'environnement ou du banc d'essai donnée (ex. `HalfCheetah-v4`, version de MATH-500 ou du jeu de test) ; liste de contrôle v1.2.
    - Y8 test de généralisation au-delà des conditions d'entraînement (autres graines d'environnement, autres tâches, dynamiques modifiées, distribution de test distincte) ; feuille de route de NeurIPS, p. 37-51.
    - Y9 sensibilité aux hyperparamètres montrée (balayage ou ablation d'au moins un hyperparamètre) ; ICLR 24-26.
    - Y10 dépendances logicielles listées (versions ou fichier d'environnement) ; liste de contrôle v1.2.
    - Y11 type d'incertitude nommé (écart type, erreur type, IC, intervalle interquartile) ; comparable à Gorsane et al. 2022.
    - Y12 outils statistiques post-2018 employés (IQM, IC bootstrap, rliable, profils de performance, probabilité d'amélioration) ; mesure l'adoption d'Agarwal et al. 2021.
    Analyse identique à la v1 (Wilson, calibration 2018 comme garde-fou). Statut : préenregistrée, codage non lancé. Y11 et Y12 ajoutés le même jour, après la recherche de travaux voisins, toujours avant tout codage.
12. **Élargissement du sondage, écrit le 9 novembre 2026 AVANT tout tirage et toute lecture des articles ajoutés.** L'audit (`audit_stats.py`) montre que notre calibration de 2018 (12 articles) et notre RL classique de 2026 (14 articles) manquent de puissance : un écart de 30 points n'y est pas détectable. On ajoute deux échantillons, lus avec la grille v1 et la grille v2 en une seule passe, mêmes règles, citation obligatoire.
    - **A2, calibration de 2018 portée à 50 articles.** Population : les articles de RL (même expression régulière de titre) d'ICML 2018, de NeurIPS 2018 et, si sa liste d'articles acceptés s'obtient, d'ICLR 2018, les trois conférences que Pineau annonce. Les 12 articles actuels restent. Les 38 autres sont tirés dans l'ordre d'un mélange `random.Random(2018)` du reste de la population, avec une répartition proportionnelle à la taille de chaque conférence dans la population. Un article sans PDF librement accessible est remplacé par le suivant dans l'ordre du tirage, et c'est noté.
    - **A3, RL classique de 2026 porté à 50 articles.** Population : les 1 252 articles de `rl_population_2026.json`, moins les 50 déjà lus. Ordre : un mélange `random.Random(2026)`. Tri préalable sur le seul titre, fixé ici : un titre qui contient `LLM`, `language model`, `reasoning`, `RLHF`, `RLVR`, `GRPO`, `preference`, `alignment`, `reward model`, `chain-of-thought`, `math` ou `agentic` (sans tenir compte de la casse) est présumé `llm` et sauté. Les autres titres sont lus dans l'ordre. Le lecteur code la famille (X5) comme avant, et la lecture s'arrête quand 36 articles `classic` ont été codés. Les articles `llm` et `theory` lus en route restent codés et rapportés à part : ils ne s'ajoutent pas à l'échantillon aléatoire de 2026, puisque le tri sur le titre les a filtrés.
    - **Grille v2 (écart 11)** appliquée aussi, dans la même passe, aux 62 articles déjà lus.
    - **Fidélité** : 10 articles tirés au sort parmi les nouveaux (`random.Random(7)`) sont relus par un second agent qui ne voit pas la première lecture. L'accord se calcule sur les lectures brutes, avant harmonisation.
    - **Analyse**, fixée d'avance et identique à `audit_stats.py` (intervalle de Newcombe, test exact de Fisher, correction de Holm). Comparaison principale : RL classique de 2026 (50 articles) contre notre lecture de 2018 (50 articles). Comparaisons secondaires : 2026 (tous) contre Pineau, et notre lecture de 2018 contre Pineau, qui mesure à quel point notre grille diffère de la sienne.
    - **Harmonisation** : les règles des écarts 1, 2, 5 et 6 s'appliquent. Toute règle nouvelle s'écrit ici avant le premier pourcentage.
13. **Relecture humaine à l'aveugle (A1), écrite le 9 novembre 2026 avant toute relecture.** Warith relit seul 10 articles de 2026, les 10 premiers articles expérimentaux hors double lecture dans l'ordre d'un mélange `random.Random(2027)` (NE16, LR16, LR05, MLR06, LR02, LR08, ML03, NER06, ML06, ML15), sur les critères Q4, Q5, Q6, Q7, Q8, X1 et X2, sans voir les lectures des agents. Fiche et règles : `relecture_humaine/`. Accord et kappa de Cohen calculés sur les lectures brutes des agents (`relecture_humaine/compare.py`). Les désaccords sont rapportés un par un, avec les deux citations ; aucun code d'agent n'est modifié après coup sur la foi de cette relecture sans un écart daté.
14. **Règles de décision de la grille v2, écrites le 9 novembre 2026 AVANT tout codage v2** (complément de l'écart 11, qui définissait les critères sans leurs cas limites). Elles valent pour les 62 articles déjà lus comme pour ceux de l'écart 12. Fiche remise aux lecteurs : `GRILLE.md`. Contrôle mécanique de chaque fichier : `check_codes.py`.
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
15. **Harmonisation de la calibration de 2018 (9 novembre 2026, APRÈS avoir vu les pourcentages).** La vérification des citations introuvables (`.private/v1_quotes_audit.md` : 89 citations, aucune inventée, 83 présentes mot pour mot, 1 paraphrase fidèle, 5 valeurs contraires aux règles) a montré que les règles d'harmonisation des écarts 1, 2 et 4 n'avaient été appliquées qu'aux articles de 2026 : `overrides.json` ne contenait aucun article de 2018. La comparaison entre les deux années était donc faite avec deux grilles un peu différentes. Correction : les mêmes règles, appliquées depuis les citations aux 12 articles de 2018 (X4 : C11, C13, C16 et C14 passent à `no` ; Q7 : C14 passe de `na` à `no` ; X7 : C14 passe à `no`). Aucune règle nouvelle. Les pourcentages de 2018 et les comparaisons sont recalculés par `analyze_final.py`, qui régénère désormais `results_final.json` (jusque-là écrit sans script). La seconde lecture (lecteur G) de ML16 sur Q7 contredit aussi l'écart 4 ; elle reste telle quelle, puisque l'accord entre lecteurs se calcule sur les lectures brutes.
16. **Pilote de la lecture élargie, écrit le 9 novembre 2026 AVANT toute lecture v2 et toute lecture des articles ajoutés.** Avant les lecteurs principaux, un lecteur pilote code trois articles : LR08 (`llm`) et ML15 (`classic`), grille v2 seule, choisis par la règle de `.private/planification.md` (`random.Random(11)` sur les 40 articles de 2026 hors double lecture), et C218, grille v1 et v2 en une passe, premier des 38 nouveaux articles de 2018 après un mélange `random.Random(11)` de leurs identifiants triés. Le pilote sert seulement à trouver les règles ambiguës et à tester `check_codes.py` ; ses fichiers (`codes_v2/pilot/`) n'entrent dans aucune analyse, et ces trois articles sont recodés ensuite par leur lecteur normal. Une règle précisée après le pilote est écrite ici, datée, avant le codage principal, et seulement pour lever une ambiguïté.
17. **Règles précisées après le pilote, écrites le 9 novembre 2026 AVANT le codage principal.** Le pilote (écart 16 : LR08, ML15, C218) a relevé des cas que les règles ne tranchaient pas. Chaque précision lève une ambiguïté ; aucune ne vise un chiffre, puisqu'aucun pourcentage v2 n'existe.
    - **Annexes de 2018.** Les annexes de NeurIPS 2018 sont récupérées sur la page officielle des actes (copie de l'Internet Archive, le site étant injoignable) et rangées en `pdf/<id>-supp.pdf` : 9 des 14 nouveaux articles NeurIPS en ont une (C28, C29, C210, C212, C213, C214, C215, C216, C218) ; les pages des 5 autres (C27, C211, C217, C219, C220) n'en listent aucune. Un article qui renvoie à une annexe introuvable est codé sur ce qui existe, et le lecteur le note dans `doubts`.
    - **Y1.** `yes` exige la quantité et le point de mesure (final, N derniers épisodes, meilleur point, aire sous la courbe). Un score normalisé dont on ne dit pas à quel point il est pris : `no`. Le nombre d'épisodes d'évaluation n'est pas exigé.
    - **Y3.** Une tâche est un cadre d'entraînement distinct sur lequel la méthode est entraînée et comparée : un environnement, ou un jeu de données d'entraînement pour `llm`. Plusieurs bancs d'évaluation d'un même modèle entraîné ne multiplient pas les tâches. Les variantes de qualité d'un jeu de données d'un même environnement (D4RL medium, replay, expert) comptent pour une seule tâche, comme les niveaux de difficulté.
    - **Y5.** Des chiffres de références recopiés d'articles publiés, avec la source citée pour chacun, comptent `yes` : l'origine des chiffres est dite.
    - **Y6.** Une combinaison omise des résultats (modèle, jeu de données, tâche) avec sa raison compte comme une exclusion dite.
    - **Y7.** « Chaque » reste strict. Un jeu de données publié sur un dépôt nommé (lien Hugging Face, par exemple) compte comme versionné ; une séparation construite par les auteurs compte seulement si elle est publiée.
    - **Y8 et Q7.** Des graines d'entraînement nouvelles, utilisées pour entraîner, ne sont pas des conditions tenues à part : `no` pour Y8, et `no` pour Q7 par la règle v1 (« non vus à l'entraînement ni au réglage »).
    - **Y9.** Compte un hyperparamètre que l'article présente comme tel. Une variante que l'article présente comme un composant reste une ablation.
    - **Y11.** Des bandes de centiles autres que l'intervalle interquartile : `kind` = `other`.
    - **Portée.** Pour les articles déjà lus en v1, le lecteur reçoit les valeurs v1 de Q1, Q4 et X2, qui fixent les règles de portée ; il ne voit pas les autres codes v1.
    - **Format.** Une citation cousue sur deux pages peut avoir une liste de pages. Dans un PDF à deux colonnes, le lecteur découpe une citation qui chevauche des lignes en morceaux d'une ligne joints par « [...] ».
    - **A3, PDF introuvables.** Un article de la file sans PDF librement accessible est sauté, comme pour A2. Les 9 articles d'ICLR 2026 de tête de file (K007, K018, K020, K022, K025, K026, K027, K029, K031) étaient injoignables le 9 novembre 2026 après deux tentatives, le site des actes étant en panne : ils sont sautés aussi, et la file est figée telle quelle pour que la sélection ne dépende pas de la date de lecture.
18. **X5 précisé, écrit le 9 novembre 2026 APRÈS la lecture de la file A3 et AVANT de figer l'échantillon et tout pourcentage.** X5 décide de l'entrée d'un article de la file A3 dans l'échantillon classique. La définition v1 (« RL appliqué à un grand modèle de langage ou de vision-langage ») se lit sur le modèle que le RL entraîne : `llm` si la politique optimisée est un modèle génératif préentraîné conditionné par le langage (modèle de langue de toute taille, modèle de vision-langage, modèle texte-image) ; `classic` si le RL entraîne autre chose, même au service d'un grand modèle (un masque de sélection de données, une machine à récompense écrite par un modèle de fondation non entraîné), ou un réseau d'architecture transformeur entraîné de zéro sur des tâches de RL. `theory` reste réservé aux articles sans expérience ou à expériences jouets seulement ; un article à résultats théoriques qui compare des méthodes sur des bancs d'essai usuels, même en annexe, est `classic`. Appliquée aux citations X5 des 120 articles lus, la règle ne change qu'un code : K006 passe de `llm` à `classic` (`overrides_v2.json`). Les 50 articles du premier échantillon et les 50 de 2018 la respectent déjà.
19. **Harmonisation de la grille v2, écrite le 9 novembre 2026 APRÈS l'audit des lectures brutes (`harmonisation_audit.md`) et AVANT tout pourcentage.** L'audit relit tous les fichiers critère par critère, sans compter de `yes`. Il trouve des codes contraires aux règles et dix cas qu'aucune règle ne tranchait. Les décisions ci-dessous s'appliquent aux deux années, depuis les citations, dans `overrides_v2.json`, chaque changement avec sa raison. L'accord entre lecteurs reste calculé sur les lectures brutes.
    - **Y1.** Une courbe d'apprentissage dont les points d'évaluation sont dits vaut un point de mesure. « Entraîné N pas » puis un seul chiffre pour le modèle entraîné vaut le point final. Pour une quantité qui n'est pas le score d'une politique entraînée (erreur d'un estimateur, temps de calcul, test statistique, sortie d'un solveur), le point de mesure ne s'applique pas : `yes` si la quantité est définie. Sinon la règle de l'écart 17 s'applique telle quelle.
    - **Y3.** Un seul méta-entraînement (RL en contexte, méta-RL) compte pour une tâche. Un cadre présent seulement en annexe ne compte pas.
    - **Y5.** Comptent comme origine dite : un dépôt, une bibliothèque ou un cadre logiciel nommé, avec ou sans version (la version relève de Y10) ; « réimplémenté par nous » ; des chiffres recopiés avec leur source (écart 17) ; un modèle publié désigné par son nom exact et évalué par les auteurs ; le cadre d'entraînement des auteurs, s'il est dit que les références y tournent. Une réimplémentation sous-entendue mais jamais dite ne compte pas. « Chaque » s'applique aux références principales : une seule sans origine donne `no`.
    - **Y6.** Un filtrage des données d'entraînement dit, avec ce qu'il retire, compte comme une exclusion de données.
    - **Y7.** Un banc d'essai ou une séparation désignés par un nom qui fixe un seul ensemble publié comptent comme MATH-500. Un nom qui couvre plusieurs ensembles ou plusieurs années sans dire lequel (« MATH », « AMC », « Minerva ») ne compte pas. Un environnement entièrement spécifié dans l'article (équations, paramètres) compte comme versionné.
    - **Y8.** Pour `llm`, un banc présenté explicitement comme une généralisation à un domaine ou à une tâche absents de l'entraînement compte ; un banc différent sans ce propos ne compte pas. Une séparation de test i.i.d. de la même distribution relève de Q7, pas de Y8. Y8 `yes` suppose Q7 `yes` : si les deux codes d'un article se contredisent, le passage est relu et la valeur de Y8 suit la lecture ; Q7 v1 n'est pas recodé.
    - **Y9.** Un paramètre réglé à l'inférence compte s'il est présenté comme un hyperparamètre ; une condition de l'environnement ne compte pas ; le résultat montré doit être une mesure de performance.
    - **Q5 (écart 6).** Chaque lien vers une page de projet est visité le 9 novembre 2026 : `yes` si la page mène à du code, `no` si elle n'y mène pas ou ne répond plus. Un miroir anonyme qui contient le code compte `yes`.
    - **X3, X4, X7 (v1).** Aucune règle nouvelle : une règle ajoutée maintenant ne s'appliquerait qu'aux articles de la lecture élargie, ce que l'écart 15 interdit. Les cas limites relevés par l'audit (temps d'inférence seul, graines ratées écartées) restent codés comme le lecteur les a lus, et le texte les mentionne dans les limites.
    - **Application (9 novembre 2026, avant tout pourcentage).** 80 changements, chacun avec sa raison dans `overrides_v2.json` : Y1 21, Y3 5 (et Y4 5 par la règle de portée), Y5 10, Y6 3, Y7 19, Y8 6, Y9 9, Q5 2. Pages de projet visitées : cinq mènent au code, deux non (K090 : miroir anonyme expiré, HTTP 410 ; C19 : la page mène à une bibliothèque publiée après l'article, sans ses scripts). Deux cas tranchés par le responsable : pour NE16 et ML14, dont toutes les expériences sont en annexe, la règle « un cadre présent seulement en annexe ne compte pas » ne s'applique pas, et Y3 reste celui du lecteur.
20. **Règle de verdict du document, décidée le 9 novembre 2026 APRÈS les premiers résultats de la lecture élargie.** Jusqu'ici, un critère « avait changé » quand l'écart tenait contre les chiffres de Pineau, et le changement était « confirmé » contre notre lecture de 2018. La comparaison secondaire de l'écart 12 montre que notre grille lit 2018 autrement que Pineau (Q3 : 55 % contre 90 %, Holm p = 0,001 ; Q7 : 33 % contre 10 %, Holm p = 0,03). Comparer 2026 à ses chiffres mêle donc deux changements. Désormais, un verdict du document repose seulement sur la comparaison principale de l'écart 12 (RL classique 2026 contre notre lecture de 2018, mêmes grilles, mêmes lecteurs), fixée avant toute lecture des articles ajoutés ; les comparaisons avec Pineau restent montrées comme contexte. Ce changement de règle est décidé après avoir vu ces résultats : nous le déclarons comme tel.
