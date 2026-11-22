"""Draw of the blind human re-reading (PROTOCOL.md, deviation 35, written before this draw).

Frame: the experimental papers of the main comparison (samples.py), minus every paper already re-read or designated
for a re-reading: a file in codes/G, codes_v2/G2, R2, R3, pilot, codes_x8/S7, S8, or one of the ten A1 papers
(deviation 13). random.Random(2034): 15 of the sorted 2018 ids (rng.sample), then 15 of the sorted 2026 ids, then the
30 ids shuffled and named H01 to H30 in that order.
The reader must not open the output before filling the 30 sheets: it maps each sheet to its paper.
Run from study/: ../sim/env-an/bin/python relecture_humaine/tirage35.py  -> relecture_humaine/tirage35.json
"""
import json
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE.parent)
sys.path.insert(0, str(HERE.parent))
from samples import classic26, experimental, ours18  # noqa: E402

A1 = ["NE16", "LR16", "LR05", "MLR06", "LR02", "LR08", "ML03", "NER06", "ML06", "ML15"]
REREAD = ["codes/G", "codes_v2/G2", "codes_v2/R2", "codes_v2/R3", "codes_v2/pilot", "codes_x8/S7", "codes_x8/S8"]
N = 15

excluded = {}
for d in REREAD:
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            excluded.setdefault(f[:-5], []).append(d)
for p in A1:
    excluded.setdefault(p, []).append("A1")
e18, e26 = experimental(ours18), experimental(classic26)
f18 = sorted(p for p in e18 if p not in excluded)
f26 = sorted(p for p in e26 if p not in excluded)
rng = random.Random(2034)
s18, s26 = rng.sample(f18, N), rng.sample(f26, N)
ids = s18 + s26
rng.shuffle(ids)
sheets = {f"H{i + 1:02d}": p for i, p in enumerate(ids)}
out = dict(sheets=sheets, year={h: ("2018" if p in s18 else "2026") for h, p in sheets.items()},
           frame=dict(experimental_2018=len(e18), experimental_2026=len(e26), left_2018=len(f18), left_2026=len(f26)),
           excluded={p: excluded[p] for p in sorted(set(excluded) & set(e18 + e26))})
json.dump(out, open(HERE / "tirage35.json", "w"), indent=1)
print(f"frame: {len(f18)} of 2018, {len(f26)} of 2026 left; {len(sheets)} sheets written to tirage35.json")
