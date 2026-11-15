# Qui a lu les articles, avec quelles consignes

*English: [README.md](README.md)*

Les articles du sondage ont été lus par des agents de langage (des sous-agents de Claude Code), un dossier
de lecture par agent (`study/codes/<lecteur>/`, `study/codes_v2/<lecteur>/`). Ce dossier en donne la
provenance, reconstruite le 15 novembre 2026 à partir des transcriptions des sessions de Claude Code, qui
restent sur la machine de l'auteur et ne sont pas publiées.

- `readers.csv` : une ligne par agent (38 lecteurs, 3 agents d'audit ou d'harmonisation, 4 sous-tâches
  lancées par l'agent d'harmonisation). Colonnes : grille, rôle, session, début et fin (UTC), modèle exact
  relevé dans la transcription, articles écrits, outils appelés, manière de lire les PDF, preuves (numéros
  de ligne et horodatages dans les transcriptions).
- `prompts/<lecteur>.md` : la consigne exacte donnée à chaque agent, mot pour mot, suivie de tout message
  envoyé ensuite au même agent (reprise après une limite d'usage, passe sur les annexes). Seuls les débuts
  de chemins sont abrégés : `~/` pour le dossier personnel, `<scratchpad>/` pour le dossier temporaire,
  `<transcripts of …>/` pour les transcriptions.
- `folder_check.csv` : pour chacun des 38 dossiers de lecture, l'agent qui l'a écrit, et l'accord entre
  les fichiers du dossier et les articles confiés à cet agent. Aucun écart.

Ce que la reconstruction établit, et ses limites (écart 28 de `../PROTOCOL.md`) :

- Tous les lecteurs ont tourné sur le modèle `claude-opus-5-5`, sauf deux qui ont fini sur `claude-opus-5`
  après l'arrêt d'une réponse par un filtre de sécurité : C2 (articles ML14 à ML17) et M4 (neuf articles
  de A4). Les consignes ont toutes été écrites par l'agent coordinateur, aucune à la main.
- Chaque lecteur a converti les PDF en texte avec `pdftotext`, et beaucoup ont aussi regardé des images
  des pages (`pdftoppm`).
- Les seconds lecteurs (G, G2, R2, R3) n'ont ouvert aucun fichier d'un autre lecteur : leurs appels
  d'outils le montrent. Un lecteur principal, M7, a ouvert le fichier K002 de K1 comme exemple de format ;
  K002 n'est ni à lui ni dans une double lecture.
- Les doubles lectures sont faites par des copies du même modèle : leur accord mesure la stabilité de la
  lecture par ce modèle, pas l'accord entre deux lecteurs indépendants.
