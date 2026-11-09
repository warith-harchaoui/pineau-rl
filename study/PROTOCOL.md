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
