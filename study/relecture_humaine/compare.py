"""Blind human re-reading of deviation 35 (study/PROTOCOL.md): the analysis fixed in advance.

1. Every sheet feuilles/H01.md to H30.md is parsed (feuille.py); the script stops while one is missing or incomplete,
   before reading tirage35.json or any agent code.
2. Only then are the agents' codes imported (agents.py). Reference: the agents' final harmonised values (X8 as
   x8_stats.py: "no" when the final X2 is not "yes"); beside them, the primary readers' raw reads. For X8, "na" counts
   as "no" on both sides.
3. Per criterion (Q5, Y9, X7, X2, X8), on the papers where both sides give yes or no: agreement with Wilson's interval,
   Cohen's kappa with a percentile bootstrap over papers (10,000 resamples, default_rng(2035)), the agents' "yes" apart
   from their "no", the agreement per year.
4. Per criterion, on the same papers: the 2026 - 2018 difference in the share of "yes" read by the human (Newcombe,
   Fisher, Holm over the five criteria) and by the agents, and the gap human - agents with a percentile bootstrap
   stratified by year (10,000 resamples, default_rng(2036), papers drawn with replacement within each year, the pair
   kept together). Reading: same sign and human interval excluding zero "found again"; same sign and an interval
   containing zero "same direction, not established"; opposite sign "not found again".
Run from study/: ../sim/env-an/bin/python relecture_humaine/compare.py  -> relecture_humaine/compare35.json
FEUILLES=<folder> reads the sheets from another folder (a scratch copy, to test the script).
"""
import json
import os
import sys
from pathlib import Path

from feuille import CRIT, parse, problems

HERE = Path(__file__).resolve().parent
SHEETS = Path(os.environ.get("FEUILLES", HERE / "feuilles"))
OUT = Path(os.environ.get("OUT", HERE / "compare35.json"))
NAMES = [f"H{i:02d}" for i in range(1, 31)]


def read_sheets():
    sheets, errors = {}, []
    for name in NAMES:
        f = SHEETS / f"{name}.md"
        if not f.exists():
            errors.append(f"{name} : feuille absente")
            continue
        s = parse(f.read_text(encoding="utf-8"))
        errors += [f"{name} : {p}" for p in problems(s)]
        sheets[name] = s
    if errors:
        sys.exit(f"{len(errors)} problèmes dans les feuilles ; rien n'est calculé tant qu'une feuille est incomplète.\n"
                 + "\n".join(errors[:60]) + ("\n..." if len(errors) > 60 else ""))
    return sheets


def yn(k, v):
    if k == "X8" and v == "na":
        return "no"
    return v if v in ("yes", "no") else None


def main():
    sheets = read_sheets()
    # Every sheet is complete: only now are the draw and the agents' codes read.
    import numpy as np
    from agents import agreement, final, quote, r6, raw
    from pineau_rl.stats import compare, holm
    tirage = json.load(open(HERE / "tirage35.json"))
    pid, year = tirage["sheets"], tirage["year"]
    assert sorted(pid) == NAMES
    rng_k, rng_d = np.random.default_rng(2035), np.random.default_rng(2036)
    out = dict(sheets=len(sheets), minutes=sum(int(s["minutes"]) for s in sheets.values() if s["minutes"]),
               dates=sorted({s["date"] for s in sheets.values()}), criteria={}, disagreements=[])
    for k in CRIT:
        res = {}
        for ref, get in (("final", final), ("raw", raw)):
            rows = [(h, yn(k, sheets[h]["criteria"][k]["decision"]), yn(k, get(pid[h], k)), year[h]) for h in NAMES]
            rows = [r for r in rows if r[1] and r[2]]
            pairs = [(hv, av) for _, hv, av, _ in rows]
            r = dict(agreement=agreement(pairs, rng_k),
                     by_year={y: agreement([(hv, av) for _, hv, av, yy in rows if yy == y], rng_k) for y in ("2018", "2026")})
            if ref == "final":
                cnt = {who: {y: (sum(row[i] == "yes" for row in rows if row[3] == y), sum(row[3] == y for row in rows))
                             for y in ("2018", "2026")} for who, i in (("human", 1), ("agents", 2))}
                diff = {who: dict(y2026=list(c["2026"]), y2018=list(c["2018"]),
                                  **{a: r6(b) for a, b in compare(c["2026"], c["2018"]).items()})
                        for who, c in cnt.items()}
                by = {y: np.array([(row[1] == "yes", row[2] == "yes") for row in rows if row[3] == y], float)
                      for y in ("2018", "2026")}
                gaps = []
                for _ in range(10_000):
                    m = {y: by[y][rng_d.integers(0, len(by[y]), len(by[y]))].mean(axis=0) for y in by}
                    d = m["2026"] - m["2018"]
                    gaps.append(d[0] - d[1])
                hd, ad = diff["human"]["diff"], diff["agents"]["diff"]
                if hd * ad > 0:
                    reading = "found again" if (diff["human"]["lo"] > 0 or diff["human"]["hi"] < 0) else \
                        "same direction, not established"
                elif hd * ad < 0:
                    reading = "not found again"
                else:
                    reading = "a difference is zero"
                r.update(difference=diff, gap_human_minus_agents=dict(
                    value=r6(hd - ad), boot95=[r6(np.percentile(gaps, 2.5)), r6(np.percentile(gaps, 97.5))]),
                    reading=reading)
            res[ref] = r
        out["criteria"][k] = res
        for h in NAMES:
            c = sheets[h]["criteria"][k]
            hv, av = yn(k, c["decision"]), yn(k, final(pid[h], k))
            if hv and av and hv != av:
                q = quote(pid[h], k) or {}
                out["disagreements"].append(dict(sheet=h, id=pid[h], year=year[h], criterion=k, human=hv,
                                                 human_quote=c["quote"], human_page=c["page"], human_source=c["source"],
                                                 agents_final=av, agents_raw=raw(pid[h], k),
                                                 agents_quote=q.get("quote"), agents_page=q.get("page"),
                                                 agents_source=q.get("source")))
    ph = holm([out["criteria"][k]["final"]["difference"]["human"]["p"] for k in CRIT])
    for k, p in zip(CRIT, ph):
        out["criteria"][k]["final"]["difference"]["human"]["p_holm5"] = r6(p)
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    for k in CRIT:
        r = out["criteria"][k]["final"]
        a, d = r["agreement"], r["difference"]
        print(f"{k}: agreement {a['same']}/{a['n']} kappa {a['kappa']} {a['kappa_boot95']} | 2026-2018 human "
              f"{d['human']['diff']:+.2f} [{d['human']['lo']:+.2f}, {d['human']['hi']:+.2f}] agents {d['agents']['diff']:+.2f}"
              f" | gap {r['gap_human_minus_agents']['value']:+.2f} {r['gap_human_minus_agents']['boot95']} | {r['reading']}")
    print(len(out["disagreements"]), "disagreements")


if __name__ == "__main__":
    main()
