# v46_HK — change report (from v45_HK)

## What changed
Mask-wide pad standard: **160×160µm pad / 150×150µm contact window → 150×150µm pad /
140×140µm contact window** (5µm inset kept on both). Every standard pad on the reticle,
found by direct survey, not estimated:

| | count |
|---|---|
| pad squares resized (Metal_1/2/3) | 392 |
| window squares resized (Isolation_1/Passivation) | 544 |
| other shapes adjusted to stay flush with the new pad edge (taper cones + a few plain connector strips) | 383 polygons, 1748 vertices |

Every pad's **center stayed exactly where it was** — only the edges moved in by 5µm, so no
probe coordinate or electrical node moved.

## How it was done
There's no single from-scratch generator left for this mask (built by successive diff
scripts across v34–v45, several without their own source present), so this was a direct
geometric transform on v45_HK.oas rather than a re-run of a parametric build:
1. Every 160×160 square on Metal_1/2/3 → shrunk to 150×150, same center.
2. Every 150×150 square on Isolation_1/Passivation **concentric with one of those pads** →
   shrunk to 140×140, same center. A 150×150 square with no matching pad center nearby was
   left alone.
3. Every other shape touching a pad's edge (the 75µm lead-in taper this mask's `pad_lead()`
   draws, or a plain connector box butted straight into a pad's side) gets that touching
   edge/vertex moved out to the pad's new edge, so nothing is left with a gap.

## Two things the survey caught that a blind resize would have gotten wrong
- **A real 10-item exception**: `1T1R` / `1T1R_single_v36` each have Metal_2 squares that are
  already 150×150 — those are the memristor's own bottom-electrode plate (a device-area
  dimension), not a pad. They don't match the 160×160 filter, so they were never touched.
- **A first pass broke things** it shouldn't have: `Transistors_BottomGate` and
  `Transistors_BottomGate_HfO2Only`'s pad windows sit 0.75µm off-center from their pads (an
  old quirk from however that block was originally drawn) — my first center-matching
  tolerance was tighter than that offset, so those windows got skipped while their pads
  still shrank, leaving 20 windows sitting flush with no enclosure margin (10 connectivity +
  40 overlay findings). And `STEP_COVERAGE`'s force/sense connectors tap into the *middle*
  of a pad's edge rather than its corners — pure corner-matching left a 5µm gap there,
  floating 2 M3 nets. Both caught by the full verification suite before this was called
  done, not shipped and found later.

## Verification (`v46_build_log.txt`)
| check | result |
|---|---|
| shape count per (cell, layer), old vs new | identical everywhere — nothing added or dropped, only resized |
| any 160×160 pad remaining | 0 |
| any paired 150×150 window remaining | 0 |
| connectivity / fabricability | 0 findings (matches baseline) |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 µm², same pre-existing legacy stray dash near CBKR, unchanged |
| TEXT$ collisions | 0 |
| alignment keep-out violations | 0 |
| DRC 2µm TOP | width 25 / space 61 — identical to v42–v45 baseline |

Visually spot-checked `STEP_COVERAGE` (all 8 pads still land cleanly on the serpentine, no
gaps) and `Transistors_BottomGate` (12 devices, all gate/source/drain pads intact).
