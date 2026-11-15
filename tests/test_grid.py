"""pineau_rl.grid: reading folders, overrides, the three value semantics and the validator, on fabricated readings."""
import json

import pytest

from pineau_rl.grid import (
    V1,
    V2,
    is_note,
    iter_reads,
    list_readers,
    load_overrides,
    load_reads,
    segments,
    tally,
    validate,
    value,
    value_v1,
    y3_yes_no,
)


def rec(pid, **values):
    return {"id": pid, "criteria": {k: {"value": v, "quote": "q"} for k, v in values.items()}}


# v1 readings of P1 and P2, v2 readings of P1 and P3, and the harmonisation of both grids
V1R = {"P1": rec("P1", Q1="yes", Q5="no", X2="yes", X5="classic"), "P2": rec("P2", Q1="no", Q5="yes")}
V2R = {"P1": rec("P1", Q5="yes", Y3=1, Y9="no"), "P3": rec("P3", Q1="yes", Q5="no", Y3=3)}
OV1 = {"Q5": {"P1": "yes", "P2": "no"}}
OV2 = {"Y9": {"P1": "yes"}, "Q5": {"P3": "yes"}}


def test_v1_semantics():
    """analyze_final.py, audit_stats.py: one reading, its override if any; absent -> None (or KeyError if strict)."""
    assert value_v1(V1R["P1"], "Q5", OV1) == "yes"        # overridden
    assert value_v1(V1R["P1"], "X2", OV1) == "yes"        # reader's value
    assert value_v1(V1R["P1"], "Q8", OV1) is None         # absent
    assert value_v1(V1R["P1"], "Q8", {"Q8": {"P1": "no"}}) == "no"  # an override fills an absent criterion
    with pytest.raises(KeyError):
        value_v1(V1R["P1"], "Q8", OV1, strict=True)       # title_filter_compare.py
    assert value_v1(V2R["P1"], "Y3", {}) == 1             # no Y3 conversion


def test_v2_with_v1_fallback_and_y3():
    """extension_stats.py, trajectory.py, robustness.py: v2 when it has k, else v1; Y3 as yes/no; unknown -> None."""
    v = lambda pid, k: value(pid, k, V2R, V1R, OV2, OV1)
    assert v("P1", "Q5") == "yes"                          # v2 reading (v1 said no, overridden to yes: not used)
    assert v("P1", "Y9") == "yes"                          # v2 override
    assert v("P1", "X5") == "classic"                      # not in v2: falls back to v1
    assert v("P1", "Q8") is None                           # in neither reading of a known paper
    assert v("P1", "Y3") == "no" and v("P3", "Y3") == "yes"  # 1 run: no; 3 runs: yes
    assert v("P2", "Q5") == "no"                           # v1 only, overridden
    assert v("P3", "Q5") == "yes"                          # v2 only, overridden
    assert v("P4", "Q5") is None                           # unknown paper


def test_v2_without_y3_conversion_and_strict_paper():
    """falsify_no.py: Y3 stays an integer; checklist.py: also an unknown paper is an error."""
    assert value("P3", "Y3", V2R, V1R, OV2, OV1, y3=False) == 3
    assert value("P4", "Q5", V2R, V1R, OV2, OV1, y3=False) is None
    assert value("P3", "Y3", V2R, V1R, OV2, OV1, y3=False, missing_ok=False) == 3
    assert value("P2", "Q5", V2R, V1R, OV2, OV1, y3=False, missing_ok=False) == "no"
    with pytest.raises(KeyError):
        value("P4", "Q5", V2R, V1R, OV2, OV1, y3=False, missing_ok=False)


def test_y3_and_tally():
    assert [y3_yes_no(n) for n in (0, 1, 2, 10)] == ["no", "no", "yes", "yes"]
    assert tally(["yes", "no", "na", None, "yes", 3]) == (2, 3)
    assert tally([]) == (0, 0)


def test_overrides_and_folders(tmp_path, in_dir):
    in_dir(tmp_path)
    (tmp_path / "ov.json").write_text(json.dumps({"_note": "why", "Q5": {"P1": "yes"}}))
    assert load_overrides("ov.json") == {"Q5": {"P1": "yes"}}
    assert load_overrides("absent.json", missing_ok=True) == {}
    with pytest.raises(FileNotFoundError):
        load_overrides("absent.json")
    for reader, pid, v in (("B", "P1", "no"), ("A", "P2", "yes"), ("A", "P1", "yes"), ("K2", "P3", "no")):
        (tmp_path / "codes" / reader).mkdir(parents=True, exist_ok=True)
        (tmp_path / "codes" / reader / f"{pid}.json").write_text(json.dumps(rec(pid, Q5=v)))
    assert list_readers("codes") == ["A", "B", "K2"] and list_readers("codes", "K*") == ["K2"]
    assert [(d, r["id"]) for d, r in iter_reads("codes", "BA")] == [("B", "P1"), ("A", "P1"), ("A", "P2")]
    assert load_reads("codes", "AB")["P1"]["criteria"]["Q5"]["value"] == "no"  # the later reader wins
    assert load_reads("codes", "BA")["P1"]["criteria"]["Q5"]["value"] == "yes"
    assert list(load_reads("codes", "AB")) == ["P1", "P2"]


def full(**changes):
    """A valid v2 reading of a paper not read in v1: every criterion, consistent scopes."""
    c = {k: {"value": "yes", "quote": "The code is available at github.com/x/y."} for k in V1 + V2}
    c["X1"]["value"], c["X6"]["value"], c["Y3"]["value"], c["X5"]["value"] = 5, None, 3, "classic"
    c["Y11"]["kind"] = "std"
    for k, v in changes.items():
        c[k]["value"] = v
    return {"id": "P9", "criteria": c}


def test_validate_accepts_a_valid_reading():
    r = full()
    assert validate(r, q1="yes", x2="yes", q4="yes") == []
    assert validate(r, q1="yes", x2="yes", q4="yes", found=lambda q, pid: True) == []


def test_validate_reports_each_problem():
    r = full(Q3="maybe", X1=-1, X5="robotics", Y3=1)
    del r["criteria"]["Q8"]
    r["criteria"]["Y11"].pop("kind")
    r["criteria"]["Q2"]["quote"] = ""
    errs = validate(r, q1="yes", x2="yes", q4="yes")
    assert "Q8 missing" in errs
    assert "Q3 must be yes/no/na, got 'maybe'" in errs
    assert "X1 must be an integer or null, got -1" in errs
    assert "X5 must be llm/classic/theory, got 'robotics'" in errs
    assert any(e.startswith("Y11 yes needs kind") for e in errs)
    assert "Q2 has no quote" in errs
    assert "Y3 is 1, so Y4 must be na" in errs
    assert validate(full(), need_v1=False, q1="yes", x2="yes", q4="yes") == []
    no_v1 = {"id": "P9", "criteria": {k: v for k, v in full()["criteria"].items() if k in V2}}
    assert validate(no_v1, need_v1=False, q1="yes", x2="yes", q4="yes") == []   # paper read in v1: v2 suffices
    assert "Q1 missing" in validate(no_v1, q1="yes", x2="yes", q4="yes")


def test_validate_scope_rules():
    assert validate(full(), q1="no", x2="yes", q4="yes")[0].startswith("Q1 is no, so these must be na")
    na = full(**{k: "na" for k in V2 + V1 if k not in ("Q1", "X5", "X1", "X6", "Y3")}, X1=None, Y3=None)
    assert validate(na, q1="no") == []
    assert validate(full(), q1="yes", x2="no", q4="yes") == [
        "Y2 is na iff X2 is no (X2=no, Y2=yes)", "Y11 is na iff X2 is no (X2=no, Y11=yes)"]
    assert validate(full(), q1="yes", x2="yes", q4="na") == ["Y5 is na iff Q4 is na (Q4=na, Y5=yes)"]


def test_validate_quotes():
    seen = []
    r = full()
    r["criteria"]["Q4"]["quote"] = "absent: no table of baseline settings"
    errs = validate(r, q1="yes", x2="yes", q4="yes", found=lambda q, pid: seen.append(pid) or False)
    assert len(errs) == len(V1 + V2) - 1 and all("quote not found" in e for e in errs)  # the note is not looked for
    assert set(seen) == {"P9"}


def test_segments_and_notes():
    assert segments("We use 10 random seeds [...] and report the standard deviation") == [
        "We use 10 random seeds ", " and report the standard deviation"]
    assert segments("short [x] / tiny") == []
    assert segments("results over five seeds [Table 2] are averaged") == ["results over five seeds   are averaged"]
    assert is_note("Absent: no code link") and is_note("n/a") and is_note("ok")
    assert not is_note("Code is available at github.com/x")
