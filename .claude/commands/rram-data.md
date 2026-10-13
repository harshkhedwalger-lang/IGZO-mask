---
description: Load the RRAM / 1T1R I-V raw data, scripts and plotting conventions, then do the task given
argument-hint: <what to plot or analyse>
---
You are working with the owner's RRAM and 1T1R I-V measurement data in this repository.

1. Make sure the data is present. If `rram_1R_IV/` does not exist, run
   `git fetch origin claude/ecstatic-fermat-lqf97q && git checkout claude/ecstatic-fermat-lqf97q`.
2. Read `rram_1R_IV/CLAUDE.md` (dataset map, raw file format, agreed conventions) and `rram_1R_IV/README.md`
   (per-dataset results) before touching anything.
3. Install what the scripts need if missing: `pip install numpy pandas matplotlib`.
4. Reuse the existing scripts (`plot_1T1R_2x2.py`, `plot_device.py <device>`, `publication_plots.py`, ...) and
   their style instead of writing new plotting code from scratch. Put new outputs in the matching `out_*` folder.
5. Keep the conventions: read rules at |V| = 0.05 / 0.1 V, report the median, rule-based cycle exclusions stated
   in the caption, and the journal plot style with no annotations. Ask the owner before guessing anything process-related.
6. Look at every figure you produce before reporting, and give the owner the files plus the data as .txt.

Task: $ARGUMENTS
