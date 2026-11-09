import sys
from playwright.sync_api import sync_playwright
from PIL import Image
S = "/private/tmp/claude-501/-Users-warithharchaoui-enterprise-ai/5c5a3839-6024-4a3d-97ae-a7b9fa3acb44/scratchpad"
url, tag, w = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1280
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": w, "height": 900})
    pg.goto(url, wait_until="networkidle")
    pg.evaluate("document.querySelectorAll('[data-drz-reveal]').forEach(e=>e.classList.add('is-visible'))")
    h = pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h, 800):
        pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(60)
    pg.wait_for_timeout(500)
    pg.screenshot(path=f"{S}/{tag}.png", full_page=True)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    b.close()
im = Image.open(f"{S}/{tag}.png"); H = im.size[1]; step = 2600 if w > 500 else 1800
n = 0
for i in range(0, H, step):
    c = im.crop((0, i, im.size[0], min(i + step, H))); c.thumbnail((760, 1600)); c.save(f"{S}/{tag}-{n}.png"); n += 1
print("height", H, "parts", n, "scrollWidth", sw)
