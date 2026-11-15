"""Download again the PDFs we read, from the exact address recorded at reading time, and check each one by SHA-256.

The PDFs are under copyright, so the repository holds only their fingerprints (pdfs.csv: id, file, sha256, bytes,
source, read). This script fetches each `source` as it is (an arXiv address keeps its version, `.../2401.01234v2`),
writes it under OUT/, and compares its SHA-256 with the one of the file we read. It never modifies a committed file.
A publisher may serve a re-encoded file with the same text: a mismatch is reported, not hidden, and check_codes.py
can still check the quotes against the text of the new file.

  python3 fetch_pdfs.py pdf            # the PDFs read in the survey, into study/pdf/
  python3 fetch_pdfs.py pdf --all      # every PDF of pdfs.csv, read or not

Requests are spaced by a random pause of 1.5 to 4 s, one at a time; a refused request waits with exponential
backoff and full jitter, at most five attempts. Exit code 1 if a download fails or a file differs; the supplements
and checklist pages with no recorded source (see pdfs.csv) are listed.
"""
import argparse
import csv
import hashlib
import os
import random
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "pineau-rl-study/2.0 (+https://github.com/warith-harchaoui/pineau-rl)"}


def get(url, attempts=5):
    for k in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            if k == attempts - 1:
                raise
            retry_after = getattr(e, "headers", None) and e.headers.get("Retry-After")
            floor = float(retry_after) if retry_after and retry_after.isdigit() else 0.0
            time.sleep(floor + random.uniform(0, min(300, 5 * 2 ** k)))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("out", help="output folder (pdf/ is the one check_codes.py reads)")
    p.add_argument("--all", action="store_true", help="every PDF of pdfs.csv, not only those read")
    p.add_argument("--ids", nargs="*", help="only these ids (e.g. LR01 C11)")
    args = p.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    rows = [r for r in csv.DictReader(open(os.path.join(here, "pdfs.csv"), encoding="utf-8")) if (args.all or r["read"] == "yes") and (not args.ids or r["id"] in args.ids)]
    ok, differ, failed, nosource = 0, [], [], []
    for i, r in enumerate(rows):
        f = os.path.join(args.out, os.path.basename(r["file"]))
        if os.path.exists(f) and hashlib.sha256(open(f, "rb").read()).hexdigest() == r["sha256"]:
            ok += 1
            continue
        if not r["source"]:
            nosource.append(r["id"])
            continue
        if i:
            time.sleep(random.uniform(1.5, 4.0))
        try:
            b = get(r["source"])
        except Exception as e:  # reported below, with the exit code
            failed.append(f"{r['id']}: {e}")
            continue
        os.makedirs(args.out, exist_ok=True)
        open(f, "wb").write(b)
        if hashlib.sha256(b).hexdigest() == r["sha256"]:
            ok += 1
        else:
            differ.append(r["id"])
        print(r["id"], "identical" if r["id"] not in differ else "DIFFERENT", flush=True)
    print(f"{ok} of {len(rows)} identical to the files we read; {len(differ)} different: {differ}; "
          f"{len(failed)} failed: {failed}; {len(nosource)} with no recorded source: {nosource}")
    sys.exit(1 if differ or failed else 0)  # files with no recorded source are listed, not counted as failures


if __name__ == "__main__":
    main()
