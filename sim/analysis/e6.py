"""E6, as pre-registered: PPO-SB3 on Hopper-v5, library defaults against the published RL Zoo settings, 10 seeds each."""
import json
import numpy as np
from pineau_rl.bootstrap import iqm_interval, improvement_interval
np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
RS = np.random.RandomState(2026)
from scipy import stats
from pineau_rl.runs import finals
d, z = (finals('results', tag, 'Hopper-v5', range(10), 1_000_000, strict=True) for tag in ('ppo_sb3', 'ppo_sb3_zoo'))  # explicit seeds 0 to 9, every run at 1M steps
print('n', len(d), len(z))
assert len(d) == len(z) == 10, (len(d), len(z))
print('default', np.round(np.sort(d)), 'mean', d.mean().round(), 'sd', d.std(ddof=1).round())
print('zoo    ', np.round(np.sort(z)), 'mean', z.mean().round(), 'sd', z.std(ddof=1).round())
est = iqm_interval({'default': d, 'zoo': z}, reps=2000, random_state=RS)
print({k: (round(v[0]), [round(v[1]), round(v[2])]) for k, v in est.items()})
print('Welch', stats.ttest_ind(z, d, equal_var=False))
print('P(zoo>default)', np.mean([a > b for a in z for b in d]))
json.dump(dict(default=d.tolist(), zoo=z.tolist(), iqm={k: v[0] for k, v in est.items()}, ci={k: list(v[1:]) for k, v in est.items()}), open('analysis/e6.json', 'w'), indent=1)
