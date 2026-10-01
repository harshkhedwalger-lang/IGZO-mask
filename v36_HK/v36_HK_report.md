# v36_HK — change report (from v35_HK)

## Removed (per feedback — not the current priority)
- **`HFO2_TDDB`** (the reliability/Weibull array). Owner is focused on working-device performance, not reliability statistics right now.
- **`1T1R_WSWEEP`, `1T1R_LSWEEP`** — these swept W and L independently, which breaks the fixed W/L = 25 ratio the 1T1R device needs to source enough current for the memristor. Removed rather than fixed, since the owner wants W=500/L=20 kept constant, not swept.

## 1T1R: pitch tightened, W/L unchanged
- **W = 500 µm, L = 20 µm on every device, unchanged** (W/L = 25 kept exactly constant, as required to drive the memristor).
- **Edge-to-edge gap cut from 130 µm to 80 µm** (device pitch 1200 → 1150 µm, X-only spacing edit — CLAUDE.md rule 5 satisfied since this was explicitly requested). Device footprint is 1070 µm; 1150 − 1070 = 80 µm exactly.
- Column header labels (2X2/4X4/5X5/8X8/10X10) re-centred on the new column positions.
- **Verification:** rebuilt with the same generator validated in v35 against the real device (0.000 µm² diff at W500/L20/s2). Net topology checked against the untouched pitch-1200 reference cell — identical: 120 nets, pad distribution `{1-pad: 90, 2-pad: 30}`, confirming the tighter pitch changed nothing electrically, only spacing.

## New: HfO₂-only-dielectric staggered TFT (process split)
- **`Transistors_BottomGate_HfO2Only`** — same staggered bottom-gate topology as `Transistors_BottomGate` (L = 150/150/100/100/50/50/20/20/10/10/5/5, W = 500), placed in the area freed by removing the top-gate devices and `1T1R_WSWEEP`.
- **Important process caveat (please confirm before running):** Al₂O₃#1 is a single blanket ALD film deposited across the *entire* wafer before M2. There is no mask layer in this process that can remove Al₂O₃ under one block while leaving it under another **on the same wafer**. This new block is geometrically identical to the standard TFT — getting a genuine "HfO₂-only" comparison means running a **separate process-split wafer** with the Al₂O₃ ALD step skipped entirely, not a new mask feature. I did not add a new etch layer to attempt local removal since that's a real process change beyond a mask edit — flag if you want to pursue it.
- Net topology matches `Transistors_BottomGate` exactly (36 nets each, same generator input).

## Memristors_Gated: relocated and de-crowded
- **Moved up** into the area freed by removing `1T1R_LSWEEP`/`RESERVED_AREA`, new position (4220,1780)–(5282,5191), well clear of everything.
- **Restructured:** the gap between each of the 4 sections (LATERAL RING GATED / LATERAL OPEN GATED / VERTICAL GATED / PROCESS SPLITS) was a uniform 72 µm; widened to 250 µm. Moved as whole rigid sections (all 42 device instances + their own labels), never by height alone.
- **A first attempt broke this** by grouping shapes purely by Y-extent thinness (treating anything short as "text"); a real M1 gate-lead protrusion on one device was misclassified as a label and shifted independently of its own device, creating an M1–M2 short. Caught by the audit, not shipped — the section boundaries used in the final version come from the actual instance Y-positions (a clean, verified 72 µm gap at each of the 3 section boundaries), not from shape height.
- Internal row spacing within each section (the ~2–3 µm device-to-label pairing) was left untouched — audited safe both before and after.

## Verification (`v36_build_log.txt`)
| Check | Result |
|---|---|
| Fabricability audit | 4 findings, all pre-existing `MIS OPEN` reference plates (by design, unchanged since v35) |
| Overlay findings | 8, all pre-existing `MEM_HIGH_VALUE` resistor end windows (by design, unchanged since v35) |
| 1T1R net topology | Identical to the pitch-1200 reference: 120 nets, `{1:90, 2:30}` |
| HfO2Only net topology | Identical to `Transistors_BottomGate`: 36 nets each |
| Structure overlap | 63 µm², the same legacy stray v22 dash near CBKR (unchanged) |
| Text collisions | 0 |
| Alignment-mark clearance | 0 violations |
| DRC 2 µm | 25 width / 63 space on TOP; new/changed cells (`1T1R`, `Transistors_BottomGate_HfO2Only`, `Memristors_Gated`) all 0/0 |
| TOP-own geometry / TEXT$ instances | Identical to v35 |
| Cells geometry-changed vs v35 | `1T1R`, `Memristors_Gated`, `TOP` only |

## Still open (unchanged from v35)
1. Measured layer-to-layer overlay (mkaudit still assumes OVL 2 µm / ENC 3 µm).
2. Stray "20" + 2 dashes in `TOP` near CBKR (v22 leftovers).
3. `CBKR_Structures` ↔ `1T1R` gap is 6.5 µm (legacy).
4. `Memristors_Gated` pads are ~80 µm, not the 160 µm standard — untouched this round (de-crowding only).

## Freed / available space
- Below `Transistors_BottomGate_HfO2Only` (down to the original top-gate area's lower bound) and to the right/below the relocated `Memristors_Gated` in the old top-gate region — not filled, no filler structures added per the hard rule.
