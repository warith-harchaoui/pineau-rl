# Did we listen to Joelle Pineau in 2018?

*Version française : [LISEZMOI.md](LISEZMOI.md)*

In 2018, at ICLR and then at NeurIPS, Joelle Pineau showed sixteen flaws that made results in deep
reinforcement learning (RL) hard to believe. Among them: missing code, unreported settings,
competing methods tuned less carefully, too few runs, no statistical test, evaluation on the
training conditions. This repository measures, flaw by flaw, what has changed since.

It contains everything needed to recompute every number and every figure in the document. That
is part of the argument: work on reproducibility owes its readers a reproducible repository.

**Status on 9 November 2026**: work in progress. Simulations are still running, and several
experiments remain to be done (see "What remains to be measured" in the document).

## The document

- English: [`docs/conclusions-en.md`](docs/conclusions-en.md), compiled to
  [`docs/conclusions-en.pdf`](docs/conclusions-en.pdf).
- French: [`docs/conclusions.md`](docs/conclusions.md), compiled to
  [`docs/conclusions.pdf`](docs/conclusions.pdf).

## Two instruments

**A survey of papers** (`study/`).
- We read 50 RL papers drawn at random from the 1,252 RL papers of ICLR 2026, ICML 2026 and
  NeurIPS 2025, with Pineau's grid and a second grid of our own (Y1 to Y12). We topped up the
  classical RL papers to 50, and read 50 papers from 2018 with the same grids. Verdicts rest on
  classical RL in 2026 against our own reading of 2018, since our grid reads 2018 differently
  from Pineau's.
- The reading is done by language-model agents. Every decision rests on an exact quote from the
  paper, with its page. Twenty papers were read twice, blind. A blind human rereading is still
  pending.
- The protocol was written before any reading. Deviations are recorded in it, with their dates.

**Experiments** (`sim/`). We rerun the 2018 experiments with the algorithms of 2026:
- PPO in two implementations, SAC and CrossQ;
- four MuJoCo tasks, ten random seeds per pair, thirty for experiment E1;
- evaluation on random seeds never seen in training and on modified physics;
- a part on large language models: a hand-written GRPO, true reward against coin-flip reward.

The protocol was written before the first training run. No run is removed, and mistakes stay in
the results, our own included.

## What is in the repository

| Folder or file | Contents |
|---|---|
| `study/PROTOCOL-en.md` (French original: `PROTOCOL.md`) | The survey protocol: population, draw, grid, decision rules, deviations. |
| `study/GRILLE-en.md`, `study/RESULTS-en.md`, `study/harmonisation_audit.md` | The readers' sheet, the first results, the audit of the raw readings. |
| `study/codes/<reader>/<paper>.json` | One decision per criterion and per paper, with quote and page. |
| `study/final_2026.json`, `study/calib_2018.json` | The papers drawn, with their addresses. |
| `study/analyze.py`, `study/audit_stats.py`, `study/extension_stats.py` | The percentages, the audit of the differences (Newcombe, Fisher, Holm), then the enlarged survey. |
| `sim/SIM_PROTOCOL-en.md`, `sim/llm/LLM_PROTOCOL-en.md` (French originals without `-en`) | The experiment protocols and their deviations. |
| `sim/run.py` | One training run: algorithm, task, random seed, number of steps. |
| `sim/jobs.txt`, `sim/drive.sh` | The full list of training runs and the launcher. |
| `sim/results/` | The evaluation curves of every run (CSV). |
| `sim/models/` | The final policies, to re-evaluate without retraining. |
| `sim/analysis/` | One script and one JSON file per experiment. |
| `sim/llm/` | GRPO, the length diagnostic and the results. |
| `slides-en.md` | Pineau's ICLR 2018 slides, described one by one. |
| `docs/` | The document in two languages, the bibliography and the figures (`docs/figures/build.py`). |

## Reproducing the results

Hardware used: a Mac with an Apple M2 Max chip, Python 3.11.

```bash
# Three environments, pinned versions
python3.11 -m venv sim/env     && sim/env/bin/pip install -r sim/requirements.lock
python3.11 -m venv sim/env-an  && sim/env-an/bin/pip install -r sim/requirements-analysis.lock
python3.11 -m venv sim/env-llm && sim/env-llm/bin/pip install -r sim/requirements-llm.lock

# The survey: percentages and audit of the differences (a few seconds)
cd study && ../sim/env-an/bin/python analyze.py && ../sim/env-an/bin/python audit_stats.py && ../sim/env-an/bin/python extension_stats.py && cd ..

# Download again the PDFs of the papers we read (not redistributed here)
cd study && python3 fetch.py final_2026.json pdf && cd ..

# One experiment: one training run (PPO, HalfCheetah, random seed 0, one million steps)
cd sim && env/bin/python run.py ppo_sb3 HalfCheetah-v5 0 1000000

# All experiments (P runs in parallel; about 250 core-hours in total)
P=4 ./drive.sh

# The analyses, from the results already in the repository (a few minutes)
env-an/bin/python analysis/e1.py && env-an/bin/python analysis/e1_curve.py && cd ..

# The figures, then the document (needs md2star, pandoc, LuaLaTeX and sprezzature-figures)
cd docs/figures && ../../sim/env-llm/bin/python build.py && cd .. && ./build.sh
```

The raw results are already in the repository: analyses and figures can be rebuilt without
retraining. The full path, training included, takes a few days on a desktop machine.

## What is not in this repository

- The PDFs of the papers we read, which are under copyright. `study/fetch.py` downloads them
  again.
- Pineau's slides, for the same reason. They are on the ICLR 2018 and NeurIPS 2018 websites.

## Citing this work

Warith Harchaoui, "Did we listen to Joelle Pineau in 2018?", 2026.

## License

BSD 3-Clause, the license of scikit-learn: see [LICENSE](LICENSE).
