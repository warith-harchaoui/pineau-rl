"""Every key number of conclusions.md and conclusions-en.md, recomputed from the result files.

Each claim recomputes a value from study/ or sim/analysis/, formats it the way each text writes it, and
checks that the formatted string appears in that text (whitespace and line breaks normalised). A claim that
no file supports (a figure from a slide or a cited paper) does not belong here: its source is the
bibliography. Exit code 1 on the first missing number, so docs/build.sh stops before compiling.

Run from docs/: python3 check_numbers.py
"""
import json, re, statistics, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "study"))
J = lambda p: json.load(open(ROOT / p))

res = {r["k"]: r for r in J("study/results_final.json")}
audit = {r["k"]: r for r in J("study/audit_stats.json")["rows"]}
agree = J("study/audit_stats.json")["agreement"]
e1, curve = J("sim/analysis/e1.json"), J("sim/analysis/e1_curve.json")

# Survey counts that analyze.py does not write out: recount them from the codes, with the same rules.
import os
os.chdir(ROOT / "study")
from load import load
ov = {k: v for k, v in json.load(open("overrides.json")).items() if not k.startswith("_")}
val = lambda d, k: ov.get(k, {}).get(d["id"], d["criteria"].get(k, {}).get("value"))
D = load("ABCDE")
exp = [d for d in D.values() if val(d, "Q1") != "no"]
rl = [d for d in exp if val(d, "X5") != "theory"]
seeds = [val(d, "X1") for d in rl]
llm = [d for d in exp if val(d, "X5") == "llm"]
classic = [d for d in exp if val(d, "X5") == "classic"]
yes = lambda ds, k: sum(val(d, k) == "yes" for d in ds)
applicable = lambda ds, k: sum(val(d, k) in ("yes", "no") for d in ds)


def half_up(x, nd=0):
    """Round half away from zero, as a reader does: 1.15 -> 1.2, -66.5 -> -67 (Python's round is to even)."""
    q = Decimal(1).scaleb(-nd)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def pct(x, nd=0, lang="fr"):
    s = str(half_up(Decimal(str(x)) * 100, nd))
    return (s.replace(".", ",") + " %") if lang == "fr" else s + "%"


def num(x, lang="fr"):
    s = f"{int(half_up(x)):,}"
    return s.replace(",", " ") if lang == "fr" else s


def ci(lo, hi, lang="fr"):
    return f"[{int(half_up(Decimal(str(lo)) * 100))}, {int(half_up(Decimal(str(hi)) * 100))}]"


def pts(t, lang="fr"):
    lo, hi = int(half_up(Decimal(str(t["lo"])) * 100)), int(half_up(Decimal(str(t["hi"])) * 100))
    m = "−" if lang == "fr" else "−"
    f = lambda v: f"{m}{abs(v)}" if v < 0 else (f"+{v}" if lang == "fr" else f"+{v}")
    return f(lo), f(hi)


# (description, French string, English string). Each string is built from the data, never typed by hand.
C = []
add = lambda d, fr, en: C.append((d, fr, en))
FR_WORDS = {1: "Un", 2: "Deux", 3: "Trois", 4: "Quatre", 5: "Cinq", 15: "Quinze", 16: "Seize", 17: "Dix-sept"}
EN_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen"}
fr_low = {3: "trois", 4: "quatre", 5: "cinq", 6: "six"}
for k in ("Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X4", "X7"):
    r = res[k]
    p26, (lo, hi) = r["y2026"] / r["n2026"], audit[k]["wilson2026"]  # exact k/n, full-precision Wilson bounds
    add(f"{k} 2026 with Wilson CI", f"{pct(p26)} {ci(lo, hi)}", f"{pct(p26, lang='en')} {ci(lo, hi)}")
add("experimental papers 2026", f"{len(exp)} articles expérimentaux", f"{len(exp)} experimental papers")
silent, single = sum(s is None for s in seeds), sum(s == 1 for s in seeds)
med = int(statistics.median([s for s in seeds if s]))
add("RL papers silent on runs", f"Sur {len(rl)} articles de RL expérimentaux de 2026, {silent} ne disent pas",
    f"{len(rl)} experimental RL papers from 2026, {silent}")
add("papers with a single run", f"{FR_WORDS[single]} n'en ont qu'un", f"{EN_WORDS[single]} have only one")
add("median runs", f"médiane des autres est {fr_low[med]}", f"median among the others is {['zero','one','two','three','four','five','six'][med]}")
add("Q7 llm", f"{yes(llm, 'Q7')} articles sur {applicable(llm, 'Q7')}", f"{yes(llm, 'Q7')} papers out of {applicable(llm, 'Q7')}")
add("Q7 classic", f"{yes(classic, 'Q7')} articles sur {applicable(classic, 'Q7')}", f"{yes(classic, 'Q7')} papers out of {applicable(classic, 'Q7')}")
add("X2 classic", f"{yes(classic, 'X2')} articles sur {applicable(classic, 'X2')}", f"{yes(classic, 'X2')} papers out of {applicable(classic, 'X2')}")
add("X2 llm", f"({yes(llm, 'X2')} sur {applicable(llm, 'X2')})", f"({yes(llm, 'X2')} out of {applicable(llm, 'X2')})")
add("X3 visible", f"{yes(exp, 'X3')} articles sur {applicable(exp, 'X3')}", f"{yes(exp, 'X3')} papers out of {applicable(exp, 'X3')}")
one_family = sum(val(d, "X6") == 1 for d in llm)
add("llm papers with one model family", f"{FR_WORDS[one_family]} articles sur {len(llm)} n'essaient",
    f"{EN_WORDS[one_family]} papers out of {len(llm)} try")
CRIT13 = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X3", "X4", "X7", "X5")
same, total = sum(agree[k]["same"] for k in CRIT13), sum(agree[k]["n"] for k in CRIT13)
add("agreement", f"{same} décisions sur {total} ({pct(same / total)})", f"{same} decisions out of {total} ({pct(same / total, lang='en')})")
kap = [a["kappa"] for a in agree.values() if a["kappa"] is not None]
add("kappa range", f"de {min(kap):.2f} à {max(kap):.0f}".replace(".", ","), f"from {min(kap):.2f} to {max(kap):.0f}")
# Audit: differences with Newcombe intervals.
t = audit["Q7"]["vs_pineau"]; d = pts(t)
add("Q7 vs Pineau", f"écart de {int(half_up(Decimal(str(t['diff'])) * 100))} points, de {d[0].lstrip('+')} à {d[1].lstrip('+')}",
    f"gap of {int(half_up(Decimal(str(t['diff'])) * 100))} points, from {d[0].lstrip('+')} to {d[1].lstrip('+')}")
t = audit["Q6"]["vs_pineau"]; d = pts(t)
add("Q6 vs Pineau", f"+{int(half_up(Decimal(str(t['diff'])) * 100))} points, avec un intervalle de {d[0]} à {d[1]}",
    f"+{int(half_up(Decimal(str(t['diff'])) * 100))} points, with an interval from {d[0]} to {d[1]}")
t = audit["Q4"]["classic_vs_ours2018"]; d = pts(t)
add("Q4 classic vs ours", f"de {d[0]} à {d[1]} points", f"from {d[0]} to {d[1]} points")
t = audit["Q4"]["vs_ours2018"]
add("Q4 vs ours", f"(−{abs(int(half_up(Decimal(str(t['diff'])) * 100)))} points contre elle)",
    f"(−{abs(int(half_up(Decimal(str(t['diff'])) * 100)))} points against that reading)")
# E1, final scores.
add("E1 mean, sd, median", f"Moyenne {num(e1['mean'])}, écart type {num(e1['sd'])}, médiane {num(e1['median'])}",
    f"Mean {num(e1['mean'], 'en')}, standard deviation {num(e1['sd'], 'en')}, median {num(e1['median'], 'en')}")
add("E1 cv", f"L'écart type vaut {pct(e1['cv'])} de la moyenne", f"The standard deviation equals {pct(e1['cv'], lang='en')} of the mean")
sh = f"{e1['shapiro_p']:.0e}"; mant, ex = sh.split("e-")
add("E1 shapiro", f"p = {mant} × 10^−{int(ex)}^", f"p = {mant} × 10^−{int(ex)}^")
s27 = sorted(e1["seeds_sorted"])
add("E1 27 runs range", f"entre {num(s27[0])} et {num(s27[26])}", f"between {num(s27[0], 'en')} and {num(s27[26], 'en')}")
for k, fr_lab, en_lab in (("random_3v3", "3 essais contre 3", "3 runs against 3"), ("random_5v5", "5 essais contre 5", "5 runs against 5"),
                          ("random_10v10", "10 essais contre 10", "10 runs against 10")):
    r = e1[k]
    add(f"E1 {k}", f"{fr_lab}, tirés au hasard | {pct(r['false_positive'], 1)} | {pct(r['median_gap'])} | {pct(r['p95_gap'])}",
        f"{en_lab}, drawn at random | {pct(r['false_positive'], 1, 'en')} | {pct(r['median_gap'], lang='en')} | {pct(r['p95_gap'], lang='en')}")
r = e1["extreme_5v5_of_10"]
add("E1 sorted cut", f"{pct(r['false_positive'], 1)} | {pct(r['median_gap'])}", f"{pct(r['false_positive'], 1, 'en')} | {pct(r['median_gap'], lang='en')}")
r = e1["top3_of_10"]
add("E1 top-3 inflation", f"{pct(r['inflation'])} ({num(r['mean_top3'])} contre {num(r['mean_all'])})",
    f"{pct(r['inflation'], lang='en')} ({num(r['mean_top3'], 'en')} against {num(r['mean_all'], 'en')})")
# E1, Henderson's statistic (e1_curve.py).
q_r, q_s = curve["random_5v5"]["abs_mean_t_p95"], curve["sorted_5v5"]["abs_mean_t_p95"]
add("curve p95", f"dépasse {half_up(q_r, 1)} quand les groupes sont tirés au hasard, {half_up(q_s, 1)} quand on les trie".replace(".", ","),
    f"exceeds {half_up(q_r, 1)} when the groups are drawn at random, {half_up(q_s, 1)} when")
assert curve["random_5v5"]["share_abs_mean_t_ge_9"] == 0 and curve["sorted_5v5"]["share_abs_mean_t_ge_9"] == 0

norm = lambda s: re.sub(r"\s+", " ", s)
bad = 0
for name, lang in (("conclusions.md", 0), ("conclusions-en.md", 1)):
    p = ROOT / "docs" / name
    if not p.exists():
        continue
    text = norm(p.read_text())
    for c in C:
        want = norm(c[1 + lang])
        if want and want not in text:
            print(f"{name}: missing [{c[0]}] {want!r}")
            bad += 1
print(f"{len(C)} claims checked, {bad} missing")
sys.exit(1 if bad else 0)
