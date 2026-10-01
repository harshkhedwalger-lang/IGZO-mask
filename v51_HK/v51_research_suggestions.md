# What is still missing on the IGZO/HfO2 mask: ranked suggestions (after v51)

Stack: M1 | Al2O3 | M2 | HfO2 | Iso1 | IGZO | M3 | Passivation. Bottom gates only, 2 um rules.

Already on the die (not repeated here):
- W500 L-sweep on both gate stacks
- LOV sweep and IDT devices
- gated VdP + Greek cross, gated TLM, CTLM, CBKR
- guarded MIS/oxide tests
- 1T1R singles, SYN_1T1R, XBAR 4x4, the memristor families
- 4-probe TFT, split gate, floating-gate TFT, single 2T0C cell, verniers

Split C-V needs no new structure: W500 L150 gives about 0.2-0.3 pF, which is enough.

## Tier A: add in v52 (high impact, fits the stack as-is, few pads)
| # | Structure | Why it is publishable | Fit / cost |
|---|---|---|---|
| A1 | **Ultra-low I_off charge-retention monitor** (SEL method): a large-W DUT TFT (about 10 mm total, as W500 fingers) drains onto a floating node. The node has an M1/Al2O3/M2 capacitor of known size and a 2T0C-style sense TFT. | I_off = C·dV/dt reaches ~1e-20 A/um, 5-6 decades below the SMU floor. I_off(T) gives the activation energy. This is the defining IGZO figure of merit and is rarely measured correctly in academia. | 5 pads, ~1.0 x 0.8 mm. Iso1 via M3→M2 is already proven in 2T0C. |
| A2 | **2T0C 2x2 array**, shared WWL/WBL/RWL/RBL | Write disturb, half-select, multi-bit storage, analog MAC by read-current summation. This is the imec / Science Adv. 2025 direction; the single cell alone cannot show array effects. | 8 pads, ~1.3 x 0.9 mm |
| A3 | **Logic from the two gate stacks**: diode-load and depletion-load inverters (depletion load = the other stack's V_T, gate tied to source via Iso1), a pseudo-CMOS inverter, and an 11-stage RO with an output buffer. Beta ratio 2/4/8. | V_T engineering by the dielectric stack (Al2O3+HfO2 vs HfO2), with no extra process step. The RO gives the speed benchmark (ns/stage) that every EDL/TED paper wants. | Inverters 4 pads each; RO 4 pads (VDD, GND, OUT, VSS2) |
| A4 | **Contact-gated TFT**: M1 gates the channel, and separate M2 gates sit under the 45 um source and drain contact regions (4 um overlap, as in SPLIT). Also add an **ungated-extension sweep**: IGZO past the gate 5/10/20/45 um at W100 L10. | Changes Rc electrostatically on one device, which separates contact injection from channel transport experimentally. The sweep gives L_T and complements your LOV sweep. | 5 pads + 4 x 3 pads |
| A5 | **IGZO-overhang (fringe) sweep**: W100 L10, IGZO past W by 2/5/10/20 um | Fringe current can inflate mobility by >70% (ACS Nano 2025). It measures how much your 10 um convention overestimates mobility at W50/W100. | 4 x 3 pads |
| A6 | **Gate-heater TFT**: M1 gate strip with a pad at each end | In-situ electrothermal annealing (ms Joule pulses) to recover PBTS/NBIS; fast temperature steps for BTI; gate-R(T) thermometer for self-heating. The same heater concept can go under a memristor (retention acceleration, thermal crosstalk). | 4 pads, small |

## Tier B: high impact, but a process answer is needed first
| # | Structure | Blocking question |
|---|---|---|
| B1 | **Schottky diode + source-gated transistor (SGT)**: IGZO on an M2 bottom contact through Iso1, with the M1 gate under the source. SGT intrinsic gain ~450 vs an ohmic TFT; IGZO Schottky diodes have reached >160 GHz. | What are the M1/M2/M3 metals? This only works if M2 (or M1) is Pt/Pd/Au. |
| B2 | **1T1R 3x3 wired array** (WL = TFT gates, BL/SL shared) for analog vector-matrix multiplication | Memristor yield on the current run. The 1T1R singles are not wired as an array. |
| B3 | **FeFET / ferroelectric synapse** | Is the HfO2 doped (HZO/Si/Zr), i.e. ferroelectric? |
| B4 | **RF TFT** (GSG pads, L2, 2 um overlap, multi-finger) for f_T/f_max | GSG probe pitch |
| B5 | **Open-back-channel TFT** (passivation window over the channel): ambient/gas/humidity, and the role of passivation in PBTS/NBIS | Passivation material, and whether its etch attacks IGZO |

## Tier C: optional
- 3x3 photo-TFT array for in-sensor reservoir computing (persistent photoconductivity). A crowded field.
- Memristor pairs at a 2/5/10/20 um pitch for thermal crosstalk during forming/SET.
- Matched-pair / mismatch array (Pelgrom A_VT for an IGZO/high-k stack), which also works as a PUF. Needs a probe card or many pads.
- Corbino TFT (no W edges, exact W/L). The inner contact needs a C-shaped outer electrode.
- LIF neuron (TFT + threshold-switching memristor + M1/M2 capacitor). Only works if HfO2 shows volatile switching.
- Place the orphaned TS cell's TFT_Wsweep_L10: a free W-sweep.

## Sources
- imec capacitor-less IGZO DRAM: https://www.imec-int.com/en/articles/capacitor-less-igzo-based-dram-cell-excellent-retention-endurance-and-gate-length-scaling
- 3D stacked IGZO 2T0C array, multibit CIM (Science Adv. 2025): https://www.science.org/doi/10.1126/sciadv.adu4323
- Mobility overestimation / fringe currents (ACS Nano 2025): https://pubs.acs.org/ancac3/article-abstract/19/41/36614/3756556/
- Gated VdP for short-channel IGZO mobility (ACS AMI 2024): https://pubs.acs.org/doi/10.1021/acsami.4c14405
- IGZO SGT high gain: https://ncbi.nlm.nih.gov/pmc/articles/PMC6421470 ; https://www.pnas.org/doi/10.1073/pnas.2216672120
- 160 GHz IGZO Schottky diodes: https://pmc.ncbi.nlm.nih.gov/articles/PMC12910416/
- Electrothermal annealing of IGZO TFTs: https://ieeexplore.ieee.org/document/7959112/
- Pseudo-CMOS IGZO ring oscillators: https://khu.elsevierpure.com/en/publications/high-speed-pseudo-cmos-circuits-using-bulk-accumulation-a-igzo-tf-2/
- SEL oxide-semiconductor / NOSRAM: https://www.sel.co.jp/en/technology/os.html
- IGZO optoelectronic synapse, reservoir computing: https://advanced.onlinelibrary.wiley.com/doi/10.1002/adom.202500634
- IGZO PUF: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11095217/
