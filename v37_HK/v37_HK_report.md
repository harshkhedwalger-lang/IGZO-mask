# v37_HK — change report (from v36_HK)

Two new blocks. **Nothing else in the mask changed** (only `TOP` differs, by the two added instances).

## SYN_1T1R — gate-set-compliance analog synapse (8 cells)
Compact 4-pad cell, N/S/E/W manual probing: **W = gate, N = source, S = drain/BE node, E = memristor TE**.

The S pad sits on the internal drain–BE node. That is the point of the cell: the *same* junction can be measured
- as a bare 1R (TE ↔ S pad), then
- as 1T1R (TE ↔ N source, gate = compliance knob),

so the variability/analog-level improvement is proven on one device rather than across two populations.

| driver (W/L = 25 fixed) | fingers | junction |
|---|---|---|
| W500 / L20 | 4 | 2×2 and 4×4 µm |
| W250 / L10 | 2 | 2×2 and 4×4 µm |
| W125 / L5 | 1 | 2×2 and 4×4 µm |
| W50 / L2 | 1 | 2×2 and 4×4 µm |

W/L is held at exactly 25 per your requirement, while footprint drops ~10× across the set → answers "same drive, less area", and sweeps the compliance range the gate can deliver. Junction area measured back out of the geometry: **4.0 µm² and 16.0 µm²** exactly (cross-point, both necks overshoot the crossing ≥10 µm → area is overlay-independent).

## PERF_TFT — high-Id / mobility / footprint TFTs (14 cells)
3 pads (W gate, N source, S drain). Interdigitated comb generator; W set by the IGZO edge, L by the M3 finger gap (single-edge on both).

- **Id per unit area:** straight W100/L10 reference vs interdigitated W1000/L10, W1000/L5, W2000/L10. The W2000 comb occupies ~210 × 200 µm of active area instead of a 2000 µm-wide device.
- **Contact-overlap sweep** Lov = finger width = 2/5/10/20/40 µm at W100/L10 → R_c vs contact length, transfer length L_T. In staggered IGZO the vertical access through un-accumulated IGZO dominates R_c, so this directly sets how much Id you can get.
- **Channel-length ladder** L = 2/3/5/10/20/50/100 µm at W100 → R_total·W vs L at fixed V_ov, i.e. R_c·W intercept and intrinsic mobility. This was the long-standing roadmap item.

## Verification (`v37_build_log.txt`)
| check | result |
|---|---|
| connectivity / fabricability | 4 findings, all the pre-existing `MIS OPEN` plates (unchanged since v35) |
| overlay rules (ENC 3, OVL 2) | 8 findings, all the pre-existing `MEM_HIGH_VALUE` resistor ends |
| net extraction, new cells | 8 synapse cells = 4 nets / 4 pads each; 14 TFT cells = 3 nets / 3 pads each; **0 mismatches** |
| structure overlap | 63 µm² (the same legacy v22 stray dash at CBKR) |
| block gaps to neighbours | ≥ 80 µm, none closer |
| text / label collisions | 0 (TEXT$ instances and in-cell labels) |
| alignment-mark keep-out | 0 violations |
| DRC 2 µm | TOP 25 width / 63 space (unchanged); `SYN_1T1R` and `PERF_TFT` **0 / 0** |
| existing cells changed | none (`TOP` only) |

## Note on the hatched layer in your screenshot
That is layer **0/0 `Alignment`** — one box spanning −9950…10050 µm that frames the whole die, present since v22. It underlies every structure, so it hatches the whole view wherever 0/0 is visible. Not an overlap; hide 0/0 in the layer panel.
