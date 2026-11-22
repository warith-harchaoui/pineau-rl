"""Q5 project pages of deviation 36 (PROTOCOL.md): the new readers do not visit links, the analysis settles them.

For each new Q5 `yes` with link_kind project_page: if the final Q5 quote of the original reading cites the same
address (letters and digits, without the scheme and "www"), the original final value applies (deviations 6 and 19:
every project page of the original readings was visited on 9 November 2026). Otherwise the page is visited once
(one host at a time, a randomised pause between requests) and the visit is written by hand, dated, in
r36_page_visits.json: {"<id>": {"url", "date", "leads_to_code": true/false, "note"}}. A page that is neither in the
original reading nor visited stops the script. When the new quote gives no address (the address sits only behind a
hyperlink), the addresses are taken from the link annotations of the PDF (/URI entries, arXiv links left out).
Run from study/: ../sim/env-an/bin/python r36_pages.py  -> r36_project_pages.json
"""
import json, re
from pineau_rl.grid import iter_reads
from samples import OLD, V2READ, val

R = [f"T{i}" for i in range(1, 9)]
URL = re.compile(r"(?:https?://)?(?:www\.)?([A-Za-z0-9.-]+\.[a-z]{2,}(?:/[^\s\"'<>)\]]*)?)")
visits = json.load(open("r36_page_visits.json"))


def addr(q):
    return [re.sub(r"[^a-z0-9]", "", m.group(1).lower().rstrip("./")) for m in URL.finditer(q or "")]


def pdf_links(pid):  # address only behind a hyperlink: the link annotations of the PDF (/URI entries)
    raw = open(f"pdf/{pid}.pdf", "rb").read().decode("latin-1")
    return [a for u in re.findall(r"/URI\s*\(([^)]*)\)", raw) for a in addr(u) if "arxiv.org" not in a]


def orig_quote(pid):
    rec = V2READ[pid] if pid in V2READ and "Q5" in V2READ[pid]["criteria"] else OLD[pid]
    return rec["criteria"]["Q5"].get("quote", "")


out, missing = {}, []
for rd, rec in iter_reads("codes_r36", R):
    c = rec["criteria"]["Q5"]
    if c.get("value") != "yes" or c.get("link_kind") != "project_page":
        continue
    pid, new = rec["id"], addr(c["quote"]) or pdf_links(rec["id"])
    old = addr(orig_quote(pid))
    if new and any(a and (a in old or any(a.startswith(o) or o.startswith(a) for o in old if o)) for a in new):
        out[pid] = dict(value=val(pid, "Q5"), how="original reading (deviations 6 and 19)", reader=rd)
    elif pid in visits:
        v = visits[pid]
        out[pid] = dict(value="yes" if v["leads_to_code"] else "no", how=f"visited {v['date']}: {v['url']}", reader=rd)
    else:
        missing.append((pid, c["quote"]))
if missing:
    raise SystemExit("project pages to visit and record in r36_page_visits.json: " + repr(missing))
json.dump(out, open("r36_project_pages.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "project pages:", out)
