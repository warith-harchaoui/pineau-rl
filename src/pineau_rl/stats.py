"""Statistics of the survey and of the experiments: proportions, trends, agreement, Henderson's statistic.

Every function is deterministic. The bootstrap intervals (rliable) are in `pineau_rl.bootstrap`.
The computations are written in the exact order of the scripts they came from, so that the result files regenerate
byte for byte: do not "simplify" an expression here without rerunning `make verify`.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy import stats as _st
from scipy.stats import fisher_exact, norm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint

__all__ = ["wilson", "wilson_ci", "newcombe_diff", "fisher", "compare", "holm", "cochran_armitage", "cohen_kappa",
           "probability_of_improvement", "welch_curve", "welch_pooled", "henderson_script"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n, with a fixed z (1.96 by default).

    With p = k/n: centre (p + z²/2n) / (1 + z²/n), half-width z √(p(1-p)/n + z²/4n²) / (1 + z²/n).
    Wilson, "Probable inference, the law of succession, and statistical inference", JASA 22 (1927), 209-212.
    Raises ZeroDivisionError when n = 0. `wilson_ci` gives the same interval with z = Φ⁻¹(0.975), as statsmodels.
    """
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson interval of statsmodels (`proportion_confint(method="wilson")`, z = Φ⁻¹(1 - alpha/2)).

    Returns statsmodels' own NumPy floats (a subclass of float): rounding them with `round` keeps NumPy's rounding.
    """
    lo, hi = proportion_confint(k, n, alpha=alpha, method="wilson")
    return lo, hi


def newcombe_diff(ka: int, na: int, kb: int, nb: int) -> tuple[float, float]:
    """95% interval of the difference ka/na - kb/nb, Newcombe's hybrid score method (method 10).

    Each proportion gets its Wilson interval (l_a, u_a), (l_b, u_b); with d = p_a - p_b the interval is
    d - √((p_a - l_a)² + (u_b - p_b)²), d + √((u_a - p_a)² + (p_b - l_b)²).
    Newcombe, "Interval estimation for the difference between independent proportions", Stat. Med. 17 (1998), 873-890.
    Computed by statsmodels (`confint_proportions_2indep(method="newcomb", compare="diff")`).
    """
    lo, hi = confint_proportions_2indep(ka, na, kb, nb, method="newcomb", compare="diff")
    return float(lo), float(hi)


def fisher(ka: int, na: int, kb: int, nb: int) -> float:
    """Two-sided p-value of Fisher's exact test on the table [[ka, na - ka], [kb, nb - kb]] (scipy).

    Fisher, "On the interpretation of χ² from contingency tables", J. R. Stat. Soc. 85 (1922), 87-94.
    """
    return float(fisher_exact([[ka, na - ka], [kb, nb - kb]])[1])


def compare(a: tuple[int, int], b: tuple[int, int]) -> dict[str, float]:
    """Two shares a = (ka, na) and b = (kb, nb): {diff, lo, hi, p}, the difference ka/na - kb/nb with Newcombe's
    interval and Fisher's exact p, at full precision (round only when printing)."""
    (ka, na), (kb, nb) = a, b
    lo, hi = newcombe_diff(ka, na, kb, nb)
    return dict(diff=ka / na - kb / nb, lo=lo, hi=hi, p=fisher(ka, na, kb, nb))


def holm(pvalues: Sequence[float]) -> list[float]:
    """Holm's step-down adjusted p-values, in the input order (statsmodels `multipletests(method="holm")`).

    Sorted p_(1) ≤ ... ≤ p_(m): adjusted p_(i) = min(1, max_{j ≤ i} (m - j + 1) p_(j)).
    Holm, "A simple sequentially rejective multiple test procedure", Scand. J. Stat. 6 (1979), 65-70.
    """
    if not len(pvalues):
        return []
    return [float(x) for x in multipletests(list(pvalues), method="holm")[1]]


def cochran_armitage(k: Sequence[int], n: Sequence[int], x: Sequence[float]) -> tuple[float, float]:
    """Cochran-Armitage test for a linear trend in proportions k_i/n_i against scores x_i: (z, two-sided p).

    With p = Σk/Σn and x̄ = Σ x_i n_i / Σn: T = Σ x_i (k_i - n_i p), Var T = p(1-p) Σ n_i (x_i - x̄)², z = T/√Var T
    (z = 0 when the variance is 0). Equals √N times the Pearson correlation between score and outcome over the N units.
    Armitage, "Tests for linear trends in proportions and frequencies", Biometrics 11 (1955), 375-386.
    """
    N, K = sum(n), sum(k)
    p = K / N
    xbar = sum(xi * ni for xi, ni in zip(x, n, strict=True)) / N
    t = sum(xi * (ki - ni * p) for xi, ki, ni in zip(x, k, n, strict=True))
    v = p * (1 - p) * sum(ni * (xi - xbar) ** 2 for xi, ni in zip(x, n, strict=True))
    z = t / math.sqrt(v) if v else 0.0
    return z, 2 * norm.sf(abs(z))


def cohen_kappa(a: Sequence[Any], b: Sequence[Any], categories: Sequence[Any] | None = None) -> float | None:
    """Cohen's kappa of two raters on the same items: (p_o - p_e) / (1 - p_e); None when p_e = 1 (undefined).

    p_o is the share of identical answers, p_e = Σ_c (share of a in c)(share of b in c), summed over `categories`
    (default: every value either rater gave, sorted). Cohen, Educ. Psychol. Meas. 20 (1960), 37-46.
    """
    n = len(a)
    cats = sorted(set(a) | set(b), key=str) if categories is None else categories
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pe = sum((sum(x == c for x in a) / n) * (sum(y == c for y in b) / n) for c in cats)
    return None if pe == 1 else (po - pe) / (1 - pe)


def probability_of_improvement(x: np.ndarray, y: np.ndarray) -> float:
    """P(X > Y) + ½ P(X = Y) over every pair of a run of x and a run of y (the Mann-Whitney U divided by n_x n_y).

    Agarwal et al., "Deep reinforcement learning at the edge of the statistical precipice", NeurIPS 2021.
    """
    return float((x[:, None] > y[None, :]).mean() + 0.5 * (x[:, None] == y[None, :]).mean())


def welch_curve(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Welch's t test at every evaluation point of two groups of learning curves (runs x points), then averaged:
    mean_t, p_mean_t (p of mean_t with the mean Welch degrees of freedom), mean_p (the p-values averaged), final_p.

    The two readings of "the average 2-sample t-test across entire training distribution", Henderson et al.,
    "Deep reinforcement learning that matters", AAAI 2018, figure 5.
    """
    t = _st.ttest_ind(a, b, axis=0, equal_var=False)
    va, vb = a.var(axis=0, ddof=1) / len(a), b.var(axis=0, ddof=1) / len(b)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    mean_t = t.statistic.mean()
    return dict(mean_t=mean_t, p_mean_t=2 * _st.t.sf(abs(mean_t), df.mean()), mean_p=t.pvalue.mean(),
                final_p=t.pvalue[-1])


def welch_pooled(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Third reading: every point of every curve taken as an independent observation, one Welch test: (t, p)."""
    r = _st.ttest_ind(a.ravel(), b.ravel(), equal_var=False)
    return r.statistic, r.pvalue


def henderson_script(M: np.ndarray, S: np.ndarray, a: Any, b: Any, n: int) -> tuple[float, float]:
    """Henderson et al.'s own computation (`from_same_dist.py`, 2017): the curves of groups a and b averaged run by run
    (means M, between-episode standard deviations S, runs x points), a Welch test from these statistics with n episodes
    at each point, then the mean t and the mean p. The spread between random seeds never enters the test."""
    t, p = _st.ttest_ind_from_stats(M[a].mean(0), S[a].mean(0), n, M[b].mean(0), S[b].mean(0), n, equal_var=False)
    return t.mean(), p.mean()
