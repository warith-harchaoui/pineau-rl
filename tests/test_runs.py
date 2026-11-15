"""pineau_rl.runs: the run format, its checked reader, the final scores and the grid, on fabricated runs."""
import numpy as np
import pytest

from pineau_rl.runs import COLUMNS, finals, load_grid, read_run, run_path, write_run


def make(root, algo, task, seed, last, score, every=50_000):
    """A run evaluated every 50,000 steps up to `last`, its score growing linearly to `score`."""
    write_run(run_path(str(root), algo, task, seed),
              [dict(step=s, eval_mean=score * s / last, eval_std=1.0, perturbed_mean=score / 2, wall=s / 1000)
               for s in range(every, last + 1, every)])


def test_run_path_and_columns():
    assert run_path("results", "sac", "Hopper-v5", 3) == "results/sac/Hopper-v5/seed3.csv"
    assert COLUMNS == ("step", "eval_mean", "eval_std", "perturbed_mean", "wall")


def test_write_then_read(tmp_path):
    make(tmp_path, "sac", "Hopper-v5", 0, 200_000, 1000.0)
    f = run_path(str(tmp_path), "sac", "Hopper-v5", 0)
    assert open(f).readline().strip() == ",".join(COLUMNS)
    rows = read_run(f)
    assert [int(r["step"]) for r in rows] == [50_000, 100_000, 150_000, 200_000]
    assert rows[-1] == dict(step="200000", eval_mean="1000.0", eval_std="1.0", perturbed_mean="500.0", wall="200.0")
    assert read_run(f, final_step=200_000) == rows
    assert read_run(f, final_step=200_000, upto=100_000) == rows[:2]   # read at a smaller budget


def test_missing_and_unfinished_runs_give_none(tmp_path):
    assert read_run(str(tmp_path / "nothing.csv")) is None
    make(tmp_path, "sac", "Hopper-v5", 0, 150_000, 1000.0)
    assert read_run(run_path(str(tmp_path), "sac", "Hopper-v5", 0), final_step=200_000) is None


def test_malformed_files_raise(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("step,score\n50000,1.0\n")
    with pytest.raises(ValueError, match="missing column"):
        read_run(str(f))
    f.write_text("step,eval_mean\n100000,1.0\n50000,2.0\n")
    with pytest.raises(ValueError, match="increasing"):
        read_run(str(f))
    f.write_text("step,eval_mean\n")
    with pytest.raises(ValueError, match="no evaluation"):
        read_run(str(f))
    f.write_text("step,eval_mean,eval_std\n50000,1.0,0.5\n")      # optional columns may be absent
    assert read_run(str(f))[0]["eval_mean"] == "1.0"


def test_finals(tmp_path):
    root = str(tmp_path)
    for s in range(3):
        make(root, "ppo", "Hopper-v5", s, 1_000_000, 100.0 + s)
    assert finals(root, "ppo", "Hopper-v5", range(3), 1_000_000).tolist() == [100.0, 101.0, 102.0]
    assert finals(root, "ppo", "Hopper-v5", [2, 0], 1_000_000).tolist() == [102.0, 100.0]  # the order of the seeds
    at_200k = finals(root, "ppo", "Hopper-v5", range(3), 1_000_000, step=200_000)
    assert at_200k.tolist() == pytest.approx([20, 20.2, 20.4])
    assert finals(root, "ppo", "Hopper-v5", range(3), 1_000_000, column="perturbed_mean").tolist() == [50, 50.5, 51]
    assert finals(root, "ppo", "Hopper-v5", range(4), 1_000_000) is None              # seed 3 missing
    with pytest.raises(ValueError, match="seed3"):
        finals(root, "ppo", "Hopper-v5", range(4), 1_000_000, strict=True)
    assert finals(root, "ppo", "Hopper-v5", range(3), 2_000_000) is None              # not at that budget
    assert finals(root, "ppo", "Hopper-v5", range(3), None).tolist() == [100.0, 101.0, 102.0]  # any last step
    with pytest.raises(ValueError, match="no evaluation at step"):
        finals(root, "ppo", "Hopper-v5", range(3), 1_000_000, step=120_000)


def test_load_grid_golden(tmp_path):
    root = str(tmp_path)
    final = {"ppo": 1_000_000, "sac": 200_000}
    for t, base in (("Hopper-v5", 1000.0), ("Swimmer-v5", 50.0)):
        for s in range(5):
            make(root, "ppo", t, s, 1_000_000, base + s)
            if t == "Hopper-v5":
                make(root, "sac", t, s, 200_000, 2 * base + s)
    G, missing = load_grid(root, ["ppo", "sac"], ["Hopper-v5", "Swimmer-v5"], range(5), final)
    assert missing == ["sac/Swimmer-v5"]
    assert list(G) == ["Hopper-v5", "Swimmer-v5"] and list(G["Hopper-v5"]) == ["ppo", "sac"]
    assert G["Hopper-v5"]["sac"].tolist() == [2000.0, 2001.0, 2002.0, 2003.0, 2004.0]
    assert isinstance(G["Swimmer-v5"]["ppo"], np.ndarray)
    G, _ = load_grid(root, ["ppo", "sac"], ["Hopper-v5"], range(5), final, step={"ppo": 200_000, "sac": 200_000})
    assert G["Hopper-v5"]["ppo"].tolist() == pytest.approx([200.0, 200.2, 200.4, 200.6, 200.8])  # equal budget
