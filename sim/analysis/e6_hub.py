"""E6, the RL Zoo's own published agent (SIM_PROTOCOL.md, deviation 33 (b), written before this download and evaluation).
`fetch`: downloads the files of the Hugging Face repository sb3/ppo-Hopper-v3 into zoo_hub/ (one host, one session,
requests spaced at random by 0.3 to 1.5 s, stop at the first refusal). `eval`: inspects every pickle before loading it
(only NumPy, collections, Gym and Stable-Baselines3 objects allowed; the serialised entries of the model's data are
not unpickled but replaced by our own objects, as rl_zoo3 does), then evaluates the policy with OUR protocol on
Hopper-v4 (same observation space as v3): deterministic, frozen observation normalisation, evaluation seeds 10000 to
10009 (our 10-episode score) and 10000 to 10099 (100 episodes), recording info["x_velocity"]. Compared with the score
of the model card and with the hyperparameters of our recipe (run.py's ZOO_PPO_HOPPER).
Run from sim/ with env-zoo: env-zoo/bin/python analysis/e6_hub.py fetch, then eval  -> analysis/e6_hub.json
"""
import io, json, os, pickle, pickletools, random, sys, time, zipfile
import numpy as np

REPO, DIR, TASK = "sb3/ppo-Hopper-v3", "zoo_hub", "Hopper-v4"
# run.py's ZOO_PPO_HOPPER (the recipe of E6), copied: importing run.py would start a training
ZOO_PPO_HOPPER = dict(batch_size=32, n_steps=512, gamma=0.999, learning_rate=9.80828e-05, ent_coef=0.00229519,
                      clip_range=0.2, n_epochs=5, gae_lambda=0.99, max_grad_norm=0.7, vf_coef=0.835671)
ALLOWED = ("numpy", "collections", "builtins", "gym.", "gymnasium.", "stable_baselines3.", "copyreg", "_codecs",
           "torch._utils._rebuild_tensor", "torch.FloatStorage", "torch.LongStorage")  # tensors in the .pth files


def fetch():
    from huggingface_hub import HfApi, hf_hub_download
    os.makedirs(DIR, exist_ok=True)
    api = HfApi(user_agent="pineau-rl research reproduction (github.com/warith-harchaoui/pineau-rl)")
    files = api.list_repo_files(REPO)
    print("files:", files)
    keep = [f for f in files if f.endswith((".zip", ".pkl", ".yml", ".json", ".md")) and "/" not in f]
    for f in keep:
        time.sleep(random.uniform(0.3, 1.5))
        hf_hub_download(REPO, f, local_dir=DIR, user_agent="pineau-rl research reproduction")  # raises on refusal: stop
        print("got", f)
    json.dump(dict(repo=REPO, files=files, downloaded=keep, revision=api.model_info(REPO).sha),
              open(f"{DIR}/fetch.json", "w"), indent=1)


def globals_of(raw):
    """Every module.name a pickle would import."""
    out, strings = set(), []
    for op, arg, _ in pickletools.genops(raw):
        if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE", "BINSTRING", "SHORT_BINSTRING"):
            strings.append(arg)
        if op.name == "GLOBAL":
            out.add(arg.replace(" ", "."))
        if op.name == "STACK_GLOBAL":
            out.add(f"{strings[-2]}.{strings[-1]}")
    return sorted(out)


def check(raw, what):
    g = globals_of(raw)
    bad = [x for x in g if not x.startswith(ALLOWED)]
    print(what, "imports:", g)
    assert not bad, f"{what}: refused imports {bad}"
    return g


def evaluate():
    import gymnasium as gym
    from torch import nn
    from stable_baselines3 import PPO
    from stable_baselines3.common.running_mean_std import RunningMeanStd
    zips = ["ppo-Hopper-v3.zip"]  # train_eval_metrics.zip holds the training logs
    assert len(zips) == 1, zips
    z = zipfile.ZipFile(f"{DIR}/{zips[0]}")
    data = json.loads(z.read("data"))
    serialised = sorted(k for k, v in data.items() if isinstance(v, dict) and ":serialized:" in v)
    readable = {k: v for k, v in data.items() if k not in serialised}
    for k in z.namelist():  # torch files are zip archives holding a pickle: inspect those too
        if k.endswith(".pth"):
            inner = zipfile.ZipFile(io.BytesIO(z.read(k)))
            for n in inner.namelist():
                if n.endswith("data.pkl"):
                    check(inner.read(n), f"{k}/{n}")
    raw = open(f"{DIR}/vec_normalize.pkl", "rb").read()
    vn_imports = check(raw, "vec_normalize.pkl")

    class Restricted(pickle.Unpickler):  # gym 0.21 objects are not installed: stand-ins that keep only their state
        def find_class(self, module, name):
            if not module.startswith(ALLOWED):
                raise pickle.UnpicklingError(f"{module}.{name}")
            if module.startswith("gym."):
                return type(name, (), {"__setstate__": lambda self, s: self.__dict__.update(s if isinstance(s, dict) else {})})
            return super().find_class(module, name)
    vn = Restricted(io.BytesIO(raw)).load()
    obs_rms, clip_obs, eps = vn.obs_rms, vn.clip_obs, vn.epsilon
    assert isinstance(obs_rms, RunningMeanStd)
    env0 = gym.make(TASK)
    from stable_baselines3.common.policies import ActorCriticPolicy
    custom = {k: None for k in serialised}
    custom["policy_class"] = ActorCriticPolicy
    custom.update(observation_space=env0.observation_space, action_space=env0.action_space,
                  learning_rate=0.0, lr_schedule=lambda _: 0.0, clip_range=lambda _: 0.0,
                  policy_kwargs=dict(log_std_init=-2, ortho_init=False, activation_fn=nn.ReLU,  # its config.yml
                                     net_arch=dict(pi=[256, 256], vf=[256, 256])))
    model = PPO.load(f"{DIR}/{zips[0]}", custom_objects=custom, device="cpu")
    norm = lambda o: np.clip((o - obs_rms.mean) / np.sqrt(obs_rms.var + eps), -clip_obs, clip_obs)

    def episode(seed):
        env = gym.make(TASK)
        obs, _ = env.reset(seed=seed)
        x0, ret, n, vel, done = float(env.unwrapped.data.qpos[0]), 0.0, 0, [], False
        while not done:
            act, _ = model.predict(norm(obs).astype(np.float32), deterministic=True)
            obs, r, term, trunc, info = env.step(act)
            ret += r; n += 1; vel.append(float(info["x_velocity"])); done = term or trunc
        return dict(ret=float(ret), length=n, mean_x_velocity=float(np.mean(vel)),
                    displacement=float(info["x_position"] - x0))
    eps100 = [episode(10_000 + i) for i in range(100)]
    r = np.array([e["ret"] for e in eps100])
    card = open(f"{DIR}/README.md").read() if os.path.exists(f"{DIR}/README.md") else ""
    results = json.load(open(f"{DIR}/results.json")) if os.path.exists(f"{DIR}/results.json") else None
    keys = ["batch_size", "n_steps", "gamma", "learning_rate", "ent_coef", "clip_range", "n_epochs", "gae_lambda",
            "max_grad_norm", "vf_coef"]
    hub_hp = {k: readable.get(k) for k in keys}
    res = dict(repo=REPO, fetch=json.load(open(f"{DIR}/fetch.json")), serialised_entries_not_loaded=serialised,
               vec_normalize_imports=vn_imports,
               system_info_of_model=z.read("system_info.txt").decode() if "system_info.txt" in z.namelist() else None,
               model_card_results=results, model_card_mean_reward_line=[l for l in card.splitlines() if "mean_reward" in l or "value:" in l][:4],
               hyperparameters_hub=hub_hp, policy_kwargs_hub=readable.get("policy_kwargs"),
               hyperparameters_ours={k: ZOO_PPO_HOPPER.get(k) for k in keys},
               score_10_episodes=float(r[:10].mean()), score_100_episodes=float(r.mean()), sd_100=float(r.std()),
               share_full_length_100=float(np.mean([e["length"] == 1000 for e in eps100])),
               mean_x_velocity_100=float(np.mean([e["mean_x_velocity"] for e in eps100])), episodes=eps100)
    json.dump(res, open("analysis/e6_hub.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "episodes"}, indent=1, default=str))


{"fetch": fetch, "eval": evaluate}[sys.argv[1]]()
