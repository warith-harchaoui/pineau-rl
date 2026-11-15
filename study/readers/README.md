# Who read the papers, with which instructions

*Version française : [LISEZMOI.md](LISEZMOI.md)*

The papers of the survey were read by language-model agents (Claude Code subagents), one reading folder
per agent (`study/codes/<reader>/`, `study/codes_v2/<reader>/`). This folder gives their provenance,
rebuilt on 15 November 2026 from the transcripts of the Claude Code sessions, which stay on the author's
machine and are not published.

- `readers.csv`: one line per agent (38 readers, 3 audit or harmonisation agents, 4 subtasks launched by
  the harmonisation agent). Columns: grid, role, session, start and end (UTC), exact model read from the
  transcript, papers written, tools called, how the PDFs were read, evidence (line numbers and timestamps
  in the transcripts).
- `prompts/<reader>.md`: the exact instructions given to each agent, word for word, followed by every
  message later sent to the same agent (resume after a usage limit, supplement pass). Only path prefixes
  are shortened: `~/` for the home folder, `<scratchpad>/` for the temporary folder, `<transcripts of …>/`
  for the transcripts.
- `folder_check.csv`: for each of the 38 reading folders, the agent that wrote it, and the match between
  the folder's files and the papers given to that agent. No mismatch.

What the reconstruction establishes, and its limits (deviation 28 of `../PROTOCOL-en.md`):

- Every reader ran on the model `claude-opus-5-5`, except two that finished on `claude-opus-5` after a
  safety filter stopped one of their responses: C2 (papers ML14 to ML17) and M4 (nine papers of A4). All
  the instructions were written by the coordinating agent, none by hand.
- Every reader converted the PDFs to text with `pdftotext`, and many also looked at page images
  (`pdftoppm`).
- The second readers (G, G2, R2, R3) opened no file of another reader: their tool calls show it. One
  primary reader, M7, opened K1's file for K002 as a format example; K002 is neither its paper nor part of
  a double reading.
- The double readings are made by copies of the same model: their agreement measures how stable this
  model's reading is, not the agreement between two independent readers.
