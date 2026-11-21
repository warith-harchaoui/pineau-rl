"""E6, the published recipe replayed (SIM_PROTOCOL.md, deviation 33 (a), written before these evaluations).
The 10 official RL Zoo policies (zoo_official/), our corrected-Zoo policies and our default policies on Hopper-v4,
replayed with OUR protocol (run.py's evaluate: 10 deterministic episodes, evaluation seeds 10000 to 10009, frozen
observation normalisation), recording at each step info["x_velocity"], info["x_position"] and the action cost.
Control: the mean returns must equal analysis/e6_official_eval.json (official) and the final eval_mean of
results/<tag>/Hopper-v4/seed<i>.csv (ours), exactly. Then one episode (evaluation seed 10000) of the official policy
and of our default policy with the median score, rendered to MP4 (one frame in four), under results/e6_video/.
Hopper reward per step: x_velocity + 1 (healthy) - 0.001 |a|^2, so a return of about 1 per step is standing still.
Deviation 33 (c): once the 10 runs of ppo_sb3_zoog99 exist, they are replayed the same way (group "zoog99").
Run from sim/ with env-zoo: env-zoo/bin/python analysis/e6_enjoy.py  -> analysis/e6_enjoy.json, results/e6_video/
"""
import csv, json, os
import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

TASK, EPISODES, SEEDS = "Hopper-v4", 10, range(10)
TAGS = {"zoofix": "ppo_sb3_zoofix", "default": "ppo_sb3", "zoog99": "ppo_sb3_zoog99"}
# deviation 33 (c): the gamma = 0.99 recipe joins once its 10 policies exist (rerun this script then; the rest is identical)
GROUPS = ["official", "zoofix", "default"] + (["zoog99"] if all(os.path.exists(f"models/ppo_sb3_zoog99/{TASK}/seed{s}.zip")
                                                                for s in SEEDS) else [])


def load(group, seed):
    """(model, observation normaliser or None) as run.py / e6_official.py use them."""
    if group == "official":
        d = f"zoo_official/seed{seed}/ppo/Hopper-v4_1"
        zip_, vn = f"{d}/Hopper-v4.zip", f"{d}/Hopper-v4/vecnormalize.pkl"
    else:
        tag = TAGS[group]
        zip_, vn = f"models/{tag}/{TASK}/seed{seed}.zip", f"models/{tag}/{TASK}/seed{seed}.vecnorm.pkl"
    model = PPO.load(zip_, device="cpu")
    if not os.path.exists(vn):
        return model, None
    norm = VecNormalize.load(vn, DummyVecEnv([lambda: gym.make(TASK)]))
    norm.training, norm.norm_reward = False, False
    return model, norm


def episode(model, norm, seed, frames=None):
    env = gym.make(TASK, render_mode="rgb_array", width=320, height=240) if frames is not None else gym.make(TASK)
    obs, _ = env.reset(seed=seed)
    x0 = float(env.unwrapped.data.qpos[0])
    ret, vel, ctrl, n, done, term = 0.0, [], [], 0, False, False
    while not done:
        if frames is not None and n % 4 == 0:
            frames.append(env.render())
        act, _ = model.predict(norm.normalize_obs(obs) if norm else obs, deterministic=True)
        obs, r, term, trunc, info = env.step(act)
        ret += r; n += 1
        vel.append(float(info["x_velocity"]))
        ctrl.append(float(1e-3 * np.square(np.clip(act, -1, 1)).sum()))
        done = term or trunc
    env.close()
    return dict(ret=float(ret), length=n, terminated=bool(term), mean_x_velocity=float(np.mean(vel)),
                displacement=float(info["x_position"] - x0), mean_ctrl_cost=float(np.mean(ctrl)),
                return_per_step=float(ret / n))


def reference(group, seed):
    if group == "official":
        return json.load(open("analysis/e6_official_eval.json"))[str(seed)]
    tag = TAGS[group]
    return float(list(csv.DictReader(open(f"results/{tag}/{TASK}/seed{seed}.csv")))[-1]["eval_mean"])


res = dict(task=TASK, groups={})
for group in GROUPS:
    runs = {}
    for s in SEEDS:
        model, norm = load(group, s)
        eps = [episode(model, norm, 10_000 + i) for i in range(EPISODES)]
        mean = float(np.mean([e["ret"] for e in eps]))
        runs[s] = dict(mean_return=mean, control_equal=mean == reference(group, s),
                       mean_x_velocity=float(np.mean([e["mean_x_velocity"] for e in eps])),
                       mean_displacement=float(np.mean([e["displacement"] for e in eps])),
                       share_full_length=float(np.mean([e["length"] == 1000 for e in eps])), episodes=eps)
        print(group, s, f"return {mean:.1f} control {runs[s]['control_equal']} "
                        f"speed {runs[s]['mean_x_velocity']:.3f} m/s full {runs[s]['share_full_length']:.0%}")
    v = np.array([r["mean_x_velocity"] for r in runs.values()])
    res["groups"][group] = dict(runs=runs, all_controls_equal=all(r["control_equal"] for r in runs.values()),
                                median_speed=float(np.median(v)), min_speed=float(v.min()), max_speed=float(v.max()))

# videos: the policy with the median score (lower median) of the official runs and of our default runs
import imageio
os.makedirs("results/e6_video", exist_ok=True)
res["videos"] = {}
for group in ("official", "default"):
    runs = res["groups"][group]["runs"]
    s = sorted(runs, key=lambda k: runs[k]["mean_return"])[len(runs) // 2 - 1]
    model, norm = load(group, s)
    frames = []
    e = episode(model, norm, 10_000, frames)
    path = f"results/e6_video/{group}_seed{s}.mp4"
    imageio.mimsave(path, frames, fps=31, macro_block_size=8)  # Hopper dt = 0.008 s: one frame in four is about real time
    res["videos"][group] = dict(seed=s, file=path, episode=e)
    print("video", path, e)
json.dump(res, open("analysis/e6_enjoy.json", "w"), indent=1)
