"""Stratified bootstrap intervals of rliable (Agarwal et al., NeurIPS 2021): IQM and probability of improvement.

Reproducibility: rliable 1.2.0 accepts `random_state` but its bootstrap draws from NumPy's GLOBAL generator
(SIM_PROTOCOL.md, deviation 13). Seed it once at the top of a script, `np.random.seed(2026)`, then call these
functions in a fixed order: each call consumes the global generator, so the intervals depend on the calls before it.
The scripts of sim/analysis/ also pass `random_state=np.random.RandomState(2026)`, kept for byte identity.
rliable is imported here, at import time, never inside a function: an import must not happen after the seed.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from rliable import metrics
from rliable.library import get_interval_estimates

from pineau_rl.stats import probability_of_improvement

__all__ = ["iqm", "iqm_interval", "improvement_interval", "probability_of_improvement_bootstrap"]


def iqm(x: np.ndarray) -> float:
    """Interquartile mean: the mean of the middle 50% of the scores (scipy's trim_mean at 25%), via rliable."""
    return metrics.aggregate_iqm(x)


def _iqm1(x: np.ndarray) -> np.ndarray:
    return np.array([metrics.aggregate_iqm(x)])


def iqm_interval(scores: Mapping[str, np.ndarray], reps: int = 2000,
                 random_state: Any = None) -> dict[str, tuple[float, float, float]]:
    """{name: (IQM, low, high)}: the IQM of each group of runs with its 95% stratified bootstrap percentile interval.

    `scores` maps a name to a 1-D array of scores (one per run). Draws from NumPy's global generator (see the module).
    """
    pe, ci = get_interval_estimates({k: np.asarray(v)[:, None] for k, v in scores.items()}, _iqm1, reps=reps,
                                    random_state=random_state)
    return {k: (float(pe[k][0]), float(ci[k][0][0]), float(ci[k][1][0])) for k in scores}


def improvement_interval(x: np.ndarray, y: np.ndarray, reps: int = 2000,
                         random_state: Any = None) -> tuple[float, float, float]:
    """(P(X > Y), low, high): rliable's probability of improvement of the runs x over the runs y with its 95%
    stratified bootstrap interval. Draws from NumPy's global generator (see the module)."""
    ppe, pci = get_interval_estimates({"p": (x[:, None], y[:, None])}, metrics.probability_of_improvement, reps=reps,
                                      random_state=random_state)
    lo, hi = (float(v) for v in np.ravel(pci["p"]))
    return float(ppe["p"]), lo, hi


def probability_of_improvement_bootstrap(x: np.ndarray, y: np.ndarray, rng: np.random.Generator,
                                         reps: int = 5000) -> tuple[float, list[float]]:
    """P(X > Y) + ½ P(X = Y) with a 95% percentile bootstrap interval, x and y resampled independently with `rng`
    (a draw of x, then a draw of y, reps times): (point, [low, high]). No rliable, no global generator."""
    pi = probability_of_improvement
    boots = [pi(rng.choice(x, len(x)), rng.choice(y, len(y))) for _ in range(reps)]
    return pi(x, y), [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
