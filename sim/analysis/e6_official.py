"""E6 (SIM_PROTOCOL.md, Écart 5): the official RL Zoo policies, evaluated with OUR protocol (run.py's evaluate):
10 deterministic episodes, evaluation random seeds 10000 to 10009, frozen observation normalisation.
Then official against our zoofix v4 and our default v4: IQM with a 95% bootstrap interval, probability of
improvement with a bootstrap interval, Welch p with Holm over the two comparisons.
Run from sim/ with env-zoo for the evaluation step: env-zoo/bin/python analysis/e6_official.py eval
and env-an for the statistics: env-an/bin/python analysis/e6_official.py stats  -> analysis/e6_official.json
"""
import csv, glob, json, sys
import numpy as np


def evaluate_official():
    import gymnasium as gym
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    out = {}
    for seed in range(10):
        d = f"zoo_official/seed{seed}/ppo/Hopper-v4_1"
        model = PPO.load(f"{d}/Hopper-v4.zip", device="cpu")
        vn = VecNormalize.load(f"{d}/Hopper-v4/vecnormalize.pkl", DummyVecEnv([lambda: gym.make("Hopper-v4")]))
        vn.training, vn.norm_reward = False, False
        rets = []
        for i in range(10):
            env = gym.make("Hopper-v4")
            obs, _ = env.reset(seed=10_000 + i)
            done, ret = False, 0.0
            while not done:
                act, _ = model.predict(vn.normalize_obs(obs), deterministic=True)
                obs, r, term, trunc, _ = env.step(act)
                ret += r
                done = term or trunc
            rets.append(ret)
        out[seed] = float(np.mean(rets))
        print(seed, out[seed])
    json.dump(out, open("analysis/e6_official_eval.json", "w"), indent=1)


def stats_official():
    from pineau_rl.bootstrap import iqm_interval, probability_of_improvement_bootstrap
    np.random.seed(2026)  # rliable draws from the global generator and ignores random_state (SIM_PROTOCOL.md, deviation 13)
    RS = np.random.RandomState(2026)
    from scipy import stats
    from pineau_rl.stats import holm
    off = np.array(list(json.load(open("analysis/e6_official_eval.json")).values()))
    finals = lambda tag: np.array([float(list(csv.DictReader(open(f)))[-1]["eval_mean"])
                                   for f in sorted(glob.glob(f"results/{tag}/Hopper-v4/seed*.csv"))])
    G = {"official v4": off, "zoofix v4": finals("ppo_sb3_zoofix"), "default v4": finals("ppo_sb3")}
    assert all(len(v) == 10 for v in G.values()), {k: len(v) for k, v in G.items()}
    est = iqm_interval(G, reps=5000, random_state=RS)
    rng = np.random.default_rng(2018)
    comps = []
    for a, b in (("official v4", "zoofix v4"), ("official v4", "default v4")):
        x, y = G[a], G[b]
        p, pci = probability_of_improvement_bootstrap(x, y, rng, reps=5000)  # 10 runs on each side
        comps.append(dict(a=a, b=b, p_improve=p, p_improve_ci=pci,
                          welch_p=float(stats.ttest_ind(x, y, equal_var=False).pvalue)))
    for c, h in zip(comps, holm([c["welch_p"] for c in comps])):
        c["welch_p_holm"] = float(h)
    res = dict(groups={k: dict(runs=v.tolist(), iqm=est[k][0], iqm_ci=list(est[k][1:]))
                       for k, v in G.items()}, comparisons=comps)
    json.dump(res, open("analysis/e6_official.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


{"eval": evaluate_official, "stats": stats_official}[sys.argv[1]]()
