"""Compare the result JSON files of the working tree with those of a git commit, number by number.

`git diff` says that a file changed; this says which values changed and by how much, so that a difference between two
platforms can be judged: last-digit noise of floating-point arithmetic, or a change in a count, a verdict, a ranking.
Strings, booleans, integers and the structure must be equal; floats must agree within --rtol (default 0: exact).

  python tools/compare_results.py                 # every result file against HEAD, exact
  python tools/compare_results.py --rtol 1e-9     # tolerate relative differences up to 1e-9 on floats
  python tools/compare_results.py --ref <commit> study/trajectory.json

Exit code 1 if any value differs beyond the tolerance.
"""
import argparse
import glob
import json
import math
import subprocess
import sys

FILES = ["study/*.json", "sim/analysis/*.json", "sim/llm/results/*.json"]


def walk(a, b, path, rtol, out):
    """Append (path, a, b) to out for every leaf where a and b differ beyond rtol."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append((f"{path}/{k}", a.get(k, "<absent>"), b.get(k, "<absent>")))
            else:
                walk(a[k], b[k], f"{path}/{k}", rtol, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((f"{path} (length)", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", rtol, out)
    elif isinstance(a, float) and isinstance(b, float):
        if not (a == b or (math.isnan(a) and math.isnan(b)) or math.isclose(a, b, rel_tol=rtol, abs_tol=0.0)):
            out.append((path, a, b))
    elif type(a) is not type(b) or a != b:
        out.append((path, a, b))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("files", nargs="*", help="result files (default: every tracked result JSON)")
    p.add_argument("--ref", default="HEAD", help="git commit to compare against (default HEAD)")
    p.add_argument("--rtol", type=float, default=0.0, help="relative tolerance on floats (default 0)")
    args = p.parse_args()
    files = args.files or sorted(f for g in FILES for f in glob.glob(g))
    tracked = set(subprocess.run(["git", "ls-files", *files], capture_output=True, text=True, check=True).stdout.split())
    bad = 0
    for f in files:
        if f not in tracked:
            continue
        old = json.loads(subprocess.run(["git", "show", f"{args.ref}:{f}"], capture_output=True, text=True, check=True).stdout)
        with open(f, encoding="utf-8") as fh:
            new = json.load(fh)
        diffs = []
        walk(old, new, "", args.rtol, diffs)
        for path, a, b in diffs:
            rel = f"  rel {abs(a - b) / max(abs(a), abs(b)):.1e}" if isinstance(a, float) and isinstance(b, float) and (a or b) else ""
            print(f"{f}{path}: {a!r} -> {b!r}{rel}")
        bad += len(diffs)
    print(f"{len(files)} files compared with {args.ref}, {bad} values differ" + (f" beyond rtol={args.rtol}" if args.rtol else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
