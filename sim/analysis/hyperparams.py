"""The hyperparameters actually used (SIM_PROTOCOL.md, deviation 28; a record, no statistics).
Builds each program on Hopper-v5 exactly as run.py does (library defaults, seed 0; E6's recipe on Hopper-v4), reads the
attributes of the algorithm, of the policy and of the optimiser, and compares them with the parameters stored in one
saved model per program (models/<algo>/<task>/seed0.zip; CrossQ's models were moved to /Volumes/orange-dev).
Run from sim/ with the TRAINING environment: env/bin/python analysis/hyperparams.py  -> analysis/hyperparams.json
(make hyperparams; not in make verify, which lacks that environment).
"""
import inspect, json, os, sys, zipfile
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")
import numpy as np
import torch
torch.set_num_threads(1)

ALGO_KEYS = ["learning_rate", "n_steps", "batch_size", "n_epochs", "gamma", "gae_lambda", "clip_range", "clip_range_vf",
             "normalize_advantage", "ent_coef", "vf_coef", "max_grad_norm", "target_kl", "use_sde", "buffer_size",
             "learning_starts", "tau", "train_freq", "gradient_steps", "policy_delay", "target_entropy",
             "target_update_interval", "cg_max_steps", "cg_damping", "line_search_shrinking_factor",
             "line_search_max_iter", "n_critic_updates", "qf_learning_rate", "n_envs"]
POLICY_KEYS = ["net_arch", "activation_fn", "ortho_init", "log_std_init", "share_features_extractor", "use_expln",
               "squash_output", "n_critics", "layer_norm", "dropout_rate", "batch_norm", "batch_norm_momentum",
               "renorm_warmup_steps", "batch_norm_actor", "optimizer_class", "optimizer_kwargs"]


def plain(v):
    if isinstance(v, (bool, int, float, str)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, np.generic):
        return v.item()
    if callable(v) and getattr(v, "__name__", "") in ("<lambda>", "func", "constant_fn"):
        try:
            return plain(v(1.0))  # a schedule: its value at the start
        except Exception:
            pass
    return getattr(v, "__qualname__", None) or getattr(v, "__name__", None) or repr(v)


def record(model):
    out = {k: plain(getattr(model, k)) for k in ALGO_KEYS if hasattr(model, k)}
    out["ent_coef_init"] = plain(getattr(model, "ent_coef_init", None)) if hasattr(model, "ent_coef_init") else None
    pol = model.policy
    out["policy_class"] = type(pol).__qualname__
    out["policy"] = {k: plain(getattr(pol, k)) for k in POLICY_KEYS if hasattr(pol, k)}
    for sub in ("actor", "qf", "critic"):  # sbx: flax modules carry the network settings
        m = getattr(pol, sub, None)
        if m is not None and hasattr(m, "__dataclass_fields__"):
            out["policy"][sub] = {f: plain(getattr(m, f)) for f in m.__dataclass_fields__ if f not in ("parent", "name")}
    if hasattr(pol, "optimizer") and isinstance(pol.optimizer, torch.optim.Optimizer):
        g = pol.optimizer.param_groups[0]
        out["optimizer"] = dict(cls=type(pol.optimizer).__name__, betas=list(g.get("betas", [])), eps=g.get("eps"))
    return out


def saved(algo, task, seed=0):
    for root in ("models", "/Volumes/orange-dev/pineau-rl-models-crossq"):
        for f in (f"{root}/{algo}/{task}/seed{seed}.zip", f"{root}/{task}/seed{seed}.zip"):
            if os.path.exists(f):
                d = json.loads(zipfile.ZipFile(f).read("data"))
                return f, {k: (v if not (isinstance(v, dict) and ":serialized:" in v) else
                               {kk: vv for kk, vv in v.items() if kk != ":serialized:"}) for k, v in d.items()
                           if k in ALGO_KEYS + ["policy_kwargs", "num_timesteps"]}
    return None, None


res = dict(task="Hopper-v5", programs={})
from stable_baselines3 import PPO as PPO_SB3
from sb3_contrib import TRPO
from sbx import PPO as PPO_SBX, SAC, CrossQ
build = {"ppo_sb3": lambda: PPO_SB3("MlpPolicy", "Hopper-v5", seed=0, verbose=0, device="cpu"),
         "ppo_sbx": lambda: PPO_SBX("MlpPolicy", "Hopper-v5", seed=0, verbose=0),
         "sac": lambda: SAC("MlpPolicy", "Hopper-v5", seed=0, verbose=0),
         "crossq": lambda: CrossQ("MlpPolicy", "Hopper-v5", seed=0, verbose=0),
         "trpo": lambda: TRPO("MlpPolicy", "HalfCheetah-v5", seed=0, verbose=0, device="cpu")}
for algo, make in build.items():
    model = make()
    r = record(model)
    if algo in ("sac", "crossq"):  # sbx's optax optimisers: read the source of the policy's build step
        src = inspect.getsource(type(model.policy).build)
        r["optimizer_source"] = [l.strip() for l in src.splitlines() if "optax" in l or "b1" in l or "optimizer" in l][:12]
    if algo == "ppo_sbx":
        src = inspect.getsource(type(model.policy).build)
        r["optimizer_source"] = [l.strip() for l in src.splitlines() if "optax" in l or "optimizer" in l][:12]
    f, d = saved(algo, "HalfCheetah-v5" if algo == "trpo" else "Hopper-v5")
    r["saved_model"] = f
    r["saved_model_data"] = d
    res["programs"][algo] = r
    print(algo, json.dumps(r, default=str)[:600])
res["e6_recipe_note"] = "run.py ZOO_PPO_HOPPER (rl_zoo3 2.9.2 hyperparams/ppo.yml, Hopper-v4), VecNormalize obs+reward"
json.dump(res, open("analysis/hyperparams.json", "w"), indent=1, default=str)
