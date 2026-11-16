"""The 2026 draw comes back from its rule (study/draw_2026.py)."""
import json
import subprocess
import sys

from conftest import ROOT


def test_draw_2026_reproduces_the_committed_sample():
    r = subprocess.run([sys.executable, "draw_2026.py"], cwd=ROOT / "study", capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "50 of 50" in r.stdout


def test_draw_depends_on_the_seed():
    sys.path.insert(0, str(ROOT / "study"))
    from draw_2026 import draw
    population = json.loads((ROOT / "study/rl_population_2026.json").read_text())
    assert [p["title"] for p in draw(population, 2018)] != [p["title"] for p in draw(population, 2019)]
