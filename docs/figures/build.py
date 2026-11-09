"""Builds every figure of docs/ with sprezzature-figures, from the project's own result files.

Run with the LLM environment (it needs the Qwen tokenizer to count truncated completions):
    ../../sim/env-llm/bin/python build.py
Writes data/*.csv, then <name>.svg (Markdown) and <name>.pdf (LaTeX) for each figure.
"""
import collections, csv, json, os, subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
DATA.mkdir(exist_ok=True)


def write(name, header, rows):
    with open(DATA / f"{name}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


# Every label in both languages: <name>.svg is French (conclusions.md), <name>-en.svg is English (conclusions-en.md).
L = {
    "fr": dict(
        dumbbell=["Hyperparamètres des références", "Hyperparamètres de la méthode",
                  "Choix des hyperparamètres décrit", "Code en lien", "Évaluation tenue à part"],
        ic=["Réf. réglées", "Test signif.", "Hyperparam. réf.", "Choix hyperparam.", "Incertitude", "Calcul",
            "Code", "Tenue à part"],
        fp=["3 c. 3, au hasard", "5 c. 5, au hasard", "10 c. 10, au hasard", "5 meilleures c. 5 pires"],
        kinds=["Complète et juste", "Complète et fausse", "Coupée à 160 jetons"],
        median="Médiane globale"),
    "en": dict(
        dumbbell=["Baseline hyperparameters", "Method hyperparameters", "Tuning method described",
                  "Code linked", "Held-out evaluation"],
        ic=["Baselines tuned", "Signif. test", "Baseline hyperparams", "Tuning method", "Uncertainty",
            "Compute", "Code", "Held-out"],
        fp=["3 vs 3, random", "5 vs 5, random", "10 vs 10, random", "5 best vs 5 worst"],
        kinds=["Complete and right", "Complete and wrong", "Cut at 160 tokens"],
        median="Overall median"),
}

# Remesure (study/RESULTS.md): Pineau's 2018 figures against our 2026 sample, and our 2026 Wilson intervals.
DUMBBELL = [(60, 18), (90, 67), (20, 27), (55, 67), (10, 70)]
IC = [(5, 1, 15), (4, 1, 15), (18, 10, 32), (27, 16, 41), (47, 33, 61), (47, 33, 61), (67, 52, 79), (70, 56, 82)]
e1 = json.load(open(ROOT / "sim/analysis/e1.json"))
FP = [float(Decimal(str(e1[k]["false_positive"] * 100)).quantize(Decimal("0.1"), ROUND_HALF_UP)) for k in ("random_3v3", "random_5v5", "random_10v10", "extreme_5v5_of_10")]

# GRPO diagnostic (sim/llm/diag/replay_batch.json): base model on the pilot's step-10 batch.
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
replay = json.load(open(ROOT / "sim/llm/diag/replay_batch.json"))
count = collections.Counter()
for r in replay:
    cut = len(tok(r["text"])["input_ids"]) >= 158
    count[(r["q"], 2 if cut else 0 if r["right"] else 1)] += 1
problems = list(dict.fromkeys(r["q"] for r in replay))

for lang, l in L.items():
    write(f"remesure_dumbbell_{lang}", ["category", "group_a", "group_b"],
          [(c, a, b) for c, (a, b) in zip(l["dumbbell"], DUMBBELL)])
    write(f"remesure_ic_{lang}", ["g", "mean", "lo", "hi"], [(g, *v) for g, v in zip(l["ic"], IC)])
    write(f"e1_seeds_{lang}", ["group", "value"], [("PPO-SB3", round(v)) for v in e1["seeds_sorted"]])
    write(f"e1_false_positive_{lang}", ["region", "value"], list(zip(l["fp"], FP)))
    write(f"grpo_truncation_{lang}", ["quarter", "type", "share"],
          [(q.replace("*", " × "), l["kinds"][k], count[(q, k)]) for q in problems for k in range(3)])

# Audit (study/audit_stats.json, sim/analysis/e1_curve.json): differences with their Newcombe interval, and
# Henderson et al.'s curve statistic against what our 30 runs produce.
audit = {r["k"]: r for r in json.load(open(ROOT / "study/audit_stats.json"))["rows"]}
NAMES = {"fr": {"Q3": "Hyperparam. méthode", "Q4": "Hyperparam. réf.", "Q5": "Code", "Q6": "Choix hyperparam.",
                "Q7": "Tenue à part", "Q8": "Test signif.", "X2": "Incertitude", "X4": "Réf. réglées",
                "X7": "Calcul"},
         "en": {"Q3": "Method params", "Q4": "Baseline params", "Q5": "Code", "Q6": "Tuning method",
                "Q7": "Held-out", "Q8": "Signif. test", "X2": "Uncertainty", "X4": "Baselines tuned",
                "X7": "Compute"}}
curve = json.load(open(ROOT / "sim/analysis/e1_curve.json"))
b1 = json.load(open(ROOT / "sim/analysis/b1_trpo.json"))["trpo"]
for lang, names in NAMES.items():
    hu = lambda x: int(Decimal(str(x * 100)).quantize(Decimal("1"), ROUND_HALF_UP))
    pts = lambda t: (hu(t["diff"]), hu(t["lo"]), hu(t["hi"]))
    write(f"ecarts_pineau_{lang}", ["g", "mean", "lo", "hi"],
          [(names[k], *pts(audit[k]["vs_pineau"])) for k in ("Q3", "Q4", "Q5", "Q6", "Q7", "Q8")])
    write(f"ecarts_classique_{lang}", ["g", "mean", "lo", "hi"],
          [(names[k], *pts(audit[k]["classic_vs_ours2018"])) for k in ("Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "X2", "X4", "X7")])
    write(f"e1_henderson_{lang}", ["region", "value"], [
        ("PPO, au hasard" if lang == "fr" else "PPO, random", round(curve["random_5v5"]["abs_mean_t_p95"], 1)),
        ("PPO, triés" if lang == "fr" else "PPO, sorted", round(curve["sorted_5v5"]["abs_mean_t_p95"], 1)),
        ("TRPO, au hasard" if lang == "fr" else "TRPO, random", round(b1["random_5v5"]["mean_t"]["abs_t_p95"], 1)),
        ("TRPO, triés" if lang == "fr" else "TRPO, sorted", round(b1["sorted_5v5"]["mean_t"]["abs_t_p95"], 1)),
        ("TRPO, points empilés" if lang == "fr" else "TRPO, stacked points", round(b1["random_5v5"]["pooled"]["abs_t_p95"], 1)),
        ("Henderson 2018" if lang == "fr" else "Henderson 2018", 9.1)])

# Every figure in the academic theme (Okabe-Ito palette, serif text). FIXES are deterministic edits of the
# rendered SVG for what the kinds expose no option for; the PDF is then drawn from that same SVG.
T = {
    "fr": {
        "remesure-dumbbell": [
            "--title", "La grille de Pineau, en 2018 et en 2026",
            "--set", "subtitle_template=Part des articles expérimentaux : Pineau ({a}) contre nous ({b})",
            "--set", "axis_title=Part des articles (%, plus haut est mieux)"],
        "remesure-ic": [
            "--title", "Ce que les articles de 2026 rapportent",
            "--set", "subtitle=Part des articles expérimentaux, intervalle de Wilson à 95 %",
            "--set", "y_axis_title=Part des articles (%, plus haut est mieux)",
            "--set", "x_axis_title=Critère de la grille"],
        "e1-seeds": [
            "--title", "Même code, trente graines aléatoires",
            "--set", "subtitle=PPO-SB3 sur HalfCheetah-v5, score final à 1 M de pas, un point par essai",
            "--set", "y_axis_title=Score d'évaluation final (plus haut est mieux)", "--set", "language=fr"],
        "e1-false-positive": [
            "--title", "Trier les essais trompe le test",
            "--set", "subtitle=10 000 tirages de deux groupes du même code : part des p < 0,05 (Welch)",
            "--set", "x_label=Façon de former les deux groupes",
            "--set", "y_label=Faux positifs (%, plus bas est mieux)", "--set", "language=fr"],
        "grpo-truncation": [
            "--title", "Le modèle de départ ne finit pas ses réponses",
            "--set", "subtitle=Qwen2.5-0.5B-Instruct, lot du pas 10, 8 réponses tirées par problème",
            "--set", "y_axis_title=Part des 8 réponses", "--set", "x_axis_title=Problème"],
        "ecarts-pineau": [
            "--title", "Écart entre 2026 et les chiffres de Pineau",
            "--set", "subtitle=45 articles expérimentaux de 2026 contre ses 50 de 2018, intervalle de Newcombe à 95 %",
            "--set", "y_axis_title=Écart en points (2026 moins 2018)",
            "--set", "x_axis_title=Critère de la grille"],
        "ecarts-classique": [
            "--title", "Le RL classique seul, de 2018 à 2026",
            "--set", "subtitle=14 articles de 2026 contre nos 12 de 2018, même grille, intervalle de Newcombe à 95 %",
            "--set", "y_axis_title=Écart en points (2026 moins 2018)",
            "--set", "x_axis_title=Critère de la grille"],
        "e1-henderson": [
            "--title", "Ni PPO ni TRPO n'approchent la statistique de 2018",
            "--set", "subtitle=HalfCheetah-v5, deux groupes de 5 essais parmi 30. Nos barres : 95e centile sur 10 000 tirages",
            "--set", "x_label=Origine des essais",
            "--set", "y_label=Valeur absolue du t moyen le long de la courbe", "--set", "language=fr"],
    },
    "en": {
        "remesure-dumbbell": [
            "--title", "Pineau's grid, in 2018 and in 2026",
            "--set", "subtitle_template=Share of experimental papers: Pineau ({a}) against us ({b})",
            "--set", "axis_title=Share of papers (%, higher is better)"],
        "remesure-ic": [
            "--title", "What 2026 papers report",
            "--set", "subtitle=Share of experimental papers, 95% Wilson interval",
            "--set", "y_axis_title=Share of papers (%, higher is better)",
            "--set", "x_axis_title=Checklist item"],
        "e1-seeds": [
            "--title", "Same code, thirty random seeds",
            "--set", "subtitle=PPO-SB3 on HalfCheetah-v5, final score at 1M steps, one dot per run",
            "--set", "y_axis_title=Final evaluation score (higher is better)"],
        "e1-false-positive": [
            "--title", "Sorting the runs fools the test",
            "--set", "subtitle=10,000 draws of two groups of the same code: share with p < 0.05 (Welch)",
            "--set", "x_label=How the two groups are formed",
            "--set", "y_label=False positives (%, lower is better)"],
        "grpo-truncation": [
            "--title", "The base model does not finish its answers",
            "--set", "subtitle=Qwen2.5-0.5B-Instruct, step-10 batch, 8 sampled answers per problem",
            "--set", "y_axis_title=Share of the 8 answers", "--set", "x_axis_title=Problem"],
        "ecarts-pineau": [
            "--title", "Gap between 2026 and Pineau's figures",
            "--set", "subtitle=45 experimental papers from 2026 against her 50 from 2018, 95% Newcombe interval",
            "--set", "y_axis_title=Gap in points (2026 minus 2018)",
            "--set", "x_axis_title=Checklist item"],
        "ecarts-classique": [
            "--title", "Classic RL alone, from 2018 to 2026",
            "--set", "subtitle=14 papers from 2026 against our 12 from 2018, same grid, 95% Newcombe interval",
            "--set", "y_axis_title=Gap in points (2026 minus 2018)",
            "--set", "x_axis_title=Checklist item"],
        "e1-henderson": [
            "--title", "Neither PPO nor TRPO comes near the 2018 statistic",
            "--set", "subtitle=HalfCheetah-v5, two groups of 5 runs out of 30. Our bars: 95th percentile over 10,000 draws",
            "--set", "x_label=Where the runs come from",
            "--set", "y_label=Absolute mean t along the learning curve"],
    },
}
KINDS = {"remesure-dumbbell": ("dumbbell", "remesure_dumbbell", [
             "--set", "group_a_label=2018", "--set", "group_b_label=2026",
             "--set", "value_prefix=", "--set", "value_suffix="]),
         "remesure-ic": ("errorbar", "remesure_ic", ["--set", "width=1040"]),
         "e1-seeds": ("beeswarm", "e1_seeds", []),
         "e1-false-positive": ("bar", "e1_false_positive", []),
         "grpo-truncation": ("stacked-bar", "grpo_truncation", []),
         "ecarts-pineau": ("errorbar", "ecarts_pineau", ["--set", "width=1040"]),
         "ecarts-classique": ("errorbar", "ecarts_classique", ["--set", "width=1160"]),
         "e1-henderson": ("bar", "e1_henderson", ["--set", "width=900"])}

for lang in L:
    for name, (kind, data, common) in KINDS.items():
        opts = T[lang][name]
        out = name if lang == "fr" else f"{name}-en"
        svg = HERE / f"{out}.svg"
        subprocess.run(["sprezzature-figures", "render", kind, "--data", str(DATA / f"{data}_{lang}.csv"),
                        "--out", str(svg), "--theme", "academic", *opts, *common], check=True)
        text = svg.read_text()
        fixes = {"remesure-dumbbell": [("Overall median", L[lang]["median"])] if lang == "fr" else [],
                 "grpo-truncation": [("#009E73", "#8E8E93")]}  # a wrong answer is not good news: grey, not green
        for old, new in fixes.get(name, []):
            assert old in text, (name, old)
            text = text.replace(old, new)
        svg.write_text(text)
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(HERE / f"{out}.pdf"), str(svg)], check=True)
        subprocess.run(["sprezzature-figures", "check", str(svg), "--expect-title", opts[1]])
print("figures written to", HERE)
