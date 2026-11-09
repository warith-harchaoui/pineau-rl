"""A1: agreement between the blind human reading (grille.csv) and the agents' raw reading (study/codes/)."""
import csv, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import os; os.chdir(HERE.parent)
from load import load
D = load("ABCDE")
rows = list(csv.DictReader(open(HERE / "grille.csv")))
assert all(r["Q4"] for r in rows), "grille.csv is not filled in yet"
out = {}
for c in ("Q4", "Q5", "Q6", "Q7", "Q8", "X1", "X2"):
    pairs, dis = [], []
    for r in rows:
        h = r[c].strip() or None
        a = D[r["id"]]["criteria"][c]
        av = None if a["value"] is None else str(a["value"])
        h = None if h is None else (str(int(h)) if c == "X1" else h)
        pairs.append((h, av))
        if h != av:
            dis.append(dict(id=r["id"], human=h, human_quote=r[c + "_citation"], agent=av, agent_quote=a["quote"]))
    n, same = len(pairs), sum(h == a for h, a in pairs)
    cats = {x for p in pairs for x in p}
    pe = sum((sum(h == k for h, _ in pairs) / n) * (sum(a == k for _, a in pairs) / n) for k in cats)
    out[c] = dict(same=same, n=n, kappa=None if pe == 1 else round((same / n - pe) / (1 - pe), 2), disagreements=dis)
    print(f"{c}: {same}/{n} kappa={out[c]['kappa']}")
json.dump(out, open(HERE / "compare.json", "w"), indent=1, ensure_ascii=False)
