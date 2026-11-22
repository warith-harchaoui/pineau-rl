"""Reading lists of deviation 36 (PROTOCOL.md): the year and the readers disentangled, written before any reading.

Sample: the experimental papers of the main comparison, all of them (our 2018: 48, classical RL 2026: 50).
Eight fresh readers T1 to T8. rng = random.Random(2035): the sorted 2018 ids are shuffled and dealt in turn from
T1, then the sorted 2026 ids are shuffled and dealt in turn from a reader drawn by the same rng, so that every
reader reads 6 papers of 2018 and 6 or 7 of 2026. Each list is then shuffled by the same rng: the years are mixed
in the reading order. No double reading (deviation 36 says why).
Run from study/: ../sim/env-an/bin/python r36_assign.py  -> assignments_r36.json
"""
import json, random
from samples import classic26, experimental, ours18

R = [f"T{i}" for i in range(1, 9)]
y18, y26 = sorted(experimental(ours18)), sorted(experimental(classic26))
rng = random.Random(2035)
a, b = y18[:], y26[:]
rng.shuffle(a)
rng.shuffle(b)
out = {r: [] for r in R}
for i, p in enumerate(a):
    out[R[i % 8]].append(p)
start = rng.randrange(8)
for i, p in enumerate(b):
    out[R[(start + i) % 8]].append(p)
for r in R:
    rng.shuffle(out[r])
out["_years"] = {"2018": y18, "2026": y26}
json.dump(out, open("assignments_r36.json", "w"), indent=1)
for r in R:
    print(r, len(out[r]), sum(p in y18 for p in out[r]), "of 2018")
print(len(y18), len(y26))
