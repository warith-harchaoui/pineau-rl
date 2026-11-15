"""E7 dose-response (SIM_PROTOCOL.md, deviation 12): re-evaluates one saved final policy under several physics changes,
mass and friction separately, with the same 10 held-out evaluation seeds (10000+i) as run.py. No training.

Usage: python dose.py ALGO TASK SEED  -> results/dose/<ALGO>/<TASK>/seed<SEED>.json
"""
import os, sys, json
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import gymnasium as gym

ALGO, TASK, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3])
MASS = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
FRICTION = [0.6, 0.7, 0.8, 0.9, 1.1, 1.2]
EVAL_EPISODES = 10  # as run.py
OUT = f"results/dose/{ALGO}/{TASK}/seed{SEED}.json"


def load():
    path = f"models/{ALGO}/{TASK}/seed{SEED}.zip"
    if ALGO == "ppo_sb3":
        import torch
        torch.set_num_threads(1)
        from stable_baselines3 import PPO
        return PPO.load(path, device="cpu")
    from sbx import PPO, SAC, CrossQ
    return dict(ppo_sbx=PPO, sac=SAC, crossq=CrossQ)[ALGO].load(path)


def evaluate(model, mass=1.0, friction=1.0):
    rets = []
    for i in range(EVAL_EPISODES):
        env = gym.make(TASK)
        m = env.unwrapped.model
        m.body_mass[:] = m.body_mass * mass
        m.geom_friction[:, 0] = m.geom_friction[:, 0] * friction
        obs, _ = env.reset(seed=10_000 + i)
        done, ret = False, 0.0
        while not done:
            act, _ = model.predict(obs, deterministic=True)
            obs, r, term, trunc, _ = env.step(act)
            ret += r
            done = term or trunc
        rets.append(ret)
        env.close()
    return float(np.mean(rets))


model = load()
res = dict(algo=ALGO, task=TASK, seed=SEED,
           mass={str(k): evaluate(model, mass=k) for k in MASS},
           friction={str(k): evaluate(model, friction=k) for k in FRICTION})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(dict(algo=ALGO, task=TASK, seed=SEED, base=res["mass"]["1.0"])))
