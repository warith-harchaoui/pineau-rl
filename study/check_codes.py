"""Mechanical check of every reading file in codes_v2/ (PROTOCOL.md, écarts 12 and 14), before any percentage.

For each file: schema (criteria present, allowed values, integers, `kind` for Y11), scope rules (Q1 no -> all na;
Y2 and Y11 na iff X2 no; Y4 na if Y3 is 1; Y5 na iff Q4 na), and quotes: every quote that is not an
"absent" note must be found in the paper's text (pdftotext, main PDF plus supplement), fuzzily (spaces,
hyphenation, ligatures), with a similarity threshold of 0.9. For papers already read in v1, the v1 values
(Q1, Q4, X2) come from codes/ with the harmonisation of overrides.json.
Exit code 1 on any problem; the list says which file goes back to its reader.
Run from study/: python3 check_codes.py [codes_v2/<reader> ...]
"""
import difflib, glob, json, re, subprocess, sys, unicodedata
from pathlib import Path
from pineau_rl.grid import load_overrides, segments, validate
from load import load

ov = load_overrides("overrides.json")
OLD = load("ABCDEF")
_text = {}


def norm(s):
    s = unicodedata.normalize("NFKC", s).replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"-\s*\n\s*", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def text(pid):
    if pid not in _text:
        t = ""
        for f in (f"pdf/{pid}.pdf", f"pdf/{pid}-supp.pdf"):
            if Path(f).exists():
                t += subprocess.run(["pdftotext", "-layout", f, "-"], capture_output=True, text=True).stdout
        _text[pid] = norm(t)
    return _text[pid]


ALNUM = lambda s: re.sub(r"[^a-z0-9]", "", norm(s))


def found(quote, pid, threshold=0.9):
    """True when every piece of the quote is in the paper's text, compared on letters and digits only (so that
    spaces, hyphenation, ligatures and maths symbols do not matter), with a fuzzy fallback at 90% per piece."""
    t = text(pid)
    if not t:
        return False
    ta = re.sub(r"[^a-z0-9]", "", t)
    for seg in segments(quote):
        sa = ALNUM(seg)
        if sa in ta:
            continue
        n, ok = len(sa), False
        for anchor in {sa[:12], sa[n // 2: n // 2 + 12], sa[-12:]}:
            for m in re.finditer(re.escape(anchor), ta):
                win = ta[max(0, m.start() - n): m.start() + 2 * n]
                sm = difflib.SequenceMatcher(None, sa, win, autojunk=False)
                if sum(x.size for x in sm.get_matching_blocks()) / n >= threshold:
                    ok = True
                    break
            if ok:
                break
        if not ok:
            return False
    return True


def v1value(pid, rec, k):  # this file's raw value if it has k, else the v1 reading with overrides.json
    if k in rec["criteria"]:
        return rec["criteria"][k].get("value")
    if pid in OLD:
        return ov.get(k, {}).get(pid, OLD[pid]["criteria"].get(k, {}).get("value"))
    return None


def check(path):
    """Schema and scope rules (pineau_rl.grid.validate), every quote looked for in the PDF's text."""
    rec = json.load(open(path))
    pid = rec["id"]
    return validate(rec, need_v1=pid not in OLD, q1=v1value(pid, rec, "Q1"), x2=v1value(pid, rec, "X2"),
                    q4=v1value(pid, rec, "Q4"), found=found)


dirs = sys.argv[1:] or sorted(glob.glob("codes_v2/*"))
bad = 0
for d in dirs:
    for f in sorted(glob.glob(f"{d}/*.json")):
        errs = check(f)
        if errs:
            bad += 1
            print(f"{f}:")
            for e in errs:
                print("   ", e)
print(f"{bad} file(s) to send back")
sys.exit(1 if bad else 0)
