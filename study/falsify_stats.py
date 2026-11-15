"""Mechanical search against the "no" decisions (PROTOCOL.md, deviation 27), step 2: the result.

Reads falsify_candidates.json (step 1, falsify_no.py) and falsify_verdicts.json (the arbiters' verdicts, one per
decision with at least one occurrence; the blinded batches they saw and their raw answers are in falsify_batches/).
Per criterion and per year: the "no" decisions, those with no occurrence, with occurrences, turned, uncertain. Then the
main comparison redone with the turned decisions (extension_stats.py with OVERRIDES_EXTRA, same tests), as announced;
and, as an extra bound not announced in deviation 27, with the uncertain decisions turned as well.
Run from study/: ../sim/env-an/bin/python falsify_stats.py  -> falsify_no.json
"""
import json, os, subprocess, sys

CRIT = ["Q4", "Q5", "Q7", "Q8", "X2", "X7", "Y9"]
cand = json.load(open("falsify_candidates.json"))
verd = {(r["id"], r["k"]): r for r in json.load(open("falsify_verdicts.json"))}
assert set(verd) == {(r["id"], r["k"]) for r in cand if r["hits"]}  # one verdict per decision with an occurrence

counts = {}
for year in ("2018", "2026"):
    for k in CRIT:
        rows = [r for r in cand if r["year"] == year and r["k"] == k]
        v = [verd[(r["id"], r["k"])] for r in rows if r["hits"]]
        counts[f"{year} {k}"] = dict(no=len(rows), no_occurrence=sum(not r["hits"] for r in rows), with_occurrence=len(v),
                                     turned=sorted(x["id"] for x in v if x["turn"]),
                                     uncertain=sorted(x["id"] for x in v if x["uncertain"]))


def rerun(name, keep):
    """extension_stats.py with the decisions selected by keep() set to yes; returns its rows by criterion."""
    extra = {}
    for (pid, k), x in verd.items():
        if keep(x):
            extra.setdefault(k, {})[pid] = "yes"
    json.dump(extra, open(f"falsify_overrides_{name}.json", "w"), indent=1, sort_keys=True)
    env = dict(os.environ, OVERRIDES_EXTRA=f"falsify_overrides_{name}.json", SUFFIX=f"_falsify_{name}")
    subprocess.run([sys.executable, "extension_stats.py"], env=env, check=True, capture_output=True)
    return {r["k"]: r for r in json.load(open(f"extension_stats_falsify_{name}.json"))["rows"]}


base = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}
runs = dict(turned=rerun("turned", lambda x: x["turn"]), bound=rerun("bound", lambda x: x["turn"] or x["uncertain"]))
comparison = {}
for k in CRIT:
    comparison[k] = {}
    for name, rows in (("published", base), *runs.items()):
        c = rows[k]["classic_vs_ours2018"]
        comparison[k][name] = dict(ours2018=rows[k]["ours2018"], classic2026=rows[k]["classic2026"], diff=c["diff"],
                                   lo=c["lo"], hi=c["hi"], p_holm=c["p_holm"], settled=c["p_holm"] < .05)
out = dict(counts=counts, comparison=comparison,
           verdict_changes={name: [k for k in CRIT if comparison[k][name]["settled"] != comparison[k]["published"]["settled"]]
                            for name in runs})
json.dump(out, open("falsify_no.json", "w"), indent=1)
for key, c in counts.items():
    print(f"{key}: {c['no']} no, {c['no_occurrence']} with no occurrence, {c['with_occurrence']} with, "
          f"{len(c['turned'])} turned {c['turned']}, {len(c['uncertain'])} uncertain")
for k in CRIT:
    p, t, b = (comparison[k][n] for n in ("published", "turned", "bound"))
    print(f"{k}: 2018 {p['ours2018']} -> {t['ours2018']} (bound {b['ours2018']}), 2026 {p['classic2026']} -> {t['classic2026']}"
          f" (bound {b['classic2026']}); diff {p['diff']:+.2f} -> {t['diff']:+.2f} ({b['diff']:+.2f}); "
          f"p Holm {p['p_holm']:.4f} -> {t['p_holm']:.4f} ({b['p_holm']:.4f})")
print("verdicts that change:", out["verdict_changes"])
