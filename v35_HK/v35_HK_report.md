# v35_HK — change report (from v34_HK)

## Process stack after this version (6 layers)
`M1 | Al2O3#1 | M2 | HfO2 | [Iso1] | IGZO | M3 | Passivation (Al2O3#2) | [Passivation open]`
Layers 1/0…6/0 only. **6/0 is renamed `Passivation`** (was `Isolation_2`). Metal_4 (7/0) is deleted.
Interpretation used: "remove L7 and the one above it" = remove L7 (Metal_4); L6 stays as the 6th, passivation layer.

## Removed
| what | detail |
|---|---|
| Top-gate TFTs | `Transistors_TopGate` (24 devices), `Dual_Gate` (12 devices) |
| Coplanar TFTs | 12 coplanar devices in `Transistors_BottomGate`. They were also non-functional: audit rule 4 showed their IGZO had no contact to the M2 S/D (HfO₂ never opened) |
| GATE OXIDE 2 tests | M3/Al₂O₃#2/M4 caps — Al₂O₃#2 is now passivation |
| L7 legend row | both `ResolutionTests` instances (L1…L6 remain) |
| Metal_4 | 122 leftover shapes cleared (incl. an M3 duplicate on the TLM contact bars — those bars keep M3 + passivation windows), layer deleted |
| Orphans | 17 cells that became unreferenced were deleted |

## Added (all on standard 160 µm pads, all DRC-clean, all net-checked)
| block | content | why |
|---|---|---|
| `1T1R_WSWEEP` | W = 100/50/20/10 µm × junction 2/4/10 µm (L = 20) — 12 devices | TFT W/L sets the compliance current; LRS vs I_comp |
| `1T1R_LSWEEP` | L = 10/5/40 µm × junction 2/10 µm (W = 100) — 6 devices | L dependence of compliance, short-channel behaviour |
| `HFO2_TDDB` | A: 20 × 10×10 µm, B: 10 × 30×30 µm; common M2 bus probed from both ends, own TE pad per cap, N/S alternating | Weibull slope + area scaling of HfO₂ breakdown; cross-point caps so the area does not depend on overlay |
| `RESERVED_AREA` | 2340 × 1709 µm at x 4220…6560, y 1780…3489, only a label | space for new structures |
Al₂O₃#1 TDDB was **not** added (GATE OXIDE 1 tests already cover it).
`t1r()` reproduces the original 1T1R device exactly (self-check: 0.000 µm² difference).

## Overlay rules (`mkaudit.py`)
Assumed OVL = 2 µm, ENC = 3 µm — **please give me your measured overlay**. Rules O1–O3 in CLAUDE.md §6.
Applied: 42 pad-window enclosures (Memristors_Gated pads were 2.5 µm, now 3), 28 IGZO-stack junction windows enlarged in M2/M3/IGZO, 8 resistor-end windows widened perpendicular to the neck.
Also corrected the audit itself: a pad on M1/M2 is valid with an Iso1 window under it (direct exposure) or an M3 cap; the old "must have M3 cap" rule falsely flagged 1000+ legacy pads.

## Verification (see `v35_build_log.txt`)
- fabricability audit: 4 findings, all the floating `MIS OPEN` reference plates (by design)
- overlay findings: 8, all `MEM_HIGH_VALUE` resistor end windows (1 µm end enclosure by design)
- net extraction: 1T1R sweeps 72 nets (12+6 devices × G/S/D-BE/TE), TDDB 32 nets — as intended
- structure overlap 63 µm² (legacy stray v22 dash in TOP over CBKR); text collisions 0; alignment clearance 0
- DRC 2 µm: 25 width / 63 space (was 29/67), no new markers; new blocks 0/0
- TOP-own geometry and all `TEXT$` instances identical to v34/v22

## Open items
1. Give the measured overlay (OVL) so ENC can be set correctly.
2. Stray "20" + 2 dashes in TOP near CBKR (v22 leftovers) — delete?
3. `Memristors_Gated` pads are ~80 µm (not 160).
4. CBKR_Structures ↔ 1T1R gap 6.5 µm (legacy).
5. Cells `MIScap_comb_N6`, `MIScap_comb_N10`, `TS` are extra top cells (not in TOP) from the source file; left untouched.
6. Free space also opened at the bottom (removed GATE OXIDE 2 row): about 3900 × 750 µm (x −1800…2100, y −6738…−5960) under the GATE OXIDE 1 row. Not marked, not used.
