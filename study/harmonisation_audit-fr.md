*Traduction de [harmonisation_audit.md](harmonisation_audit.md), faite le 10 novembre 2026. Le texte anglais est l'original daté et fait foi.*

# Audit d'harmonisation des lectures brutes v2 (avant tout pourcentage)

Périmètre : chaque JSON de `codes_v2/{A2,B2,C2,D2,E2,F2,H1,H2,H3,H4,K1..K7}/` (170 fichiers ; G2, R2 et le pilote exclus).
Règles appliquées : `GRILLE.md`, écarts 1 à 6, 14, 17 et 18 de `PROTOCOL.md`. Pour les fichiers qui ne contiennent que Y1 à Y12, les valeurs v1
qui servent aux règles de portée (Q1, Q4, X2, X5) ont été lues dans `codes/` (premier lecteur, pas G).
Aucune part ni aucun compte de `yes` par critère, par année ou par échantillon n'a été calculé. Le contexte a été vérifié avec
`pdftotext` quand un signalement en dépendait ; « aucun point trouvé » signifie qu'une recherche dans le texte intégral de
final/last/best/converged/end of training/after N steps n'a rien trouvé qui s'applique aux tableaux principaux.

Format : `article (lecteur) : actuel -> proposé · règle · citation ou raison`.

---

## Y1, mesure ET point de mesure (écart 17)

### Y1 `yes` dont la citation ne donne aucun point de mesure (proposé `no`)

- LR02 (A2) : yes -> no · é17 · « Attack Success Rate (ASR) and Benign Return (BR) ... defined below » ; aucun checkpoint indiqué.
- LR05 (A2) : yes -> no · é17 · « the reported metric is the mean of this indicator over the evaluation videos » ; checkpoint non précisé.
- LR13 (B2) : yes -> no · é17 · « We employ the sub em score for all benchmarks » ; métrique seule.
- LR16 (B2) : yes -> no · é17 · « we adopt LLM as judges for correctness evaluation » ; métrique seule.
- LR17 (B2) : yes -> no · é17 · « we use accuracy as both the evaluation metric and the reinforcement learning reward signal » ; « accuracy » seul est le cas d'école du `no` de l'é14.
- ML01 (B2) : yes -> no · é17 · « zero-shot setting, ... temperature set to 0 » ; réglages de décodage, pas un point.
- ML03 (B2) : yes -> no · é17 · « we compute PSNR and SSIM in non-edit regions » ; métrique seule.
- ML07 (C2) : yes -> no · é17 · « Detection performance (F1 score, %) » ; métrique seule.
- ML08 (C2) : yes -> no · é17 · « average success rate over 50 evaluation episodes per task » ; le nombre d'épisodes est explicitement exclu comme point.
- ML12 (C2) : yes -> no · é17 · « Accuracy is reported ... final average performance is calculated by first averaging ... ID, OOD » ; « final » désigne l'agrégat et non le checkpoint.
- ML13 (C2) : yes -> no · é17 · « we use greedy decoding (temperature = 0) » ; décodage seulement (« final performance » n'apparaît que dans une ablation en annexe).
- NER04 (E2) : yes -> no · é17 · définition de la récompense et températures d'échantillonnage ; aucun point.
- C117 (H1) : yes -> no · é17 · « Accumulated Reward (AR) and Episode Length (EL) of each episode are calculated » ; aucun checkpoint.
- C32 (H1) : yes -> no · é17 · « Top-1 Generalization Accuracy ... of the most likely program » ; aucun checkpoint.
- C38 (H3) : yes -> no · é17 · « For each of the 50 total test mazes we ran 100 episodes ... and averaged » ; aucun checkpoint.
- K002 (K1) : yes -> no · é17 · « Accall(τ) is the percentage of all outputs that satisfy ... » ; aucun point.
- K004 (K1) : yes -> no · é17 · « average accuracy@8 at an inference temperature of 1.0 » ; aucun checkpoint pour le tableau principal.
- K014 (K1) : yes -> no · é17 · « HPSv3 ... and ImageReward ... as in-domain and out-of-domain evaluation metrics » ; métrique seule.
- K016 (K1) : yes -> no · é17 · « Time in Range (TIR). The percentage of time blood glucose remains within ... » ; métrique seule.
- K044 (K3) : yes -> no · é17 · LC win rate, WR, score MT-Bench, strict accuracy ; aucun checkpoint.
- K052 (K3) : yes -> no · é17 · « FR measures the ratio ... FT records the time ... » ; aucun checkpoint de la politique entraînée.
- K059 (K4) : yes -> no · é17 · « we report mean AUROC » ; aucun point.
- K061 (K4) : yes -> no · é17 · « weighted average of the F1-scores » ; aucun point.
- K063 (K4) : yes -> no · é17 · « each teammate instance is evaluated over 100 episodes; a per-instance mean return » ; aucun checkpoint.
- K067 (K4) : yes -> no · é17 · « completion accuracy ... for a single generated completion » ; aucun checkpoint.
- K068 (K5) : yes -> no · é17 · « report pass@1 using non-zero temperature » ; aucun checkpoint.
- K075 (K5) : yes -> no · é17 · « final evaluation score ... average speedup ratio across all execution rounds » ; « final » désigne l'agrégat et non le checkpoint.
- K077 (K5) : yes -> no · é17 · « ROUGE-L Recall ... Measures the longest common subsequence overlap » ; métrique seule.
- K078 (K5) : yes -> no · é17 · « Reward (average episode return over 10 runs) » ; « Return » sans plus.
- K106 (K7) : yes -> no · é17 · « Pass@1 as the average accuracy across K generated samples » ; aucun checkpoint.
- K110 (K7) : yes -> no · é17 · « speedup of the fastest kernel (within the trajectory) » ; aucun checkpoint.

Cas plus faibles (la citation est hors sujet, ou la métrique n'est pas le score d'une politique entraînée ; à trancher avec la lacune 1c) :
- C19 (H3) : yes -> no? · é17 · retour actualisé par évaluation ; seulement la courbe, aucun point pour les nombres rapportés.
- C220 (H2) : yes -> no? · é17 · la citation concerne la récompense de l'oracle, pas la façon dont le nombre de la méthode est mesuré.
- C26 (F2) : yes -> no? · é17 · « optimality gap ... normalized » ; aucun checkpoint.
- C22 (F2) : yes -> no? · é17 · test KS sur des échantillons ; aucun checkpoint.

### Y1 `no` alors que l'article donne bien le point

- K089 (K6) : no -> yes · l'é17 cite « aire sous la courbe » · « Results are averaged over 1M training steps in MuJoCo tasks » est une moyenne sur l'entraînement (un point de type aire sous la courbe).
- ML16 (C2) : no -> yes seulement si la lacune 1b reçoit la réponse « durée d'entraînement = final » · « we run 500K steps training for all baselines ... averaging results over 4 seeds ».

### Divergences entre lecteurs que la règle ne tranche pas (voir les lacunes 1a à 1c)

- Les courbes d'apprentissage comme point. Codés `yes` sur une courbe seule : LR04, LR11, C12, C16, C17, C24, C35, C113, C118, C120, C211, C212, C34, K003, K015, K072. Codés `no` sur une courbe seule : ML14 (C2), C111 (H2), C112 (H3), C121 (H3), C210 (H1), K090 (K6), K030 (K2), NER06 (E2).
- La durée d'entraînement comme point « final » implicite. D2 accepte « trained for N steps » comme point : MLR02, MLR03, MLR07, NE04, NE05, NE06 codés `yes` ; NE02, NE08 codés `no` faute de cette mention. D'autres lecteurs (B2, C2, K*) ont codé `yes` sans aucun point (liste ci-dessus) ; E2 et les K* ont codé `no` quand le checkpoint d'un tableau n'était pas indiqué (NER01, NER06, K056, K111, K113, K103).

---

## Y5, origine du code des références (écarts 14 et 17) : classement, sans proposition

Q4 `na` ⇔ Y5 `na` se vérifie dans chaque fichier. « Chacune ? » vaut `no` quand la citation ou le doute du lecteur lui-même indique
qu'au moins une référence principale n'a pas d'origine déclarée (la règle de l'é14 dit « pour chaque référence principale »).

### (a) Dépôt ou bibliothèque nommé pour les références

| article (lecteur) | Y5 | fondement | chacune ? |
|---|---|---|---|
| LR03 (A2) | yes | banc ODRL, OfflineRL-kit, description de REAG | yes |
| NE10 (E2) | yes | deux URL GitHub (zero-shot-rl, HILP) | yes |
| NE15 (E2) | yes | OpenRLHF + « official code in RLHFlow » pour RRM | yes |
| C11 (F2) | yes | « specialized systems ... (OpenAI, 2017; Hesse) » | yes |
| C14 (F2) | yes | Gurobi 7.5 (avec sa version) | yes |
| C15 (F2) | yes | OpenAI Baselines (sans version) | yes |
| C22 (F2) | yes | « we are using the open source codes » (aucun dépôt nommé) | yes |
| C26 (F2) | yes | URL d'or-tools | yes |
| C39 (H1) | yes | OpenAI Baselines | yes |
| C113 (H2) | yes | rllab | yes |
| C119 (H2) | yes | GitHub des auteurs (référence UCRL incluse) | yes |
| C18 (H2) | yes | dépôt OpenAI baselines, GitHub de l'auteur de SAC, DDPG maison | yes |
| C33 (H2) | yes | implémentations publiées + DistMult maison + nombres rapportés | yes |
| C19 (H3) | yes | PPO d'OpenAI Baselines | yes |
| C110 (H4) | yes | fork d'OpenAI Baselines par Henderson | yes |
| K012 (K1) | yes | implémentation de Craftax, valeurs par défaut de PQN tirées de [79] | yes |
| K030 (K2) | yes | base de code CleanRL pour toutes les références | yes |
| K038 (K2) | yes | base de code JaxGCRL | yes |
| K045 (K3) | yes | réimplémentation PyTorch de DreamerV3, Simulus officiel | yes |
| K052 (K3) | yes | SCIP v8.1.0 + code publié par les auteurs | yes |
| K059 (K4) | yes | GitHub officiel ou bibliothèque SDV, selon la référence | yes |
| K066 (K4) | yes | fork du dépôt des auteurs | yes |
| K077 (K5) | yes | cadre d'évaluation RWKU | yes |
| K079 (K5) | yes | URL de CORL | yes |
| K082 (K5) | yes | implémentations officielles ou Syntheseus | yes |
| K089 (K6) | yes | implémentation officielle de RPP | ? (les autres références sont absentes de la citation) |
| K102 (K7) | yes | dépôts PyTorch publics pour chaque référence | yes |
| K105 (K7) | yes | code des auteurs avec le hash du commit | yes |
| K107 (K7) | yes | URL officielle de DreamerV3 | yes |
| ML16 (C2) | yes | implémentations de FQL et de Value Flows | yes |
| K096 (K6) | yes | ∗ dépôt officiel, † nombres tirés de SPICE (a et c mêlés) | yes |
| C17 (H1) | no | OpenAI Baselines pour Double DQN ; références HRL sans origine | no |
| C210 (H1) | no | rllab + code de MAML ; RL2 et VIME sans origine | no |
| C114 (H3) | no | TRPO/DDPG de Baselines, dépôts SAC/Soft-Q ; SVPG sans origine | no |
| C116 (H4) | no | code de DQfD, DDPG public ; TRPO et GAIL sans origine | no |
| C117 (H1) | no | OpenCV et Dlib, sans version (le lecteur a appliqué « bibliothèque avec sa version ») | yes |
| K016 (K1) | no | valeurs par défaut d'OmniSafe pour l'architecture du critique seulement | no |
| K043 (K3) | no | RLKit pour l'acteur-critique seulement ; références Atari non identifiées | no |
| K060 (K4) | no | RLeXplore, sans version ; ReAct sans origine | no |
| K095 (K6) | no | CleanRL pour PPO ; NPG, Q-learning, TS, UCB sans origine | no |
| K015 (K1) | no | « the corresponding reference implementation » (non nommée) | ? |
| K073 (K5) | no | « IQL default config in get config » (dépôt non nommé) | ? |

Remarque : C117 (no, bibliothèque sans version) et C15/C19/C39/C113 (yes, bibliothèque ou dépôt sans version) appliquent
« bibliothèque avec sa version » de deux façons différentes. Seuls C14, K052 et K105 donnent une version ou un commit.

### (b) « Réimplémenté » ou « implémenté par nous » dit en toutes lettres

| article (lecteur) | Y5 | fondement | chacune ? |
|---|---|---|---|
| LR17 (B2) | yes | « we implemented a Textual RL baseline » | ? (une seule référence nommée) |
| ML01 (B2) | yes | « we reproduce several training methodologies » | yes |
| ML11 (C2) | yes | « All methods are implemented within the same codebase » | yes |
| NE12 (E2) | yes | « we implement previous solutions within the RDC framework » | yes |
| C112 (H3) | yes | « We adapt the model of He et al. » | yes |
| C120 (H4) | yes | « In our implementation of this method » | yes |
| C212 (H4) | yes | « All baselines ... were re-implementations » | yes |
| C214 (H3) | yes | « we have implemented and run the policy gradient method » | yes |
| C34 (H4) | yes | remerciements : des collègues « implementing DDPG » | ? |
| K006 (K1) | yes | « We implemented Semdedup » ; les autres références sont des jeux de données | yes |
| K037 (K2) | yes | « we reproduce their method on Qwen2.5-VL-3B » | yes |
| K054 (K3) | yes | « we implement our ... and baseline attack algorithms » | yes |
| K075 (K5) | yes | « We implement evolutionary LLM strategies » | yes |
| K083 (K6) | yes | toutes les méthodes « share the same ... framework written in JAX » | yes |
| K113 (K7) | yes | « we implement CQL ... based on DDPG » | yes |
| K063 (K4) | yes | « Our implementations are built entirely in JAX and Flax » (doute : AD et DPT réimplémentés, AMAGO adapté) | ? |
| K039 (K2) | yes | références « tested using the same iterative RAG workflow » | no (doute : origine de R1-Searcher et de DeepResearcher non précisée) |
| MLR02 (D2) | no | JEPO réimplémenté, les autres copiés avec leur source, RAFT/TRACT « own runs » | no |
| K069 (K5) | no | Feedback Descent réimplémenté ; GRPO non identifié | no |
| K056 (K3) | no | « we run all baselines ourselves » (aucune origine du code) | ? |

### (c) Nombres copiés d'articles publiés, avec la source

| article (lecteur) | Y5 | fondement | chacune ? |
|---|---|---|---|
| LR14 (B2) | yes | « Baseline results are directly cited from Ye et al. » | yes |
| ML15 (C2) | yes | « we adopted the same results from the previous works (Ding & Jin; Park) », sans correspondance par référence | ? |
| K017 (K1) | yes | tableau 1 de MOBILE pour CQL/EDAC/MOPO, les autres tirés des articles originaux | yes |
| K028 (K2) | yes | † Deshpande et al., ‡ Li et al. | yes |
| K064 (K4) | yes | « report results from their official publications or recommended evaluation settings » | ? (aucune source par référence) |
| K067 (K4) | yes | « When available, we use baseline results reported in prior work » | ? (« when available ») |
| C218 (H1) | yes | valeurs rapportées par Rajeswaran, Salimans, Schulman, Haarnoja | yes |
| NE04 (D2) | no | « reported performance » sans source par nombre + « evaluated by us » | no |
| NE06 (D2) | no | modèles fermés tirés d'un site public de banc d'évaluation ; Logic-RL et d'autres sans origine | no |
| K068 (K5) | no | « sourced from their official release report or ... independent testing », sans dire lequel | no |

### (d) Modèle publié nommé ou cité, évalué par les auteurs (surtout `llm`)

| article (lecteur) | Y5 | fondement | chacune ? |
|---|---|---|---|
| LR07 (A2) | yes | modèles 1.5B nommés exactement, sans lien ; plus une exécution DAPO des auteurs | yes (par le nom) |
| LR10 (A2) | yes | Qwen 3 32B, Llama 3.3 70B, DeepSeek Coder v2 Lite, Sonnet 4, sans source de checkpoint | yes (par le nom) |
| LR13 (B2) | yes | DeepSeek-R1-Distill-Qwen, Qwen-2.5-Instruct(-1M), QwenLong-L1 cités | yes (par le nom) |
| LR16 (B2) | yes | checkpoints instruct de Qwen2.5/Qwen3, SFT faite par les auteurs | yes (par le nom) |
| MLR07 (D2) | yes | « official APIs », « publicly released checkpoints », DeepEyes | yes |
| ML13 (C2) | yes | variantes SFT/RLVF des auteurs + modèle propriétaire guidé par prompt | yes |
| K061 (K4) | yes | modèle de base publié + variantes affinées par les auteurs (implicite) | yes |
| K065 (K4) | yes | modèles par API dans le harnais des auteurs ; o4-mini aussi copié de Lee et al. | yes |
| NER01 (E2) | yes | GRPO dans verl + chiffre de DeepSeek-R1-Zero avec sa source | yes |
| K004 (K1) | no | « Our reproduction uses official author-provided prompts » ; PAPO-D copié sans source | no |
| (voir aussi NE04, MLR02, K068 ci-dessus : réévaluation par les auteurs de modèles nommés, codée `no`) | | | |

Voici le partage llm que le responsable avait signalé : les modèles publiés nommés et évalués par les auteurs sont `yes` chez
A2, B2, D2 (MLR07), C2, K4 et E2, mais `no` chez D2 (NE04, MLR02), K1 (K004) et K5 (K068).

### (e) Réimplémentation implicite (jamais dite) ou absence d'origine

| article (lecteur) | Y5 | fondement | chacune ? |
|---|---|---|---|
| LR04 (A2) | yes | « In our codebase ... » ; doute : recettes réimplémentées, « not said in so many words » | no (implicite) |
| LR11 (B2) | yes | « implementation ... using only NumPy and Matplotlib » (CVaR-Q réimplémenté implicitement) | implicite |
| ML14 (C2) | yes | référence entraîner-puis-corriger = checkpoints des auteurs (variante maison) | implicite |
| C31 (H4) | yes | « We perform pruning based on Molchanov et al. » | implicite |
| K085 (K6) | yes | CleanRL pour PQN ; GNS « seems reimplemented, never said » | no |
| LR02 (A2) | no | « We extend TrojDRL and SleeperNets to continuous action space » | implicite |
| LR09 (A2) | no | même architecture MLP pour toutes les références | implicite |
| NE05 (D2) | no | « All baseline models are trained ... under the consistent dataset » | implicite |
| MLR03 (D2) | no | « follow its original training setting » | implicite |
| MLR06 (D2) | no | estimateurs cités, code non précisé | implicite |
| ML12 (C2) | no | détecteurs « trained on our dataset using their original preprocessing » | implicite |
| C215 (H3) | no | « PPO uses the same hyper parameters with its original paper » | implicite |
| C216 (H1) | no | références entraînées avec le même TD3 | implicite |
| C32 (H1) | no | référence MLE « similar to » Devlin et al. | implicite |
| C220 (H2) | no | « we compare VIPER to fitted Q iteration » | implicite |
| C217 (H2) | no | mlCoP « previous reimplementation [23] » (la base du prouveur, pas les références) | ? |
| C213 (H1) | no | code MTMLIRL de BURLAP essayé, références principales sans origine | no |
| K021 (K1) | no | hyperparamètres de CleanRL, « implementations standardized » | implicite |
| K032 (K2) | no | GRPO, GRESO, CPPO cités comme algorithmes | implicite |
| K042 (K2) | no | Stream Q(λ), QRC(λ), streaming DQN cités | implicite |
| K072 (K5) | no | « Algorithm 3 in [...] » | implicite |
| K081 (K5) | no | SIL et PPO « seem reimplemented in the Julia pipeline, never said » | implicite |
| K090 (K6) | no | RPO FS « follows » Mandal et al. | implicite |

### (f) Cadre d'entraînement des auteurs nommé (l'origine des références n'en découle que si toutes les exécutions l'emploient)

| article (lecteur) | Y5 | fondement | chacune ? |
|---|---|---|---|
| LR08 (A2) | yes | « We base our experiments on the verl repository » ; doute : origine de BAPO et de GPG non précisée | no |
| K062 (K4) | yes | « Our method and all baselines are implemented on top of VeRL » | yes |
| K106 (K7) | yes | verl pour tous les algorithmes ; doute : NSR n'a pas d'origine | no |
| K110 (K7) | yes | « built our training framework on top of OpenRLHF » ; o4-mini/o3-mini par le nom | ? |
| K044 (K3) | no | « We adopt the OpenRLHF framework » ; récompenses des références non identifiées | no |

Contradictions avec « chaque » parmi les codes `yes` (le doute du lecteur lui-même nomme une référence non identifiée) :
LR04, LR08, K039, K085, K106. Même fondement, codes opposés : (f) K110/K106/LR08 `yes` contre K044 `no` ;
(a) C15/C19/C39 `yes` contre C117 `no` ; (c)+(d) K064 `yes` contre K068 `no`.

---

## Y3, nombre de conditions d'entraînement (écart 17) ; seuls les passages entre 1 et ≥2

- K036 (K2) : 2 -> 1 · é17 (une seule condition d'entraînement) · « During training, we jointly optimize two tasks: score regression and degradation perception » ; une seule exécution d'entraînement conjointe sur un seul jeu de données (sous-ensemble de DQ-495K). Y4 passe alors à na.
- K103 (K7) : 2 -> 1 · é17 (conclusion principale) · les résultats principaux viennent de l'entraînement dans l'environnement GUI simulé ; la seconde « condition » est un complément d'entraînement continu (« we continue training our agents ... with 24k samples »), rapporté dans un tableau secondaire. Y4 passe alors à na.
- K055 (K3) : 8 -> 1 en lecture stricte · é17 (« plusieurs bancs d'évaluation d'un même modèle entraîné ne multiplient pas les tâches ») · OmniRL est méta-entraîné une seule fois sur AnyMDP ; « Gymnasium, DarkRoom, and Bandits tasks are entirely absent from OmniRL's training regimen ». Le RL en contexte apprend chaque tâche au moment du test : voir la lacune 3a. Y4 suivrait.

Vérifiés, sans passage : LR08 (jeux d'entraînement en mathématiques et en code, ≥2, même si le 4 compte des familles de modèles), LR10 (jeux d'entraînement MBPP-X et CF-X), LR17 (jeux d'entraînement OmniMedVQA et VQA-RAD+SLAKE ; la citation n'en montre qu'un), K062 (GURU et le jeu de préférences Dolphin), K014, K032, NE15, NER04, ML07 (le leave-one-domain-out donne des jeux d'entraînement distincts), ML06 (niveaux d'Overcooked = difficulté, 1 est juste), K051 (degrés comme niveaux, 1 est juste), K110 (Level 1 + Level 2, 1 est juste), K077 (TOFU seulement en annexe B.1 : 1 est juste si les expériences propres à l'annexe ne comptent pas ; voir la lacune 3b).

---

## Q5 / écart 6, pages de projet et « will be released »

« Will be released » codé `yes` : aucun. (K035, K036, K039, K043, K077, K106 et C32 sont tous `no`, comme le veut la règle.)

Page de projet, Google Sites, github.io ou page anonyme codée `yes` :

| article (lecteur) | lien | l'article dit-il que la page contient du code ? | proposition |
|---|---|---|---|
| C19 (H3) | sites.google.com/view/time-limits-in-rl | yes : « The source code and videos can be found at » | garder yes si le lien mène au code (vérification de l'é6) |
| C120 (H4) | sites.google.com/view/goalgeneration4rl | yes : « Videos and code available at » | garder yes si le lien mène au code |
| K038 (K2) | wang-kevin3290.github.io/scaling-crl | yes : « The project webpage and code can be found here » (un seul lien, vers la page) | garder yes si le lien mène au code |
| K056 (K3) | kaifukazawa.github.io/ramac-project (hyperlien) | yes : « The code and experimental results are available on the project website » | garder yes si le lien mène au code |
| K064 (K4) | tiger-ai-lab.github.io/Critique-Coder (URL nue sous les noms des auteurs) | no : aucune phrase sur le code | yes -> no sauf si la page est vérifiée et mène au code (é6) ; cohérent avec K069 et K089, que les lecteurs ont codés `no` pour des pages de projet sans mention de code |
| K090 (K6) | anonymous.4open.science/r/PePG-0C27 | yes : « Code of PePG is available in Link » | un miroir de code anonymisé, pas une page de projet ; yes convient, mais le lien a peut-être expiré |

Pages de projet codées `no` (vidéos seulement, cohérent) : C210, C216, C114, C34, K069, K089, K107 ; C27 (vidéo seulement), C217 (jeu de données seulement).

---

## Critères v1 sur les fichiers v1+v2 (C1*, C2*, C3*, K*)

### X4 (écart 1)
- C210 (H1) : no -> yes · é1 (réglage décrit pour les références) · annexe : « We describe the hyper-parameters swept over for gradient based meta-learning methods ... for MAESN, latentspace baseline and MAML ... For each method, we selected hyperparameters which gave best train time performance ».
- Cas limites, non signalés : K111 (K7) no (« λUCB is a hyperparameter we tune for each method », sans description du réglage) ; C121 (H3) yes (entraînement par population pour tous les agents, références comprises, déduit de la légende de la figure) ; C39 (H1) yes (taux d'apprentissage réglé avec DQN, la référence, puis partagé).
- Q4 `na` ⇔ X4 `na` se vérifie partout.

### X7 (écart 2)
Aucune contradiction. Chaque `yes` donne une quantité. Les `no` fondés sur le seul matériel (C121, C210, C114, C214, K014, K015, K023, K037, K043, K049, K056, K061, K078, K084, K089, K102, K106) sont cohérents. Le `yes` de C212 s'appuie sur la figure 5 (heures de temps réel). Voir les lacunes 5a et 5b pour les durées mesurées à l'inférence seule et les durées vagues.

### X3 (écart 5)
Aucune contradiction nette. Cas à trancher par une règle (lacune 5c) : C35 (H3) yes (la sélection fait partie de la définition de la *référence*, « selects the policy with the maximum performance ») ; K072 (K5) yes et C34 (H4) yes (l'abandon des graines aléatoires mauvaises ou non résolues est compté comme sélection du meilleur essai) ; C33 (H2) no (« We found it easy to obtain/reproduce the highest scores across several runs » désigne peut-être un meilleur sur N).

### Q7 (écart 4)
Chaque article `theory` avec des expériences jouets est `no` (C111, C119, C29, K003, K023, K090, K098, K099) ; C28 et K109 sont `na` avec Q1 `no`. Aucune contradiction. Le yes de K028 (K2) s'appuie sur un chiffre de « validation set » ; le tableau principal concerne l'« official C-STS benchmark ». Cela reste en deçà d'une contradiction nette.

---

## Y7, version de CHAQUE environnement ou banc principal (écart 14, « chaque » strict de l'écart 17)

`yes` en contradiction avec la règle :
- LR08 (A2) : yes -> no · é17 (une partition des auteurs ne compte que si elle est publiée) · DAPO-Eval est construit par les auteurs ; le lecteur note que le texte dit « will release ». La citation est l'URL de la page de projet.
- LR10 (A2) : yes -> no · « chaque » · le doute du lecteur dit « MultiPL-E n'a pas de numéro de version ».
- K106 (K7) : yes -> no · « chaque » · « Minerva Math » n'a ni version ni partition. La même liste (AIME 2024/2025, AMC 2023, MATH500, Minerva, Olympiad) est codée `no` dans LR07 (A2).
- K037 (K2) : yes -> no · analogue de « MATH seul : no » · « VSI-Bench, VideoMMMU, MMVU, MVBench, TempCompass, and VideoMME » sont seulement nommés. Comparer avec K004 et K006 (K1), codés `no` sur le même genre de liste.
- K014 (K1) : yes -> no · GenEval et DPG sont nommés sans version. Le même lecteur a codé K004 `no` sur les seuls noms.
- MLR02 (D2) : yes -> no · « chaque » · le doute du lecteur dit « FLASK, Vicuna Bench et MT Bench ... sans version ni lien, codé yes par analogie avec MATH-500 ».

Dépendent de la lacune 7a (une partition nommée sans version ni date) :
- NE02 (D2) yes et NE08 (D2) yes : noms de partition seulement (test, val, testmini).
- MLR07 (D2) yes : le nom « XLRS-Bench » seulement.
- K065 (K4) yes : « FHIR-AgentBench validation set (424) ».
- K072 (K5) yes : un environnement LQ des auteurs, entièrement spécifié par ses paramètres (lacune 7b).

---

## Y9, seulement ce que l'article présente comme un hyperparamètre (écart 17)

- LR07 (A2) : yes -> no · é14/é17 (une ablation de composant n'est pas un balayage) · « Adding uncertainty weighting (λ2 = 0.4) increases exploration diversity » compare la présence et l'absence du composant. Le doute du lecteur dit aussi que le balayage ne montre que des métriques de recherche, pas le score final.
- Dépendent de la lacune 9a (paramètres d'inférence ou d'environnement) : LR14 (B2) yes (MAX_NUM_FRAMES varié à l'inférence) ; K068 (K5) yes (longueur de contexte et nombre d'appels d'outils à l'inférence) ; C24 (F2) yes (pas d'entraînement au moment du test U) ; C26 (F2) yes (largeur du faisceau) ; K095 (K6) yes (budget d'attaque B, que le lecteur soupçonne d'être une condition d'environnement).

---

## Y6, exclusions (écart 17)

Aucun code `yes`/`no` ne contredit le texte écrit. Une divergence que la règle ne tranche pas (lacune 6a) : le filtrage des données d'*entraînement* est compté comme exclusion déclarée dans LR05, LR07, LR13, LR14, LR16, LR17, ML03, ML07, ML12, ML13, K044, K061, K063, K064 et K073. Tous les autres codes `yes` concernent des exécutions d'évaluation, des graines aléatoires, des tâches ou des combinaisons omises, que l'écart 17 couvre explicitement. Le `no` de K072 (K5) (« removing extremely poor results », sans dire lesquels) est cohérent avec « dit quels essais ».

---

## Y8, généralisation au-delà des conditions d'entraînement (plus strict que Q7)

- K082 (K5) : yes -> no · é14 (un banc différent ne compte que s'il est présenté comme une condition réservée ou décalée) · « We evaluate performance on three benchmarks of increasing difficulty: Retro*-190 ... ». Ce sont des jeux de test standard, que l'article ne présente pas comme de la généralisation.
- C12 (F2) Y8 yes avec Q7 v1 `no` (codes/) : Y8 est plus strict que Q7, cette paire se contredit donc elle-même. Y8 paraît juste (« we introduced a small change to the environment: ... teleport »), ce qui rend le Q7 v1 suspect. ML07 (C2) montre le même schéma : Y8 yes (leave-one-domain-out), Q7 v1 `no`.
- Dépendent de la lacune 8a (banc llm dit de « generalization » mais pas « out-of-distribution ») : LR10 (A2) yes, K044 (K3) yes, K096 (K6) yes, ML03 (B2) yes.
- Dépendent de la lacune 8b (partition de test réservée i.i.d., ou instances réservées) : codés `yes` K081 (K5), C219 (H4), K086 (K6, un environnement de validation avec une nouvelle graine aléatoire) ; codés `no` K110 (K7, « 100 unseen KernelBench tasks »), C32 (H1), C33 (H2), C114 (H3), NER04 (E2), K049 (K3).

---

## Cohérence de portée

Vérifié mécaniquement sur les 170 fichiers :
- Y2 et Y11 sont `na` si et seulement si X2 = no.
- Y4 est `na` si et seulement si Y3 = 1.
- Y5 est `na` si et seulement si Q4 = na.
- Q4 `na` ⇔ X4 `na`.
- Q1 = no met tous les Y à `na` ; pour les nouveaux articles, il met aussi à `na` tous les critères v1 de Q2 à X7.
- Y11 = yes s'accompagne toujours d'un `kind`.

Aucune violation. Les seuls changements de portée viennent des recodages Y3 proposés : K036, K103 et K055 exigeraient Y4 -> na.

---

## Lacunes des règles (cas qu'aucune règle écrite ne tranche)

1. **Y1**
   - 1a. Une courbe d'apprentissage (la performance en fonction des pas) est-elle un point de mesure ? Les lecteurs se partagent : 16 `yes` contre 8 `no`, listés plus haut.
   - 1b. Indiquer la durée d'entraînement (« trained for N steps/1 epoch ») implique-t-il que le nombre rapporté vient du checkpoint final ? D2 répond oui ; la plupart des autres lecteurs ne l'ont ni exigé ni employé.
   - 1c. Quel est le « point » pour des métriques qui ne sont pas le score d'une politique entraînée : erreur d'estimateur (MLR06, C25), temps de calcul (C14), tests KS (C22), solveurs combinatoires (K052, C26) ?
2. **Y5**
   - 2a. Un modèle publié nommé (références llm) compte-t-il comme origine déclarée ? Les lecteurs se partagent ; voir le tableau (d).
   - 2b. « Bibliothèque avec sa version » s'applique-t-il aussi à un dépôt GitHub ou à un cadre comme OpenAI Baselines, verl ou OpenRLHF ? La plupart des codes `yes` n'ont pas de version ; C117 a été codé `no` pour cette seule raison.
   - 2c. Nommer le cadre dans lequel tourne la méthode des auteurs identifie-t-il le code des références (catégorie f) ?
   - 2d. Sources mêlées sans correspondance par référence (« from official reports or our own testing »).
   - 2e. Une réimplémentation implicite (« all methods in the same codebase », « same TD3 for all », « our implementation is NumPy only ») vaut-elle « réimplémenté par nous » ?
3. **Y3**
   - 3a. RL en contexte ou méta-RL : une seule exécution de méta-entraînement, puis un apprentissage par tâche au moment du test (K055 ; comparer avec C210, C219, NER02, qui s'entraînent par distribution).
   - 3b. Les conditions d'entraînement présentes seulement en annexe comptent-elles (K077 TOFU, C119 « App. G ») ?
4. **Q5.** Une page de projet dont la phrase promet du code (C19, C120, K038, K056) attend encore la vérification du lien que l'écart 6 renvoie à « l'analyse ». La règle ne dit ni qui vérifie, ni quand, ni que faire si la page a disparu. Elle ne mentionne pas non plus les miroirs anonymes (K090).
5. **Critères v1**
   - 5a. X7 : le calcul consacré seulement à l'évaluation, à l'inférence ou à la vérification compte-t-il (C33, C220, K016) ?
   - 5b. X7 : les durées vagues (« multiple days », K110) ou les durées relatives (« 0.78× SAC », K021) comptent-elles ?
   - 5c. X3 : abandonner des graines aléatoires ratées ou mauvaises compte-t-il comme sélection du meilleur essai (K072, C34) ? Une sélection inscrite dans la définition d'une référence compte-t-elle (C35) ?
6. **Y6**
   - 6a. Le filtrage ou la curation du jeu de données d'*entraînement* compte-t-il comme exclusion déclarée ? 15 codes `yes` reposent dessus.
7. **Y7**
   - 7a. Un nom de banc figé ou un nom de partition sans version ni date (XLRS-Bench, « MathVista testmini », « FHIR-AgentBench validation », FLASK, GenEval) se range-t-il avec MATH-500 (yes) ou avec MATH (no) ? Les lecteurs appliquent « par analogie avec MATH-500 » dans des sens opposés, parfois au sein d'un même lecteur (K1 : K014 `yes` contre K004/K006 `no`).
   - 7b. Un environnement que les auteurs définissent entièrement dans l'article (paramètres LQ de K072, puddle world modifié de C115).
8. **Y8**
   - 8a. Pour les llm, « generalization » ou « generalize beyond » comptent-ils comme « présenté comme un test hors distribution », ou seulement les mots out-of-distribution/out-of-domain ?
   - 8b. Une partition de test réservée i.i.d. (instances ou tâches inédites tirées de la distribution d'entraînement) compte-t-elle ? La règle nomme « autres graines d'environnement annoncées comme telles », qui sont i.i.d. ; pourtant les partitions de test des llm et des jeux de données ont été codées `no`.
9. **Y9**
   - 9a. Les paramètres d'inférence ou du moment du test (images, longueur de contexte, largeur de faisceau, pas au moment du test) et les conditions d'environnement (budget d'attaque) comptent-ils comme hyperparamètres ?
   - 9b. Le résultat montré doit-il être la mesure de performance principale, ou toute métrique compte-t-elle (entropie de LR07) ?
10. **Entre les tours.** Quand un code v2 (Y8) contredit le code v1 du même article (Q7) dans un sens que les règles interdisent (Y8 yes, Q7 no : C12, ML07), lequel recode-t-on ? L'écart 15 garde les lectures brutes pour l'accord, mais rien ne couvre l'incohérence entre v1 et v2.

## ML13, relu par le responsable du projet (10 novembre 2026)

Le lecteur C2 avait écrit ML13 après une interruption, sans relecture. Relu contre le PDF (`pdftotext`) : aucun
code ne change. Y1 `yes` (TSR défini par l'équation 8, mesuré sur le modèle entraîné, règle de l'écart 19) ; Y3 = 1
(un seul jeu d'entraînement procédural, T1 à T7 ; les bancs Cello et Literature-91 sont des évaluations, écart 17) ;
Y5 `yes` (les références tournent dans le cadre des auteurs, modèles publiés nommés) ; Y7 `no` (données « sur
demande », non publiées) ; Q5 `no` (aucun lien vers du code dans l'article). `check_codes.py` : aucune erreur.
La section Y1 ci-dessus proposait `yes -> no` pour ML13 au titre de l'é17. La règle de l'écart 19, écrite après cet
audit, tranche dans l'autre sens : l'article donne la durée d'entraînement (3 époques, 30 200 pas de GRPO) et un seul
TSR pour le modèle entraîné, ce qui vaut le point final. Aucune correction n'a été écrite : le `yes` du lecteur tient.
ML13 est un article `llm` : il ne compte pas dans la comparaison principale.
