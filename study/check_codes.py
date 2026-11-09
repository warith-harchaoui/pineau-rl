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
from load import load

V1 = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X1", "X2", "X3", "X4", "X5", "X6", "X7"]
V2 = ["Y%d" % i for i in range(1, 13)]
INT = {"X1", "X6", "Y3"}
YNA = {"yes", "no", "na"}
KINDS = {"std", "se", "ci", "iqr", "minmax", "other"}
ov = {k: v for k, v in json.load(open("overrides.json")).items() if not k.startswith("_")}
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
NOTE = re.compile(r"\[(?!\.\.\.\])[^\]]*\]")  # a reader's note in brackets, e.g. [no std in Table 3]


def segments(quote):
    """The parts of a quote that must appear in the paper: the reader's bracketed notes are removed, and a
    quote stitched with [...] or " / " is split into its pieces. Pieces under 12 letters are too short to test."""
    q = NOTE.sub(" ", quote)
    parts = re.split(r"\[\.\.\.\]|\.\.\.|…|\s/\s", q)
    return [p for p in parts if len(ALNUM(p)) >= 12]


def is_note(quote):
    q = quote.strip().lower()
    return q.startswith(("absent", "non applicable", "sans objet", "n/a", "na ", "aucun", "pas d'", "pas de ")) or not segments(quote)


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


def v1value(pid, rec, k):
    if k in rec["criteria"]:
        return rec["criteria"][k].get("value")
    if pid in OLD:
        return ov.get(k, {}).get(pid, OLD[pid]["criteria"].get(k, {}).get("value"))
    return None


def check(path):
    rec = json.load(open(path))
    pid, C, errs = rec["id"], rec["criteria"], []
    need = V2 + ([] if pid in OLD else V1)
    for k in need:
        if k not in C:
            errs.append(f"{k} missing")
            continue
        c, v = C[k], C[k].get("value")
        if k in INT:
            if v is not None and not (isinstance(v, int) and v >= 0):
                errs.append(f"{k} must be an integer or null, got {v!r}")
        elif k == "X5":
            if v not in ("llm", "classic", "theory"):
                errs.append(f"X5 must be llm/classic/theory, got {v!r}")
        elif v not in YNA:
            errs.append(f"{k} must be yes/no/na, got {v!r}")
        if k == "Y11" and v == "yes" and c.get("kind") not in KINDS:
            errs.append(f"Y11 yes needs kind in {sorted(KINDS)}")
        q = c.get("quote") or ""
        if not q:
            errs.append(f"{k} has no quote")
        elif not is_note(q) and not found(q, pid):
            errs.append(f"{k} quote not found in the PDF: {q[:80]!r}")
    q1, x2, q4 = v1value(pid, rec, "Q1"), v1value(pid, rec, "X2"), v1value(pid, rec, "Q4")
    val = lambda k: C.get(k, {}).get("value")
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
