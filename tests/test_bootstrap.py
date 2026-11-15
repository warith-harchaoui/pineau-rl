"""pineau_rl.bootstrap: rliable's intervals draw from NumPy's global generator; seeded once, they repeat exactly."""
import numpy as np
import pytest
from rliable import metrics
from rliable.library import get_interval_estimates

from pineau_rl.bootstrap import improvement_interval, iqm, iqm_interval, probability_of_improvement_bootstrap
from pineau_rl.stats import probability_of_improvement

X = np.array([3.0, 1, 4, 1, 5, 9, 2, 6, 5, 3])
Y = np.array([2.0, 7, 1, 8, 2, 8, 1, 8, 2, 8])
GOLD = dict(rel=1e-12)  # the last digits of a bootstrap may move with the processor; the counts may not


def test_iqm_is_the_mean_of_the_middle_half():
    assert iqm(np.arange(1, 9.0)) == 4.5                     # mean of 3, 4, 5, 6
    assert iqm(np.array([0.0, 10, 10, 1000])) == 10           # robust to the outlier


def test_iqm_interval_golden_under_a_fixed_global_seed():
    np.random.seed(2026)
    est = iqm_interval({"x": X, "y": Y}, reps=200)
    assert list(est) == ["x", "y"]
    assert est["x"] == pytest.approx((3.6666666666666665, 2.0, 5.004166666666667), **GOLD)
    assert est["y"] == pytest.approx((4.833333333333333, 1.8333333333333333, 7.670833333333334), **GOLD)


def test_iqm_interval_depends_only_on_the_global_seed():
    np.random.seed(7)
    a = iqm_interval({"x": X}, reps=300, random_state=np.random.RandomState(1))
    np.random.seed(7)
    b = iqm_interval({"x": X}, reps=300, random_state=np.random.RandomState(99))  # ignored by rliable 1.2.0
    assert a == b
    c = iqm_interval({"x": X}, reps=300)                      # the generator moved on: another interval
    assert c["x"][0] == a["x"][0] and c != a


def test_iqm_interval_is_rliable():
    np.random.seed(11)
    est = iqm_interval({"x": X}, reps=300)
    np.random.seed(11)
    pe, ci = get_interval_estimates({"x": X[:, None]}, lambda s: np.array([metrics.aggregate_iqm(s)]), reps=300)
    assert est["x"] == (pe["x"][0], ci["x"][0][0], ci["x"][1][0])


def test_improvement_interval_golden_and_point():
    np.random.seed(2026)
    p, lo, hi = improvement_interval(X, Y, reps=200)
    assert p == pytest.approx(probability_of_improvement(X, Y))
    assert (p, lo, hi) == pytest.approx((0.455, 0.164875, 0.73025), **GOLD)
    assert lo <= p <= hi


def test_probability_of_improvement_bootstrap_uses_only_its_generator():
    np.random.seed(0)
    before = np.random.get_state()[1].copy()
    p, ci = probability_of_improvement_bootstrap(X, Y, np.random.default_rng(2018), reps=500)
    assert (np.random.get_state()[1] == before).all()        # the global generator is untouched
    assert (p, *ci) == pytest.approx((0.455, 0.17, 0.72), **GOLD)
    assert (p, ci) == probability_of_improvement_bootstrap(X, Y, np.random.default_rng(2018), reps=500)
