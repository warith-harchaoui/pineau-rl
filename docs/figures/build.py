"""Builds every figure of docs/ with sprezzature-figures, from the project's own result files.

Run with the LLM environment (it needs the Qwen tokenizer to count truncated completions):
    ../../sim/env-llm/bin/python build.py
Writes data/*.csv, then <name>.svg (Markdown) and <name>.pdf (LaTeX) for each figure.
"""
import collections, csv, json, os, subprocess
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
FP = [round(100 * e1[k]["false_positive"], 1) for k in ("random_3v3", "random_5v5", "random_10v10", "extreme_5v5_of_10")]

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
    },
}
KINDS = {"remesure-dumbbell": ("dumbbell", "remesure_dumbbell", [
             "--set", "group_a_label=2018", "--set", "group_b_label=2026",
             "--set", "value_prefix=", "--set", "value_suffix="]),
         "remesure-ic": ("errorbar", "remesure_ic", ["--set", "width=1040"]),
         "e1-seeds": ("beeswarm", "e1_seeds", []),
         "e1-false-positive": ("bar", "e1_false_positive", []),
         "grpo-truncation": ("stacked-bar", "grpo_truncation", [])}

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
