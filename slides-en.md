*Translation of [slides.md](slides.md), made on 10 November 2026. The French text is the original.*

# The slides of Joelle Pineau's talk, ICLR 2018

Invited talk, ICLR 2018, Vancouver, Thursday 3 May 2018:
"Reproducibility, Reusability, and Robustness in Deep Reinforcement Learning".
Video: https://www.youtube.com/watch?v=Vh4H0gOwdIg (49 min 22 s), local copy `video/talk.mp4`.

Inventory reconstructed on 8 November 2026 from the video: shot-change detection on the slide
area alone (`ffmpeg`, 960 × 720 crop on the left, scene threshold 0.04), then a few frames taken
by hand in the gaps. The frames are in `video/slides-scan/` (s-NNN.jpg, timestamps in
`video/slides-scan/times.txt`) and `video/gaps/`; the first eleven, extracted by the other session,
are in `video/frames/` (their `times.txt` is empty). Three full-resolution frames of the key slides:
`video/slide23-full.png`, `video/slide30-full.png`, `video/slide31-full.png`.

Numbers 25 and 26 corrected on 9 November 2026 from the frame at 25:30, where number 26 can be read on "How should we measure…". The number is the one printed at the bottom of the slide when it is legible; otherwise it is
inferred from the order (marked "~"). Slides 1, 2, 7, 10, 11, 27 and 32 never appear legibly
on screen (title, transitions, or a slide skipped too fast).

| No. | Timestamp | Frame | Title and content |
|---|---|---|---|
| 3 | 2:47 | s-001 | Reproducibility crisis in science (2016): Nature donut chart, 1,576 researchers, **52%** "yes, a significant crisis", 38% "slight", 7% don't know, 3% no. (Out loud she says "50%": the slide says 52%.) Link nature.com/news/1-500-scientists-lift-the-lid-on-reproducibility-1.19970 |
| 4 | 3:16 | s-002 | Same donut + bars "Have you failed to reproduce an experiment?" by discipline (chemistry, biology, physics, medicine, earth, other), "someone else's" against "my own" |
| 5 | 4:15 | s-003 | Reproducibility crisis in ML? Pie chart "ML Experts (n=20)": 45% slight, 35% significant, 10% no, 10% not sure (so 80% "crisis") |
| 6 | 4:51 | s-004 | A criteria for reproducible research: "An article about computational science in a scientific publication is not the scholarship itself, it is merely the advertising of the scholarship." Buckheit and Donoho, *WaveLab and reproducible research*, Stanford, 1995 |
| 8 | 6:48 | s-005 | 25 years of RL papers: histogram of the number of RL papers per year (Google Scholar), 1990 to 2016, close to 14,000 in the last year; two asterisks around 2000 (her beginnings); ref. Henderson et al., AAAI |
| 9 | 8:17 | s-006 | Impressive results! AlphaGo (2016): game against Lee Sedol, Nature cover "All systems Go" |
| ~10 | 9:05 | s-007 | Got the blueprints!: same visual + first page of the Nature paper "Mastering the game of Go with deep neural networks and tree search" |
| 12 | 10:49 | s-008 | Fermat's last theorem (1637): statement + annotated page of Diophantus's Arithmetica |
| 13 | 11:28 | s-009 | Same + Guinness logo "Longest standing maths problem (ever)! Until 1995 when Andrew Wiles published a proof, after 358 years" |
| 14 | 12:21 | s-010 | Eureka!: photos (pupils in front of a screen, a child raising both arms) + learning curves |
| 15 | 13:18 | s-011 | Reusable platforms for RL: Robot soccer (partial obs.), MuJoCo (Todorov et al. 2012; Half Cheetah, Walker), Arcade Learning Environment (Bellemare et al. 2013), ELF (Tian et al. 2017) |
| 16 | 15:07 | s-012 | The thesis: "REUSABLE material (software, datasets, experimental platforms) help us REPRODUCE scientific methods to establish the ROBUSTNESS of the findings." |
| 17 | 15:42 | s-013 | RL setting: Policy gradient methods: policy gradient equation, on-policy / off-policy actor-critic diagrams |
| 18 | 17:09 | s-014 | Policy gradient papers: 11 recent papers, 7 of them accepted at ICLR 2018; "Most papers use same policy gradient baseline algorithms." |
| 19 | 18:24 | s-015 | Policy gradient baseline algorithms: TRPO (Schulman 2015), PPO (Schulman 2017), DDPG (Lillicrap 2015), ACKTR (Wu 2017) |
| 20 | 18:58 | s-016, s-017 | Robustness of policy gradient algorithms: HalfCheetah curves, Alg.1 to Alg.4 anonymised + video of the Half Cheetah (19:27) |
| 21 | 20:08 | s-030 | Same + Hopper and Swimmer: the ranking flips; on Swimmer, the red algorithm (best on HalfCheetah) learns nothing |
| 22 | 21:33 | s-031 | Codebase comparison: screenshot of a GitHub search for "TRPO" (about ten repositories) + HalfCheetah-v1 curves (TRPO, Codebase Comparison), three implementations |
| 23 | 22:23 | s-032 | Codebase comparison: TRPO implementations (3 curves) and DDPG implementations (3 curves) on HalfCheetah |
| 24 | 22:48 | s-033 | Effect of hyper-parameter configurations: network structure (64,64), (100,50,25), (400,300) for PPO; activation tanh, relu, leaky_relu for TRPO |
| 25 | 23:30 | s-034 | An intricate interplay of hyper-parameters: DDPG, reward scale with and without layer norm; in red "When testing a baseline, how motivated are we to find the best hyper-parameters?" |
| 26 | 25:20 | s-035 | How should we measure performance of the learned policy?: HalfCheetah curves Alg.1 to 4 |
| 28 | 26:30 | s-036 | How many trials?: table of 7 papers (names masked in yellow): top-5, 3-9, 5 (5), 3, 5, 5, top-2 / top-3 |
| 29 | 27:07 | s-037 | Consider the case of n=10: ten curves, one "Baseline to beat" line |
| 30 | 27:45 | gaps/g-002745 | Same + "Top-3 results": "Strong positive bias: seems to beat the baseline! Variance appears much smaller." |
| 31 | 28:23 | s-038, slide31-full.png | Let's look a little closer: two curves with bands, orange above blue, "n=5" and "n=5". Out loud: same TRPO code, same hyperparameters, only the random seeds change |
| 33 | 29:26 | s-039 | Simulation ➜ Real-world: medical treatment design, intelligent transportation, energy & resource management, financial systems |
| 34 | 31:08 | s-040 | "Science aims to understand and explain. Science as a collective institution aims to produce more and more accurate explanations of how the world works." |
| 35 | 32:09 | s-041 | ELF OpenGo: open source Go playing bot (github.com/pytorch/elf), Tian, Ma, Gong, Sengupta, Chen, Zitnick; "System can be trained with 2000 GPUs in 2 weeks" |
| 36 | 33:20 | s-042 | ELF OpenGo: "Performance vs top professional players: 14-0 record (April 2018). Single GPU, 80k rollouts, 50 secs"; Kim Ji-seok (#3) 3-0, Shin Jin-seo (#5) 2-0, Park Yeonghun (#23) 4-0, Choi Cheolhan (#30) 5-0; "vs strong bot (LeelaZero): 200-0 record" |
| 37 | 34:31 | s-043 | ICLR 2018 reproducibility challenge: OpenReview screenshot, ICLR 2018 submissions |
| 38 | 36:18 | s-044 | Survey from the reproducibility challenge: 54 participants, 30 authors, 14 others; before (n=98): 49% slight, 22.4% significant, 11.2% no, 17.3% not sure; after: 51% opinion unchanged, 29.8% more convinced |
| 39 | 37:07 | s-045 | Successful? 54.5% "reproduced some", 32.7% "most", 9.1% no. Difficult? 44.4% reasonable, 22.2% very difficult, 31.5% mild |
| 40 | 37:53 | s-046 | Same + participants (n=54): confidence in their conclusions, 53.8% moderate, 34.6% high |
| 41 | 38:09 | s-047 | Authors (n=27): "Do you TRUST the validity of the reproducibility report?" **59.3% yes** (out loud she says "69%"), 18.5% no, 14.8% not sure; Authors (n=26): "61% said yes" to updating the paper |
| 42 | 39:05 | s-048 | All (n=98): mechanisms: 46% course project, 36% open call with prizes, 11% interest in quality, 7% handing replication to reviewers |
| 43 | 39:28 | s-049 | Authors (n=28): 79% yes for ICLR 2019, 14% maybe, 8% no; verbatim comments |
| 44 | 39:56 | s-050 | What can you do? Share reusable material; "be as critical of the 'good' results as the 'bad' results"; contribute to the reproducibility effort |
| 45 | 40:36 | s-051 | Contributors: Peter Henderson, Riashat Islam, Phil Bachman, Doina Precup, David Meger; ELF OpenGo team; Genevieve Fried, Rosemary Nan Ke, Hugo Larochelle; Reasoning and Learning Lab, McGill |
| | 41:31 | s-052 to s-055 | Questions from the floor (shots of the speaker and the audience) |

## Gaps between the spoken talk and the slides

- Nature 2016: 52% on the slide, "50%" out loud.
- Authors' trust in the challenge reports: 59.3% on the slide, "69%" out loud.
- TRPO implementations: the GitHub screenshot shows about ten repositories, the curves compare
  three (as does the paper by Henderson et al., which compares Schulman's original
  implementation, the OpenAI Baselines one and the rllab one; for DDPG, rllab Theano,
  rllabplusplus and OpenAI Baselines).

## Official copy of the slides: found (NeurIPS 2018 version)

Reference copy filed by Warith: `slides/neurips2018-pineau.pdf` (same file), with checklists v1.2 and v2.0 and the ICLR 2018 challenge page retrieved from the Wayback Machine, in `slides/`.

- **Official PDF of the NeurIPS 2018 version**, hosted by NeurIPS:
  https://media.neurips.cc/Conferences/NIPS2018/Slides/jpineau-NeurIPS-dec18-fb.pdf
  (58 pages, 3.7 MB), local copy `jpineau-NeurIPS-dec18-fb.pdf`, pages rendered as
  thumbnails in `neurips2018-pages/`. Posner lecture, "Reproducible, Reusable, and Robust
  Reinforcement Learning", Montréal, 5 December 2018. NeurIPS video:
  https://videoken.com/embed/jH0AgVcwIBc
- This deck is the NeurIPS one. Still, its pages 10 to 26 repeat slides 8 to 31 from Vancouver
  almost identically (same figures from Henderson et al.). Page 22 spells out what she said out
  loud in May: "Both are same TRPO code with best hyperparameter configuration!". Additions
  found only at NeurIPS: a link to Alex Irpan's blog post "Deep Reinforcement Learning Doesn't
  Work Yet" (p. 27), the survey of 50 RL papers from 2018 published at NeurIPS, ICML and ICLR
  (pp. 29 and 30: code linked 55%, method for choosing hyperparameters 20%, evaluation on a
  held-out set 10%, significance test 5%), the first reproducibility checklist (pp. 31 to 33)
  and "Myth or fact? Reinforcement Learning is the only case of ML where it is acceptable to test
  on your training set" (pp. 36 to 39, 51).
- ICLR listing (https://iclr.cc/virtual/2018/invited-talk/346): Thursday 3 May 2018, 9:00 to
  9:45 a.m., Exhibition Hall A; no link to slides.
- Joelle Pineau's page at McGill (https://www.cs.mcgill.ca/~jpineau/): no link to the ICLR deck
  found. The page of the 2018 challenge exists:
  https://www.cs.mcgill.ca/~jpineau/ICLR2018-ReproducibilityChallenge.html
- The Vancouver deck itself (ICLR, about 45 slides) is still nowhere to be found as a PDF;
  the inventory above, taken from the video, stands in for it.

The figures of slides 20 to 31 come from Henderson et al., "Deep Reinforcement Learning that
Matters", AAAI 2018 (arXiv 1709.06560): figure 5 for the two random seeds (t = -9.09,
p = 0.0016), figure 6 for the implementations, table 3 for the per-task ranking, table 7 for the
number of trials in published papers.
