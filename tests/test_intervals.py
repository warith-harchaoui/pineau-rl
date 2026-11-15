"""Wilson intervals, Cohen's kappa and the Cochran-Armitage trend test of the survey (study/)."""
import math

import numpy as np
import pytest
from statsmodels.stats.proportion import proportion_confint

from conftest import extract

CASES = [(0, 10), (1, 10), (5, 10), (10, 10), (17, 48), (3, 50), (49, 50)]


def test_analyze_wilson_matches_statsmodels():
    from analyze import wilson  # analyze.py runs its computation under __main__ only
    for k, n in CASES:
        p, lo, hi = wilson(k, n)
        ref = proportion_confint(k, n, alpha=0.05, method="wilson")
        assert p == k / n
        assert lo == pytest.approx(ref[0], abs=1e-4) and hi == pytest.approx(ref[1], abs=1e-4)
    assert all(math.isnan(x) for x in wilson(0, 0))


@pytest.mark.parametrize("path", ["study/checklist.py", "study/title_filter.py"])
def test_other_wilson_copies_agree(path):
    from analyze import wilson as reference
    w = extract(path, ["wilson"])["wilson"]
    for k, n in CASES:
        assert w(k, n) == pytest.approx(list(reference(k, n)[1:]), abs=1e-12)


def test_cohen_kappa():
    kappa = extract("study/agree_v2.py", ["cohen_kappa"])["cohen_kappa"]
    assert kappa(["yes", "no", "yes"], ["yes", "no", "yes"]) == 1
    assert kappa(["yes", "yes", "no", "no"], ["yes", "no", "yes", "no"]) == 0
    # 50 items: 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no; observed 0.7, chance 0.5, kappa 0.4
    a = ["yes"] * 25 + ["no"] * 25
    b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    assert kappa(a, b) == pytest.approx(0.4)
    assert kappa(["no"] * 4, ["no"] * 4) is None  # chance agreement 1: kappa undefined


def test_cochran_armitage_equals_sqrt_n_times_correlation():
    ca = extract("study/trajectory.py", ["cochran_armitage"])["cochran_armitage"]
    years = [2018, 2019, 2020, 2022, 2024, 2026]
    k, n = [6, 7, 9, 10, 12, 20], [48, 20, 20, 20, 20, 50]
    z, p = ca(k, n, years)
    # Independent route: z = sqrt(N) * Pearson correlation between score and outcome over the N papers
    x = np.repeat(years, n)
    y = np.concatenate([[1] * ki + [0] * (ni - ki) for ki, ni in zip(k, n)])
    assert z == pytest.approx(math.sqrt(len(x)) * np.corrcoef(x, y)[0, 1])
    assert 0 < p < 1
    assert ca([n_ - k_ for k_, n_ in zip(k, n)], n, years)[0] == pytest.approx(-z)  # flip the outcome, flip the sign
    assert ca([5, 5, 5], [10, 10, 10], [1, 2, 3]) == (0.0, 1.0)  # flat shares: no trend
