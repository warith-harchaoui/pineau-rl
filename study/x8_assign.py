"""Reading lists of criterion X8 (PROTOCOL.md, deviation 32), written before any reading.

Sample: the papers of the main comparison with final X2 yes (our 2018, classical RL 2026). Primary readers S1 to S6:
the sorted ids shuffled by random.Random(2032), dealt in turn. Double reading: 10 papers per year drawn by
random.Random(2033), re-read by S7 and S8, each 5 of 2018 and 5 of 2026.
Run from study/: ../sim/env-an/bin/python x8_assign.py  -> assignments_x8.json
"""
import json, random
from samples import classic26, experimental, ours18, val

y18 = sorted(p for p in experimental(ours18) if val(p, "X2") == "yes")
y26 = sorted(p for p in experimental(classic26) if val(p, "X2") == "yes")
ids = sorted(y18 + y26)
random.Random(2032).shuffle(ids)
out = {f"S{i + 1}": sorted(ids[i::6]) for i in range(6)}
rng = random.Random(2033)
d18, d26 = rng.sample(y18, 10), rng.sample(y26, 10)
out["S7"], out["S8"] = sorted(d18[:5] + d26[:5]), sorted(d18[5:] + d26[5:])
out["_years"] = {"2018": y18, "2026": y26}
json.dump(out, open("assignments_x8.json", "w"), indent=1)
for r in [f"S{i}" for i in range(1, 9)]:
    print(r, len(out[r]), sum(p in y18 for p in out[r]), "of 2018")
print(len(y18), len(y26))
