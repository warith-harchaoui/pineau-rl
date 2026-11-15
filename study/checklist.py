"""A5 (PROTOCOL.md, deviation 22): what NeurIPS 2025 papers declare in their checklist, against what we read.

For the 30 NeurIPS 2025 papers already read, finds the official proceedings version by title in the volume 38
listing of proceedings.neurips.cc, downloads it (pdf/<id>-proc.pdf), extracts the answer and the justification of
four checklist questions, and sets them against our harmonised codes: code (Q5), settings (Q3), statistical
significance (X2 for an uncertainty, Q8 for a test), compute (X7). For each disagreement on code, looks for a link to
code in the proceedings version. Standard library, pineau_rl and the `pdftotext` command.
Run from study/: ../sim/env-an/bin/python checklist.py  -> checklist.json
"""
import json, os, re, subprocess, time, urllib.request
from pineau_rl.grid import list_readers, load_overrides, load_reads, value
from pineau_rl.stats import wilson as _wilson
from load import load

BASE = "https://proceedings.neurips.cc"
LISTING = "pdf/neurips2025-vol38.html"  # a copy of a conference page: kept locally only, like pdf/
Q = {"code": ("Open access to data and code", ["Q5"]), "settings": ("Experimental setting/details", ["Q3"]),
     "significance": ("Experiment statistical significance", ["X2", "Q8"]),
     "compute": ("Experiments compute resources", ["X7"])}
CODE_URL = re.compile(r"(github\.com|gitlab\.com|huggingface\.co|bitbucket\.org|codeocean|zenodo\.org|anonymous\.4open)", re.I)

ov1, ov2 = load_overrides("overrides.json"), load_overrides("overrides_v2.json")
OLD = load("ABCDE")
V2 = load_reads("codes_v2", list_readers("codes_v2", "K*"))


def val(pid, k):  # as in extension_stats.py, but Y3 kept as an integer and a paper in neither grid is an error
    return value(pid, k, V2, OLD, ov2, ov1, y3=False, missing_ok=False)


norm = lambda t: " ".join(re.sub(r"[^a-z0-9]+", " ", t.lower()).split())
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()


def wilson(k, n):
    return list(_wilson(k, n)) if n else None


meta = [x for x in json.load(open("final_2026.json")) if x["venue"] == "NeurIPS 2025"]
a3 = json.load(open("extension_stats.json"))["samples"]["a3"]
meta += [x for x in json.load(open("classic_queue_2026.json")) if x["id"] in a3 and x["venue"] == "NeurIPS 2025"]
assert len(meta) == 30, len(meta)
if not os.path.exists(LISTING):
    open(LISTING, "wb").write(get(BASE + "/paper_files/paper/2025/vol38-main-conference"))
listing = open(LISTING, encoding="utf-8").read()
index = {norm(re.sub(r"<[^>]+>", "", t)): h for h, t in
         re.findall(r'href="(/paper_files/paper/2025/hash/[0-9a-f]+-Abstract-Conference\.html)"[^>]*>(.*?)</a>', listing, re.S)}

rows = []
for m in meta:
    pid, r = m["id"], dict(id=m["id"], title=m["title"], family=val(m["id"], "X5"))
    h = index.get(norm(m["title"]))
    r["proceedings"] = BASE + h if h else None
    f = f"pdf/{pid}-proc.pdf"
    if h and not os.path.exists(f):
        open(f, "wb").write(get(BASE + h.replace("/hash/", "/file/").replace("-Abstract-Conference.html", "-Paper-Conference.pdf")))
        time.sleep(1)
    text = subprocess.run(["pdftotext", f, "-"], capture_output=True, text=True).stdout if h else ""
    r["declared"] = {}
    for key, (head, codes) in Q.items():
        a = re.search(re.escape(head) + r".*?Answer:\s*\[([A-Za-z/ ]+)\]\s*Justification:\s*(.*?)\n\s*Guidelines", text, re.S)
        r["declared"][key] = dict(answer=a.group(1).strip().upper().replace("N/A", "NA"), justification=" ".join(a.group(2).split())) if a else None
        r[key] = {c: val(pid, c) for c in codes}
    r["proc_code_link"] = bool(CODE_URL.search(text.split("NeurIPS Paper Checklist")[0])) if text else None
    rows.append(r)

summary = {}
for key, (head, codes) in Q.items():
    for c in codes:
        have = [r for r in rows if r["declared"][key] and r[key][c] in ("yes", "no")]
        yes = [r for r in have if r["declared"][key]["answer"] == "YES"]
        bad = [r for r in yes if r[key][c] == "no"]
        s = dict(question=head, criterion=c, papers_with_answer=len(have), declared_yes=len(yes), yes_but_our_no=len(bad),
                 share=len(bad) / len(yes) if yes else None, wilson=wilson(len(bad), len(yes)), ids=[r["id"] for r in bad])
        if c == "Q5":
            s["yes_but_no_link_even_in_proceedings"] = [r["id"] for r in bad if not r["proc_code_link"]]
        summary[f"{key}/{c}"] = s
        print(f"{head:40s} vs {c}: {len(bad)}/{len(yes)} declared Yes but coded no"
              + (f"  ({len(s['yes_but_no_link_even_in_proceedings'])} with no code link in the proceedings either)" if c == "Q5" else ""))
missing = [r["id"] for r in rows if not any(r["declared"].values())]
print("no readable checklist:", missing)
json.dump(dict(rows=rows, summary=summary, no_checklist=missing), open("checklist.json", "w"), indent=1, ensure_ascii=False)
