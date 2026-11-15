"""Shared helpers for the test suite.

The tests import the package pineau_rl (installed with `make install`, or found on PYTHONPATH by `make test`), and
sim/analysis/runs.py, this study's thin layer over pineau_rl.runs. No analysis script is imported: they compute at
import time, and their pieces now live in the package.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # the package, even when it is not installed
sys.path.insert(0, str(ROOT / "sim" / "analysis"))


@pytest.fixture
def in_dir(monkeypatch):
    """Change into a directory for the duration of a test (the scripts read relative paths)."""
    def go(path):
        monkeypatch.chdir(path)
        return Path(path)
    return go
