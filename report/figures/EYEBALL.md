# Eyeball loop of the new data figures (report/tools/new_figures.py)

One section per figure, overwritten at each iteration: the latest honest verdict.

## courbes-apprentissage
Iteration 6 (FR and EN, PDF rendered at 150 dpi): print pass (every text 13 px or more, 7.5 pt at text width; 760 x 988): spectacular? yes, because the tinted leader panels still carry the title, scales now read in print with two labels per panel (half and top) set outside the curves, one budget label per pair of rows; Chromium PDF checked.

## forest-criteres
Iteration 3 (FR and EN, PDF rendered at 150 dpi): spectacular? yes, because the four Holm rows stand as a green block at the top of a gap-sorted list, the dumbbells show where each share came from and went, the diff column with its zero line makes the 'interval clears zero' test visible; title fits in the PDF after the narrower serif wrap; numbers glued to their nouns in the subtitle.

## accord-lecteurs
Iteration 4 (FR and EN, PDF rendered at 150 dpi): spectacular? yes, because 675 grey squares and 29 red ones make agreement and its exceptions countable at a glance; kappa appears only where readings differ, red under 0.70; the per-column tally (3, 7, 8, 11) closes the table; title broken by sense group.

## e5-graines
Iteration 4 (FR and EN, PDF rendered at 150 dpi): spectacular? yes, because the two red medians sag far below the black one while the grey lines pile up at 100%, the dashed coin-flip line gives the floor (one twenty-seed pair even dips under it), direct labels replace any legend; title split by sense group on two lines in both languages.

## e7-carte
Iteration 4 (FR and EN, PDF rendered at 150 dpi): spectacular? yes, because the Hopper and Walker2d columns darken where PPO keeps a fifth to a third of its score, Swimmer stays pale or green, each cell carries number, interval, verdict and a gauge with its 100% tick, so colour is never the only code; the two verdicts that change with twenty seeds are flagged and spelled out; ink text now clears contrast on every cell.

## dose-carte
Iteration 6 (FR and EN, PDF rendered at 150 dpi): print pass (every text 13 px or more; 760 x 1015): spectacular? yes, because the two maps now stack on shared columns at full width, so 42 px cells carry 13 px strength labels and program names, the loss counts sit as a bold red row under each map, the red pools (heavy masses, Hopper friction) read even more clearly than side by side.

## b1-distribution
Iteration 3 (FR and EN, PDF rendered at 150 dpi): spectacular? yes, because the two humps sit a decade apart on TRPO and the 37.8% of script draws beyond Henderson's 9.09 are painted solid red against 0% between seeds, while PPO shows that even the script stays short; labels sit in a reserved band above each histogram, no collision; the recomputed distributions match b1_trpo.json and b1_script.json to the last digit (asserted).

## grpo-courbes
Iteration 6 (FR and EN, PDF rendered at 150 dpi): print pass (every text 13 px or more; 760 x 842): spectacular? yes, because the same two opposite stories hold with larger end labels spread 16 px apart, one shared vertical scale per row, annotations and note at 13 px; Chromium PDF checked.

## e1-grille
Iteration 2 (FR and EN, PDF rendered at 110 dpi, Latin Modern): spectacular? yes, because sixteen dumbbells run from a hollow circle stuck under the dashed 5 % line to a filled dot in the program's colour, so the spread of the sorted rate (26 % to 99,8 %) reads at once, and the highlighted preregistered pair sits at the low end; seeds moved to the subtitle so the note no longer leaves "à 19." alone on its line; title shortened to fit the PDF in English.

## e6-vitesse
Iteration 3: spectacular? yes, because nine of ten official dots stack on the 0 m/s line beside a right column that says 997 and 994, while the default dots sit at 2.5 to 2.9 m/s and the 2022 hub agent at 1.44; fixed: "1 000" broke across lines in the subtitle (now glued), the fall labels crossed the swarm (now under the row, with a pale leader), the default median label crossed its dots (now below the swarm).

## e6-images
Iteration 2: spectacular? yes, because the same four steps show a straight pole on the same square against a leaning, running hopper; fixed: the note touched the step labels of the last row (sprezzature labels_overlap), moved down 16 px. Frames come from the repository's MP4s through ffmpeg (bitexact), cropped 200 x 200 around the robot.

## q5-lectures
Iteration 1: spectacular? yes, because every reading keeps its interval right of zero (+30 to +43) and the 2018 hollow circles all stay left of Pineau's dashed 55 % line; bounds indented in pale green under their reading; nothing to fix.

## x2-x8
Iteration 2: spectacular? yes, because the 2026 waffle fills with red "not stated" squares while green "over seeds" squares barely grow (17 to 21), and the two gap bars below make the contrast exact (+26 passes Holm, +7 crosses zero); fixed: squares enlarged to use the width, key and gap header spaced apart, French title reworded ("celles calculées sur des graines à peine").

## grpo-mesures
Iteration 1: spectacular? yes, because in the Llama true-reward panel the pass@1 bar straddles +6 while greedy and pass@8 sit far below zero, and the coin-flip column shows every measure falling with tight intervals; the thin percentile bar beside each thick Student bar shows how much narrower the protocol's interval was; nothing to fix.
