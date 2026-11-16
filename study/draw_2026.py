"""The 2026 draw (PROTOCOL.md, section Tirage): random.Random(2018), then 17 papers of ICLR 2026, 17 of ICML 2026 and
16 of NeurIPS 2025, in that order, each drawn with sample() from that venue's RL papers in rl_population_2026.json
(listing order). Recomputes the draw and checks that sample_2026.json holds the same papers in the same order (the
committed file adds the ids and the PDF addresses). Run from study/: python3 draw_2026.py  (exit code 1 if it differs)
"""
import json, random, sys

DRAW = (("ICLR 2026", 17), ("ICML 2026", 17), ("NeurIPS 2025", 16))


def draw(population, seed=2018):
    r = random.Random(seed)
    return [p for venue, n in DRAW for p in r.sample([p for p in population if p["venue"] == venue], n)]


if __name__ == "__main__":
    got = draw(json.load(open("rl_population_2026.json")))
    committed = json.load(open("sample_2026.json"))
    same = [(a["venue"], a["title"], a["url"]) == (b["venue"], b["title"], b["url"]) for a, b in zip(got, committed)]
    print(f"{sum(same)} of {len(committed)} papers drawn again, in the same order")
    sys.exit(0 if len(got) == len(committed) and all(same) else 1)
