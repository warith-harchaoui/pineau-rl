"""Experiment B1: the two readings of Henderson et al.'s t statistic (sim/analysis/b1_trpo.py, b1_script.py)."""
import numpy as np
import pytest
from scipy import stats

from conftest import extract

readings = extract("sim/analysis/b1_trpo.py", ["readings"])["readings"]
script = extract("sim/analysis/b1_script.py", ["script"])["script"]


def test_readings_against_scipy():
    rng = np.random.default_rng(0)
    a, b = rng.normal(1000, 300, (5, 20)), rng.normal(1100, 300, (5, 20))
    r = readings(a, b)
    per_point = stats.ttest_ind(a, b, axis=0, equal_var=False)
    assert r["mean_t"][0] == pytest.approx(per_point.statistic.mean())
    assert r["mean_p"][1] == pytest.approx(per_point.pvalue.mean())
    pooled = stats.ttest_ind(a.ravel(), b.ravel(), equal_var=False)
    assert r["pooled"] == pytest.approx((pooled.statistic, pooled.pvalue))


def test_script_is_welch_from_the_averaged_progress():
    rng = np.random.default_rng(1)
    M, S = rng.normal(1000, 300, (10, 20)), rng.uniform(5, 50, (10, 20))
    a, b = np.arange(5), np.arange(5, 10)
    t, p = script(M, S, a, b, 10)
    ref = stats.ttest_ind_from_stats(M[a].mean(0), S[a].mean(0), 10, M[b].mean(0), S[b].mean(0), 10, equal_var=False)
    assert (t, p) == pytest.approx((ref.statistic.mean(), ref.pvalue.mean()))


@pytest.mark.filterwarnings("ignore:Precision loss:RuntimeWarning")  # group b has zero variance on purpose
def test_script_ignores_the_spread_between_seeds():
    """The mechanism behind a |t| of 9: the test sees the spread between episodes, never between random seeds."""
    M = np.array([[0.0] * 20, [2000.0] * 20, [1000.0] * 20,       # group a: seeds at 0, 2000, 1000 (mean 1000)
                  [1100.0] * 20, [1100.0] * 20, [1100.0] * 20])   # group b: three identical seeds at 1100
    S = np.full_like(M, 20.0)                                     # small spread between evaluation episodes
    t, p = script(M, S, np.arange(3), np.arange(3, 6), 10)
    assert abs(t) > 9.0916 and p < 1e-6                           # "significant" beyond Henderson's |t|
    welch = stats.ttest_ind(M[:3, -1], M[3:, -1], equal_var=False)
    assert welch.pvalue > 0.5                                      # the seeds themselves show nothing
