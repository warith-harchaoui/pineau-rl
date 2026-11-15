"""Mechanical search against the "no" decisions (PROTOCOL.md, deviation 27), step 1: the candidates.

For both samples of the main comparison (as extension_stats.py: our 50 papers of 2018, the 50 classical papers of
2026), every final "no" (after harmonisation) on Q4, Q5, Q7, Q8, X2, X7 and Y9 is set against the text of the paper and
of its supplement (pdftotext of pdf/<id>.pdf and pdf/<id>-supp.pdf), outside the references section, with the patterns
fixed in deviation 27. Each occurrence keeps 300 characters of context. Step 2, the arbiter's verdicts, is read from
falsify_verdicts.json by falsify_stats.py.

Needs the PDFs (fetch_pdfs.py) and pdftotext (poppler). Run from study/: python3 falsify_no.py -> falsify_candidates.json
"""
import glob, json, os, re, subprocess
from load import load

CRIT = ["Q4", "Q5", "Q7", "Q8", "X2", "X7", "Y9"]
PATTERNS = {  # deviation 27, verbatim
    "Q5": r"github|gitlab|bitbucket|anonymous\.4open|code (is |are |will be )?(publicly )?available|source code|our (code|implementation)|open[- ]source",
    "X7": r"gpu|tpu|cpu|core|hours?|days|wall[- ]?clock|compute|nvidia|v100|a100",
    "X2": r"±|\+/-|standard (deviation|error)|std|confidence interval|error bar|shaded|variance|percentile",
    "Y9": r"sensitivity|ablation|sweep|grid search|robust(ness)? to|effect of|different values of",
    "Q8": r"t-test|p-value|p ?<|welch|mann|wilcoxon|significan|bootstrap|kolmogorov|anova",
    "Q7": r"held[- ]out|unseen|test (environment|level|seed|task)|generali[sz]|out-of-distribution|transfer",
    "Q4": r"baselines?.{0,60}hyper-?parameter|hyper-?parameters?.{0,60}baselines?|default (hyper-?)?parameters|same hyper-?parameters",
}
CONTEXT = 150  # characters on each side: 300 in all

# The samples and the final values, as extension_stats.py
N_A3 = 36
PRIMARY = ["A2", "B2", "C2", "D2", "E2", "F2", "H1", "H2", "H3", "H4"]
ld = lambda f: {k: v for k, v in json.load(open(f)).items() if not k.startswith("_")} if os.path.exists(f) else {}
ov1, ov2 = ld("overrides.json"), ld("overrides_v2.json")
OLD = load("ABCDEF")
V2READ = {}
for d in PRIMARY + sorted(os.path.basename(x) for x in glob.glob("codes_v2/K*")):
    for f in sorted(glob.glob(f"codes_v2/{d}/*.json")):
        r = json.load(open(f))
        V2READ[r["id"]] = r


def val(pid, k):
    if pid in V2READ and k in V2READ[pid]["criteria"]:
        return ov2.get(k, {}).get(pid, V2READ[pid]["criteria"][k].get("value"))
    if pid in OLD:
        return ov1.get(k, {}).get(pid, OLD[pid]["criteria"].get(k, {}).get("value"))
    return None


ours18 = sorted(p for p in OLD if p.startswith("C")) + [x["id"] for x in json.load(open("calib_2018_v2.json"))[12:]]
all26 = sorted(p for p in OLD if not p.startswith("C"))
queue = [x["id"] for x in json.load(open("classic_queue_2026.json"))]
a3 = [p for p in queue if p in V2READ and val(p, "X5") == "classic"][:N_A3]
classic26 = sorted(p for p in all26 if val(p, "X5") == "classic") + a3
assert len(ours18) == len(classic26) == 50


def text(pid):
    """Text of the paper and its supplement, the references section cut out of each."""
    out = []
    for f in (f"pdf/{pid}.pdf", f"pdf/{pid}-supp.pdf"):
        if not os.path.exists(f):
            continue
        t = subprocess.run(["pdftotext", "-q", "-enc", "UTF-8", f, "-"], capture_output=True, text=True).stdout
        out.append(cut_references(t))
    return "\n".join(out)


REF = re.compile(r"^\s*(\d+\.?\s*)?(references|bibliography)\s*$", re.I | re.M)
AFTER = re.compile(r"^\s*(appendix|appendices|supplementary material|[A-H](\.\d*)?\s+[A-Z][a-z])", re.M)


def cut_references(t):
    """Drop each references section: from its heading to the next appendix heading, or to the end."""
    while (m := REF.search(t)):
        n = AFTER.search(t, m.end())
        t = t[:m.start()] + (t[n.start():] if n else "")
    return t


out = []
for year, ids in (("2018", ours18), ("2026", classic26)):
    for pid in ids:
        if val(pid, "Q1") == "no":
            continue
        nos = [k for k in CRIT if val(pid, k) == "no"]
        if not nos:
            continue
        t = text(pid)
        flat = re.sub(r"\s+", " ", t)
        for k in nos:
            hits, last = [], -1
            for m in re.finditer(PATTERNS[k], flat, re.I):
                if m.start() <= last:  # inside the previous context: same excerpt
                    continue
                a, b = max(0, m.start() - CONTEXT), min(len(flat), m.end() + CONTEXT)
                hits.append(dict(match=m.group(0), context=flat[a:b]))
                last = b
            out.append(dict(year=year, id=pid, k=k, text_chars=len(flat), hits=hits))
json.dump(out, open("falsify_candidates.json", "w"), indent=1, ensure_ascii=False)
for year in ("2018", "2026"):
    for k in CRIT:
        rows = [r for r in out if r["year"] == year and r["k"] == k]
        print(f"{year} {k}: {len(rows)} no, {sum(not r['hits'] for r in rows)} with no occurrence, "
              f"{sum(len(r['hits']) for r in rows)} occurrences")
print("papers with no text:", sorted({r["id"] for r in out if not r["text_chars"]}))
