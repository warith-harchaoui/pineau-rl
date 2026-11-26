"""Builds the blog figures of the article, in French and in English, from the project's result files.

Every number drawn here is read from a result file of the project, never typed by hand:
    sim/analysis/e1.json, e1_curve.json, b1_trpo.json, b1_script.json   (E1, B1: thirty runs, the t of 9)
    sim/analysis/e2.json, e4.json, e7_rank.json                          (E2, E4, E7: four algorithms, four tasks)
    sim/analysis/dose.json                                               (E7 at several strengths, one quantity at a time)
    study/extension_stats.json, study/trajectory.json                   (the survey, same grid, year by year)
    sim/llm/results/summary.json                                         (GRPO, true and coin-flip reward)
    docs/figures/data/grpo_truncation_{fr,en}.csv                        (counted by docs/figures/build.py from
                                                                          sim/llm/diag/replay_batch.json)
Run from anywhere, CPU-light:  nice python3 article/figures/build.py [name ...]
Writes data/<name>_<lang>.csv, then <name>-fr.svg and <name>-en.svg, and runs `sprezzature-figures check` on each.
The technical report draws the same figures in its own fonts, into its own directory, desktop width only:
    DRAW_FONTS=latex python3 article/figures/build.py --out DIR --data DIR2
(--out: where the SVGs go, phone versions skipped; --data: where the CSVs go, default data/ here). Without these
options: the blog's figures, in Latin Modern like the report's (draw.py's default), next to this file.
"""
import argparse, csv, json, re, subprocess, sys

import draw
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_ap = argparse.ArgumentParser(description="Blog figures of the article (and the report's, with --out).")
_ap.add_argument("names", nargs="*", help="figures to draw (default: all)")
_ap.add_argument("--out", type=Path, help="write the SVGs here, desktop versions only (default: here, both widths)")
_ap.add_argument("--data", type=Path, help="write the CSVs here (default: data/ here)")
ARGS = _ap.parse_args() if __name__ == "__main__" else _ap.parse_args([])
OUT = (ARGS.out or HERE).resolve()
DATA = (ARGS.data or HERE / "data").resolve()
DATA.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
J = lambda p: json.load(open(ROOT / p))
# The blog speaks in the first person singular, the report in the plural (Warith, 2026-11-22).
BLOG = ARGS.out is None
MY_FR, MY_EN = ("mon", "my") if BLOG else ("notre", "our")
MES_FR, MES_EN = ("mes", "my") if BLOG else ("nos", "our")


def r(x, nd=0):
    """Round half away from zero, as a reader does."""
    q = Decimal(1).scaleb(-nd)
    v = Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)
    return int(v) if nd == 0 else float(v)


def write(name, header, rows):
    with open(DATA / f"{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return DATA / f"{name}.csv"


LANGS = ("fr", "en")
ALGO = {"fr": {"ppo_sb3": "PPO (PyTorch)", "ppo_sbx": "PPO (JAX)", "sac": "SAC", "crossq": "CrossQ"},
        "en": {"ppo_sb3": "PPO (PyTorch)", "ppo_sbx": "PPO (JAX)", "sac": "SAC", "crossq": "CrossQ"}}
TASKS = ["HalfCheetah-v5", "Hopper-v5", "Walker2d-v5", "Swimmer-v5"]
TASK = lambda t: t.replace("-v5", "")
ALGOS = ["sac", "crossq", "ppo_sb3", "ppo_sbx"]

FIGS = {}  # name -> {lang: (kind, csv, [options])}

# 1. E1: thirty runs of the same program, one dot each.
e1 = J("sim/analysis/e1.json")
for lang in LANGS:
    csvp = write(f"e1_graines_{lang}", ["group", "value"], [("PPO", r(v)) for v in e1["seeds_sorted"]])
    FIGS.setdefault("e1-graines", {})[lang] = ("beeswarm", csvp, {
        "fr": ["--title", "Même programme, trente graines aléatoires",
               "--set", "subtitle=PPO sur HalfCheetah, score final après un million de pas, un point par essai",
               "--set", "y_axis_title=Score final (plus haut est mieux)", "--set", "language=fr",
               "--set", "width=760", "--set", "height=330"],
        "en": ["--title", "Same program, thirty random seeds",
               "--set", "subtitle=PPO on HalfCheetah, final score after one million steps, one dot per run",
               "--set", "y_axis_title=Final score (higher is better)",
               "--set", "width=760", "--set", "height=330"]}[lang])

# 2. E1: how often a statistical test declares two groups of the same program different.
FP_KEYS = ("random_3v3", "random_5v5", "random_10v10", "extreme_5v5_of_10")
FP_LAB = {"fr": ["3 contre 3, au hasard", "5 contre 5, au hasard", "10 contre 10, au hasard",
                 "5 meilleurs contre 5 pires"],
          "en": ["3 vs 3, at random", "5 vs 5, at random", "10 vs 10, at random", "5 best vs 5 worst"]}
for lang in LANGS:
    csvp = write(f"e1_faux_positifs_{lang}", ["region", "value"],
                 [(lab, r(e1[k]["false_positive"] * 100, 1)) for lab, k in zip(FP_LAB[lang], FP_KEYS)])
    FIGS.setdefault("e1-faux-positifs", {})[lang] = ("bar", csvp, {
        "fr": ["--title", "Le hasard trompe rarement le test, le tri le trompe",
               "--set", "subtitle=10 000 tirages de deux groupes d'essais du même programme : part déclarée différente (Welch, p < 0,05)",
               "--set", "x_label=Façon de former les deux groupes",
               "--set", "y_label=Faux positifs (%, plus bas est mieux)", "--set", "language=fr",
               "--set", "width=760", "--set", "height=440"],
        "en": ["--title", "Chance rarely fools the test, sorting does",
               "--set", "subtitle=10,000 draws of two groups of runs of the same program: share declared different (Welch, p < 0.05)",
               "--set", "x_label=How the two groups are formed",
               "--set", "y_label=False positives (%, lower is better)",
               "--set", "width=760", "--set", "height=440"]}[lang])

# 3. The t of 9: share of random draws (two groups of five) whose mean t reaches Henderson's 9.09.
curve, b1, b1s = J("sim/analysis/e1_curve.json"), J("sim/analysis/b1_trpo.json"), J("sim/analysis/b1_script.json")
T9 = [("PPO", f"{MY_FR} calcul", f"{MY_EN} computation", curve["random_5v5"]["share_abs_mean_t_ge_9"]),
      ("TRPO", f"{MY_FR} calcul", f"{MY_EN} computation", b1["trpo"]["random_5v5"]["mean_t"]["share_abs_t_ge_henderson"]),
      ("TRPO", "points empilés", "stacked points", b1["trpo"]["random_5v5"]["pooled"]["share_abs_t_ge_henderson"]),
      ("PPO", "script de 2017", "2017 script", b1s["ppo_sb3"]["n10"]["random_5v5"]["share_abs_t_ge_henderson"]),
      ("TRPO", "script de 2017", "2017 script", b1s["trpo"]["n10"]["random_5v5"]["share_abs_t_ge_henderson"])]
for lang in LANGS:
    csvp = write(f"t_de_neuf_{lang}", ["region", "value"],
                 [(f"{a}, {fr if lang == 'fr' else en}", r(v * 100)) for a, fr, en, v in T9])
    FIGS.setdefault("t-de-neuf", {})[lang] = ("bar", csvp, {
        "fr": ["--title", "Seul le script de 2017 retrouve le t de 9",
               "--set", "subtitle=10 000 tirages au hasard de deux groupes de cinq essais : part où le t moyen atteint 9,09",
               "--set", "x_label=Algorithme et façon de calculer le t",
               "--set", "y_label=Tirages qui atteignent 9,09 (%)", "--set", "language=fr",
               "--set", "width=760", "--set", "height=440"],
        "en": ["--title", "Only the 2017 script finds the t of 9",
               "--set", "subtitle=10,000 random draws of two groups of five runs: share where the mean t reaches 9.09",
               "--set", "x_label=Algorithm and way of computing t",
               "--set", "y_label=Draws reaching 9.09 (%)",
               "--set", "width=760", "--set", "height=440"]}[lang])

# 4. E4: inflation of the mean when only the best three runs of ten are kept, per algorithm and task.
e4 = J("sim/analysis/e4.json")["cells"]
for lang in LANGS:
    csvp = write(f"meilleurs_sur_dix_{lang}", ["period", "region", "v"],
                 [(TASK(t), ALGO[lang][a], r(e4[f"{a}/{t}"]["inflation"] * 100)) for t in TASKS for a in ALGOS])
    FIGS.setdefault("meilleurs-sur-dix", {})[lang] = ("bar-grouped", csvp, {
        "fr": ["--title", "Garder les 3 meilleurs sur 10 gonfle tout",
               "--set", "subtitle=Hausse de la moyenne, en %, quand on ne garde que les trois meilleurs des dix essais",
               "--set", "language=fr", "--set", "width=760", "--set", "height=460"],
        "en": ["--title", "Keeping the best 3 of 10 inflates everything",
               "--set", "subtitle=Rise of the mean, in %, when only the best three of the ten runs are kept",
               "--set", "width=760", "--set", "height=460"]}[lang])

# 5. E2: each algorithm's score as a share of the best on its task (100 = leader).
e2 = J("sim/analysis/e2.json")["tasks"]
for lang in LANGS:
    rows = []
    for a in ALGOS:
        for t in TASKS:
            iqm = e2[t]["iqm"]
            rows.append((TASK(t), ALGO[lang][a], r(iqm[a] / max(iqm.values()) * 100)))
    rows.sort(key=lambda x: TASKS.index(x[0] + "-v5"))
    csvp = write(f"classement_taches_{lang}", ["period", "region", "v"], rows)
    FIGS.setdefault("classement-taches", {})[lang] = ("bar-grouped", csvp, {
        "fr": ["--title", "Le premier change avec la tâche",
               "--set", "subtitle=Score de dix graines aléatoires, en % du meilleur de chaque tâche (100 = en tête)",
               "--set", "language=fr", "--set", "width=760", "--set", "height=460"],
        "en": ["--title", "The leader changes with the task",
               "--set", "subtitle=Score over ten random seeds, as a % of the best on each task (100 = leader)",
               "--set", "width=760", "--set", "height=460"]}[lang])

# 6. E7: Hopper, training physics against modified physics (masses x1.2, friction x0.8).
e7 = J("sim/analysis/e7_rank.json")["Hopper-v5"]["iqm"]
PER = {"fr": ("Physique d'entraînement", "Physique modifiée"), "en": ("Training physics", "Modified physics")}
for lang in LANGS:
    rows = []
    for a in ALGOS:
        rows.append((PER[lang][0], ALGO[lang][a], r(e7["eval_mean"][a])))
        rows.append((PER[lang][1], ALGO[lang][a], r(e7["perturbed_mean"][a])))
    csvp = write(f"physique_modifiee_{lang}", ["quarter", "product", "share"], rows)
    FIGS.setdefault("physique-modifiee", {})[lang] = ("bump", csvp, {
        "fr": ["--title", "Sur Hopper, le premier finit dernier",
               "--set", "subtitle=Rang de quatre programmes et leur score sur dix graines aléatoires",
               "--set", "rank_note=Physique modifiée : masses alourdies de 20 %, frottements réduits de 20 %",
               "--set", "finding=PPO (JAX), premier à l'entraînement, finit dernier ; CrossQ prend la tête.",
               "--set", "rank_label=Rang (1 en haut)", "--set", "x_label=",
               "--set", "tie_within=0", "--set", "width=760", "--set", "height=400"],
        "en": ["--title", "On Hopper, the leader ends last",
               "--set", "subtitle=Rank of four programs and their score over ten random seeds",
               "--set", "rank_note=Modified physics: masses 20% heavier, friction 20% lower",
               "--set", "finding=PPO (JAX), first in training, ends last; CrossQ takes the lead.",
               "--set", "rank_label=Rank (1 at the top)", "--set", "x_label=",
               "--set", "tie_within=0", "--set", "width=760", "--set", "height=400"]}[lang])

# 7. The survey with the same grid: classical RL of 2026 against our own reading of 2018, gap and Newcombe interval.
ext = {x["k"]: x for x in J("study/extension_stats.json")["rows"]}
CRIT = {"fr": {"Q5": "Code en lien", "Y9": "Effet d'un réglage", "X7": "Calcul chiffré", "X2": "Incertitude",
               "Q7": "Évaluation à part", "Q8": "Test statistique", "Y7": "Version des bancs",
               "Q4": "Réglages des références"},
        "en": {"Q5": "Code linked", "Y9": "Effect of a setting", "X7": "Compute stated", "X2": "Uncertainty",
               "Q7": "Held-out evaluation", "Q8": "Statistical test", "Y7": "Benchmark version",
               "Q4": "Baseline settings"}}
for lang in LANGS:
    keys = sorted(CRIT[lang], key=lambda k: -ext[k]["classic_vs_ours2018"]["diff"])
    pts = lambda t: (r(t["diff"] * 100), r(t["lo"] * 100), r(t["hi"] * 100))
    csvp = write(f"grille_egale_{lang}", ["g", "mean", "lo", "hi"],
                 [(CRIT[lang][k], *pts(ext[k]["classic_vs_ours2018"])) for k in keys])
    FIGS.setdefault("grille-egale", {})[lang] = ("errorbar", csvp, {
        "fr": ["--title", "À grille égale, quatre pratiques ont changé",
               "--set", f"subtitle=50 articles de RL classique de 2026 contre {MES_FR} 50 de 2018 ; barre : intervalle à 95 %",
               "--set", "y_axis_title=Écart en points (2026 moins 2018)",
               "--set", "x_axis_title=Pratique relevée dans l'article",
               "--set", "width=820", "--set", "height=460"],
        "en": ["--title", "With the same grid, four practices changed",
               "--set", f"subtitle=50 classical RL papers from 2026 against {MES_EN} 50 from 2018; bar: 95% interval",
               "--set", "y_axis_title=Gap in points (2026 minus 2018)",
               "--set", "x_axis_title=Practice found in the paper",
               "--set", "width=820", "--set", "height=460"]}[lang])

# 8. The trajectory, 2018 to 2026, 20 papers a year in between.
traj = J("study/trajectory.json")["rows"]
TCRIT = ["Q5", "Y9", "X7", "X2", "Q8"]
for lang in LANGS:
    rows = []
    for k in TCRIT:
        for y, v in sorted(traj[k]["by_year"].items()):
            rows.append((CRIT[lang][k], int(y), r(v["k"] / v["n"] * 100)))
    csvp = write(f"trajectoire_{lang}", ["hour", "platform", "sessions"], [(y, c, v) for c, y, v in rows])
    axis = ["--set", "y_domain=0,100", "--set", "y_tick_step=25", "--set", "x_tick_step=2",
            "--set", "width=760", "--set", "height=460",
            "--set", f"series_colors={CRIT[lang]['Q8']}=#8E8E93"]
    FIGS.setdefault("trajectoire", {})[lang] = ("line-multi", csvp, {
        "fr": ["--title", "Une montée lente, sans saut après 2019",
               "--set", "subtitle=Part des articles de RL classique qui suivent la pratique, de 2018 à 2026",
               "--set", "y_label=Part des articles (%)", "--set", "x_label=Année de publication", *axis],
        "en": ["--title", "A slow climb, with no jump after 2019",
               "--set", "subtitle=Share of classical RL papers that follow the practice, from 2018 to 2026",
               "--set", "y_label=Share of papers (%)", "--set", "x_label=Year of publication", *axis]}[lang])

# 9. GRPO: success at the first attempt, at the start and after 100 steps, per run, five random seeds
# (sim/llm/results/summary_5.json; the run that failed twice is drawn as a failure, from extra_5.json).
summ = J("sim/llm/results/summary_5.json")
failed = {(x["model"], x["reward"], x["seed"]) for x in J("sim/llm/results/extra_5.json")["failed"]}
MOD = {"qwen05": "Qwen", "llama1": "Llama"}
REW = {"fr": {"true": "vraie récompense", "random": "pile ou face"},
       "en": {"true": "true reward", "random": "coin flip"}}
DEV = {"mps": "GPU", "cuda": "GPU", "cpu": "CPU"}
for lang in LANGS:
    rows = []
    for m in ("qwen05", "llama1"):
        for rw in ("true", "random"):
            runs = {s["seed"]: s for s in summ if s["model"] == m and s["reward"] == rw}
            for seed in range(5):
                if seed in runs:
                    s = runs[seed]
                    rows.append((f"{MOD[m]}, {REW[lang][rw]}", seed, r(s["pass1_100"] * 100), r(s["pass1_0"] * 100),
                                 DEV[s["device"]]))
                else:
                    assert (m, rw, seed) in failed, (m, rw, seed)
                    rows.append((f"{MOD[m]}, {REW[lang][rw]}", seed, "", "", "failed"))
    csvp = write(f"grpo_graines_{lang}", ["group", "seed", "pass1_100", "pass1_0", "device"], rows)
    FIGS.setdefault("grpo-graines", {})[lang] = ("dumbbell", csvp, {
        "fr": ["--title", "Pile ou face fait tomber la réussite à zéro",
               "--set", "subtitle=Problèmes réussis au premier essai, au départ puis après 100 pas, cinq graines aléatoires par modèle et par récompense"],
        "en": ["--title", "A coin flip drives success down to zero",
               "--set", "subtitle=Problems solved at the first attempt, at the start and after 100 steps, five random seeds per model and reward"]}[lang])

# 10. GRPO: the base model's answers on the pilot's step-10 batch, cut at 160 tokens or complete.
for lang in LANGS:
    src = list(csv.DictReader(open(ROOT / f"docs/figures/data/grpo_truncation_{lang}.csv")))
    csvp = write(f"grpo_coupure_{lang}", ["quarter", "type", "share"],
                 [(x["quarter"], x["type"], int(x["share"])) for x in src])
    FIGS.setdefault("grpo-coupure", {})[lang] = ("stacked-bar", csvp, {
        "fr": ["--title", "Le modèle de départ ne finit pas ses réponses",
               "--set", "subtitle=Qwen2.5 de 0,5 milliard de paramètres, 8 réponses tirées par problème de multiplication",
               "--set", "y_axis_title=Part des 8 réponses", "--set", "x_axis_title=Problème posé",
               "--set", "width=700", "--set", "height=440"],
        "en": ["--title", "The base model does not finish its answers",
               "--set", "subtitle=Qwen2.5 with 0.5 billion parameters, 8 answers sampled per multiplication problem",
               "--set", "y_axis_title=Share of the 8 answers", "--set", "x_axis_title=Problem asked",
               "--set", "width=700", "--set", "height=440"]}[lang])

# 11. E7 at several strengths (sim/analysis/dose.json): how many of the 16 algorithm-task pairs lose a detectable
# share of their score when one quantity of the physics changes. x is the change in %, 0 being the training physics,
# where every ratio equals 1 by construction and no loss is possible.
dose = J("sim/analysis/dose.json")
assert dose["missing"] == {} and dose["control_max_rel_gap"] == 0
DOSE_Q = {"fr": {"mass": "Masses", "friction": "Frottements"}, "en": {"mass": "Masses", "friction": "Friction"}}
dose_loss = {}
for k, v in dose["ratio"].items():
    a, t, q, s = k.split("/")
    dose_loss.setdefault((q, s), []).append(v["verdict"] == "loss")
assert all(len(v) == len(ALGOS) * len(TASKS) for v in dose_loss.values())
for lang in LANGS:
    rows = []
    for q in ("mass", "friction"):
        pts = sorted((r((float(s) - 1) * 100), sum(v)) for (qq, s), v in dose_loss.items() if qq == q)
        pts = sorted(pts + [(0, 0)])  # the training physics itself: the reference, no loss by construction
        rows += [(x, DOSE_Q[lang][q], n) for x, n in pts]
    csvp = write(f"intensites_{lang}", ["hour", "platform", "sessions"], rows)
    axis = ["--set", "y_domain=0,16", "--set", "y_tick_step=4", "--set", "x_tick_step=10",
            "--set", "width=760", "--set", "height=460", "--set", "right_margin=40"]
    FIGS.setdefault("intensites", {})[lang] = ("line-multi", csvp, {
        "fr": ["--title", "Plus la physique s'écarte, plus les agents perdent",
               "--set", "subtitle=Sur 16 couples de programme et de tâche, combien perdent une part détectable de leur score",
               "--set", "y_label=Couples qui perdent (sur 16, plus bas est mieux)",
               "--set", "x_label=Écart à la physique d'entraînement (%)", *axis],
        "en": ["--title", "The further the physics moves, the more agents lose",
               "--set", "subtitle=Out of 16 pairs of program and task, how many lose a detectable share of their score",
               "--set", "y_label=Pairs that lose (out of 16, lower is better)",
               "--set", "x_label=Change from the training physics (%)", *axis]}[lang])

# Narrow variants for phones: the same data and the same message, drawn for a column of about 400 px.
# Shorter titles and labels, a canvas 400 px wide and taller, so the type stays near its printed size.
CRIT_M = {"fr": {"Q5": "Code", "Y9": "Réglage", "X7": "Calcul", "X2": "Incertitude", "Q7": "Tenue à part",
                 "Q8": "Test", "Y7": "Versions", "Q4": "Réf. réglées"},
          "en": {"Q5": "Code", "Y9": "Setting", "X7": "Compute", "X2": "Uncertainty", "Q7": "Held-out",
                 "Q8": "Test", "Y7": "Versions", "Q4": "Baselines"}}
MOB = {  # name -> lang -> (title, subtitle, width, height, relabel, extra options)
    "e1-graines": {
        "fr": ("30 graines aléatoires", "PPO sur HalfCheetah, un point par essai", 400, 300, {},
               ["--set", "y_axis_title=Score final"]),
        "en": ("30 random seeds", "PPO on HalfCheetah, one dot per run", 400, 300, {},
               ["--set", "y_axis_title=Final score"])},
    "e1-faux-positifs": {
        "fr": ("Trier trompe le test", "Groupes déclarés différents, même code", 400, 460,
               dict(zip(FP_LAB["fr"], ["Hasard 3/3", "Hasard 5/5", "Hasard 10/10", "Triés 5/5"])), []),
        "en": ("Sorting fools the test", "Groups declared different, same code", 400, 460,
               dict(zip(FP_LAB["en"], ["Random 3/3", "Random 5/5", "Random 10/10", "Sorted 5/5"])), [])},
    "t-de-neuf": {
        "fr": ("Seul le script atteint 9", "Tirages au hasard où le t moyen atteint 9,09", 400, 460,
               {"PPO, mon calcul": "PPO, moi", "TRPO, mon calcul": "TRPO, moi", "TRPO, points empilés": "TRPO, empilés",
                "PPO, script de 2017": "PPO, script", "TRPO, script de 2017": "TRPO, script"}, []),
        "en": ("Only the script reaches 9", "Random draws where the mean t reaches 9.09", 400, 460,
               {"PPO, my computation": "PPO, mine", "TRPO, my computation": "TRPO, mine", "TRPO, stacked points": "TRPO, stacked",
                "PPO, 2017 script": "PPO, script", "TRPO, 2017 script": "TRPO, script"}, [])},
    "meilleurs-sur-dix": {
        "fr": ("3 sur 10 gonflent tout", "Hausse de la moyenne, trois meilleurs essais sur dix", 400, 520, {}, []),
        "en": ("Best 3 of 10 inflate all", "Rise of the mean, best three runs of ten", 400, 520, {}, [])},
    "classement-taches": {
        "fr": ("Le premier change", "Score en % du meilleur de chaque tâche", 400, 520, {}, []),
        "en": ("The leader changes", "Score as a % of the best on each task", 400, 520, {}, [])},
    "physique-modifiee": {
        "fr": ("Hopper : le premier tombe", "Rang avant et après une physique modifiée", 400, 400,
               {"Physique d'entraînement": "Entraînement", "Physique modifiée": "Modifiée"},
               ["--set", "rank_note=Masses +20 %, frottements −20 %", "--set", "finding=PPO (JAX) passe de premier à dernier."]),
        "en": ("Hopper: the leader falls", "Rank before and after modified physics", 400, 400,
               {"Training physics": "Training", "Modified physics": "Modified"},
               ["--set", "rank_note=Masses +20%, friction −20%", "--set", "finding=PPO (JAX) goes from first to last."])},
    "grille-egale": {
        "fr": ("Quatre pratiques ont changé", "Écart 2026 moins 2018, intervalle à 95 %", 400, 440,
               {v: CRIT_M["fr"][k] for k, v in CRIT["fr"].items()}, ["--set", "x_axis_title=Pratique", "--set", "y_axis_title=Écart (points)"]),
        "en": ("Four practices changed", "Gap 2026 minus 2018, 95% interval", 400, 440,
               {v: CRIT_M["en"][k] for k, v in CRIT["en"].items()}, ["--set", "x_axis_title=Practice", "--set", "y_axis_title=Gap (points)"])},
    "trajectoire": {
        "fr": ("Une montée lente", "Part des articles de RL classique", 400, 520,
               {"Effet d'un réglage": "Réglage", "Calcul chiffré": "Calcul", "Code en lien": "Code", "Test statistique": "Test"},
               ["--set", "x_tick_step=4", "--set", "x_label=Année", "--set", "series_colors=Test=#8E8E93"]),
        "en": ("A slow climb", "Share of classical RL papers", 400, 520,
               {"Effect of a setting": "Setting", "Compute stated": "Compute", "Code linked": "Code", "Statistical test": "Test"},
               ["--set", "x_tick_step=4", "--set", "x_label=Year", "--set", "series_colors=Test=#8E8E93"])},
    "grpo-graines": {
        "fr": ("Pile ou face : zéro", "Réussite au départ et après 100 pas", 400, 520,
               {}, []),
        "en": ("Coin flip: down to zero", "Success at the start and after 100 steps", 400, 520,
               {}, [])},
    "grpo-coupure": {
        "fr": ("Des réponses coupées", "Qwen2.5 de 0,5 milliard, 8 réponses par problème", 400, 500,
               {"Complète et juste": "Juste", "Complète et fausse": "Fausse", "Coupée à 160 jetons": "Coupée"},
               ["--set", "x_axis_title=Problème"]),
        "en": ("Answers cut short", "Qwen2.5 with 0.5 billion, 8 answers per problem", 400, 500,
               {"Complete and right": "Right", "Complete and wrong": "Wrong", "Cut at 160 tokens": "Cut"},
               ["--set", "x_axis_title=Problem"])},
    "intensites": {
        "fr": ("Plus d'écart, plus de pertes", "Couples qui perdent, sur 16, une grandeur à la fois", 400, 480, {},
               ["--set", "x_tick_step=20", "--set", "x_label=Écart à l'entraînement (%)", "--set", "y_label=Couples qui perdent"]),
        "en": ("More change, more loss", "Pairs that lose, out of 16, one quantity at a time", 400, 480, {},
               ["--set", "x_tick_step=20", "--set", "x_label=Change from training (%)", "--set", "y_label=Pairs that lose"])},
}


def mobile_spec(name, lang, kind, csvp, opts):
    title, sub, w, h, relabel, extra = MOB[name][lang]
    rows = list(csv.reader(open(csvp)))
    out = write(f"{csvp.stem}_mobile", rows[0], [[relabel.get(c, c) for c in r] for r in rows[1:]])
    reset = {"width", "height"} | {extra[j + 1].split("=")[0] for j in range(0, len(extra), 2) if extra[j] == "--set"}
    keep, i = [], 0
    while i < len(opts):
        a, b = opts[i], opts[i + 1]
        if a == "--title":
            b = title
        elif a == "--set" and b.split("=")[0] in reset:
            i += 2
            continue
        elif a == "--set" and b.split("=")[0] in ("subtitle", "subtitle_template"):
            b = f"{b.split('=')[0]}={sub}"
        keep += [a, b]
        i += 2
    return kind, out, keep + extra + ["--set", f"width={w}", "--set", f"height={h}"]




# The words each drawing adds to the title and subtitle: notes, keys, sources. Numbers come from the files above.
def frac(x, lang):
    return draw.num(x, lang)


RANK = {"fr": lambda k: "1er" if k == 1 else f"{k}e", "en": lambda k: {1: "1st", 2: "2nd", 3: "3rd"}.get(k, f"{k}th")}
E1V = sorted(e1["seeds_sorted"])
CUT = 3000
NHI = sum(v >= CUT for v in E1V)
TRAJ_N = traj["Q5"]["by_year"]
MID = sorted(int(y) for y in TRAJ_N if y not in ("2018", "2026"))
assert all(TRAJ_N[str(y)]["n"] == TRAJ_N[str(MID[0])]["n"] for y in MID)
E4MED = r(J("sim/analysis/e4.json")["inflation_median"] * 100)
DPEAK = None


def text(name, lang):
    fr = lang == "fr"
    P = lambda x, **k: draw.pct(x, lang, **k)
    N = lambda x, **k: draw.num(x, lang, **k)
    return {
        "e1-graines": dict(
            cut=CUT, median="médiane" if fr else "median",
            note=(f"{NHI} essais sur {len(E1V)} dépassent {N(CUT)} :|même code,|autre graine" if fr
                  else f"{NHI} of {len(E1V)} runs pass {N(CUT)}:|same code,|another seed"),
            axis="Score final après un million de pas (plus haut est mieux)" if fr
            else "Final score after one million steps (higher is better)",
            source=(f"Données : {len(E1V)} entraînements de PPO (Stable-Baselines3) sur HalfCheetah, un par graine aléatoire" if fr
                    else f"Data: {len(E1V)} PPO trainings (Stable-Baselines3) on HalfCheetah, one per random seed"),
            desc=(f"Trente points sur un axe de score. {len(E1V) - NHI} essais vont de {N(E1V[0])} à {N(E1V[-NHI - 1])}, "
                  f"{NHI} dépassent {N(CUT)}, jusqu'à {N(E1V[-1])}." if fr else
                  f"Thirty dots on a score axis. {len(E1V) - NHI} runs range from {N(E1V[0])} to {N(E1V[-NHI - 1])}, "
                  f"{NHI} pass {N(CUT)}, up to {N(E1V[-1])}.")),
        "e1-faux-positifs": dict(
            ref="5 % : le risque accepté" if fr else "5%: the accepted risk",
            source="Données : 10 000 tirages parmi les 30 essais de PPO, test de Welch au seuil de 5 %" if fr
            else "Data: 10,000 draws among the 30 PPO runs, Welch test at the 5% level",
            desc="Barres horizontales : au hasard, de 1 à 2 % des tirages sont déclarés différents ; "
                 "cinq meilleurs contre cinq pires, 31 %." if fr else
                 "Horizontal bars: at random, 1 to 2% of draws are declared different; five best against five worst, 31%."),
        "t-de-neuf": dict(
            source="Données : 10 000 tirages de deux groupes de cinq essais ; 9,09 est le t publié par Henderson et al. en 2018" if fr
            else "Data: 10,000 draws of two groups of five runs; 9.09 is the t published by Henderson et al. in 2018",
            desc="Cinq barres horizontales : quatre façons de calculer donnent 0 % ; le script de 2017 sur TRPO, 38 %." if fr
            else "Five horizontal bars: four ways of computing give 0%; the 2017 script on TRPO, 38%."),
        "classement-taches": dict(
            first="1er" if fr else "1st",
            source="Données : moyenne interquartile de dix graines aléatoires, par programme et par tâche" if fr
            else "Data: interquartile mean over ten random seeds, per program and task",
            desc="Quatre panneaux, un par tâche, barres classées : SAC en tête sur HalfCheetah, PPO (JAX) sur Hopper "
                 "et Swimmer, CrossQ sur Walker2d." if fr else
                 "Four panels, one per task, sorted bars: SAC leads on HalfCheetah, PPO (JAX) on Hopper and Swimmer, "
                 "CrossQ on Walker2d."),
        "meilleurs-sur-dix": dict(
            median="médiane" if fr else "median", median_value=E4MED,
            source="Données : dix entraînements par programme et par tâche" if fr
            else "Data: ten trainings per program and task",
            desc=f"Seize barres, quatre par tâche : la moyenne gonfle de {P(6)} à {P(84)}, {P(E4MED)} en médiane." if fr
            else f"Sixteen bars, four per task: the mean inflates by {P(6)} to {P(84)}, {P(E4MED)} at the median."),
        "physique-modifiee": dict(
            hot={"PPO (JAX)", "CrossQ"}, rank=RANK[lang],
            note="Physique modifiée : masses alourdies de 20 %, frottements réduits de 20 %." if fr
            else "Modified physics: masses 20% heavier, friction 20% lower.",
            source="Données : Hopper, moyenne interquartile de dix graines aléatoires, mêmes politiques dans les deux physiques" if fr
            else "Data: Hopper, interquartile mean over ten random seeds, the same policies in both physics",
            desc="Quatre lignes du score d'entraînement au score en physique modifiée : PPO (JAX) passe de premier à dernier, "
                 "CrossQ de troisième à premier." if fr else
                 "Four lines from the training score to the score in modified physics: PPO (JAX) goes from first to last, "
                 "CrossQ from third to first."),
        "grille-egale": dict(
            better="plus fréquente en 2026" if fr else "more common in 2026",
            worse="moins fréquente" if fr else "less common",
            axis="Écart en points, 2026 moins 2018, avec son intervalle à 95 %" if fr
            else "Gap in points, 2026 minus 2018, with its 95% interval",
            source=f"Données : 50 articles de RL classique de 2026 et {MES_FR} 50 de 2018, lus avec la même grille" if fr
            else f"Data: 50 classical RL papers from 2026 and {MES_EN} 50 from 2018, read with the same grid",
            desc="Huit pratiques, un point et son intervalle : code en lien, effet d'un réglage, calcul chiffré et incertitude "
                 "progressent nettement ; les quatre autres intervalles contiennent zéro." if fr else
                 "Eight practices, a dot and its interval: code linked, effect of a setting, compute stated and uncertainty "
                 "clearly rise; the four other intervals contain zero."),
        "trajectoire": dict(
            grey=CRIT[lang]["Q8"],
            neurips="2019 : NeurIPS adopte la liste de contrôle de Pineau" if fr
            else "2019: NeurIPS adopts Pineau's checklist",
            axis="Année de publication" if fr else "Year of publication",
            source=(f"Données : {TRAJ_N['2018']['n']} articles de 2018, {TRAJ_N['2026']['n']} de 2026, "
                    f"{TRAJ_N[str(MID[0])]['n']} pour chacune des années entre les deux" if fr else
                    f"Data: {TRAJ_N['2018']['n']} papers from 2018, {TRAJ_N['2026']['n']} from 2026, "
                    f"{TRAJ_N[str(MID[0])]['n']} for each year in between"),
            desc="Cinq lignes de 2018 à 2026 : toutes montent lentement, sans saut après 2019 ; le test statistique reste "
                 "sous 25 %." if fr else
                 "Five lines from 2018 to 2026: all climb slowly, with no jump after 2019; the statistical test stays "
                 "under 25%."),
        "grpo-graines": dict(
            start="au départ" if fr else "at the start", end="après 100 pas" if fr else "after 100 steps",
            gpu="carte graphique" if fr else "GPU", cpu="processeur" if fr else "CPU",
            failed="arrêté deux fois" if fr else "stopped twice",
            source="Données : vingt entraînements GRPO de cent pas, dont un arrêté deux fois par le garde-fou des gradients" if fr
            else "Data: twenty GRPO trainings of a hundred steps, one of them stopped twice by the gradient safeguard",
            desc="Dix-neuf flèches du départ à 100 pas, une croix pour l'essai arrêté. Vraie récompense : Qwen finit "
                 "entre 0 et 61 %, Llama entre 20 et 48 %. Pile ou face : 1,25 % au plus dans les neuf essais finis." if fr else
                 "Nineteen arrows from the start to step 100, a cross for the stopped run. True reward: Qwen ends between "
                 "0 and 61%, Llama between 20 and 48%. Coin flip: 1.25% at most in all nine finished runs."),
        "grpo-coupure": dict(
            count=lambda c, t: (f"{c} sur {t}" if fr else f"{c} of {t}"),
            count_note=("réponses coupées | avant de donner un résultat, | toutes comptées fausses" if fr
                        else "answers cut | before giving a result, | all counted wrong"),
            source="Données : le lot du pas 10 du pilote, réponses du modèle de départ, coupées à 160 jetons" if fr
            else "Data: the step-10 batch of the pilot, answers of the base model, cut at 160 tokens",
            desc="Quatre rangées de huit carrés, un par réponse : la plupart sont coupées avant la fin." if fr
            else "Four rows of eight squares, one per answer: most are cut before the end."),
        "intensites": dict(
            zero="physique d'entraînement" if fr else "training physics",
            peak=lambda p: (f"{p[1]} sur 16 à {P(p[0], sign=True)}" if fr else f"{p[1]} of 16 at {P(p[0], sign=True)}"),
            yaxis="Couples qui perdent, sur 16 (plus bas est mieux)" if fr else "Pairs that lose, out of 16 (lower is better)",
            axis="Écart à la physique d'entraînement" if fr else "Change from the training physics",
            source="Données : 16 couples de programme et de tâche, dix graines aléatoires, une grandeur changée à la fois" if fr
            else "Data: 16 pairs of program and task, ten random seeds, one quantity changed at a time",
            desc="Deux lignes en V : nulle perte à la physique d'entraînement, de plus en plus de couples perdent quand "
                 "masses ou frottements s'en écartent." if fr else
                 "Two V-shaped lines: no loss at the training physics, more and more pairs lose as masses or friction "
                 "move away from it."),
    }[name]


def opt(opts, key):
    for a, b in zip(opts[::2], opts[1::2]):
        if a == "--title" and key == "title":
            return b
        if a == "--set" and b.startswith(key + "="):
            return b.split("=", 1)[1]


def render(only=None):
    bad = 0
    for name, per in FIGS.items():
        if only and name not in only:
            continue
        for lang, (kind, csvp, opts) in per.items():
            for mob in (False,) if ARGS.out else (False, True):
                if mob:
                    _, src, _ = mobile_spec(name, lang, kind, csvp, opts)
                    title, sub = MOB[name][lang][:2]
                else:
                    src, title, sub = csvp, opt(opts, "title"), opt(opts, "subtitle")
                rows = list(csv.reader(open(src)))[1:]
                svg = OUT / f"{name}{'-mobile' if mob else ''}-{lang}.svg"
                svg.write_text(draw.DRAW[name](rows, lang, mob, title, sub, text(name, lang)), encoding="utf-8")
                res = subprocess.run(["sprezzature-figures", "check", str(svg), "--expect-title", title],
                                     capture_output=True, text=True)
                bad += res.returncode != 0
                print(f"{svg.name}: {'clean' if res.returncode == 0 else 'FINDINGS'}")
                if res.returncode:
                    print(res.stdout.strip(), res.stderr.strip())
    return bad


if __name__ == "__main__":
    sys.exit(1 if render(set(ARGS.names) or None) else 0)
