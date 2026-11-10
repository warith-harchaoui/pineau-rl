*Translation of [SIM_PROTOCOL.md](SIM_PROTOCOL.md), made on 10 November 2026. The French text is the dated original and prevails.*

# Redoing the 2018 experiments with Pineau's rules, in 2026

Written on 2026-11-08 BEFORE any training. What changes afterwards is recorded under “Deviations”.

## Why

Henderson, Islam, Bachman, Pineau, Precup, Meger (AAAI 2018) showed on MuJoCo: (1) two
groups of five random seeds of the same code look like two different algorithms; (2) the ranking of
algorithms changes from one task to another; (3) two implementations of the same algorithm differ;
(4) publishing the best runs inflates and tightens the results. Eight years later, we redo these
experiments with the algorithms of 2026 and, this time, with the rules she asked for: enough
random seeds, confidence intervals, baselines tuned with the same care, evaluation held
out, code and data published.

## Tools (frozen versions)

Python 3.11; Gymnasium 1.1.1 (successor of OpenAI Gym, maintained by Farama); MuJoCo 4.0.0 (free and open
since 2022; a licence was required in 2018); `-v5` tasks; Stable-Baselines3 2.6.0 (PyTorch);
sbx 0.28 (Stable-Baselines in JAX); rliable for the statistics (Agarwal et al., NeurIPS 2021).
Environment: `~/pineau-rl/sim/env`, `pip freeze` in `requirements.lock`.

## Algorithms (an informed choice, 2026)

- **PPO** (Schulman 2017): the 2018 reference, still the most used in 2026 and the direct
  ancestor of GRPO, the algorithm of RL on large models. Two implementations: Stable-Baselines3
  (PyTorch) and sbx (JAX), with default settings as identical as possible.
- **SAC** (Haarnoja 2018): the off-policy standard for continuous control since 2019.
- **CrossQ** (Bhatt et al., ICLR 2024): one of the most cited recent methods for
  data efficiency (no target network, batch normalization).
- **TD3** (Fujimoto 2018): only if the budget allows (otherwise recorded as a deviation).

## Tasks

HalfCheetah-v5, Hopper-v5, Walker2d-v5, Swimmer-v5 (the tasks of Henderson et al. 2018).

## Budget and random seeds

- On-policy (PPO, two implementations): 1,000,000 steps. Off-policy (SAC, CrossQ): 300,000 steps
  (the “low-data” regime, the one in which these methods are compared from 2024 to 2026).
- 10 random seeds per (algorithm, task) pair; 30 random seeds for PPO-SB3 on HalfCheetah (E1).
- Random seeds 0 to 29, fixed before launching; NO run is removed or relaunched; a run that
  crashes is relaunched once with the same random seed and the incident is recorded.

## Evaluation (held out)

Every 50,000 steps and at the end: 10 episodes, deterministic policy, on an evaluation
environment whose random seeds (10,000 + i) are never used for training. At the end, in addition:
10 episodes on modified dynamics (masses × 1.2, friction × 0.8), for generalization.
Main measure: final mean evaluation return.

## Experiments

- **E1 Same code, different random seed**: PPO-SB3 on HalfCheetah, 30 random seeds. We draw, 10,000 times, two
  disjoint groups of 5 random seeds at random; share of draws in which a Welch test gives p < 0.05
  (should be about 5% if all goes well); then the “worst” split (5 best against 5 worst
  among 10), which reproduces the 2018 figure. Same thing with 10 random seeds per group.
- **E2 The ranking changes from task to task**: PPO-SB3, PPO-sbx, SAC, CrossQ on 4 tasks,
  10 random seeds. Ranking per task by IQM (interquartile mean) with a 95% stratified bootstrap
  confidence interval (CI) (rliable); probability of improvement between pairs; performance profiles.
- **E3 Two implementations of the same algorithm**: PPO-SB3 against PPO-sbx, same tasks, same
  random seeds; gap and CI.
- **E4 The best three out of ten**: on the E2 data, what the mean and the spread become
  when only the 3 best runs out of 10 are kept; how many E2 comparisons flip.
- **E5 How many random seeds?**: from E1 and E2, by resampling, the probability of
  recovering the correct ranking of two algorithms with n = 3, 5, 10, 20 random seeds.
- **E6 The badly tuned baseline**: PPO-SB3 on Hopper with the default settings against the
  settings published in RL Baselines3 Zoo, 10 random seeds each: the gap that a “new method”
  can claim for itself by tuning only its own.
- **E7 Held out**: gap between the evaluation on the training dynamics and on the
  modified dynamics, per algorithm.

## Statistics

IQM and stratified bootstrap CI (rliable, 2,000 resamples); Welch for E1 (it is the test
under criticism); no comparison is declared a winner without non-overlapping CIs or a
probability of improvement whose CI lies above 0.5.

## Publication

Code, `requirements.lock`, evaluation logs (CSV), analysis scripts and figures, published with
the article. The videos (“In 2018”, “In 2026”) show policies actually trained here.

## Deviations

1. Off-policy (SAC, CrossQ): 200,000 steps instead of 300,000, so that the compute fits on a heavily loaded shared machine (19 ms per step, measured). TD3 not launched. Decided before the first training run.
2. E6: an error on our side. The Zoo's normalization uses the algorithm's gamma (0.999) and the first pass left 0.99. First pass kept (`ppo_sb3_zoo`), corrected recipe relaunched (`ppo_sb3_zoofix`). The surprising result (Zoo 994 against default 2,776, plateau at 1,000 from 50,000 steps on) triggered this diagnosis, added AFTER seeing that result: corrected Zoo on Hopper-v5 and v4, default on v4, 10 random seeds each.
3. E1, second statistic (9 November 2026, AFTER seeing the results of `analysis/e1.py`): `e1.py` tests the final scores, whereas Henderson et al. report “the average 2-sample t-test across entire training distribution” (caption of their figure 5). `analysis/e1_curve.py` redoes this statistic on our 30 curves (Welch test at each of the 20 evaluation points, then the mean of the t values or the mean of the p values), for splits of 10 runs into two groups of 5, at random or sorted by final score. Added because the comparison with their figure requires it; it complements the preregistered analysis without replacing it.
4. Experiment B1, Henderson's statistic with their algorithm (written on 9 November 2026, BEFORE any TRPO training). Question: our 30 PPO runs come nowhere near the t = −9.09 of Henderson et al. (figure 5, TRPO on HalfCheetah, two unsorted groups of 5 according to Pineau). Did TRPO spread more, or did their calculation differ? Plan: 30 TRPO training runs (sb3-contrib 2.9.2, default hyperparameters, with no tuning at all) on HalfCheetah-v5, random seeds 0 to 29, one million steps, evaluation every 50,000 steps as in E1. Analysis fixed in advance (`analysis/b1_trpo.py`): the same statistics as `e1_curve.py` (mean of the t values, mean of the p values, random and sorted) plus a third reading, in which the points of all the curves of a group are stacked as independent observations (5 runs × 20 points = 100 per group). How the results will be read: if the 95th percentile of |mean t| over random splits approaches 9 with TRPO, the algorithm's spread explains their number; if only the stacked reading approaches it, their calculation explains it; otherwise neither explains it and we say so. DDPG stays outside this plan (too costly on 4 cores). Order: alongside the main queue, 2 TRPO training runs at a time (1 core each) with the main queue reduced to 1 JAX training run (2 cores), to stay at 4 cores.
5. E6, the official Zoo pipeline (written on 9 November 2026, AFTER the analysis `analysis/e6_diag.py` and BEFORE any official training). Finding: correcting our gamma error changes nothing (corrected Zoo v5: IQM 1,012 [902, 1,138] against 1,003 with the error; probability of improvement 0.47). The published recipe, as we apply it, plateaus around 1,000 on v4 as on v5, against 2,423 and 2,877 with the default values. The hyperparameters in `rl_zoo3/hyperparams/ppo.yml` (version 2.9.2) for Hopper-v4 are identical to ours. Question: does the plateau come from the published recipe itself, or from the way we apply it? Plan: 10 training runs with the official script (`python -m rl_zoo3.train --algo ppo --env Hopper-v4 --seed i`, i = 0 to 9, rl_zoo3 2.9.2, separate environment `env-zoo` with the same versions as `requirements.lock`, one thread), then evaluation of the final policies with OUR protocol (`analysis/e6_official.py`: 10 deterministic episodes, evaluation random seeds 10,000 to 10,009, observation normalization frozen, no reward normalization). Comparison fixed in advance: official against our corrected Zoo v4 and against default v4 (IQM with bootstrap interval, probability of improvement, Holm over the two). How the results will be read: if the official runs clearly exceed 1,000, our application of the recipe was at fault and we look for where; if they plateau too, the published recipe does worse than the default values in this version of the libraries, which the document states without speaking of a “baseline badly tuned by us”.
6. B1, Henderson's script (written on 9 November 2026 at 23:55, AFTER the results of `analysis/b1_trpo.py` and BEFORE any calculation with this script). Two facts found this evening. (a) The published pair, t = −9.09 and p = 0.0016, implies about 3.4 degrees of freedom (two-sided test): it rules out the “stacked points” reading (about 198 degrees of freedom, p of the order of 10⁻¹⁶) and the “mean t converted into a p” reading (a Welch test on 5 against 5 has at least 4 degrees of freedom); only the mean of the p values remains compatible. (b) On 17 June 2017, Henderson published the script `from_same_dist.py` (repository `Breakend/ReproducibilityInContinuousPolicyGradientMethods`, companion to Islam, Henderson et al. 2017). This script averages, column by column, the progress files of the random seeds of a group (`ave_results.py`), then applies at each iteration a Welch test built from the mean of the returns, their standard deviation BETWEEN EPISODES of a single iteration and the number of episodes (`ttest_ind_from_stats`). It then reports the mean of the t values and the mean of the p values. The variability between random seeds does not enter into it. Nothing proves that this script produced their figure 5; its name (“from the same distribution”) and its output (“t=…, p=…”) make it likely. Analysis fixed before running it (`analysis/b1_script.py`): on our 30 TRPO curves and our 30 PPO curves, the same draws as `b1_trpo.py` (random seed 2018, 10,000 draws of 10 runs split 5 against 5, at random then sorted), the script's calculation applied to our evaluations (mean of the `eval_mean` and of the `eval_std` of the 5 random seeds, n = 10 evaluation episodes), with n = 5 (their number of trajectories per iteration: 5,000 steps, episodes of 1,000 steps) as a sensitivity check. Differences from their case, stated in advance: our evaluation episodes follow a deterministic policy rather than the stochastic training policy; we have 20 evaluation points instead of their iterations. How the results will be read: if this calculation gives, over random splits, |mean t| of the order of 9 and a majority of false positives, their number is explained by a test that ignores the variability between random seeds; otherwise it remains unexplained.
7. Analysis details for E2, E4 and E5 (written on 10 November 2026, AFTER the PPO and SAC results and BEFORE any CrossQ result, with 3 CrossQ runs out of 40 finished; scripts `analysis/e2.py`, `analysis/e4.py`, `analysis/e5.py`). Score of each run: `eval_mean` at the last step (1 million for PPO, 200,000 for SAC and CrossQ, deviation 1: the comparison is therefore made at different budgets, which the document states). Random seeds 0 to 9 for all, including PPO-SB3 on HalfCheetah. **E2**: per task, IQM and stratified bootstrap interval (rliable, 2,000 resamples), rank by IQM; for each pair of algorithms and each task, probability of improvement with its interval; a pair is “settled” if that interval excludes 0.5. The ranking changes from task to task if the algorithm leading by IQM is not the same everywhere; we also say whether this change is settled (the leader on one task beaten in a settled way by another algorithm on another task). Performance profiles: share of runs above each threshold, with scores divided by the best IQM of the task. **E4**: for each algorithm and task, mean and standard deviation of the 10 runs, then of the 3 best; a comparison (a pair of algorithms on one task, 24 in all) “flips” if the sign of the difference in means changes when each algorithm keeps only its 3 best. **E5**: for each E2 comparison, the “correct” ranking is that of the means of the 10 runs; for n = 3, 5, 10 and 20, 10,000 draws with replacement of n runs per algorithm from its 10 (the observed distribution stands in for the algorithm), then the share of draws that recover the correct ranking; for PPO-SB3 on HalfCheetah, the 30 runs of E1 serve as the distribution. Result reported: the median share over the 24 comparisons as well as over those whose relative difference in means is below 20%.
8. B3, does the measure change the ranking (F8)? Written on 10 November 2026, AFTER the PPO and SAC results and BEFORE any CrossQ result; script `analysis/b3.py`, with no training. On the evaluation curves already recorded (20 points for PPO, 4 for SAC and CrossQ, one every 50,000 steps), three measures per run: the final score, the best score reached along the curve, the mean of the curve (the area under the curve divided by its length). Per task, IQM of each measure and ranking of the four algorithms. A pair of algorithms "reverses" between two measures if the order of their IQMs changes; the reversal is "settled" if, under each of the two measures, the interval of the probability of improvement (rliable, 2,000 resamples) excludes 0.5 in opposite directions. The budgets differ (deviation 1): the mean of the curve covers 1 million steps for PPO and 200,000 for SAC and CrossQ, which the document will state.
