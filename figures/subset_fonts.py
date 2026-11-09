"""Réduit les polices embarquées des SVG sprezzature aux seuls glyphes utilisés."""
import base64, io, re, sys, html
from fontTools import subset
from fontTools.ttLib import TTFont
for path in sys.argv[1:]:
    s = open(path, encoding="utf-8").read()
    text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", " ", s, flags=re.S)))
    chars = set(text) | set("0123456789.,%-+ ")
    def repl(m):
        font = TTFont(io.BytesIO(base64.b64decode(m.group(1))))
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]
        sub = subset.Subsetter(opts); sub.populate(text="".join(chars)); sub.subset(font)
        buf = io.BytesIO(); font.flavor = "woff2"; font.save(buf)
        return "url(data:font/woff2;base64," + base64.b64encode(buf.getvalue()).decode()
    s2 = re.sub(r"url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)", repl, s)
    open(path, "w", encoding="utf-8").write(s2)
    print(path, len(s), "->", len(s2))
