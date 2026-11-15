# Pinned environments

*Version française : [LISEZMOI.md](LISEZMOI.md)*

Four Python environments ran this project, all on Python 3.11.18, on a Mac with an Apple M2 Max chip
(macOS 27.2, arm64). Each file below is the `pip freeze` of one of them, taken on 15 November 2026, with
the Python version and the platform written at the top.

| File | Environment | What it runs | Key versions |
|---|---|---|---|
| `train.txt` | `sim/env` | training (`sim/run.py`, `sim/dose.py`) | Stable-Baselines3 2.9.2, SBX 0.28.0, JAX 0.10.2, Gymnasium 1.1.1, MuJoCo 4.0.0, PyTorch 2.15.0 |
| `analysis.txt` | `sim/env-an` | every analysis script, `docs/check_numbers.py`, the CI | NumPy 2.4.6, SciPy 1.17.1, statsmodels 0.15.0, rliable 1.2.0 |
| `zoo.txt` | `sim/env-zoo` | the official RL Baselines3 Zoo pipeline of experiment E6 | rl_zoo3 2.9.2, same libraries as `train.txt` |
| `llm.txt` | `sim/env-llm` | GRPO (`sim/llm/grpo.py`) and the figures of `docs/` | PyTorch 2.15.0, Transformers 5.22.2, Accelerate 1.15.0 |
| `test.txt` | on top of `analysis.txt` | the unit tests (`tests/`) | pytest 9.2.0 |

## Recreating an environment

```bash
python3.11 -m venv sim/env-an
sim/env-an/bin/pip install -r envs/analysis.txt -r envs/test.txt
make verify            # recomputes every number and compares the JSON files byte for byte
```

The other three follow the same pattern: `sim/env` from `train.txt`, `sim/env-zoo` from `zoo.txt`,
`sim/env-llm` from `llm.txt`. The paths matter, since the scripts and launchers call
`sim/env/bin/python` and its siblings.

The originals came from conda (`conda create -p sim/env python=3.11`), then pip installed every package.
A plain `venv` gets the same packages. `sim/env-zoo` is a `venv` built over the Python of `sim/env`.

## What to know before installing

- **The same lists, under two names.** The four files repeat `sim/requirements.lock`,
  `sim/requirements-analysis.lock`, `sim/requirements-zoo.lock` and `sim/requirements-llm.lock`, the
  names the protocols cite. `envs/` adds the header and gathers them in one place.
- **rliable 1.2.0** ships as a source archive only. pip builds it in a few seconds (pure Python).
- **On Linux**, `analysis.txt` installs as it is: the continuous integration does it on Ubuntu
  (`.github/workflows/verify.yml`). There, `check_numbers.py` and the tests decide; the last digits of a
  bootstrap move with the processor, so the byte-for-byte comparison is enforced on macOS arm64, the
  platform of the results, while Linux only shows it.
- **Training on Linux** works with `train.txt` too, but the runs of this repository come from macOS arm64.
  A rerun elsewhere gives other curves for the same random seed: MuJoCo, JAX and PyTorch round differently
  from one processor to the next. A rerun on another machine tests the statistics, not each curve.
- **GRPO** ran on the Apple GPU (MPS) or on the CPU, depending on the run (`sim/llm/LLM_PROTOCOL-en.md`,
  deviation 11). `grpo.py` downloads `Qwen/Qwen2.5-0.5B-Instruct` and `unsloth/Llama-3.2-1B-Instruct`
  from Hugging Face; `docs/figures/build.py` downloads the Qwen tokenizer. The model revision is the one
  served on the day of the run: it is not pinned.

## The document toolchain

Outside the Python environments, building the PDFs and figures used:

| Tool | Version | Used by |
|---|---|---|
| pandoc | 3.6.1 | `docs/build.sh` |
| md2star | 3.13.5 (PyPI) | `docs/build.sh` (DOCX and a first PDF) |
| TeX Live 2026: LuaHBTeX 1.24.0, latexmk 4.88 | | `docs/build.sh` (the final PDF) |
| sprezzature-figures | 2.14.1 (2.14.0 on PyPI) | `docs/figures/build.py`, `figures/build.py` |
| rsvg-convert (librsvg) | 2.61.3 | SVG to PDF and PNG |
| git | 2.50.0 | `make verify` |

`make check` and `make verify` need only `analysis.txt`: these tools draw and typeset, they compute no number.
