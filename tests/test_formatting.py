"""The number formatters of docs/check_numbers.py (pineau_rl.fmt): every figure of the two texts goes through them."""
from decimal import Decimal

from pineau_rl.fmt import ci, half_up, num, pct, pts


def test_half_up_rounds_half_away_from_zero():
    assert half_up(1.15, 1) == Decimal("1.2")  # binary float 1.15 is 1.1499..., the reader's rounding is not
    assert half_up(2.5) == Decimal("3") and round(2.5) == 2  # Python rounds half to even
    assert half_up(-66.5) == Decimal("-67")
    assert half_up(0.125, 2) == Decimal("0.13")


def test_pct_in_both_languages():
    assert pct(0.125) == "13 %"
    assert pct(0.125, lang="en") == "13%"
    assert pct(0.0515, 1) == "5,2 %"
    assert pct(0.0515, 1, lang="en") == "5.2%"
    assert pct(1) == "100 %"


def test_num_thousands_separator():
    assert num(1252) == "1 252"
    assert num(1252, lang="en") == "1,252"
    assert num(2422.5, lang="en") == "2,423"


def test_ci_in_percentage_points():
    assert ci(0.1234, 0.4567) == "[12, 46]"
    assert ci(0.005, 0.995) == "[1, 100]"


def test_pts_signs_use_the_minus_sign():
    lo, hi = pts({"lo": -0.054, "hi": 0.123})
    assert lo == "−5" and hi == "+12"
    assert pts({"lo": 0.0, "hi": 0.0}, lang="en") == ("+0", "+0")
