"""A6 (PROTOCOL.md, deviation 24): does the title filter miss RL papers?

Population: the papers of the three 2026 listings whose title does not match RX (the population's expression).
Draw: 400 with random.Random(2029). For each, the abstract from the official page; "hidden RL" if the abstract
matches RX. Share with its Wilson interval, estimated number of RL papers missed, and their fraction of the total.
The listing pages are copies of conference pages, kept locally only; the drawn papers and their abstracts are
saved in title_filter.json, so the counts can be redone without them. Standard library and pineau_rl.stats.
Run from study/: ../sim/env-an/bin/python title_filter.py  -> title_filter.json
"""
import html, json, os, random, re, time, urllib.request
from pineau_rl.stats import wilson

RX = re.compile(r'reinforcement learning|\bRL\b|\bRLHF\b|\bRLVR\b|policy optimi[sz]ation|'
                r'policy gradient|q-learning|actor-critic|\bMDPs?\b', re.I)  # as sample_v2.py
N, POP_RL = 400, 1252
OUT = "title_filter.json"
clean = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "replace")


def listing():
    papers, seen = [], set()
    for f, venue, pat, base in (
            ("iclr2026.html", "ICLR 2026", r'href="(/paper_files/paper/2026/hash/[0-9a-f]+-Abstract-Conference\.html)">([^<]+)', "https://proceedings.iclr.cc"),
            ("icml2026v.html", "ICML 2026", r'href="(/virtual/2026/poster/\d+)">([^<]+)', "https://icml.cc"),
            ("neurips2025v.html", "NeurIPS 2025", r'href="(/virtual/2025/poster/\d+)">([^<]+)', "https://neurips.cc")):
        for u, t in re.findall(pat, open(f, encoding="utf-8").read()):
            if u not in seen:
                seen.add(u); papers.append(dict(venue=venue, title=clean(t), url=base + u))
    return papers


def abstract(url):
    t = get(url)
    m = (re.search(r'class="paper-abstract">(.*?)</section>', t, re.S) or re.search(r'id="abstractText"[^>]*>(.*?)</div>', t, re.S))
    return clean(m.group(1)) if m else None


if os.path.exists(OUT):
    data = json.load(open(OUT))
else:
    pop = listing()
    rest = [p for p in pop if not RX.search(p["title"])]
    draw = random.Random(2029).sample(rest, N)
    data = dict(population=len(pop), outside_filter=len(rest), draw=draw)
for p in data["draw"]:
    if "abstract" not in p:
        try:
            p["abstract"] = abstract(p["url"])
        except Exception as e:
            p["abstract"], p["error"] = None, str(e)[:120]
        time.sleep(0.5)
        json.dump(data, open(OUT, "w"), indent=1, ensure_ascii=False)
read = [p for p in data["draw"] if p.get("abstract")]
hidden = [p for p in read if RX.search(p["abstract"])]
for p in data["draw"]:
    p["hidden_rl"] = bool(p.get("abstract") and RX.search(p["abstract"]))
k, n = len(hidden), len(read)
lo, hi = wilson(k, n)
miss = [x * data["outside_filter"] for x in (k / n, lo, hi)]
data["result"] = dict(abstracts_read=n, hidden_rl=k, share=k / n, wilson=[lo, hi], missed_estimate=miss,
                      missed_fraction=[m / (m + POP_RL) for m in miss], hidden_ids=[p["url"] for p in hidden])
json.dump(data, open(OUT, "w"), indent=1, ensure_ascii=False)
print(f"population {data['population']}, outside the filter {data['outside_filter']}; abstracts read {n}/{N}; "
      f"hidden RL {k} ({k / n:.1%}, Wilson [{lo:.1%}, {hi:.1%}]); missed about {miss[0]:.0f} [{miss[1]:.0f}, {miss[2]:.0f}], "
      f"{data['result']['missed_fraction'][0]:.0%} of all RL papers")
for p in hidden:
    print(" ", p["venue"], "|", p["title"][:90])
