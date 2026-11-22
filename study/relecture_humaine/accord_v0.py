"""Agreement between Warith Harchaoui's past human re-reading (warith_v0.csv) and the agents' reading.

Computed as study/agree_v2.py and survey_extra.py (deviation 30 a): per criterion, on the papers where both give
yes or no (Y3 turned into yes/no), the share of agreement with Wilson's interval and Cohen's kappa with a percentile
bootstrap over papers (10,000 resamples, numpy default_rng(2037), resamples with an undefined kappa dropped and
counted). The agents' "yes" are counted apart from their "no": a re-reading done while seeing the agents' reading
(aveugle = non) checks the "yes" it was shown more than it finds the "no" it missed. Every count is given for all
rows, for the blind rows (aveugle = oui) and for the others (aveugle = non), against the agents' final harmonised
values and against their raw reads. Rows whose decision is not yes or no (na, an integer for X1) are listed apart.

The CSV has one row per paper and criterion: id, critere, decision, date, aveugle (oui/non), citation, page, source.
The script refuses to run while the CSV has no row, and before checking every row it reads none of the agents' codes.
Run from study/: ../sim/env-an/bin/python relecture_humaine/accord_v0.py  -> relecture_humaine/accord_v0.json
"""
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLS = ["id", "critere", "decision", "date", "aveugle", "citation", "page", "source"]
CRIT = ["Q%d" % i for i in range(1, 9)] + ["X%d" % i for i in range(1, 9)] + ["Y%d" % i for i in range(1, 13)]
INTEGER = ("X1", "X6", "Y3")


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if r.fieldnames != COLS:
            sys.exit(f"{path.name}: header must be exactly {','.join(COLS)}")
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in r]
    rows = [row for row in rows if any(row.values())]
    if not rows:
        sys.exit(f"{path.name} has no row yet: nothing to compare (see LISEZMOI.md, section « warith_v0.csv »).")
    errors, seen = [], set()
    for i, row in enumerate(rows, start=2):
        c, d = row["critere"], row["decision"]
        if not row["id"]:
            errors.append(f"line {i}: empty id")
        if c not in CRIT:
            errors.append(f"line {i}: unknown criterion {c!r}")
        if not (d in ("yes", "no", "na") or (c in INTEGER and re.fullmatch(r"\d+", d))):
            errors.append(f"line {i}: decision {d!r} is not yes, no, na" + (" or an integer" if c in INTEGER else ""))
        if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", row["date"]):
            errors.append(f"line {i}: date {row['date']!r} is not YYYY, YYYY-MM or YYYY-MM-DD")
        if row["aveugle"] not in ("oui", "non"):
            errors.append(f"line {i}: aveugle {row['aveugle']!r} is not oui or non")
        if not row["source"]:
            errors.append(f"line {i}: empty source (where the record comes from)")
        if row["page"] and not re.fullmatch(r"\d+(\s*[,-]\s*\d+)*", row["page"]):
            errors.append(f"line {i}: page {row['page']!r} is not a number, a list or a range")
        if (row["id"], c) in seen:
            errors.append(f"line {i}: {row['id']} {c} given twice")
        seen.add((row["id"], c))
    if errors:
        sys.exit("\n".join(errors))
    return rows


def yes_no(c, v):
    if c == "Y3" and v is not None and re.fullmatch(r"\d+", str(v)):
        return "yes" if int(v) >= 2 else "no"
    return v if v in ("yes", "no") else None


def main():
    rows = read_rows(HERE / "warith_v0.csv")
    import numpy as np  # the agents' codes are read only now, after the check
    from agents import agreement, final, known, quote, raw
    unknown = sorted({r["id"] for r in rows if not known(r["id"])})
    if unknown:
        sys.exit("ids read by no agent: " + ", ".join(unknown))
    rng = np.random.default_rng(2037)
    out = dict(rows=len(rows), papers=len({r["id"] for r in rows}), criteria={}, outside_pairs=[], disagreements=[])
    for c in [k for k in CRIT if any(r["critere"] == k for r in rows)]:
        sub = [r for r in rows if r["critere"] == c]
        res = {}
        for ref, get in (("final", final), ("raw", raw)):
            res[ref] = {}
            for blind in ("all", "oui", "non"):
                pairs = [(yes_no(c, r["decision"]), yes_no(c, get(r["id"], c))) for r in sub
                         if blind == "all" or r["aveugle"] == blind]
                res[ref][blind] = agreement([p for p in pairs if p[0] and p[1]], rng)
        out["criteria"][c] = res
        for r in sub:
            h, g = yes_no(c, r["decision"]), yes_no(c, final(r["id"], c))
            if not (h and g):
                out["outside_pairs"].append(dict(id=r["id"], criterion=c, human=r["decision"], agents=final(r["id"], c)))
            elif h != g:
                q = quote(r["id"], c) or {}
                out["disagreements"].append(dict(id=r["id"], criterion=c, aveugle=r["aveugle"], human=h,
                                                 human_quote=r["citation"], human_page=r["page"], agents_final=g,
                                                 agents_raw=raw(r["id"], c), agents_quote=q.get("quote"),
                                                 agents_page=q.get("page")))
    json.dump(out, open(HERE / "accord_v0.json", "w"), indent=1, ensure_ascii=False)
    for c, res in out["criteria"].items():
        a = res["final"]["all"]
        if a["n"]:
            print(f"{c:4s} {a['same']}/{a['n']} [{a['wilson'][0]:.2f}, {a['wilson'][1]:.2f}] kappa {a['kappa']} "
                  f"{a['kappa_boot95']}  agents yes {a['agents_yes']['human_same']}/{a['agents_yes']['n']}"
                  f"  agents no {a['agents_no']['human_same']}/{a['agents_no']['n']}")
    print(len(out["disagreements"]), "disagreements,", len(out["outside_pairs"]), "rows outside the yes/no pairs")


if __name__ == "__main__":
    main()
