"""B1, Henderson's own script (SIM_PROTOCOL.md, Écart 6, written before this computation).

`from_same_dist.py` (Breakend/ReproducibilityInContinuousPolicyGradientMethods, 17 June 2017) averages the
progress files of a group's seeds column by column (`ave_results.py`), then, at each iteration, runs a Welch test
from the mean return, the standard deviation of returns between episodes of that iteration and the number of
episodes (`scipy.stats.ttest_ind_from_stats`), and reports the mean t and the mean p. The spread between seeds
never enters the test. We apply this computation to our evaluations: mean of the 5 seeds' `eval_mean` and
`eval_std`, n = 10 evaluation episodes, and n = 5 (their trajectories per iteration) as a sensitivity check.
Same draws as b1_trpo.py: generator seed 2018, 10,000 draws of 10 runs cut into 5 against 5, at random, then sorted.
Run from sim/: env-an/bin/python analysis/b1_script.py  -> analysis/b1_script.json
"""
import csv, glob, json
import numpy as np
from scipy import stats

HENDERSON_T = 9.0916


def curves(algo):
    files = sorted(glob.glob(f"results/{algo}/HalfCheetah-v5/seed*.csv"),
                   key=lambda f: int(f.split("seed")[-1].split(".")[0]))
    rows = [list(csv.DictReader(open(f))) for f in files]
    M = np.array([[float(r["eval_mean"]) for r in rs] for rs in rows])
    S = np.array([[float(r["eval_std"]) for r in rs] for rs in rows])
    assert M.shape == S.shape == (30, 20), (algo, M.shape)
    return M, S


def script(M, S, a, b, n):
    """from_same_dist.py on the averaged progress of groups a and b."""
    t, p = stats.ttest_ind_from_stats(M[a].mean(0), S[a].mean(0), n, M[b].mean(0), S[b].mean(0), n, equal_var=False)
    return t.mean(), p.mean()


def run(M, S, sort, rng, n, N=10000):
    ts, ps = [], []
    for _ in range(N):
        idx = rng.choice(30, 10, replace=False)
        idx = idx[np.argsort(M[idx, -1])] if sort else rng.permutation(idx)
        t, p = script(M, S, idx[5:], idx[:5], n)
        ts.append(abs(t)); ps.append(p)
    ts, ps = np.array(ts), np.array(ps)
    return dict(false_positive=float((ps < .05).mean()), abs_t_median=float(np.median(ts)),
                abs_t_p95=float(np.percentile(ts, 95)), share_abs_t_ge_henderson=float((ts >= HENDERSON_T).mean()),
                p_median=float(np.median(ps)))


res = {}
for algo in ("ppo_sb3", "trpo"):
    M, S = curves(algo)
    res[algo] = dict(eval_std_over_between_seed_sd=float(S[:, -1].mean() / M[:, -1].std(ddof=1)))
    for n in (10, 5):
        rng = np.random.default_rng(2018)
        res[algo][f"n{n}"] = dict(random_5v5=run(M, S, False, rng, n), sorted_5v5=run(M, S, True, rng, n))
json.dump(res, open("analysis/b1_script.json", "w"), indent=1)
print(json.dumps(res, indent=1))
