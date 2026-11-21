# Eyeball loop of the report's figures in Latin Modern (DRAW_FONTS=latex)

All 30 figures of the report plus flux-sondage-2 and architecture-2, French and English: 60 PDFs, each looked at
after rendering with `pdftoppm -r 150` (pass 1, French; English at 110 to 150 dpi), then again after the fixes
(pass 2). Every text is Latin Modern (Roman 12 bold for titles, Roman 10 regular, demibold and bold, Mono 10 for
code), the site's name aside (Satoshi bold); `pdffonts` on every PDF lists only LMRoman*, LMMono* and the Satoshi
subset (tools/figures.py now fails the build otherwise). No text under 13 px at 760 px width.

Mechanical checks, last run: `tools/check_bounds.py` (every text, measured in Latin Modern, inside the canvas and
its panel, at least 4 px from a text beside it): 60 SVG, no finding. `sprezzature-figures check`: no overlap, no
clipping, no missing title; left: grey source lines and house-palette contrast notes (accepted), and one
`identical_adjacent_labels` on flux-sondage-2-en ("10", "10", "10": three cards that each read ten papers, true
data, not an axis). Two runs give byte-identical SVGs.

Fixes made in the loop, by figure: e1-graines (median label on the note's baseline), physique-modifiee (labels
spread 4 px further for the 13 px values), trajectoire (NeurIPS note on one line above the plot: two lines crossed
the top series), e5-graines (label column measured: "médiane, 8 proches" ran off the canvas and "médiane, toutes"
into the right panel's ticks), e7-carte (verdict in demibold: "no detectable change" in bold overflowed its cell),
ecarts-pineau and remesure-ic (label column measured: the bold labels started left of their band), dose-carte
(label column measured: "HalfCheetah" touched "PPO (PyTorch)"), b1-distribution (row label clear of the first bin,
"au-delà : 37,8 % du script" inside the right margin), forest-criteres (gap axis numbered every 30 points, not 15:
13 px numbers were crowding), flux-sondage and flux-sondage-2 (years in Roman, not typewriter; card text on the
line grid of the card beside). Everywhere: Latin Modern's U+00A0 is a figure wide, so the latex set prints a thin
space (U+202F, added to the subsets) in 1 580, 5 %, before ; ! ? and inside « », a word space elsewhere.

## e1-graines
Pass 2: no overflow: yes. Median label and red note share a baseline; ticks and extreme values clear of the dots.

## e1-faux-positifs
Pass 2: no overflow: yes. Four waffles, values and labels centred under each, the dashed 5-square frame legible.

## t-de-neuf
Pass 2: no overflow: yes. "TRPO, script de 2017" wraps under its waffle in French, one line in English.

## meilleurs-sur-dix
Pass 2: no overflow: yes. Legend on one line, "PPO (JAX) +84 %" above its dot, median label right of its line.

## classement-taches
Pass 2: no overflow: yes. Four panels, names right-aligned, "1er/1st" in white on the leading bar, values after bars.

## physique-modifiee
Pass 2: no overflow: yes. Name and value lines of each program 4 px further apart; right column labels clear.

## intensites
Pass 2: no overflow: yes. Peak label above its point, end labels "Masses"/"Frottements" clear, ticks to −40 %.

## grpo-graines
Pass 2: no overflow: yes. Subtitle on two lines, value labels above the arrow heads, key on one line.

## grpo-coupure
Pass 2: no overflow: yes. "23 sur 32" and its three-line note right of the squares.

## grille-egale
Pass 2: no overflow: yes. Bands hold their labels, values right of the intervals.

## trajectoire
Pass 2: no overflow: yes. NeurIPS note above the plot on one line; five end labels spread, none on a line.

## courbes-apprentissage
Pass 2: no overflow: yes. 4 x 4 panels, "1er" chips and values above the panels, scales outside the curves.

## forest-criteres
Pass 2: no overflow: yes. Labels inside the green bands; gap axis −30, 0, +30, +60 clear of "100 %".

## accord-lecteurs
Pass 2: no overflow: yes. Column heads on two lines, kappas right of the squares, tallies under each column.

## e5-graines
Pass 2: no overflow: yes. Direct labels in a measured column between the panels; tick labels of the right panel clear.

## e7-carte
Pass 2: no overflow: yes. Verdicts in demibold inside every cell, gauges and asterisks clear.

## dose-carte
Pass 2: no overflow: yes. Task names and program names in a measured column, loss counts under each map.

## b1-distribution
Pass 2: no overflow: yes. Row labels clear of the histograms; the shares beyond Henderson's line end inside the margin.

## grpo-courbes
Pass 2: no overflow: yes. End labels spread 16 px apart, annotation of the stopped run with its leader.

## e1-henderson
Pass 2: no overflow: yes. Labels left of the bars, the published-t label above its dashed line.

## ecarts-classique
Pass 2: no overflow: yes. Seventeen rows, legend and direction heads on one line each.

## ecarts-pineau
Pass 2: no overflow: yes. Label column widened to the bold red labels, which now start inside their band.

## remesure-dumbbell
Pass 2: no overflow: yes. Percentages either side of each dumbbell, gap column at the right.

## remesure-ic
Pass 2: no overflow: yes. Label column widened to "Références réglées comme la méthode".

## grpo-truncation
Pass 2: no overflow: yes. Products, counts "7/8", the big "23 sur 32" and its note.

## flux-sondage
Pass 2: no overflow: yes. Years 2019 to 2024 now in Roman beside their bold counts; every card's text inside.

## flux-sondage-2
Pass 2: no overflow: yes. The "38 agents" card text now on the same baselines as the card beside.

## frise-ecarts
Pass 2: no overflow: yes. Numbered dots inside their day rows, milestones wrapped in their column.

## architecture
Pass 2: no overflow: yes. Code in Latin Modern Mono inside every card, "make analysis" chip on the rule.

## architecture-2
Pass 2: no overflow: yes. Chips on their rules, the dark CI card's text inside it.
