"""Builds the blog figures of the article, in French and in English, from the project's result files.

Every number drawn here is read from a result file of the project, never typed by hand:
    sim/analysis/e1.json, e1_curve.json, b1_trpo.json, b1_script.json   (E1, B1: thirty runs, the t of 9)
    sim/analysis/e2.json, e4.json, e7_rank.json                          (E2, E4, E7: four algorithms, four tasks)
    study/extension_stats.json, study/trajectory.json                   (the survey, same grid, year by year)
    sim/llm/results/summary.json                                         (GRPO, true and coin-flip reward)
    docs/figures/data/grpo_truncation_{fr,en}.csv                        (counted by docs/figures/build.py from
                                                                          sim/llm/diag/replay_batch.json)
Run from anywhere, CPU-light:  nice python3 article/figures/build.py
Writes data/<name>_<lang>.csv, then <name>-fr.svg and <name>-en.svg, and runs `sprezzature-figures check` on each.
"""
import csv, json, re, subprocess, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
DATA.mkdir(exist_ok=True)
J = lambda p: json.load(open(ROOT / p))


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
T9 = [("PPO", "notre calcul", "our computation", curve["random_5v5"]["share_abs_mean_t_ge_9"]),
      ("TRPO", "notre calcul", "our computation", b1["trpo"]["random_5v5"]["mean_t"]["share_abs_t_ge_henderson"]),
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
               "--set", "subtitle=Rang de quatre algorithmes, score de dix graines aléatoires en bout de ligne",
               "--set", "rank_note=Physique modifiée : masses alourdies de 20 %, frottements réduits de 20 %",
               "--set", "finding=PPO (JAX), premier à l'entraînement, finit dernier ; CrossQ prend la tête.",
               "--set", "rank_label=Rang (1 en haut)", "--set", "x_label=",
               "--set", "tie_within=0", "--set", "width=760", "--set", "height=400"],
        "en": ["--title", "On Hopper, the leader ends last",
               "--set", "subtitle=Rank of four algorithms, score over ten random seeds at each end of the line",
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
               "--set", "subtitle=50 articles de RL classique de 2026 contre nos 50 de 2018 ; barre : intervalle à 95 %",
               "--set", "y_axis_title=Écart en points (2026 moins 2018)",
               "--set", "x_axis_title=Pratique relevée dans l'article",
               "--set", "width=820", "--set", "height=460"],
        "en": ["--title", "With the same grid, four practices changed",
               "--set", "subtitle=50 classical RL papers from 2026 against our 50 from 2018; bar: 95% interval",
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

# 9. GRPO: success at the first attempt, before and after 100 steps, per run.
summ = J("sim/llm/results/summary.json")
MOD = {"qwen05": "Qwen", "llama1": "Llama"}
REW = {"fr": {"true": "vraie récompense", "random": "pile ou face"},
       "en": {"true": "true reward", "random": "coin flip"}}
ORD = {"fr": ["première", "deuxième", "troisième"], "en": ["first", "second", "third"]}
for lang in LANGS:
    rows = []
    for m in ("qwen05", "llama1"):
        for rw in ("true", "random"):
            for s in sorted((s for s in summ if s["model"] == m and s["reward"] == rw), key=lambda s: s["seed"]):
                rows.append((f"{MOD[m]}, {REW[lang][rw]}", ORD[lang][s["seed"]], r(s["pass1_100"] * 100)))
    start = {m: sorted({r(s["pass1_0"] * 100) for s in summ if s["model"] == m}) for m in MOD}
    q, l = start["qwen05"], start["llama1"]
    csvp = write(f"grpo_graines_{lang}", ["period", "region", "v"], rows)
    FIGS.setdefault("grpo-graines", {})[lang] = ("bar-grouped", csvp, {
        "fr": ["--title", "Pile ou face fait tomber la réussite à zéro",
               "--set", f"subtitle=Problèmes réussis au premier essai après 100 pas. Au départ : {q[0]} à {q[-1]} % pour Qwen, {l[0]} à {l[-1]} % pour Llama",
               "--set", "language=fr", "--set", "width=760", "--set", "height=460"],
        "en": ["--title", "A coin flip drives success down to zero",
               "--set", f"subtitle=Problems solved at the first attempt after 100 steps. At the start: {q[0]} to {q[-1]}% for Qwen, {l[0]} to {l[-1]}% for Llama",
               "--set", "width=760", "--set", "height=460"]}[lang])

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

# Deterministic touch-ups for what a kind exposes no option for. bar-grouped writes demo axis titles
# ("Region", "Units", "Quarter") with no option to change them: they are replaced here, and the check forbids them.
CHROME = {"fr": ("Région", "Unités", "Trimestre"), "en": ("Region", "Units", "Quarter")}
AXES = {
    "classement-taches": {"fr": ("Algorithme", "% du meilleur (plus haut est mieux)", "Tâche"),
                          "en": ("Algorithm", "% of the best (higher is better)", "Task")},
    "meilleurs-sur-dix": {"fr": ("Algorithme", "Hausse de la moyenne (%)", "Tâche"),
                          "en": ("Algorithm", "Rise of the mean (%)", "Task")},
    "grpo-graines": {"fr": ("Graine aléatoire", "Réussite au premier essai (%)", "Modèle et récompense"),
                     "en": ("Random seed", "Success at the first attempt (%)", "Model and reward")},
}


def swap(text, a, b):
    return text.replace(a, "\0").replace(b, a).replace("\0", b)


def fix(name, lang, text, mobile=False):
    axes = AXES_M if mobile else AXES
    if name in axes:
        for old, new in zip(CHROME[lang], axes[name][lang]):
            assert text.count(f">{old}<") == 1, (name, old)
            text = text.replace(f">{old}<", f">{new}<")
    if name == "e1-graines":  # the swarm has a single group: its legend says nothing
        for old in (">Groupe PPO<", ">Group PPO<"):
            text = text.replace(old, ">PPO, un point par graine aléatoire<" if lang == "fr" else ">PPO, one dot per random seed<")
        text = text.replace("Groupe PPO", "Essai de PPO").replace("Group PPO", "PPO run")
    if name == "grpo-coupure":  # a wrong answer is not good news: grey, not green
        text = text.replace("#009E73", "#8E8E93")
    if name == "grpo-graines":  # the third seed in a darker blue: pale yellow bars vanish on white
        text = text.replace("#F0E442", "#56B4E9")
    if name == "physique-modifiee":  # same colour per algorithm as in the bar charts
        text = swap(text, "#CC79A7", "#009E73")
    if name == "grille-egale":
        text = rotate_labels(text, list((CRIT_M if mobile else CRIT)[lang].values()), extra=70 if mobile else 96)
    return text


def rotate_labels(text, labels, extra=96, left=40):
    """Eight practice names do not fit side by side under the errorbar chart: tilt them by 35 degrees.

    The kind exposes no option for it, so this edits the rendered SVG: each label hangs from its tick, the canvas
    grows downward and to the left, and the axis title moves under the tilted labels."""
    w, h = map(int, re.search(r'<svg[^>]* width="(\d+)" height="(\d+)"', text).groups())
    ys = set()
    for lab in labels:
        pat = re.compile(rf'<text x="([\d.]+)" y="([\d.]+)" font-size="13" fill="#1D1D1F" text-anchor="middle">{re.escape(lab)}</text>')
        m = pat.findall(text)
        assert len(m) == 1, lab
        ys.add(m[0][1])
        text = pat.sub(lambda m: f'<text x="{float(m[1]) + 4:.1f}" y="{float(m[2]) - 4:.1f}" font-size="13" fill="#1D1D1F" '
                                 f'text-anchor="end" transform="rotate(-35 {float(m[1]) + 4:.1f} {float(m[2]) - 4:.1f})">{lab}</text>', text)
    assert len(ys) == 1
    head = f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"'
    assert text.count(head) == 1
    text = text.replace(head, f'width="{w + left}" height="{h + extra}" viewBox="-{left} 0 {w + left} {h + extra}"')
    rect = f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>'
    assert text.count(rect) == 1
    text = text.replace(rect, f'<rect x="-{left}" width="{w + left}" height="{h + extra}" fill="#FFFFFF"/>')
    title = re.compile(r'(<text x="[\d.]+" y=")([\d.]+)(" font-size="13" fill="#1D1D1F" text-anchor="middle">)(?!-)')
    found = [m for m in title.finditer(text) if float(m[2]) > float(next(iter(ys)))]
    assert len(found) == 1, found
    m = found[0]
    return text[:m.start()] + f"{m[1]}{h + extra - 14}{m[3]}" + text[m.end():]


# Narrow variants for phones: the same data and the same message, drawn for a column of about 400 px.
# Shorter titles and labels, a canvas 400 px wide and taller, so the type stays near its printed size.
CRIT_M = {"fr": {"Q5": "Code", "Y9": "Réglage", "X7": "Calcul", "X2": "Incertitude", "Q7": "Tenue à part",
                 "Q8": "Test", "Y7": "Versions", "Q4": "Réf. réglées"},
          "en": {"Q5": "Code", "Y9": "Setting", "X7": "Compute", "X2": "Uncertainty", "Q7": "Held-out",
                 "Q8": "Test", "Y7": "Versions", "Q4": "Baselines"}}
AXES_M = {
    "classement-taches": {"fr": ("Algorithme", "% du meilleur", "Tâche"), "en": ("Algorithm", "% of the best", "Task")},
    "meilleurs-sur-dix": {"fr": ("Algorithme", "Hausse (%)", "Tâche"), "en": ("Algorithm", "Rise (%)", "Task")},
    "grpo-graines": {"fr": ("Graine aléatoire", "Réussite (%)", "Modèle, récompense"),
                     "en": ("Random seed", "Success (%)", "Model, reward")},
}
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
               {"PPO, notre calcul": "PPO, nous", "TRPO, notre calcul": "TRPO, nous", "TRPO, points empilés": "TRPO, empilés",
                "PPO, script de 2017": "PPO, script", "TRPO, script de 2017": "TRPO, script"}, []),
        "en": ("Only the script reaches 9", "Random draws where the mean t reaches 9.09", 400, 460,
               {"PPO, our computation": "PPO, ours", "TRPO, our computation": "TRPO, ours", "TRPO, stacked points": "TRPO, stacked",
                "PPO, 2017 script": "PPO, script", "TRPO, 2017 script": "TRPO, script"}, [])},
    "meilleurs-sur-dix": {
        "fr": ("3 sur 10 gonflent tout", "Hausse de la moyenne, trois meilleurs essais sur dix", 400, 520, {"HalfCheetah": "Cheetah"}, []),
        "en": ("Best 3 of 10 inflate all", "Rise of the mean, best three runs of ten", 400, 520, {"HalfCheetah": "Cheetah"}, [])},
    "classement-taches": {
        "fr": ("Le premier change", "Score en % du meilleur de chaque tâche", 400, 520, {"HalfCheetah": "Cheetah"}, []),
        "en": ("The leader changes", "Score as a % of the best on each task", 400, 520, {"HalfCheetah": "Cheetah"}, [])},
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
        "fr": ("Pile ou face : zéro", "Réussite après 100 pas ; P/F : pile ou face", 400, 520,
               {"Qwen, vraie récompense": "Qwen vraie", "Qwen, pile ou face": "Qwen P/F",
                "Llama, vraie récompense": "Llama vraie", "Llama, pile ou face": "Llama P/F"}, []),
        "en": ("Coin flip: down to zero", "First-attempt success after 100 steps", 400, 520,
               {"Qwen, true reward": "Qwen true", "Qwen, coin flip": "Qwen coin",
                "Llama, true reward": "Llama true", "Llama, coin flip": "Llama coin"}, [])},
    "grpo-coupure": {
        "fr": ("Des réponses coupées", "Qwen2.5 de 0,5 milliard, 8 réponses par problème", 400, 500,
               {"Complète et juste": "Juste", "Complète et fausse": "Fausse", "Coupée à 160 jetons": "Coupée"},
               ["--set", "x_axis_title=Problème"]),
        "en": ("Answers cut short", "Qwen2.5 with 0.5 billion, 8 answers per problem", 400, 500,
               {"Complete and right": "Right", "Complete and wrong": "Wrong", "Cut at 160 tokens": "Cut"},
               ["--set", "x_axis_title=Problem"])},
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


def render(only=None):
    bad = 0
    for name, per in FIGS.items():
        if only and name not in only:
            continue
        jobs = [(lang, False, spec) for lang, spec in per.items()] + \
               [(lang, True, mobile_spec(name, lang, *spec)) for lang, spec in per.items()]
        for lang, mob, (kind, csvp, opts) in jobs:
            svg = HERE / f"{name}{'-mobile' if mob else ''}-{lang}.svg"
            subprocess.run(["nice", "sprezzature-figures", "render", kind, "--data", str(csvp), "--out", str(svg),
                            "--theme", "academic", "--set", "mode=static", *opts], check=True, stdout=subprocess.DEVNULL)
            svg.write_text(fix(name, lang, svg.read_text(), mob))
            forbid = [x for c in CHROME.values() for x in c] + ["Overall median", "of week total"]
            res = subprocess.run(["sprezzature-figures", "check", str(svg), "--expect-title", opts[1],
                                  *[a for f in forbid for a in ("--forbid", f)]],
                                 capture_output=True, text=True)
            status = "clean" if res.returncode == 0 else "FINDINGS"
            bad += res.returncode != 0
            print(f"{svg.name}: {status}")
            if res.returncode:
                print(res.stdout.strip(), res.stderr.strip())
    return bad


if __name__ == "__main__":
    sys.exit(1 if render(set(sys.argv[1:]) or None) else 0)
