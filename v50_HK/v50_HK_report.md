# v50_HK — change report (from v49_HK)

High-Id TFT block redrawn to the same source/drain overlap convention as the main TFTs
(`Transistors_BottomGate`, identical in all 12 devices): gate = L + 2 x 5 um, IGZO 45 um past
each gate edge under the electrode, electrode past the IGZO, W = electrode width (IGZO 10 um
wider per side), gate exits along W and never runs under an electrode.

| devices | before | now (measured from the drawn geometry) |
|---|---|---|
| REF W100 L10 | 10 um overlap per side, contacts fully gated | **5 / 5 um**, 45 um ungated IGZO contact |
| L ladder L2/3/5/20/50/100 (W100) | same as REF before | **5 / 5 um**, 45 um |
| LOV sweep (W100 L10) | finger width 2/5/20/40, fully gated | **gated overlap 2 / 5(=REF) / 10 / 20 / 40 um**, 45 um ungated fixed; PT_LOV5 -> PT_LOV10 |
| IDT W1000 L10, W1000 L5, W2000 L10 | 10 um fingers incl. outer ones | inner fingers 10 um (5 um per channel side), **outer fingers 5 um** |

Single-channel devices are the main-TFT cross-section rotated 90 deg, so the pads stay
gate W / source N / drain S (subtitle unchanged). Rc and dL from the ladder now apply directly
to your TFTs; the LOV sweep isolates the gated overlap with the ungated contact held constant.

**Trade-off:** the interdigitated devices keep all-gated contacts (no 45 um ungated extension) —
adding it would force the gate lead under an electrode, and it would destroy their current density.

Block re-packed column-first: PERF_TFT 1840 x 3071 um (4 columns 4/4/4/2), SYN_1T1R right beside it.

## Verification
connectivity 0 · overlay 8 (same pre-existing MEM_HIGH_VALUE windows) · structure overlap 63 um² ·
gaps < 60 um: none · TEXT 0 · keep-out 0 · DRC 25/61 (baseline), PERF_TFT 0/0 · no cells changed
outside PERF_TFT + its 14 device cells.

Not changed: the SYN_1T1R synapse drivers still use the old fully-gated 10 um fingers.
