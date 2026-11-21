"""E5, as pre-registered (SIM_PROTOCOL.md, écart 7): how many seeds does it take to recover the right ranking?
For each comparison of E2, the right ranking is that of the means of the 10 runs. For n = 3, 5, 10 and 20, 10,000
draws with replacement of n runs per algorithm among its runs (the observed distribution stands in for the
algorithm; for PPO-SB3 on HalfCheetah, the 30 runs of E1), share of draws that recover the right ranking.
Run from sim/: env-an/bin/python analysis/e5.py  -> analysis/e5.json
"""
import itertools, json, sys
import numpy as np
sys.path.insert(0, "analysis")
from runs import DEFAULT, finals, grid, out_json

G, missing = grid()
if DEFAULT:  # the preregistered analysis uses E1's 30 runs; deviation 12 draws from the chosen seeds only
    G["HalfCheetah-v5"]["ppo_sb3"] = finals("ppo_sb3", "HalfCheetah-v5", range(30))
rng = np.random.default_rng(2026)
NS, N = (3, 5, 10, 20), 10000
comps = []
for task, S in G.items():
    for a, b in itertools.combinations(sorted(S), 2):
        x, y = S[a], S[b]
        k = 10 if DEFAULT else len(x)  # the right ranking: means of the 10 runs; deviation 20: of all the chosen seeds
        right = np.sign(x[:k].mean() - y[:k].mean())
        rel = abs(x[:k].mean() - y[:k].mean()) / max(abs(x[:k].mean()), abs(y[:k].mean()))
        hit = {n: float((np.sign(rng.choice(x, (N, n)).mean(1) - rng.choice(y, (N, n)).mean(1)) == right).mean()) for n in NS}
        comps.append(dict(task=task, pair=f"{a} vs {b}", rel_gap=float(rel), recovered=hit))
close = [c for c in comps if c["rel_gap"] < .2]
res = dict(missing=missing, comparisons=comps,
           median_all={n: float(np.median([c["recovered"][n] for c in comps])) for n in NS},
           n_close=len(close), median_close={n: float(np.median([c["recovered"][n] for c in close])) for n in NS} if close else None)
print("median over", len(comps), "comparisons:", res["median_all"])
print("gaps under 20%:", len(close), res["median_close"], "\nmissing", missing)
json.dump(res, open(out_json("e5"), "w"), indent=1)
