"""Effect sizes in score points (SIM_PROTOCOL.md, deviation 30, written before this computation).
Beside each probability of improvement, the gap in score points: the Hodges-Lehmann estimator (median of the pairwise
differences x_i - y_j) with a 95% percentile interval (5,000 resamples, each group resampled separately,
default_rng(2026)), and the difference of interquartile means. For each pair of E2 on each task (ten and twenty seeds,
each program at its budget), for E3 (the rows ppo_sb3-ppo_sbx of E2: SB3 minus sbx) and for E6 (official, corrected Zoo and
default on Hopper-v4, from e6_official.json; corrected Zoo against default on Hopper-v5).
Run from sim/: env-an/bin/python analysis/effect_sizes.py  -> analysis/effect_sizes.json
"""
import itertools, json, sys
import numpy as np
from pineau_rl.bootstrap import iqm
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, TASKS
from pineau_rl.runs import finals

rng = np.random.default_rng(2026)


def effect(x, y, reps=5000):
    hl = lambda a, b: float(np.median(a[:, None] - b[None, :]))
    boots = [hl(rng.choice(x, len(x)), rng.choice(y, len(y))) for _ in range(reps)]
    return dict(hodges_lehmann=hl(x, y), ci=np.percentile(boots, [2.5, 97.5]).tolist(),
                iqm_difference=float(iqm(x) - iqm(y)), n=[len(x), len(y)])


res = dict(e2={})
for name, seeds in (("s10", range(10)), ("s20", range(20))):
    res["e2"][name] = {}
    for task in TASKS:
        G = {a: finals(ROOT, a, task, seeds, FINAL[a], strict=True) for a in ALGOS}
        res["e2"][name][task] = {f"{a}-{b}": effect(G[a], G[b]) for a, b in itertools.combinations(ALGOS, 2)}
        print(name, task, {k: round(v["hodges_lehmann"]) for k, v in res["e2"][name][task].items()})
e6 = json.load(open("analysis/e6_official.json"))["groups"]
G6 = {k: np.array(v["runs"]) for k, v in e6.items()}
v5 = {t: finals(ROOT, t, "Hopper-v5", range(10), 1_000_000, strict=True) for t in ("ppo_sb3_zoofix", "ppo_sb3")}
res["e6"] = {"official v4 - zoofix v4": effect(G6["official v4"], G6["zoofix v4"]),
             "official v4 - default v4": effect(G6["official v4"], G6["default v4"]),
             "zoofix v4 - default v4": effect(G6["zoofix v4"], G6["default v4"]),
             "zoofix v5 - default v5": effect(v5["ppo_sb3_zoofix"], v5["ppo_sb3"])}
for k, v in res["e6"].items():
    print("E6", k, round(v["hodges_lehmann"]), np.round(v["ci"]))
json.dump(res, open("analysis/effect_sizes.json", "w"), indent=1)
