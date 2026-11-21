"""B1, the inflation factor of the script's t (SIM_PROTOCOL.md, deviation 27, written before this computation).
With 5 seeds per group, a Welch test over the seeds has a standard error sigma sqrt(2/5); Henderson's script uses the
between-episode standard deviation S with n episodes, S sqrt(2/n). So t_script / t_seed = sqrt(n/5) / rho, with rho = S
/ sigma (b1_script.json: "eval_std_over_between_seed_sd"). Check on our curves: the random draws of b1_script.py
(generator seed 2018, 10,000 draws of 10 runs cut into 5 against 5), at the last evaluation point, the script's t (n = 10
and n = 5) against Welch's t on the seeds' eval_mean; the median of their ratio against sqrt(n/5)/rho and 1/rho, rho
measured in each draw (mean eval_std of the 10 runs over the pooled standard deviation of the two groups' eval_mean)
and over the 30 runs.
Run from sim/: env-an/bin/python analysis/b1_factor.py  -> analysis/b1_factor.json
"""
import json
import numpy as np
from scipy import stats
from pineau_rl.runs import read_run, run_path


def last(algo):
    rows = [read_run(run_path("results", algo, "HalfCheetah-v5", s))[-1] for s in range(30)]  # explicit seeds 0 to 29
    return np.array([float(r["eval_mean"]) for r in rows]), np.array([float(r["eval_std"]) for r in rows])


res = {}
for algo in ("ppo_sb3", "trpo"):
    M, S = last(algo)
    rho30 = float(S.mean() / M.std(ddof=1))
    res[algo] = dict(rho_30_runs=rho30)
    for n in (10, 5):
        rng = np.random.default_rng(2018)
        ratios, preds, rhos = [], [], []
        for _ in range(10000):
            idx = rng.permutation(rng.choice(30, 10, replace=False))
            a, b = idx[5:], idx[:5]
            t_script = stats.ttest_ind_from_stats(M[a].mean(), S[a].mean(), n, M[b].mean(), S[b].mean(), n,
                                                  equal_var=False).statistic
            t_seed = stats.ttest_ind(M[a], M[b], equal_var=False).statistic
            sigma = np.sqrt((M[a].var(ddof=1) + M[b].var(ddof=1)) / 2)
            rho = np.sqrt((S[a].mean() ** 2 + S[b].mean() ** 2) / 2) / sigma
            ratios.append(t_script / t_seed); rhos.append(rho); preds.append(np.sqrt(n / 5) / rho)
        ratios, preds, rhos = map(np.array, (ratios, preds, rhos))
        res[algo][f"n{n}"] = dict(median_ratio=float(np.median(ratios)), median_predicted_sqrt_n5_over_rho=float(np.median(preds)),
                                  median_1_over_rho=float(np.median(1 / rhos)), max_abs_gap_ratio_vs_prediction=float(
                                      np.max(np.abs(ratios / preds - 1))),
                                  predicted_from_rho_30=float(np.sqrt(n / 5) / rho30), one_over_rho_30=1 / rho30)
        print(algo, n, {k: round(v, 3) for k, v in res[algo][f"n{n}"].items()})
json.dump(res, open("analysis/b1_factor.json", "w"), indent=1)
