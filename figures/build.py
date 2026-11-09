"""Figures de l'article « Même code, autre graine » (deraison.ai, 8 novembre 2026).
Rendu par sprezzature-figures. Données : ../sim/analysis/e1.json (30 vraies graines de PPO, E1),
Henderson et al. 2018 tableau 3 (classement), Shao et al. 2025 (récompenses).
Usage : python3 build.py  -> svg + png dans ./out/
"""
import csv, subprocess, numpy as np
from pathlib import Path
OUT = Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)

def csvw(name, header, rows):
    p = OUT / name
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    return str(p)

def render(kind, data, maps, out, **opts):
    cmd = ["sprezzature-figures", "render", kind, "--data", data, "--mode", "static", "--out", str(OUT / out)]
    for k, v in maps.items(): cmd += ["--map", f"{k}={v}"]
    for k, v in opts.items():
        cmd += [f"--{k.replace('_','-')}"] if v is True else [f"--{k.replace('_','-')}", str(v)]
    subprocess.run(cmd, check=True, capture_output=True)
    subprocess.run(["rsvg-convert", "-w", "1100", str(OUT / out), "-o", str(OUT / out.replace(".svg", ".png"))], check=True)

T = {
 "fr": dict(
   s_title="Trente graines, une seule distribution",
   s_sub="PPO sur HalfCheetah, même code, seule la graine change · 10 graines tirées, triées, coupées en deux",
   s_groups=("Les 5 pires des 10", "Les 5 meilleures des 10", "Les 30 graines"), s_y="Retour d'évaluation final (plus haut = mieux)", s_x="Ce que l'on compare",
   r_title="Le meilleur sur HalfCheetah finit dernier partout ailleurs",
   r_sub="Rang de quatre algorithmes sur quatre tâches MuJoCo · Henderson et al. (2018), tableau 3",
   r_x="Tâche MuJoCo", r_rank="Rang (1 en haut)",
   r_note="Quatre algorithmes classés par retour moyen sur chaque tâche, le meilleur en haut",
   r_find="DDPG, premier sur HalfCheetah, est dernier sur les trois autres tâches ; TRPO fait le chemin inverse.",
   e_title="Trois essais sur dix suffisent à battre la référence",
   e_sub="Retour final · la barre va du pire au meilleur essai · valeurs illustratives",
   e_groups=("Référence, 10 essais", "Ma méthode, 10 essais", "Ma méthode, 3 meilleurs"), e_y="Retour final (plus haut = mieux)", e_x="Ce qu'on publie",
   p_title="Le RL gagne au premier essai, le modèle de base au centième",
   p_sub="Part des problèmes résolus en k tentatives (pass@k) · allure d'après Yue et al. (2025), valeurs illustratives",
   p_series=("Modèle de base", "Après RL à récompense vérifiable"), p_x="Nombre de tentatives k (échelle logarithmique)", p_y="Problèmes résolus (%)",
   b_title="Une récompense tirée à pile ou face fait presque aussi bien",
   b_sub="Gain sur MATH-500 de Qwen2.5-Math-7B après RL, en points · Shao et al. (2025)",
   b_cats=("Vraie récompense", "Réponse fausse récompensée", "Récompense aléatoire"), b_x="Signal de récompense", b_y="Gain (points, plus haut = mieux)",
 ),
 "en": dict(
   s_title="Thirty seeds, one distribution",
   s_sub="PPO on HalfCheetah, same code, only the seed changes · 10 seeds drawn, sorted, split in two",
   s_groups=("Worst 5 of the 10", "Best 5 of the 10", "All 30 seeds"), s_y="Final evaluation return (higher is better)", s_x="What gets compared",
   r_title="The best on HalfCheetah comes last everywhere else",
   r_sub="Rank of four algorithms on four MuJoCo tasks · Henderson et al. (2018), table 3",
   r_x="MuJoCo task", r_rank="Rank (1 at the top)",
   r_note="Four algorithms ranked by mean return on each task, best at the top",
   r_find="DDPG, first on HalfCheetah, is last on the three other tasks; TRPO goes the opposite way.",
   e_title="Three runs out of ten are enough to beat the baseline",
   e_sub="Final return · the bar spans the worst to the best run · illustrative values",
   e_groups=("Baseline, 10 runs", "My method, 10 runs", "My method, best 3"), e_y="Final return (higher is better)", e_x="What gets published",
   p_title="RL wins on the first try, the base model on the hundredth",
   p_sub="Share of problems solved within k attempts (pass@k) · shape after Yue et al. (2025), illustrative values",
   p_series=("Base model", "After RL with verifiable rewards"), p_x="Number of attempts k (log scale)", p_y="Problems solved (%)",
   b_title="A coin-flip reward does almost as well",
   b_sub="MATH-500 gain of Qwen2.5-Math-7B after RL, in points · Shao et al. (2025)",
   b_cats=("True reward", "Wrong answer rewarded", "Random reward"), b_x="Reward signal", b_y="Gain (points, higher is better)",
 ),
}

import json
seeds30 = np.array(json.load(open(Path(__file__).parent.parent / "sim/analysis/e1.json"))["seeds_sorted"]).round().astype(int)
# The sorted 5-vs-5 cut of E1, shown on a typical draw, not an extreme one: among 1 000 draws of 10 seeds,
# the one whose gap (best 5 / worst 5 - 1) is closest to the median gap.
_rng = np.random.default_rng(2018)
_draws = [np.sort(_rng.choice(seeds30, 10, replace=False)) for _ in range(1000)]
_gaps = np.array([d[5:].mean() / d[:5].mean() - 1 for d in _draws])
ten = _draws[int(np.argmin(abs(_gaps - np.median(_gaps))))]
# Henderson et al. 2018, Table 3 (bootstrap mean)
henderson = {"HalfCheetah": {"DDPG": 5037, "ACKTR": 3888, "TRPO": 1254.5, "PPO": 3043},
             "Hopper": {"DDPG": 1632, "ACKTR": 2546, "TRPO": 2965, "PPO": 2715},
             "Walker2d": {"DDPG": 1582, "ACKTR": 2285, "TRPO": 3072, "PPO": 2926},
             "Swimmer": {"DDPG": 31, "ACKTR": 50, "TRPO": 214, "PPO": 107}}
# illustrative top-3 example (scores on a 0-70 scale, like slide 29)
base = [36, 38, 39, 41, 41, 42, 43, 44, 46, 47]
mine = [27, 31, 34, 37, 39, 41, 43, 47, 51, 54]
top3 = sorted(mine)[-3:]
ks = [1, 2, 4, 8, 16, 32, 64, 128, 256]
p_base = [12, 19, 27, 35, 43, 51, 58, 64, 69]
p_rl = [28, 34, 40, 45, 49, 52, 55, 57, 59]

for lang, t in T.items():
    g1, g2, ga = t["s_groups"]
    rows = [(g1, v) for v in ten[:5]] + [(g2, v) for v in ten[5:]] + [(ga, v) for v in seeds30]
    d = csvw(f"seeds-{lang}.csv", ["group", "value"], rows)
    render("strip", d, {}, f"rl-trente-graines-{lang}.svg", title=t["s_title"], subtitle=t["s_sub"], y_axis_title=t["s_y"], x_axis_title=t["s_x"], width=760, height=500)

    rows = [(task, algo, v) for task, dd in henderson.items() for algo, v in dd.items()]
    d = csvw(f"rank-{lang}.csv", ["quarter", "product", "share"], rows)
    render("bump", d, {}, f"rl-classement-{lang}.svg", title=t["r_title"], subtitle=t["r_sub"], x_label=t["r_x"], rank_label=t["r_rank"], rank_note=t["r_note"], finding=t["r_find"], width=900, height=560)

    def mm(v): return (round(float(np.mean(v)), 1), min(v), max(v))
    rows = [(n, *mm(v)) for n, v in zip(t["e_groups"], (base, mine, top3))]
    d = csvw(f"top3-{lang}.csv", ["g", "mean", "lo", "hi"], rows)
    render("errorbar", d, {}, f"rl-trois-sur-dix-{lang}.svg", title=t["e_title"], subtitle=t["e_sub"], y_axis_title=t["e_y"], x_axis_title=t["e_x"], width=760, height=480)

    s1, s2 = t["p_series"]
    rows = [(k, s1, v) for k, v in zip(ks, p_base)] + [(k, s2, v) for k, v in zip(ks, p_rl)]
    d = csvw(f"passk-{lang}.csv", ["hour", "platform", "sessions"], rows)
    render("line-multi", d, {}, f"rl-pass-at-k-{lang}.svg", title=t["p_title"], subtitle=t["p_sub"], x_label=t["p_x"], y_label=t["p_y"], log_x=True, width=860, height=500)

    rows = list(zip(t["b_cats"], (29.1, 24.1, 21.4)))
    d = csvw(f"spurious-{lang}.csv", ["region", "value"], rows)
    render("bar", d, {}, f"rl-recompense-aleatoire-{lang}.svg", title=t["b_title"], subtitle=t["b_sub"], x_label=t["b_x"], y_label=t["b_y"], language=lang, width=760, height=480)
print("ok", ten)

# Grille de Pineau, NeurIPS 2018, diapositive 29 (50 articles de RL de 2018)
GRID = [100, 90, 90, 60, 55, 20, 10, 5]
LBL = {"fr": ["Expériences", "Réseaux", "Réglages méthode", "Réglages références", "Code en lien", "Méthode de réglage", "Test tenu à part", "Test statistique"],
       "en": ["Experiments", "Neural nets", "Method settings", "Baseline settings", "Code linked", "Tuning method", "Held-out test", "Significance test"]}
TT = {"fr": ("En 2018, plus on approche de la preuve, moins on la trouve", "Part des 50 articles de RL de 2018 (NeurIPS, ICML, ICLR) qui cochent chaque case, % · Pineau, NeurIPS 2018", "Critère", "Articles qui le remplissent (%)"),
      "en": ("In 2018, the closer to proof, the rarer it gets", "Share of 50 RL papers from 2018 (NeurIPS, ICML, ICLR) that tick each box, % · Pineau, NeurIPS 2018", "Criterion", "Papers that meet it (%)")}
for lang in ("fr", "en"):
    d = csvw(f"grid2018-{lang}.csv", ["region", "value"], list(zip(LBL[lang], GRID)))
    a, b, c, e = TT[lang]
    render("bar", d, {}, f"rl-grille-2018-{lang}.svg", title=a, subtitle=b, x_label=c, y_label=e, language=lang, width=1000, height=500)

# 2018 contre 2026 : Pineau 2018, notre calibration 2018 (12 articles), notre mesure 2026 (50 articles)
P18 = GRID
C18 = [round(100*a/b) for a, b in [(11,12),(9,11),(6,10),(6,11),(6,11),(2,10),(4,10),(1,11)]]
N26 = [90, 89, 67, 18, 67, 27, 70, 4]
SER = {"fr": ("Pineau, 2018", "Notre relecture de 2018", "Notre mesure, 2026"),
       "en": ("Pineau, 2018", "Our re-reading of 2018", "Our measurement, 2026")}
TT2 = {"fr": ("Le tenu-à-part progresse, les références reculent, la statistique n'a pas bougé",
              "Part des articles de RL expérimentaux qui cochent chaque case, % · 2018 : 50 articles (Pineau) et 12 relus par nous ; 2026 : 50 articles tirés au hasard"),
       "en": ("Held-out testing rose, baselines fell back, statistics did not move",
              "Share of experimental RL papers that tick each box, % · 2018: 50 papers (Pineau) and 12 re-read by us; 2026: 50 papers drawn at random")}
for lang in ("fr", "en"):
    rows = []
    for i, lab in enumerate(LBL[lang]):
        for s, vals in zip(SER[lang], (P18, C18, N26)):
            rows.append((lab, s, vals[i]))
    d = csvw(f"grid2026-{lang}.csv", ["period", "region", "v"], rows)
    render("bar-grouped", d, {}, f"rl-grille-2018-2026-{lang}.svg", title=TT2[lang][0], subtitle=TT2[lang][1], language=lang, width=1100, height=560)

# bar-grouped n'expose pas ses titres d'axe : on remplace sa légende et ses axes de démonstration.
FIX = {"fr": {">Région<": ">Source<", ">Unités<": ">Articles qui cochent la case (%)<", ">Trimestre<": ">Critère<"},
       "en": {">Region<": ">Source<", ">Units<": ">Papers that tick the box (%)<", ">Quarter<": ">Criterion<"}}
for lang, rep in FIX.items():
    p = OUT / f"rl-grille-2018-2026-{lang}.svg"
    s = p.read_text(encoding="utf-8")
    for a, b in rep.items():
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8")

# Polices réduites aux glyphes employés, puis aperçus PNG.
svgs = sorted(str(p) for p in OUT.glob("rl-*.svg"))
subprocess.run(["python3", str(Path(__file__).parent / "subset_fonts.py"), *svgs], check=True, capture_output=True)
for s in svgs:
    subprocess.run(["rsvg-convert", "-w", "1100", s, "-o", s.replace(".svg", ".png")], check=True)
