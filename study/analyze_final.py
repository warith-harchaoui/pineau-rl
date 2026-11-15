"""Regenerates results_final.json from the raw reads (codes/) and the harmonisation (overrides.json), for 2026
(readers A to E) and for the 2018 calibration (reader F). Until 9 November 2026 this file was written without
a script (PROTOCOL.md, Écart 15).

Shares are over experimental papers (Q1 not "no"), with a 95% Wilson interval for 2026. The verdict follows
PROTOCOL.md and audit_stats.py: "changé" when the gap with Pineau's 2018 figure passes Holm's correction, and
"confirmé" when it also passes against our own 2018 reading; otherwise "aucun changement détectable".
Run from study/: ../sim/env-an/bin/python analyze_final.py  -> results_final.json
"""
import json
from pineau_rl.grid import load_overrides, tally, value_v1
from pineau_rl.stats import fisher, holm, wilson_ci
from load import load

PINEAU = {"Q1": 1.00, "Q2": .90, "Q3": .90, "Q4": .60, "Q5": .55, "Q6": .20, "Q7": .10, "Q8": .05}
LAB = {"Q1": "Paper has experiments", "Q2": "Uses neural networks", "Q3": "All hyperparams, proposed method",
       "Q4": "All hyperparams, baselines", "Q5": "Code is linked", "Q6": "Hyperparam selection method specified",
       "Q7": "Hold-out evaluation", "Q8": "Significance testing", "X2": "Uncertainty reported",
       "X3": "Best-of / top-k selection", "X4": "Baselines tuned like the method", "X7": "Compute reported"}
ov = load_overrides("overrides.json")


def val(d, k):  # v1 only: this reading and overrides.json
    return value_v1(d, k, ov)


def count(D, k):
    return tally(val(d, k) for d in D.values() if k == "Q1" or val(d, "Q1") != "no")


D26, D18 = load("ABCDE"), load("F")
rows, pin_p, own_p = [], [], []
for k, lab in LAB.items():
    (y, n), (y18, n18) = count(D26, k), count(D18, k)
    lo, hi = wilson_ci(y, n)
    r = dict(k=k, label=lab, pineau2018=PINEAU.get(k), ours2018=f"{y18}/{n18}", ours2018_p=round(y18 / n18, 3),
             y2026=y, n2026=n, p2026=round(y / n, 3), lo=round(lo, 3), hi=round(hi, 3))
    if k in PINEAU and k != "Q1":
        r["p_vs_pineau"] = fisher(y, n, round(PINEAU[k] * 50), 50)
        pin_p.append(r)
    if k != "Q1":
        r["p_vs_ours2018"] = fisher(y, n, y18, n18)
        own_p.append(r)
    rows.append(r)
for group, key in ((pin_p, "p_vs_pineau"), (own_p, "p_vs_ours2018")):
    for r, h in zip(group, holm([r[key] for r in group])):
        r[key + "_holm"] = round(float(h), 4)
        r[key] = round(float(r[key]), 4)
for r in rows:
    pin, own = r.get("p_vs_pineau_holm"), r.get("p_vs_ours2018_holm")
    up = r["pineau2018"] is not None and r["p2026"] > r["pineau2018"]
    if pin is not None and pin < .05:
        r["verdict"] = ("en hausse" if up else "en baisse") + (", confirmé" if own is not None and own < .05 else
                                                              ", non confirmé contre notre lecture de 2018")
    elif own is not None and own < .05:
        r["verdict"] = "écart avec notre lecture de 2018 seulement"
    else:
        r["verdict"] = "aucun changement détectable"
json.dump(rows, open("results_final.json", "w"), indent=1, ensure_ascii=False)
for r in rows:
    print(f"{r['k']}: 2018 Pineau {r['pineau2018']} ours {r['ours2018']}  2026 {r['y2026']}/{r['n2026']} "
          f"[{r['lo']:.2f},{r['hi']:.2f}]  {r['verdict']}")
