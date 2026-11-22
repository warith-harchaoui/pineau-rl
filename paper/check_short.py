"""Every number of the short paper (paper/short_en.md), asserted against its source.

On the model of article/check_article.py:
  1. each claim builds, from a result file and its key, the phrase the paper writes; the phrase must appear in the text;
  2. a few numbers have no result file (Pineau's slides, a cited paper, a software version, a time step): their claim
     says so ("doc"), and each of its numbers must then appear in the English technical report (report/en/*.tex);
  3. every numeric token left in the body after removing the claimed phrases is a failure. Years, section numbers,
     figure numbers, deviation numbers, criterion codes and code spans are not numeric claims and are removed first.
     The reference list is checked against report/refs.bib.
Exit code 1 on any failure.  Run: python3 paper/check_short.py
"""
import json, re, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
J = lambda p: json.load(open(ROOT / p))
norm = lambda t: re.sub(r"\s+", " ", t)
RAW = (HERE / "short_en.md").read_text()
TEXT = norm(RAW)
REPORT = norm(" ".join(p.read_text() for p in sorted((ROOT / "report/en").glob("*.tex")))).replace("\\num{", "").replace("{,}", ".")
REPORT_NUMS = set(re.findall(r"\d+(?:[.,]\d+)*", REPORT)) | {n.replace(",", "") for n in re.findall(r"\d+(?:,\d{3})+", REPORT)}
BIB = norm((ROOT / "report/refs.bib").read_text())


def hu(x, nd=0):
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def num(x, nd=0):
    v = hu(x, nd)
    return str(v) if nd else f"{int(v):,}"


def pct(x, nd=0):
    """x is a fraction: 0.31 -> '31%'."""
    return num(Decimal(str(x)) * 100, nd) + "%"


def sg(x):
    """A gap in points, signed: +43, -7, 0 (x already in points)."""
    v = int(hu(x))
    return f"+{v}" if v > 0 else (f"-{abs(v)}" if v < 0 else "0")


def pv(x, sig=1):
    """A p-value to `sig` significant digits: 0.000443 -> 0.0004, 0.0361 -> 0.04, 1.0 -> 1."""
    x = Decimal(str(x))
    if x >= 1:
        return "1"
    e = x.adjusted() - sig + 1
    return format(x.quantize(Decimal(1).scaleb(e), rounding=ROUND_HALF_UP), "f")


C = []  # (label, phrase, kind)


def claim(label, phrase, kind="json"):
    C.append((label, phrase, kind))


def D(label, phrase):
    claim(label, phrase, "doc")


share = lambda kn: Decimal(kn[0]) / Decimal(kn[1])
iv = lambda t: f"[{sg(t['lo'] * 100)}, {sg(t['hi'] * 100)}]"

# The main comparison (study/extension_stats.json, key rows[k].ours2018 / classic2026 / classic_vs_ours2018).
X = {r["k"]: r for r in J("study/extension_stats.json")["rows"]}
N = {k: (X[k]["ours2018"], X[k]["classic2026"], X[k]["classic_vs_ours2018"]) for k in X}
for k in ("Q5", "Y9", "X7", "X2"):  # abstract and table of section 3.1
    a, b, t = N[k]
    claim(f"{k} table row", f"| {pct(share(a))} ({a[0]} of {a[1]}) | {pct(share(b))} ({b[0]} of {b[1]}) | "
          f"{sg(t['diff'] * 100)} | {iv(t)} | {pv(t['p_holm'])} |")
a, b, t = N["Q5"]
claim("abstract Q5", f"Linking the code rose from {pct(share(a))} to {pct(share(b))} ({sg(t['diff'] * 100)} points, {iv(t)})")
claim("abstract Y9 X7 X2", "hyperparameter rose from {} to {}, quantifying the compute from {} to {}, reporting an uncertainty from {} to "
      "{}".format(*[pct(share(N[k][i])) for k in ("Y9", "X7", "X2") for i in (0, 1)]))
claim("abstract Q4", f"settings of their baselines go from {pct(share(N['Q4'][0]))} to {pct(share(N['Q4'][1]))}")
claim("Q4 gap", f"go from {pct(share(N['Q4'][0]))} to {pct(share(N['Q4'][1]))}: {sg(N['Q4'][2]['diff'] * 100)} points, {iv(N['Q4'][2])}")
a, b, t = N["Q2"]
claim("Q2", f"from {pct(share(a))} to {pct(share(b))} ({sg(t['diff'] * 100)} points, {iv(t)})")
claim("Q3 calibration", f"our reading finds {pct(share(N['Q3'][0]))} where she counted 90%")
D("Pineau Q3", "where she counted 90%")
claim("Q3 calibration 2", f"she counted 90%, we find {pct(share(N['Q3'][0]))}")
claim("Q7 calibration", f"she counted 10%, we find {pct(share(N['Q7'][0]))}")
D("Pineau Q7", "she counted 10%")
for k, name in (("Q7", "Held-out evaluation (Q7) rises"), ("Q6", "the choice of\nhyperparameters (Q6)"),
                ("Q3", "the method's hyperparameters (Q3)"), ("Q8", "the statistical test (Q8)")):
    pass
claim("Q7 Q6 Q3 Q8", "Held-out evaluation (Q7) rises from {} to {}, the choice of hyperparameters (Q6) from {} to {}, the method's "
      "hyperparameters (Q3) from {} to {}, the statistical test (Q8) from {} to {}".format(
          *[pct(share(N[k][i])) for k in ("Q7", "Q6", "Q3", "Q8") for i in (0, 1)]))
NAMES1 = {"Q2": "neural networks used", "Q3": "method's hyperparameters given", "Q4": "baselines' hyperparameters given",
          "Q5": "code linked", "Q6": "choice of hyperparameters stated", "Q7": "held-out evaluation", "Q8": "significance test",
          "X2": "uncertainty reported", "X3": "best runs kept", "X4": "baselines tuned with the same care", "X7": "compute quantified"}
for k, name in NAMES1.items():
    a, b, t = N[k]
    claim(f"grid v1 row {k}", f"| {k}, {name} | {pct(share(a))} | {pct(share(b))} | {sg(t['diff'] * 100)} | {iv(t)} | {pv(t['p_holm'])} |")
claim("grid v1 count", "The correction runs over these 11 criteria")
assert len(NAMES1) == 11
claim("Y12", f"(Y12, from {pct(share(N['Y12'][0]))} to {pct(share(N['Y12'][1]))}, {iv(N['Y12'][2])})")
assert N["Q6"][2]["lo"] > 0 and N["Y12"][2]["lo"] > 0 and N["Q6"][2]["p_holm"] > .05 and N["Y12"][2]["p_holm"] > .05
claim("11 and 12 criteria", "With 11 and 12 criteria tested at once")
claim("Holm families", "applies separately to the 11 criteria of grid v1 and to the 12 of grid v2")
sm = J("study/extension_stats.json")["samples"]
claim("samples 2018", f"we read {sm['ours2018']} RL papers from ICLR, ICML and NeurIPS 2018")
claim("samples 2026", f"we read {sm['classic2026']} classical RL papers from ICLR 2026")
claim("experimental 2018", f"Of the 2018 papers, {N['Q5'][0][1]} have experiments")
claim("main comparison", f"{sm['classic2026']} classical RL papers from 2026 (robotics, games, control, language models excluded) "
      f"against our own reading of {sm['ours2018']} papers from 2018")
claim("abstract samples", f"We read {sm['classic2026']} classical RL papers from 2026 and {sm['ours2018']} papers from 2018")
claim("conclusion fifty", "With fifty papers per year")
claim("about fifty", "With about fifty papers per year")
D("Pineau survey", "of 50 RL papers from 2018, 90% gave the hyperparameters of their method, 60% those of their baselines, 55% "
  "linked their code, 20% said how they chose their hyperparameters and 5% applied a significance test")
D("Pineau abstract", "She surveyed 50 RL papers from 2018 and found that 55% linked their code and 5% applied a significance test")
D("Pineau 50", "Pineau did not describe how she drew her 50 papers")

# Criterion X8 (study/x8_stats.json, key main).
x8 = J("study/x8_stats.json")
c18, c26, d8 = x8["main"]["counts"]["2018"], x8["main"]["counts"]["2026"], x8["main"]["diff"]
claim("X8 abstract", f"({pct(c18['share'])} then {pct(c26['share'])}, {iv(d8)})")
claim("X8", f"X8 goes from {pct(c18['share'])} ({c18['yes']} of {c18['n']}) to {pct(c26['share'])} ({c26['yes']} of {c26['n']}): "
      f"{sg(d8['diff'] * 100)} points, {iv(d8)}, p = {pv(d8['p'], 2)}")
uns = x8["sources"]["2026"]["unstated"]
claim("X8 unstated", f"In 2026, {uns} of the {c26['x2_yes']} papers that draw a bar do not say")
claim("X8 unstated 2", f"In 2026, {uns} of the {c26['x2_yes']} papers that draw a bar do not say. A bar")

# Power (study/survey_extra.json, key mde).
md = J("study/survey_extra.json")["mde"]["Q7"]
claim("mde Q7", f"only if it reaches {int(hu(md['up_5'] * 100))} points, {int(hu(md['up_bonf'] * 100))} after the Bonferroni correction")
claim("power Q7", f"had an {pct(md['power_observed_5'])} chance of being detected at the 5% level, {pct(md['power_observed_bonf'])} after")
claim("80% chance", "with an 80% chance")
D("interval width", "each Newcombe interval spans twenty to forty points")

# Double readings (study/survey_extra.json, key double_readings.pooled).
dr = J("study/survey_extra.json")["double_readings"]
assert all(dr["pooled"][k]["same"] == dr["pooled"][k]["n"] == dr["papers"] for k in ("Q5", "Y9", "X7", "X2"))
claim("double readings", f"{dr['papers'] if dr['papers'] != 30 else 'Thirty'} papers were reread blind")
claim("30 of 30", f"agrees with the first on {dr['pooled']['Q5']['same']} papers out of {dr['pooled']['Q5']['n']}")

# The search against the "no" decisions (study/falsify_no.json, keys counts and comparison).
fc = J("study/falsify_no.json")
cn = fc["counts"].values()
n_no, n_none, n_occ = (sum(c[f] for c in cn) for f in ("no", "no_occurrence", "with_occurrence"))
tr = {y: sum(len(c["turned"]) for k, c in fc["counts"].items() if k.startswith(y)) for y in ("2018", "2026")}
unc = sum(len(c["uncertain"]) for c in cn)
assert fc["verdict_changes"]["turned"] == []
claim("falsify", f"Of {n_no} \"no\" decisions, {n_none} have no occurrence of the patterns. The other {n_occ} were shown")
claim("falsify turned", f"Ten turned into \"yes\" ({tr['2018']} in 2018, {tr['2026']} in 2026)")
assert tr["2018"] + tr["2026"] == 10
claim("falsify seven", "every final \"no\" on seven criteria")
assert len(fc["counts"]) == 14
bx, by = fc["comparison"]["X2"]["bound"]["p_holm"], fc["comparison"]["Y9"]["bound"]["p_holm"]
claim("falsify bound", f"If the {unc} decisions the arbiter found doubtful are turned as well, uncertainty and sensitivity end just "
      f"above the threshold (p = {pv(bx)} and p = {pv(by, 2)} after Holm)")

# Without the papers read partly by the neighbouring model (study/extension_stats_sans_opus5.json).
so = {r["k"]: r["classic_vs_ours2018"]["p_holm"] for r in J("study/extension_stats_sans_opus5.json")["rows"]}
claim("sans opus5", f"the code link (p = {pv(so['Q5'])}), sensitivity (p = {pv(so['Y9'])}) and compute (p = {pv(so['X7'])}) still "
      f"pass the correction. Reported uncertainty no longer does (p = {pv(so['X2'])})")
D("thirteen papers", "Without the thirteen papers read partly by the neighbouring model")

# The version read (study/q5_versions.json, readings P1 = proceedings both years, P2 = latest arXiv both years).
qv = J("study/q5_versions.json")["readings"]
assert qv["P1"]["p_holm"] < .05 and qv["P2"]["p_holm"] < .05
claim("Q5 proceedings", f"the code link still rises by {sg(qv['P1']['diff'] * 100)} points")
claim("Q5 arXiv", f"it rises by {sg(qv['P2']['diff'] * 100)} points. Both pass")

# Reader effect within 2018 (study/survey_extra.json, readers_year.confound.2018.Q5.p_perm).
pp = J("study/survey_extra.json")["readers_year"]["confound"]["2018"]["Q5"]["p_perm"]
claim("reader permutation", f"(permutation p = {pv(pp, 2)})")

# Year and readers disentangled (study/r36_stats.json, keys main, mixed_model, verdicts; survey deviation 36).
r36 = J("study/r36_stats.json")
rm, rv, rmm = r36["main"], r36["verdicts"], r36["mixed_model"]
assert [rv[k]["verdict"] for k in ("Q5", "Y9", "X7", "X2")] == ["holds"] * 3 + ["same direction, not established"]
assert sorted(k for k in rmm if rmm[k]["reader_sd"] == 0) == ["Q5", "Y9"] and all(rmm[k]["p_reader_sd"] > .05 for k in rmm)
sh = lambda k, y: pct(rm[k]["counts"][y]["share"])
claim("r36 n", f"reread all {rm['Q5']['counts']['2018']['n'] + rm['Q5']['counts']['2026']['n']} papers with experiments")
claim("r36 three", f"the code link goes from {sh('Q5', '2018')} to {sh('Q5', '2026')}, sensitivity from {sh('Y9', '2018')} to "
      f"{sh('Y9', '2026')} and compute from {sh('X7', '2018')} to {sh('X7', '2026')}")
dx = rm["X2"]["diff"]
s1 = lambda x: f"+{num(x * 100, 1)}" if x > 0 else f"-{num(-x * 100, 1)}"
claim("r36 X2", f"Reported uncertainty goes from {sh('X2', '2018')} to {sh('X2', '2026')}, a gap of {sg(dx['diff'] * 100)} points "
      f"with interval [{s1(dx['lo'])}, {s1(dx['hi'])}]")
claim("r36 X2 p", f"Its year effect passes (p = {pv(rmm['X2']['p_lrt_holm4'])} after Holm) but the Fisher test misses "
      f"(p = {pv(dx['p_holm4'], 2)} after Holm)")

# Trajectory (study/trajectory.json, rows.Q5).
tq = J("study/trajectory.json")["rows"]["Q5"]
by = tq["by_year"]
claim("trajectory Q5", "The code link goes from {} in 2018 to {} in 2019, {} in 2020, {} in 2022, {} in 2024 and {} in 2026".format(
    *[pct(share((by[y]["k"], by[y]["n"]))) for y in ("2018", "2019", "2020", "2022", "2024", "2026")]))
claim("trajectory trend", f"(p = {pv(tq['trend']['p_holm']):s})")
im = tq["immediate"]
claim("trajectory step", f"({sg(im['diff'] * 100)} points, {iv(im)}), does not (p = {pv(im['p_holm'])} after Holm)")
claim("twenty per year", "Twenty papers per year read in 2019, 2020, 2022 and 2024")
assert all(J("study/trajectory.json")["sizes"][y] == 20 for y in ("2019", "2020", "2022", "2024"))
claim("twenty per year 2", "With twenty papers per intermediate year")
claim("six years", "over the six years")

# Our reading against Pineau's figures (study/survey_extra.json, original_rule.classic2026).
orr = J("study/survey_extra.json")["original_rule"]["classic2026"]
assert orr["Q7"]["vs_pineau"]["p_holm"] < .05 and orr["Q4"]["vs_pineau"]["p_holm"] < .05
claim("vs Pineau", f"held-out evaluation ({sg(orr['Q7']['vs_pineau']['diff'] * 100)} points) and declined on the baselines' "
      f"hyperparameters ({sg(orr['Q4']['vs_pineau']['diff'] * 100)} points)")

# E1 (sim/analysis/e1.json).
e1 = J("sim/analysis/e1.json")
claim("E1 runs", f"thirty times on HalfCheetah")
assert e1["n"] == 30
claim("E1 spread", f"mean of {num(e1['mean'])} and a standard deviation of {num(e1['sd'])}, from {num(e1['min'])} to {num(e1['max'])}")
claim("E1 random", f"declares a difference in {pct(e1['random_5v5']['false_positive'], 1)} of the draws")
claim("E1 sorted", f"the test declares a difference in {pct(e1['extreme_5v5_of_10']['false_positive'])} of the draws")
claim("E1 top3", f"the mean rises by {pct(e1['top3_of_10']['inflation'])}")
claim("E1 B1 intro", f"fool Welch's t-test in {pct(e1['random_5v5']['false_positive'], 1)} of cases. Sorted groups fool it in "
      f"{pct(e1['extreme_5v5_of_10']['false_positive'])}")
D("draws", "10,000 times")
claim("ten into two", "Split ten of them into two groups of five")
claim("best three", "Keep the best three runs out of ten")

# B1 (sim/analysis/b1_trpo.json, b1_script.json, b1_factor.json).
bt, bs, bf = J("sim/analysis/b1_trpo.json"), J("sim/analysis/b1_script.json"), J("sim/analysis/b1_factor.json")
T = bt["trpo"]
claim("TRPO spread", f"a final mean of {num(T['final_mean'])} with a standard deviation of {num(T['final_sd'])}, or {pct(T['cv'])} of "
      f"the mean, against {pct(bt['ppo_sb3']['cv'])} for PPO")
claim("TRPO mean t", f"exceeds {num(T['random_5v5']['mean_t']['abs_t_p95'], 1)} only one time in twenty")
claim("TRPO sorted", f"it exceeds {num(T['sorted_5v5']['mean_t']['abs_t_p95'], 1)} one time in twenty")
claim("pooled", f"its t exceeds {num(T['random_5v5']['pooled']['abs_t_p95'], 1)} with random groups, "
      f"{num(T['sorted_5v5']['pooled']['abs_t_p95'], 1)} with sorted groups")
assert T["random_5v5"]["pooled"]["share_abs_t_ge_henderson"] == 0 == T["sorted_5v5"]["pooled"]["share_abs_t_ge_henderson"]
claim("pooled false", f"in {pct(T['random_5v5']['pooled']['false_positive'])} of the random draws with TRPO and "
      f"{pct(bt['ppo_sb3']['random_5v5']['pooled']['false_positive'])} with PPO")
claim("hundred points", "stacks the hundred points of the five curves")
D("Welch df", "has about 3.4 degrees of freedom. The stacked points have about 198")
D("10^-16", "of the order of 10^-16")
D("at least 4", "would need at least 4")
S = bs["trpo"]["n10"]
claim("script random", f"the average t reaches 9.09 in {pct(S['random_5v5']['share_abs_t_ge_henderson'])} of 10,000 draws, with a "
      f"median of {num(S['random_5v5']['abs_t_median'], 1)}. The test declares a difference in "
      f"{pct(S['random_5v5']['false_positive'])} of the draws")
claim("script sorted", f"with sorted groups, {pct(S['sorted_5v5']['share_abs_t_ge_henderson'])} of the draws reach 9.09")
claim("script n5", f"{pct(bs['trpo']['n5']['random_5v5']['share_abs_t_ge_henderson'])} of the random draws still reach 9.09")
claim("abstract 38", f"reaches that value in {pct(S['random_5v5']['share_abs_t_ge_henderson'])} of random draws")
P = bs["ppo_sb3"]["n10"]
assert P["random_5v5"]["share_abs_t_ge_henderson"] == 0 == P["sorted_5v5"]["share_abs_t_ge_henderson"]
claim("script PPO", f"its average t exceeds {num(P['random_5v5']['abs_t_p95'], 1)}")
claim("ten episodes", "with ten evaluation episodes per point")
claim("five episodes", "with five episodes instead of ten")
claim("five seeds", "five seeds per group divides the gap between means by σ√(2/5)")
claim("rho", f"only {pct(bf['trpo']['rho_30_runs'])} of the spread between agents. For our PPO, it is {pct(bf['ppo_sb3']['rho_30_runs'])}")
claim("factor", f"The median factor is {num(bf['trpo']['n10']['median_ratio'], 1)} for TRPO and {num(bf['ppo_sb3']['n10']['median_ratio'], 1)} "
      "for PPO with ten episodes")
assert bf["trpo"]["n10"]["max_abs_gap_ratio_vs_prediction"] < 1e-12
claim("identity", "The identity holds on each of the 10,000 draws to rounding error")
claim("ratio", "√(n/5)/ρ")
claim("S sqrt", "S√(2/n)")
D("Henderson t", "t = -9.09")
D("Henderson p", "p = 0.0016")
D("Henderson pair", "t = 9.09 and p = 0.0016")
D("figure 5", "Figure 5 of Henderson et al.")
claim("thirty PPO", "with thirty PPO runs of our own")
claim("thirty TRPO", "Our thirty TRPO runs")
claim("thirty TRPO curves", "Applied to our thirty TRPO curves")
claim("thirty PPO curves", "Applied to our thirty PPO curves")
claim("groups of five", "two groups of five")
claim("groups of five 2", "with groups of five drawn at random")
claim("best five worst five", "set the best five against the worst five")

# E6 (sim/analysis/e6_diag.json, e6_official.json, e6_speed.json, e6_enjoy.json, e6_hub.json, effect_sizes.json).
dg = J("sim/analysis/e6_diag.json")["groups"]
ivn = lambda c: f"[{num(c[0])}, {num(c[1])}]"
claim("E6 default v5", f"an interquartile mean (IQM) of {num(dg['default v5']['iqm'])} {ivn(dg['default v5']['iqm_ci'])}")
claim("E6 zoo v5", f"The tuned version reached {num(dg['zoo v5 (bug)']['iqm'])} {ivn(dg['zoo v5 (bug)']['iqm_ci'])}")
claim("E6 zoofix", f"The corrected recipe obtains {num(dg['zoofix v5']['iqm'])} {ivn(dg['zoofix v5']['iqm_ci'])} on Hopper-v5 and "
      f"{num(dg['zoofix v4']['iqm'])} {ivn(dg['zoofix v4']['iqm_ci'])} on Hopper-v4")
claim("E6 default v4", f"The defaults obtain {num(dg['default v4']['iqm'])} {ivn(dg['default v4']['iqm_ci'])} on v4")
claim("E6 plateau", "with a plateau near 1,000")
claim("E6 near 1,000", "all plateau near 1,000")
D("gamma", "the algorithm's discount factor, 0.999")
D("gamma 0.99", "E6 with a discount factor of 0.99")
ofc = J("sim/analysis/e6_official.json")
og, cp = ofc["groups"], {(c["a"], c["b"]): c for c in ofc["comparisons"]}
claim("E6 official", f"evaluated with our protocol, obtain {num(og['official v4']['iqm'])} {ivn(og['official v4']['iqm_ci'])}")
c1, c2 = cp[("official v4", "zoofix v4")], cp[("official v4", "default v4")]
claim("E6 p_improve zoofix", f"with a probability of {num(c1['p_improve'], 2)} [{num(c1['p_improve_ci'][0], 2)}, "
      f"{num(c1['p_improve_ci'][1], 2)}]")
pi2 = c2["p_improve_ci"]
claim("E6 p_improve default", f"beats a default policy with a probability of {num(c2['p_improve'], 2)} [{num(pi2[0]) if pi2[0] == 0 else num(pi2[0], 2)}, "
      f"{num(pi2[1], 2)}]")
claim("E6 holm", f"The gap survives the Holm correction (p = {pv(c2['welch_p_holm'])})")
claim("ten policies", "Ten policies trained by `rl_zoo3.train`")
es = J("sim/analysis/effect_sizes.json")["e6"]
h1, h2 = es["official v4 - default v4"], es["official v4 - zoofix v4"]
claim("E6 HL default", f"is {num(h1['hodges_lehmann'])} [{num(h1['ci'][0])}, {num(h1['ci'][1])}]")
claim("E6 HL zoofix", f"it is {sg(h2['hodges_lehmann'])} [{num(h2['ci'][0])}, {num(h2['ci'][1])}]")
claim("E6 ten runs", "we set ten PPO runs with the default values of Stable-Baselines3 against ten runs")
sp = J("sim/analysis/e6_speed.json")["summary"]
claim("E6 per step", f"earn a median of {num(sp['return_per_step_median_of_seeds'], 3)} per step, from {num(sp['range'][0], 3)} to "
      f"{num(sp['range'][1], 3)} depending on the seed")
D("last 200", "Over the last 200 episodes of each seed, the episodes that reach 1,000 steps")
en = J("sim/analysis/e6_enjoy.json")
o, df = en["groups"]["official"], en["groups"]["default"]
assert o["all_controls_equal"] and df["all_controls_equal"]
claim("E6 speed official", f"forward at a median of {num(abs(o['median_speed']), 2)} m/s, from {num(o['min_speed'], 2)} to "
      f"{num(o['max_speed'], 2)} m/s")
claim("E6 speed default", f"Our default agents run at {num(df['min_speed'], 2)} to {num(df['max_speed'], 2)} m/s")
claim("abstract speed", f"(median speed {num(abs(o['median_speed']), 2)} m/s)")
vo, vd = en["videos"]["official"], en["videos"]["default"]
claim("video official", f"The official agent of seed {vo['seed']} stays upright for {num(vo['episode']['length'])} steps and ends "
      f"{int(hu(abs(vo['episode']['displacement']) * 100))} centimetres behind")
assert vo["episode"]["displacement"] < 0
claim("video default", f"The default agent of seed {vd['seed']} runs {num(vd['episode']['displacement'])} metres in "
      f"{num(vd['episode']['length'])} steps")
hub = J("sim/analysis/e6_hub.json")
mc = hub["model_card_results"]
claim("hub card", f"Its model card reports {num(mc['mean_reward'])} ± {num(mc['std_reward'])} on Hopper-v3")
claim("hub ours", f"it obtains {num(hub['score_10_episodes'])} over ten episodes and {num(hub['score_100_episodes'])} ± "
      f"{num(hub['sd_100'])} over a hundred, all of 1,000 steps, at {num(hub['mean_x_velocity_100'], 2)} m/s")
assert hub["share_full_length_100"] == 1.0
claim("abstract hub", f"runs at {num(hub['mean_x_velocity_100'], 2)} m/s under our protocol")
claim("hub 2022", "trained in 2022 with Stable-Baselines3 1.5.1a8, Gym 0.21 and PyTorch 1.11")
assert "1.5.1a8" in hub["system_info_of_model"] and "0.21.0" in hub["system_info_of_model"] and "1.11.0" in hub["system_info_of_model"]
D("Hopper step", "A step lasts 0.008 seconds. A return close to 1,000 over 1,000 steps")
D("bonus", "a bonus of 1 while the robot stays upright")
D("eight seconds", "in eight seconds")
claim("ten episodes eval", "ten episodes without randomness in the actions")
claim("three times", "nearly three times worse")
assert dg["default v5"]["iqm"] / dg["zoo v5 (bug)"]["iqm"] > 2.5
claim("ten official seeds", "our ten official seeds")

# What is still running, and the protocol (counts fixed in the protocols).
D("98 papers", "reads the 98 papers with experiments")
D("eight new agents", "eight new agents then reread all")
D("eight new readers", "Eight new readers separate the year from the reader set")
D("thirty papers human", "rereads thirty papers, fifteen from each year")
D("89 quotes", "left 89 quotes not found")
D("90% chars", "passes if 90% of its characters")
D("pilot", "A pilot of two papers")
D("checklist", "which NeurIPS adopted in 2019")
claim("three contributions", "Our contributions are three")
claim("three leads", "we wrote down three leads")
claim("four criteria", "Four criteria carry the verdicts")
claim("four gaps", "Four gaps pass the Holm correction")
claim("four practices", "Four practices changed")
claim("four practices 2", "These four practices")
claim("four practices 3", "All four accompany the result")
claim("four of them", "None of these asks for more compute. All four ask")
claim("eight practices", "draws the gaps for eight practices")
claim("twelve criteria", "a second grid of twelve criteria")
claim("eight criteria", "Grid v1 holds Pineau's eight criteria (Q1 to Q8) and seven criteria")
claim("twelve v2", "Grid v2 holds twelve criteria")
claim("three checks", "Three checks ran before any percentage")
claim("two of three", "we keep two here")
claim("two experiments", "Two experiments make the survey concrete")
claim("two instruments", "with two instruments")
claim("fifth", "A fifth criterion also passes")
claim("two intervals", "Two intervals avoid zero")
claim("five groups", "Five groups of work come close")
claim("two papers primary", "except two that finished on a neighbouring model")
claim("fifteen", "fifteen from each year")
claim("seed groups", "the five seeds of each group")
claim("one task", "E6 rests on one task, one algorithm of the collection and one published agent")
claim("single agent", "a single published agent")
claim("abstract 50+50", "and 50 papers from 2018 with the same grids")
claim("100 episodes", "over a hundred")
D("related 74.4", "rose from under 50% to 74.4%")
D("related 400", "score 400 papers from IJCAI and AAAI")
D("related coakley", "track 56,800 papers from five AI conferences from 2014 to 2024: the share that releases code and data rises from "
  "11% to 64%")
D("related marl", "covers 75 papers on cooperative multi-agent RL")
D("related sober", "standard deviations of 5 to 15 points")
D("Atari", "claimed on Atari games")
D("TD", "Pineau's eight criteria")
D("5% threshold", "passes the 5% threshold after this correction")
D("5% level", "at the 5% level")
D("5% promises", "under the 5% it promises")
D("one time in twenty", "one time in twenty")
D("version 1.0", "version 1.0")
D("t of 9", "the t of 9")
D("near 9", "never comes near 9")
D("reaches 9", "No draw reaches 9")
claim("PPO never", "the same script never reaches 9.09")
D("return near 1,000", "A return near 1,000 on Hopper is a robot standing still")
D("version 1.0 b", "like version 1.0 of the technical report")
D("95%", "| 95% interval |")


def body_and_refs(t):
    body, _, refs = t.partition("## References")
    body = re.sub(r"^\d+\. ", " ", body, flags=re.M)                       # numbered list markers
    body = re.sub(r"`[^`]*`", " ", body)                                   # code spans: file names, script names, model ids
    body = re.sub(r"^#+ [\d.]+[a-z]?", " ", body, flags=re.M)               # section numbers
    body = re.sub(r"\b(Section|Sections|Figure|Figures|Table|[Dd]eviations?|item)\s+[\d.]+(\s*(and|to|,)\s*[\d.]+)*", " ", body)
    body = re.sub(r"\b(?:Q|X|Y)\d+\b", " ", body)                           # criterion codes
    body = re.sub(r"\b(?:Hopper|Walker2d|HalfCheetah|Swimmer)-v\d\b", " ", body)
    body = re.sub(r"\b(?:ppo-Hopper-v3|pass@\d+|claude-opus-\d(?:-\d)?|BSD 3-Clause|sb3-contrib)\b", " ", body)
    body = re.sub(r"\b(?:19|20)\d\d\b", " ", body)                          # years
    body = re.sub(r"\b(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December)\b", " ", body)
    return norm(body), norm(refs)


fails = 0
body, refs = body_and_refs(RAW)
work = body
for label, ph, kind in sorted(C, key=lambda c: -len(c[1])):
    p = norm(ph)
    if p not in TEXT:
        print(f"MISSING ({kind}) {label}: «{p}»")
        fails += 1
        continue
    if kind == "doc":
        for n in re.findall(r"\d+(?:[.,]\d+)*", p):
            if n not in REPORT_NUMS and n.replace(",", "") not in REPORT_NUMS and not re.fullmatch(r"(19|20)\d\d", n):
                print(f"NOT IN THE REPORT {label}: {n}")
                fails += 1
    pb, _ = body_and_refs(p)
    work = work.replace(pb.strip(), " ")
NUM = r"(?<![\w.])[−+-]?\d+(?:[,.]\d+)*%?"
left = re.findall(NUM, work)
for n in left:
    i = work.find(n)
    print(f"UNSOURCED number «{n}» near «{work[max(0, i - 60):i + 30]}»")
fails += len(left)
for line in refs.split(" - ")[1:]:
    for n in re.findall(r"\d+(?:\.\d+)*", re.sub(r"`[^`]*`", " ", line)):
        if n not in BIB:
            print(f"reference number «{n}» not in report/refs.bib: {line[:80]}")
            fails += 1
print(f"{len(C)} claims checked, {len(re.findall(NUM, body))} numeric tokens in the body")
print("OK: every number of the short paper has a source" if not fails else f"{fails} failure(s)")
sys.exit(1 if fails else 0)
