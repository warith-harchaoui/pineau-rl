"""The reading grid (study/GRILLE-en.md): reading files, harmonisation overrides, final values, validation.

A reading file is one JSON per paper and reader, in <root>/<reader>/<id>.json (study/codes/ for the v1 grid,
study/codes_v2/ for v2):

    {"id": "ML14", "criteria": {"Q1": {"value": "yes", "quote": "...", "page": 3}, ..., "Y3": {"value": 5, ...}}}

The harmonisation (overrides.json for v1, overrides_v2.json for v2) is {criterion: {paper id: value}}; keys starting
with "_" are comments. The final value of a criterion has three semantics, kept apart because the scripts differ:
`value_v1` (one reading and its overrides), `value` (the v2 reading when it has the criterion, else the v1 one,
optionally Y3 turned into yes/no and a missing paper giving None or an error).
"""
from __future__ import annotations

import glob
import json
import os
import re
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Any

__all__ = ["V1", "V2", "INT", "YNA", "KINDS", "FAMILIES", "Record", "Overrides", "load_overrides", "list_readers",
           "iter_reads", "load_reads", "y3_yes_no", "value_v1", "value", "tally", "segments", "is_note", "validate"]

V1 = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X1", "X2", "X3", "X4", "X5", "X6", "X7"]  # Pineau's + ours
V2 = [f"Y{i}" for i in range(1, 13)]                                                             # écart 12
INT = {"X1", "X6", "Y3"}                     # integers (or null): seeds, families, number of runs
YNA = {"yes", "no", "na"}
KINDS = {"std", "se", "ci", "iqr", "minmax", "other"}  # the kind of spread of Y11
FAMILIES = ("llm", "classic", "theory")      # X5

Record = dict[str, Any]
Overrides = dict[str, dict[str, Any]]


def load_overrides(path: str, missing_ok: bool = False) -> Overrides:
    """{criterion: {paper id: value}} from a harmonisation file, comment keys ("_...") left out.
    A missing file raises FileNotFoundError, or gives {} with `missing_ok`."""
    if missing_ok and not os.path.exists(path):
        return {}
    with open(path) as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def list_readers(root: str, pattern: str = "*") -> list[str]:
    """The reader folders of root matching pattern, sorted by name (e.g. list_readers("codes_v2", "K*"))."""
    return sorted(os.path.basename(x) for x in glob.glob(f"{root}/{pattern}"))


def iter_reads(root: str, readers: Iterable[str]) -> Iterator[tuple[str, Record]]:
    """(reader, record) for every file of <root>/<reader>/*.json, readers in the given order, files sorted."""
    for d in readers:
        for f in sorted(glob.glob(f"{root}/{d}/*.json")):
            with open(f) as fh:
                yield d, json.load(fh)


def load_reads(root: str, readers: Iterable[str]) -> dict[str, Record]:
    """{paper id: record} over the readers in the given order; a later reader's reading of a paper replaces an
    earlier one (load("ABCDEF") of study/load.py is load_reads("codes", "ABCDEF"))."""
    return {r["id"]: r for _, r in iter_reads(root, readers)}


def y3_yes_no(v: int) -> str:
    """Y3 (number of tasks behind the main conclusion) as a yes/no criterion: yes when at least 2."""
    return "yes" if v >= 2 else "no"


def value_v1(rec: Record, k: str, overrides: Overrides, strict: bool = False) -> Any:
    """Final value of criterion k in ONE reading: the override for this paper if any, else the reader's value.
    A criterion absent from the reading gives None, or a KeyError with `strict`. No Y3 conversion.
    (analyze_final.py, audit_stats.py; title_filter_compare.py with strict and the v2 overrides.)"""
    raw = rec["criteria"][k]["value"] if strict else rec["criteria"].get(k, {}).get("value")
    return overrides.get(k, {}).get(rec["id"], raw)


def value(pid: str, k: str, v2: Mapping[str, Record], v1: Mapping[str, Record], ov2: Overrides, ov1: Overrides,
          y3: bool = True, missing_ok: bool = True) -> Any:
    """Final value of criterion k for paper pid across both grids: the v2 reading (with ov2) when it has the
    criterion, else the v1 reading (with ov1).

    y3:         Y3 (an integer) turned into yes/no, yes when at least 2 (extension_stats.py, trajectory.py,
                robustness.py); False keeps the integer (falsify_no.py, checklist.py).
    missing_ok: a paper in neither grid gives None; False raises KeyError (checklist.py).
    """
    if pid in v2 and k in v2[pid]["criteria"]:
        v = ov2.get(k, {}).get(pid, v2[pid]["criteria"][k].get("value"))
    elif pid in v1 or not missing_ok:
        v = ov1.get(k, {}).get(pid, v1[pid]["criteria"].get(k, {}).get("value"))
    else:
        return None
    if y3 and k == "Y3" and v is not None:
        return y3_yes_no(v)
    return v


def tally(values: Iterable[Any]) -> tuple[int, int]:
    """(number of "yes", number of "yes" or "no"): a share's numerator and denominator, "na" and None left out."""
    vs = [v for v in values if v in ("yes", "no")]
    return sum(v == "yes" for v in vs), len(vs)


# Quotes: what of a quote must be found in the paper (check_codes.py compares it with the PDF's text).
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"-\s*\n\s*", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _norm(s))


_NOTE = re.compile(r"\[(?!\.\.\.\])[^\]]*\]")  # a reader's note in brackets, e.g. [no std in Table 3]


def segments(quote: str) -> list[str]:
    """The parts of a quote that must appear in the paper: the reader's bracketed notes are removed, and a
    quote stitched with [...] or " / " is split into its pieces. Pieces under 12 letters are too short to test."""
    q = _NOTE.sub(" ", quote)
    parts = re.split(r"\[\.\.\.\]|\.\.\.|…|\s/\s", q)
    return [p for p in parts if len(_alnum(p)) >= 12]


def is_note(quote: str) -> bool:
    """True when a "quote" is a reader's note (absent, not applicable...) rather than text of the paper."""
    q = quote.strip().lower()
    return q.startswith(("absent", "non applicable", "sans objet", "n/a", "na ", "aucun", "pas d'", "pas de ")) \
        or not segments(quote)


def validate(rec: Record, need_v1: bool = True, q1: Any = None, x2: Any = None, q4: Any = None,
             found: Callable[[str, str], bool] | None = None) -> list[str]:
    """The problems of one v2 reading file, as messages (empty list: the file is valid). PROTOCOL.md, écarts 12, 14.

    Schema: every criterion of V2 (and of V1 when `need_v1`, i.e. the paper was not read in v1) present, yes/no/na,
    integers or null for INT, X5 in FAMILIES, a `kind` in KINDS when Y11 is yes, a quote for each criterion.
    Scope: Q1 no -> everything else na; Y2 and Y11 na iff X2 no; Y4 na if Y3 is 1; Y5 na iff Q4 na. q1, x2, q4 are
    the paper's final v1 values (from this file, or from its v1 reading and overrides when the file lacks them).
    found(quote, id): True when the quote is in the paper's text; None skips that check (no PDF needed).
    """
    pid, C, errs = rec["id"], rec["criteria"], []
    for k in V2 + (V1 if need_v1 else []):
        if k not in C:
            errs.append(f"{k} missing")
            continue
        c, v = C[k], C[k].get("value")
        if k in INT:
            if v is not None and not (isinstance(v, int) and v >= 0):
                errs.append(f"{k} must be an integer or null, got {v!r}")
        elif k == "X5":
            if v not in FAMILIES:
                errs.append(f"X5 must be llm/classic/theory, got {v!r}")
        elif v not in YNA:
            errs.append(f"{k} must be yes/no/na, got {v!r}")
        if k == "Y11" and v == "yes" and c.get("kind") not in KINDS:
            errs.append(f"Y11 yes needs kind in {sorted(KINDS)}")
        q = c.get("quote") or ""
        if not q:
            errs.append(f"{k} has no quote")
        elif found is not None and not is_note(q) and not found(q, pid):
            errs.append(f"{k} quote not found in the PDF: {q[:80]!r}")

    def val(k: str) -> Any:
        return C.get(k, {}).get("value")

    if q1 == "no":
        bad = [k for k in V2 + [x for x in V1 if x not in ("Q1", "X5")] if k in C and val(k) not in ("na", None)]
        if bad:
            errs.append(f"Q1 is no, so these must be na: {bad}")
    else:
        for k in ("Y2", "Y11"):
            if (val(k) == "na") != (x2 == "no"):
                errs.append(f"{k} is na iff X2 is no (X2={x2}, {k}={val(k)})")
        if val("Y3") == 1 and val("Y4") != "na":
            errs.append("Y3 is 1, so Y4 must be na")
        if (val("Y5") == "na") != (q4 == "na"):
            errs.append(f"Y5 is na iff Q4 is na (Q4={q4}, Y5={val('Y5')})")
    return errs
