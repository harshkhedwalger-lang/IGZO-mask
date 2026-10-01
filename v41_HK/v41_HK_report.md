# v41_HK — change report (from v40_HK)

## What changed
The HfO2-only-dielectric TFT process split (`Transistors_BottomGate_HfO2Only`) had its **gate moved from
Metal_1 to Metal_2**, per your correction. This is a real fix, not cosmetic — it changes what the block
actually demonstrates:

- **v36 version (gate = M1):** geometrically identical to the standard TFT. Flagged at the time as
  unbuildable on the same wafer as every other structure, because Al2O3#1 sits directly under M1's gate
  stack as a blanket ALD film — there's no way to remove it under one M1-gated device while keeping it
  under another, on one wafer.
- **v41 version (gate = M2):** M2's own gate dielectric, going up toward the channel, is **HfO2 only** —
  Al2O3#1 sits *below* M2 (between M1 and M2), not between M2 and the channel. This is a real,
  single-edge HfO2-only-dielectric TFT, buildable on the exact same wafer and same process as everything
  else on this reticle, using layers that already exist. No process change needed.

Implementation: the 32 non-text Metal_1 shapes (gate pad + lead + plate, all 12 devices — L = 150/150/
100/100/50/50/20/20/10/10/5/5, W = 500) were moved to layer 3/0 (Metal_2), position and shape byte-for-
byte unchanged. IGZO, Metal_3 (S/D), the Isolation_1 window and the Passivation window were not touched —
the standard M1/M2 pad recipe (Isolation_1 window + Metal_3 cap + Passivation window) already treats
both layers identically, so the *same* window that used to open both Al2O3 and HfO2 over an M1 pad now
opens only HfO2 over the M2 pad — exactly the physics this block exists to test, with zero new geometry.

Heading corrected to: **"TFT BOTTOM GATE STAGGERED — GATE = M2, HFO2 ONLY (AL2O3 BELOW M2, SAME WAFER)"**
(old wording implied a same-wafer M1 trick that was never actually achievable).

## Bugs hit and fixed before shipping
1. **First heading-removal pass only caught the widest text cluster**, not the whole line — the old
   wording had three word-groups (word spacing exceeded the 20 µm merge-dilation used to find them), so
   two of the three survived and left a stale, now-wrong "(PROCESS SPLIT, NO AL2O3)" fragment rendered
   under the new heading.
2. **A ±3 µm height-tolerance re-check still missed two punctuation glyphs** ("-" and ","), which sit at
   a slightly different baseline than letters. Fixed by selecting on position relative to the real device
   body (anything above it is heading, full stop) instead of a height tolerance.
3. **The body-top calculation for placing the new heading initially included Metal_1 itself** (all real
   gate shapes had just been retyped away, so Metal_1's own shapes were now purely the heading being
   measured against) — nothing got erased on that pass. Fixed by excluding Metal_1 from the "real device
   geometry" scan.
4. **The corrected placement still overlapped the per-device "L150_W500" column labels**, because those
   are child `TEXT$` cell instances, not own shapes, and the scan only looked at own shapes. Fixed by
   using the cell's own recursive `bbox()` (which sees everything) after the heading was erased.
5. **The net-topology check itself under- and over-counted** before being trusted: `mkaudit.Audit.R()`
   merges glyph polygons *before* the glyph filter can run, so touching heading characters occasionally
   fuse into a word-sized blob that survives the small-glyph filter and gets counted as a real, pad-less
   "net" (46 found vs the expected 36). Not a device defect — fixed by classifying each polygon before
   any merge, using the cell's raw (unmerged) recursive shapes.

## Verification (`v41_build_log.txt`)
| check | result |
|---|---|
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| **gate geometry congruence** (old M1 position vs new M2 position) | **0.0000 µm² diff** — exact match |
| net topology vs reference `Transistors_BottomGate` | 36 nets both, pad distribution match |
| stray Metal_2 elsewhere in the file | 0 cells |
| structure overlap | 63 µm², same pre-existing legacy stray dash near CBKR |
| heading label collisions | 0 |
| text collisions | 0 |
| DRC 2 µm | `Transistors_BottomGate_HfO2Only`: 0 width / 0 space |
| cells changed other than the target | none |

## Still to do (from your message)
- Move `STEP_COVERAGE`, `XBAR_4X4`, `SPLIT_CV`, `PERF_TFT` down to join `TestStructures`.
- Move the original `1T1R` block (25 devices) up into the freed space.

These are top-level instance moves (not internal flat-geometry surgery like the `TestStructures`
reorganisation), so lower risk — but `1T1R` alone is 5920×5602 µm, larger than all four blocks-to-move
combined, so I'll compute a real floor plan rather than guess at a swap. Building that next as v42.
