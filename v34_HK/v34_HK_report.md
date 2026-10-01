# v34_HK — change report (from v33_HK (2).oas)

## Fixed
| # | problem | fix |
|---|---|---|
| 1 | Alignment-mark text and headings had been moved (+450 µm) in v33 | TOP-own geometry and all 36 `TEXT$` instances restored to v22: **0 µm² / 0 instances differ** |
| 2 | Memristors 2X2…10X10 heading row sat mid-array on top of devices | Headings moved back to v22 height (top of the array); block shifted 60 µm left so the 10X10 column is 62 µm from the MEM_ASYM column (was 2 µm) |
| 3 | v33 shredded labels in MEM_ASYM / MEM_STACK_SPLIT / MEM_REDUNDANT | Labels restored from v32 (non-text M1 verified identical), 2 labels nudged off pads |
| 4 | MEM_HIGH_VALUE labels on pads | Device labels parked beside the N pad, headings raised 50 µm |
| 5 | SPLIT_CV label on the S/D pads; "W=L=" printed as "W L" (font has no "=") | Label raised 70 µm, both "=" drawn |
| 6 | **STEP_COVERAGE: all five rows shorted at the right end (not a serpentine, 4 pads on one net)** | Rebuilt as true serpentine, F+/S+ at start, S-/F- at end; 2 nets, 4 pads each |
| 7 | Memristors_Gated title touched "BOTTOM GATE" and its own sub-headings | Title/headings spaced, instance 40 µm lower |
| 8 | STEP/XBAR bbox overlap, legend on bottom-right alignment label | STEP stacked 100 µm above XBAR; ResolutionTests legend 380 µm left |

## Verification
- fabricability audit: **0** findings (v33 script's rules, extended to STEP)
- structure-to-structure overlap: 0 µm² (only 63 µm² legacy v22 stray M1 dash in TOP overlapping CBKR, see open items)
- TEXT-to-structure / TEXT-to-TEXT collisions: 0; in-block label collisions: 0
- DRC 2 µm: 29 width / 67 space (glyph corners + litho rungs, same class as v33)
- cell diff v33→v34: only SPLIT_CV, STEP_COVERAGE, MEM_STACK_SPLIT, MEM_ASYM, MEM_HIGH_VALUE, MEM_REDUNDANT, Memristors_Gated, Memristors, TOP

## Open items (not changed, need a decision)
1. Stray "20" glyph + two dashes in TOP (v22 leftovers of the removed ungated CBKR variants) beside "CBKR CONTACT RESISTANCE"; one dash overlaps CBKR by 63 µm². Delete?
2. `Memristors_Gated` pads are ~80 µm, not the 160 µm standard.
3. CBKR_Structures / 1T1R gap 6.5 µm; TestStructures (550 µm²) and left ResolutionTests (202 µm²) are within 40 µm of an alignment cross — all v22 positions.
