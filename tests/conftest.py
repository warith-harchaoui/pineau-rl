"""Shared helpers for the test suite.

Most analysis scripts run their whole computation at import time (they are scripts, not modules). To test one of
their functions without running the script, `extract` reads the file, keeps only the named top-level functions and
assignments, then executes them in a fresh namespace. The scripts themselves are never modified or imported.
"""
import ast
import math
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import numpy as np
import pytest
from scipy import stats
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]


def extract(relpath, names, extra=None):
    """Return {name: object} for the first top-level function or assignment of each of `names` in ROOT/relpath."""
    tree = ast.parse((ROOT / relpath).read_text(encoding="utf-8"))
    keep, found = [], set()
    for node in tree.body:  # the first definition of each name only: some scripts reuse a name further down
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            continue
        if name in names and name not in found:
            keep.append(node)
            found.add(name)
    missing = set(names) - found
    assert not missing, f"{relpath} no longer defines {sorted(missing)}"
    ns = dict(math=math, np=np, stats=stats, norm=norm, Decimal=Decimal, ROUND_HALF_UP=ROUND_HALF_UP)
    ns.update(extra or {})
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(ROOT / relpath), "exec"), ns)
    return {k: ns[k] for k in names}


@pytest.fixture
def in_dir(monkeypatch):
    """Change into a directory for the duration of a test (the scripts read relative paths)."""
    def go(path):
        monkeypatch.chdir(path)
        return Path(path)
    return go


sys.path.insert(0, str(ROOT / "study"))
sys.path.insert(0, str(ROOT / "sim" / "analysis"))
