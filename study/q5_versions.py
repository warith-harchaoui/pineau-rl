"""arXiv version against proceedings version for Q5 (PROTOCOL.md, deviation 31), step 1: versions, occurrences, repositories.

  fetch       2018: for each paper of our 2018 with final Q5 "no", the arXiv API is queried on the title; the entry whose
              title is at least 85% identical (difflib, as fetch.py) gives the latest version, saved as pdf/<id>-arxiv.pdf.
              2026: for each classical paper read on arXiv, the proceedings version: NeurIPS 2025 already on disk
              (pdf/<id>-proc.pdf, deviation 22), ICLR 2026 from proceedings.iclr.cc (file address from the paper's), ICML
              2026 from PMLR volume 306 (found by title, at least 85%). Fingerprints appended to pdfs.csv.
  candidates  text by pdftotext, references cut as falsify_no.py. 2026 "yes": the address cited in the final Q5 quote is
              looked for in the proceedings text (letters and digits only); found, "yes" stays. Otherwise, and for every
              "no", each occurrence of the Q5 pattern of deviation 27 with 300 characters of context -> q5_versions_candidates.json
  batch       the occurrences to arbitrate, both years mixed (random.Random(31)), ids replaced by item numbers, years in
              digits (1990-2029) masked -> q5_versions_batches/batch.json (the key to the items stays in the candidates file)
  verdicts    the arbiter's answers mapped back to papers -> q5_versions_verdicts.json
  repos       for each GitHub link of a "yes" in either version, the repository's creation date (gh api, one request at a
              time, 1.5-4 s apart) -> q5_repos.json

Network: one session per host, one host at a time; arXiv 3-6 s between requests, other hosts 1.5-4 s; a refusal, 429 or
503 stops, then exponential backoff with full jitter (base 5 s, cap 5 min, 4 attempts), Retry-After honoured.
Run from study/: ../sim/env-an/bin/python q5_versions.py fetch|candidates|batch|repos
"""
import csv, difflib, hashlib, html, json, os, random, re, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from samples import OLD, V2READ, classic26, experimental, ours18, val

UA = "pineau-rl-study/2.0 (+https://github.com/warith-harchaoui/pineau-rl)"
Q5 = r"github|gitlab|bitbucket|anonymous\.4open|code (is |are |will be )?(publicly )?available|source code|our (code|implementation)|open[- ]source"
CONTEXT = 150
LAST_DAY = {"ICLR 2018": "2018-05-03", "ICML 2018": "2018-07-15", "NeurIPS 2018": "2018-12-08",
            "NeurIPS 2025": "2025-12-07", "ICLR 2026": "2026-04-27", "ICML 2026": "2026-07-11"}
PMLR = "https://proceedings.mlr.press/v306/"
URLRE = re.compile(r"(?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org|anonymous\.4open\.science|[\w.-]+\.github\.io|sites\.google\.com|[\w-]+\.[\w.-]+)/[^\s\"'<>)\]},;]+", re.I)
GH = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)

meta = {x["id"]: x for f in ("calib_2018_v2.json", "final_2026.json", "classic_queue_2026.json") for x in json.load(open(f))}
src = {r["id"]: r for r in csv.DictReader(open("pdfs.csv", encoding="utf-8"))}
no18 = [p for p in experimental(ours18) if val(p, "Q5") == "no"]
yes18 = [p for p in experimental(ours18) if val(p, "Q5") == "yes"]
arxiv26 = [p for p in experimental(classic26) if "arxiv.org" in src.get(p, {}).get("source", "")]


def venue(pid):
    return meta[pid]["venue"]


def quote(pid, k="Q5"):
    rec = V2READ[pid] if pid in V2READ and k in V2READ[pid]["criteria"] else OLD[pid]
    return rec["criteria"][k].get("quote") or ""


# ---------------------------------------------------------------- network, paced
_last = {}


def get(url, binary=True, attempts=4):
    host = urllib.parse.urlparse(url).netloc
    lo, hi = (3, 6) if "arxiv.org" in host else (1.5, 4)
    wait = _last.get(host, 0) + random.uniform(lo, hi) - time.time()
    if wait > 0:
        time.sleep(wait)
    for k in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            _last[host] = time.time()
            return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            _last[host] = time.time()
            if e.code == 404:
                return None
            if e.code not in (429, 503, 403) or k == attempts - 1:
                raise
            ra = e.headers.get("Retry-After")
            pause = max(float(ra) if ra and ra.isdigit() else 0, random.uniform(0, min(300, 5 * 2 ** k)))
            print(f"  HTTP {e.code} on {host}, waiting {pause:.0f} s", flush=True)
            time.sleep(pause + random.uniform(0, 3))
        except (urllib.error.URLError, TimeoutError) as e:
            _last[host] = time.time()
            if k == attempts - 1:
                raise
            pause = random.uniform(0, min(300, 5 * 2 ** k))
            print(f"  {e!r} on {host}, waiting {pause:.0f} s", flush=True)
            time.sleep(pause)


def ratio(a, b):  # as fetch.py
    return difflib.SequenceMatcher(None, " ".join(a.split()).lower(), b.lower()).ratio()


def save(pid, suffix, data, source):
    path = f"pdf/{pid}-{suffix}.pdf"
    open(path, "wb").write(data)
    row = dict(id=f"{pid}-{suffix}", file=path, sha256=hashlib.sha256(data).hexdigest(), bytes=str(len(data)),
               source=source, read="yes")
    if row["id"] not in {r["id"] for r in csv.DictReader(open("pdfs.csv", encoding="utf-8"))}:  # appended, file untouched
        with open("pdfs.csv", "a", encoding="utf-8") as f:
            f.write(",".join(row.values()) + "\n")
    return path


def arxiv_search(title):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    words = re.sub(r"[^\w\s-]", " ", title).split()
    queries = ['ti:"%s"' % " ".join(words), " AND ".join(f"ti:{w}" for w in words if len(w) > 3)[:300]]
    best = None
    for q in queries:
        x = get("http://export.arxiv.org/api/query?" + urllib.parse.urlencode(dict(search_query=q, max_results=10)), False)
        for e in ET.fromstring(x).findall("a:entry", ns):
            t = " ".join(e.find("a:title", ns).text.split())
            sc = ratio(t, title)
            if sc > 0.85 and (not best or sc > best[0]):
                best = (sc, e.find("a:id", ns).text.rsplit("/abs/", 1)[1], t)
        if best:
            break
    return best


def fetch():
    log = json.load(open("q5_versions_fetch.json")) if os.path.exists("q5_versions_fetch.json") else {}
    for pid in no18:  # arXiv host only, one request at a time
        if pid in log:
            continue
        title = meta[pid]["title"]
        best = arxiv_search(title)
        rec = dict(year="2018", title=title, version="arxiv")
        if best:
            sc, aid, t = best
            data = get(f"http://export.arxiv.org/pdf/{aid}")
            rec.update(score=round(sc, 3), arxiv_id=aid, arxiv_title=t,
                       file=save(pid, "arxiv", data, f"http://export.arxiv.org/pdf/{aid}") if data else None)
        else:
            rec.update(file=None, note="no arXiv entry at 85%")
        log[pid] = rec
        json.dump(log, open("q5_versions_fetch.json", "w"), indent=1, ensure_ascii=False)
        print(pid, rec.get("arxiv_id"), rec.get("score"), flush=True)
    for pid in [p for p in arxiv26 if venue(p) == "ICLR 2026"]:  # proceedings.iclr.cc
        if pid in log:
            continue
        m = re.search(r"/hash/([0-9a-f]+)-Abstract", meta[pid]["url"])
        url = f"https://proceedings.iclr.cc/paper_files/paper/2026/file/{m.group(1)}-Paper-Conference.pdf"
        data = get(url)
        log[pid] = dict(year="2026", version="proc", title=meta[pid]["title"], file=save(pid, "proc", data, url) if data else None)
        json.dump(log, open("q5_versions_fetch.json", "w"), indent=1, ensure_ascii=False)
        print(pid, url, bool(data), flush=True)
    icml = [p for p in arxiv26 if venue(p) == "ICML 2026" and p not in log]
    if icml:  # PMLR volume 306: the index, then the PDFs
        idx = get(PMLR, False)
        papers = [(html.unescape(re.sub(r"\s+", " ", t)).strip(), u) for t, u in re.findall(
            r'<p class="title">(.*?)</p>.*?<a href="([^"]+\.pdf)"', idx, re.S)]
        for pid in icml:
            title = meta[pid]["title"]
            sc, t, u = max(((ratio(t, title), t, u) for t, u in papers), default=(0, None, None))
            rec = dict(year="2026", version="proc", title=title, score=round(sc, 3))
            if sc > 0.85:
                data = get(u)
                rec.update(pmlr_title=t, file=save(pid, "proc", data, u) if data else None)
            else:
                rec.update(file=None, note="not found in PMLR v306 at 85%")
            log[pid] = rec
            json.dump(log, open("q5_versions_fetch.json", "w"), indent=1, ensure_ascii=False)
            print(pid, rec.get("score"), rec.get("file"), flush=True)
    for pid in [p for p in arxiv26 if venue(p) == "NeurIPS 2025"]:  # deviation 22, already on disk
        if os.path.exists(f"pdf/{pid}-proc.pdf"):
            log[pid] = dict(year="2026", version="proc", title=meta[pid]["title"], file=f"pdf/{pid}-proc.pdf", note="deviation 22")
        else:
            log[pid] = dict(year="2026", version="proc", title=meta[pid]["title"], file=None, note="no proceedings PDF on disk")
    json.dump(log, open("q5_versions_fetch.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- occurrences
REF = re.compile(r"^\s*(\d+\.?\s*)?(references|bibliography)\s*$", re.I | re.M)  # as falsify_no.py
AFTER = re.compile(r"^\s*(appendix|appendices|supplementary material|[A-H](\.\d*)?\s+[A-Z][a-z])", re.M)


def cut_references(t):
    while (m := REF.search(t)):
        n = AFTER.search(t, m.end())
        t = t[:m.start()] + (t[n.start():] if n else "")
    return t


def flat_text(path):
    t = subprocess.run(["pdftotext", "-q", "-enc", "UTF-8", path, "-"], capture_output=True, text=True).stdout
    return re.sub(r"\s+", " ", cut_references(t))


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def hits(flat):
    out, last = [], -1
    for m in re.finditer(Q5, flat, re.I):
        if m.start() <= last:
            continue
        a, b = max(0, m.start() - CONTEXT), min(len(flat), m.end() + CONTEXT)
        out.append(dict(match=m.group(0), context=flat[a:b]))
        last = b
    return out


def candidates():
    log = json.load(open("q5_versions_fetch.json"))
    out = []
    for pid, rec in log.items():
        base = dict(id=pid, year=rec["year"], version=rec["version"], venue=venue(pid), read=val(pid, "Q5"), file=rec["file"])
        if not rec["file"]:
            out.append(dict(base, status="no other version", hits=[]))
            continue
        flat = flat_text(rec["file"])
        r = dict(base, text_chars=len(flat))
        if base["read"] == "yes":
            urls = [u.rstrip(".") for u in URLRE.findall(quote(pid))]
            r["quoted_urls"] = urls
            key = [alnum(re.sub(r"^(https?://)?(www\.)?", "", u)) for u in urls]
            if key and any(k and k in alnum(flat) for k in key):
                out.append(dict(r, status="quoted address found", hits=[]))
                continue
        h = hits(flat)
        out.append(dict(r, status="to arbitrate" if h else "no occurrence", hits=h))
    json.dump(out, open("q5_versions_candidates.json", "w"), indent=1, ensure_ascii=False)
    for s in sorted({x["status"] for x in out}):
        for y in ("2018", "2026"):
            ids = [x["id"] for x in out if x["status"] == s and x["year"] == y]
            print(y, s, len(ids), ids)


YEARS = re.compile(r"\b(199\d|20[0-2]\d)\b")
RULE = ("Q5: the paper gives a link to code (GitHub, GitLab, Bitbucket, an anonymous mirror that contains the code, or a "
        "project page that leads to code). 'Available on request', 'will be released', 'will be made public at <URL>': no. "
        "A link to someone else's library, dataset or benchmark is not the paper's code.")


def batch():
    cand = [x for x in json.load(open("q5_versions_candidates.json")) if x["status"] == "to arbitrate"]
    random.Random(31).shuffle(cand)
    os.makedirs("q5_versions_batches", exist_ok=True)
    items, key = [], {}
    for i, x in enumerate(cand, 1):
        items.append(dict(item=i, rule=RULE, excerpts=[YEARS.sub("[year]", h["context"]) for h in x["hits"]]))
        key[i] = [x["id"], x["year"], x["version"]]
    json.dump(items, open("q5_versions_batches/batch.json", "w"), indent=1, ensure_ascii=False)
    json.dump(key, open("q5_versions_batches/key.json", "w"), indent=1)
    print(len(items), "items")


def verdicts():
    """The arbiter's answers (q5_versions_batches/answers.json, by item) mapped back to papers -> q5_versions_verdicts.json"""
    key = json.load(open("q5_versions_batches/key.json"))
    out = []
    for a in json.load(open("q5_versions_batches/answers.json")):
        pid, year, version = key[str(a["item"])]
        out.append(dict(id=pid, year=year, version=version, item=a["item"], turn=bool(a["yes"]),
                        uncertain=bool(a["uncertain"]), url=a.get("url"), reason=a.get("reason")))
    assert len(out) == len(key)
    json.dump(sorted(out, key=lambda v: v["item"]), open("q5_versions_verdicts.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- repositories
def repos():
    """GitHub links of every yes in either version: 2018 as read, 2018 turned on arXiv (the arbiter's url), 2026 as read."""
    verd = {(v["id"], v["version"]): v for v in json.load(open("q5_versions_verdicts.json"))} \
        if os.path.exists("q5_versions_verdicts.json") else {}
    links = {}
    for pid in yes18 + [p for p in experimental(classic26) if val(p, "Q5") == "yes"]:
        links.setdefault(pid, set()).update("/".join(m) for m in GH.findall(quote(pid)))
    for (pid, version), v in verd.items():
        if v["turn"] and v.get("url"):
            links.setdefault(pid, set()).update("/".join(m) for m in GH.findall(v["url"]))
    old = json.load(open("q5_repos.json")) if os.path.exists("q5_repos.json") else {}
    out = {}
    for pid in sorted(links):
        out[pid] = dict(venue=venue(pid), last_day=LAST_DAY[venue(pid)], repos={})
        for rep in sorted(links[pid]):
            o, r = rep.split("/")
            r = re.sub(r"\.git$", "", r.rstrip("."))
            rep = f"{o}/{r}"
            prev = old.get(pid, {}).get("repos", {}).get(rep)
            if prev is not None:
                out[pid]["repos"][rep] = prev
                continue
            time.sleep(random.uniform(1.5, 4))
            p = subprocess.run(["gh", "api", f"repos/{rep}", "--jq", ".created_at"], capture_output=True, text=True)
            if p.returncode == 0:
                out[pid]["repos"][rep] = p.stdout.strip()
            elif "Not Found" in p.stderr or "404" in p.stderr:
                out[pid]["repos"][rep] = None
            else:  # refusal or rate limit: stop at once
                print("gh api refused:", p.stderr.strip())
                json.dump(out, open("q5_repos.json", "w"), indent=1)
                sys.exit(1)
            print(pid, rep, out[pid]["repos"][rep], flush=True)
        if not links[pid]:
            out[pid]["note"] = "no GitHub link in the quote"
    json.dump(out, open("q5_repos.json", "w"), indent=1)


if __name__ == "__main__":
    dict(fetch=fetch, candidates=candidates, batch=batch, verdicts=verdicts, repos=repos)[sys.argv[1]]()
