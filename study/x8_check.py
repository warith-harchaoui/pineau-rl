"""Mechanical check of the X8 reading files (PROTOCOL.md, deviation 32): codes_x8/<reader>/<id>.json.

Format: {"id", "coder", "criteria": {"X8": {"value": yes/no/na, "source": seeds/pooled/episodes/items/unstated/other,
"quote", "page"}}, "doubts"}. Every quote that is not an "absent" note must be found in the paper's text (the function
of check_codes.py, threshold 0.9); value yes needs source seeds; na is not allowed (every paper of the sample has X2 yes).
Run from study/: python3 x8_check.py codes_x8/<reader> ...  (exit code 1 on any problem)
"""
import glob, json, sys
from check_codes import found
from pineau_rl.grid import is_note

SOURCES = {"seeds", "pooled", "episodes", "items", "unstated", "other"}


def check(path):
    rec, errs = json.load(open(path)), []
    c = rec.get("criteria", {}).get("X8")
    if not c:
        return ["X8 missing"]
    if c.get("value") not in ("yes", "no"):
        errs.append(f"X8 must be yes/no (X2 is yes for every paper), got {c.get('value')!r}")
    if c.get("source") not in SOURCES:
        errs.append(f"source must be one of {sorted(SOURCES)}, got {c.get('source')!r}")
    if c.get("value") == "yes" and c.get("source") != "seeds":
        errs.append("X8 yes needs source seeds")
    q = c.get("quote") or ""
    if not q:
        errs.append("X8 has no quote")
    elif not is_note(q) and not found(q, rec["id"]):
        errs.append(f"quote not found in the PDF: {q[:80]!r}")
    return errs


if __name__ == "__main__":
    bad = 0
    for d in sys.argv[1:]:
        for f in sorted(glob.glob(f"{d}/*.json")):
            if (errs := check(f)):
                bad += 1
                print(f"{f}:", *errs, sep="\n    ")
    print(f"{bad} file(s) to send back")
    sys.exit(1 if bad else 0)
