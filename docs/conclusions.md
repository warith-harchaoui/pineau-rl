---
title: "A-t-on écouté Joelle Pineau en 2018 ?"
subtitle: "Un état de l'art revisité. Chaque faille qu'elle a montrée en 2018, mesurée dans les articles de 2018 à 2026 et dans nos propres expériences"
author: "Warith Harchaoui"
date: "9 novembre 2026, état intermédiaire"
lang: fr
bibliography: refs.bib
link-citations: true
---

# Résumé {.unnumbered}

En 2018, la chercheuse Joelle Pineau a donné deux conférences devant les plus grands congrès de
l'intelligence artificielle. Elle y a montré, chiffres à l'appui, pourquoi on avait du mal à croire
les résultats d'un domaine alors en pleine gloire : l'apprentissage par renforcement profond, qui
apprend à une machine à agir par essais et erreurs. Nous y avons relevé seize failles. Le code des
articles manquait. Les réglages restaient secrets. Les méthodes concurrentes étaient moins bien
réglées que la méthode défendue. Les expériences reposaient sur trop peu d'essais, dont on gardait
les meilleurs. Aucun test statistique ne venait trancher. On évaluait même les agents sur les
situations qui avaient servi à les entraîner [@pineau2018iclr; @pineau2018neurips;
@henderson2018matters].

Ce document reprend la liste entière, faille par faille. Il pose chaque fois la même question :
huit ans plus tard, l'avons-nous écoutée ? Deux instruments répondent. Le premier est un sondage :
nous relisons 50 articles de 2025 et 2026 tirés au sort, avec la grille de lecture de Pineau. Nous relisons aussi
12 articles de 2018 pour vérifier que notre lecture retrouve ses chiffres. Le second rassemble des
expériences : nous refaisons celles de 2018 avec les algorithmes de 2026, en écrivant le protocole
avant le premier entraînement.

Sur seize failles, une seule a progressé nettement, pour une raison inattendue : 70 % des articles
de 2026 évaluent leurs agents sur des situations tenues à part, contre 10 % en 2018. La hausse
vient presque entière des articles sur les grands modèles de langue, dont les bancs d'essai
séparent par construction l'entraînement et le test. Dans le RL classique, nous ne détectons aucun
changement. Une faille a reculé : les réglages des méthodes concurrentes ne sont plus donnés que
dans 18 % des articles, contre 60 % chez Pineau, un écart qui résiste à la correction pour
comparaisons multiples. Pour trois autres, nous ne détectons aucun changement : le test
statistique (4 % des articles), la description de la façon dont on règle une méthode (27 %) et le
nombre d'essais, que la moitié des articles taisent. Nos expériences précisent la faille la plus
célèbre. Sur nos trente essais, deux groupes de cinq tirés au hasard ne trompent un test
statistique que dans 1,2 % des cas. Le test se laisse tromper quand on trie les essais (31 %). Garder
les meilleurs gonfle le score de 33 %. Elles montrent aussi pourquoi un résultat trop beau se vérifie : notre
propre référence s'est effondrée, une erreur de notre code semblait l'expliquer. Sa correction n'a
rien changé. Six failles restent à mesurer :
ce document dit comment.

# Deux conférences en 2018

**Vancouver, puis Montréal.** Au printemps 2018, Joelle Pineau, professeure à l'université McGill
de Montréal et directrice du laboratoire montréalais de recherche en intelligence artificielle de
Facebook, monte sur la scène d'ICLR (*International Conference on Learning Representations*,
conférence internationale sur l'apprentissage des représentations), à Vancouver. En décembre, elle
reprend et augmente son propos à NeurIPS (*Neural Information Processing Systems*), à Montréal.
ICLR, NeurIPS et ICML (*International Conference on Machine Learning*) forment le trio de tête des
congrès où se publie la recherche en apprentissage automatique. Sa conférence d'ICLR s'intitule
« Reproductibilité, réutilisabilité et robustesse en apprentissage par renforcement profond ».
Celle de NeurIPS, donnée comme conférence Posner, s'intitule « Apprentissage par renforcement
reproductible, réutilisable et robuste ».

**Une question simple.** Si une équipe publie un résultat, une autre équipe qui suit la recette
obtient-elle le même ? Pineau part d'un sondage de la revue *Nature* : sur 1 576 chercheurs de
toutes disciplines, plus de 70 % disaient avoir déjà échoué à reproduire l'expérience d'un collègue
[@baker2016reproducibility]. Dans le même sondage, 52 % des chercheurs voient une crise
« significative » de la reproductibilité, 38 % une crise « légère ». Pineau a posé la même question
à vingt spécialistes de l'apprentissage automatique lors d'un atelier, en décembre 2017 : 80 % y
voient une crise, légère ou significative [@pineau2018iclr]. Elle cite ensuite une phrase de deux chercheurs de Stanford,
Buckheit et Donoho, écrite en 1995 pour condenser une idée de leur collègue Jon Claerbout : un
article scientifique sur le calcul est seulement la publicité de la recherche. La recherche
elle-même, c'est l'environnement logiciel complet et l'ensemble des instructions qui ont produit
les figures [@buckheit1995wavelab]. Puis elle montre, figure après figure, ce qui manque à son propre
domaine pour mériter la confiance. Les figures viennent pour la plupart d'un article de son
équipe, signé Peter Henderson et ses coauteurs [@henderson2018matters].

**Ce que nous faisons de cette conférence.** Huit ans ont passé. Le domaine a changé de taille et
de terrain. NeurIPS a adopté en 2019 la liste de contrôle que Pineau proposait
[@pineau2021improving]. D'autres congrès ont suivi avec leurs propres listes. Nous voulons savoir ce qu'elle a changé dans les articles eux-mêmes. Nous
prenons donc sa liste de failles comme une grille, nous l'appliquons aux articles d'aujourd'hui,
puis à nos propres expériences. C'était la règle qu'elle demandait : la critique s'applique
d'abord à soi.

# Ce qu'il faut savoir pour suivre

Ce document s'adresse à qui n'a jamais entraîné d'agent. Six notions suffisent.

**L'apprentissage par renforcement.** Un programme, l'agent, agit dans un monde, l'environnement.
À chaque pas, il observe une situation, choisit une action, reçoit une récompense chiffrée. Il
cherche la façon d'agir, appelée politique, qui rapporte le plus de récompense au total. Notre
exemple fil rouge s'appelle HalfCheetah : un guépard articulé, dessiné en deux dimensions dans un
simulateur de physique. L'agent commande ses six articulations. Il reçoit une récompense quand le
guépard avance. Au début il gigote, au bout d'un million de pas il court. On parle
d'apprentissage par renforcement profond (*deep reinforcement learning*, abrégé RL dans la suite)
quand la politique est un réseau de neurones.

**La graine aléatoire.** L'entraînement tire beaucoup de nombres au hasard : les poids de départ
du réseau, les actions d'exploration, la position initiale du guépard. Un ordinateur fabrique ce
hasard à partir d'un nombre de départ, la graine aléatoire (*random seed*). Même programme, même
graine aléatoire : même résultat. Même programme, autre graine aléatoire : autre résultat. Un
« essai » désigne dans ce document un entraînement complet avec une graine aléatoire donnée.

**L'hyperparamètre.** Le réseau apprend ses poids tout seul. D'autres réglages restent à la main
de l'expérimentateur : la vitesse d'apprentissage, la taille du réseau, le nombre d'exemples traités
à la fois. Ce sont les hyperparamètres. Le résultat en dépend beaucoup.

**La référence.** Pour montrer qu'une méthode nouvelle fait mieux, un article la compare à des
méthodes existantes, appelées références (*baselines*). La comparaison est loyale quand toutes ont
reçu le même soin de réglage.

**Le banc d'essai.** Un banc d'essai (*benchmark*) est un ensemble de tâches standard sur lesquelles
tout le monde se compare. Pour le RL de 2018, les guépards, sauteurs et marcheurs du simulateur
MuJoCo [@todorov2012mujoco] servaient de banc d'essai. Pour les modèles de langue de 2026, ce sont
des recueils de problèmes de mathématiques corrigés.

**Le test statistique et l'intervalle de confiance.** Deux moyennes diffèrent toujours un peu. Un
test statistique chiffre la probabilité d'observer un écart au moins aussi grand si les deux
méthodes étaient en vérité équivalentes : c'est la valeur p. Par convention, p < 0,05 fait déclarer
l'écart « significatif ». Un intervalle de confiance à 95 % donne une plage de valeurs compatibles
avec les données : plus il est large, moins la mesure est sûre. Nous employons l'intervalle de
Wilson, adapté aux proportions calculées sur peu d'articles [@wilson1927probable].

# Du backgammon aux modèles de langue

**Vingt ans avec un seul exemple.** En 1995, Gerald Tesauro, chercheur chez IBM, décrit TD-Gammon :
un réseau de neurones qui apprend le backgammon en jouant contre lui-même. Sa version 2.1 atteint
un niveau de maître « extrêmement proche » de celui des meilleurs joueurs humains
[@tesauro1995tdgammon]. À Vancouver, Pineau raconte que les chercheurs du RL ont cité ce résultat
pendant près de vingt ans comme le plus remarquable de leur domaine. AlphaGo, vainqueur de Lee
Sedol au go en 2016, leur a enfin donné un autre exemple [@silver2016alphago; @pineau2018iclr].

**Un domaine qui a grandi très vite.** Pineau commence à travailler sur le RL vers 1999. Vers
2000, à un atelier sur le RL du congrès NIPS (le nom de NeurIPS jusqu'en 2018), trente-cinq
personnes occupent la salle. En 2016, elle compte environ treize mille articles de RL publiés dans
l'année. Avec un tel volume, note-t-elle, un nouveau venu peine à savoir lesquels font vraiment
avancer le domaine [@pineau2018iclr].

**Des erreurs qui commencent à coûter.** À la fin de sa conférence de Vancouver, Pineau dit
pourquoi ces questions lui importent tant. Longtemps, le RL a joué au backgammon et à rien
d'autre, si bien que ses imprécisions ne coûtaient rien. Il s'approche maintenant, dit-elle, de
problèmes qui comptent : la conception de traitements médicaux, la gestion des ressources
naturelles, des réseaux d'énergie et des systèmes financiers [@pineau2018iclr]. Le doute venait
aussi des praticiens. En février 2018, Alex Irpan, de l'équipe de recherche Google Brain, écrit
sur son blog : « Quand quelqu'un me demande si l'apprentissage par renforcement peut résoudre son
problème, je lui réponds que non. Je pense avoir raison au moins 70 % du temps. » Pineau projette
l'adresse de ce billet à NeurIPS [@irpan2018rlhard; @pineau2018neurips].

**Le RL apprend à converser.** En 2022, OpenAI décrit InstructGPT, un modèle de langue affiné en
deux temps. Des annotateurs écrivent d'abord des exemples de bonnes réponses, que le modèle apprend
à imiter. Ils classent ensuite plusieurs réponses du modèle, de la meilleure à la pire. Un
apprentissage par renforcement à partir de ces retours humains (RLHF, *reinforcement learning from
human feedback*) fait le reste. Les évaluateurs préfèrent les réponses de la version
d'InstructGPT à 1,3 milliard de paramètres à celles de GPT-3, qui en compte 175 milliards, cent
fois plus [@ouyang2022instructgpt]. Le 30 novembre 2022, OpenAI présente ChatGPT, entraîné « avec
les mêmes méthodes qu'InstructGPT » [@openai2022chatgpt].

**Une récompense qu'un programme vérifie.** L'entreprise chinoise DeepSeek publie dans *Nature*,
en septembre 2025, le modèle R1. Sa première version, R1-Zero, apprend à raisonner par RL seul,
sans exemples de raisonnement écrits par des humains. La récompense se calcule par des règles. Pour
un problème de mathématiques, un programme compare la réponse finale à la bonne réponse. Pour un
problème de programmation, un compilateur fait tourner le code sur des tests fixés d'avance. Sur
l'AIME 2024 (*American Invitational Mathematics Examination*, un concours de mathématiques
américain), la part de problèmes résolus au premier essai passe de 15,6 % à 77,9 % au fil de
l'entraînement [@deepseek2025r1]. Les annexes de l'article chiffrent le calcul : 147 000 heures de
processeur graphique, soit 294 000 dollars au tarif de location de 2 dollars l'heure. Ce compte
couvre R1-Zero, la préparation des données et R1. Il exclut l'entraînement du modèle de départ,
DeepSeek-V3. En mars 2025, l'Association for Computing Machinery (ACM), société savante
d'informatique, remet son prix Turing à Andrew Barto et Richard Sutton pour avoir posé « les
fondations conceptuelles et algorithmiques » du RL [@acm2025turing].

**Ce que ces succès ont en commun.** Chacun dispose d'un monde qu'on relance sans frais : un
plateau de jeu, une liste de problèmes corrigés, des tests de programmation. Chacun reçoit aussi
une récompense qu'un programme calcule sans se tromper. Les auteurs de DeepSeek-R1 le disent
eux-mêmes : le succès du RL pur dépend d'une récompense fiable. Attribuée par un autre modèle au
lieu de règles fixées d'avance, la récompense se laisse plus facilement exploiter [@deepseek2025r1]. Même
dans ces conditions, le signal reste pauvre. Andrej Karpathy, qui a participé aux débuts d'OpenAI,
le résume en octobre 2025 : « L'apprentissage par renforcement est terrible. Il se trouve
simplement que tout ce que nous avions avant est bien pire. » Le modèle travaille parfois une
minute entière pour recevoir une seule note à la fin, appliquée ensuite à chacune de ses actions,
les bonnes comme les mauvaises : « on aspire la supervision à travers une paille »
[@patel2025karpathy]. Un apprentissage aussi bruité donne des scores qui changent d'une graine
aléatoire à l'autre. Pour séparer un progrès du hasard, il faut alors lancer chaque expérience
plusieurs fois, avec des références réglées aussi bien que la méthode. Les seize failles de 2018
décrivent ce qui arrive quand ce calcul manque.

# Les seize failles de 2018

Pineau ne se contente pas d'un reproche général. Elle montre chaque faille par un exemple, souvent
par une figure. Nous les avons relevées dans l'ordre de ses deux conférences, puis rangées en quatre
familles. Pour chacune, ce document dit ce qu'elle est, pourquoi elle fausse un résultat et ce que
Pineau en montrait. Le numéro F1 à F16 sert seulement à retrouver la faille dans les tableaux.

## Le matériel : ce qu'il faut pour refaire

**L'article publié sans son code (F1).** Un article de RL décrit sa méthode en quelques pages
d'équations et de prose. Le programme qui a produit les résultats compte des milliers de lignes,
pleines de choix que la prose ne mentionne pas. Sans ce programme, une autre équipe réécrit tout et
retombe rarement sur les mêmes chiffres. Elle ignore alors si l'écart vient de la méthode ou de sa
propre réécriture. Pineau reprend la formule de Buckheit et Donoho : l'article seul est la
publicité, le code et les instructions qui produisent les figures sont le produit. Sur les 50 articles de RL de 2018 qu'elle a
lus, 55 % donnent un lien vers leur code.

**Aucun plan pour refaire l'expérience (F2).** Donner le code ne suffit pas toujours. Il faut aussi
les réglages exacts et une idée du calcul nécessaire, sans quoi personne ne sait si l'expérience est
à sa portée. L'exemple de Pineau est AlphaGo, le programme de DeepMind qui a battu en 2016 le
champion de go Lee Sedol. L'article de *Nature* est très détaillé, elle le reconnaît, avec une
longue annexe. Sa diapositive pose pourtant la question : cela suffit-il ? Il faudrait aussi les
données, les parties d'experts, le code, les hyperparamètres, les ordinateurs et le protocole
d'évaluation. À l'oral, elle explique que les parties d'experts, le code, la recherche des
réglages et le calcul restent hors de portée des autres équipes. Une découverte qu'aucun
laboratoire extérieur n'a les moyens de refaire reste une affirmation.

**Le matériel et les logiciels, qui font partie du résultat (F3).** Le même code, lancé sur deux
machines, donne parfois deux résultats. Les cartes graphiques n'arrondissent pas les calculs de la
même façon que les processeurs. Une nouvelle version d'une bibliothèque change un réglage par
défaut. À NeurIPS, Pineau montre donc des processeurs, des cartes graphiques et une salle de
serveurs, puis inscrit deux points dans sa liste de contrôle : l'article déclare « l'infrastructure
de calcul employée » et donne son code « avec toutes ses dépendances ».

## Le réglage : hyperparamètres et références

**Les hyperparamètres de la méthode, donnés en partie (F4).** Un agent de RL dépend de dizaines de
réglages : la vitesse d'apprentissage, la taille du réseau, la longueur des épisodes, le facteur qui
pèse les récompenses futures. Un seul réglage oublié dans l'article suffit à empêcher la
reproduction : le lecteur prend la valeur par défaut de sa bibliothèque et obtient autre chose.
Pineau compte que 90 % des articles de 2018 donnent tous ceux de leur méthode.

**La façon de choisir les hyperparamètres, tue (F5).** Donner la valeur finale ne dit pas comment
on l'a trouvée. Une équipe qui a essayé cent combinaisons et gardé la meilleure n'a pas fait la
même expérience qu'une équipe qui a pris les valeurs d'un article précédent. La première a
optimisé sur son banc d'essai : son score en profite. Le lecteur a besoin du budget de
recherche dépensé pour obtenir ce chiffre : une grille de valeurs, une recherche au hasard, combien
d'essais. Seuls 20 % des articles de 2018 le disent.

**Des réglages qui changent tout et qui interagissent (F6).** Henderson et ses coauteurs changent un
seul réglage à la fois et regardent le score bouger. La taille du réseau, la fonction d'activation
(la petite formule appliquée par chaque neurone), l'échelle de la récompense avec ou sans
normalisation des couches du réseau : chaque changement déplace le résultat. Pour PPO sur
HalfCheetah, passer d'un réseau de deux couches de 64 neurones à un réseau de 400 puis 300
neurones fait tomber le score de 2 201 à −1 180. Pire, les
réglages interagissent. Le meilleur réseau pour un algorithme cesse de l'être pour un autre. Une
comparaison entre deux méthodes dépend alors des réglages choisis pour chacune.

**Des références moins bien réglées que la méthode (F7).** Cette faille découle des deux
précédentes. L'auteur d'une méthode nouvelle la règle avec soin, parce qu'il veut qu'elle marche.
Il prend souvent la référence telle quelle, avec ses valeurs par défaut. La comparaison oppose alors
une méthode réglée à une méthode qui ne l'est pas. La nouvelle gagne d'avance. Pineau compte que
60 % des articles de 2018 donnent les hyperparamètres de leurs références.

## Les graines aléatoires et la statistique

**Une mesure de performance jamais définie (F8).** « Comment mesurer la performance de la politique
apprise ? » demande Pineau. Plusieurs réponses existent. Le score à la fin de l'entraînement
récompense la méthode qui finit haut. La moyenne sur tout l'entraînement récompense celle qui
apprend vite. Le meilleur score atteint en cours de route récompense celle qui a un pic chanceux.
Ces mesures ne classent pas toujours les méthodes dans le même ordre. Un article qui ne dit pas
laquelle il emploie, ni ce que représentent ses barres d'erreur, ne se compare à aucun autre.

**Trop peu d'essais (F9).** D'une graine aléatoire à l'autre, le même programme donne des scores
très différents, nous le verrons plus loin. Avec trois essais, une moyenne dépend beaucoup du hasard
d'un seul essai. Pineau montre pourtant un tableau d'articles de 2015 à 2017 : ils lancent trois ou
cinq graines aléatoires. Aucun n'atteint dix.

**Les meilleurs essais sur N, seuls publiés (F10).** Une équipe lance dix essais, garde les cinq
meilleurs et publie leur moyenne. Chaque chiffre est vrai, mais celui qu'on publie dépasse ce que la
méthode donne en moyenne. Pineau l'illustre par un exemple construit pour l'occasion : dix courbes,
dont on ne garde que les trois meilleures. La moyenne monte. La dispersion paraît bien plus
petite qu'elle n'est. Henderson et ses coauteurs signalent que des articles publiés procèdent
ainsi.

**Même code, autre graine aléatoire : deux « algorithmes » (F11).** C'est la figure la plus célèbre
des deux conférences. Henderson et ses coauteurs entraînent dix fois le même programme sur
HalfCheetah, en changeant seulement la graine aléatoire. Ils répartissent les dix essais en deux
groupes de cinq et tracent les deux courbes moyennes : elles sont nettement séparées. Un test
statistique les déclare différentes (t = −9,09, p = 0,0016). Pineau précise sur scène que les
deux groupes ne sont pas triés : ce sont « juste cinq essais » de chaque côté. Un lecteur y verrait deux algorithmes,
l'un meilleur que l'autre. Il s'agit d'un seul programme. Le hasard seul suffit donc à fabriquer
une « amélioration » publiable.

**Aucun test statistique (F12).** Quand deux méthodes diffèrent de quelques points, la question est
de savoir si l'écart dépasse ce que le hasard des graines aléatoires produit tout seul. Un test
statistique ou un intervalle de confiance y répond. Sans eux, le lecteur juge à l'œil. La faille
précédente montre ce que vaut l'œil. Seuls 5 % des articles de 2018 appliquent un test à leurs
comparaisons.

## La portée des conclusions

**Le meilleur algorithme qui change avec la tâche (F13).** Henderson et ses coauteurs classent
quatre algorithmes sur quatre tâches du simulateur MuJoCo. L'algorithme en tête sur le guépard
cesse de l'être sur le sauteur ou sur le nageur. Un article qui conclut « notre méthode est
meilleure » à partir d'une ou deux tâches tire une conclusion générale d'un cas particulier. Pour
que la conclusion tienne, il faut plusieurs tâches et l'aveu de celles où la méthode perd.

**Deux implémentations du même algorithme qui divergent (F14).** TRPO, un algorithme de 2015, existe
en plusieurs versions écrites par des équipes différentes. Henderson et ses coauteurs en comparent
trois sur HalfCheetah, avec le même réseau : elles finissent à 1 939, 834 et 205. Des choix de code
que l'article d'origine ne détaille pas, comme l'optimiseur de la fonction de valeur, font une
part du score. Un article qui compare sa méthode à « TRPO » sans dire quelle implémentation il a prise
compare en fait sa méthode à un programme anonyme.

**L'évaluation sur les conditions d'entraînement (F15).** En apprentissage automatique classique, on
évalue un modèle sur des données qu'il n'a jamais vues, parce que c'est la seule façon de savoir
s'il a appris une règle générale ou seulement retenu des exemples. Un élève qui a vu le sujet de
l'examen la veille réussit sans avoir rien compris. En RL, l'agent s'évalue souvent dans le monde
même où il s'est entraîné, avec les mêmes graines aléatoires. Pineau projette une phrase qu'elle met
en débat : « le RL est le seul cas de l'apprentissage automatique où il est acceptable de tester sur
son ensemble d'entraînement ». Puis elle propose une feuille de route : séparer les graines
aléatoires d'entraînement et de test, séparer les tâches, ajouter des fonds d'image naturels,
passer à des simulateurs photoréalistes [@zhang2018dissection; @zhang2018natural]. Seuls 10 % des
articles de 2018 évaluent sur des conditions tenues à part.

**Des bancs d'essai trop simples, faciles à apprendre par cœur (F16).** Pineau juge « ridiculement
simples » beaucoup de bancs d'essai du RL : des situations décrites par peu de nombres (MuJoCo),
peu d'actions possibles (les jeux Atari), peu de situations de départ, des transitions et des
récompenses déterministes, le tout pesant moins de 100 kilo-octets. Un agent assez gros y retient la bonne suite
d'actions sans rien comprendre du monde, comme un élève récite une table sans savoir multiplier
[@machado2018revisiting]. Un succès sur ces bancs d'essai dit alors peu de chose de la méthode.

**L'inventaire.** Le tableau ci-dessous range les seize failles avec leur source dans les
diapositives et l'instrument qui la mesure dans ce document. Les instruments sont décrits à la
section suivante.

| | La faille montrée en 2018 | Où Pineau la montre | Ce qui la mesure ici | Où nous en sommes le 9 novembre 2026 |
|:----|:-----------------------------------------|:----------------|:----------------|:----------------------|
| F1 | L'article publié sans son code | diapositive 6 à ICLR, page 29 à NeurIPS | critère Q5 | écoutée en partie |
| F2 | Aucun plan pour refaire l'expérience, comme pour AlphaGo | diapositives 9 à 12 à ICLR | critères Q3 et X7 | écoutée en partie |
| F3 | Le matériel et les logiciels, qui font partie du résultat | pages 34 et 35 à NeurIPS | critères X7 et Y10 | écoutée en partie, reste à mesurer |
| F4 | Les hyperparamètres de la méthode, donnés en partie | page 29 à NeurIPS | critère Q3 | impossible à trancher |
| F5 | La façon de choisir les hyperparamètres, tue | page 29 à NeurIPS | critère Q6 | pas écoutée |
| F6 | Des réglages qui changent tout et qui interagissent | diapositives 24 et 25 à ICLR | critère Y9 | reste à mesurer |
| F7 | Des références moins bien réglées que la méthode | diapositive 25 à ICLR, page 29 à NeurIPS | critères Q4 et X4, expérience E6 | en recul net contre les chiffres de Pineau |
| F8 | Une mesure de performance jamais définie | diapositives 26 et 27 à ICLR | critères Y1 et Y2 | reste à mesurer |
| F9 | Trop peu d'essais, trois ou cinq, jamais dix dans son tableau | diapositive 28 à ICLR | critère X1, expérience E5 | pas écoutée |
| F10 | Les meilleurs essais sur N, seuls publiés | diapositives 29 et 30 à ICLR | critère X3, expériences E1 et E4 | devenue rare, effet mesuré |
| F11 | Même code, autre graine aléatoire : deux « algorithmes » | diapositive 31 à ICLR, page 22 à NeurIPS | expérience E1 | nuancée par nos mesures |
| F12 | Aucun test statistique | page 29 à NeurIPS | critères Q8 et X2 | pas écoutée |
| F13 | Le meilleur algorithme qui change avec la tâche | diapositives 20 et 21 à ICLR | expérience E2, critères Y3 et Y4 | mesure en cours |
| F14 | Deux implémentations du même algorithme qui divergent | diapositives 22 et 23 à ICLR | expérience E3, critère Y5 | mesure en cours |
| F15 | L'évaluation sur les conditions d'entraînement | pages 36 à 51 à NeurIPS | critère Q7, expérience E7, critère Y8 | en hausse par changement de population, aucun changement détectable dans le RL classique |
| F16 | Des bancs d'essai trop simples, faciles à apprendre par cœur | pages 43 à 50 à NeurIPS | critères X6 et Y7 | reste à mesurer |

: Les seize failles de 2018. Pour chacune : la diapositive de la conférence d'ICLR ou la page du document de NeurIPS qui la montre, le critère de lecture ou l'expérience qui la mesure dans ce document, puis le verdict à la date du 9 novembre 2026.

# Comment nous mesurons

## Le sondage : relire les articles avec la grille de Pineau

**La grille.** Pour chiffrer les failles de 2018, Pineau avait lu 50 articles de RL publiés cette
année-là et noté, pour chacun, huit critères : l'article a-t-il des expériences, emploie-t-il des
réseaux de neurones, donne-t-il tous les hyperparamètres de sa méthode, ceux de ses références,
le lien vers son code, la façon de choisir les hyperparamètres, une évaluation tenue à part, un test
statistique ? Nous appelons ces huit critères Q1 à Q8. Nous en ajoutons sept, notés X1 à X7, tirés
de sa conférence d'ICLR : le nombre d'essais, l'incertitude rapportée, la sélection des meilleurs
essais, le réglage loyal des références, la famille de l'article, le nombre de familles de modèles
essayées, le calcul rapporté.

**Les articles.** Nous avons pris tous les articles d'ICLR 2026, d'ICML 2026 et de NeurIPS 2025
dont le titre parle d'apprentissage par renforcement : 1 252 sur 17 836. Nous en avons tiré 50 au
sort. Parmi eux, 27 appliquent le RL à de grands modèles de langue, 14 relèvent du RL classique
(robotique, jeux, contrôle) et 9 sont théoriques, dont 5 sans aucune expérience. Les pourcentages
de ce document se calculent sur les articles qui ont des expériences.

**Qui lit les articles.** La lecture est confiée à des agents de modèle de langue : des
programmes qui lisent le PDF entier, annexes comprises, puis remplissent la grille. Pour qu'un agent
n'invente rien, chaque décision s'accompagne d'une citation exacte de l'article et de sa page, que
n'importe qui peut vérifier dans `study/codes/`. Dix articles tirés au sort ont été lus une seconde
fois par un autre agent, qui ne voyait pas la première lecture. Les deux lectures s'accordent sur
127 décisions sur 130 (98 %). Le kappa de Cohen, qui retire de cet accord la part due au hasard,
vaut de 0,74 à 1 selon le critère. Un accord entre deux machines reste un accord entre machines :
une relecture humaine à l'aveugle de dix articles est prévue. Ce document le signale tant
qu'elle manque.

**Vérifier notre lecture.** Le tirage de Pineau et sa façon de trancher les cas douteux restent
inconnus. Pour savoir si notre lecture ressemble à la sienne, nous avons aussi lu 12 articles de
2018, avec la même grille et les mêmes agents. Sur les hyperparamètres de la méthode, nous sommes
plus sévères qu'elle (6 sur 10 contre 90 %). Sur l'évaluation tenue à part, plus indulgents
(4 sur 11 contre 10 %).

**Comparer deux échantillons.** Les 50 articles de Pineau forment eux aussi un échantillon. Avec
un autre tirage, son 55 % de code en lien serait sorti entre 41 % et 68 %. Traiter son chiffre
comme exact gonflerait la sûreté de nos verdicts. Nous calculons donc l'écart entre les deux
années avec son propre intervalle de confiance (l'intervalle de Newcombe) puis un test exact de
Fisher. Quand on teste neuf critères à la fois, l'un d'eux finit par franchir le seuil par hasard :
la correction de Holm relève le seuil en conséquence. Enfin, 2018 ne comptait aucun article sur
les grands modèles de langue. Pour séparer un changement de pratique d'un changement de
population, nous comparons aussi le seul RL classique de 2026 à notre lecture de 2018. Un critère
« a changé » quand l'écart tient contre les chiffres de Pineau après correction. Le changement est
« confirmé » quand il tient aussi contre notre propre lecture de 2018. Le script
`study/audit_stats.py` fait tous ces calculs.

**Une seconde grille, préparée.** Les quinze critères ne couvrent pas toutes les failles. Une
seconde grille de douze critères (Y1 à Y12) les complète : mesure définie, barres d'erreur définies,
nombre de tâches, tâches où la méthode perd, implémentation des références, essais exclus,
versions des bancs d'essai, test de généralisation, sensibilité aux réglages, dépendances
logicielles, type d'incertitude, outils statistiques récents. Elle est écrite et datée du
9 novembre 2026 dans `study/PROTOCOL.md` avant toute lecture. Sa lecture n'a pas commencé.

## Les expériences : refaire 2018 avec les outils de 2026

**Un protocole écrit d'avance.** Le protocole des expériences (`sim/SIM_PROTOCOL.md`) date du
8 novembre 2026, avant le premier entraînement. Il fixe les algorithmes, les tâches, le nombre de
graines aléatoires et les analyses. Tout changement ultérieur s'inscrit dans une liste d'« écarts »,
avec la mention de ce que nous avions déjà vu au moment de le décider. Aucun essai n'est retiré.

**Les outils.** Les tâches de Henderson et ses coauteurs, dans leur version de 2026 : HalfCheetah,
Hopper (un sauteur à une jambe), Walker2d (un marcheur à deux jambes) et Swimmer (un nageur), dans
le simulateur MuJoCo et la bibliothèque Gymnasium 1.1.1 [@towers2024gymnasium]. Quatre algorithmes :
PPO (*Proximal Policy Optimization*) [@schulman2017ppo], écrit dans deux bibliothèques,
Stable-Baselines3 en PyTorch [@raffin2021sb3] et sa réécriture en JAX, puis SAC (*Soft Actor-Critic*)
[@haarnoja2018sac] et CrossQ, un descendant de SAC paru en 2024 [@bhatt2024crossq]. Dix graines
aléatoires par couple d'algorithme et de tâche, trente pour l'expérience E1. L'évaluation se fait
sur des graines aléatoires jamais vues à l'entraînement, puis sur une physique modifiée (masses
multipliées par 1,2, frottement par 0,8).

**Sept expériences.** E1 entraîne trente fois PPO sur HalfCheetah, pour étudier la dispersion due
aux graines aléatoires. E2 classe les quatre algorithmes sur les quatre tâches. E3 compare les deux
implémentations de PPO. E4 mesure l'effet de garder les trois meilleurs essais sur dix. E5 chiffre
le nombre de graines aléatoires nécessaire pour retrouver le bon classement. E6 compare une référence
réglée à une référence laissée à ses valeurs par défaut. E7 mesure ce que coûte la physique modifiée.

**Le volet des grands modèles de langue.** Le RL sert aujourd'hui surtout à affiner des modèles de
langue. On leur pose un problème de mathématiques, on vérifie la réponse et on récompense les
bonnes. Nous employons GRPO (*Group Relative Policy Optimization*,
optimisation de politique relative à un groupe), l'un des plus répandus [@shao2024deepseekmath]. Nous l'avons écrit
nous-mêmes, sur deux petits modèles ouverts, Qwen2.5 de 0,5 milliard de paramètres
[@qwen2025qwen25] et Llama 3.2 de 1 milliard [@meta2024llama32; @grattafiori2024llama3]. Chaque modèle s'entraîne deux
fois : avec la vraie récompense, puis avec une récompense tirée à pile ou face. Le protocole
(`sim/llm/LLM_PROTOCOL.md`) annonce d'avance cette petite échelle.

# Le matériel : code, réglages, calcul (F1 à F3)

![La grille de Pineau, appliquée en 2018 et en 2026. Chaque ligne est un critère de lecture. Le point de 2018 donne la part des 50 articles lus par Pineau qui satisfont le critère. Le point de 2026 donne la part dans nos 45 articles expérimentaux tirés d'ICLR 2026, d'ICML 2026 et de NeurIPS 2025. Le test statistique, absent du dessin, passe de 5 % à 4 %.](figures/remesure-dumbbell.svg){width=100%}

| Critère de lecture | Faille visée | Pineau, 2018 | Notre lecture de 12 articles de 2018 | Nos 45 articles de 2026, avec intervalle à 95 % |
|:------------------------------------|:----|--------:|----------:|-------------:|
| Q5, le code est en lien | F1 | 55 % | 6 sur 11 | 67 % [52, 79] |
| Q3, tous les hyperparamètres de la méthode sont donnés | F2, F4 | 90 % | 6 sur 10 | 67 % [52, 79] |
| X7, le calcul employé est chiffré | F2, F3 | non mesuré | 3 sur 11 | 47 % [33, 61] |
| Q6, la façon de choisir les hyperparamètres est décrite | F5 | 20 % | 2 sur 10 | 27 % [16, 41] |
| Q4, tous les hyperparamètres des références sont donnés | F7 | 60 % | 6 sur 11 | **18 % [10, 32]** |
| X4, les références sont réglées avec le même soin | F7 | non mesuré | 1 sur 11 | 5 % [1, 15] |
| X2, une incertitude est rapportée | F12 | non mesuré | 8 sur 11 | 47 % [33, 61] |
| Q8, un test statistique est appliqué | F12 | 5 % | 1 sur 11 | 4 % [1, 15] |
| Q7, l'évaluation se fait sur des conditions tenues à part | F15 | 10 % | 4 sur 11 | **70 % [56, 82]** |

: La grille de Pineau réappliquée, critère par critère. En gras, les deux écarts avec ses chiffres qui passent la correction de Holm et que notre grille n'explique pas. Le recul des hyperparamètres de la méthode la passe aussi, mais notre lecture de 2018 montre qu'il vient de notre grille, plus sévère que la sienne. « Non mesuré » : Pineau n'avait pas ce critère. Données : `study/results_final.json` et `study/audit_stats.json`.

**Les écarts, avec leur incertitude.** La figure suivante donne, pour chaque critère, l'écart
entre 2026 et les chiffres de Pineau avec son intervalle. Un intervalle qui ne croise pas la ligne
zéro signale un changement. Trois intervalles s'écartent nettement de zéro : les hyperparamètres
de la méthode, ceux des références et l'évaluation tenue à part.

![Écart entre la part des articles de 2026 et celle des 50 articles de 2018 lus par Pineau, critère par critère, en points de pourcentage. Le point est l'écart observé, la barre son intervalle de Newcombe à 95 %, qui tient compte de l'incertitude des deux échantillons. Au-dessus de zéro, la pratique est plus fréquente en 2026.](figures/ecarts-pineau.svg){width=100%}

**Le RL classique, comparé à lui-même.** La seconde figure retire les articles sur les grands
modèles de langue et compare les 14 articles de RL classique de 2026 à notre propre lecture de
2018. Un seul intervalle reste entièrement sous zéro, de justesse : celui des hyperparamètres des
références, de −67 à −3 points. Il ne passe pas la correction de Holm. Avec si peu d'articles de chaque côté, l'absence de changement
détectable ne prouve pas l'absence de changement. Elle interdit en tout cas d'annoncer un
progrès du RL classique.

![Écart entre les 14 articles de RL classique de 2026 et nos 12 articles de 2018, lus avec la même grille et les mêmes agents, en points de pourcentage. Le point est l'écart observé, la barre son intervalle de Newcombe à 95 %. Les intervalles sont larges parce que les deux échantillons sont petits.](figures/ecarts-classique.svg){width=100%}

**Le code, plus souvent en lien (F1).** En 2026, 67 % des articles donnent le lien vers leur code,
contre 55 % chez Pineau. L'intervalle [52, 79] ne permet pas de conclure sur notre seul
échantillon. Le bilan officiel du programme de reproductibilité de NeurIPS 2019 va dans le même
sens : la part d'articles acceptés avec du code passe de moins de 50 % à 74,4 %
[@pineau2021improving]. La faille est donc écoutée en partie. Un article sur trois reste une
publicité sans le produit.

**Le plan pour refaire, à moitié livré (F2).** Les hyperparamètres de la méthode sont tous donnés
dans 67 % des articles de 2026 et le calcul est chiffré dans 47 %. La baisse apparente des
hyperparamètres, de 90 % à 67 %, disparaît contre notre propre lecture de 2018 (6 sur 10). Notre
grille est simplement plus sévère que celle de Pineau. Le verdict reste impossible à trancher.

**L'infrastructure, chiffrée une fois sur deux (F3).** Moins d'un article sur deux chiffre son
calcul en 2026, alors que le RL de grands modèles a fait du calcul un poste de budget à part entière
[@khatri2025art]. Une seule étude de 2025 sur la croissance du RL de ces modèles a consommé plus de
400 000 heures de processeur graphique. Les versions des logiciels (critère Y10) attendent la seconde grille.

# Le réglage : hyperparamètres et références (F4 à F7)

**La façon de régler, toujours tue (F4 et F5).** La façon de choisir les hyperparamètres est décrite
dans 27 % des articles de 2026, contre 20 % en 2018. Nous ne détectons aucun changement : l'écart vaut
+7 points, avec un intervalle de −10 à +23.

**Les réglages qui changent tout (F6).** La littérature a confirmé à grande échelle l'observation
de Henderson et ses coauteurs. En 2020, une équipe du MIT et de Two Sigma montre que des
optimisations présentes seulement dans le code, ou décrites comme des détails, expliquent
l'essentiel de l'avantage de PPO sur TRPO [@engstrom2020implementation]. En 2021, une équipe de
Google entraîne plus de 250 000 agents pour mesurer l'effet de plus de cinquante choix
[@andrychowicz2021matters]. Reste à savoir si les articles de 2026 montrent
leur propre sensibilité aux réglages : le critère Y9 le dira.

**Les références, de moins en moins décrites (F7).** Cette faille a nettement reculé. Les
hyperparamètres des références sont tous donnés dans 18 % des articles de 2026, contre 60 % chez
Pineau et 6 sur 11 dans notre lecture de 2018. Seuls 5 % des articles disent avoir réglé leurs
références avec le même soin que leur méthode. Notre échantillon ne dit pas d'où vient ce recul.

**Une référence qui s'effondre (E6).** Notre expérience E6 voulait illustrer la faille. Elle oppose
PPO sur Hopper avec les valeurs par défaut de la bibliothèque à PPO avec les réglages publiés par
le recueil RL Baselines3 Zoo [@raffin2020zoo], qui font foi pour cette bibliothèque. Premier
passage : la version par défaut atteint une moyenne interquartile de 2 877 [2 268, 3 365], la
version réglée 1 003 [852, 1 158]. La moyenne interquartile (*interquartile mean*, IQM) écarte le
quart le plus bas et le quart le plus haut des essais, puis fait la moyenne du reste
[@agarwal2021precipice]. Les réglages publiés feraient trois fois moins bien que les valeurs par
défaut ? Le résultat était trop beau. En vérifiant, nous avons trouvé une erreur de notre côté :
notre code normalisait les observations avec un facteur d'actualisation de 0,99, alors que le
recueil emploie celui de l'algorithme, 0,999. Nous avons relancé la recette corrigée, dix graines
aléatoires par condition, sur Hopper dans ses versions 4 et 5. Ce diagnostic a été décidé après
avoir vu le premier résultat, ce que le protocole déclare.

**L'erreur corrigée ne change rien.** La recette corrigée obtient 1 012 [902, 1 138] sur la
version 5 contre 984 [785, 1 003] sur la version 4, celle pour laquelle le recueil a été réglé. Les
valeurs par défaut obtiennent 2 423 [1 673, 3 067] sur la version 4. La probabilité qu'un essai
corrigé batte un essai avec l'erreur vaut 0,47, autant dire le hasard. Notre erreur
était réelle, sans expliquer l'écart. Deux possibilités demeurent : la recette publiée fait
vraiment moins bien que les valeurs par défaut avec les versions actuelles des bibliothèques, ou
notre façon de l'appliquer diffère encore de celle du recueil. Pour trancher, nous entraînons
dix agents avec le script officiel du recueil, puis nous les évaluons avec notre protocole. D'ici
là, E6 n'illustre aucune faille. Elle montre seulement pourquoi un résultat trop beau se vérifie
jusqu'au bout.

# Les graines aléatoires et la statistique (F8 à F12)

**La mesure, à définir (F8).** Le critère Y1 dira si les articles de 2026 définissent leur mesure
de performance, le critère Y2 s'ils disent ce que représentent leurs barres d'erreur. Le RL de
grands modèles offre déjà un exemple de mesure qui renverse un classement. En 2025, Yang Yue et ses
coauteurs, surtout de l'université Tsinghua, comparent des modèles avant et après un RL à
récompense vérifiable. Leur mesure, le pass@k, donne la part des problèmes résolus en au plus k
tentatives. Pour une seule tentative, le modèle entraîné l'emporte. Pour un grand nombre de
tentatives, le modèle de départ obtient le meilleur score. Les auteurs en concluent que les
raisonnements du modèle entraîné existaient déjà dans le modèle de départ. La distillation, qui
fait imiter un modèle plus fort, en apporte au contraire de nouveaux [@yue2025rlvr]. Un article
qui annonce un gain sans dire combien de tentatives il compte laisse le lecteur ignorer lequel des
deux modèles gagne.

**Toujours cinq essais (F9).** Sur 41 articles de RL expérimentaux de 2026, 20 ne disent pas
combien d'entraînements indépendants soutiennent leurs résultats. Quatre n'en ont qu'un. La
médiane des autres est cinq, la valeur la plus fréquente dans le tableau que Pineau montrait. La faille n'a pas été écoutée.
Le coût explique une part de cette économie. En 2021, Agarwal et ses coauteurs relèvent que trois à
dix essais par tâche restent la norme du RL profond : cinq essais sur plus de cinquante jeux Atari
demandent déjà plus de mille jours de calcul sur carte graphique. Sur Atari 100k, un banc d'essai
à petit budget de données, il faudrait plutôt de 50 à 100 essais pour estimer la médiane des
scores avec assez de précision [@agarwal2021precipice].
L'expérience E5 dira combien de graines aléatoires il faut vraiment.

## Même code, autre graine aléatoire (F11)

Nous avons refait l'expérience la plus célèbre de 2018 à plus grande échelle : trente
entraînements de PPO sur HalfCheetah, un million de pas chacun, avec le même code et les mêmes
hyperparamètres. Seule la graine aléatoire change.

![Trente entraînements du même programme sur la même tâche. Chaque point est un essai, placé à hauteur de son score d'évaluation final. Seule la graine aléatoire change d'un point à l'autre. Moyenne 1 688, écart type 568, médiane 1 580. Vingt-sept essais finissent entre 1 138 et 1 999. Trois décollent au-delà de 3 000.](figures/e1-seeds.svg){width=100%}

**Une dispersion qui ne ressemble pas à une cloche.** L'écart type vaut 34 % de la moyenne. La
distribution s'éloigne beaucoup de la courbe en cloche : un test de Shapiro-Wilk, qui mesure cet
éloignement, donne p = 4 × 10^−7^. Trois essais sur trente décollent loin au-dessus des autres.

**Combien de fois le hasard trompe-t-il le test ?** Nous avons ensuite tiré 10 000 fois deux groupes
parmi les trente essais, puis appliqué à chaque paire le test de Welch, la version du test t de
Student qui ne suppose pas les deux variances égales [@welch1947generalization]. Puisque les deux groupes sortent du même
programme, chaque écart déclaré significatif est un faux positif.

![Part des 10 000 tirages où le test de Welch déclare différents deux groupes d'essais du même programme, au seuil de 5 %. Quand les groupes sont tirés au hasard, le test se trompe moins souvent que ce seuil. Quand on trie dix essais et qu'on oppose les cinq meilleurs aux cinq pires, il se trompe près d'une fois sur trois.](figures/e1-false-positive.svg){width=90%}

| Façon de former les deux groupes | Part des tirages déclarés différents (p < 0,05) | Écart apparent entre les moyennes, en médiane | Écart apparent dépassé une fois sur vingt |
|:-----------------------------------|----------:|----------:|----------:|
| 3 essais contre 3, tirés au hasard | 1,6 % | 17 % | 62 % |
| 5 essais contre 5, tirés au hasard | 1,2 % | 17 % | 47 % |
| 10 essais contre 10, tirés au hasard | 1,7 % | 11 % | 33 % |
| Les 5 meilleurs contre les 5 pires, sur 10 essais | 31,0 % | 42 % | non calculé |

: Expérience E1, 10 000 tirages par ligne. L'écart apparent rapporte la différence des deux moyennes à la plus petite des deux. Données : `sim/analysis/e1.json`.

**Le hasard trompe l'œil, le tri trompe le test.** Deux groupes de cinq essais tirés au hasard ne
trompent presque jamais le test (1,2 %). Ils trompent l'œil : leurs moyennes diffèrent de 17 % en
médiane et de 47 % une fois sur vingt, de quoi dessiner deux courbes bien séparées. Le test se
trompe quand on trie : opposer les cinq meilleurs essais aux cinq pires donne 31 % de faux
positifs.

**La statistique de 2018, hors de portée de nos essais.** Henderson et ses coauteurs testaient autre
chose que les scores finaux. Leur légende parle d'un test t moyen sur toute la courbe
d'apprentissage. Leur figure concerne TRPO [@henderson2018matters]. Les groupes n'étaient pas triés,
précise Pineau. Nous avons donc refait leur statistique sur nos trente courbes de PPO : un test de
Welch à chacun des vingt points d'évaluation, puis la moyenne. Une fois sur vingt, la valeur absolue
du t moyen dépasse 1,4 quand les groupes sont tirés au hasard, 2,5 quand on les trie. Aucun de nos
20 000 tirages n'atteint 9. Cette analyse a été ajoutée après les premiers résultats de E1, ce que
le protocole déclare.

**Avec leur algorithme, toujours pas (B1).** Deux explications restaient ouvertes : TRPO disperse
plus que PPO, ou leur calcul différait du nôtre. Nous avons écrit le plan avant tout entraînement :
trente essais de TRPO, avec ses réglages par défaut, sur la même tâche, et trois lectures de leur
légende. TRPO disperse bien davantage : son écart type vaut 48 % de sa moyenne, contre 34 % pour
PPO. Pourtant, avec des groupes tirés au hasard, le t moyen ne dépasse 1,4 qu'une fois sur vingt,
comme pour PPO ; triés, 1,9. La troisième lecture empile les cent points des cinq courbes de chaque
groupe, comme s'ils étaient indépendants. Elle monte à 5,0 au hasard et à 6,3 triés. Aucun tirage,
dans aucune lecture, n'atteint 9. Cette lecture a un défaut plus grave : elle déclare une différence
dans 53 % des tirages au hasard, alors que les deux groupes font tourner le même code. Ni la
dispersion de TRPO ni ces façons de calculer n'expliquent donc leur chiffre. Notre TRPO de 2026
n'est toutefois pas le leur, et leur calcul exact reste inconnu.

Sur nos essais, le hasard des graines aléatoires trompe donc l'œil bien plus souvent que le test. La
faille reste entière pour qui compare deux courbes sans intervalle, ou traite les points d'une même
courbe comme des essais indépendants.

![Nos trente essais de PPO et nos trente essais de TRPO, comparés au chiffre publié en 2018. Pour chaque façon de répartir dix essais en deux groupes de cinq, au hasard ou triés par score final, la barre donne la valeur absolue du t moyen le long de la courbe d'apprentissage dépassée une fois sur vingt, sur 10 000 tirages. La barre des points empilés traite les cent points des courbes de chaque groupe comme des observations indépendantes, avec des groupes tirés au hasard. La barre de Henderson et ses coauteurs est la valeur qu'ils publient, sur leurs propres essais.](figures/e1-henderson.svg){width=85%}

**Les meilleurs sur N, devenus rares (F10).** Dans E1, garder les trois meilleurs essais sur dix
gonfle la moyenne de 33 % (2 249 contre 1 692). Dans les articles de 2026, la pratique est devenue
rare ou discrète : 2 articles sur 45 la laissent voir. L'expérience E4 dira combien de comparaisons
entre algorithmes elle inverse.

**La statistique, toujours absente (F12).** Le test statistique reste à 4 % des articles, contre
5 % en 2018. Une incertitude est rapportée dans 47 % des articles, mais cette moyenne mêle deux
mondes. Le RL classique la rapporte toujours (14 articles sur 14). Le RL de grands modèles presque
jamais (4 sur 27), alors qu'une équipe surtout basée à Tübingen y a mesuré, en 2025, des écarts types
de 5 à 15 points de pourcentage pour un même modèle évalué avec différentes graines aléatoires
d'échantillonnage, sur de petits bancs d'essai comme AIME 2024 [@hochlehnert2025sober]. Sur les
30 problèmes d'AIME 2024, une seule réponse juste de plus déplace le score de 3,3 points.
Réévaluées dans un cadre commun, la plupart des méthodes de RL de leur étude gagnent peu, « bien en
deçà » de ce que leurs articles annonçaient. Le RL classique a connu la même réanalyse. En 2021,
Agarwal et ses coauteurs recalculent des résultats publiés sur les jeux Atari avec des intervalles
de confiance. Plusieurs améliorations annoncées s'y fondent dans l'incertitude : un algorithme,
M-IQN, se disait meilleur qu'un autre, Rainbow, alors que leurs intervalles se chevauchent
nettement. Leur article a reçu le prix de l'article remarquable de NeurIPS 2021
[@agarwal2021precipice].

![Part des articles de 2026 qui satisfont chaque critère, avec son intervalle de confiance de Wilson à 95 %. Les barres verticales montrent la plage compatible avec nos 45 articles expérimentaux. Avec un échantillon de cette taille, un écart de moins de quinze points avec 2018 se confond avec le hasard du tirage.](figures/remesure-ic.svg){width=100%}

# La portée des conclusions (F13 à F16)

**Le classement et les implémentations (F13 et F14).** L'expérience E2 classe quatre algorithmes
sur quatre tâches. E3 compare PPO écrit en PyTorch et PPO écrit en JAX, avec les mêmes graines
aléatoires. Les deux attendent la fin des simulations. Les critères Y3 à Y5 diront si les articles
de 2026 testent plusieurs tâches, montrent celles où leur méthode perd et disent d'où vient le code
de leurs références.

**L'évaluation tenue à part, en hausse par changement de terrain (F15).** 70 % des articles de 2026
évaluent sur des conditions tenues à part, contre 10 % chez Pineau : un écart de 60 points, de 42
à 73 avec son intervalle. La hausse vient presque entière du RL de grands modèles : 26 articles sur
27. Leurs bancs d'essai, des recueils de problèmes de mathématiques, séparent par construction les
problèmes d'entraînement et les problèmes de test. Le RL classique reste à 5 articles sur 13,
contre 4 sur 11 dans notre lecture de 2018 : nous n'y détectons aucun changement. La faille a donc
reculé parce que le RL a changé de terrain, bien plus que parce que le RL classique a changé de
pratique. L'expérience E7 mesure, sur nos propres agents, ce que coûte une
physique modifiée.

**Les bancs d'essai trop simples, sous une autre forme (F16).** Le RL de grands modèles a changé
d'échelle sans changer de risque. Seize articles sur 27 n'essaient qu'une seule famille de modèles
de langue. Or une équipe de l'université de Washington a montré en 2025 qu'une récompense tirée au
sort améliore les modèles Qwen en mathématiques, mais pas les modèles Llama ou OLMo
[@shao2025spurious]. Sur le modèle Qwen2.5-Math-7B et le banc d'essai MATH-500, la vraie
récompense fait gagner 29,1 points de pourcentage. Une récompense qui félicite une réponse fausse
fixée d'avance en fait gagner 24,1, une récompense tirée au hasard 21,4. Les auteurs l'expliquent
par un comportement que l'entraînement amplifie sans le créer : le modèle écrit son raisonnement
sous forme de code, sans l'exécuter, dans 65 % des réponses avant l'entraînement et dans plus de
90 % après un entraînement à récompense trompeuse. Ils recommandent de valider une méthode de RL sur plusieurs familles de modèles. Un résultat obtenu sur une seule famille renseigne sur cette famille,
sans rien prouver de la méthode.

**Une limite de longueur qui fausse le gain.** Notre volet GRPO a fait apparaître un piège de banc
d'essai. Les réponses du modèle sont coupées à 160 jetons, les morceaux de mots qu'il produit un à
un. Avec le modèle de départ, 23 réponses sur 32 atteignent cette limite avant de donner un
résultat. Aucune de ces réponses coupées n'est juste. Avec la vraie récompense, le modèle
apprend d'abord à finir avant la coupure, ce que la récompense tirée au sort n'enseigne pas. Une
part du « gain » mesuré vient donc d'un détail du banc d'essai. Nous mesurons désormais la part
de réponses coupées à chaque évaluation.

![Les réponses du modèle Qwen2.5 de 0,5 milliard de paramètres, avant tout entraînement, sur les quatre problèmes de multiplication du dixième pas de notre essai pilote. Huit réponses tirées par problème. La plupart atteignent la limite de 160 jetons avant de donner un résultat et sont comptées fausses.](figures/grpo-truncation.svg){width=80%}

**Trois essais GRPO finis.** Sur les douze essais prévus, trois ont abouti, tous sur Qwen. Avec la
vraie récompense, la réussite au premier essai passe de 10 % et 12 % à 36 % et 61 % en cent pas.
Avec la récompense tirée au sort, elle tombe à 1 %. Les neuf autres essais ont échoué à la reprise
du 9 novembre 2026, pour des raisons de calcul consignées dans le protocole. Une seule graine
aléatoire par condition ne permet aucune conclusion.

# Les remèdes : liste de contrôle et défi de reproduction

**La liste de contrôle.** Pineau ne s'arrêtait pas au constat. Elle proposait une liste de contrôle
de reproductibilité (pages 31 à 33 à NeurIPS). Pour chaque algorithme : une description claire, une
analyse de complexité, le lien vers le code et ses dépendances. Pour chaque résultat théorique :
l'énoncé, les hypothèses, la preuve. Pour chaque figure : la collecte des données, la répartition
entre entraînement, validation et test, les données exclues, la plage et la méthode de choix des
hyperparamètres, le nombre exact d'essais, la définition des statistiques et des barres d'erreur,
le matériel employé.

**Le défi de reproduction.** Elle présentait aussi le défi de reproduction d'ICLR 2018
(diapositives 37 à 43 à ICLR) : n'importe qui pouvait tenter de refaire un article soumis. Le
défi est né dans son cours de McGill, où environ 180 étudiants de master et de doctorat avaient
besoin d'un projet de fin de semestre. D'après
la conférence, 124 équipes ou personnes se sont inscrites et 95 articles ont été choisis. Parmi les
participants qui ont répondu au sondage, 54,5 % en ont reproduit une partie, 32,7 % l'essentiel.
Sur 26 auteurs qui ont répondu, 61 % comptaient mettre à jour leur soumission. Pour 22 % des
participants, l'exercice a été très difficile. Enfin, 79 % des 28 auteurs interrogés voulaient
voir leur article de 2019 passer par le même examen.

**Ce que la liste a changé.** La liste de contrôle a gagné l'institution : NeurIPS l'impose depuis
2019 [@pineau2021improving]. Notre grille dit ce qu'elle a changé dans les articles. Le code un
peu, l'évaluation tenue à part beaucoup, la statistique pas du tout, la description des
références dans le mauvais sens. Une liste fait cocher des cases. Lancer dix graines aléatoires et
régler ses références coûte du calcul. Aucune case ne le paie.

**Sept questions pour lire une annonce de RL.** La liste de contrôle s'adresse aux auteurs. Le
lecteur d'un article, d'un communiqué ou d'une démonstration en tire sept questions, qui ne
demandent pas de savoir programmer. Chacune renvoie aux failles qu'elle détecte.

- Combien de graines aléatoires ? Avec moins de cinq essais, ou avec « les meilleurs essais », le
  résultat dit peu de chose (F9 et F10).
- Quelle incertitude ? Une moyenne sans intervalle de confiance ni bande autour de la courbe ne
  permet pas de juger un écart (F11 et F12).
- Quelle référence, réglée comment ? Si la méthode a reçu un mois de réglages et la référence ses
  valeurs par défaut, l'écart mesure le mois de réglages (F7).
- Combien de tâches, combien de familles de modèles ? Un résultat obtenu sur une seule tâche avec
  un seul modèle de départ vaut pour ce couple-là (F13 et F16).
- Évalué où ? Un agent jugé sur les situations de son entraînement a pu les apprendre par cœur
  (F15).
- Quel code ? Sans code publié, le lecteur ignore ce que l'article a vraiment fait (F1 et F14).
- Quel calcul ? Un résultat dont personne d'autre ne peut payer le calcul ne se reproduit pas
  (F2 et F3).

# Travaux voisins

**Personne n'a refait cette mesure.** Nous avons cherché le 9 novembre 2026 sur arXiv, OpenReview
et dans les actes des congrès. À notre connaissance, aucun travail ne réapplique la grille de Pineau
à des articles de RL récents en la calibrant sur 2018. Aucun ne refait le protocole de Henderson et
ses coauteurs avec les algorithmes de 2026 sous un protocole écrit d'avance. Les pièces voisines
existent : elles situent notre apport.

**Les audits de la littérature.** En 2018, Gundersen et Kjensmo notent 400 articles des congrès IJCAI
et AAAI sur la documentation des méthodes, des données et des expériences [@gundersen2018state].
En 2026, Coakley et ses coauteurs suivent 56 800 articles de cinq congrès d'intelligence
artificielle de 2014 à 2024 : la part qui partage code et données passe de 11 % à 64 %. La hausse
commence avant les listes de contrôle [@coakley2026shift]. Magnusson et ses coauteurs mesurent
l'effet de la liste de contrôle des congrès de traitement automatique des langues
[@magnusson2023nlpchecklist]. En RL, l'audit le plus proche est celui de Gorsane et ses coauteurs :
75 articles de RL coopératif à plusieurs agents, de 2016 à 2022, dont environ un tiers ne quantifie
aucune incertitude [@gorsane2022marl]. Aucun de ces audits ne cible le RL à un seul agent, ni la
grille de 2018.

**La méthode statistique.** Colas et ses coauteurs calculent combien de graines aléatoires il faut
pour détecter un écart donné [@colas2018seeds]. Jordan et ses coauteurs discutent la mesure
elle-même [@jordan2020evaluating], puis le coût en calcul d'une comparaison rigoureuse
[@jordan2024position]. Agarwal et ses coauteurs apportent la
moyenne interquartile et des intervalles calculés par rééchantillonnage [@agarwal2021precipice].
Patterson et ses coauteurs en font un guide [@patterson2024empirical]. Eimer et ses coauteurs
réclament le même budget de réglage pour les références que pour la méthode
[@eimer2023hyperparameters]. Ces travaux disent quoi faire. Notre sondage mesure si la communauté
le fait.

**Les expériences refaites.** Islam et ses coauteurs précèdent Henderson sur les mêmes tâches
[@islam2017reproducibility]. Lynnerup et ses coauteurs refont des algorithmes sur un vrai bras
robotique [@lynnerup2020survey]. Bjorck et ses coauteurs montrent, pour le contrôle à partir d'images,
qu'une part de la variance entre graines aléatoires vient d'essais qui échouent tôt par instabilité
numérique. Une normalisation de l'avant-dernière couche du réseau la réduit
[@bjorck2022variance].

**Le RL de grands modèles.** Hochlehnert et ses coauteurs réévaluent des modèles de raisonnement et
trouvent de forts écarts d'une graine aléatoire d'échantillonnage à l'autre
[@hochlehnert2025sober]. Chandak et ses
coauteurs relèvent, dans un billet non relu par des pairs, des modèles de départ sous-évalués dans
sept articles [@chandak2025incorrect] : l'équivalent moderne des références mal réglées de 2018.
Shao et ses coauteurs montrent la récompense tirée au sort qui « marche » [@shao2025spurious]. Notre
volet GRPO illustre ce dernier résultat sans prétendre le découvrir.

**Notre apport.** Il vient de la combinaison : une mesure avant et après sur la grille d'origine,
calibrée par notre propre lecture de 2018, les expériences de 2018 refaites avec les outils de
2026 sous un protocole écrit d'avance, enfin un pont vers le RL de grands modèles.

# Ce que nous en retenons

**Écoutée en partie, ailleurs qu'on l'attendait.** La seule faille en net progrès, l'évaluation
tenue à part, doit sa hausse au changement de terrain du RL : les recueils de problèmes de
mathématiques ont un jeu de test par construction. Les failles qui demandaient un effort sans
contrainte extérieure n'ont pas changé de façon détectable, ou ont reculé : dix graines aléatoires, un test statistique, des
références réglées comme la méthode.

**Le hasard trompe l'œil, nos choix trompent le test.** Sur nos essais de PPO, les graines
aléatoires fabriquent des écarts visibles. Ce sont nos choix, trier et
garder les meilleurs, qui changent ces écarts en faux positifs. Nous en tirons deux
consignes : ne jamais trier les graines aléatoires, montrer un intervalle à côté de chaque
courbe.

**La grille s'applique d'abord à soi.** Dans E6, nous avons trouvé une erreur dans notre propre
code, puis constaté qu'elle n'expliquait rien. Notre premier indicateur GRPO mesurait une limite de
longueur. Nous avons trouvé ces deux pièges parce que le protocole était écrit d'avance et que nous avons vérifié les résultats
surprenants avant de les publier. C'était le conseil de Pineau en 2018 : être aussi critique envers
ses bons résultats qu'envers ses mauvais.

# Limites

**Ce qui affaiblit le sondage.** Nous les listons pour qu'aucun lecteur n'ait à les chercher.

- Les articles sont lus par des agents de modèle de langue. Chaque décision cite l'article. Un
  second agent s'accorde avec le premier sur 98 % des décisions, mais aucun humain n'a encore
  relu à l'aveugle.
- Notre lecture de 2018 compte 12 articles. Elle ne détecte qu'un écart très grand : le recul des
  réglages des références (−36 points contre elle) ne passe pas la correction de Holm, alors
  qu'il la passe contre les chiffres de Pineau.
- La population a changé : 27 articles de 2026 sur 50 traitent de grands modèles de langue, une
  famille absente en 2018. Les comparaisons sur le seul RL classique reposent sur 14 articles.
- Le filtre de titre (« reinforcement learning », « RL », « policy optimization »…) rate les
  articles de RL dont le titre ne le dit pas, en 2018 comme en 2026.
- Le tirage de Pineau en 2018 reste inconnu. Nos comparaisons avec ses chiffres supposent
  un tirage comparable au nôtre.

**Ce qui n'est pas encore mesuré.** Six failles (F6, F8, F13, F14, F16 et une part de F3) attendent
la seconde grille ou la fin des simulations. E1 se limite à une tâche et un algorithme. Le volet
GRPO reste une illustration sur des modèles de 0,5 et 1 milliard de paramètres, loin d'une
réplication de Shao et ses coauteurs.

# Ce qui reste à mesurer

- La seconde grille (Y1 à Y12) sur les 50 articles de 2026 et les 12 de 2018, avec les mêmes règles et une double lecture de 10 articles. Le plan est écrit.
- Les expériences E2 à E5 et E7, quand les 75 entraînements restants seront finis. Pour E6, les dix entraînements du script officiel du recueil Zoo, préenregistrés.
- Les neuf essais GRPO restants, relancés la nuit, avec la part de réponses coupées mesurée à chaque évaluation.

# Reproductibilité

Le code, les protocoles, les journaux d'évaluation et les scripts d'analyse se trouvent dans
`study/`, `sim/` et `sim/llm/`. Le script `docs/figures/build.py` régénère toutes les figures à
partir des fichiers de résultats. L'environnement logiciel est figé dans `sim/requirements.lock`.
