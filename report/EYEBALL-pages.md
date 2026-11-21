# Ralph eyeball loop: pages of the French report (rapport.tex)

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
