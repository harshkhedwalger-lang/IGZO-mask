# Handoff: local session → cloud session (2026-10-01)

Read `CLAUDE.md` first, then this file, then `v52_HK/v52_HK_report.md`.

## Current state
**v52_HK** is the current, fully verified mask.
- Build: `cd v52_HK && python -u build_v52.py > v52_build_log.txt`. It reads `../v51_HK/v51_HK.oas`.
- Setup: `pip install klayout matplotlib`. Import `klayout.lib` before reading any .oas, so the Basic.TEXT PCells resolve.
- Rendering: there is no KLayout GUI in the cloud. Use `render_preview.py <oas> <out_prefix> <CELL>[:x0,y0,x1,y1] ...` and send the PNGs to the owner.

| check | v52 result |
|---|---|
| polygon text left | 0 |
| non-PCell text | 0 |
| text clearance violations | 0 |
| connectivity | 0 |
| overlay | 8 (pre-existing MEM_HIGH_VALUE windows) |
| Iso1 exposing M1 under IGZO | 0 |
| structure overlap | 63 um² (pre-existing CBKR) |
| block gaps < 60 um | none |
| alignment-cross keep-out | 0 |
| DRC TOP | width 25 / space 26 |
| unintended geometry changes | none |

## History in brief

| version | change |
|---|---|
| v44–v45 | oxide tests reorganised (OX1 Al2O3 M1/M2, OX2 HfO2 M2/M3), guarded MIS_CV block restored |
| v46 | mask-wide pad standard 160/150 → **150/140** |
| v47–v48 | gated memristors compact (100/90 pads, 1 per type), MEM_HIGH_VALUE rebuilt, TestStructures column: TLM → VdP+Greek → OX1 → OX2 |
| v49 | PERF_TFT + SYN_1T1R packed column-first, STEP_COVERAGE moved near TestStructures |
| v50 | high-Id TFTs redrawn to the owner's TFT convention (5 um overlap/side, IGZO 45 um past the gate); IDT outer fingers 5 um |
| v51 | high-Id L ladder removed; L3/L3/L2/L2 W500 third row added to both W500 blocks (M1 and M2 gate); NOVEL_DEVICES added (4-probe TFT, split dual-EOT gate, floating-gate synaptic TFT R0/R2/R5/R2_PAD, 2T0C L10/L50/CAL); OVL_VERNIERS (6 layer pairs, 0.25 um/step) |
| v52 | all text → Basic.TEXT PCells, 3 sizes (70/35/21 um), upper case; 1T1R flat 6th row aligned; ResolutionTests (L1–L6) moved to opposite die corners; STEP_COVERAGE 40 um down |

## Open questions for the owner (ask, don't guess)
1. **MEM_O*_1 labels:** they were drawn "G2-1…G6-1", identical to the G variant. v52 relabelled them "O2-1…O6-1" to match the cell names. Confirm.
2. **Stray "20" + dash polygons** in TOP near CBKR (TOP-own M1, not a text cell): delete or keep?
3. **Process:** HfO2 and Al2O3 thicknesses; M1/M2/M3 metals (decides Schottky / source-gated TFT ideas); whether the HfO2 is ferroelectric (HZO); passivation material and whether its etch attacks IGZO; GSG probe pitch / probe card.
4. **MEM_HIGH_VALUE guard ring:** it is closed across TE and its bars cross BE. Intended?
5. **SYN_1T1R drivers:** they still use the old fully-gated 10 um fingers. Convert them to the 5 um overlap convention?
6. **Gated memristors:** restore 3 repeats per type?
7. **1T1R 6th row:** all columns use 2 um junction lines and the row has no label. Intended?

## Proposals waiting for the owner's choice of scope (nothing built yet)
- **Devices:** `v51_HK/v51_research_suggestions.md`.
  - Tier A: I_off charge-retention monitor; 2T0C 2x2 array; dual-stack logic (inverters + 11-stage ring oscillator); contact-gated TFT + ungated-extension sweep; IGZO overhang (fringe) sweep; gate-heater TFT.
  - Tier B depends on the process answers above.
- **Test structures:** `v51_HK/v51_test_structure_plan.md`.
  - P1: GATE OXIDE 3 bilayer MIM (M1/Al2O3+HfO2/M3); OPEN / NO-IGZO / SHORT dummies; Iso1 via chains + Kelvin (M3→M1, M3→M2); comb–serpentine–comb (M3 at 2/3 um, M1/M2 at 2 um); cross-bridge CD for M1/M3 + gated IGZO bridge; IGZO island isolation.
  - P2/P3 listed in the file.
  - Pad question: may pure-metal monitors use 100/90 pads?
  - Orphan `TS` library cell: delete?

## Conventions (summary; details in CLAUDE.md)
- klayout.db only; write .oas + .gds; generator next to the output; never touch alignment marks, headings or TOP geometry unless asked.
- Pads 150/140, 75 um taper (memristor blocks 100/90). 2 um minimum width and space.
- TFT: gate = L + 2x5 um, IGZO 45 um past each gate edge, IGZO 10 um wider than W per side, gate exits along W.
- Text: Basic.TEXT PCells, title mag 100 / label 50 / note 30; ≥10 um to structures, ≥8 um between texts.
- The owner prefers short, direct answers with numbers, column-first packing, and to be asked before process assumptions.
- Git commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
