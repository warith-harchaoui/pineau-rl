# Eyeball loop: the three diagrams (tools/diagrams.py)

Each diagram rendered through the report's own route (tools/svg2pdf.py, headless Chromium, then pdftoppm), looked
at in French and English, one honest line per look, fixed, rendered again.

## Iteration 1

- flux-sondage fr: readable flow, but the trajectory population shows the counts before the title screen (135, 223,
  311, 413) while the label says after it; the column descriptors of the header collide ("NeurIPS 2025" runs into the
  third dot); "entrent" sits alone on its line; the accent strip pokes out of the rounded corners.
- flux-sondage en: same structure; the 2018 and trajectory draw cells are half empty beside the tall 2026 cell.
- frise-ecarts fr: strong at once, numbered dots read well, hollow undated dots clear; the title leaves "jours" alone
  on its second line; the weekday labels are not aligned (they follow the width of the day number).
- frise-ecarts en: same; nothing else.
- architecture fr: drafted, not designed: mono paths overflow their cards ("article/check_article.py",
  "sim/llm/results/*.json"), the make verify pills sit on top of their own text, the make test pill hangs off the
  package card, the gutter eats a quarter of the width.
- architecture en: same faults.

## Iteration 2

- flux-sondage fr: counts now right (134, 222, 301, 374 after the title screen), header clean; the trajectory draw
  cell still ends on "entrent" alone, the title breaks inside "chaque décision".
- flux-sondage en: draw cells filled with true facts (no replacement needed in 2018; 24 read per year, ICLR missing);
  good rhythm, one colour per stream, grey bands where the streams join.
- frise-ecarts fr: title on one line, weekdays aligned; the lane counts "20 écarts" crowd the lane names.
- frise-ecarts en: "Simulations" and "20 deviations" collide in the header.
- architecture fr: rebuilt with level labels above the rows and make targets as pills beside them: paths fit; the
  JSON bus runs over the "make check" pill; arrows touch the "make docs" and "make figures" pills.
- architecture en: title leaves "push" alone; the CI card is half empty next to the make verify card.

## Iteration 3

- flux-sondage fr: designed: three coloured streams, seeds pinned to the foot of each draw card, every count from a
  file; secondary grey darkened to clear 4.5:1; title breaks after the comma. Spectacular enough to print.
- flux-sondage en: same; the three "10" of the double readings are real (three samples of ten), the checker's
  "identical labels" finding is a false alarm.
- frise-ecarts fr: lane counts as coloured figures, orange darkened until white numbers clear 4.5:1; the 35 dots of
  the first two days carry the title at a glance. Spectacular.
- frise-ecarts en: same; nothing left.
- architecture fr: clear six-level pipeline, bus before the checks, arrows clear of the pills, tables.py marked as run
  by make report (it is not under make check), tests aligned with the check row. Spectacular.
- architecture en: title breaks after the comma, CI card filled with the workflow's real steps. Spectacular.

## Converted figures (PDF through headless Chromium, one look each)

- The 11 article figures (FR, EN): faithful, Roboto Serif semibold title, Roboto, Roboto Mono, Satoshi signature,
  same layout as the SVG.
- The 6 docs figures (FR, EN): faithful to their SVG, which asks for "LM Roman, Latin Modern Roman, Georgia" and
  "LM Mono, ui-monospace": Chromium falls back on Georgia and Courier, as rsvg-convert did with Georgia and Menlo. The
  overlap of "18" and "60" in remesure-dumbbell is in the source SVG.
- The 8 new data figures of tools/new_figures.py (FR): converted faithfully.

## Follow-up: publication on 21 November, the six docs figures in the house style

- frise-ecarts fr, iteration 4: the 21st now has two milestones, the end of training and "Article publié sur
  deraison.ai" in bold with a red dot; no 24 November left in the figure, its description or its source line.
- frise-ecarts en, iteration 4: same; the publication reads as the last event of the timeline.
- Docs figures, iteration 1 (tools/docs_figures.py, FR and EN): ecarts-classique with the four Holm-passing rows
  banded green reads at once; ecarts-pineau and remesure-dumbbell clear, the old "18"/"60" overlap gone (each value
  sits outside its own dot); remesure-ic good; grpo-truncation good; e1-henderson good. Faults: source lines wrap on
  a second line for the CSV paths, the GRPO title says "run past 160 tokens" where the data say "cut at 160 tokens",
  the Henderson chart starts too low under its subtitle; the tick labels of the first Henderson draw (draw.hbars)
  are in the light grey that fails 4.5:1.
- Docs figures, iteration 2: own bars for e1-henderson (ticks in the darker grey, the 2018 t as one dashed line
  across every bar), titles fixed, sources on one line. All twelve SVGs clean apart from the accepted grey source
  line. Spectacular: every title states the finding, one accent per figure, the highlighted rows carry the story.

## Print sizes: every text 13 px or more, no figure taller than 1.35 times its width

- Iteration 1, measured: every text of the five diagrams is 13 px or more (7.5 pt in print). Heights, 760 px wide:
  flux-sondage 881 and 833, flux-sondage-2 921 and 886, frise-ecarts 936, architecture 952, architecture-2 886 and
  868 (FR, EN). The house footer is redrawn at 13 px (draw.py untouched).
- flux-sondage fr: the draws now stand alone on one page; big counts, seeds at the foot of each card. The three
  family chips of 2026 stack one per line, which the 220 px column forces at 13 px: acceptable.
- flux-sondage-2 fr: reading, double readings, harmonisation, checks, comparisons; texts shortened without losing a
  count, column heads repeated so the reader keeps the three samples in mind. Clear.
- frise-ecarts en: dots 25 px with 13 px numbers, milestones shortened to fit 176 px; reads at once in print.
- architecture fr: producing and analysing, then the shared package as a table of its five modules. Good.
- architecture-2 en: one finding, the CI card's first line 3 px off the make verify pill, then a second near miss.
- Iteration 2: both baselines aligned; sprezzature check clean apart from the accepted grey source line and the
  three genuine "10" counts. Readable in print, still designed.

## Print sizes for the six redrawn docs figures

- Iteration 1: every size under 13 px raised to 13 (ticks, values, axis notes, the "écart" column head, the footer
  through the 13 px house footer of diagrams.py); all six stay well under 1.35 times their width (0.57 to 0.97).
  One near miss: the "23 sur 32" note of grpo-truncation sat 10 px off the 5/8 of its rows.
- Iteration 2: the note's lines now share the baselines of rows 2 and 3; the last 12.5 px value of e1-henderson
  raised. Checks clean apart from the accepted grey source line; readable in print, layout unchanged.
