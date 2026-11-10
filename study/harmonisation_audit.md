*Version française : [harmonisation_audit-fr.md](harmonisation_audit-fr.md).*

# Harmonisation audit of the raw v2 readings (before any percentage)

Scope: every JSON in `codes_v2/{A2,B2,C2,D2,E2,F2,H1,H2,H3,H4,K1..K7}/` (170 files; G2, R2 and pilot skipped).
Rules applied: `GRILLE.md`, `PROTOCOL.md` écarts 1–6, 14, 17, 18. For files with only Y1–Y12, the v1 values
used for the scope rules (Q1, Q4, X2, X5) were read from `codes/` (first reader, not G).
No share or count of `yes` per criterion, year or sample was computed. Context was checked with
`pdftotext` where a flag depended on it; "no point found" means a search of the full text for
final/last/best/converged/end of training/after N steps found nothing that applies to the main tables.

Format: `paper (reader): current -> proposed — rule — quote or reason`.

---

## Y1 — measure AND point of measurement (écart 17)

### Y1 `yes` whose quote gives no point of measurement (proposed `no`)

- LR02 (A2): yes -> no — é17 — "Attack Success Rate (ASR) and Benign Return (BR) ... defined below"; no checkpoint stated.
- LR05 (A2): yes -> no — é17 — "the reported metric is the mean of this indicator over the evaluation videos"; checkpoint not said.
- LR13 (B2): yes -> no — é17 — "We employ the sub em score for all benchmarks"; metric only.
- LR16 (B2): yes -> no — é17 — "we adopt LLM as judges for correctness evaluation"; metric only.
- LR17 (B2): yes -> no — é17 — "we use accuracy as both the evaluation metric and the reinforcement learning reward signal"; "accuracy" alone is the textbook `no` case of é14.
- ML01 (B2): yes -> no — é17 — "zero-shot setting, ... temperature set to 0"; decoding settings, not a point.
- ML03 (B2): yes -> no — é17 — "we compute PSNR and SSIM in non-edit regions"; metric only.
- ML07 (C2): yes -> no — é17 — "Detection performance (F1 score, %)"; metric only.
- ML08 (C2): yes -> no — é17 — "average success rate over 50 evaluation episodes per task"; number of episodes is explicitly not the point.
- ML12 (C2): yes -> no — é17 — "Accuracy is reported ... final average performance is calculated by first averaging ... ID, OOD"; "final" means the aggregate, not the checkpoint.
- ML13 (C2): yes -> no — é17 — "we use greedy decoding (temperature = 0)"; decoding only ("final performance" appears only in an appendix ablation).
- NER04 (E2): yes -> no — é17 — reward definition and sampling temperatures; no point.
- C117 (H1): yes -> no — é17 — "Accumulated Reward (AR) and Episode Length (EL) of each episode are calculated"; no checkpoint.
- C32 (H1): yes -> no — é17 — "Top-1 Generalization Accuracy ... of the most likely program"; no checkpoint.
- C38 (H3): yes -> no — é17 — "For each of the 50 total test mazes we ran 100 episodes ... and averaged"; no checkpoint.
- K002 (K1): yes -> no — é17 — "Accall(τ) is the percentage of all outputs that satisfy ..."; no point.
- K004 (K1): yes -> no — é17 — "average accuracy@8 at an inference temperature of 1.0"; no checkpoint for main table.
- K014 (K1): yes -> no — é17 — "HPSv3 ... and ImageReward ... as in-domain and out-of-domain evaluation metrics"; metric only.
- K016 (K1): yes -> no — é17 — "Time in Range (TIR). The percentage of time blood glucose remains within ..."; metric only.
- K044 (K3): yes -> no — é17 — LC win rate, WR, MT-Bench score, strict accuracy; no checkpoint.
- K052 (K3): yes -> no — é17 — "FR measures the ratio ... FT records the time ..."; no checkpoint of the trained policy.
- K059 (K4): yes -> no — é17 — "we report mean AUROC"; no point.
- K061 (K4): yes -> no — é17 — "weighted average of the F1-scores"; no point.
- K063 (K4): yes -> no — é17 — "each teammate instance is evaluated over 100 episodes; a per-instance mean return"; no checkpoint.
- K067 (K4): yes -> no — é17 — "completion accuracy ... for a single generated completion"; no checkpoint.
- K068 (K5): yes -> no — é17 — "report pass@1 using non-zero temperature"; no checkpoint.
- K075 (K5): yes -> no — é17 — "final evaluation score ... average speedup ratio across all execution rounds"; "final" is the aggregate, not the checkpoint.
- K077 (K5): yes -> no — é17 — "ROUGE-L Recall ... Measures the longest common subsequence overlap"; metric only.
- K078 (K5): yes -> no — é17 — "Reward (average episode return over 10 runs)"; "Return" sans plus.
- K106 (K7): yes -> no — é17 — "Pass@1 as the average accuracy across K generated samples"; no checkpoint.
- K110 (K7): yes -> no — é17 — "speedup of the fastest kernel (within the trajectory)"; no checkpoint.

Weaker cases (quote is off-target or the metric is not a trained-policy score; decide with gap 1c):
- C19 (H3): yes -> no? — é17 — per-evaluation discounted return; only the curve, no point for the reported numbers.
- C220 (H2): yes -> no? — é17 — the quote concerns the oracle's reward, not how the method's number is measured.
- C26 (F2): yes -> no? — é17 — "optimality gap ... normalized"; no checkpoint.
- C22 (F2): yes -> no? — é17 — KS test on samples; no checkpoint.

### Y1 `no` where the paper does give the point

- K089 (K6): no -> yes — é17 lists "aire sous la courbe" — "Results are averaged over 1M training steps in MuJoCo tasks" is a mean over training (an AUC-type point).
- ML16 (C2): no -> yes only if gap 1b is answered "training length = final" — "we run 500K steps training for all baselines ... averaging results over 4 seeds".

### Cross-reader divergences that the rule does not settle (see gaps 1a–1c)

- Learning curves as the point. Coded `yes` on a curve alone: LR04, LR11, C12, C16, C17, C24, C35, C113, C118, C120, C211, C212, C34, K003, K015, K072. Coded `no` on a curve alone: ML14 (C2), C111 (H2), C112 (H3), C121 (H3), C210 (H1), K090 (K6), K030 (K2), NER06 (E2).
- Training length as an implicit "final" point. D2 accepts "trained for N steps" as the point: MLR02, MLR03, MLR07, NE04, NE05, NE06 coded `yes`; NE02, NE08 coded `no` for lacking it. Other readers (B2, C2, K*) coded `yes` with no point at all (list above), and E2/K* coded `no` when a table's checkpoint was unstated (NER01, NER06, K056, K111, K113, K103).

---

## Y5 — origin of baseline code (écarts 14 and 17): classification, no proposals

Q4 `na` ⇔ Y5 `na` holds in every file. "Each?" is `no` when the reader's own quote or doubt says that
at least one main baseline has no stated origin (the é14 rule says "pour chaque référence principale").

### (a) Repository or library named for the baselines

| paper (reader) | Y5 | basis | each? |
|---|---|---|---|
| LR03 (A2) | yes | ODRL benchmark, OfflineRL-kit, REAG description | yes |
| NE10 (E2) | yes | two GitHub URLs (zero-shot-rl, HILP) | yes |
| NE15 (E2) | yes | OpenRLHF + "official code in RLHFlow" for RRM | yes |
| C11 (F2) | yes | "specialized systems ... (OpenAI, 2017; Hesse)" | yes |
| C14 (F2) | yes | Gurobi 7.5 (with version) | yes |
| C15 (F2) | yes | OpenAI Baselines (no version) | yes |
| C22 (F2) | yes | "we are using the open source codes" (no repo named) | yes |
| C26 (F2) | yes | or-tools URL | yes |
| C39 (H1) | yes | OpenAI Baselines | yes |
| C113 (H2) | yes | rllab | yes |
| C119 (H2) | yes | authors' own GitHub (UCRL baseline inside) | yes |
| C18 (H2) | yes | OpenAI baselines repo, SAC author GitHub, own DDPG | yes |
| C33 (H2) | yes | released implementations + own DistMult + reported numbers | yes |
| C19 (H3) | yes | OpenAI Baselines PPO | yes |
| C110 (H4) | yes | Henderson's fork of OpenAI Baselines | yes |
| K012 (K1) | yes | Craftax implementation, PQN defaults from [79] | yes |
| K030 (K2) | yes | CleanRL codebase for all baselines | yes |
| K038 (K2) | yes | JaxGCRL codebase | yes |
| K045 (K3) | yes | DreamerV3 PyTorch reimplementation, official Simulus | yes |
| K052 (K3) | yes | SCIP v8.1.0 + authors' released code | yes |
| K059 (K4) | yes | official GitHub / SDV library per baseline | yes |
| K066 (K4) | yes | fork of authors' repository | yes |
| K077 (K5) | yes | RWKU benchmarking framework | yes |
| K079 (K5) | yes | CORL URL | yes |
| K082 (K5) | yes | official implementations or Syntheseus | yes |
| K089 (K6) | yes | official RPP implementation | ? (other baselines not in quote) |
| K102 (K7) | yes | public PyTorch repos for each baseline | yes |
| K105 (K7) | yes | authors' code with commit hash | yes |
| K107 (K7) | yes | official DreamerV3 URL | yes |
| ML16 (C2) | yes | FQL and Value Flows implementations | yes |
| K096 (K6) | yes | ∗ official repo, † numbers from SPICE (mixed a/c) | yes |
| C17 (H1) | no | OpenAI Baselines for Double DQN; HRL baselines no origin | no |
| C210 (H1) | no | rllab + MAML code; RL2 and VIME no origin | no |
| C114 (H3) | no | Baselines TRPO/DDPG, SAC/Soft-Q repos; SVPG no origin | no |
| C116 (H4) | no | DQfD code, public DDPG; TRPO and GAIL no origin | no |
| C117 (H1) | no | OpenCV and Dlib, no version (reader applied "library with its version") | yes |
| K016 (K1) | no | OmniSafe defaults for critic architecture only | no |
| K043 (K3) | no | RLKit for actor-critic only; Atari baselines unidentified | no |
| K060 (K4) | no | RLeXplore, no version; ReAct no origin | no |
| K095 (K6) | no | CleanRL for PPO; NPG, Q-learning, TS, UCB no origin | no |
| K015 (K1) | no | "the corresponding reference implementation" (unnamed) | ? |
| K073 (K5) | no | "IQL default config in get config" (repo not named) | ? |

Note: C117 (no, library without version) and C15/C19/C39/C113 (yes, library or repo without version) apply
"bibliothèque avec sa version" differently. Only C14, K052 and K105 give a version or commit.

### (b) "Reimplemented"/"implemented by us" said

| paper (reader) | Y5 | basis | each? |
|---|---|---|---|
| LR17 (B2) | yes | "we implemented a Textual RL baseline" | ? (one baseline named) |
| ML01 (B2) | yes | "we reproduce several training methodologies" | yes |
| ML11 (C2) | yes | "All methods are implemented within the same codebase" | yes |
| NE12 (E2) | yes | "we implement previous solutions within the RDC framework" | yes |
| C112 (H3) | yes | "We adapt the model of He et al." | yes |
| C120 (H4) | yes | "In our implementation of this method" | yes |
| C212 (H4) | yes | "All baselines ... were re-implementations" | yes |
| C214 (H3) | yes | "we have implemented and run the policy gradient method" | yes |
| C34 (H4) | yes | acknowledgement: colleagues "implementing DDPG" | ? |
| K006 (K1) | yes | "We implemented Semdedup"; other baselines are datasets | yes |
| K037 (K2) | yes | "we reproduce their method on Qwen2.5-VL-3B" | yes |
| K054 (K3) | yes | "we implement our ... and baseline attack algorithms" | yes |
| K075 (K5) | yes | "We implement evolutionary LLM strategies" | yes |
| K083 (K6) | yes | all methods "share the same ... framework written in JAX" | yes |
| K113 (K7) | yes | "we implement CQL ... based on DDPG" | yes |
| K063 (K4) | yes | "Our implementations are built entirely in JAX and Flax" (doubt: AD and DPT reimplemented, AMAGO adapted) | ? |
| K039 (K2) | yes | baselines "tested using the same iterative RAG workflow" | no (doubt: R1-Searcher, DeepResearcher origin not said) |
| MLR02 (D2) | no | JEPO reimplemented, others copied with source, RAFT/TRACT "own runs" | no |
| K069 (K5) | no | Feedback Descent reimplemented; GRPO unidentified | no |
| K056 (K3) | no | "we run all baselines ourselves" (no code origin) | ? |

### (c) Numbers copied from published papers with the source

| paper (reader) | Y5 | basis | each? |
|---|---|---|---|
| LR14 (B2) | yes | "Baseline results are directly cited from Ye et al." | yes |
| ML15 (C2) | yes | "we adopted the same results from the previous works (Ding & Jin; Park)", no mapping per baseline | ? |
| K017 (K1) | yes | MOBILE Table 1 for CQL/EDAC/MOPO, others from original papers | yes |
| K028 (K2) | yes | † Deshpande et al., ‡ Li et al. | yes |
| K064 (K4) | yes | "report results from their official publications or recommended evaluation settings" | ? (no per-baseline source) |
| K067 (K4) | yes | "When available, we use baseline results reported in prior work" | ? ("when available") |
| C218 (H1) | yes | values reported by Rajeswaran, Salimans, Schulman, Haarnoja | yes |
| NE04 (D2) | no | "reported performance" without per-number source + "evaluated by us" | no |
| NE06 (D2) | no | closed models from a public benchmark site; Logic-RL etc. no origin | no |
| K068 (K5) | no | "sourced from their official release report or ... independent testing", without saying which | no |

### (d) Published model named or cited, evaluated by the authors (mostly `llm`)

| paper (reader) | Y5 | basis | each? |
|---|---|---|---|
| LR07 (A2) | yes | 1.5B models named exactly, no link; plus authors' own DAPO run | yes (by name) |
| LR10 (A2) | yes | Qwen 3 32B, Llama 3.3 70B, DeepSeek Coder v2 Lite, Sonnet 4, no checkpoint source | yes (by name) |
| LR13 (B2) | yes | DeepSeek-R1-Distill-Qwen, Qwen-2.5-Instruct(-1M), QwenLong-L1 cited | yes (by name) |
| LR16 (B2) | yes | Qwen2.5/Qwen3 instruct checkpoints, SFT by authors | yes (by name) |
| MLR07 (D2) | yes | "official APIs", "publicly released checkpoints", DeepEyes | yes |
| ML13 (C2) | yes | authors' own SFT/RLVF variants + prompted proprietary model | yes |
| K061 (K4) | yes | released base model + authors' own finetuned variants (implicit) | yes |
| K065 (K4) | yes | API models in authors' harness; o4-mini also copied from Lee et al. | yes |
| NER01 (E2) | yes | GRPO in verl + DeepSeek-R1-Zero figure with source | yes |
| K004 (K1) | no | "Our reproduction uses official author-provided prompts"; PAPO-D copied without source | no |
| (also NE04, MLR02, K068 above: own re-evaluation of named models coded `no`) | | | |

This is the llm split the lead mentioned: named published models evaluated by the authors are `yes` for
A2, B2, D2 (MLR07), C2, K4, E2, and `no` for D2 (NE04, MLR02), K1 (K004), K5 (K068).

### (e) Implicit (never said) reimplementation or no origin

| paper (reader) | Y5 | basis | each? |
|---|---|---|---|
| LR04 (A2) | yes | "In our codebase ..." — doubt: recipes reimplemented "not said in so many words" | no (implicit) |
| LR11 (B2) | yes | "implementation ... using only NumPy and Matplotlib" (CVaR-Q implicitly reimplemented) | implicit |
| ML14 (C2) | yes | train-then-fix baseline = own checkpoints (own variant) | implicit |
| C31 (H4) | yes | "We perform pruning based on Molchanov et al." | implicit |
| K085 (K6) | yes | CleanRL for PQN; GNS "seems reimplemented, never said" | no |
| LR02 (A2) | no | "We extend TrojDRL and SleeperNets to continuous action space" | implicit |
| LR09 (A2) | no | same MLP architecture for all baselines | implicit |
| NE05 (D2) | no | "All baseline models are trained ... under the consistent dataset" | implicit |
| MLR03 (D2) | no | "follow its original training setting" | implicit |
| MLR06 (D2) | no | estimators cited, code not said | implicit |
| ML12 (C2) | no | detectors "trained on our dataset using their original preprocessing" | implicit |
| C215 (H3) | no | "PPO uses the same hyper parameters with its original paper" | implicit |
| C216 (H1) | no | baselines trained with the same TD3 | implicit |
| C32 (H1) | no | MLE baseline "similar to" Devlin et al. | implicit |
| C220 (H2) | no | "we compare VIPER to fitted Q iteration" | implicit |
| C217 (H2) | no | mlCoP "previous reimplementation [23]" (the prover's base, not the baselines) | ? |
| C213 (H1) | no | MTMLIRL code in BURLAP tried, main baselines no origin | no |
| K021 (K1) | no | CleanRL hyperparameters, "implementations standardized" | implicit |
| K032 (K2) | no | GRPO, GRESO, CPPO cited as algorithms | implicit |
| K042 (K2) | no | Stream Q(λ), QRC(λ), streaming DQN cited | implicit |
| K072 (K5) | no | "Algorithm 3 in [...]" | implicit |
| K081 (K5) | no | SIL and PPO "seem reimplemented in the Julia pipeline, never said" | implicit |
| K090 (K6) | no | RPO FS "follows" Mandal et al. | implicit |

### (f) Framework of the authors' own training named (baseline origin follows only if all runs use it)

| paper (reader) | Y5 | basis | each? |
|---|---|---|---|
| LR08 (A2) | yes | "We base our experiments on the verl repository" — doubt: BAPO and GPG origin not said | no |
| K062 (K4) | yes | "Our method and all baselines are implemented on top of VeRL" | yes |
| K106 (K7) | yes | verl for all algorithms — doubt: NSR has no origin | no |
| K110 (K7) | yes | "built our training framework on top of OpenRLHF"; o4-mini/o3-mini by name | ? |
| K044 (K3) | no | "We adopt the OpenRLHF framework" — baseline rewards not identified | no |

Contradictions with "chaque" among `yes` codes (reader's own doubt names an unidentified baseline):
LR04, LR08, K039, K085, K106. Same basis, opposite codes: (f) K110/K106/LR08 `yes` vs K044 `no`;
(a) C15/C19/C39 `yes` vs C117 `no`; (c)+(d) K064 `yes` vs K068 `no`.

---

## Y3 — number of training settings (écart 17); only 1 vs ≥2 crossings

- K036 (K2): 2 -> 1 — é17 (one training setting) — "During training, we jointly optimize two tasks: score regression and degradation perception"; one joint training run on one dataset (DQ-495K subset). Y4 then -> na.
- K103 (K7): 2 -> 1 — é17 (main conclusion) — main results come from training in the simulated GUI environment; the second "setting" is a continual-training add-on ("we continue training our agents ... with 24k samples"), reported in a secondary table. Y4 then -> na.
- K055 (K3): 8 -> 1 under a strict reading — é17 ("plusieurs bancs d'évaluation d'un même modèle entraîné ne multiplient pas les tâches") — OmniRL is meta-trained once on AnyMDP; "Gymnasium, DarkRoom, and Bandits tasks are entirely absent from OmniRL's training regimen". In-context RL learns per task at test time, so see gap 3a. Y4 would follow.

Checked and not crossing: LR08 (math and code training sets, ≥2 although 4 counts model families), LR10 (MBPP-X and CF-X training sets), LR17 (OmniMedVQA and VQA-RAD+SLAKE training sets; quote shows only one), K062 (GURU and Dolphin preference set), K014, K032, NE15, NER04, ML07 (leave-one-domain-out gives distinct training sets), ML06 (Overcooked levels = difficulty, 1 is right), K051 (degrees as levels, 1 is right), K110 (Level 1 + Level 2, 1 is right), K077 (TOFU only in appendix B.1, 1 is right if appendix-only experiments do not count; see gap 3b).

---

## Q5 / écart 6 — project pages and "will be released"

"Will be released" coded `yes`: none. (K035, K036, K039, K043, K077, K106, C32 are all `no`, as the rule says.)

Project page, Google Sites, github.io or anonymous page coded `yes`:

| paper (reader) | link | does the paper say the page holds code? | proposal |
|---|---|---|---|
| C19 (H3) | sites.google.com/view/time-limits-in-rl | yes: "The source code and videos can be found at" | keep yes if the link leads to code (é6 check) |
| C120 (H4) | sites.google.com/view/goalgeneration4rl | yes: "Videos and code available at" | keep yes if the link leads to code |
| K038 (K2) | wang-kevin3290.github.io/scaling-crl | yes: "The project webpage and code can be found here" (single link to the page) | keep yes if the link leads to code |
| K056 (K3) | kaifukazawa.github.io/ramac-project (hyperlink) | yes: "The code and experimental results are available on the project website" | keep yes if the link leads to code |
| K064 (K4) | tiger-ai-lab.github.io/Critique-Coder (bare URL under the authors) | no: no sentence about code | yes -> no unless the page is checked and leads to code (é6); consistent with K069 and K089, which readers coded `no` for project pages without a code statement |
| K090 (K6) | anonymous.4open.science/r/PePG-0C27 | yes: "Code of PePG is available in Link" | an anonymised code mirror, not a project page; yes is fine, but the link may have expired |

Project pages coded `no` (videos only, consistent): C210, C216, C114, C34, K069, K089, K107; C27 (video only), C217 (dataset only).

---

## v1 criteria on the v1+v2 files (C1*, C2*, C3*, K*)

### X4 (écart 1)
- C210 (H1): no -> yes — é1 (tuning described for the baselines) — appendix: "We describe the hyper-parameters swept over for gradient based meta-learning methods ... for MAESN, latentspace baseline and MAML ... For each method, we selected hyperparameters which gave best train time performance".
- Borderline, not flagged: K111 (K7) no ("λUCB is a hyperparameter we tune for each method", with no description of the tuning); C121 (H3) yes (population-based training for all agents, baselines included, inferred from the figure caption); C39 (H1) yes (learning rate tuned with DQN, the baseline, then shared).
- Q4 `na` ⇔ X4 `na` holds everywhere.

### X7 (écart 2)
No contradictions. Every `yes` has a quantity. Hardware-only `no` (C121, C210, C114, C214, K014, K015, K023, K037, K043, K049, K056, K061, K078, K084, K089, K102, K106) is consistent. C212 `yes` is supported by Figure 5 (wall-clock hours). See gaps 5a–5b for inference-only timings and vague durations.

### X3 (écart 5)
No clear contradictions. Cases to settle by rule (gap 5c): C35 (H3) yes (the selection is part of the *baseline's* definition, "selects the policy with the maximum performance"); K072 (K5) yes and C34 (H4) yes (dropping poor or unsolved seeds counted as best-run selection); C33 (H2) no ("We found it easy to obtain/reproduce the highest scores across several runs" may mean best of N).

### Q7 (écart 4)
Every `theory` paper with toy experiments is `no` (C111, C119, C29, K003, K023, K090, K098, K099); C28 and K109 are `na` with Q1 `no`. No contradiction. K028 (K2) yes rests on a "validation set" figure; the main table is on the "official C-STS benchmark". This is not a clear contradiction.

---

## Y7 — version of EACH main environment/benchmark (écart 14, 17 "chaque" strict)

`yes` contradicting the rule:
- LR08 (A2): yes -> no — é17 (an authors' split counts only if published) — DAPO-Eval is built by the authors; the reader notes the text says "will release". The quote is the project-page URL.
- LR10 (A2): yes -> no — "chaque" — the reader's doubt says "MultiPL-E n'a pas de numéro de version".
- K106 (K7): yes -> no — "chaque" — "Minerva Math" has no version or split. The same list (AIME 2024/2025, AMC 2023, MATH500, Minerva, Olympiad) is coded `no` in LR07 (A2).
- K037 (K2): yes -> no — "MATH seul : no" analogue — "VSI-Bench, VideoMMMU, MMVU, MVBench, TempCompass, and VideoMME" are named only. Compare K004 and K006 (K1), coded `no` on the same kind of list.
- K014 (K1): yes -> no — GenEval and DPG are named without version. The same reader coded K004 `no` on names alone.
- MLR02 (D2): yes -> no — "chaque" — the reader's doubt says "FLASK, Vicuna Bench et MT Bench ... sans version ni lien, codé yes par analogie avec MATH-500".

Depend on gap 7a (a named split without a version or date):
- NE02 (D2) yes and NE08 (D2) yes: split names only (test, val, testmini).
- MLR07 (D2) yes: "XLRS-Bench" name only.
- K065 (K4) yes: "FHIR-AgentBench validation set (424)".
- K072 (K5) yes: an authors' LQ environment fully specified by its parameters (gap 7b).

---

## Y9 — only what the paper presents as a hyperparameter (écart 17)

- LR07 (A2): yes -> no — é14/é17 (a component ablation is not a sweep) — "Adding uncertainty weighting (λ2 = 0.4) increases exploration diversity" is on versus off. The reader's doubt also says the sweep shows only search metrics, not the final score.
- Depend on gap 9a (inference-time or environment parameters): LR14 (B2) yes (MAX_NUM_FRAMES varied at inference); K068 (K5) yes (context length and number of tool calls at inference); C24 (F2) yes (test-time training steps U); C26 (F2) yes (beam width); K095 (K6) yes (attack budget B, which the reader suspects is an environment condition).

---

## Y6 — exclusions (écart 17)

No `yes`/`no` code contradicts the written text. One divergence the rule does not decide (gap 6a): filtering of the *training* data is counted as a stated exclusion in LR05, LR07, LR13, LR14, LR16, LR17, ML03, ML07, ML12, ML13, K044, K061, K063, K064 and K073. All other `yes` codes concern evaluation runs, seeds, tasks or omitted combinations, which écart 17 explicitly covers. K072 (K5) `no` ("removing extremely poor results", without saying which) is consistent with "dit quels essais".

---

## Y8 — generalisation beyond training conditions (stricter than Q7)

- K082 (K5): yes -> no — é14 (a different benchmark counts only if presented as a held-out or shifted condition) — "We evaluate performance on three benchmarks of increasing difficulty: Retro*-190 ...". These are standard test sets, not presented as generalisation.
- C12 (F2) Y8 yes with v1 Q7 `no` (codes/): Y8 is stricter than Q7, so this pair is internally contradictory. Y8 looks right ("we introduced a small change to the environment: ... teleport"), which makes v1 Q7 the suspect. ML07 (C2) shows the same pattern: Y8 yes (leave-one-domain-out), v1 Q7 `no`.
- Depend on gap 8a (llm benchmark called "generalization" but not "out-of-distribution"): LR10 (A2) yes, K044 (K3) yes, K096 (K6) yes, ML03 (B2) yes.
- Depend on gap 8b (i.i.d. held-out test split or instances): coded `yes` K081 (K5), C219 (H4), K086 (K6, a validation environment with a new seed); coded `no` K110 (K7, "100 unseen KernelBench tasks"), C32 (H1), C33 (H2), C114 (H3), NER04 (E2), K049 (K3).

---

## Scope consistency

Checked mechanically on all 170 files:
- Y2 and Y11 are `na` if and only if X2 = no.
- Y4 is `na` if and only if Y3 = 1.
- Y5 is `na` if and only if Q4 = na.
- Q4 `na` ⇔ X4 `na`.
- Q1 = no gives all Y `na`, and all v1 Q2–X7 `na` for the new papers.
- Y11 = yes always carries a `kind`.

No violation. The only scope changes come from the proposed Y3 recodes: K036, K103 and K055 would need Y4 -> na.

---

## Rule gaps (cases no written rule decides)

1. **Y1**
   - 1a. Is a learning curve (performance against steps) a point of measurement? Readers split: 16 `yes` against 8 `no`, listed above.
   - 1b. Does stating the training length ("trained for N steps/1 epoch") imply that the reported number is the final checkpoint? D2 says yes; most other readers neither asked for it nor used it.
   - 1c. What is the "point" for metrics that are not a trained policy's score: estimator error (MLR06, C25), compute time (C14), KS tests (C22), combinatorial solvers (K052, C26)?
2. **Y5**
   - 2a. Does a named published model (llm baselines) count as a stated origin? Readers split; see table (d).
   - 2b. Does "library with its version" also apply to a GitHub repo or a framework such as OpenAI Baselines, verl or OpenRLHF? Most `yes` codes have no version; C117 was coded `no` for exactly that.
   - 2c. Does naming the framework the authors' own method runs in identify the baselines' code (category f)?
   - 2d. Mixed sources without a per-baseline mapping ("from official reports or our own testing").
   - 2e. Is an implicit reimplementation ("all methods in the same codebase", "same TD3 for all", "our implementation is NumPy only") a "réimplémenté par nous"?
3. **Y3**
   - 3a. In-context or meta-RL: one meta-training run, then learning per task at test time (K055; compare C210, C219, NER02, which train per distribution).
   - 3b. Do appendix-only training settings count (K077 TOFU, C119 "App. G")?
4. **Q5.** A project page whose sentence promises code (C19, C120, K038, K056) still needs the link check that écart 6 defers to "the analysis". The rule does not say who checks or when, or what to do if the page is gone. Anonymous mirrors (K090) are not mentioned either.
5. **v1 criteria**
   - 5a. X7: does compute for evaluation, inference or verification only count (C33, C220, K016)?
   - 5b. X7: do vague durations count ("multiple days", K110) or relative timings ("0.78× SAC", K021)?
   - 5c. X3: does dropping failed or poor seeds count as best-run selection (K072, C34)? Does a selection built into a baseline's definition count (C35)?
6. **Y6**
   - 6a. Does filtering or curating the *training* dataset count as a stated exclusion? 15 `yes` codes rest on it.
7. **Y7**
   - 7a. Is a fixed benchmark name or a split name without version or date (XLRS-Bench, "MathVista testmini", "FHIR-AgentBench validation", FLASK, GenEval) like MATH-500 (yes) or like MATH (no)? Readers apply "par analogie avec MATH-500" in opposite directions, sometimes within one reader (K1: K014 `yes` against K004/K006 `no`).
   - 7b. An environment the authors define completely in the paper (K072 LQ parameters, C115 modified puddle world).
8. **Y8**
   - 8a. For llm, does "generalization" or "generalize beyond" count as "présenté comme un test hors distribution", or only the words out-of-distribution/out-of-domain?
   - 8b. Does an i.i.d. held-out test split (unseen instances or tasks from the training distribution) count? The rule names "autres graines d'environnement annoncées comme telles", which is i.i.d., yet llm/dataset test splits were coded `no`.
9. **Y9**
   - 9a. Do inference-time or test-time parameters (frames, context length, beam width, test-time steps) and environment conditions (attack budget) count as hyperparameters?
   - 9b. Must the result shown be the main performance measure, or does any metric count (LR07 entropy)?
10. **Cross-round.** When a v2 code (Y8) contradicts the v1 code of the same paper (Q7) in a direction the rules forbid (Y8 yes, Q7 no: C12, ML07), which one is recoded? Écart 15 keeps raw readings for agreement, but nothing covers v1 and v2 inconsistency.

## ML13, reread by the project lead (10 November 2026)

Reader C2 had written ML13 after an interruption, without rereading it. Reread against the PDF (`pdftotext`): no
code changes. Y1 `yes` (TSR defined by equation 8, measured on the trained model, the écart 19 rule); Y3 = 1
(a single procedural training set, T1 to T7; the Cello and Literature-91 benchmarks are evaluations, écart 17);
Y5 `yes` (the baselines run in the authors' framework, published models named); Y7 `no` (data "on
request", not published); Q5 `no` (no link to code in the paper). `check_codes.py`: no errors.
The Y1 section above proposed `yes -> no` for ML13 under é17. The écart 19 rule, written after this audit, settles it
the other way: the paper gives the training length (3 epochs, 30,200 GRPO steps) and one TSR for the trained
model, which counts as the final point. No override was written, so the reader's `yes` stands.
ML13 is an `llm` paper: it does not count in the main comparison.
