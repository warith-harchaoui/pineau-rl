"""Final scores of the main grid (SIM_PROTOCOL.md, écart 7), shared by the analysis scripts.

The run format and its reader are in the package (pineau_rl.runs); this module fixes the grid of this study and reads
three environment variables (deviation 12), all off by default (the preregistered ten-seed analysis):
  SEEDS="a:b"     the random seeds a to b-1 (default 0:10; 0:20 for twenty seeds, 10:20 for the E4 replication);
  BUDGET=equal    every algorithm read at 200,000 steps (PPO from its evaluation curve), instead of its own budget;
  SUFFIX=_xyz     appended to the output name, so analysis/e2.json becomes analysis/e2_xyz.json.
"""
import os
from pineau_rl import runs as _runs

ALGOS = ["ppo_sb3", "ppo_sbx", "sac", "crossq"]
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
FINAL = {"ppo_sb3": 1_000_000, "ppo_sbx": 1_000_000, "sac": 200_000, "crossq": 200_000}  # écart 1
ROOT = "results"
SEEDS = range(*map(int, os.environ.get("SEEDS", "0:10").split(":")))
EQUAL = os.environ.get("BUDGET") == "equal"
STEP = {a: 200_000 for a in ALGOS} if EQUAL else FINAL  # the step at which each algorithm is read
SUFFIX = os.environ.get("SUFFIX", "")
out_json = lambda name: f"analysis/{name}{SUFFIX}.json"
DEFAULT = SEEDS == range(0, 10) and not EQUAL


def read(algo, task, s):
    """Rows of a finished run's evaluation curve, cut at the step this analysis reads; None if not finished."""
    return _runs.read_run(_runs.run_path(ROOT, algo, task, s), FINAL[algo], STEP[algo])


def finals(algo, task, seeds=None):
    """Evaluation score of each seed at the step this analysis reads; None when a run is not finished yet."""
    return _runs.finals(ROOT, algo, task, SEEDS if seeds is None else seeds, FINAL[algo], STEP[algo])


def grid():
    """{task: {algo: scores}} for every finished algorithm and task, and the list of what is missing."""
    return _runs.load_grid(ROOT, ALGOS, TASKS, SEEDS, FINAL, STEP)
