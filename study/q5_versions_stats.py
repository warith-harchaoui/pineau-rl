"""arXiv version against proceedings version for Q5 (PROTOCOL.md, deviation 31), step 2: the four readings.

Reads q5_versions_candidates.json (q5_versions.py candidates), q5_versions_verdicts.json (the blind arbiter's verdicts,
one per item of q5_versions_batches/batch.json, mapped back by q5_versions_batches/key.json) and q5_repos.json.
  P0  as published (extension_stats.json);
  P1  both years on the proceedings: 2018 as read; each 2026 paper read on arXiv takes its proceedings decision
      (quoted address found, or an occurrence the arbiter turns; otherwise no); a paper with no proceedings PDF keeps
      its reading;
  P2  both years on the latest arXiv version: each 2018 "no" with an arXiv version takes its arXiv decision; 2026 as read;
  P3  available at the conference: P2, each "yes" whose GitHub repositories were all created after the conference's
      last day turned "no" (a link with no date, or no GitHub link, keeps "yes"; the bound "unknown_no" turns them too).
Each reading redoes the main comparison with the same test: Newcombe, Fisher, Holm over the 11 v1 criteria with the 10
other p-values of extension_stats.json. "uncertain" verdicts: "no" in the main reading whatever the arbiter's best guess, "yes" in the "_bound" one.
Run from study/: ../sim/env-an/bin/python q5_versions_stats.py  -> q5_versions.json
"""
import json
from pineau_rl.stats import compare, holm
from samples import classic26, experimental, ours18, val

V1 = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7"]
ext = {r["k"]: r for r in json.load(open("extension_stats.json"))["rows"]}
cand = {(c["id"], c["version"]): c for c in json.load(open("q5_versions_candidates.json"))}
key = {int(i): tuple(v) for i, v in json.load(open("q5_versions_batches/key.json")).items()}
verd = {}
for v in json.load(open("q5_versions_verdicts.json")):
    pid, year, version = key[v["item"]]
    verd[(pid, version)] = dict(v, id=pid, year=year, version=version)
assert set(verd) == {k for k, c in cand.items() if c["status"] == "to arbitrate"}, "one verdict per item"
repos = json.load(open("q5_repos.json"))
E18, E26 = experimental(ours18), experimental(classic26)


def r6(x):
    return None if x is None else round(float(x), 6)


def other_version(pid, version, bound):
    c = cand.get((pid, version))
    if c is None or c["status"] == "no other version":
        return None  # keeps its reading
    if c["status"] == "quoted address found":
        return "yes"
    if c["status"] == "no occurrence":
        return "no"
    v = verd[(pid, version)]
    return "yes" if (v["turn"] and not v["uncertain"]) or (bound and (v["turn"] or v["uncertain"])) else "no"


def available(pid, unknown_no):
    r = repos.get(pid)
    if not r or not r["repos"]:
        return not unknown_no
    dates = list(r["repos"].values())
    if any(d is None for d in dates) and not unknown_no:
        return True
    return any(d is not None and d[:10] <= r["last_day"] for d in dates)


def reading(name, bound=False, unknown_no=False):
    v18 = {p: val(p, "Q5") for p in E18}
    v26 = {p: val(p, "Q5") for p in E26}
    if name == "P1":
        for p in E26:
            v26[p] = other_version(p, "proc", bound) or v26[p]
    if name in ("P2", "P3"):
        for p in E18:
            if v18[p] == "no":
                v18[p] = other_version(p, "arxiv", bound) or v18[p]
    if name == "P3":
        for d in (v18, v26):
            for p in d:
                if d[p] == "yes" and not available(p, unknown_no):
                    d[p] = "no"
    c18 = (sum(x == "yes" for x in v18.values()), sum(x in ("yes", "no") for x in v18.values()))
    c26 = (sum(x == "yes" for x in v26.values()), sum(x in ("yes", "no") for x in v26.values()))
    c = compare(c26, c18)
    ps = [ext[k]["classic_vs_ours2018"]["p"] if k != "Q5" else c["p"] for k in V1]
    c["p_holm"] = holm(ps)[V1.index("Q5")]
    changed = {"2018": sorted(p for p in E18 if v18[p] != val(p, "Q5")), "2026": sorted(p for p in E26 if v26[p] != val(p, "Q5"))}
    return dict(ours2018=list(c18), classic2026=list(c26), **{a: r6(b) for a, b in c.items()},
                holds=c["p_holm"] < .05, fragile=c["lo"] <= 0, changed=changed)


out = dict(readings={"P0": reading("P0"), "P1": reading("P1"), "P1_bound": reading("P1", bound=True),
                     "P2": reading("P2"), "P2_bound": reading("P2", bound=True),
                     "P3": reading("P3"), "P3_bound": reading("P3", bound=True, unknown_no=True)})
assert out["readings"]["P0"]["ours2018"] == ext["Q5"]["ours2018"] and out["readings"]["P0"]["classic2026"] == ext["Q5"]["classic2026"]
out["coverage"] = {
    "2018_no": len([p for p in E18 if val(p, "Q5") == "no"]),
    "2018_arxiv_found": sorted(p for (p, v), c in cand.items() if v == "arxiv" and c["status"] != "no other version"),
    "2018_no_arxiv": sorted(p for (p, v), c in cand.items() if v == "arxiv" and c["status"] == "no other version"),
    "2026_proc_found": sorted(p for (p, v), c in cand.items() if v == "proc" and c["status"] != "no other version"),
    "2026_no_proc": sorted(p for (p, v), c in cand.items() if v == "proc" and c["status"] == "no other version"),
    "status": {f"{v} {s}": sorted(p for (p, vv), c in cand.items() if vv == v and c["status"] == s)
               for v in ("arxiv", "proc") for s in ("quoted address found", "no occurrence", "to arbitrate", "no other version")},
    "turned": sorted(f"{p} {v}" for (p, v), x in verd.items() if x["turn"]),
    "uncertain": sorted(f"{p} {v}" for (p, v), x in verd.items() if x["uncertain"])}
rep = []
for pid, r in sorted(repos.items()):
    for name, d in r["repos"].items():
        rep.append(dict(id=pid, repo=name, created=d, last_day=r["last_day"],
                        after=None if d is None else d[:10] > r["last_day"]))
out["repositories"] = dict(n=len(rep), unknown=sum(x["after"] is None for x in rep),
                           created_after={y: sorted({x["id"] for x in rep if x["after"] and x["id"] in (E18 if y == "2018" else E26)})
                                          for y in ("2018", "2026")},
                           no_github_link=sorted(p for p, r in repos.items() if not r["repos"]), rows=rep)
json.dump(out, open("q5_versions.json", "w"), indent=1)
for n, r in out["readings"].items():
    print(f"{n:9s} 2018 {r['ours2018']}  2026 {r['classic2026']}  diff {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"
          f"  Holm p {r['p_holm']:.4g}  holds {r['holds']}  changed {r['changed']}")
print({k: (len(v) if isinstance(v, list) else v) for k, v in out["coverage"].items() if k != "status"})
print("repos:", out["repositories"]["n"], "unknown", out["repositories"]["unknown"], "after", out["repositories"]["created_after"])
