"""The run format of the experiments: one CSV file per algorithm, task and random seed.

    <root>/<algo>/<task>/seed<k>.csv        step,eval_mean,eval_std,perturbed_mean,wall

One line per evaluation, steps increasing: `eval_mean` and `eval_std` are the mean and standard deviation of the
evaluation episodes' returns, `perturbed_mean` the mean return under modified physics (empty when not measured),
`wall` the elapsed seconds. A run is finished when its last step is the algorithm's budget. Any library can write
this format (`write_run`); every function here takes the algorithms, tasks, seeds and budgets explicitly.
"""
from __future__ import annotations

import csv
import os
from collections.abc import Iterable, Mapping, Sequence

import numpy as np

__all__ = ["COLUMNS", "REQUIRED", "run_path", "read_run", "write_run", "finals", "load_grid"]

COLUMNS = ("step", "eval_mean", "eval_std", "perturbed_mean", "wall")
REQUIRED = ("step", "eval_mean")  # the columns every reader needs; the others are read when present

Row = dict[str, str]


def run_path(root: str, algo: str, task: str, seed: int) -> str:
    """The file of one run: <root>/<algo>/<task>/seed<seed>.csv (a relative root gives a relative path)."""
    return f"{root}/{algo}/{task}/seed{seed}.csv"


def read_run(path: str, final_step: int | None = None, upto: int | None = None) -> list[Row] | None:
    """The rows of a run, as strings (csv.DictReader), checked: required columns, steps strictly increasing.

    None when the file does not exist, or when `final_step` is given and the last step is not it (unfinished run).
    `upto` keeps the rows whose step is at most `upto` (a run read at a smaller budget). Raises ValueError on a
    malformed file.
    """
    if not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing column(s) {missing}, expected {','.join(COLUMNS)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no evaluation")
    steps = [int(r["step"]) for r in rows]
    if any(b <= a for a, b in zip(steps, steps[1:], strict=False)):
        raise ValueError(f"{path}: steps not strictly increasing")
    if final_step is not None and steps[-1] != final_step:
        return None
    return rows if upto is None else [r for r, s in zip(rows, steps, strict=True) if s <= upto]


def write_run(path: str, rows: Iterable[Mapping[str, object]]) -> None:
    """Write a run in the format above (missing columns left empty), creating the folders."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def finals(root: str, algo: str, task: str, seeds: Iterable[int], final_step: int | None, step: int | None = None,
           column: str = "eval_mean", strict: bool = False) -> np.ndarray | None:
    """The score of each seed at `step` (default: `final_step`, the budget), in the order of `seeds`.

    None as soon as one run is missing or unfinished; with `strict`, a ValueError instead. `final_step=None`
    accepts any last step (and then `step`, if given, still cuts the curve).
    """
    step = final_step if step is None else step
    out = []
    for s in seeds:
        f = run_path(root, algo, task, s)
        r = read_run(f, final_step, step)
        if r is None:
            if strict:
                raise ValueError(f"{f}: missing, or not finished at step {final_step}")
            return None
        if step is not None and int(r[-1]["step"]) != step:
            raise ValueError(f"{f}: no evaluation at step {step}")
        out.append(float(r[-1][column]))
    return np.array(out)


def load_grid(root: str, algos: Sequence[str], tasks: Sequence[str], seeds: Iterable[int],
              final: Mapping[str, int], step: Mapping[str, int] | None = None
              ) -> tuple[dict[str, dict[str, np.ndarray]], list[str]]:
    """({task: {algo: scores}}, missing): every finished algorithm and task, and "algo/task" for the others.

    `final` maps each algorithm to its budget; `step` (default `final`) to the step at which it is read.
    """
    seeds = list(seeds)
    step = final if step is None else step
    G: dict[str, dict[str, np.ndarray]] = {}
    missing: list[str] = []
    for t in tasks:
        G[t] = {}
        for a in algos:
            x = finals(root, a, t, seeds, final[a], step[a])
            if x is None:
                missing.append(f"{a}/{t}")
            else:
                G[t][a] = x
    return G, missing
