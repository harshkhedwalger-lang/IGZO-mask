# v51_HK — change report (from v50_HK)

## 1. High-Id block (PERF_TFT)
- L ladder removed (PT_L2/L3/L5/L20/L50/L100 cells deleted). It duplicated the W500 L-sweep.
- Kept: REF W100 L10, IDT W1000 L10, IDT W1000 L5, IDT W2000 L10, and the LOV sweep 2/10/20/40.
- Retitled "HIGH-ID TFT: IDT AND LOV SWEEP" and re-packed column-first (2 columns of 4). It is now 921 um wide instead of 1840.
- SYN_1T1R follows 120 um to its right.

## 2. W500 main TFT blocks: new third row, L3 L3 L2 L2
Added to both **Transistors_BottomGate** (M1 gate) and **Transistors_BottomGate_HfO2Only** (M2 gate).
- Each new device is a copy of that block's own L5_W500 device.
- The copy is split along the gate centre. The source half moves +d and the drain half moves −d, with d = (5 − L)/2.
- The gate pad and taper are unchanged, so the only difference from L5 is the channel.
- Labels L3_W500 and L2_W500 use glyphs from the mask's existing label font.

Measured from the drawn geometry, all 8 new devices:

| | L | gate width | overlap S/D | IGZO past gate | W |
|---|---|---|---|---|---|
| L3_W500 (×2 per block) | 3.0 | 13.0 | 5.0 / 5.0 | 45.0 | 500 |
| L2_W500 (×2 per block) | 2.0 | 12.0 | 5.0 / 5.0 | 45.0 | 500 |

The W500 L-sweep is now 150/100/50/20/10/5/3/2, with 2 devices per L, on both gate stacks. This is the set to use for TLM-style Rc/ΔL extraction.

## 3. NOVEL_DEVICES (new block, 11 devices, 5 um overlap / 45 um IGZO convention)
| cell | what it is | what it gives you |
|---|---|---|
| NV_4PR_M1, NV_4PR_M2 | Gated four-probe TFT, W100 L60. Two IGZO probe tabs at L/3 and 2L/3 sit on the gate. The M3 probe tips stay on IGZO, never on bare dielectric. | Intrinsic channel mobility and V_T from ΔV between the probes, free of Rc. Also gives Rc directly from one device, as a cross-check of the TLM. |
| NV_SPLIT_M1S, NV_SPLIT_M2S | Split dual-EOT gate, W100 L20. Half the channel is gated by M1 (Al2O3+HfO2), half by M2 (HfO2 only). The two gates overlap by 4 um, so there is no ungated gap. Source side and drain side are swapped between the two cells. | Stack-dependent V_T and mobility inside one channel. Asymmetric-gate/pinch-off behaviour. Bias with both gates tied or independently. |
| NV_FG_R0 / R2 / R5 | Floating-gate synaptic TFT, W100 L10. M1 control gate / Al2O3 / isolated M2 floating gate / HfO2 / IGZO. The CG lies entirely inside the FG. The FG wing sets the coupling area ratio A(CG)/A(channel) = 0.67 / 2.37 / 5.17. | Charge-trap/FG analog memory (potentiation/depression by CG pulses). The R-series isolates the coupling-ratio effect. |
| NV_FG_R2_PAD | Same as FG_R2, but the FG has its own pad. | Calibration: measure the FG-gated TFT directly and extract the coupling ratio. |
| NV_2T0C_L10, NV_2T0C_L50 | 2T0C gain cell. The write TFT (W50 L10, M1 gate) drains onto an M3 storage node. An Iso1 landing drops it to M2, which is the gate of the read TFT (W100, L10 or L50, HfO2 only). No capacitor. | IGZO DRAM/retention: write, then read the stored charge non-destructively over time. The ultra-low IGZO I_off sets the retention. |
| NV_2T0C_CAL | 2T0C L10 with a probe pad on the storage node. | Calibrates the read-TFT transfer curve I_read(V_SN) and lets you check the SN leakage directly. |

## 4. OVL_VERNIERS (new)
- Six layer pairs: M1/M2, M1/IGZO, M1/M3, M2/IGZO, M2/M3, IGZO/M3.
- Each pair has an X and a Y vernier: 25 bars, pitch 10 vs 10.25 um, which reads 0.25 um per step over ±3 um.
- The first layer is on the top (X) or right (Y); the centre bar is longer.
- Excluded from the device rules, like ResolutionTests.

## Placement
| block | TOP bbox (um) |
|---|---|
| PERF_TFT | [-6600, 1474, -5679, 4545] |
| SYN_1T1R | [-5559, 1444, -4099, 4545] |
| Transistors_BottomGate | [-5260, 3720, -1225, 6505] (third row below the existing rows) |
| Transistors_BottomGate_HfO2Only | [-1150, 3720, 2885, 6461] |
| NOVEL_DEVICES | [4180, 2049, 5810, 6250] (≥170 um below the logo) |
| OVL_VERNIERS | [-1140, 2971, 207, 3760] |

## Verification (all against the v50 baseline)
- connectivity: 0
- overlay: 8, the same pre-existing MEM_HIGH_VALUE windows
- Iso1 windows exposing M1 under IGZO: 0
- structure overlap: 63 um², the pre-existing CBKR one
- gaps < 60 um: none
- TEXT collisions: 0
- keep-out: 0
- DRC TOP: 25/61 (baseline)
- DRC for every new or changed cell: 0/0
- device pairs < 20 um inside PERF/SYN/NOVEL: 0
- cells changed outside the intended set: none
- the original 12 devices of both W500 blocks are unchanged

## Open questions (need your input)
- **HfO2 / Al2O3 thicknesses.** These set the FG coupling ratio in capacitance, not only in area, and the program voltages. If Al2O3 is much thicker than HfO2, R5 may be needed just to reach coupling ~0.5.
- **Guard ring on MEM_HIGH_VALUE** is still closed across TE (pre-existing). Please confirm the intent.
- **SYN_1T1R drivers** still use the old fully-gated 10 um fingers.
