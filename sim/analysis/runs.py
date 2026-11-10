"""Final scores of the main grid (SIM_PROTOCOL.md, écart 7), shared by e2.py, e4.py and e5.py."""
import csv, glob
import numpy as np

ALGOS = ["ppo_sb3", "ppo_sbx", "sac", "crossq"]
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
FINAL = {"ppo_sb3": 1_000_000, "ppo_sbx": 1_000_000, "sac": 200_000, "crossq": 200_000}  # écart 1


def finals(algo, task, seeds=range(10)):
    """Final evaluation score of each seed; None when a run is not finished yet."""
    out = []
    for s in seeds:
        f = f"results/{algo}/{task}/seed{s}.csv"
        if not glob.glob(f):
            return None
        r = list(csv.DictReader(open(f)))
        if int(r[-1]["step"]) != FINAL[algo]:
            return None
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
