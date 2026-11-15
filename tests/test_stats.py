"""pineau_rl.stats: Wilson, Newcombe, Fisher, Holm, Cochran-Armitage, Cohen's kappa, probability of improvement.

Three kinds of checks: values published in the literature, an independent computation (statsmodels, scipy, numpy),
and golden values on fabricated data (frozen at 1e-12 relative: a change there changes a result file).
"""
import math

import numpy as np
import pytest
from scipy.stats import fisher_exact
from statsmodels.stats.proportion import proportion_confint

from pineau_rl.stats import (
    cochran_armitage,
    cohen_kappa,
    compare,
    fisher,
    holm,
    newcombe_diff,
    probability_of_improvement,
    wilson,
    wilson_ci,
)

CASES = [(0, 10), (1, 10), (5, 10), (10, 10), (17, 48), (3, 50), (49, 50)]
GOLD = dict(rel=1e-12)


# ---------------------------------------------------------------- Wilson
def test_wilson_published_value():
    """Newcombe (1998, Stat. Med. 17, 857-872), table I: 81/263, score interval 0.2553 to 0.3662."""
    assert wilson(81, 263) == pytest.approx((0.2553, 0.3662), abs=1e-4)
    assert wilson_ci(81, 263) == pytest.approx((0.2553, 0.3662), abs=1e-4)


def test_wilson_matches_statsmodels():
    for k, n in CASES:
        lo, hi = wilson(k, n)
        ref = proportion_confint(k, n, alpha=0.05, method="wilson")
        assert lo == pytest.approx(ref[0], abs=1e-4) and hi == pytest.approx(ref[1], abs=1e-4)  # z 1.96 vs 1.95996
        assert wilson_ci(k, n) == pytest.approx(ref, abs=1e-15)
        assert wilson(k, n, z=1.959963984540054) == pytest.approx(ref, abs=1e-12)


def test_wilson_properties():
    rng = np.random.default_rng(3)
    for _ in range(200):
        n = int(rng.integers(1, 500))
        k = int(rng.integers(0, n + 1))
        lo, hi = wilson(k, n)
        assert -1e-12 <= lo <= k / n <= hi <= 1 + 1e-12            # contains the share, within [0, 1]
        assert wilson(n - k, n) == pytest.approx((1 - hi, 1 - lo), abs=1e-12)  # symmetric
        assert wilson(k, n, z=2.576)[0] <= lo                       # wider at 99%
    with pytest.raises(ZeroDivisionError):
        wilson(0, 0)


def test_wilson_golden():
    assert wilson(17, 48) == pytest.approx((0.23433457112685735, 0.4956120354593591), **GOLD)


# ---------------------------------------------------------------- Newcombe, Fisher, compare
def test_newcombe_published_value():
    """Newcombe (1998, Stat. Med. 17, 873-890), table II, example (a): 56/70 - 48/80, method 10: 0.0524 to 0.3339."""
    assert newcombe_diff(56, 70, 48, 80) == pytest.approx((0.0524, 0.3339), abs=1e-4)


def test_newcombe_from_the_two_wilson_intervals():
    """Method 10 is built from each side's Wilson interval (statsmodels' z)."""
    for (ka, na), (kb, nb) in [((17, 48), (6, 50)), ((3, 12), (9, 10)), ((0, 20), (5, 20))]:
        (la, ua), (lb, ub) = wilson_ci(ka, na), wilson_ci(kb, nb)
        pa, pb = ka / na, kb / nb
        d = pa - pb
        expected = (d - math.sqrt((pa - la) ** 2 + (ub - pb) ** 2), d + math.sqrt((ua - pa) ** 2 + (pb - lb) ** 2))
        assert newcombe_diff(ka, na, kb, nb) == pytest.approx(expected, abs=1e-12)


def test_fisher_published_and_scipy():
    assert fisher(3, 4, 1, 4) == pytest.approx(0.4857, abs=1e-4)    # Fisher's lady tasting tea (1935): 34/70
    assert fisher(17, 48, 6, 50) == fisher_exact([[17, 31], [6, 44]])[1]
    assert fisher(5, 10, 5, 10) == 1.0


def test_compare_golden():
    c = compare((17, 48), (6, 50))
    assert list(c) == ["diff", "lo", "hi", "p"]                     # key order: the JSON files depend on it
    assert c["diff"] == 17 / 48 - 6 / 50
    assert (c["lo"], c["hi"]) == pytest.approx((0.06595651754647627, 0.3893425605853041), **GOLD)
    assert c["p"] == pytest.approx(0.008414293221765613, **GOLD)
    assert all(type(v) is float for v in c.values())


# ---------------------------------------------------------------- Holm
def test_holm_by_hand():
    # sorted 0.01, 0.03, 0.04: 3 x 0.01 = 0.03, 2 x 0.03 = 0.06, max(0.06, 1 x 0.04) = 0.06; back in input order
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([0.2, 0.001, 0.04, 0.012]) == pytest.approx([0.2, 0.004, 0.08, 0.036])
    assert holm([0.6, 0.9]) == [1.0, 1.0]                           # capped at 1
    assert holm([]) == []


def test_holm_properties():
    rng = np.random.default_rng(4)
    for _ in range(100):
        p = rng.uniform(0, 1, int(rng.integers(1, 15)))
        h = np.array(holm(p))
        assert (h >= p - 1e-15).all() and (h <= 1).all()
        o = np.argsort(p)
        assert (np.diff(h[o]) >= -1e-15).all()                      # monotone in the order of the p-values
        assert h[o[0]] == pytest.approx(min(1, len(p) * p[o[0]]))   # the smallest gets Bonferroni's factor


# ---------------------------------------------------------------- Cochran-Armitage
def test_cochran_armitage_equals_sqrt_n_times_correlation():
    years = [2018, 2019, 2020, 2022, 2024, 2026]
    k, n = [6, 7, 9, 10, 12, 20], [48, 20, 20, 20, 20, 50]
    z, p = cochran_armitage(k, n, years)
    # Independent route: z = sqrt(N) * Pearson correlation between score and outcome over the N papers
    x = np.repeat(years, n)
    y = np.concatenate([[1] * ki + [0] * (ni - ki) for ki, ni in zip(k, n, strict=True)])
    assert z == pytest.approx(math.sqrt(len(x)) * np.corrcoef(x, y)[0, 1])
    assert 0 < p < 1
    assert cochran_armitage([n_ - k_ for k_, n_ in zip(k, n, strict=True)], n, years)[0] == pytest.approx(-z)
    assert cochran_armitage([5, 5, 5], [10, 10, 10], [1, 2, 3]) == (0.0, 1.0)  # flat shares: no trend
    assert cochran_armitage(k, n, [2 * y_ + 7 for y_ in years])[0] == pytest.approx(z)  # affine scores: same z
    assert (z, p) == pytest.approx((2.8593940165751888, 0.004244512218193549), **GOLD)


# ---------------------------------------------------------------- Cohen's kappa
def test_cohen_kappa():
    assert cohen_kappa(["yes", "no", "yes"], ["yes", "no", "yes"]) == 1
    assert cohen_kappa(["yes", "yes", "no", "no"], ["yes", "no", "yes", "no"]) == 0
    # 50 items: 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no; observed 0.7, chance 0.5, kappa 0.4
    a = ["yes"] * 25 + ["no"] * 25
    b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    assert cohen_kappa(a, b) == pytest.approx(0.4)
    assert cohen_kappa(["no"] * 4, ["no"] * 4) is None  # chance agreement 1: kappa undefined


def test_cohen_kappa_categories_leave_none_out_of_chance():
    """audit_stats.py: a missing answer (None) counts in the observed agreement, not in the chance agreement."""
    a, b = ["yes", "no", None, "yes"], ["yes", "no", None, "no"]
    po, pe = 3 / 4, (2 / 4) * (1 / 4) + (1 / 4) * (2 / 4)
    assert cohen_kappa(a, b, categories=["no", "yes"]) == pytest.approx((po - pe) / (1 - pe))
    pe_all = pe + (1 / 4) * (1 / 4)
    assert cohen_kappa(a, b) == pytest.approx((po - pe_all) / (1 - pe_all))


# ---------------------------------------------------------------- probability of improvement
def test_probability_of_improvement():
    assert probability_of_improvement(np.array([1.0, 2.0, 3.0]), np.array([2.0])) == 0.5  # 1/3 + 1/2 x 1/3
    x, y = np.array([3.0, 4.0]), np.array([1.0, 2.0])
    assert probability_of_improvement(x, y) == 1.0 and probability_of_improvement(y, x) == 0.0
    rng = np.random.default_rng(5)
    for _ in range(20):
        a, b = rng.integers(0, 5, 7).astype(float), rng.integers(0, 5, 9).astype(float)
        assert probability_of_improvement(a, b) + probability_of_improvement(b, a) == pytest.approx(1)
