"""Why the two PPOs diverge (SIM_PROTOCOL.md, deviation 34, written before any training).
Final score at one million steps on Walker2d-v5 and Swimmer-v5. Three contrasts per task:
  (1) PPO-sbx against PPO-SB3, seeds 0 to 39 (seeds 20 to 39 trained for this deviation);
  (2) PPO-sbx with ortho_init=True (ppo_sbx_ortho) against PPO-sbx (default False), seeds 0 to 19;
  (3) PPO-SB3 (default True) against PPO-SB3 with ortho_init=False (ppo_sb3_noortho), seeds 0 to 19.
For each: probability of improvement with its 95% interval (rliable, 2,000 resamples, global generator seeded with
2026), two-sided Mann-Whitney p, Holm over the 6 tests (2 tasks x 3 contrasts), IQM of each side with its interval and
their ratio, Hodges-Lehmann gap with a 95% percentile interval (5,000 resamples, default_rng(2026)).
Descriptive: ppo_sbx_ortho against PPO-SB3, ppo_sb3_noortho against PPO-sbx (seeds 0 to 19).
Reading: the initialisation explains the gap when (2) and (3) are settled in the direction of the gap and the swap
closes it. Run from sim/ once the 160 runs are finished: env-an/bin/python analysis/c2.py  -> analysis/c2.json
(PARTIAL=1 prints the contrasts on the runs finished so far, writes nothing: a progress check, not a result.)
"""
import json, os
import numpy as np
from scipy import stats
from pineau_rl.bootstrap import iqm_interval, improvement_interval
from pineau_rl.stats import holm
from pineau_rl.runs import finals, read_run, run_path
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
rng = np.random.default_rng(2026)
PARTIAL = os.environ.get("PARTIAL") == "1"
TASKS = ["Walker2d-v5", "Swimmer-v5"]


def scores(tag, task, seeds):
    if not PARTIAL:
        return finals("results", tag, task, seeds, 1_000_000, strict=True)
    rows = [read_run(run_path("results", tag, task, s), 1_000_000) for s in seeds]
    return np.array([float(r[-1]["eval_mean"]) for r in rows if r is not None])


def hodges_lehmann(x, y, reps=5000):
    hl = lambda a, b: float(np.median(a[:, None] - b[None, :]))
    boots = [hl(rng.choice(x, len(x)), rng.choice(y, len(y))) for _ in range(reps)]
    return hl(x, y), np.percentile(boots, [2.5, 97.5]).tolist()


def contrast(x, y, nx, ny):
    est = iqm_interval({nx: x, ny: y}, reps=2000, random_state=RS)
    p, lo, hi = improvement_interval(x, y, reps=2000, random_state=RS)
    hl, hl_ci = hodges_lehmann(x, y)
    return dict(a=nx, b=ny, n=[len(x), len(y)], p_improve=p, ci=[lo, hi], settled=not (lo <= .5 <= hi),
                mw_p=float(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue),
                iqm={k: v[0] for k, v in est.items()}, iqm_ci={k: list(v[1:]) for k, v in est.items()},
                iqm_ratio=est[nx][0] / est[ny][0], hodges_lehmann=hl, hodges_lehmann_ci=hl_ci)


res = dict(contrasts={}, descriptive={})
for task in TASKS:
    S40 = {t: scores(t, task, range(40)) for t in ("ppo_sb3", "ppo_sbx")}
    S20 = {t: scores(t, task, range(20)) for t in ("ppo_sb3", "ppo_sbx", "ppo_sbx_ortho", "ppo_sb3_noortho")}
    res["contrasts"][f"{task} (1) sbx vs sb3, seeds 0-39"] = contrast(S40["ppo_sbx"], S40["ppo_sb3"], "ppo_sbx", "ppo_sb3")
    res["contrasts"][f"{task} (2) sbx ortho vs sbx"] = contrast(S20["ppo_sbx_ortho"], S20["ppo_sbx"], "ppo_sbx_ortho", "ppo_sbx")
    res["contrasts"][f"{task} (3) sb3 vs sb3 no ortho"] = contrast(S20["ppo_sb3"], S20["ppo_sb3_noortho"], "ppo_sb3", "ppo_sb3_noortho")
    res["descriptive"][f"{task} sbx ortho vs sb3"] = contrast(S20["ppo_sbx_ortho"], S20["ppo_sb3"], "ppo_sbx_ortho", "ppo_sb3")
    res["descriptive"][f"{task} sb3 no ortho vs sbx"] = contrast(S20["ppo_sb3_noortho"], S20["ppo_sbx"], "ppo_sb3_noortho", "ppo_sbx")
for k, h in zip(res["contrasts"], holm([c["mw_p"] for c in res["contrasts"].values()])):
    res["contrasts"][k]["mw_p_holm"] = h
    res["contrasts"][k]["settled_holm"] = bool(h < .05)
for k, c in {**res["contrasts"], **res["descriptive"]}.items():
    print(f"{k:42s} n {c['n']} P {c['p_improve']:.2f} [{c['ci'][0]:.2f}, {c['ci'][1]:.2f}] MW {c['mw_p']:.4f} "
          f"Holm {c.get('mw_p_holm', float('nan')):.4f} IQM ratio {c['iqm_ratio']:.2f} HL {c['hodges_lehmann']:.1f}")
if not PARTIAL:
    json.dump(res, open("analysis/c2.json", "w"), indent=1)
