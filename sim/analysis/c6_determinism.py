"""Determinism of SAC and CrossQ (SIM_PROTOCOL.md, deviation 32, written before any training).
SAC on Hopper-v5 seeds 0 and 1 and CrossQ on Walker2d-v5 seed 0 were rerun with the same code and environment, under the
names sac_rerun and crossq_rerun (run.py: the same programs, nothing changed). At each evaluation point: exact equality
of eval_mean, eval_std and perturbed_mean (wall is a duration), SHA-256 of these columns, largest relative gap.
Rule: identical everywhere, "same program, same seed, same machine: same run" holds for these programs on this machine;
otherwise it goes for SAC and CrossQ and the gaps are reported.
Run from sim/ once the reruns are finished: env-an/bin/python analysis/c6_determinism.py  -> analysis/c6_determinism.json
"""
import hashlib, json
from pineau_rl.runs import read_run, run_path

COLS = ("step", "eval_mean", "eval_std", "perturbed_mean")
RUNS = [("sac", "Hopper-v5", 0), ("sac", "Hopper-v5", 1), ("crossq", "Walker2d-v5", 0)]
res = dict(runs={})
for algo, task, s in RUNS:
    a = read_run(run_path("results", algo, task, s), 200_000)
    b = read_run(run_path("results", f"{algo}_rerun", task, s), 200_000)
    assert a is not None and b is not None, (algo, task, s, "rerun not finished")
    sha = lambda rows: hashlib.sha256("\n".join(",".join(r[c] for c in COLS) for r in rows).encode()).hexdigest()
    gaps = [abs(float(x[c]) - float(y[c])) / abs(float(x[c])) for x, y in zip(a, b) for c in COLS[1:] if x[c] and y[c]]
    res["runs"][f"{algo}/{task}/seed{s}"] = dict(
        identical=all(x[c] == y[c] for x, y in zip(a, b) for c in COLS) and len(a) == len(b),
        sha256_original=sha(a), sha256_rerun=sha(b), max_relative_gap=max(gaps),
        final_original=float(a[-1]["eval_mean"]), final_rerun=float(b[-1]["eval_mean"]),
        points_identical=[all(x[c] == y[c] for c in COLS) for x, y in zip(a, b)])
    print(algo, task, s, res["runs"][f"{algo}/{task}/seed{s}"])
res["all_identical"] = all(r["identical"] for r in res["runs"].values())
print("all identical:", res["all_identical"])
json.dump(res, open("analysis/c6_determinism.json", "w"), indent=1)
