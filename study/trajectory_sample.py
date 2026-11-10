"""A4 (PROTOCOL.md, deviation 25): the per-year queues of classical RL papers, ICML and NeurIPS, 2019 to 2024.

For each year: the RL papers (title matches RX) of the ICML main proceedings (PMLR) and of the NeurIPS main track,
shuffled with random.Random(<year>); titles with a prescreen term (deviation 12, A3) are skipped. PDFs (and a PDF
supplement when there is one) are fetched in queue order until 24 per year have a PDF.
The listing pages are copies of conference pages, kept locally in pdf/ (not in the repository); their parse is
frozen in trajectory_queue.json. Standard library plus `pdfinfo`.
Run from study/: python3 trajectory_sample.py  -> trajectory_queue.json, pdf/Y<year>_<k>.pdf
"""
import html, json, os, random, re, subprocess, time, urllib.request

RX = re.compile(r'reinforcement learning|\bRL\b|\bRLHF\b|\bRLVR\b|policy optimi[sz]ation|'
                r'policy gradient|q-learning|actor-critic|\bMDPs?\b', re.I)  # as sample_v2.py
PRESCREEN = ['llm', 'language model', 'reasoning', 'rlhf', 'rlvr', 'grpo', 'preference',
             'alignment', 'reward model', 'chain-of-thought', 'math', 'agentic']  # as sample_v2.py
YEARS = {2019: 97, 2020: 119, 2022: 162, 2024: 235}
PER_YEAR, OUT = 24, "trajectory_queue.json"
clean = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()


def page(name, url):
    f = f"pdf/{name}"
    if not os.path.exists(f):
        open(f, "wb").write(get(url))
    return open(f, encoding="utf-8", errors="replace").read()


def population(year):
    pop = []
    s = page(f"icml{year}.html", f"https://proceedings.mlr.press/v{YEARS[year]}/")
    for blk in s.split('<div class="paper">')[1:]:
        t = clean(re.search(r'<p class="title">(.*?)</p>', blk, re.S).group(1))
        pdf = re.search(r'href="([^"]+?\.pdf)"[^>]*>\s*Download PDF', blk)
        supp = re.search(r'href="([^"]+?-supp\.pdf)"', blk)
        if pdf:
            pop.append(dict(venue=f"ICML {year}", title=t, url=pdf.group(1), pdf_url=pdf.group(1),
                            supp_url=supp.group(1) if supp else None))
    s = page(f"neurips{year}.html", f"https://papers.nips.cc/paper_files/paper/{year}")
    for h, t in re.findall(r'<a title="paper title" href="([^"]+)">(.*?)</a>', s):
        if not re.search(r"-Abstract(-Conference)?\.html$", h):
            continue  # main track only
        u = "https://papers.nips.cc" + h
        conf = "-Conference" if h.endswith("-Abstract-Conference.html") else ""
        pdf = u.replace("/hash/", "/file/").replace(f"-Abstract{conf}.html", f"-Paper{conf}.pdf")
        supp = u.replace("/hash/", "/file/").replace(f"-Abstract{conf}.html", f"-Supplemental{conf}.pdf")
        pop.append(dict(venue=f"NeurIPS {year}", title=clean(t), url=u, pdf_url=pdf, supp_url=supp))
    return [p for p in pop if RX.search(p["title"])]


def valid(f):
    r = subprocess.run(["pdfinfo", f], capture_output=True, text=True)
    return r.returncode == 0 and "Pages:" in r.stdout


q = json.load(open(OUT)) if os.path.exists(OUT) else {}
for year in YEARS:
    if str(year) not in q:
        pop = population(year)
        random.Random(year).shuffle(pop)
        q[str(year)] = dict(population=len(pop), queue=[p for p in pop if not any(w in p["title"].lower() for w in PRESCREEN)])
        for k, p in enumerate(q[str(year)]["queue"], 1):
            p["id"] = f"Y{year}_{k:03d}"
    have = 0
    for p in q[str(year)]["queue"]:
        if have >= PER_YEAR:
            break
        f = f"pdf/{p['id']}.pdf"
        if not (os.path.exists(f) and valid(f)):
            try:
                open(f, "wb").write(get(p["pdf_url"])); time.sleep(1)
            except Exception as e:
                p["pdf_error"] = str(e)[:100]
        p["pdf"] = f if os.path.exists(f) and valid(f) else None
        if p["pdf"] and p.get("supp_url") and not os.path.exists(f"pdf/{p['id']}-supp.pdf"):
            try:
                b = get(p["supp_url"])
                if b[:4] == b"%PDF":
                    open(f"pdf/{p['id']}-supp.pdf", "wb").write(b)
            except Exception:
                pass
        p["supp"] = os.path.exists(f"pdf/{p['id']}-supp.pdf")
        have += bool(p["pdf"])
    json.dump(q, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(year, "RL population", q[str(year)]["population"], "after prescreen", len(q[str(year)]["queue"]), "with PDF", have)
