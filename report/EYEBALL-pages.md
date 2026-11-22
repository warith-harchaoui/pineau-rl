# Ralph eyeball loop: pages of the French report (rapport.tex)

## Pass of 22 November 2026 (consolidation of the French writing wave)

Build: `latexmk -lualatex -outdir=build/fr-final rapport.tex`, 211 pages, 0 overfull box, 0 undefined reference
or citation, 0 multiply defined label, no « ?? » in the `pdftotext` output. Every page rendered at 40 dpi in
contact sheets of 12 (18 sheets), suspicious pages at 55 dpi.

| Page(s) | Issue | Fix |
|---|---|---|
| ch. 4, X8 paragraph (section 4.2) | the X8 table (4.3) and figure (4.3) landed five and seven pages after their paragraph, behind the four large floats of the main comparison (tables 4.1, 4.2, figures 4.1, 4.2) | `\fig{x2-x8}` now comes before `\gentable{x8}` in fr/04, so the figure, which carries the argument, is placed first: figure 4.3 now on p. 40, table 4.3 on p. 41, table 4.4 on p. 42; the float queue of section 4.2 stays dense (seven floats for about four pages of text) |
| ch. 4 to 11 | the 16 new generated tables and 6 new figures | each included exactly once (tables 4.3 x8, 4.4 difference-detectable, 4.6 q5-versions, 4.8 regle-origine, 4.12 accord-intervalles, 5.1 hyperparametres, 5.2 regle-tranche, 6.2 e1-grille, 6.6 e2-strict, 6.8 e3-holm, 6.9 e3-puissance, 6.12 e5-hors-echantillon, 6.14 e6-vitesse, 6.16 e7-test, 7.2 grpo-mesures, 7.3 grpo-contraste), none overflowing |
| annex B, table B.2 | new tables named by file name | now `\Cref{tab:...}`: « Tableau 4.12 », etc. |

Checked and left as is: chapter ends with a short last page (ch. 3, 4, 5, 10, 11), which move with every edit; the
longtable of the deviations (9.1) starting with five rows at the foot of p. 155, as allowed by the `\Needspace`
rule; the generated captions that still contain a « , et » (gen/fr/regle-tranche, sondage-lrl, calcul, e4 and ecarts are
generated: to be fixed in `report/tools/tables.py`, not here).

## Pass of 21 November 2026

State on 21 November 2026, after three full passes (every page at 40 dpi in contact sheets of 12, suspicious pages
at 60 to 90 dpi). Build: `latexmk -lualatex -outdir=build/full rapport.tex`, 168 pages (8 roman + 160 arabic),
0 overfull box, 0 undefined reference, 0 multiply defined label.

## Issues found and their fix

| Page(s) at the time | Issue | Fix |
|---|---|---|
| ch. 4, tableau 4.1 caption | « tableau ?? »: tab:sondage-pineau-contexte never included | `\gentable{sondage-pineau-contexte}` in fr/04, section 4.5, after the list of the six gaps |
| ch. 4 and annex B | tab:sondage-lrl included twice (multiply defined label) | kept in chapter 4 next to its discussion, removed from annex B (B.1 now points to it) |
| p. 25 (old) | figure 3.1 (flux-sondage, 760 x 1442) taller than the page: ran 246 pt into the footer | `\fig` caps every figure at 0.86 `\textheight` (keepaspectratio) |
| p. 130 (old) | figure 8.1 (architecture) caption ran into the footer (64 pt too tall) | same cap |
| p. 44, 52, 103, 109, 111, 123, 124, 126 (old) | float pages holding one small figure over a blank half page | float parameters (topfraction 0.88, textfraction 0.1, floatpagefraction 0.72, topnumber 3) and float pages filled from the top |
| p. 39 (pass 1) | table 4.1 floated above the heading of its own section | `flafter`: no float before the text that calls it |
| tables 4.1, 4.2 | « Critère » wrapped over three lines next to wide number columns; tables vertically centred | generator: text column as a tabularx X column, % and interval in two aligned columns, gap and interval likewise, group headers on two lines, `[a ; b]` with thin spaces, p-values below 1e-4 in the text font instead of Computer Modern math |
| tableau 4.4 (contexte) | criterion and comparison in two narrow columns, three-line labels | one group row per criterion, its two comparisons indented below |
| tableau 4.6 (trajectoire) | numbers spread, criterion squeezed | X column |
| tableaux 6.3, 7.1 | 4.2 pt and 1.3 pt too wide | tabcolsep 3.4 pt and 3.2 pt |
| tableau D.2 | `\small` where every other table is `\footnotesize` | `\footnotesize` |
| p. 17 to 18 (pass 2) | table 2.2 (longtable) started with caption and header alone at the foot of a page | `\Needspace*{14\baselineskip}` before every longtable |
| table of contents | 30 overfull lines (three-digit page numbers, « 5.10.10 »); 3 pages + 1 line alone on a 4th | wider page-number and number boxes; no `\parskip` inside the TOC (now 3 full pages) |
| pages i and 1 | duplicate PDF anchor « page.i » (title page and abstract) | no page anchor on the title page |
| everywhere | `\paragraph` headings with 1.3 lines of space above | tighter `\paragraph` spacing |
| EN build | three paths 7 to 15 pt into the margin | `\file{}` may break after « / » and « _ » (fixes two of three in English, none left in French) |

## Remaining, not fixable in the layout

- Figure text size. The house figures are 760 px wide with labels of 11 to 12 px: at text width (443 pt) 1 px is
  0.58 pt, so most labels print at 6.4 to 7 pt. Smaller than 6 pt: flux-sondage (4.1 pt, the figure must shrink to
  fit the page), architecture (5.0 pt, same reason), courbes-apprentissage and dose-carte (5.2 pt, 9 px labels),
  frise-ecarts and grpo-courbes (5.8 pt). They need print versions (fewer, larger labels or a narrower viewBox).
- Chapter ends with two to five lines on their last page (ch. 1, 2, 9, 10, annex B): left as is, they move with every
  edit of the text.
- 48 underfull lines (badness up to 10000) in table cells with narrow ragged columns and code paths; none visible.
- Font warning « RobotoSerif/m/sc undefined »: one caption label asks for small caps in the serif font; it falls back
  to upright, invisible.
- Mathematics are set in Computer Modern next to Roboto Serif: a matching math font would be a design decision.

## Résumé en français

Trois passes complètes sur les 168 pages. Corrigés : le tableau manquant 4.4 (« ?? »), le tableau 4.5 inclus deux
fois, deux figures plus hautes que la page, les pages de flottants presque vides, un tableau placé avant le titre de
sa section, les colonnes de critères sur trois lignes, les nombres mal alignés, deux tableaux trop larges, la table
des matières qui débordait, un tableau long coupé juste après son en-tête, les chemins de fichiers qui débordaient
dans la version anglaise. Restent : le texte des figures maison, imprimé entre 6,4 et 7 points et à moins de 6 points
pour six figures, à redessiner pour l'impression ; quelques fins de chapitre de deux à cinq lignes.
