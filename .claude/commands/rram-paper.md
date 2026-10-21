---
description: Write or edit the journal paper using the analysed RRAM / 1T1R results, figures and data
argument-hint: <which section or task, e.g. "draft the Results section for the 1T1R device">
---
You are helping the owner write a journal paper on HfO₂ RRAM and IGZO-TFT 1T1R devices.

1. If `rram_1R_IV/` is missing, run
   `git fetch origin claude/ecstatic-fermat-lqf97q && git checkout claude/ecstatic-fermat-lqf97q`.
2. Read `rram_1R_IV/PAPER_CONTEXT.md` completely. It is the single source of truth: methods, results with exact
   medians and P10–P90, figure files with draft captions, draft text, limitations and open questions.
   Use `rram_1R_IV/README.md` and the files under `rram_1R_IV/out_*` for any detail it points to.
3. Follow its rules:
   - use only numbers that exist in those files;
   - report medians with the read voltage and polarity;
   - state the excluded cycles;
   - never call selected cycles consecutive;
   - note that 1T1R resistances include the TFT channel;
   - never fill a `[CONFIRM]` item yourself. List the ones the task needs and ask the owner.
4. Use the journal figures (`rram_1R_IV/out_1T1R_2x2/journal_*.pdf`). If a new figure or number is needed, generate
   it with the existing scripts (`/rram-data` conventions), and add it to `PAPER_CONTEXT.md` with its source file.
5. Put manuscript text in `paper/` (create it if needed). When finished, list the claims you made and the file that
   backs each number.

Task: $ARGUMENTS
