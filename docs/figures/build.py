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


# Remesure (study/RESULTS.md): Pineau's 2018 figures against our 2026 sample, and our 2026 Wilson intervals.
write("remesure_dumbbell", ["category", "group_a", "group_b"], [
    ("Hyperparamètres des références", 60, 18),
    ("Hyperparamètres de la méthode", 90, 67),
    ("Choix des hyperparamètres décrit", 20, 27),
    ("Code en lien", 55, 67),
    ("Évaluation tenue à part", 10, 70),
])
write("remesure_ic", ["g", "mean", "lo", "hi"], [
    ("Réf. réglées", 5, 1, 15),
    ("Test signif.", 4, 1, 15),
    ("Hyperparam. réf.", 18, 10, 32),
    ("Choix hyperparam.", 27, 16, 41),
    ("Incertitude", 47, 33, 61),
    ("Calcul", 47, 33, 61),
    ("Code", 67, 52, 79),
    ("Tenue à part", 70, 56, 82),
])

# E1 (sim/analysis/e1.json): the 30 final returns, and the false-positive rate of each cut.
e1 = json.load(open(ROOT / "sim/analysis/e1.json"))
write("e1_seeds", ["group", "value"], [("PPO-SB3", round(v)) for v in e1["seeds_sorted"]])
write("e1_false_positive", ["region", "value"], [
    ("3 c. 3, au hasard", round(100 * e1["random_3v3"]["false_positive"], 1)),
    ("5 c. 5, au hasard", round(100 * e1["random_5v5"]["false_positive"], 1)),
    ("10 c. 10, au hasard", round(100 * e1["random_10v10"]["false_positive"], 1)),
    ("5 meilleures c. 5 pires", round(100 * e1["extreme_5v5_of_10"]["false_positive"], 1)),
])

# GRPO diagnostic (sim/llm/diag/replay_batch.json): base model on the pilot's step-10 batch.
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
replay = json.load(open(ROOT / "sim/llm/diag/replay_batch.json"))
kinds = ("Complète et juste", "Complète et fausse", "Coupée à 160 jetons")
count = collections.Counter()
for r in replay:
    cut = len(tok(r["text"])["input_ids"]) >= 158
    count[(r["q"], kinds[2] if cut else kinds[0] if r["right"] else kinds[1])] += 1
problems = list(dict.fromkeys(r["q"] for r in replay))
write("grpo_truncation", ["quarter", "type", "share"],
      [(q.replace("*", " × "), k, count[(q, k)]) for q in problems for k in kinds])

# Every figure in the academic theme (Okabe-Ito palette, serif text). FIXES are deterministic edits of the
# rendered SVG for what the kinds expose no option for; the PDF is then drawn from that same SVG.
FIGURES = [
    ("remesure-dumbbell", "dumbbell", "remesure_dumbbell", [
        "--title", "La grille de 2018 réappliquée, de 2018 à 2026",
        "--set", "subtitle_template=Part des articles expérimentaux : Pineau ({a}) contre nous ({b})",
        "--set", "axis_title=Part des articles (%, plus haut est mieux)",
        "--set", "group_a_label=2018", "--set", "group_b_label=2026",
        "--set", "value_prefix=", "--set", "value_suffix="]),
    ("remesure-ic", "errorbar", "remesure_ic", [
        "--title", "Ce que les articles de 2026 rapportent",
        "--set", "subtitle=Part des articles expérimentaux, IC de Wilson à 95 %",
        "--set", "y_axis_title=Part des articles (%, plus haut est mieux)",
        "--set", "x_axis_title=Critère de la grille", "--set", "width=1040"]),
    ("e1-seeds", "beeswarm", "e1_seeds", [
        "--title", "Même code, trente graines",
        "--set", "subtitle=PPO-SB3 sur HalfCheetah-v5, retour d'évaluation final à 1 M de pas, un point par graine",
        "--set", "y_axis_title=Retour d'évaluation final (plus haut est mieux)", "--set", "language=fr"]),
    ("e1-false-positive", "bar", "e1_false_positive", [
        "--title", "Ce qui trompe le test, ce n'est pas le hasard",
        "--set", "subtitle=10 000 tirages de deux groupes du même code : part des p < 0,05 (Welch)",
        "--set", "x_label=Façon de former les deux groupes",
        "--set", "y_label=Faux positifs (%, plus bas est mieux)", "--set", "language=fr"]),
    ("grpo-truncation", "stacked-bar", "grpo_truncation", [
        "--title", "Le modèle de base ne finit pas ses réponses",
        "--set", "subtitle=Qwen2.5-0.5B-Instruct, lot du pas 10, 8 réponses échantillonnées par problème",
        "--set", "y_axis_title=Part des 8 réponses", "--set", "x_axis_title=Problème"]),
]
FIXES = {
    "remesure-dumbbell": [("Overall median", "Médiane globale")],
    "grpo-truncation": [("#009E73", "#8E8E93")],  # a wrong answer is not good news: grey, not green
}

for name, kind, data, opts in FIGURES:
    svg = HERE / f"{name}.svg"
    subprocess.run(["sprezzature-figures", "render", kind, "--data", str(DATA / f"{data}.csv"),
                    "--out", str(svg), "--theme", "academic", *opts], check=True)
    text = svg.read_text()
    for old, new in FIXES.get(name, []):
        assert old in text, (name, old)
        text = text.replace(old, new)
    svg.write_text(text)
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(HERE / f"{name}.pdf"), str(svg)], check=True)
    subprocess.run(["sprezzature-figures", "check", str(svg), "--expect-title", opts[1]])
print("figures written to", HERE)
