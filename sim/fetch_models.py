"""Download the trained policies that are too large for git, and check every policy against models/MANIFEST.sha256.

The PPO, TRPO and E6 policies are in the repository. The SAC and CrossQ weights (8.6 MB and 68 MB each) are attached
to the GitHub release `policies-v1`, as tar archives listed with their SHA-256 in the release's SHA256SUMS. This script
downloads each archive, checks it, unpacks it under models/, then checks every policy file of models/MANIFEST.sha256,
the fingerprints taken on the machine that trained them (15 November 2026).

  python3 fetch_models.py            # from sim/: download, unpack, check everything
  python3 fetch_models.py --check    # only check the policies already present

Downloads are one at a time, spaced by a random pause of 1.5 to 4 s; a refused request waits with exponential backoff
and full jitter, at most five attempts. Exit code 1 if anything is missing or differs.
"""
import argparse
import hashlib
import os
import random
import sys
import tarfile
import time
import urllib.error
import urllib.request

RELEASE = "https://github.com/warith-harchaoui/pineau-rl/releases/download/policies-v1/"
UA = {"User-Agent": "pineau-rl/1.0 (+https://github.com/warith-harchaoui/pineau-rl)"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def get(url, out, attempts=5):
    for k in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(out, "wb") as f:
                while block := r.read(1 << 20):
                    f.write(block)
            return
        except (urllib.error.URLError, TimeoutError):
            if k == attempts - 1:
                raise
            time.sleep(random.uniform(0, min(300, 5 * 2 ** k)))


def check():
    bad = []
    rows = [line.split() for line in open("models/MANIFEST.sha256", encoding="utf-8") if line.strip()]
    for digest, path in rows:
        if not os.path.exists(path) or sha256(path) != digest:
            bad.append(path)
    print(f"{len(rows) - len(bad)} of {len(rows)} policies identical to those trained; differ or missing: {bad}")
    return not bad


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="only check the policies already present")
    args = p.parse_args()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not args.check:
        os.makedirs("downloads", exist_ok=True)
        get(RELEASE + "SHA256SUMS", "downloads/SHA256SUMS")
        for line in open("downloads/SHA256SUMS", encoding="utf-8"):
            digest, name = line.split()
            out = os.path.join("downloads", name)
            if not (os.path.exists(out) and sha256(out) == digest):
                time.sleep(random.uniform(1.5, 4.0))
                print("downloading", name, flush=True)
                get(RELEASE + name, out)
            if sha256(out) != digest:
                sys.exit(f"{name}: SHA-256 differs from the release's SHA256SUMS")
            with tarfile.open(out) as t:
                t.extractall(".", filter="data")
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
