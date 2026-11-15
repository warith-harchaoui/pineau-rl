"""Final scores of the main grid (SIM_PROTOCOL.md, écart 7), shared by the analysis scripts.

Deviation 12 adds three environment variables, all off by default (the preregistered ten-seed analysis):
  SEEDS="a:b"     the random seeds a to b-1 (default 0:10; 0:20 for twenty seeds, 10:20 for the E4 replication);
  BUDGET=equal    every algorithm read at 200,000 steps (PPO from its evaluation curve), instead of its own budget;
  SUFFIX=_xyz     appended to the output name, so analysis/e2.json becomes analysis/e2_xyz.json.
"""
import csv, glob, os
import numpy as np

ALGOS = ["ppo_sb3", "ppo_sbx", "sac", "crossq"]
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
FINAL = {"ppo_sb3": 1_000_000, "ppo_sbx": 1_000_000, "sac": 200_000, "crossq": 200_000}  # écart 1
SEEDS = range(*map(int, os.environ.get("SEEDS", "0:10").split(":")))
EQUAL = os.environ.get("BUDGET") == "equal"
STEP = {a: 200_000 for a in ALGOS} if EQUAL else FINAL  # the step at which each algorithm is read
SUFFIX = os.environ.get("SUFFIX", "")
out_json = lambda name: f"analysis/{name}{SUFFIX}.json"
DEFAULT = SEEDS == range(0, 10) and not EQUAL


def read(algo, task, s):
    """Rows of a finished run's evaluation curve, cut at the step this analysis reads; None if not finished."""
    f = f"results/{algo}/{task}/seed{s}.csv"
    if not glob.glob(f):
        return None
    r = list(csv.DictReader(open(f)))
    if int(r[-1]["step"]) != FINAL[algo]:
        return None
    return [x for x in r if int(x["step"]) <= STEP[algo]]


def finals(algo, task, seeds=None):
    """Evaluation score of each seed at the step this analysis reads; None when a run is not finished yet."""
    out = []
    for s in SEEDS if seeds is None else seeds:
        r = read(algo, task, s)
        if r is None:
            return None
        assert int(r[-1]["step"]) == STEP[algo], (algo, task, s)
        out.append(float(r[-1]["eval_mean"]))
    return np.array(out)


def grid():
    """{task: {algo: scores}} for every finished algorithm and task, and the list of what is missing."""
    G, missing = {}, []
    for t in TASKS:
        G[t] = {}
        for a in ALGOS:
            x = finals(a, t)
            if x is None:
                missing.append(f"{a}/{t}")
            else:
                G[t][a] = x
    return G, missing
