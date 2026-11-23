# Did We Listen to Joelle Pineau? Reinforcement Learning Papers of 2018 and 2026 Read with the Same Grid, Two Experiments Rerun

**Warith Harchaoui**, Deraison.ai, warithmetics@deraison.ai

Short version of the technical report *Reinforcement Learning: Did We Listen to Joelle Pineau in 2018?* (version 1.0,
24 November 2026). Every number below comes from a result file of the repository. `paper/check_short.py` ties
each one to its key. Code, data and protocols: the repository of the technical report, BSD 3-Clause licence for the
code.

## Abstract

In 2018, at ICLR and then at NeurIPS, Joelle Pineau showed why the published results of deep reinforcement learning
(RL) earned little trust. She surveyed 50 RL papers from 2018 and found that 55% linked their code and 5% applied a
significance test. Eight years later, we ask whether the practices she named have changed. We read 50 classical RL
papers from 2026 and 50 papers from 2018 with the same grids, the same decision rules and AI agents of the same model,
under a protocol written before the first reading. Four practices changed in a way that survives the Holm correction
for multiple tests. Linking the code rose from 31% to 74% (+43 points, [+23, +58]). Showing the sensitivity to a
hyperparameter rose from 44% to 80%, quantifying the compute from 27% to 58%, reporting an uncertainty from 63% to
88%. All four accompany the result. The tuning of baselines shows no sign of progress: papers that give all the
settings of their baselines go from 35% to 29%. The rise of error bars comes with no detectable rise of uncertainty
computed over independent random seeds (35% then 42%, [-12, +25]). Two experiments make the survey concrete. The
first explains the most famous figure of 2018, two groups of five runs of the same code with t = -9.09: a script
published in 2017, which tests the spread between episodes instead of the spread between random seeds, reaches that
value in 38% of random draws on our own TRPO runs and never on PPO. The second shows that a published tuning can age
with its software: the recipe of the RL Baselines3 Zoo for PPO on Hopper, applied today with the collection's own
script, produces a robot that stands still (median speed 0.00 m/s), while the agent the Zoo published in 2022 with the
same settings runs at 1.44 m/s under our protocol.

## 1. Introduction

In May 2018, Joelle Pineau gave an invited talk at ICLR in Vancouver on reproducibility, reusability and robustness in
deep RL. In December 2018, she gave an expanded version at NeurIPS in Montréal. Figure after figure, most of them from
the paper of her team signed by Peter Henderson and his coauthors, she showed what RL lacked to deserve trust. The
best algorithm changed from one simulated task to the next. Implementations of the same algorithm disagreed. Network
architecture, reward scale and activation function changed the ranking. Papers reported three or five runs, sometimes
the best three. The most famous slide showed two groups of five training runs of the same TRPO code, with the same
settings, whose learning curves looked like two algorithms. A test declared them different, with t = -9.09 and
p = 0.0016. At NeurIPS she added a survey: of 50 RL papers from 2018, 90% gave the hyperparameters of their method,
60% those of their baselines, 55% linked their code, 20% said how they chose their hyperparameters and 5% applied a
significance test. She proposed a reproducibility checklist, which NeurIPS adopted in 2019.

The question of this paper is whether the papers published since then changed the practices she named. We answer
with two instruments, each under a protocol written before its first use, with every later deviation dated and
marked as written before or after the result it concerns.

The first instrument is a survey. Its verdict rests on one comparison: 50 classical RL papers from 2026 (robotics,
games, control, language models excluded) against our own reading of 50 papers from 2018, with the same grids, the
same harmonised rules and agents of the same model. We reread 2018 ourselves because our grid does not read 2018 as
Pineau did. On the method's hyperparameters, our reading finds 55% where she counted 90%. Comparing 2026 to her
figures would mix a change of practice with a change of grid.

The second instrument reruns the experiments of 2018 with the algorithms of 2026. Of the experiments of the technical
report, we keep two here. B1 asks where the t of 9 comes from. E6 asks what happens when a baseline is run with its
published tuning. Both touch the survey directly: B1 shows that an error bar can satisfy a reading criterion while it
measures the wrong thing. E6 shows that a recipe can be published, followed to the letter and still fail.

Our contributions are three.

1. **A like-for-like survey.** Pineau's grid, completed with criteria from her ICLR talk and a second grid of twelve
   criteria written in advance, applied to 2018 and to 2026 by the same kind of reader. Four practices changed. The
   tuning of baselines did not. For most other criteria, the survey cannot decide. We say how large a change it
   could have seen.
2. **A probable explanation of the t of 9.** A script published by Henderson in 2017 reproduces the order of magnitude
   of the 2018 figure on our TRPO runs. The published pair (t, p) rules out the other ways of computing more than it
   designates this script.
3. **A published recipe that aged.** The Zoo's tuning of PPO on Hopper produced a running agent in 2022 and produces a
   standing one today. The failure is not ours: the collection's own training script reproduces it.

The technical report holds the rest: the trajectory of four intermediate years, the experiments on rankings across
tasks, on the best runs kept, on the number of random seeds, on modified physics, as well as a strand on language models
fine-tuned with GRPO.

### Related work

No work we found reapplies Pineau's grid to recent RL papers while calibrating it on 2018, nor reruns the protocol of
Henderson and his coauthors with the algorithms of 2026 under a protocol written in advance. Five groups of work come
close.

- **The 2018 experiment.** Henderson et al. ground most of the flaws Pineau showed: sensitivity to hyperparameters, to
  implementations, to random seeds and to tasks. Islam et al. preceded them on the same tasks.
- **Statistical method.** Colas et al. run a power analysis of the number of random seeds. Agarwal et al. contribute
  the interquartile mean, stratified bootstrap intervals and the probability of improvement. They show that several
  improvements claimed on Atari games dissolve once the intervals are computed. Patterson et al. turn these results
  into a guide. Eimer et al. call for an equal tuning budget for baselines. These works say what to do. Our survey
  measures whether papers do it.
- **Checklists.** Pineau et al. describe the NeurIPS 2019 reproducibility programme: the mandatory checklist, the
  reproducibility challenge and the code submission policy. The share of accepted papers with code rose from under
  50% to 74.4%.
- **Audits of the literature.** Gundersen and Kjensmo score 400 papers from IJCAI and AAAI on how they document
  methods, data and experiments. Coakley et al. track 56,800 papers from five AI conferences from 2014 to 2024: the
  share that releases code and data rises from 11% to 64%. The rise begins before the checklists. In RL, the
  closest audit covers 75 papers on cooperative multi-agent RL, of which about a third quantify no uncertainty
  (Gorsane et al.). None of these audits targets single-agent RL with the 2018 grid.
- **Language models.** Hochlehnert et al. find, on small reasoning benchmarks, standard deviations of 5 to 15 points
  from one sampling seed to the next. Shao et al. show that a random reward improves Qwen models in mathematics,
  with no such gain for Llama or OLMo. The flaws of 2018 come back in the newest strand of RL.

## 2. The survey: design

### 2.1 Samples

The main comparison uses two samples. For 2018, we read 50 RL papers from ICLR, ICML and NeurIPS 2018, the three
venues Pineau surveyed. For 2026, we read 50 classical RL papers from ICLR 2026, ICML 2026 and NeurIPS 2025. Of the
2018 papers, 48 have experiments. The criteria about experiments are computed on them. Pineau did not describe how
she drew her 50 papers. We therefore compare her figures with ours only as context. Both of our samples were drawn
before any of their papers was read, by a seeded shuffle of public lists of accepted papers filtered on the title.
The protocol fixed both samples on 9 November 2026, before any reading of the papers added to the first draw.

### 2.2 Grids

Each paper is read with three sets of criteria. Grid v1 holds Pineau's eight criteria (Q1 to Q8) and seven criteria
drawn from her ICLR talk (X1 to X7). Grid v2 holds twelve criteria for the flaws she showed without measuring them (Y1
to Y12): the measure of performance, the tasks, the implementations, the versions, the generalisation, the
sensitivity and the statistical tools published after 2018. Each criterion comes with decision rules for its limit
cases, written before any reading with that grid. Four criteria carry the verdicts that follow:

- **Q5, code linked**: the paper links to its own code. A dataset, a library by others, "available on request" or
  "will be released" count "no".
- **Y9, sensitivity shown**: at least one hyperparameter of the proposed method is swept and the resulting performance
  shown. An ablation that removes a component is not a sweep.
- **X7, compute quantified**: hours, GPU-hours, FLOP, or a number of GPUs with a duration. The name of the hardware
  alone counts "no".
- **X2, uncertainty reported**: the main results carry a measure of spread, of any kind.

### 2.3 Readers

AI agents read the papers. Each agent reads the whole paper, appendices included. Each "yes" quotes the exact sentence
of the paper and its page. A script then finds every quote in the text of the PDF and sends a file back to its reader
when a quote is missing. A "no" quotes nothing, which is why a later check confronts every "no" with the text
(Section 3.4). The instructions given to each agent are published word for word, together with the model each agent
ran on, reconstructed from the session transcripts. Every primary reader ran on one model, `claude-opus-5-5`, except
two that finished on a neighbouring model after a safety filter stopped one of their responses.

The double readings are made by copies of the same model. Their agreement measures how stable that model's reading
is, not the agreement between two independent readers. A blind human re-reading is preregistered (Section 6).

### 2.4 Checks built into the reading

Three checks ran before any percentage was computed.

- **The mechanical check.** A script checks each reading file before any count: the criteria present, the values
  allowed, the scope rules between criteria (a paper with no experiment is "not applicable" everywhere, an uncertainty
  criterion of grid v2 applies only when X2 is "yes"), then every quote. A quote is searched in the text of the PDF and
  of its supplement, on letters and digits only, so that spaces, hyphenation and ligatures do not count. A fragment not
  found as such passes if 90% of its characters appear in a window of the text. A file that fails goes back to its
  reader.
- **The audit of the first grid.** The first pass of this check on the files of grid v1 left 89 quotes not found. An
  audit agent checked each of them in the PDFs. None was invented. Most failures came from French comments added by a
  reader to an exact English quote, or from two-column layouts that the text extraction interleaves.
- **The pilot and the harmonisation.** A pilot of two papers read by every primary reader showed where the rules left
  room. The harmonisation that followed, applied to every paper of both years, is listed decision by decision, with
  who changed what and why.

### 2.5 Verdict rule and statistics

For each criterion, we compute the share of "yes" in each year with its Wilson interval, the gap with its Newcombe
interval and the p-value of Fisher's exact test. The Holm correction applies separately to the 11 criteria of grid v1
and to the 12 of grid v2. A criterion **changed** when its gap passes the 5% threshold after this correction. This
rule was decided after the first results, on 9 November 2026: the original rule also required a gap against Pineau's
figures. Our reading of 2018 departs from hers. The technical report gives what the original rule would have said
(it confirms no classical RL criterion and calls the code link "ambiguous").

## 3. The survey: results

Figure 1 (`report/figures/grille-egale-en.pdf`) draws the gaps for eight practices. Figure 2
(`report/figures/forest-criteres-en.pdf`) draws all the criteria.

### 3.1 Four practices changed

Four gaps pass the Holm correction.

| Criterion | 2018 | 2026 | Gap (points) | 95% interval | p (Holm) |
|---|---|---|---|---|---|
| Code linked (Q5) | 31% (15 of 48) | 74% (37 of 50) | +43 | [+23, +58] | 0.0004 |
| Sensitivity shown (Y9) | 44% (21 of 48) | 80% (40 of 50) | +36 | [+17, +52] | 0.004 |
| Compute quantified (X7) | 27% (13 of 48) | 58% (29 of 50) | +31 | [+11, +47] | 0.02 |
| Uncertainty reported (X2) | 63% (30 of 48) | 88% (44 of 50) | +26 | [+8, +41] | 0.04 |

A fifth criterion also passes: the use of neural networks (Q2), from 79% to 98% (+19 points, [+6, +32]). It describes
the population, not a flaw. Classical RL in 2026 is almost entirely deep RL, which it was not quite in 2018.

What the four have in common is that they accompany the result. A link, a figure of compute, a sweep, an error bar:
each can be added to a paper once the experiments are done. None of them changes how the experiments were designed.

### 3.2 An error bar over what?

X2 is "yes" as soon as a paper reports an uncertainty. Section 4 shows that a bar computed over the episodes of one
training run is precisely the computation that produces the t of 9. Such a bar satisfies X2. After the main results,
we therefore added an exploratory criterion, X8, written before any reading: is the reported uncertainty computed over
random seeds, that is, over independent training runs? Fresh agents, who had read no paper of the survey, read the
papers that are "yes" for X2. Each of them read papers from both years.

Among papers with experiments, X8 goes from 35% (17 of 48) to 42% (21 of 50): +7 points, [-12, +25], p = 0.54. Error
bars spread while their source changed in no detectable way. In 2026, 14 of the 44 papers that draw a bar do not say
what it is computed over (Figure 3, `report/figures/x2-x8-en.pdf`). X8 qualifies the X2 verdict without replacing it.

### 3.3 What did not change, what the survey cannot see

The tuning of baselines shows no sign of progress. Papers that give all the hyperparameters of their baselines (Q4)
go from 35% to 29%: -7 points, [-25, +11]. A new method still receives more care than the methods it claims to beat,
or at least more description.

For most other criteria, the survey cannot decide. Held-out evaluation (Q7) rises from 33% to 45%, the choice of
hyperparameters (Q6) from 26% to 48%, the method's hyperparameters (Q3) from 55% to 72%, the statistical test (Q8) from
6% to 12%. None of these gaps passes the correction. With about fifty papers per year, each Newcombe interval spans
twenty to forty points. Written before the repository's computation, a power analysis puts a number on it. Starting
from the 2018 share, Fisher's test detects a rise of Q7 with an 80% chance only if it reaches 29 points, 37 after the
Bonferroni correction. The rise actually seen had an 18% chance of being detected at the 5% level, 4% after
correction. "No detectable change" does not mean "no change".

The table below gives every criterion of grid v1 in the main comparison. The correction runs over these 11
criteria.

| Criterion | 2018 | 2026 | Gap (points) | 95% interval | p (Holm) |
|---|---|---|---|---|---|
| Q2, neural networks used | 79% | 98% | +19 | [+6, +32] | 0.03 |
| Q3, method's hyperparameters given | 55% | 72% | +17 | [-2, +34] | 0.6 |
| Q4, baselines' hyperparameters given | 35% | 29% | -7 | [-25, +11] | 1 |
| Q5, code linked | 31% | 74% | +43 | [+23, +58] | 0.0004 |
| Q6, choice of hyperparameters stated | 26% | 48% | +22 | [+3, +39] | 0.2 |
| Q7, held-out evaluation | 33% | 45% | +12 | [-8, +30] | 1 |
| Q8, significance test | 6% | 12% | +6 | [-7, +18] | 1 |
| X2, uncertainty reported | 63% | 88% | +26 | [+8, +41] | 0.04 |
| X3, best runs kept | 19% | 14% | -5 | [-20, +10] | 1 |
| X4, baselines tuned with the same care | 13% | 16% | +4 | [-11, +18] | 1 |
| X7, compute quantified | 27% | 58% | +31 | [+11, +47] | 0.02 |

Two intervals avoid zero without passing the correction: the choice of hyperparameters (Q6) and, in grid v2, the
statistical tools published after 2018 (Y12, from 2% to 14%, [+1, +24]). Taken alone, each would look like a change.
With 11 and 12 criteria tested at once, neither passes the adjusted threshold.

### 3.4 What withstands the controls

**Double readings.** Thirty papers were reread blind by agents that had read none of them. On each of the four verdict
criteria, the second reading agrees with the first on 30 papers out of 30.

**The search against the "no" decisions.** A "no" rests on no quote, while the verdicts "changed" rest mostly on the
"no" of 2018. Written after the results and before any search, a deviation confronts every final "no" on seven
criteria with the text of the paper, using patterns fixed in advance. Of 377 "no" decisions, 94 have no occurrence of
the patterns. The other 283 were shown, with their context, to an arbiter who saw neither the paper nor the year. Ten
turned into "yes" (2 in 2018, 8 in 2026). No verdict changes. If the 24 decisions the arbiter found doubtful are
turned as well, uncertainty and sensitivity end just above the threshold (p = 0.07 and p = 0.054 after Holm).

**The neighbouring model.** Without the thirteen papers read partly by the neighbouring model, the code link
(p = 0.0001), sensitivity (p = 0.008) and compute (p = 0.04) still pass the correction. Reported uncertainty no longer
does (p = 0.07). It is the most fragile of the four verdicts.

**The version read.** A link can be added to a paper after the conference, in a later arXiv version. Deviation 31,
written after the results and before any download, reread the code link on the same kind of version in both years.
On the proceedings in both years, the code link still rises by +41 points. On the latest arXiv version in both years,
it rises by +34 points. Both pass the Holm correction.

### 3.5 When did the change happen?

Twenty papers per year read in 2019, 2020, 2022 and 2024 date the change. The code link goes from 31% in 2018 to 60%
in 2019, 50% in 2020, 70% in 2022, 75% in 2024 and 74% in 2026. The trend test over the six years passes the Holm
correction (p = 0.00007). The step right after the 2019 checklist, 2019 and 2020 pooled against 2018 (+24 points,
[+3, +42]), does not (p = 0.2 after Holm). With twenty papers per intermediate year, the data show a slow climb and
cannot isolate a jump.

### 3.6 Our reading of 2018 against Pineau's figures

Our grid does not read 2018 as Pineau did. On the method's hyperparameters, she counted 90%, we find 55%. On held-out
evaluation, she counted 10%, we find 33%. Measured against her figures, classical RL in 2026 would have changed on
held-out evaluation (+35 points) and declined on the baselines' hyperparameters (-31 points), two gaps that vanish
against our own reading of 2018. They measure the change of grid as much as the change of practice. This is why the
verdicts compare our two readings and set her figures aside as context.

### 3.7 Year and readers, disentangled

No primary reader read both years. The papers of 2018 and those of 2026 were read by different agents. An effect
peculiar to one year's readers cannot be told apart from the year itself. Within 2018, the share of code links varies
between readers more than chance alone would easily explain (permutation p = 0.049). X8 escapes this confound, since each of its readers read both years.

For the four verdict criteria, eight new agents then reread all 98 papers with experiments, each of them on both
years (survey deviation 36, written before any reading). With their readings alone, the code link goes from 31% to
72%, sensitivity from 42% to 78% and compute from 31% to 66%. All three rises pass both tests fixed in advance after
Holm's correction: the Fisher test on the gap and the likelihood-ratio test on the year effect of a logistic model
with a random reader effect. Reported uncertainty goes from 69% to 86%, a gap of +17 points with interval
[+0.6, +33.0]. Its year effect passes (p = 0.04 after Holm) but the Fisher test misses (p = 0.053 after Holm). Under
the rule fixed in advance, its rise keeps the same direction without being established. The estimated spread between
readers is nil for two criteria and not significant for the other two. The new readers still come from the same model
family as the original ones, so a bias shared by the whole family would escape them.

## 4. B1: where does the t of 9 come from?

### 4.1 The puzzle

Figure 5 of Henderson et al. sets two groups of five TRPO runs against each other on HalfCheetah, with the same code
and the same settings. It reports t = -9.09, p = 0.0016. Pineau said in 2018 that the groups were not sorted. Yet with
thirty PPO runs of our own, two groups of five drawn at random fool Welch's t-test in 1.2% of cases. Sorted groups
fool it in 31%. The average t along the curve never comes near 9. Where does the figure come from? Before the computation, we
wrote down three leads: the spread specific to TRPO, another reading of the caption, or another computation.

### 4.2 Same code, another random seed, in 2026

E1, the experiment B1 starts from, trains PPO from Stable-Baselines3 thirty times on HalfCheetah, with the same code
and the same settings, changing only the random seed. The final returns have a mean of 1,688 and a standard deviation
of 568, from 1,138 to 3,430. Split ten of them into two groups of five drawn at random, 10,000 times: Welch's test
declares a difference in 1.2% of the draws, under the 5% it promises. Sort the ten runs by final score and set the
best five against the worst five: the test declares a difference in 31% of the draws. Keep the best three runs out of
ten, as some papers of 2018 did: the mean rises by 33%. Pineau's warning holds in 2026, with today's code: the
spread between seeds is large. A careless choice of seeds turns it into a result.

### 4.3 Two leads that fall short

**TRPO spreads more.** Our thirty TRPO runs, trained with the default values of sb3-contrib, spread far more than the
PPO runs: a final mean of 1,951 with a standard deviation of 930, or 48% of the mean, against 34% for PPO. Even so,
with groups of five drawn at random, the average t over the curve exceeds 1.4 only one time in twenty. With sorted
groups, it exceeds 1.9 one time in twenty. The rule fixed in advance rules out the spread of the algorithm as the
explanation.

**Stacked points.** Another reading of the caption stacks the hundred points of the five curves of each group as if
they were independent observations. One time in twenty, its t exceeds 5.0 with random groups, 6.3 with sorted groups.
No draw reaches 9. This computation also declares a difference in 53% of the random draws with TRPO and 23% with PPO,
although both groups run the same code: the points of a learning curve are far from independent.

**The published p.** A two-sided Welch test that gives t = 9.09 and p = 0.0016 has about 3.4 degrees of freedom. The
stacked points have about 198, which would give a p of the order of 10^-16. The average t converted into a p would need
at least 4. The published pair rules out both readings.

### 4.4 The 2017 script

In June 2017, Henderson published a script named `from_same_dist.py`. It averages the curves of the five seeds of each
group point by point, compares the two mean curves at each point with a Welch test whose variance is the variance of
the evaluation episodes of one iteration, then reports the mean of the t values and the mean of the p values. The
spread between random seeds, the one the figure was meant to measure, never enters the test. The script counts
episodes where it should count training runs.

Applied to our thirty TRPO curves, with ten evaluation episodes per point and a plan written before the computation:

- with groups drawn at random, the average t reaches 9.09 in 38% of 10,000 draws, with a median of 7.1. The test
  declares a difference in 43% of the draws.
- with sorted groups, 70% of the draws reach 9.09.
- with five episodes instead of ten, 23% of the random draws still reach 9.09.

Applied to our thirty PPO curves, the same script never reaches 9.09. One time in twenty, its average t exceeds 3.6
(Figure 4, `report/figures/t-de-neuf-en.pdf`, Figure 5, `report/figures/b1-distribution-en.pdf`).

### 4.5 Why TRPO alone gets there

Write S for the standard deviation between the episodes of one agent, σ for the standard deviation between agents and
ρ = S/σ. A Welch test on five seeds per group divides the gap between means by σ√(2/5). The script divides it by
S√(2/n), with n episodes. The ratio of the two t values is therefore √(n/5)/ρ. The identity holds on each of the 10,000
draws to rounding error. For our TRPO, the spread between the episodes of one agent is only 7% of the spread between
agents. For our PPO, it is 30%. The median factor is 18.1 for TRPO and 4.0 for PPO with ten episodes. A TRPO agent
scores almost the same at every episode, while two TRPO agents differ a great deal: counting episodes instead of seeds
then manufactures huge t values.

### 4.6 What B1 establishes, what it does not

We cannot prove that this script produced the 2018 figure. Its name, its output format, the order of magnitude it
recovers and the published (t, p) pair, which rules out the two other readings, make it likely. Our conditions differ:
our evaluation episodes are played by a deterministic policy, theirs were training episodes of a stochastic policy.
Our TRPO comes from sb3-contrib. The order of magnitude comes back despite these differences.

The lesson for the survey is direct. Same code, another random seed: chance fooled the very test that was meant to
measure it. An error bar computed over the episodes of a single agent satisfies X2 while it repeats the computation of
the script. This is why X8 matters. It is also why its flat line (Section 3.2) weighs on the X2 verdict.

## 5. E6: a published recipe that aged

### 5.1 The evaluation protocol

All the policies of E6 are evaluated the same way, apart from training: ten episodes without randomness in the
actions, on random seeds never seen in training. The interquartile mean (IQM) averages the middle half of the runs.
Its interval comes from a stratified bootstrap. The probability of improvement is the chance that a run of one group
beats a run of the other. A deviation written before each new computation fixed the groups, the tests and the reading
of the result.

### 5.2 A baseline that looked too good

E6 was meant to illustrate a flaw Pineau named: the gap a new method credits to itself when it alone is tuned. On
Hopper-v5, we set ten PPO runs with the default values of Stable-Baselines3 against ten runs with the settings
published by the RL Baselines3 Zoo, the reference collection of tuned settings for this library. The default version
reached an interquartile mean (IQM) of 2,877 [2,268, 3,369]. The tuned version reached 1,003 [856, 1,146], with a
plateau near 1,000 from early in training. The published settings did nearly three times worse than the defaults.

### 5.3 Our error, then the official script

The result was too good to accept without a check. We found an error of ours: the Zoo's reward normalisation uses
the algorithm's discount factor, 0.999, while our first pass left the default. The corrected recipe obtains 1,012
[902, 1,135] on Hopper-v5 and 984 [773, 1,002] on Hopper-v4, the version the collection was tuned for. The defaults
obtain 2,423 [1,657, 3,058] on v4. Our error was real. It explains nothing.

A deviation written before any official training then decided between the two remaining explanations with the
collection's own script. Ten policies trained by `rl_zoo3.train` on Hopper-v4, evaluated with our protocol, obtain
995 [821, 1,006]. An official policy beats one of our corrected-recipe policies with a probability of 0.58 [0.32,
0.82]: they are indistinguishable. An official policy beats a default policy with a probability of 0.09 [0, 0.30]. The
gap survives the Holm correction (p = 0.001). In score points, the Hodges-Lehmann estimate of the gap between an
official policy and a default policy is -1,464 [-2,342, -606]. Between an official policy and one of ours with the
corrected recipe, it is +5 [-18, 54].

### 5.4 A robot that stands still

On Hopper, the reward of one step is the forward velocity plus a bonus of 1 while the robot stays upright, minus a
small control cost. A step lasts 0.008 seconds. A return close to 1,000 over 1,000 steps is therefore the return of a
robot that stands upright without moving forward. Two checks, each written before its computation, confirm it.

- **The official training logs.** Over the last 200 episodes of each seed, the episodes that reach 1,000 steps earn a
  median of 1.002 per step, from 0.978 to 1.013 depending on the seed: the bonus alone.
- **The final policies replayed.** The official agents move forward at a median of 0.00 m/s, from -0.45 to 0.03 m/s.
  Our default agents run at 2.45 to 2.89 m/s (Figure 6, `report/figures/e6-vitesse-en.pdf`).

The evaluation videos show it (Figure 7, `report/figures/e6-images-en.pdf`). The official agent of seed 7 stays upright
for 1,000 steps and ends 2 centimetres behind its starting point. The default agent of seed 5 runs 19 metres in 862
steps, then falls.

### 5.5 The recipe worked in 2022

One last control had its reading fixed in advance: the agent the Zoo itself published for this task,
`sb3/ppo-Hopper-v3`, trained in 2022 with Stable-Baselines3 1.5.1a8, Gym 0.21 and PyTorch 1.11. Its configuration file
gives our hyperparameters. Its model card reports 2,410 ± 10 on Hopper-v3. Replayed with our protocol on Hopper-v4, it
obtains 2,439 over ten episodes and 2,438 ± 4 over a hundred, all of 1,000 steps, at 1.44 m/s. The reading written in
advance applies: the recipe worked with its original libraries and has aged with them. One caveat stands. This is a
single published agent, perhaps the best of a tuning run, whereas our ten official seeds all plateau near 1,000.

### 5.6 What E6 establishes

E6 does not show a baseline its authors tuned badly. It shows a published tuning that has aged with the software
around it, to the point of doing worse today than the default values of the same library. A baseline run "with the
published settings" can therefore be a robot standing still. A paper that beats it beats nothing. The check that
caught it went as far as the official script, the training logs and the videos. Pineau's reusability is not a
property a recipe keeps once published: it holds only with the software the recipe was tuned on.

## 6. What is still running

This short version, like version 1.0 of the technical report, comes before an addendum. Each item below has a
deviation written before its result.

- **A blind human re-reading** (survey deviation 35). We reread thirty papers, fifteen from each year, drawn
  in advance and shown without their year.
- **A reader from another model family** (survey deviation 33). A local open model reads the 98 papers with
  experiments of the main comparison on the four verdict criteria.
- **E6 with a discount factor of 0.99** (simulation deviation 33), **the determinism of SAC and CrossQ** (simulation
  deviation 32) and **why the two PPOs diverge** (simulation deviation 34).

## 7. Limits

The readers are agents of one model. Their double readings measure the stability of that model, not the agreement of
independent readers. Eight new readers separate the year from the reader set, but they share the model family of the first readers. The verdict rule
changed after the first results. The original rule would have confirmed no change. With fifty papers per year, the
survey sees only large changes. B1 recovers an order of magnitude with a different TRPO and different episodes, not
the published run itself. E6 rests on one task, one algorithm of the collection and one published agent for 2022.
We do not know which change of library made the recipe age.

## 8. What a paper can change

The survey and the two experiments point to the same short list, each item cheap next to the training it describes.

- **Say what the error bar is computed over.** In 2026, 14 of the 44 papers that draw a bar do not say. A bar over
  random seeds, with the number of seeds, is the one that answers Pineau's question. A bar over the episodes of one
  agent can make the same code look like two algorithms (Section 4).
- **Describe the baselines as carefully as the method.** The share of papers that give all the hyperparameters of
  their baselines did not rise. A reader cannot rerun a comparison whose other side is undescribed.
- **Rerun a published recipe before beating it.** A tuning copied from a collection can describe software that no
  longer exists. Report the score of the baseline next to the score its source published, with the libraries and
  their versions (Section 5).
- **Look at the agent.** A return near 1,000 on Hopper is a robot standing still. A video of one episode would have
  shown it in eight seconds.

None of these asks for more compute. All four ask that a second team be able to tell, from the paper alone, what was
measured.

## 9. Conclusion

Did we listen to Joelle Pineau? In part. Classical RL papers of 2026 link their code, quantify their compute, show
the effect of a setting and draw error bars far more often than those of 2018. These four practices accompany the
result. The practices that shape the result itself show no detectable change: baselines are not described with more
care, error bars are not computed more often over independent runs, significance tests stay rare. The two experiments
show why this distinction matters. An error bar can be present and measure the wrong spread: that is how two groups of
the same code once looked like two algorithms. A published recipe can be present, followed to the letter and still produce
a robot that stands still. Pineau asked for results that a second team can rerun, reuse and trust. The papers of 2026 show their materials far
more often. Whether those materials hold up, the survey cannot yet tell. The two experiments show why someone has
to look.

## Reproducibility statement

The protocols are dated. Every deviation says whether it was written before or after the result it concerns. The
readings, with their quotes, the instructions given to each agent, the training results and the analysis scripts are
in the repository. `make verify` reruns every analysis and checks that each result file comes back byte for byte.
`paper/check_short.py` ties every number of this paper to its result file.

## References

- Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., Meger, D. Deep Reinforcement Learning that Matters.
  AAAI 2018. arXiv:1709.06560.
- Henderson, P. `from_same_dist.py`, in the repository ReproducibilityInContinuousPolicyGradientMethods, GitHub,
  commit of 17 June 2017. Companion code of Islam, Henderson et al. (2017).
- Pineau, J. Reproducibility, Reusability, and Robustness in Deep Reinforcement Learning. Invited talk, ICLR 2018,
  Vancouver.
- Pineau, J. Reproducible, Reusable, and Robust Reinforcement Learning. Invited talk, NeurIPS 2018, Montréal.
- Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., Larochelle, H.
  Improving Reproducibility in Machine Learning Research. JMLR 22, 2021.
- Raffin, A., Hill, A., Gleave, A., Kanervisto, A., Ernestus, M., Dormann, N. Stable-Baselines3: Reliable
  Reinforcement Learning Implementations. JMLR 22, 2021.
- Raffin, A. RL Baselines3 Zoo. GitHub repository, 2020.
- Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A., Bellemare, M. G. Deep Reinforcement Learning at the Edge of
  the Statistical Precipice. NeurIPS 2021.
- Coakley, K. L., Snelleman, T., Hoos, H., Gundersen, O. E. The Shift Toward Open and Reproducible AI Research.
  Communications in AI & Computing 1, 2026.
- Colas, C., Sigaud, O., Oudeyer, P.-Y. How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement
  Learning Experiments. arXiv:1806.08295, 2018.
- Eimer, T., Lindauer, M., Raileanu, R. Hyperparameters in Reinforcement Learning and How To Tune Them. ICML 2023.
- Gorsane, R., Mahjoub, O., de Kock, R. J., Dubb, R., Singh, S., Pretorius, A. Towards a Standardised Performance Evaluation Protocol for Cooperative MARL. NeurIPS 2022.
- Gundersen, O. E., Kjensmo, S. State of the Art: Reproducibility in Artificial Intelligence. AAAI 2018.
- Hochlehnert, A., Bhatnagar, H., Udandarao, V., Albanie, S., Prabhu, A., Bethge, M. A Sober Look at Progress in
  Language Model Reasoning: Pitfalls and Paths to Reproducibility. COLM 2025.
- Islam, R., Henderson, P., Gomrokchi, M., Precup, D. Reproducibility of Benchmarked Deep Reinforcement Learning Tasks
  for Continuous Control. arXiv:1708.04133, 2017.
- Patterson, A., Neumann, S., White, M., White, A. Empirical Design in Reinforcement Learning. JMLR 25, 2024.
- Shao, R., Li, S. S., Xin, R., Geng, S., Wang, Y., Oh, S., Du, S. S., Lambert, N., Min, S., Krishna, R., Tsvetkov,
  Y., Hajishirzi, H., Koh, P. W., Zettlemoyer, L. Spurious Rewards: Rethinking Training Signals in RLVR. arXiv:2506.10947, 2025.
