"""Écart 12 of PROTOCOL.md: draw A2 (2018 calibration -> 50) and A3 (classic 2026 queue).

Deterministic, standard library only (plus the poppler command-line tools `pdfinfo` and
`pdftotext` for PDF validation). Run from anywhere:  python3 study/sample_v2.py
Resumable: a PDF already present and valid is not downloaded again.

Sources
- ICML 2018: icml2018.html (proceedings.mlr.press v80 listing, saved). PDF and -supp.pdf from PMLR.
- NeurIPS 2018: neurips2018.html (papers.nips.cc listing, saved). PDF from papers.nips.cc;
  as papers.nips.cc and proceedings.neurips.cc timed out on 2026-11-09, the Internet Archive
  copy of that same proceedings PDF URL is the second source, arXiv by title the third.
- ICLR 2018: included. On 2026-11-09 the OpenReview API (api.openreview.net) and dblp both
  answered with bot challenges (HTTP 403 / 202), so the accepted list comes from the official
  conference schedule https://iclr.cc/Conferences/2018/Schedule (raw page saved as
  iclr2018.html, parsed cards saved as iclr2018.json). Conference track = Oral + Poster cards,
  deduplicated by OpenReview forum id (336 papers); Workshop cards are excluded.
  openreview.net/pdf refuses automated downloads (403), so the PDF comes from the Internet
  Archive copy of that same OpenReview PDF URL, else arXiv by title (as fetch.py).
- 2026: rl_population_2026.json. PDFs: proceedings.iclr.cc for ICLR 2026, arXiv by title
  (SequenceMatcher ratio > 0.85, as fetch.py) for the rest.

A2 (écart 12): the 12 papers of calib_2018.json are kept. The 50-paper sample is allocated to
venues in proportion to their size in the 2018 RL population (largest remainder); the new papers
per venue are that quota minus the 6 already held. The rest of the population (all venues, in
listing order ICML, NeurIPS, ICLR) is shuffled once with random.Random(2018) and walked in that
order; a paper is taken if its venue quota is not yet full and a valid free PDF is obtained,
otherwise (no PDF) it is recorded in replacements_2018.json and the walk continues, so the
replacement is the next paper of the draw order. ICML and NeurIPS 2018 proceedings are open
access, so a failure there is a network outage: the script stops instead of replacing.
Ids: C1<k> ICML, C2<k> NeurIPS, C3<k> ICLR, k continuing after the existing ones (C17, C18,
C19, C110, C111, ...).

A3 (écart 12): the 1,252 papers minus the 50 already read (title match, case and spacing
insensitive), shuffled with random.Random(2026); a title containing one of PRESCREEN (case
insensitive substring) goes to classic_screened_out_2026.json, the others form the ordered queue
classic_queue_2026.json (K001, K002, ...). PDFs are fetched in queue order until MIN_PDF
candidates have a valid PDF; a candidate without one keeps pdf = null.
"""
import difflib, html, json, os, random, re, subprocess, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
UA = {'User-Agent': 'pineau-rl-study/1.0'}
RX = re.compile(r'reinforcement learning|\bRL\b|\bRLHF\b|\bRLVR\b|policy optimi[sz]ation|'
                r'policy gradient|q-learning|actor-critic|\bMDPs?\b', re.I)
PRESCREEN = ['llm', 'language model', 'reasoning', 'rlhf', 'rlvr', 'grpo', 'preference',
             'alignment', 'reward model', 'chain-of-thought', 'math', 'agentic']
N2018 = 50
MIN_PDF = 70
PDFDIR = 'pdf'
DOWNLOAD = '--no-download' not in sys.argv
PREV = {}  # (id, title) -> pdf_src from a previous run, so a resumed run keeps provenance
for _f in ('calib_2018_v2.json', 'classic_queue_2026.json'):
    if os.path.exists(_f):
        PREV.update({(r['id'], r['title']): r.get('pdf_src') for r in json.load(open(_f)) if r.get('pdf')})


def dump(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', t.lower()).split())


# ---------------------------------------------------------------- populations
def pop_2018():
    pop = []
    s = open('icml2018.html').read()
    for blk in s.split('<div class="paper">')[1:]:
        t = ' '.join(html.unescape(re.search(r'<p class="title">(.*?)</p>', blk, re.S).group(1)).split())
        if not RX.search(t):
            continue
        pdf = re.search(r'href="(http[^"]+?/v80/[^"]+?\.pdf)"[^>]*>Download PDF', blk).group(1)
        supp = re.search(r'href="(http[^"]+?-supp\.pdf)"', blk)
        r = {'venue': 'ICML 2018', 'title': t, 'url': pdf, 'pdf_url': pdf}
        if supp:
            r['supp_url'] = supp.group(1)
        pop.append(r)
    s = open('neurips2018.html').read()
    for h, t in re.findall(r'<a title="paper title" href="([^"]+)">(.*?)</a>', s):
        t = ' '.join(html.unescape(t).split())
        if RX.search(t):
            url = 'https://papers.nips.cc' + h
            pop.append({'venue': 'NeurIPS 2018', 'title': t, 'url': url,
                        'pdf_url': url.replace('/hash/', '/file/').replace('-Abstract.html', '-Paper.pdf')})
    seen = set()
    for c in json.load(open('iclr2018.json'))['cards']:
        if c['type'] not in ('Oral', 'Poster') or c['forum'] in seen:
            continue
        seen.add(c['forum'])
        if RX.search(c['title']):
            pop.append({'venue': 'ICLR 2018', 'title': c['title'],
                        'url': 'https://openreview.net/forum?id=' + c['forum'],
                        'pdf_url': 'https://openreview.net/pdf?id=' + c['forum']})
    return pop


# ---------------------------------------------------------------- PDF fetching
def get(u, t=40):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()


def page1_text(f):
    try:
        return subprocess.run(['pdftotext', '-l', '1', f, '-'], capture_output=True, text=True,
                              timeout=60).stdout
    except Exception:
        return ''


def valid_pdf(f, title=None, min_pages=4):
    """pdfinfo succeeds, at least min_pages pages, title roughly on page 1."""
    if not os.path.exists(f):
        return False
    with open(f, 'rb') as fh:
        if fh.read(5) != b'%PDF-':
            return False
    try:
        p = subprocess.run(['pdfinfo', f], capture_output=True, text=True, timeout=60)
    except Exception:
        return False
    m = re.search(r'^Pages:\s+(\d+)', p.stdout, re.M)
    if p.returncode != 0 or not m or int(m.group(1)) < min_pages:
        return False
    if title:
        words = [w for w in norm(title).split() if len(w) > 3] or norm(title).split()
        txt = norm(page1_text(f)).replace(' ', '')
        hit = sum(1 for w in words if w in txt)
        if hit / len(words) < 0.7:
            return False
    return True


def save_if_valid(data, f, title, min_pages=4):
    with open(f, 'wb') as fh:
        fh.write(data)
    if valid_pdf(f, title, min_pages):
        return True
    os.remove(f)
    return False


def arxiv(title):
    words = re.sub(r'[^A-Za-z0-9 ]', ' ', title).split()
    q = '+AND+'.join('ti:' + urllib.parse.quote(w) for w in words if len(w) > 3)[:900]
    x = get('http://export.arxiv.org/api/query?search_query=' + q + '&max_results=5').decode()
    time.sleep(3)
    best = None
    for eid, tt in re.findall(r'<entry>.*?<id>(.*?)</id>.*?<title>(.*?)</title>', x, re.S):
        sc = difflib.SequenceMatcher(None, ' '.join(tt.split()).lower(), title.lower()).ratio()
        if sc > 0.85 and (not best or sc > best[0]):
            best = (sc, eid)
    return best[1].replace('/abs/', '/pdf/') if best else None


def fetch(r):
    """Try the sources in order; set r['pdf'], r['pdf_src'] or r['pdf'] = None."""
    f = f"{PDFDIR}/{r['id']}.pdf"
    if valid_pdf(f, r['title']):
        r['pdf'] = f
        r['pdf_src'] = PREV.get((r['id'], r['title']))
        r.pop('pdf_note', None)
        return True
    if os.path.exists(f):
        os.remove(f)
    if not DOWNLOAD:
        r['pdf'] = None
        return False
    srcs = []
    v = r['venue']
    wb = 'https://web.archive.org/web/{}id_/{}'
    if v == 'ICML 2018':
        srcs.append(r['pdf_url'])
    elif v == 'NeurIPS 2018':  # papers.nips.cc timed out on 2026-11-09: same file via the Internet Archive
        h = r['pdf_url'].rsplit('/', 1)[1]
        old_url = 'https://proceedings.neurips.cc/paper/2018/file/' + h
        srcs += [r['pdf_url'], wb.format(2020, old_url), wb.format(2022, old_url),
                 wb.format(2024, r['pdf_url']), wb.format(2020, r['pdf_url'])]
    elif v == 'ICLR 2018':
        srcs += [r['pdf_url']] + [wb.format(y, r['pdf_url']) for y in (2019, 2018, 2021)]
    elif 'proceedings.iclr.cc' in r['url']:
        srcs.append(r['url'].replace('/hash/', '/file/').replace('-Abstract-Conference.html', '-Paper-Conference.pdf'))
    srcs.append('ARXIV')
    for s in srcs:
        try:
            if s == 'ARXIV':
                s = arxiv(r['title'])
                if not s:
                    continue
            else:
                time.sleep(1)
            if save_if_valid(get(s), f, r['title']):
                r['pdf'], r['pdf_src'] = f, s
                r.pop('pdf_note', None)
                print(r['id'], 'OK', s, flush=True)
                return True
            print(r['id'], 'invalid file from', s, flush=True)
        except Exception as e:
            print(r['id'], 'ERR', s, e, flush=True)
            if s == srcs[0] and v == 'ICLR 2026':
                r['pdf_note'] = f'official proceedings unreachable on {time.strftime("%Y-%m-%d")} ({e}); rerun to retry'
    if v in ('ICML 2018', 'NeurIPS 2018'):
        # These proceedings are open access: a failure here is a network outage, not a paper
        # without a free PDF, so it must not trigger a replacement. Stop and rerun later.
        raise RuntimeError(f"{r['id']}: open-access proceedings PDF unreachable, rerun later")
    r['pdf'] = None
    print(r['id'], 'MISSING', r['title'][:70], flush=True)
    return False


def fetch_supp(r):
    if not r.get('supp_url'):
        return
    f = f"{PDFDIR}/{r['id']}-supp.pdf"
    if valid_pdf(f, None, 1):
        r['supp'] = f
        return
    if not DOWNLOAD:
        return
    try:
        time.sleep(1)
        if save_if_valid(get(r['supp_url']), f, None, 1):
            r['supp'] = f
            return
    except Exception as e:
        print(r['id'], 'supp ERR', e, flush=True)
    r['supp'] = None


# ---------------------------------------------------------------- A2
def largest_remainder(sizes, n):
    tot = sum(sizes.values())
    q = {k: n * v / tot for k, v in sizes.items()}
    a = {k: int(x) for k, x in q.items()}
    for k in sorted(q, key=lambda k: -(q[k] - a[k]))[:n - sum(a.values())]:
        a[k] += 1
    return a


def draw_a2(pop):
    old = json.load(open('calib_2018.json'))
    old_t = {norm(r['title']) for r in old}
    assert all(norm(r['title']) in {norm(p['title']) for p in pop} for r in old)
    venues = ['ICML 2018', 'NeurIPS 2018', 'ICLR 2018']
    prefix = {'ICML 2018': 'C1', 'NeurIPS 2018': 'C2', 'ICLR 2018': 'C3'}
    sizes = {v: sum(p['venue'] == v for p in pop) for v in venues}
    quota = largest_remainder(sizes, N2018)
    held = {v: sum(r['venue'] == v for r in old) for v in venues}
    need = {v: quota[v] - held[v] for v in venues}
    nxt = {v: held[v] + 1 for v in venues}
    rest = [dict(p) for p in pop if norm(p['title']) not in old_t]
    random.Random(2018).shuffle(rest)
    new, repl = [], []
    for rank, r in enumerate(rest, 1):
        v = r['venue']
        if need[v] == 0:
            continue
        r['id'] = f"{prefix[v]}{nxt[v]}"
        r['draw_rank'] = rank
        if fetch(r):
            if v == 'ICML 2018':
                fetch_supp(r)
            new.append(r)
            nxt[v] += 1
            need[v] -= 1
        else:
            repl.append({'venue': v, 'title': r['title'], 'url': r['url'], 'draw_rank': rank,
                         'reason': 'no free PDF (proceedings, Internet Archive copy, arXiv by title)'})
        if not any(need.values()):
            break
    for x in repl:  # which drawn paper took the slot
        later = [r for r in new if r['venue'] == x['venue'] and r['draw_rank'] > x['draw_rank']]
        x['replaced_by'] = later[0]['id'] if later else None
    out = old + [{k: r[k] for k in ('venue', 'title', 'url', 'pdf_url', 'id', 'draw_rank', 'pdf',
                                    'pdf_src', 'supp') if k in r} for r in new]
    dump(out, 'calib_2018_v2.json')
    dump({'population_sizes': sizes, 'quota_50': quota, 'new_per_venue': {v: quota[v] - held[v] for v in venues},
          'replacements': repl}, 'replacements_2018.json')
    print('A2', sizes, quota, 'new', len(new), 'replacements', len(repl))
    assert len(out) == N2018, 'population exhausted before quotas were met'


# ---------------------------------------------------------------- A3
def draw_a3():
    pop = json.load(open('rl_population_2026.json'))
    read = {norm(r['title']) for r in json.load(open('final_2026.json'))}
    rest = [dict(p) for p in pop if norm(p['title']) not in read]
    assert len(pop) - len(rest) == len(read) == 50, (len(pop), len(rest), len(read))
    random.Random(2026).shuffle(rest)
    queue, out = [], []
    for rank, r in enumerate(rest, 1):
        r['draw_rank'] = rank
        hit = [w for w in PRESCREEN if w in r['title'].lower()]
        if hit:
            r['prescreen_hit'] = hit
            out.append(r)
        else:
            r['id'] = f"K{len(queue) + 1:03d}"
            queue.append(r)
    n_ok = 0
    for r in queue:
        if n_ok >= MIN_PDF:
            break
        n_ok += fetch(r)
        dump(queue, 'classic_queue_2026.json')
    dump(queue, 'classic_queue_2026.json')
    dump(out, 'classic_screened_out_2026.json')
    tried = [r for r in queue if 'pdf' in r]
    print('A3 queue', len(queue), 'screened out', len(out), 'tried', len(tried),
          'with PDF', sum(bool(r['pdf']) for r in tried),
          'first 70 with PDF', sum(bool(r.get('pdf')) for r in queue[:70]))


if __name__ == '__main__':
    os.makedirs(PDFDIR, exist_ok=True)
    pop = pop_2018()
    dump(pop, 'rl_population_2018.json')
    print('2018 population', len(pop), {v: sum(p['venue'] == v for p in pop) for v in ('ICML 2018', 'NeurIPS 2018', 'ICLR 2018')})
    if '--a3-only' not in sys.argv:
        draw_a2(pop)
    if '--a2-only' not in sys.argv:
        draw_a3()
