"""E1, as pre-registered in SIM_PROTOCOL.md: same code, 30 seeds of PPO-SB3 on HalfCheetah-v5."""
import json
import numpy as np
from scipy import stats
from pineau_rl.runs import finals
F = finals('results', 'ppo_sb3', 'HalfCheetah-v5', sorted(range(30), key=str), 1_000_000, strict=True)  # explicit seeds 0 to 29, string order of the files; every run at 1M steps
assert len(F) == 30
rng = np.random.default_rng(2018)
res = dict(n=30, mean=F.mean(), sd=F.std(ddof=1), min=F.min(), max=F.max(), median=np.median(F), cv=F.std(ddof=1)/F.mean(), shapiro_p=stats.shapiro(F).pvalue)
def draws(k, N=10000):
    sig, gaps = 0, []
    for _ in range(N):
        idx = rng.permutation(30)
        a, b = F[idx[:k]], F[idx[k:2*k]]
        sig += stats.ttest_ind(a, b, equal_var=False).pvalue < .05
        gaps.append(abs(a.mean()-b.mean())/min(a.mean(), b.mean()))
    return sig/N, np.median(gaps), np.percentile(gaps, 95)
for k in (3, 5, 10):
    p, med, p95 = draws(k); res[f'random_{k}v{k}'] = dict(false_positive=p, median_gap=med, p95_gap=p95)
# the "2018 figure" cut: draw 10 seeds, sort them, compare the 5 best with the 5 worst
sig, gaps, ps = 0, [], []
for _ in range(10000):
    x = np.sort(rng.choice(F, 10, replace=False))
    t = stats.ttest_ind(x[5:], x[:5], equal_var=False); sig += t.pvalue < .05; ps.append(t.pvalue); gaps.append(x[5:].mean()/x[:5].mean()-1)
res['extreme_5v5_of_10'] = dict(false_positive=sig/10000, median_gap=np.median(gaps), median_p=np.median(ps))
# top-3-of-10
tops, means = [], []
for _ in range(10000):
    x = np.sort(rng.choice(F, 10, replace=False)); tops.append(x[-3:].mean()); means.append(x.mean())
res['top3_of_10'] = dict(mean_all=np.mean(means), mean_top3=np.mean(tops), inflation=np.mean(tops)/np.mean(means)-1)
res['seeds_sorted'] = sorted(map(float, F))
json.dump(res, open('analysis/e1.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != 'seeds_sorted'}, indent=1, default=float))
