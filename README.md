# Reinforcement Learning: Did we listen to Joelle Pineau in 2018?

*Version française : [LISEZMOI.md](LISEZMOI.md)*

In 2018, at ICLR and then at NeurIPS, Joelle Pineau showed sixteen flaws that made results in deep
reinforcement learning (RL) hard to believe. Among them: missing code, unreported settings,
competing methods tuned less carefully, too few runs, no statistical test, evaluation on the
training conditions. Her talks asked for research that is reproducible, reusable and robust. This
repository measures, flaw by flaw, what has changed since. It holds itself to the same three words:
every number of the document comes back with one command, each piece serves again on other papers
or other runs, tests guard the computations.

**Status on 17 November 2026.** The experiments are being consolidated: twenty random seeds per
algorithm and task instead of ten, five random seeds per GRPO configuration instead of three.
Both extensions were written into the protocols before any new run (deviation 12 of
`sim/SIM_PROTOCOL-en.md`, deviation 14 of `sim/llm/LLM_PROTOCOL-en.md`). The GRPO part is finished (deviation 16 of the same
protocol): its five-seed result appears below. The other figures below come from the document
dated 13 November 2026.

**What a reader can check, and what rests on our word.** The protocols say, for each rule, whether it was
written before or after the results; a critical review of this repository found several of those statements
wrong in their details, and the corrections are dated (deviation 14 of `sim/SIM_PROTOCOL-en.md`, deviation 15
of `sim/llm/LLM_PROTOCOL-en.md`). The repository became public on 15 November 2026, and its first commit
(9 November) already holds results next to the protocols: for everything before that date, the order of
writing rests on our word and on the commit dates, which their author could have forged. Every training
attempt, including those stopped and relaunched, is listed in `sim/logs/attempts_reconstructed.csv` (until
15 November) and `sim/logs/attempts.jsonl` (since). What anyone can check without trusting us: every number
recomputed from the committed results, and every survey decision against the quote and page it rests on.

## What we found

- **Four practices changed.** Against our own reading of 2018, classical RL papers of 2026 link their
  code more often (31% then 74%), show the sensitivity to a setting (44% then 80%), quantify their
  compute (27% then 58%) and report an uncertainty (63% then 88%). The last one is fragile: without the
  thirteen papers read partly by another model, it no longer passes Holm's correction. Read on 20 papers a year in between,
  these four climb slowly, with no jump after the checklist NeurIPS has required since 2019.
- **Others did not move detectably**: a statistical test (6% then 12%), baselines described with all
  their settings (35% then 29%), evaluation on held-out conditions (33% then 45%).
- **The runs themselves.** Among thirty runs of the same program, two groups of five drawn at random
  fool a statistical test in 1.2% of cases; sorted by score, in 31%. Keeping the best runs inflates the
  score by 33%. The t of 9 that made the 2018 talks famous has an explanation: Peter Henderson's
  published script measures the spread between episodes and ignores the spread between random seeds.
  Applied to our TRPO runs, it exceeds 9 in 38% of random draws.
- **Robustness.** On four algorithms, the best one changes with the task. Physics modified by 20%
  upends the ranking on Hopper: the leader ends last (a description chosen after seeing the results,
  with no test: deviation 11).
- **Language models.** In our hand-written GRPO, part of the measured gain comes from answers cut off
  at 160 tokens, a lesson the random reward never teaches. With five random seeds, the interval of
  Qwen's mean gain with the true reward contains zero (+14 points, from −3 to +34): the gain rests on
  the two runs made on the GPU. Hardware and random seed changed together.

The full argument, with every source: [`docs/conclusions-en.md`](docs/conclusions-en.md)
([PDF](docs/conclusions-en.pdf)); in French, [`docs/conclusions.md`](docs/conclusions.md)
([PDF](docs/conclusions.pdf)).

## Two instruments

**A survey of papers** (`study/`). We read 50 RL papers drawn at random from the 1,252 RL papers of
ICLR 2026, ICML 2026 and NeurIPS 2025, with Pineau's grid and a second grid of our own (Y1 to Y12),
then topped up the classical RL papers to 50 and read 50 papers from 2018 with the same grids.
Language-model agents do the reading. Every decision rests on an exact quote from the paper, with its
page, so anyone checks any decision against the PDF. Twenty papers were read twice, blind. The
protocol was written before any reading; its deviations are dated.

**Experiments** (`sim/`). We rerun the 2018 experiments with the algorithms of 2026: PPO in two
implementations, SAC and CrossQ, on four MuJoCo tasks, ten random seeds per pair (thirty for
experiment E1), evaluated on random seeds never seen in training and on modified physics. A strand on
large language models compares a hand-written GRPO trained with the true reward against the same
training with a coin-flip reward. The protocol was written before the first training run. Every run
stays in the results, our own mistakes included.

## How the repository is organised

| Path | Contents |
|---|---|
| `docs/` | The document in two languages, its bibliography, its figures (`docs/figures/build.py`) and `check_numbers.py`, which recomputes 145 key numbers of both texts from the result files. |
| `study/PROTOCOL-en.md`, `study/GRILLE-en.md` | The survey protocol; the readers' sheet with both grids (French originals without `-en`). |
| `study/codes/`, `study/codes_v2/` | One JSON file per paper and per reader: one decision per criterion, with quote and page. |
| `study/*.py`, `study/*.json` | The draws, the analyses (Wilson intervals, Newcombe differences, Fisher, Holm, Cochran-Armitage) and their results. |
| `sim/SIM_PROTOCOL-en.md`, `sim/llm/LLM_PROTOCOL-en.md` | The experiment protocols and their deviations. |
| `sim/run.py`, `sim/jobs*.txt`, `sim/drive.sh`, `sim/queue.sh` | One training run; the lists of runs and their launchers. |
| `sim/results/`, `sim/logs/` | The evaluation curve of every run (CSV) and the training logs. |
| `sim/models/` | Final policies, to re-evaluate without retraining (SAC and CrossQ weights are kept locally only). |
| `sim/analysis/` | One script and one JSON file per experiment (E1 to E7, B1, B3). |
| `sim/llm/` | GRPO in one file (`grpo.py`), its diagnostics, results and `summary.py`. |
| `envs/` | The pinned environments, the platform and the document toolchain ([`envs/README.md`](envs/README.md)). |
| `src/pineau_rl/`, `pyproject.toml` | The reusable pieces as a Python package: statistics, run format, reading grid (see below). |
| `Makefile`, `tests/`, `.github/workflows/verify.yml` | One-command recomputation, unit tests, continuous integration. |
| `slides-en.md` | Pineau's ICLR 2018 slides, described one by one. |

## Reproducing the results, at three levels

The results come from a Mac with an Apple M2 Max chip, under Python 3.11.18
(details in [`envs/README.md`](envs/README.md)).

**1. Recompute every number from the committed results (under an hour, no training).**

```bash
python3.11 -m venv sim/env-an
sim/env-an/bin/pip install -r envs/analysis.txt -r envs/test.txt
make verify
```

`make verify` reruns the nine survey analyses, the fourteen experiment analyses and the GRPO summary,
checks the 145 numbers of both texts (`make check`), runs the unit tests (`make test`), then asks git
whether every JSON file came back byte for byte. On the M2 Max, saturated by training runs at the
same time, the whole sequence took about 45 minutes; E1, B1, B3 and E2, with their tens of thousands of
random draws, take most of it. `make verify-head` does the same in a fresh export of the last
commit, which leaves a working copy with runs in progress untouched. The continuous integration
reruns it at every push.

The figures and the PDFs need the document toolchain (pandoc, md2star, LuaLaTeX, sprezzature-figures,
listed in `envs/`):

```bash
python3.11 -m venv sim/env-llm && sim/env-llm/bin/pip install -r envs/llm.txt
make figures docs
```

**2. Retrain one run.**

```bash
python3.11 -m venv sim/env && sim/env/bin/pip install -r envs/train.txt
cd sim && env/bin/python run.py ppo_sb3 HalfCheetah-v5 0 1000000
```

The run writes `results/ppo_sb3/HalfCheetah-v5/seed0.csv`, to set against the committed one,
then `models/ppo_sb3/HalfCheetah-v5/seed0.zip`. Median wall time per run on one core, from the committed
logs: PPO (Stable-Baselines3) about half an hour for a million steps, PPO (SBX, JAX) about an hour,
SAC from twenty minutes (Swimmer) to two hours (HalfCheetah) for 200,000 steps, CrossQ from one hour
and three quarters to three hours and a half, TRPO about five minutes. One GRPO run
(`sim/llm/grpo.py`) takes about 50 minutes on the Apple GPU for Qwen2.5 0.5B, 70 to 100 minutes for
Llama 3.2 1B, five to six hours on two CPU threads for Qwen.

**3. Retrain everything.**

```bash
cd sim && P=4 ./drive.sh                 # every line of jobs.txt, four at a time
```

The 250 committed training runs add up to about 260 core-hours, so a little under three days on
four cores. The twelve GRPO runs add about 27 hours; the official RL Baselines3 Zoo pipeline of
E6 (`sim/zoo_official.sh`), ten runs more. The consolidation under way (`sim/jobs_seeds20.txt`,
`sim/jobs_consolidation.txt`) adds 160 training runs (about 200 core-hours) then 320 re-evaluations
of saved policies under several physics changes (`sim/dose.py`). Retraining on another
processor gives other curves for the same random seed; what a full rerun tests is the statistics.

## Reusing the pieces

The statistics, the run format and the reading grid form a Python package, `pineau_rl` (`src/`), whose
only dependencies are NumPy, SciPy, statsmodels and rliable. Every analysis script imports it.

```bash
pip install -e .        # anywhere; in the environment of envs/analysis.lock: make install (nothing downloaded)
```

| Module | Contents |
|---|---|
| `pineau_rl.stats` | Wilson, Newcombe difference, Fisher, Holm, Cochran-Armitage, Cohen's kappa, probability of improvement, Henderson's statistic |
| `pineau_rl.bootstrap` | IQM and probability of improvement with rliable's stratified bootstrap intervals |
| `pineau_rl.runs` | The run format (one CSV per algorithm, task and random seed), its checked reader, final scores, a grid |
| `pineau_rl.grid` | Reading files, harmonisation, final value of a criterion, validator of a reading file |

Compare shares between two samples, criterion by criterion, as the survey does:

```python
from pineau_rl.stats import compare, holm, wilson_ci

wilson_ci(17, 48)                         # 95% Wilson interval of 17/48
tests = {k: compare(a, b) for k, (a, b) in {"code": ((31, 48), (19, 50)), "seeds": ((12, 48), (9, 50))}.items()}
holm([t["p"] for t in tests.values()])    # each t: {"diff", "lo", "hi", "p"}, Newcombe and Fisher
```

Rank your own algorithms from runs in our format, written by any library:

```python
import numpy as np
from pineau_rl.bootstrap import iqm_interval
from pineau_rl.runs import load_grid

np.random.seed(2026)  # rliable draws from NumPy's global generator: seed it once, at the top
G, missing = load_grid("results", ["ppo", "sac"], ["Hopper-v5"], range(10), {"ppo": 1_000_000, "sac": 200_000})
iqm_interval(G["Hopper-v5"])              # {algo: (IQM, low, high)}, stratified bootstrap
```

Read a sample of papers with our grid:

```python
from pineau_rl.grid import load_overrides, load_reads, tally, validate, value_v1

reads = load_reads("codes", ["A", "B"])  # codes/<reader>/<paper id>.json, sorted
ov = load_overrides("overrides.json")    # {criterion: {paper id: value}}, the harmonisation
v = lambda r, k: value_v1(r, k, ov)
problems = {i: validate(r, q1=v(r, "Q1"), x2=v(r, "X2"), q4=v(r, "Q4")) for i, r in reads.items()}
tally(v(r, "Q5") for r in reads.values() if v(r, "Q1") != "no")  # (yes, yes or no): code linked
```

The scripts themselves still run from their folders (`cd study && python extension_stats.py`); `make`
finds the package without installing it.

- **The reading grid.** `study/GRILLE-en.md` turns Pineau's checklist and our twelve extra criteria
  into decision rules, each answer backed by a quote and a page. To read your own sample, copy the
  JSON format of `study/codes_v2/`, check your files with `study/check_codes.py` (schema, scope rules,
  every quote against the text of the PDF; `pineau_rl.grid.validate` without the PDF), then compute
  shares and intervals with `study/analyze_final.py` or `study/extension_stats.py`.
- **The analysis scripts on your own runs.** Every experiment script reads
  `sim/results/<algo>/<task>/seed<k>.csv`, one evaluation per line, with the columns
  `step,eval_mean,eval_std,perturbed_mean,wall`. Write your runs in that format, from any library, add
  the algorithm and its number of steps to `ALGOS` and `FINAL` at the top of `sim/analysis/runs.py`:
  E2 (ranking with intervals), E4 (best-of inflation), E5 (how many random seeds recover a
  ranking) and E7 (loss under modified physics) read them.
- **Henderson's statistic.** `pineau_rl.stats.henderson_script` reproduces the computation of
  `from_same_dist.py` (Henderson et al., 2018), used by `sim/analysis/b1_script.py`; `tests/test_henderson.py` shows on six made-up random
  seeds why it reaches a t of 9 where a test on the random seeds sees nothing.
- **GRPO in one file.** `sim/llm/grpo.py` trains a language model with GRPO in 156 lines, with
  the true reward or a coin-flip one; it logs the share of cut-off answers at every evaluation.

## What is not in this repository

- The PDFs of the papers we read, which are under copyright. `study/fetch.py` downloads them again:
  `cd study && python3 fetch.py final_2026.json pdf`.
- Pineau's slides, for the same reason. They are on the ICLR 2018 and NeurIPS 2018 websites.

## Citing this work

Warith Harchaoui, "Reinforcement Learning: Did we listen to Joelle Pineau in 2018?", 2026.
GitHub reads [`CITATION.cff`](CITATION.cff) and offers the reference in APA and BibTeX.

```bibtex
@misc{harchaoui2026pineau,
  author = {Harchaoui, Warith},
  title  = {Reinforcement Learning: Did we listen to Joelle Pineau in 2018?},
  year   = {2026}
}
```

## Licence

BSD 3-Clause licence, the licence of scikit-learn: see [LICENSE](LICENSE).
