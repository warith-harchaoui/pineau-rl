"""Mechanical check of the reading files of deviation 36 (PROTOCOL.md): codes_r36/<reader>/<id>.json.

Format: {"id", "coder", "criteria": {"Q5": {"value", "link_kind", "quote", "page"}, "Y9", "X7", "X2": {"value",
"quote", "page"}}, "doubts"}. Values yes/no only (every paper of the sample has experiments); Q5 link_kind among
code, project_page, none, and yes needs code or project_page. Every quote that is not an "absent" note must be found
in the paper's text (the function of check_codes.py, threshold 0.9); a yes needs a real quote.
Run from study/: python3 r36_check.py codes_r36/<reader> ...  (exit code 1 on any problem)
"""
import glob, json, sys
from check_codes import found
from pineau_rl.grid import is_note

CRIT = ("Q5", "Y9", "X7", "X2")
KINDS = {"code", "project_page", "none"}


def check(path):
    try:
        rec = json.load(open(path))
    except json.JSONDecodeError as e:
        return [f"not valid JSON: {e}"]
    errs, crit = [], rec.get("criteria", {})
    for k in CRIT:
        c = crit.get(k)
        if not c:
            errs.append(f"{k} missing")
            continue
        if c.get("value") not in ("yes", "no"):
            errs.append(f"{k} must be yes/no, got {c.get('value')!r}")
        if k == "Q5":
            if c.get("link_kind") not in KINDS:
                errs.append(f"Q5 link_kind must be one of {sorted(KINDS)}, got {c.get('link_kind')!r}")
            elif c.get("value") == "yes" and c["link_kind"] == "none":
                errs.append("Q5 yes needs link_kind code or project_page")
        q = c.get("quote") or ""
        if not q:
            errs.append(f"{k} has no quote")
        elif is_note(q):
            if c.get("value") == "yes":
                errs.append(f"{k} yes needs a quote from the paper, not a note")
        elif not found(q, rec.get("id", "")):
            errs.append(f"{k} quote not found in the PDF: {q[:80]!r}")
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
