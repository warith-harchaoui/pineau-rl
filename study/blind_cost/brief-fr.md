*Traduction de [brief.md](brief.md), faite le 10 novembre 2026. Le texte anglais est l'original.*

# Consigne de notation (identique pour les trois évaluateurs, PROTOCOL.md, écart 21 b)

Traduction pour le lecteur : les trois évaluateurs ont reçu le texte anglais, mot pour mot.

Vous notez des pratiques de compte rendu et d'évaluation que l'on trouve dans les articles expérimentaux d'apprentissage par renforcement profond.
Vous n'avez aucune donnée et n'en avez pas besoin : notez chaque pratique d'après sa seule définition, d'après ce que vous savez de la façon
dont ces articles s'écrivent. Ne cherchez rien et ne lisez aucun fichier.

Imaginez un auteur qui a déjà mené les expériences principales d'un article et qui tient les résultats principaux en main.
Pour chaque pratique ci-dessous, donnez deux entiers de 1 à 5 :

- **C, coût** : le travail ou le calcul supplémentaire que cet auteur doit dépenser pour satisfaire la pratique.
  1 = une phrase, un tableau ou un lien vers quelque chose qui existe déjà ; 3 = un peu d'analyse en plus ou quelques
  exécutions supplémentaires ; 5 = de nombreux nouveaux entraînements ou un gros travail nouveau.
- **R, risque pour la conclusion** : la probabilité que satisfaire la pratique affaiblisse ou renverse la thèse principale
  de l'article (par exemple en montrant que le gain n'est pas significatif, ou qu'il est plus petit qu'annoncé).
  1 = elle ne peut pas toucher la thèse ; 3 = elle la touche parfois ; 5 = elle la touche souvent.

Les pratiques (chacune est ce qu'un article doit faire pour être codé « yes ») :

1. **Q3** : donne tous les hyperparamètres de la méthode proposée, dans un tableau ou un paragraphe.
2. **Q4** : donne tous les hyperparamètres des références auxquelles il se compare.
3. **Q5** : donne dans l'article un lien vers son code (« disponible sur demande » ou « sera publié » ne comptent pas).
4. **Q6** : décrit comment les hyperparamètres ont été choisis (grille, recherche aléatoire, budget, critère) ; « tuned » seul ne compte pas.
5. **Q7** : évalue sur des tâches, des environnements, des graines aléatoires d'environnement ou des données non vus pendant l'entraînement ou le réglage.
6. **Q8** : applique un test statistique à une comparaison (test t, Welch, Mann-Whitney, bootstrap avec intervalle, intervalles IQM stratifiés) ; des barres d'erreur seules ne comptent pas.
7. **X2** : rapporte une incertitude (barres d'erreur, écart type, intervalle) sur les résultats principaux.
8. **X3 (inversé)** : ne sélectionne PAS ses meilleurs essais (pas de « top-k », pas de « best of N », pas de meilleur point de contrôle choisi sur l'ensemble de test).
9. **X4** : règle ses références avec le même soin que sa méthode et le dit (une procédure de réglage décrite pour les références, ou un budget de réglage égal annoncé).
10. **X7** : chiffre le calcul employé (heures, GPU-heures, FLOP, ou un nombre de GPU avec une durée) ; le seul nom du matériel ne compte pas.
11. **Y1** : définit la mesure de performance rapportée (score final, moyenne des derniers épisodes ou aire sous la courbe, avec le point de l'entraînement où elle est mesurée).
12. **Y5** : identifie l'implémentation (base de code) employée pour chaque référence.
13. **Y7** : donne la version de chaque environnement ou banc d'essai employé.
14. **Y8** : mène un test de généralisation hors des conditions d'entraînement (tâches, dynamiques ou données absentes de l'entraînement).
15. **Y9** : montre la sensibilité de la méthode à au moins un hyperparamètre (un balayage avec ses résultats ; une ablation de composant ne compte pas).
16. **Y10** : liste ses dépendances logicielles avec leurs versions.
17. **Y12** : emploie un outil statistique postérieur à 2018 (moyenne interquartile, rliable, profils de performance, probabilité d'amélioration).

Répondez par un objet JSON seul, sans prose, de la forme
`{"Q3": {"C": 1, "R": 1, "why": "one short sentence"}, ...}` avec les 17 clés.
