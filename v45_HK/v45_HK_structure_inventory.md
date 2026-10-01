# v45_HK — full structure inventory

Every device block on the reticle, top-level first, then what's inside `TestStructures`.
Counts are actual instance/array counts read from the mask, not estimates.

## Top-level blocks

| Block | What it is | Devices |
|---|---|---|
| `1T1R` | 1-transistor-1-resistor RRAM array | 25 devices (5×5 `1T1R_single_v36`) |
| `SYN_1T1R` | Synaptic 1T1R, W/L/junction-count sweep | 8 types (W50/125/250/500 × L2/5/10/20 × J2/J4) |
| `Memristors` | Main individual-memristor array | 11 devices |
| `Memristors_Gated` | Gated memristors — 3 process variants × gap length, regrouped by length in v43 (2×2 grid: L2/L3 top, L4/L6 bottom) | 42 devices |
| `MEM_REDUNDANT` | Memristor redundancy test block | flat array |
| `MEM_HIGH_VALUE` | High-value memristor block | flat array |
| `MEM_ASYM` | Asymmetric-electrode memristor block | flat array |
| `MEM_STACK_SPLIT` | Memristor stack-split process-window test | flat array |
| `Transistors_BottomGate` | Bottom-gate IGZO TFTs, standard stack (gate = M1, Al2O3 dielectric) | array |
| `Transistors_BottomGate_HfO2Only` | Bottom-gate TFT, HfO2-only gate dielectric — gate corrected to Metal_2 in v41 so it's actually fabricable on this stack | array |
| `PERF_TFT` | TFT perimeter/channel-length sweep + interdigitated devices | 14 types (PT_L2…L100, PT_LOV2…40, PT_IDT ×3, PT_REF) |
| `STEP_COVERAGE` | Step-coverage-over-topography test | flat array |
| `XBAR_4X4` | 4×4 crossbar array | flat array |
| `CBKR_Structures` | Cross-bridge Kelvin resistance, M2-gate contact | 4 types (2×10 / 4×10 / 4×20 / 8×10) |
| `TestStructures` | Consolidated process-control block — see below | see below |
| `ResolutionTests` | Lithography resolution targets | 2 placements |
| *(standalone, no block)* | A second gated van der Pauw / Greek-cross structure, drawn directly in `TOP`'s own layers near (1705,-5273)–(2875,-4433) — real placed geometry, not inside any instance. Currently unlabelled. | 1 |

## Inside `TestStructures` (reorganized in v45, top to bottom)

| Row | Structure | What it tests |
|---|---|---|
| 1 | `TLM_BACK_BIAS` | Transfer-length method, two back-bias conditions, contact spacings 30–270um |
| 1 | Gated van der Pauw / Greek-cross (now titled `GATED VDP + GREEK CROSS`) | Sheet resistance / Hall-type measurement under a gate bias |
| 2 | `GATE OXIDE 1 TESTS` | Al2O3 gate-dielectric integrity — 6 devices, 4-terminal (BE/TE force+sense) guard-cross, built-in area sweep. BE = Metal_1, TE = Metal_2. |
| 3 | `GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)` — new in v45 | Same measurement, HfO2 dielectric. Built by copying OXIDE 1's geometry and shifting the electrode stack up one metal level (BE→M2, TE→M3); Isolation_1 windows kept only where they still make physical sense (M2 pads keep them, M3 pads don't). |
| — | `MIS_CV_Block` ("GUARDED MIS CAPACITORS — AREA-PERIMETER SERIES") — restored in v45 | Combined Al2O3+HfO2 MIS stack (M2 absent, so the contact etch goes through both dielectrics), area-perimeter series, several guard/finger configurations plus open/short de-embed structures |

Also inside `TestStructures` (not touched in this pass, from the original library): CTLM,
gated_TLM, linear_TLM, CBKR, Kelvin_via, via_chain_M2_M3, serpentine_M2, comb_leakage_M2,
vdP_GreekCross_M2/M3, gated_vanderPauw, TFT_Lsweep_W50, TFT_Wsweep_L10, gated_4probe_TFT,
crossbar_4x4, vernier_CD, MIS_caps_M1_IGZO, MIM_caps_M2_M3 — these are library cell
definitions referenced from `TS` (see note below), not separately placed on the die.

## Removed in v44 (superseded by GATE OXIDE 1/2 TESTS, not restored)

`AL2O3_INTEGRITY` (simple 2-terminal Al2O3 MIM sweep) and `HFO2_MIM` (simple 2-terminal
HfO2 MIM sweep) and `SPLIT_CV` (W=L=400um split MIS capacitor with IGZO) — all simpler
variants of a measurement the guarded 4-terminal GATE OXIDE 1/2 rows already do better.
`MIS_CV_Block` was in that same removal but has been **restored** per this update.

## Known open item (flagged earlier this session, unchanged)

The `TS` cell — 18 PCM (process-control-monitor) structures including a second copy of the
gated van der Pauw / Greek-cross and vdP_GreekCross_M2/M3 — exists in the library but is
**not instantiated anywhere on the die** (orphaned). Not touched in this pass since it wasn't
part of the request; flagging again since it's been sitting unplaced since v37.
