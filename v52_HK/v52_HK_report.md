# v52_HK — change report (from v51_HK)

## 1. Text: all editable, three standard sizes
Every text on the die is now a KLayout **Basic.TEXT PCell**. Double-click a text in KLayout to edit it.
- 222 text cells, 608 placed instances.
- The OASIS and GDS files keep the library reference.
- All text is upper case and stays on its original layer.

| tier | mag | cap height | used for | count |
|---|---|---|---|---|
| Title | 100 | 70 um | block / section headings | 21 |
| Label | 50 | 35 um | device, row and column labels | 173 |
| Note | 30 | 21 um | subtitles, pad legends, BE/TE, TLM spacings, cross coordinates | 327 |
| exempt | 900 / 350 / 250 / 50 | — | die title Bxx_xx · IGZO_v16HK · date; ResolutionTests artwork (L1–L6 IDs, line-width numbers) | 87 |

Where the converted text came from:
- **86 lines** of polygon text in KLayout's std_font. These were decoded automatically (`textocr.py`); a line was accepted only if re-rendering the decoded string reproduces the polygons exactly.
- **66 lines** in the old `glmfont`. The strings were read from renders and are listed in the `GLM` table in `build_v52.py`.
- **156 existing TEXT PCells**, resized to their tier. **2 spliced static labels** (`TEXT_L2_W500`, `TEXT_L3_W500`) were replaced by PCells.

### Placement rule (the same rule everywhere)
- **Labels and notes** start at their old place: the centre is kept, or the shared edge of a column or stack. They are then nudged, vertically first, until they are:
  - ≥ 10 um from any structure;
  - ≥ 8 um from other text;
  - outside the alignment-cross keep-out.
- **Block titles** put the title on top with its notes below it. The lowest line sits **20 um above the content** directly underneath.
- One label needed a wider search: S200 F1, which sat between its pad and the (3000, −7000) cross.

### Titles shortened to fit their block (detail moved to a note line)

| block | v51 | v52 title / note |
|---|---|---|
| PERF_TFT | HIGH-ID TFT: IDT AND LOV SWEEP | HIGH-ID TFT / IDT AND LOV SWEEP / PADS: … |
| SYN_1T1R | GATE-SET COMPLIANCE ANALOG SYNAPSE 1T1R | SYNAPSE 1T1R / GATE-SET COMPLIANCE ANALOG SYNAPSE, W/L=25 / PADS: … |
| NOVEL_DEVICES | NOVEL DEVICES - 5UM GATE OVERLAP, … | NOVEL DEVICES / 3 note lines |
| OVL_VERNIERS | OVERLAY VERNIERS 0.25UM/STEP … | OVERLAY VERNIERS / 0.25UM/STEP … |
| Memristors_Gated | GATED MEMRISTORS - 1X/TYPE, … | GATED MEMRISTORS / 1X/TYPE, GROUPED BY GAP LENGTH |
| HfO2-only TFT block | TFT BOTTOM GATE STAGGERED - GATE = M2, … | TRANSISTOR W/ BOTTOMGATE - HFO2 ONLY / GATE = M2, … |
| MIS_CV_Block | GUARDED MIS CAPACITORS + 2 lines | GUARDED MIS CAPACITORS / AREA-PERIMETER SERIES / PADS: … |
| XBAR_4X4 | PASSIVE CROSSBAR 4X4 | CROSSBAR 4X4 / PASSIVE |
| STEP_COVERAGE | STEP COVERAGE M3 OVER M1 | STEP COVERAGE / M3 OVER M1 |
| CBKR_Structures | CBKR CONTACT RESISTANCE | same / M3 GATED |
| MEM_ASYM | ASYMMETRIC MEMRISTORS 2-10UM | ASYMMETRIC MEMRISTORS / 2-10UM |
| MEM_HIGH_VALUE | HIGH VALUE MEMRISTOR SET | HIGH VALUE MEMRISTORS |
| TestStructures | GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3) | GATE OXIDE 2 TESTS / HFO2, BE=M2 TE=M3 (now directly above its own row) |
| TestStructures | Gate Oxide 1 Tests | GATE OXIDE 1 TESTS / AL2O3, BE=M1 TE=M2 (note added for symmetry with OX2) |

### Label errors found and fixed
- **MEM_O2/3/4/6_1** (gated memristors, O variant) were labelled **G2-1 … G6-1**, identical to the G variant (XOR = 0). They are now **O2-1 … O6-1**, matching the cell names. Please confirm.
- **CBKR_M2G_2x10**: the label "CBKR M3 GATED 2X10" was drawn on top of the M1 gate plate. It is now "2X10" at the same place as its three sibling labels, and "M3 GATED" became the block note.

## 2. 1T1R last row aligned
The 6th row is flat geometry, not part of the 5-row array. Its five devices were at a 1200 um pitch instead of 1150. They were shifted by 0 / −50 / −100 / −150 / −200 um onto the array columns; the rigid shift was checked in the diff.
- Not changed: its memristors use the 2 um junction lines in every column, and the row has no label. Both are as in v51.

## 3. Alignment marks (L1–L6 ResolutionTests) in the corners
- **Top-left:** [−7270, 4802, −6075, 6580]. Its edge is flush with the corner-cross column, and it sits 60 um below the Bxx_xx die title.
- **Bottom-right:** [6075, −6580, 7270, −4802]. This is the point-symmetric position, above the (7000, −7000) cross.
- The diagonal pair keeps the long baseline for rotation alignment. The 16 M1 coordinate crosses are unchanged.

## 4. Knock-on moves
- **STEP_COVERAGE** moved 40 um down. Its 70 um title would otherwise sit 18 um from the 1T1R pads.
- **PERF_TFT, SYN_1T1R and NOVEL_DEVICES** were re-packed because their device cells grew with the larger labels.
  - PERF_TFT: [−6600, 1474, −5655, 4562]
  - SYN_1T1R: [−5535, 1444, −4033, 4562]
  - NOVEL_DEVICES: [4180, 2049, 5867, 6296]

## Verification

| check | v52 | v51 |
|---|---|---|
| polygon text left (std_font) | 0 | — |
| non-PCell text instances | 0 | 2 + polygon text |
| text clearance (≥10 um to structure, ≥8 um text-text, keep-out) | 0 violations | not checked inside blocks; the 2x10 CBKR label sat on the gate plate |
| connectivity | 0 | 0 |
| overlay | 8 (pre-existing MEM_HIGH_VALUE windows) | 8 |
| Iso1 exposing M1 under IGZO | 0 | 0 |
| structure overlap | 63 um² (pre-existing CBKR) | 63 |
| block pairs < 60 um | none | none |
| alignment-cross keep-out | 0 | 0 |
| DRC 2 um, TOP | width 25 / **space 26** | 25 / 61 (35 space hits were inside old glmfont glyphs) |
| device pairs < 20 um (PERF / SYN / NOVEL) | 0 | 0 |
| non-text geometry changed beyond the edits above | none | — |

## Files
- `v52_HK.oas` / `.gds`
- `build_v52.py`, which uses `textocr.py`, `text_place_v52.py`, `text_fixups_v52.py` and `verify_v52.py`
- `v52_build_log.txt`
- renders `v52_*.png`

Open, unchanged: the stray "20" + dash polygons in TOP near CBKR (TOP-own geometry, not text-PCell), and the guard ring / SYN driver questions from v51.
