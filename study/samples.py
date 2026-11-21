"""The two samples of the main comparison and their final values, exactly as extension_stats.py builds them
(PROTOCOL.md, deviation 12), for the scripts of deviations 30 to 33 that need them without rerunning that script.

    from samples import ours18, classic26, val      # 50 + 50 ids; val(pid, k) final harmonised value, Y3 as yes/no
"""
import json
from pineau_rl.grid import list_readers, load_overrides, load_reads, value
from load import load

N_A3 = 36
PRIMARY = ["A2", "B2", "C2", "D2", "E2", "F2", "H1", "H2", "H3", "H4"]
ov1, ov2 = load_overrides("overrides.json", missing_ok=True), load_overrides("overrides_v2.json", missing_ok=True)
OLD = load("ABCDEF")
V2READ = load_reads("codes_v2", PRIMARY + list_readers("codes_v2", "K*"))


def val(pid, k, y3=True):
    return value(pid, k, V2READ, OLD, ov2, ov1, y3=y3)


ours18 = sorted(p for p in OLD if p.startswith("C")) + [x["id"] for x in json.load(open("calib_2018_v2.json"))[12:]]
all26 = sorted(p for p in OLD if not p.startswith("C"))
_queue = [x["id"] for x in json.load(open("classic_queue_2026.json"))]
_a3 = [p for p in _queue if p in V2READ and val(p, "X5") == "classic"][:N_A3]
classic26 = sorted(p for p in all26 if val(p, "X5") == "classic") + _a3
assert len(ours18) == len(classic26) == 50


def experimental(ids):
    return [p for p in ids if val(p, "Q1") != "no"]
