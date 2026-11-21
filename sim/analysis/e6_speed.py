"""E6, the speed of the official agents read from their training logs (SIM_PROTOCOL.md, deviation 31, written before
this computation). Hopper's reward per step is the forward velocity + 1 (healthy) - 0.001 |a|^2, so a return per step
near 1 over a 1,000-step episode is a robot standing still. In zoo_official/seed<i>/ppo/Hopper-v4_1/0.monitor.csv
(raw rewards, before normalisation), over the last 200 training episodes: share of 1,000-step episodes, return per step
of these (median and range), hence a lower bound of the mean forward speed (return per step - 1; the action cost only
adds), and the median length of the other episodes.
Run from sim/: env-an/bin/python analysis/e6_speed.py  -> analysis/e6_speed.json
"""
import csv, json
import numpy as np

res = dict(seeds={})
for s in range(10):
    rows = list(csv.DictReader(l for l in open(f"zoo_official/seed{s}/ppo/Hopper-v4_1/0.monitor.csv") if not l.startswith("#")))
    r = np.array([float(x["r"]) for x in rows[-200:]]); n = np.array([int(x["l"]) for x in rows[-200:]])
    full = n == 1000
    rps = r[full] / 1000
    res["seeds"][s] = dict(episodes=len(rows), share_full_length=float(full.mean()),
                           return_per_step_full_median=float(np.median(rps)) if full.any() else None,
                           return_per_step_full_min=float(rps.min()) if full.any() else None,
                           return_per_step_full_max=float(rps.max()) if full.any() else None,
                           speed_lower_bound_median=float(np.median(rps) - 1) if full.any() else None,
                           median_length_other=float(np.median(n[~full])) if (~full).any() else None)
    print(s, res["seeds"][s])
allr = [v["return_per_step_full_median"] for v in res["seeds"].values() if v["return_per_step_full_median"] is not None]
res["summary"] = dict(seeds_with_full_episodes=len(allr), return_per_step_median_of_seeds=float(np.median(allr)),
                      range=[float(min(allr)), float(max(allr))])
print(res["summary"])
json.dump(res, open("analysis/e6_speed.json", "w"), indent=1)
