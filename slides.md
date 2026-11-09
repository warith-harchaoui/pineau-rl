# Les diapositives de la conférence de Joelle Pineau, ICLR 2018

Conférence invitée, ICLR 2018, Vancouver, jeudi 3 mai 2018 :
« Reproducibility, Reusability, and Robustness in Deep Reinforcement Learning ».
Vidéo : https://www.youtube.com/watch?v=Vh4H0gOwdIg (49 min 22 s), copie locale `video/talk.mp4`.

Inventaire reconstitué le 8 novembre 2026 à partir de la vidéo : détection des changements
de plan sur la seule zone de la diapositive (`ffmpeg`, recadrage 960 × 720 à gauche, seuil de
scène 0,04), puis quelques images prises à la main dans les trous. Les images sont dans
`video/slides-scan/` (s-NNN.jpg, horodatages dans `video/slides-scan/times.txt`) et
`video/gaps/` ; les onze premières extraites par l'autre session sont dans `video/frames/`
(leur `times.txt` est vide). Trois images pleine résolution des diapositives clés :
`video/slide23-full.png`, `video/slide30-full.png`, `video/slide31-full.png`.

Le numéro est celui imprimé en bas de la diapositive quand il est lisible ; sinon, il est
déduit de l'ordre (marqué « ~ »). Les diapositives 1, 2, 7, 10, 11, 25, 27 et 32 n'apparaissent
pas à l'écran de façon lisible (titre, transitions, ou diapositive passée trop vite).

| N° | Horodatage | Image | Titre et contenu |
|---|---|---|---|
| 3 | 2:47 | s-001 | Reproducibility crisis in science (2016) : anneau Nature, 1 576 chercheurs, **52 %** « yes, a significant crisis », 38 % « slight », 7 % ne sait pas, 3 % non. (À l'oral elle dit « 50 % » : la diapositive dit 52 %.) Lien nature.com/news/1-500-scientists-lift-the-lid-on-reproducibility-1.19970 |
| 4 | 3:16 | s-002 | Même anneau + barres « Have you failed to reproduce an experiment? » par discipline (chimie, biologie, physique, médecine, terre, autre), « someone else's » contre « my own » |
| 5 | 4:15 | s-003 | Reproducibility crisis in ML? Camembert « ML Experts (n=20) » : 45 % slight, 35 % significant, 10 % no, 10 % not sure (soit 80 % « crise ») |
| 6 | 4:51 | s-004 | A criteria for reproducible research : « An article about computational science in a scientific publication is not the scholarship itself, it is merely the advertising of the scholarship. » Buckheit et Donoho, *WaveLab and reproducible research*, Stanford, 1995 |
| 8 | 6:48 | s-005 | 25 years of RL papers : histogramme du nombre d'articles de RL par an (Google Scholar), 1990 à 2016, près de 14 000 la dernière année ; deux astérisques vers 2000 (ses débuts) ; réf. Henderson et al., AAAI |
| 9 | 8:17 | s-006 | Impressive results! AlphaGo (2016) : partie contre Lee Sedol, couverture Nature « All systems Go » |
| ~10 | 9:05 | s-007 | Got the blueprints! : même visuel + première page de l'article Nature « Mastering the game of Go with deep neural networks and tree search » |
| 12 | 10:49 | s-008 | Fermat's last theorem (1637) : énoncé + page de l'Arithmétique de Diophante annotée |
| 13 | 11:28 | s-009 | Idem + logo Guinness « Longest standing maths problem (ever)! Until 1995 when Andrew Wiles published a proof, after 358 years » |
| 14 | 12:21 | s-010 | Eureka! : photos (élèves devant un écran, enfant qui lève les bras) + courbes d'apprentissage |
| 15 | 13:18 | s-011 | Reusable platforms for RL : Robot soccer (partial obs.), MuJoCo (Todorov et al. 2012 ; Half Cheetah, Walker), Arcade Learning Environment (Bellemare et al. 2013), ELF (Tian et al. 2017) |
| 16 | 15:07 | s-012 | La thèse : « REUSABLE material (software, datasets, experimental platforms) help us REPRODUCE scientific methods to establish the ROBUSTNESS of the findings. » |
| 17 | 15:42 | s-013 | RL setting: Policy gradient methods : équation du gradient de politique, schémas on-policy / off-policy actor-critic |
| 18 | 17:09 | s-014 | Policy gradient papers : 11 articles récents dont 7 acceptés à l'ICLR 2018 ; « Most papers use same policy gradient baseline algorithms. » |
| 19 | 18:24 | s-015 | Policy gradient baseline algorithms : TRPO (Schulman 2015), PPO (Schulman 2017), DDPG (Lillicrap 2015), ACKTR (Wu 2017) |
| 20 | 18:58 | s-016, s-017 | Robustness of policy gradient algorithms : courbes HalfCheetah, Alg.1 à Alg.4 anonymisés + vidéo du Half Cheetah (19:27) |
| 21 | 20:08 | s-030 | Idem + Hopper et Swimmer : le classement s'inverse ; sur Swimmer, l'algorithme rouge (meilleur sur HalfCheetah) n'apprend rien |
| 22 | 21:33 | s-031 | Codebase comparison : capture d'une recherche GitHub « TRPO » (une dizaine de dépôts) + courbes HalfCheetah-v1 (TRPO, Codebase Comparison), trois implémentations |
| 23 | 22:23 | s-032 | Codebase comparison : TRPO implementations (3 courbes) et DDPG implementations (3 courbes) sur HalfCheetah |
| 24 | 22:48 | s-033 | Effect of hyper-parameter configurations : structure du réseau (64,64), (100,50,25), (400,300) pour PPO ; activation tanh, relu, leaky_relu pour TRPO |
| 26 | 23:30 | s-034 | An intricate interplay of hyper-parameters : DDPG, échelle de récompense avec et sans layer norm ; en rouge « When testing a baseline, how motivated are we to find the best hyper-parameters? » |
| ~27 | 25:20 | s-035 | How should we measure performance of the learned policy? : courbes HalfCheetah Alg.1 à 4 |
| 28 | 26:30 | s-036 | How many trials? : tableau de 7 articles (noms masqués en jaune) : top-5, 3-9, 5 (5), 3, 5, 5, top-2 / top-3 |
| 29 | 27:07 | s-037 | Consider the case of n=10 : dix courbes, une ligne « Baseline to beat » |
| 30 | 27:45 | gaps/g-002745 | Idem + « Top-3 results » : « Strong positive bias: seems to beat the baseline! Variance appears much smaller. » |
| 31 | 28:23 | s-038, slide31-full.png | Let's look a little closer : deux courbes avec bandes, orange au-dessus de bleu, « n=5 » et « n=5 ». À l'oral : même code TRPO, mêmes hyperparamètres, seules les graines changent |
| 33 | 29:26 | s-039 | Simulation ➜ Real-world : medical treatment design, intelligent transportation, energy & resource management, financial systems |
| 34 | 31:08 | s-040 | « Science aims to understand and explain. Science as a collective institution aims to produce more and more accurate explanations of how the world works. » |
| 35 | 32:09 | s-041 | ELF OpenGo : open source Go playing bot (github.com/pytorch/elf), Tian, Ma, Gong, Sengupta, Chen, Zitnick ; « System can be trained with 2000 GPUs in 2 weeks » |
| 36 | 33:20 | s-042 | ELF OpenGo : « Performance vs top professional players: 14-0 record (April 2018). Single GPU, 80k rollouts, 50 secs » ; Kim Ji-seok (#3) 3-0, Shin Jin-seo (#5) 2-0, Park Yeonghun (#23) 4-0, Choi Cheolhan (#30) 5-0 ; « vs strong bot (LeelaZero): 200-0 record » |
| 37 | 34:31 | s-043 | ICLR 2018 reproducibility challenge : capture d'OpenReview, soumissions ICLR 2018 |
| 38 | 36:18 | s-044 | Survey from the reproducibility challenge : 54 participants, 30 auteurs, 14 autres ; avant (n=98) : 49 % slight, 22,4 % significant, 11,2 % no, 17,3 % not sure ; après : 51 % opinion inchangée, 29,8 % plus convaincus |
| 39 | 37:07 | s-045 | Successful? 54,5 % « reproduced some », 32,7 % « most », 9,1 % non. Difficult? 44,4 % reasonable, 22,2 % very difficult, 31,5 % mild |
| 40 | 37:53 | s-046 | Idem + participants (n=54) : confiance dans leurs conclusions, 53,8 % modérée, 34,6 % haute |
| 41 | 38:09 | s-047 | Authors (n=27) : « Do you TRUST the validity of the reproducibility report? » **59,3 % yes** (elle dit « 69 % » à l'oral), 18,5 % no, 14,8 % not sure ; Authors (n=26) : « 61 % said yes » à la mise à jour de l'article |
| 42 | 39:05 | s-048 | All (n=98) : mécanismes : 46 % projet de cours, 36 % appel ouvert avec prix, 11 % intérêt pour la qualité, 7 % confier la réplication à des relecteurs |
| 43 | 39:28 | s-049 | Authors (n=28) : 79 % oui pour ICLR 2019, 14 % peut-être, 8 % non ; verbatims |
| 44 | 39:56 | s-050 | What can you do? Partager du matériel réutilisable ; « be as critical of the "good" results as the "bad" results » ; contribuer à l'effort de reproductibilité |
| 45 | 40:36 | s-051 | Contributors : Peter Henderson, Riashat Islam, Phil Bachman, Doina Precup, David Meger ; équipe ELF OpenGo ; Genevieve Fried, Rosemary Nan Ke, Hugo Larochelle ; Reasoning and Learning Lab, McGill |
| | 41:31 | s-052 à s-055 | Questions de la salle (plans sur l'oratrice et le public) |

## Écarts entre l'oral et les diapositives

- Nature 2016 : 52 % sur la diapositive, « 50 % » à l'oral.
- Confiance des auteurs dans les rapports du défi : 59,3 % sur la diapositive, « 69 % » à l'oral.
- Implémentations de TRPO : la capture GitHub montre une dizaine de dépôts, les courbes en
  comparent trois (comme l'article de Henderson et al., qui compare l'implémentation
  d'origine de Schulman, celle d'OpenAI Baselines et celle de rllab ; pour DDPG, rllab Theano,
  rllabplusplus et OpenAI Baselines).

## Copie officielle des diapositives : trouvée (version NeurIPS 2018)

Copie de référence rangée par Warith : `slides/neurips2018-pineau.pdf` (même fichier), avec les listes de contrôle v1.2 et v2.0 et la page du défi ICLR 2018 récupérées sur Wayback, dans `slides/`.

- **PDF officiel de la version NeurIPS 2018**, hébergé par NeurIPS :
  https://media.neurips.cc/Conferences/NIPS2018/Slides/jpineau-NeurIPS-dec18-fb.pdf
  (58 pages, 3,7 Mo), copie locale `jpineau-NeurIPS-dec18-fb.pdf`, pages rendues en
  vignettes dans `neurips2018-pages/`. Conférence Posner, « Reproducible, Reusable, and Robust
  Reinforcement Learning », Montréal, 5 décembre 2018. Vidéo NeurIPS :
  https://videoken.com/embed/jH0AgVcwIBc
- Ce n'est pas le jeu de l'ICLR, mais les pages 10 à 26 reprennent les diapositives 8 à 31 de
  Vancouver presque à l'identique (mêmes figures de Henderson et al.). La page 22 écrit en
  toutes lettres ce qu'elle disait à l'oral en mai : « Both are same TRPO code with best
  hyperparameter configuration! ». Ajouts propres à NeurIPS : un lien vers le billet d'Alex
  Irpan « Deep Reinforcement Learning Doesn't Work Yet » (p. 27), le sondage de 50 articles de
  RL de 2018 publiés à NeurIPS, ICML et ICLR (p. 29-30 : code lié 55 %, méthode de choix des
  hyperparamètres 20 %, évaluation sur un ensemble tenu à part 10 %, test de significativité
  5 %), la première liste de contrôle de reproductibilité (p. 31-33), et « Myth or fact?
  Reinforcement Learning is the only case of ML where it is acceptable to test on your
  training set » (p. 36-39, 51).
- Fiche ICLR (https://iclr.cc/virtual/2018/invited-talk/346) : jeudi 3 mai 2018, 9 h-9 h 45,
  Exhibition Hall A ; aucun lien vers des diapositives.
- Page de Joelle Pineau à McGill (https://www.cs.mcgill.ca/~jpineau/) : pas de lien repéré vers
  le jeu de l'ICLR. La page du défi 2018 existe :
  https://www.cs.mcgill.ca/~jpineau/ICLR2018-ReproducibilityChallenge.html
- Le jeu de Vancouver lui-même (ICLR, 45 diapositives environ) reste introuvable en PDF ;
  l'inventaire ci-dessus, tiré de la vidéo, en tient lieu.

Les figures des diapositives 20 à 31 viennent de Henderson et al., « Deep Reinforcement
Learning that Matters », AAAI 2018 (arXiv 1709.06560) : figure 5 pour les deux graines (t =
-9,09, p = 0,0016), figure 6 pour les implémentations, tableau 3 pour le classement par tâche,
tableau 7 pour le nombre d'essais des articles publiés.
