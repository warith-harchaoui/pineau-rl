"""E7, the rankings under modified physics tested (SIM_PROTOCOL.md, deviation 24, written before this computation).
Per task and pair: probability of improvement with its 95% interval (rliable, 2,000 resamples, global generator seeded
with 2026) and the two-sided Mann-Whitney p, on the final score in the training physics (eval_mean) and in the
modified physics (perturbed_mean: masses x 1.2, friction x 0.8). A pair "reverses, settled" when settled one way in
the training physics and the other way in the modified physics. Then at each strength of the dose (deviation 12 (ii),
results/dose/), the same probabilities per task, and whether the IQM leader beats every other program, settled.
Main question fixed in advance: Hopper, PPO-sbx against CrossQ and against SAC; the rest is descriptive.
Run from sim/: env-an/bin/python analysis/e7_test.py  -> analysis/e7_test.json  (SEEDS=0:20 SUFFIX=_s20)
"""
import itertools, json, sys
import numpy as np
from scipy import stats
from pineau_rl.bootstrap import iqm, improvement_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from pineau_rl.runs import finals
sys.path.insert(0, "analysis")
from runs import ALGOS, FINAL, ROOT, SEEDS, TASKS, out_json


def pairs(S):
    out = {}
    for a, b in itertools.combinations(ALGOS, 2):
        p, lo, hi = improvement_interval(S[a], S[b], reps=2000, random_state=RS)
        out[f"{a}>{b}"] = dict(p=p, ci=[lo, hi], settled=not (lo <= .5 <= hi),
                               mw_p=float(stats.mannwhitneyu(S[a], S[b], alternative="two-sided").pvalue))
    return out


def leader(S, P):
    I = {a: float(iqm(S[a])) for a in ALGOS}
    top = max(I, key=I.get)
    beats_all = all(P[f"{a}>{b}"]["settled"] and (P[f"{a}>{b}"]["p"] > .5) == (a == top)
                    for a, b in itertools.combinations(ALGOS, 2) if top in (a, b))
    return dict(iqm=I, leader=top, leader_beats_all_settled=beats_all)


res = dict(tasks={}, dose={})
for task in TASKS:
    T = {a: finals(ROOT, a, task, SEEDS, FINAL[a], strict=True) for a in ALGOS}
    M = {a: finals(ROOT, a, task, SEEDS, FINAL[a], column="perturbed_mean", strict=True) for a in ALGOS}
    PT, PM = pairs(T), pairs(M)
    rev = [k for k in PT if PT[k]["settled"] and PM[k]["settled"] and (PT[k]["p"] > .5) != (PM[k]["p"] > .5)]
    res["tasks"][task] = dict(training=dict(pairs=PT, **leader(T, PT)), modified=dict(pairs=PM, **leader(M, PM)),
                              settled_reversals=rev)
    print(task, "reversals:", rev, " modified leader", res["tasks"][task]["modified"]["leader"],
          "beats all:", res["tasks"][task]["modified"]["leader_beats_all_settled"])
    for k in ("crossq>ppo_sbx", "sac>ppo_sbx", "ppo_sb3>ppo_sbx"):
        k2 = k if k in PM else "{1}>{0}".format(*k.split(">"))
        print(f"   {k2}: training {PT[k2]['p']:.2f} {np.round(PT[k2]['ci'], 2)}  modified {PM[k2]['p']:.2f} "
              f"{np.round(PM[k2]['ci'], 2)} MW {PM[k2]['mw_p']:.4f}")
    D = {a: [json.load(open(f"results/dose/{a}/{task}/seed{s}.json")) for s in SEEDS] for a in ALGOS}
    res["dose"][task] = {}
    for q in ("mass", "friction"):
        for k in D[ALGOS[0]][0][q]:
            S = {a: np.array([d[q][k] for d in D[a]]) for a in ALGOS}
            P = pairs(S)
            res["dose"][task][f"{q} x{k}"] = dict(pairs=P, **leader(S, P))
    print("   dose leaders:", {k: (v["leader"], v["leader_beats_all_settled"]) for k, v in res["dose"][task].items()})
json.dump(res, open(out_json("e7_test"), "w"), indent=1)
