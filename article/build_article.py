"""Builds the blog article « A-t-on écouté Joelle Pineau en 2018 ? » for deraison.ai, from fr.txt and en.txt.

Writes, under an output directory that mirrors the site's tree:
  pages/fr/blog/ecouter-joelle-pineau.php
  pages/en/blog/ecouter-joelle-pineau.php
  assets/images/blog/rl-pineau-<figure>-<lang>.svg      (copied from figures/, built by figures/build.py)
  assets/images/blog/rl-pineau-<figure>-mobile-<lang>.svg  (its narrow twin, served under 640 px by <picture>)
  assets/css/article-<slug>.css                         (the page's scoped rules, to paste into base.css)
  assets/images/og/blog-<slug>.png                      (with --og: the Open Graph card, 1200 x 630)
  preview/<lang>.html                                   (with --preview: a standalone page to look at)

The output directory comes from --out DIR, else the DERAISON_OUT environment variable. There is no default:
the site (~/web/deraison) is written only when it is named explicitly.

    python3 build_article.py --out /tmp/staging --preview --og
    DERAISON_OUT=~/web/deraison python3 build_article.py fr en

Light markup, one line per block (paragraphs separated by a blank line):
  META chip | date-iso | date lisible | titre | chapeau
  BRIEF titre-encadré | titre-sommaire          (puis les paragraphes de l'encadré, jusqu'à ENDBRIEF)
  ## ancre | Titre de section
  ### Sous-titre
  FIG wide|std|portrait | src (relatif à assets/images/blog) | alt | légende (HTML permis)
  VIDEO identifiant YouTube | titre du lecteur | légende (HTML permis)
  HERO | src | alt | crédit (HTML permis) : l'image de tête, sous le chapeau
  - élément de liste (lignes consécutives)
  <...>  ligne HTML passée telle quelle
  BIBLIO titre | phrase d'introduction
  REF n | notice (HTML) | note
Dans le texte : [[n]] appel de note, *italique*, **gras**, [texte](url) lien externe,
{{/chemin}} lien interne au site (url()). Les liens vers le dépôt (https://github.com/warith-harchaoui/pineau-rl) s'ouvrent dans un nouvel onglet.
En français, les espaces avant : ; ? ! % » et après « deviennent insécables, comme l'espace des milliers.
"""
import argparse
import hashlib
import html
import os
import re
import subprocess
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).parent
SITE = Path("/Users/warithharchaoui/web/deraison")  # read-only here: CSS, fonts and photos for the preview
SLUGS = {"fr": "ecouter-joelle-pineau", "en": "listen-to-joelle-pineau"}  # the site pairs them through the registry key "twin"
FIG_PREFIX = "rl-pineau-"
# The full document, served by deraison.ai itself rather than GitHub: (source in docs/, name on the site)
PDFS = {"fr": ("conclusions.pdf", "apprentissage-par-renforcement-a-t-on-ecoute-joelle-pineau.pdf"),
        "en": ("conclusions-en.pdf", "reinforcement-learning-did-we-listen-to-joelle-pineau.pdf")}


def inline(s: str, lang: str) -> str:
    s = re.sub(r"\[\[(\d+)\]\]", r'<sup class="drz-ref"><a class="drz-text" href="#ref-\1">\1</a></sup>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r'<strong class="drz-text">\1</strong>', s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r'<em class="drz-text">\1</em>', s)
    s = re.sub(r"\[([^\]]+)\]\((https://github\.com/warith-harchaoui/pineau-rl[^)\s]*)\)", r'<a class="drz-text" href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a class="drz-text" href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\[([^\]]+)\]\{\{([^}]+)\}\}", r'<a class="drz-text" href="<?= url(\'\2\') ?>">\1</a>', s)
    s = re.sub(r"\[([^\]]+)\]\((#[^)]+)\)", r'<a class="drz-text" href="\2">\1</a>', s)
    s = re.sub(r"\[([^\]]+)\]\(/assets/([^)\s]+)\)", r'<a class="drz-text" href="<?= ASSETS ?>/\2">\1</a>', s)
    # the full document carries a fingerprint of its content, so a cache never serves an older version
    s = re.sub(r'(/pdf/([\w.-]+\.pdf))"', lambda m: f'{m[1]}?v={pdf_version(m[2])}"', s)
    if lang == "fr":
        s = nbsp(s)
    return s


def pdf_version(name: str) -> str:
    src = {site: ICI.parent / "docs" / doc for doc, site in PDFS.values()}[name]
    return hashlib.sha256(src.read_bytes()).hexdigest()[:10]


def nbsp(s: str) -> str:
    # n'agit que hors des balises et hors du PHP
    parts = re.split(r"(<\?=.*?\?>|<[^>]+>)", s)
    out = []
    for p in parts:
        if p.startswith("<"):
            out.append(p)
            continue
        p = re.sub(r" ([:;?!%»])", r"&nbsp;\1", p)
        p = re.sub(r"« ", "«&nbsp;", p)
        p = re.sub(r"(?<=\d) (?=\d{3}\b)", "&nbsp;", p)
        out.append(p)
    return "".join(out)


def renumber(raw: str) -> str:
    """Numérote les notes dans l'ordre de leur premier appel et trie la bibliographie."""
    head, sep, tail = raw.partition("\nBIBLIO ")
    order = []
    for n in re.findall(r"\[\[(\d+)\]\]", head):
        if n not in order:
            order.append(n)
    new = {old: str(i + 1) for i, old in enumerate(order)}
    head = re.sub(r"\[\[(\d+)\]\]", lambda m: f"[[{new[m.group(1)]}]]", head)
    tl = tail.split("\n")
    refs = [l for l in tl if l.startswith("REF ")]
    other = [l for l in tl if not l.startswith("REF ")]
    unused = [l for l in refs if l[4:].split("|")[0].strip() not in new]
    if unused:
        raise SystemExit(f"notices jamais appelées : {unused}")
    refs = sorted(("REF " + new[l[4:].split("|")[0].strip()] + " |" + l.split("|", 1)[1] for l in refs),
                  key=lambda l: int(l[4:].split("|")[0]))
    return head + sep + "\n".join([x for x in other if x.strip()] + refs) + "\n"


def build(lang: str) -> str:
    raw = (ICI / f"{lang}.txt").read_text(encoding="utf-8")
    raw = renumber(raw)
    # HERO | src | alt | credit: the image under the lede, as the site's other articles have one
    hero_html = ""
    mh = re.search(r"^HERO \| (.+?) \| (.+?) \| (.+)$", raw, flags=re.M)
    if mh:
        raw = raw[:mh.start()] + raw[mh.end():]
        src, alt, credit = mh.group(1).strip(), mh.group(2).strip(), mh.group(3).strip()
        hero_html = (f'        <div class="drz-photo-hero">\n'
                     f'            <img src="<?= ASSETS ?>/images/{src if "/" in src else "blog/" + src}" alt="{html.escape(alt, quote=True)}" loading="eager">\n'
                     f'            <p class="drz-text drz-hero-credit">{inline(credit, lang)}</p>\n'
                     f'        </div>')
    lines = raw.split("\n")
    blocks, buf = [], []
    for ln in lines + [""]:
        if ln.strip() == "":
            if buf:
                blocks.append(buf)
                buf = []
        else:
            buf.append(ln)
    meta = None
    body = []
    toc = []
    brief = None
    in_brief = False
    biblio = []
    biblio_head = None
    for b in blocks:
        first = b[0]
        if first.startswith("META "):
            meta = [x.strip() for x in first[5:].split("|")]
            continue
        if first.startswith("BRIEF "):
            brief = {"head": [x.strip() for x in first[6:].split("|")], "items": []}
            in_brief = True
            rest = b[1:]
            if rest:
                brief["items"].append(rest)
            continue
        if first.strip() == "ENDBRIEF":
            in_brief = False
            continue
        if in_brief:
            if "ENDBRIEF" in [x.strip() for x in b]:
                b = [x for x in b if x.strip() != "ENDBRIEF"]
                in_brief = False
            if b:
                brief["items"].append(b)
            continue
        if first.startswith("BIBLIO "):
            biblio_head = [x.strip() for x in first[7:].split("|")]
            for r in b[1:]:
                biblio.append(r)
            continue
        if first.startswith("REF "):
            biblio.extend(b)
            continue
        out = []
        para = []

        def flush():
            if para:
                out.append(f'            <p dir="auto" class="drz-text drz-text-body">{inline(" ".join(para), lang)}</p>')
                para.clear()

        items = []
        for ln in b:
            if ln.startswith("## "):
                flush()
                anchor, title = [x.strip() for x in ln[3:].split("|", 1)]
                toc.append((anchor, title))
                out.append(f'            <h2 id="{anchor}" dir="auto" class="drz-text drz-text-section">\n                <br>{inline(title, lang)}\n            </h2>')
            elif ln.startswith("### "):
                flush()
                out.append(f'            <h3 dir="auto" class="drz-text drz-text-subsection">{inline(ln[4:], lang)}</h3>')
            elif ln.startswith("FIG "):
                flush()
                kind, src, alt, cap = [x.strip() for x in ln[4:].split("|", 3)]
                cls = {"wide": "drz-art-fig drz-art-fig--wide", "portrait": "drz-art-fig drz-art-fig--portrait"}.get(kind, "drz-art-fig")
                mob = mobile_name(src)
                source = (f'<source media="(max-width: 640px)" srcset="<?= ASSETS ?>/images/blog/{mob}">'
                          if mob else "")
                out.append(
                    f'            <div class="{cls}"><picture>{source}<img src="<?= ASSETS ?>/images/blog/{src}"\n'
                    f'                    alt="{html.escape(alt, quote=True)}"\n'
                    f'                    loading="lazy"></picture>\n'
                    f'                <p class="drz-text drz-art-figcap">{inline(cap, lang)}</p>\n'
                    f'            </div>')
            elif ln.startswith("VIDEO "):
                flush()
                vid, vtitle, cap = [x.strip() for x in ln[6:].split("|", 2)]
                out.append(
                    f'            <div class="drz-art-fig drz-art-fig--wide"><div style="position:relative;width:100%;aspect-ratio:16/9">'
                    # YouTube's own embed code, as its Share > Embed button gives it, made fluid
                    f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{vid}" title="{html.escape(vtitle, quote=True)}"\n'
                    f'                    frameborder="0" style="position:absolute;inset:0;width:100%;height:100%;border-radius:8px"\n'
                    f'                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"\n'
                    f'                    referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>\n'
                    f'                <p class="drz-text drz-art-figcap">{inline(cap, lang)}</p>\n'
                    f'            </div>')
            elif ln.startswith("- "):
                flush()
                items.append(f'                <li class="drz-text">{inline(ln[2:], lang)}</li>')
            elif ln.startswith("<"):
                flush()
                if items:
                    out.append('            <ul class="drz-art-list drz-text">\n' + "\n".join(items) + "\n            </ul>")
                    items = []
                out.append("            " + (nbsp(ln) if lang == "fr" else ln))
            else:
                if items:
                    out.append('            <ul class="drz-art-list drz-text">\n' + "\n".join(items) + "\n            </ul>")
                    items = []
                para.append(ln)
        flush()
        if items:
            out.append('            <ul class="drz-art-list drz-text">\n' + "\n".join(items) + "\n            </ul>")
        body.append("\n".join(out))

    chip, date_iso, date_txt, title, lede = meta
    brief_html = ""
    if brief:
        bt, toct = brief["head"]
        inner = []
        for blk in brief["items"]:
            if all(x.startswith("- ") for x in blk):
                inner.append('            <ul class="drz-art-list drz-text">\n' + "\n".join(
                    f'                <li class="drz-text">{inline(x[2:], lang)}</li>' for x in blk) + "\n            </ul>")
            else:
                inner.append(f'            <p dir="auto" class="drz-text drz-text-body">{inline(" ".join(blk), lang)}</p>')
        toc_html = "\n".join(
            f'                        <li class="drz-text"><a class="drz-text" href="#{a}">{inline(t, lang)}</a></li>' for a, t in toc)
        brief_html = (
            f'            <section class="drz-art-brief" aria-labelledby="drz-brief-t">\n'
            f'                <p class="drz-art-brief-title drz-text" id="drz-brief-t">{bt}</p>\n'
            + "\n".join(inner) + "\n"
            f'                <nav class="drz-art-toc" aria-label="{toct}">\n'
            f'                    <p class="drz-art-toc-title drz-text">{toct}</p>\n'
            f'                    <ol class="drz-text">\n{toc_html}\n                    </ol>\n'
            f'                </nav>\n            </section>')

    refs = []
    for r in biblio:
        n, cite, note = [x.strip() for x in r[4:].split("|", 2)]
        refs.append(f'                <li id="ref-{n}" class="drz-text"><cite class="drz-text">{inline(cite, lang)}</cite> '
                    f'<span class="drz-biblio-note drz-text">{inline(note, lang)}</span></li>')
    bh, bi = biblio_head
    back = "← Retour au blog" if lang == "fr" else "← Back to the blog"
    page = f'''<?php if (!defined('DERAISON')) {{
    http_response_code(403);
    exit;
}} ?>
<style>
    html body {{
        background: none;
    }}
</style>
<div
    class="drz-article-scope drz-text-title-scope drz-text-heading-scope drz-text-subheading-scope drz-text-subsection-scope drz-text-section-scope drz-text-body-scope drz-article-page"
    style="min-height:100vh;width:auto;display:contents">
    <article class="drz-article-main">
        <div class="drz-article-header">
            <div class="drz-article-meta">
                <div class="drz-article-chip">
                    <div class="drz-article-chip-text" data-drz-box="RichTextContainer" style="transform:none">
                        <p dir="auto" style="--ui-font-size:12px;--ui-text-color:rgb(17, 17, 17)"
                            class="drz-text">{chip}</p>
                    </div>
                </div>
                <div class="drz-article-date" data-drz-box="RichTextContainer" style="transform:none">
                    <p dir="auto" style="--ui-font-size:14px;--ui-line-height:1.4em;--ui-text-color:#777777"
                        class="drz-text"><time datetime="{date_iso}T00:00:00.000Z">{date_txt}</time></p>
                </div>
            </div>
            <div class="drz-article-title" data-drz-box="RichTextContainer" style="transform:none">
                <h1 dir="auto"
                    style="--ui-font-size:clamp(32px, 6vw, 56px);--ui-letter-spacing:-0.04em;--ui-line-height:1.05em;--ui-text-color:#111111"
                    class="drz-text">{inline(title, lang).replace("A-t-on", '<span style="white-space:nowrap">A-t-on</span>')}</h1>
            </div>
            <div class="drz-article-lede" data-drz-box="RichTextContainer" style="transform:none">
                <p dir="auto"
                    style="--ui-letter-spacing:-0.01em;--ui-line-height:1.55em;--ui-text-color:rgb(102, 102, 102)"
                    class="drz-text">{inline(lede, lang)}</p>
            </div>
        </div>
{hero_html}
        <div class="drz-article-content" data-drz-box="RichTextContainer"
            style="transform:none">
{brief_html}
{chr(10).join(body)}
            <h2 dir="auto" class="drz-text drz-text-section">
                <br>{bh}
            </h2>
            <p dir="auto" class="drz-text drz-text-body">{inline(bi, lang)}</p>
            <ol class="drz-biblio drz-text">
{chr(10).join(refs)}
            </ol>
        </div>
        <div class="drz-article-footer" data-border="true">
            <div class="drz-article-back" data-drz-box="RichTextContainer" style="transform:none">
                <p dir="auto" style="--ui-font-size:14px;--ui-line-height:1.4em;--ui-text-color:#555555"
                    class="drz-text"><a class="drz-text"
                        href="<?= url('/blog') ?>">{back}</a></p>
            </div><svg class="drz-article-icon-mask drz-article-icon" role="presentation" viewBox="0 0 24 24">
                <use href="#3166100823" />
            </svg>
        </div>
    </article>
</div>
<div id="svg-templates"
    style="position: absolute; overflow: hidden; bottom: 0; left: 0; width: 0; height: 0; z-index: 0; contain: strict"
    aria-hidden="true">
    <svg id="3166100823" display="block" role="presentation" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M 0 0 L 7.5 7.5 L 0 15 Z" fill-opacity="var(--1m6trwb, 0)" fill="var(--21h8s6, rgb(0, 0, 0))"
            height="15px" id="G7JipcseD" transform="translate(9 4.5)" width="7.5px" />
        <path d="M 0 0 L 7.5 7.5 L 0 15" fill="transparent" height="15px" id="qoOYEIyEO" stroke-dasharray=""
            stroke-linecap="round" stroke-linejoin="round" stroke-width="var(--pgex8v, 1.5)"
            stroke="var(--21h8s6, rgb(0, 0, 0))" transform="translate(9 4.5)" width="7.5px" />
    </svg>
</div>
'''
    return page


def mobile_name(src: str):
    """rl-pineau-<name>-<lang>.svg has a narrow twin rl-pineau-<name>-mobile-<lang>.svg for phones."""
    m = re.fullmatch(re.escape(FIG_PREFIX) + r"(.+)-(fr|en)\.svg", src)
    if m and (ICI / "figures" / f"{m[1]}-mobile-{m[2]}.svg").exists():
        return f"{FIG_PREFIX}{m[1]}-mobile-{m[2]}.svg"
    return None


def figures_used(lang: str) -> list[str]:
    raw = (ICI / f"{lang}.txt").read_text(encoding="utf-8")
    return re.findall(r"^FIG \w+ \| (\S+)", raw, flags=re.M)


def copy_assets(out: Path, lang: str) -> None:
    """Our figures go next to the page; the site's own photos are copied only into a staging folder."""
    dst = out / "assets" / "images" / "blog"
    dst.mkdir(parents=True, exist_ok=True)
    for src in figures_used(lang):
        if src.startswith(FIG_PREFIX) and (ICI / "figures" / src[len(FIG_PREFIX):]).exists():
            shutil.copy(ICI / "figures" / src[len(FIG_PREFIX):], dst / src)
            if mobile_name(src):
                shutil.copy(ICI / "figures" / mobile_name(src)[len(FIG_PREFIX):], dst / mobile_name(src))
        elif out.resolve() != SITE.resolve():
            shutil.copy(SITE / "assets" / "images" / "blog" / src, dst / src)
    pdf = out / "assets" / "pdf" / PDFS[lang][1]
    pdf.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ICI.parent / "docs" / PDFS[lang][0], pdf)
    css = out / "assets" / "css" / f"article-{SLUGS[lang]}.css"
    css.parent.mkdir(parents=True, exist_ok=True)
    css.write_text((ICI / "site" / "article.css.tmpl").read_text().replace("SLUG", SLUGS[lang]))


def preview(out: Path, lang: str, page: str) -> Path:
    """A standalone HTML page: the site's stylesheets, the page's scoped rules, the PHP calls resolved."""
    body = page.split("?>", 1)[1]
    body = body.replace("<?= ASSETS ?>", "../assets").replace("<?= url('/blog') ?>", "#")
    body = re.sub(r"<\?= url\('([^']*)'\) \?>", r"\1", body)
    body = re.sub(r"<\?php require_once [^\n]*?\?>", "", body)
    cal = "https://calendly.com/warith-harchaoui/" + ("discuter" if lang == "fr" else "discuss")  # what /rdv redirects to
    body = re.sub(r"<\?= drz_button\(e\(rdv_url\(\)\), '([^']*)'[^\n]*?\?>",
                  lambda m: f'<a class="drz-art-cta" href="{cal}" target="_blank" rel="noopener">{m[1]}&nbsp;↗</a>', body)
    links = "".join(f'<link rel="stylesheet" href="{SITE.as_uri()}/assets/css/{c}">' for c in ("fonts.css", "site.css", "base.css"))
    doc = (f'<!doctype html><html class="drz-p-blog__{SLUGS[lang]}" lang="{lang}"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width">{links}'
           f'<link rel="stylesheet" href="../assets/css/article-{SLUGS[lang]}.css"></head><body>{body}</body></html>')
    dst = out / "preview" / f"{lang}.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(doc, encoding="utf-8")
    return dst


def og_card(out: Path, lang: str) -> Path:
    """The Open Graph card, 1200 x 630, drawn by the site's own generator (Satoshi, the h1 rule) around the hero photo, as every other card."""
    title = re.search(r"^META [^|]*\|[^|]*\|[^|]*\| ([^|]+?) \|", (ICI / f"{lang}.txt").read_text(), flags=re.M)[1]
    dst = out / "assets" / "images" / "og" / f"blog-{SLUGS[lang]}-{lang}.png"  # one card per language
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(SITE / "tools" / "og-cards" / "make_og.py"), "--lang", lang, "--title", title,
                    "--hero", str(SITE / "assets" / "images" / "conferences" / "joelle-pineau.webp"), "--out", str(dst)],
                   check=True, capture_output=True)
    return dst


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("langs", nargs="*", default=["fr", "en"])
    ap.add_argument("--out", default=os.environ.get("DERAISON_OUT"), help="output directory (or DERAISON_OUT)")
    ap.add_argument("--preview", action="store_true", help="also write preview/<lang>.html")
    ap.add_argument("--og", action="store_true", help="also render the Open Graph card")
    a = ap.parse_args()
    if not a.out:
        sys.exit("no output directory: pass --out DIR or set DERAISON_OUT")
    out = Path(a.out).expanduser()
    for lang in a.langs:
        page = build(lang)
        dst = out / "pages" / lang / "blog" / f"{SLUGS[lang]}.php"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page, encoding="utf-8")
        copy_assets(out, lang)
        print("écrit", dst)
        if a.preview:
            print("aperçu", preview(out, lang, page))
        if a.og:
            print("carte", og_card(out, lang))
