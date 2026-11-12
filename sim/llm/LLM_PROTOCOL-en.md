*Translation of [LLM_PROTOCOL.md](LLM_PROTOCOL.md), made on 10 November 2026. The French text is the dated original and prevails.*

# GRPO with whatever is at hand: true reward against a reward drawn at random

Written on 2026-11-08 BEFORE the first training run. What changes afterwards is recorded under “Deviations”.
**Scope announced in advance: a small-scale illustration**, on an Apple laptop (MPS GPU),
not a replication of Shao et al. 2025 (Qwen2.5-Math-7B, MATH-500, GPU clusters).

## Question

On small models and a verifiable arithmetic task, does a reward drawn at random
improve accuracy as much as the true reward? Does the effect depend on the model
family? And what do we see depending on whether we measure pass@1 or pass@8 (Yue et al. 2025)?

## Models (two families, at least)

- Llama-3.2-1B-Instruct (Meta, `unsloth` copy);
- a small Qwen Instruct (the smallest available, exact version recorded here after download).

## Task

Generated arithmetic problems with an integer answer; we compare the **last integer** of the answer
with the correct value (no format requirement, so as not to reward format). The population is
enumerated, then shuffled with a fixed random seed; 300 **test** problems, never seen in
training. A **pilot** on problems outside the test set, without reward, sets the difficulty:
we take the family of problems on which both models are between 15% and 70% accuracy. The pilot
also sets the learning rate, among 3 values, with the true reward only and one
random seed (9) that does not enter the results; the same value is then used for all conditions.

## Algorithm

GRPO written by hand (PyTorch), to control everything: per step, 4 problems × 8 sampled
answers (temperature 1, at most 64 tokens); advantage = (r − group mean) / (group standard
deviation + 10⁻⁴); 2 update passes with clipping at 0.2 of the per-token probability
ratio, as in PPO and GRPO; Adam; gradient norm clipped at 1; no KL term.

## Conditions

- `true`: r = 1 if the answer is correct, 0 otherwise.
- `random`: r ~ Bernoulli(0.5), drawn for each answer, without looking at the answer.
- Starting point (0 steps): the base model, measured with each random seed.

5 random seeds (0 to 4) per (model, condition) pair, fixed in advance, none removed. 200 steps (reduced
if the compute requires it; recorded as a deviation, decided before seeing the results of the condition concerned).

## Measures (on the 300 test problems)

- Greedy accuracy (one answer, with no randomness).
- On 100 test problems, 8 sampled answers: pass@1 (mean accuracy of one sampled
  answer) and pass@8 (at least one correct answer out of 8).
- At step 0, every 50 steps, at the end.

## Statistics

Gain = final measure − measure at step 0, per random seed. Mean and 95% bootstrap confidence interval (CI) (5 random seeds,
wide intervals: stated as such). No conclusion without an interval.

## Publication

Code, logs and analysis stay in `~/pineau-rl/sim/llm/` until Warith has decided.

## Deviations

1. Pilot: 64 tokens cut the answers short (Qwen writes 100 to 160 tokens), hence an apparent accuracy of 0.7%. Switched to 160 tokens, decided after reading real outputs, before any training.
2. Compute cost: measures reduced to 150 test problems for greedy decoding and 50 for sampling (instead of 300 and 100). Decided before any training.
3. Task chosen: `mul2` (product of two numbers from 12 to 99). No task places both models between 15% and 70% in greedy decoding: `add3` is too easy for Llama (91%); `mul2` gives 7% (Qwen) and 73% (Llama) in greedy decoding, 11% and 23% in sampled pass@1. The main measure becomes sampled pass@1, the one GRPO trains. Decided after the pilot without training, before any training.
4. Incident of 8 November 2026: the learning-rate pilot (Qwen, lr 3e-6) reached 65 GB of memory according to another session and pushed the machine into swap (29 GB, 11 GB of free disk). Killed between step 10 and step 20, no usable result. No relaunch without a memory cap. To be cleared up before any relaunch: `train_right` = 0.91 at step 10 whereas test pass@1 is 0.11 (only four problems, or a measurement error).
5. Diagnosis of 9 November 2026, without training (`diag/replay_batch.py`, `diag/replay_batch.json`): the exact batch of step 10 of the pilot (random seed 9: 48×49, 14×36, 21×50, 45×17) gives 5/32 for the base model, in line with the test. But 23 of the 32 sampled answers hit the 160-token limit without finishing; none of them is correct. Among the 9 complete answers, 5 are correct. The 0.91 at step 10 is therefore not a counting error: the true reward first teaches the model to finish before the cutoff. Consequence for the reading: with `true`, part of the gain is a gain in length, not in arithmetic; `random` does not have this lever. We keep 160 tokens (protocol) and from now on measure the share of truncated answers (`truncated`), in training and in test. Decided before any retained training run.
6. Reduced version (Warith's decision, 9 November 2026, option (a) of the plan): 100 steps instead of 200, random seeds 0 to 2 instead of 0 to 4, a single training run at a time, learning rate 3e-6 without a full pilot (the pilot was killed at step 10), update split into batches of 8 answers (same gradient, with a quarter of the memory: four chunks of 8 answers instead of 32 at once), MPS memory cap and automatic stop (disk < 10 GB, swap + 4 GB). Decided before any retained training run.
7. Pause of 9 November 2026 at 9:35, at Warith's request (machine too heavily loaded); resumed at 12:34 with a single CPU thread (`OMP_NUM_THREADS=1`) and at low priority. The run `qwen05 random`, random seed 1, interrupted at around step 40, restarts from scratch; on resuming it crashes just after step 0 (`probability tensor contains either inf, nan or element < 0` during sampling), whereas the first attempt had got past step 40. MPS computation is not deterministic from one attempt to the next. Rule fixed before seeing any result for this random seed: we relaunch it once, identically, after the other runs; a second crash is reported as a result (instability under random reward), not removed.
8. Resumption of 9 November 2026, 12:34 to 13:09: none of the nine remaining runs completes. The four Qwen runs (`random` with random seeds 1 and 2, `true` with random seed 2, plus the relaunch planned in deviation 7) crash at the first training step on `nan` probabilities. One Llama run crashes on a macOS error (`kIOGPUCommandBufferCallbackErrorImpactingInteractivity`: the system cuts off GPU work that hinders interactivity, as Warith was working on the machine). The other five run out of MPS memory (26.5 GB allocated against a cap of 27.2 GB: Llama 1B in fp32 with the optimizer does not fit within the 0.35 cap). Before the pause, three Qwen runs had completed without `nan`. What has changed since: `OMP_NUM_THREADS=1`, low priority and interactive use of the GPU in parallel. The three finished runs remain valid. GRPO is suspended until a time slot with no interactive use (the night). Before any retained relaunch, two corrections, decided before seeing any result from these runs: (i) a Qwen control run with the pre-pause environment (without `OMP_NUM_THREADS`), to separate the two causes; (ii) for Llama, `MICRO` set to 2 (same gradient, less memory). The rule of deviation 7 is extended: each crashed run is relaunched once; a second crash is reported.
9. Night relaunch (9 November 2026, before any result from these runs): `night.sh`, from 23:00 to 7:00, no run launched after 6:00, with the JAX simulation of the main queue paused during each run to stay at 4 cores. The control run (`qwen05 random`, random seed 1, without `OMP_NUM_THREADS`) goes first; if it still produces `nan`, the night stops and the cause is sought in `grpo.py`. Llama with `MICRO=2` (environment variable, same gradient). A crashed run is retried the following night; two failures of the same run are reported as a result.
10. Cause of the `nan` found (10 November 2026, diagnosis with no retained result: `diag/nan_step.py`, `diag/nan_where.py`, `diag/nan_step.out`). The first step of `qwen05 random`, random seed 1, replayed on MPS, gives non-finite gradients on all 290 tensors of the model, whereas the loss and the log-probabilities are finite; on CPU, the same step gives a norm of 14.4 before clipping, with no non-finite value at all. On MPS, the result changes from one attempt to the next for an identical calculation: `nan` once, a finite but absurd norm (6.4 × 10⁷) the next time. Neither the attention mask, nor `eager` attention, nor the memory cap, nor gradient accumulation, nor a forced synchronization changes anything. A test matrix product ended up raising the error that the system returns when it cuts off GPU work that hinders interactive use of the machine (`kIOGPUCommandBufferCallbackErrorImpactingInteractivity`, already seen in deviation 8). Reading retained: a GPU calculation interrupted by the system sometimes comes back without an error, with corrupted values. This reading explains why the three finished runs ran early in the morning on an idle machine, as well as why the night's control run failed at 23:02, during a work session. Corrections, decided before any relaunch: (i) `grpo.py` recomputes an update whose gradient norm before clipping is non-finite or exceeds 1,000 (the threshold comes from the norm of 14.4 measured on CPU), up to five times in a row, then stops; (ii) a generation that raises a GPU error is redone, up to five times; (iii) the run stops if the initial log-probabilities or the weights become non-finite; (iv) the log counts the recomputations at each step. Consequence for the rules of deviations 7 to 9: the past crashes came from the machine, not from learning. They therefore do not count as failures of the run; the rule “two failures of the same run are a result” starts again from zero with this code. This rule change is decided after seeing these crashes; no result from these runs exists. Limit for the three finished runs: a corrupted but finite gradient, clipped at 1, may have passed without a trace; their logs do not allow this to be checked.
11. The safeguards of deviation 10 are not enough during the day (10 November 2026, control run `guardtest`, not retained): at the first step, five recomputations in a row give a corrupted gradient, so the run stops as planned. The same step on CPU (2 threads) is clean (norms 14.4 then 6.85, then 4.71 and 4.2 at step 2) and takes about three minutes, or about six hours per Qwen run. Decision, taken before any retained run with this code: the three remaining Qwen runs (`random` random seeds 1 and 2, `true` random seed 2) run on CPU (`cpu.sh`: `DEVICE=cpu`, 2 threads, low priority, one at a time, the second of the two workers alongside the main queue); the six Llama runs, too slow on CPU (about 2.5 times Qwen), stay on GPU, at night only (`night.sh`), with the safeguards. The three finished Qwen runs ran on MPS: the difference in hardware changes the rounding of the calculations, not the algorithm; the document will say so. A run that fails is relaunched once; a second failure is reported as a result.
12. Night of 10 to 11 November 2026. The three Qwen runs on CPU finished with no recomputation at all (`random` random seeds 1 and 2, `true` random seed 2): all six Qwen runs are finished. The six Llama runs all ran out of MPS memory between step 10 and step 60 (about 26.3 GB allocated against a cap of 27.2 GB); the safeguards of deviation 10 had recomputed between 1 and 6 updates per run before that. This is the first failure of each Llama run. Corrections, decided before any relaunch: the MPS cache is emptied at every step (`torch.mps.empty_cache()`), and the memory cap goes from 0.35 to 0.45 of unified memory, at night only. The six Llama runs are relaunched the next night; a second failure of the same run will be reported as a result.
13. Night of 11 to 12 November 2026. The six Llama runs, relaunched with the corrections of deviation 12, all reached step 100, with no out-of-memory error; the safeguards of deviation 10 recomputed 0, 2 and 7 updates (`true`, random seeds 0 to 2) and 5, 4 and 3 (`random`). All twelve runs are therefore finished, and none is removed. Announced statistic (Statistics section): gain per random seed, mean and 95% bootstrap interval. Its details are set after seeing the results, with no choice among several variants: percentile bootstrap over the random seeds, 10,000 draws, `random.Random(0)` (`summary.py`, `results/gains.json`). With three random seeds the bootstrap has only ten distinct resamples: the interval is reported and read as very rough.
