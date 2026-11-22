"""The agents' reading of a paper, for the human re-readings (accord_v0.py, deviation 34 to come; compare.py,
deviation 35 of study/PROTOCOL.md). Importing this module reads the agents' codes: the scripts import it only after
checking that the human data are complete.

    final(pid, k)   final harmonised value, the one the verdicts rest on (samples.val, extended to every primary
                    reader of codes_v2); X8 as x8_stats.py: "no" when X2 is not "yes", else the reading of S1 to S6
    raw(pid, k)     the primary reader's raw value, no harmonisation (as agree_v2.py)
    quote(pid, k)   {value, quote, page} of the reading that gives the raw value
    agreement(pairs, rng)   share of agreement with Wilson's interval, Cohen's kappa with a percentile bootstrap over
                    papers (as survey_extra.py, deviation 30 a)
Y3 is turned into yes/no (yes when at least 2), as everywhere else.
"""
import os
import sys
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parent.parent
os.chdir(STUDY)
sys.path.insert(0, str(STUDY))

from pineau_rl.grid import iter_reads, list_readers, load_overrides, value, y3_yes_no  # noqa: E402
from pineau_rl.stats import cohen_kappa, wilson_ci  # noqa: E402
from load import load  # noqa: E402

SECOND = ("G2", "R2", "R3", "pilot")
OV1 = load_overrides("overrides.json", missing_ok=True)
OV2 = load_overrides("overrides_v2.json", missing_ok=True)
OLD = load("ABCDEF")
V2 = {r["id"]: r for _, r in iter_reads("codes_v2", [d for d in list_readers("codes_v2") if d not in SECOND])}
X8 = {r["id"]: r for _, r in iter_reads("codes_x8", [f"S{i}" for i in range(1, 7)])}
B = 10_000


def known(pid):
    return pid in OLD or pid in V2


def final(pid, k):
    if k == "X8":
        if final(pid, "X2") != "yes":
            return "no"
        return X8[pid]["criteria"]["X8"]["value"] if pid in X8 else None
    return value(pid, k, V2, OLD, OV2, OV1)


def _source(pid, k):
    if k == "X8":
        return X8.get(pid)
    if pid in V2 and k in V2[pid]["criteria"]:
        return V2[pid]
    return OLD.get(pid)


def quote(pid, k):
    rec = _source(pid, k)
    return None if rec is None or k not in rec["criteria"] else rec["criteria"][k]


def raw(pid, k):
    c = quote(pid, k)
    if k == "X8" and c is None:
        return "no" if raw(pid, "X2") == "no" else None
    v = None if c is None else c.get("value")
    if k == "Y3" and isinstance(v, int):
        return y3_yes_no(v)
    return v


def r6(x):
    return None if x is None else round(float(x), 6)


def kappa_boot(a, b, rng):
    a, b, n = np.array(a), np.array(b), len(a)
    ks, undefined = [], 0
    for _ in range(B):
        i = rng.integers(0, n, n)
        k = cohen_kappa(list(a[i]), list(b[i]))
        if k is None:
            undefined += 1
        else:
            ks.append(k)
    return [r6(np.percentile(ks, 2.5)), r6(np.percentile(ks, 97.5))] if ks else None, undefined


def agreement(pairs, rng):
    """pairs: [(human, agents)] of yes/no values."""
    n, same = len(pairs), sum(x == y for x, y in pairs)
    if not n:
        return dict(n=0)
    a, b = zip(*pairs)
    k = cohen_kappa(list(a), list(b)) if len(set(a)) > 1 and len(set(b)) > 1 else None
    ci, und = kappa_boot(a, b, rng) if k is not None else (None, None)
    out = dict(n=n, same=same, agree=r6(same / n), wilson=[r6(x) for x in wilson_ci(same, n)], kappa=r6(k),
               kappa_boot95=ci, boot_undefined=und)
    for side in ("yes", "no"):  # the agents' "yes" apart from their "no": a non-blind re-reading checks the "yes"
        sub = [(h, g) for h, g in pairs if g == side]
        s = sum(h == g for h, g in sub)
        out[f"agents_{side}"] = dict(n=len(sub), human_same=s, agree=r6(s / len(sub)) if sub else None,
                                     wilson=[r6(x) for x in wilson_ci(s, len(sub))] if sub else None)
    return out
