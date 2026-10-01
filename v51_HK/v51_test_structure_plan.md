# Test-structure gap analysis (v51 die) and plan for v52

## What the die has today (checked in v51_HK.oas)

| Area | On the die |
|---|---|
| Contacts | TLM_BACK_BIAS (linear, gated); CBKR_Structures (4 Kelvin M3/IGZO contacts, M1 gate) |
| Semiconductor | gated VdP + Greek cross (two copies) |
| Dielectrics | GATE OXIDE 1 (Al2O3, M1/M2); GATE OXIDE 2 (HfO2, M2/M3); MIS_CV_Block (M1/Al2O3+HfO2/IGZO, area-perimeter, open/short) |
| Topography | STEP_COVERAGE: M3 over M1 lines only |
| Litho | ResolutionTests, OVL_VERNIERS |

Missing entirely:
- metal sheet resistance and electrical linewidth
- short/open yield at 2 um
- Iso1 contact-window chains or Kelvin vias (M3→M1 and M3→M2)
- crossover isolation
- IGZO island-to-island isolation
- a MIM of the real M1-gated TFT stack (Al2O3+HfO2)
- open / no-channel dummies
- temperature sensing

The orphaned `TS` library cell is old-style: M2 bottom contacts under IGZO, 120–200 um pads, pre-convention TFTs. It is better replaced than placed.

## P1: must-have (without these, device data can't be quantified or yield-screened)

| # | Structure | Geometry (150/140 pads, 2 um rules) | What it gives |
|---|---|---|---|
| 1 | **GATE OXIDE 3: bilayer MIM**, BE = M1, TE = M3 through Al2O3+HfO2 | Copy of the OX1/OX2 row (same area sweep, same guard) | C_ox, leakage and breakdown of the M1-gated TFT's actual gate stack. OX1/OX2 give each layer alone, and MIS includes IGZO. Needed for mobility of every M1-gated TFT. |
| 2 | **OPEN / NO-IGZO / SHORT dummies**, both stacks | W500 L10 pad frame: (a) pads + leads only; (b) full TFT without IGZO; (c) S-D shorted | Measurement floor (I and C) for I_off/C-V, overlap capacitance C_ov = eps·2·5·500 um², gate leakage through the overlaps only. De-embedding for split C-V on the L150 devices. |
| 3 | **Iso1 contact chains + Kelvin vias**, M3→M1 (both dielectrics) and M3→M2 (HfO2 only) | 100-link chains at windows 3/5/10 um, plus a 4-terminal Kelvin at 2/5 um for each metal | Every M1/M2 pad and all planned circuits depend on these vias. Gives the minimum window that opens, R_via, and incomplete Al2O3 etch (the hard one). |
| 4 | **Comb–serpentine–comb yield** | M3 at 2 and 3 um space (= your L2/L3 channel gaps); M1 and M2 at 2 um. About 20 mm of line each, 3 pads | Short/open yield at the minimum rule. M3 bridging at 2–3 um is exactly what kills L2/L3 TFTs. |
| 5 | **Cross-bridge (sheet R + electrical linewidth)** for M1 and M3, plus a **gated IGZO bridge** (widths 10/20/50 on an M1 plate) | NIST Greek cross + bridge with 2/3/5/10 um segments sharing taps | Actual gate length (M1 CD), actual channel gap (M3 pitch minus linewidth), IGZO wet-etch undercut ΔW. Separates litho/etch bias from Rc in the L-sweep ΔL. |
| 6 | **IGZO island isolation** | Pairs of M3-contacted IGZO islands on one shared M1 gate, spacing 2/5/10/20 um, 500 um facing edge | Device-to-device leakage through IGZO residue or the dielectric surface, with the gate in accumulation. Must be far below I_off before arrays (2T0C, 1T1R) or I_off monitors mean anything. |

## P2: strong upgrades

| # | Structure | Gives |
|---|---|---|
| 7 | **Gated CTLM**: M3 disc (= pad) inside an M3 ring, gaps 5/10/20/40, on a full M1 plate | Rc/rho_c with no lateral current spreading (linear TLM bars suffer the fringe error). Third independent Rc method next to TLM and 4PR. |
| 8 | **Crossover / edge-intensive capacitors**: M2×M1, M3×M2, M3×M1 line grids with 100 and 1000 crossings, equal area vs a plate | Leakage and breakdown at metal edges vs area, i.e. crossover yield for routed circuits. Also covers the split-gate and FG edge regions. |
| 9 | **Vertical M2/IGZO/M3 diode**: IGZO on M2 through Iso1, windows 5/10/20/50 um | Tells you electrically whether M2/IGZO is ohmic or Schottky (the bottom-contact / Schottky-diode question). Also the IGZO series resistance in memristor stacks. Skip if MEM_STACK_SPLIT already has it. |
| 10 | **4-wire M1 RTD + M1 heater**, and an M3 RTD | Real device temperature during bias-temperature stress, chuck calibration, self-heating. |
| 11 | **STEP_COVERAGE extension**: IGZO over M1 and M2 edges (gated serpentine), M3 over the IGZO+M1 double step | Every TFT has IGZO crossing the gate edge and M3 climbing the IGZO edge. Today only M3-over-M1 is tested. |

## P3: optional

| # | Structure |
|---|---|
| 12 | Weibull breakdown arrays (16 caps per stack, common BE) |
| 13 | Electrical overlay TFT pairs, drawn overlap 3/7 · 5/5 · 7/3 |
| 14 | Remove the orphan TS library cell (needs your OK) |

Rough size: P1 is about 80 pads, 4–5 mm². With pad sharing (common grounds on chains, combs and the island gate) it is about 60 pads.
