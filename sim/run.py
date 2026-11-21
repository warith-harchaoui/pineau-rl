"""One training run: algorithm x task x seed, held-out evaluation every 50k steps.

Usage: python run.py ALGO TASK SEED STEPS [--zoo]
ALGO in {ppo_sb3, ppo_sbx, sac, crossq, td3, trpo} or a variant name of VARIANTS; writes
results/<ALGO>/<TASK>/seed<SEED>.csv and the final policy to models/<ALGO>/<TASK>/seed<SEED>.zip.
Evaluation seeds (10000+i) never train.
"""
import os, sys, csv, time, json
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import gymnasium as gym

ALGO, TASK, SEED, STEPS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
# Variants (SIM_PROTOCOL.md, deviations 32 to 34): a name for the results and models, the program it runs, and the only
# settings it changes. sac_rerun and crossq_rerun change nothing (determinism check, deviation 32).
VARIANTS = {"sac_rerun": ("sac", {}), "crossq_rerun": ("crossq", {}),
            "ppo_sbx_ortho": ("ppo_sbx", dict(policy_kwargs=dict(ortho_init=True))),     # deviation 34 (b)
            "ppo_sb3_noortho": ("ppo_sb3", dict(policy_kwargs=dict(ortho_init=False))),  # deviation 34 (b)
            "ppo_sb3_zoog99": ("ppo_sb3", dict(gamma=0.99))}  # deviation 33 (c): the corrected Zoo recipe, gamma 0.99
VARIANT = ALGO if ALGO in VARIANTS else None
ALGO, EXTRA = VARIANTS[ALGO] if VARIANT else (ALGO, {})
ZOOFIX = "--zoofix" in sys.argv or VARIANT == "ppo_sb3_zoog99"
ZOO = "--zoo" in sys.argv or ZOOFIX
TAG = VARIANT or ALGO + ("_zoofix" if ZOOFIX else "_zoo" if ZOO else "")
EVAL_EVERY, EVAL_EPISODES = int(os.environ.get("EVAL_EVERY", 50_000)), 10

# Published RL Baselines3 Zoo hyperparameters for PPO on Hopper-v4 (hyperparams/ppo.yml), used for E6.
ZOO_PPO_HOPPER = dict(batch_size=32, n_steps=512, gamma=0.999, learning_rate=9.80828e-05,
                      ent_coef=0.00229519, clip_range=0.2, n_epochs=5, gae_lambda=0.99,
                      max_grad_norm=0.7, vf_coef=0.835671,
                      policy_kwargs=dict(log_std_init=-2, ortho_init=False, activation_fn=None,
                                         net_arch=dict(pi=[256, 256], vf=[256, 256])))


def make_model():
    if ALGO == "ppo_sb3":
        import torch
        torch.set_num_threads(1)
        from stable_baselines3 import PPO
        kw, env = {}, TASK
        if ZOO:  # RL Zoo also sets normalize: true (VecNormalize on observations and rewards)
            from stable_baselines3.common.env_util import make_vec_env
            from stable_baselines3.common.vec_env import VecNormalize
            kw = dict(ZOO_PPO_HOPPER, **EXTRA)
            kw["policy_kwargs"] = dict(kw["policy_kwargs"], activation_fn=torch.nn.ReLU)
            env = VecNormalize(make_vec_env(TASK, n_envs=1, seed=SEED), gamma=kw["gamma"] if ZOOFIX else 0.99)
        else:
            kw = dict(EXTRA)
        return PPO("MlpPolicy", env, seed=SEED, verbose=0, device="cpu", **kw)
    if ALGO == "trpo":  # experiment B1: Henderson et al.'s figure 5 algorithm, library defaults, no tuning
        import torch
        torch.set_num_threads(1)
        from sb3_contrib import TRPO
        return TRPO("MlpPolicy", TASK, seed=SEED, verbose=0, device="cpu")
    from sbx import PPO, SAC, CrossQ, TD3
    cls = dict(ppo_sbx=PPO, sac=SAC, crossq=CrossQ, td3=TD3)[ALGO]
    return cls("MlpPolicy", TASK, seed=SEED, verbose=0, **EXTRA)


def evaluate(model, perturbed=False):
    rets = []
    for i in range(EVAL_EPISODES):
        env = gym.make(TASK)
        if perturbed:
            m = env.unwrapped.model
            m.body_mass[:] = m.body_mass * 1.2
            m.geom_friction[:, 0] = m.geom_friction[:, 0] * 0.8
        obs, _ = env.reset(seed=10_000 + i)
        done, ret = False, 0.0
        while not done:
            o = model.get_vec_normalize_env().normalize_obs(obs) if model.get_vec_normalize_env() else obs
            act, _ = model.predict(o, deterministic=True)
            obs, r, term, trunc, _ = env.step(act)
            ret += r
            done = term or trunc
        rets.append(ret)
        env.close()
    return float(np.mean(rets)), float(np.std(rets))


out = f"results/{TAG}/{TASK}/seed{SEED}.csv"
os.makedirs(os.path.dirname(out), exist_ok=True)
model = make_model()
rows, t0, done_steps = [], time.time(), 0
while done_steps < STEPS:
    n = min(EVAL_EVERY, STEPS - done_steps)
    model.learn(n, reset_num_timesteps=False)
    done_steps += n
    m, s = evaluate(model)
    rows.append(dict(step=done_steps, eval_mean=m, eval_std=s, perturbed_mean="", wall=round(time.time() - t0, 1)))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
pm, _ = evaluate(model, perturbed=True)
rows[-1]["perturbed_mean"] = pm
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
os.makedirs(f"models/{TAG}/{TASK}", exist_ok=True)
if model.get_vec_normalize_env():
    model.get_vec_normalize_env().save(f"models/{TAG}/{TASK}/seed{SEED}.vecnorm.pkl")
model.save(f"models/{TAG}/{TASK}/seed{SEED}.zip")
print(json.dumps(dict(algo=TAG, task=TASK, seed=SEED, final=rows[-1]["eval_mean"], perturbed=pm, wall=rows[-1]["wall"])))
