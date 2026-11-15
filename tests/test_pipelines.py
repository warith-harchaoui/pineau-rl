"""Small end-to-end checks on fabricated inputs: how runs are read (sim/analysis/runs.py) and the GRPO summary."""
import importlib
import json
import subprocess
import sys

import pytest
from conftest import ROOT


def write_run(root, algo, task, seed, final_step, score):
    d = root / "results" / algo / task
    d.mkdir(parents=True, exist_ok=True)
    rows = ["step,eval_mean,eval_std,perturbed_mean"]
    rows += [f"{s},{score * s / final_step},1.0,{score}" for s in range(50_000, final_step + 1, 50_000)]
    (d / f"seed{seed}.csv").write_text("\n".join(rows) + "\n")


@pytest.fixture
def runs(monkeypatch):
    for var in ("SEEDS", "BUDGET", "SUFFIX"):  # the preregistered analysis: ten random seeds, own budget
        monkeypatch.delenv(var, raising=False)
    import runs as module
    return importlib.reload(module)


def test_finals_reads_the_last_evaluation(runs, tmp_path, in_dir):
    in_dir(tmp_path)
    for s in range(10):
        write_run(tmp_path, "sac", "Hopper-v5", s, 200_000, 1000 + s)
    x = runs.finals("sac", "Hopper-v5")
    assert list(x) == [1000 + s for s in range(10)]


def test_unfinished_or_missing_runs_give_none(runs, tmp_path, in_dir):
    in_dir(tmp_path)
    for s in range(9):
        write_run(tmp_path, "sac", "Hopper-v5", s, 200_000, 1000)
    assert runs.finals("sac", "Hopper-v5") is None              # seed 9 missing
    write_run(tmp_path, "sac", "Hopper-v5", 9, 150_000, 1000)
    assert runs.finals("sac", "Hopper-v5") is None              # seed 9 stopped before 200,000 steps
    G, missing = runs.grid()
    assert "sac/Hopper-v5" in missing and len(missing) == 16


def test_grpo_summary_on_three_seeds(tmp_path):
    def run(model, reward, seed, p0, p100, last=100):
        d = tmp_path / "results" / model / "mul2" / reward
        d.mkdir(parents=True, exist_ok=True)
        lines = [{"step": 0, "pass1": p0, "truncated": 0.5}, {"step": 1, "loss": 0.1}]
        lines.append({"step": last, "pass1": p100, "truncated": 0.2})
        (d / f"seed{seed}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))

    for s, (p0, p100) in enumerate([(0.10, 0.30), (0.20, 0.30), (0.10, 0.40)]):
        run("qwen05", "true", s, p0, p100)
        run("qwen05", "random", s, p0, p0)
    run("qwen05", "true", 3, 0.1, 0.9, last=50)                 # unfinished: left out
    subprocess.run([sys.executable, str(ROOT / "sim/llm/summary.py")], cwd=tmp_path, check=True,
                   capture_output=True)
    summary = json.loads((tmp_path / "results/summary.json").read_text())
    gains = json.loads((tmp_path / "results/gains.json").read_text())
    assert len(summary) == 6
    g = gains["qwen05 true"]
    assert g["gains"] == pytest.approx([0.2, 0.1, 0.3]) and g["mean"] == pytest.approx(0.2)
    assert g["ci"][0] == pytest.approx(0.1) and g["ci"][1] == pytest.approx(0.3)  # only ten distinct resamples
    assert gains["qwen05 random"]["gains"] == [0, 0, 0] and gains["qwen05 random"]["ci"] == [0, 0]
