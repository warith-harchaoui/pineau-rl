"""E6, as pre-registered: PPO-SB3 on Hopper-v5, library defaults against the published RL Zoo settings, 10 seeds each."""
import glob, csv, json
import numpy as np
from rliable import metrics
from rliable.library import get_interval_estimates
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from scipy import stats
def finals(tag, col='eval_mean'):
    out = []
    for f in sorted(glob.glob(f'results/{tag}/Hopper-v5/seed*.csv')):
        r = list(csv.DictReader(open(f)))
        if int(r[-1]['step']) == 1000000: out.append(float(r[-1][col]))
    return np.array(out)
d, z = finals('ppo_sb3'), finals('ppo_sb3_zoo')
print('n', len(d), len(z))
print('default', np.round(np.sort(d)), 'mean', d.mean().round(), 'sd', d.std(ddof=1).round())
print('zoo    ', np.round(np.sort(z)), 'mean', z.mean().round(), 'sd', z.std(ddof=1).round())
scores = {'default': d[:, None], 'zoo': z[:, None]}
iqm = lambda x: np.array([metrics.aggregate_iqm(x)])
pe, ci = get_interval_estimates(scores, iqm, reps=2000, random_state=RS)
print({k: (round(float(pe[k][0])), [round(float(ci[k][0][0])), round(float(ci[k][1][0]))]) for k in pe})
print('Welch', stats.ttest_ind(z, d, equal_var=False))
print('P(zoo>default)', np.mean([a > b for a in z for b in d]))
json.dump(dict(default=d.tolist(), zoo=z.tolist(), iqm={k: float(pe[k][0]) for k in pe}, ci={k: [float(ci[k][0][0]), float(ci[k][1][0])] for k in pe}), open('analysis/e6.json', 'w'), indent=1)
