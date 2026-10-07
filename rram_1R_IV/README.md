# 1R HfO2 RRAM — DC I-V cycling, CC = 0.1 mA — best 50 cycles

Re-run everything with `python analyze_best50.py` (needs numpy, pandas, matplotlib).

## Raw data (`raw/`)
| File | Content |
|---|---|
| `2_21_ID2_forming.txt` | Forming, 0 → 15 V, CC 0.1 mA (formed at ≈ 6.7 V), 2026-08-11 |
| `2_21_ID3_set.txt` / `2_21_ID4_reset.txt` | Run 1, 46 cycles, SET 0 → 4 V, RESET 0 → −3 V (−3.5/−4 V on some), 2026-08-11 |
| `TE_SET_ID3_set.txt` / `TE_SET_ID4_reset.txt` | Run 2, 50 cycles, SET 0 → 5 V, RESET 0 → −2.5 V, 2026-08-24 |

The measurements alternate, so SET loop *n* followed by RESET loop *n* makes one cycle. The TE is biased and the BE is grounded. The SMU compliance plateau sits at 110 µA, which is the nominal 0.1 mA setting.

## How "best" is chosen
1. **Valid cycle:** the SET reaches CC; the device is in HRS before the SET (R at 0.2 V ≥ 5 × LRS), so it really switches; HRS/LRS ≥ 5 after RESET; the RESET current stays below 2 mA (no hard breakdown); the sweep is complete.
2. **Score (valid cycles only):** `log10(ON/OFF) − 0.25 × Σ robust-z(log R_LRS, log R_HRS, Vset, Vreset)`. The score rewards a large memory window and penalises cycles far from the typical behaviour.
3. The top 50 by score are taken from both runs combined: 20 from 2_21 and 30 from TE_SET.

The rejected cycles are listed in `out/cycle_metrics_all.txt` with `valid = False`:
- **2_21 cycle 1:** the first cycle after forming. It is already in LRS and the RESET current reaches 2.6 mA.
- **2_21 cycles 28, 30–35 and 43–46:** the device was stuck in LRS or leaky, with RESET currents of 2.5–4.9 mA. Cycle 46 is an aborted sweep of 5 points.
- **TE_SET cycle 1:** already in LRS from the previous step.
- **TE_SET cycle 39:** failed SET, with LRS ≈ 109 kΩ and ON/OFF ≈ 4.

## Outputs (`out/`)
| File | Content |
|---|---|
| `best50_IV_data.txt` | Full V-I data of the 50 cycles, long format (`best_no, run, cycle, sweep, V, I`) |
| `best50_IV_wide.txt` | The same data with one V/I column pair per cycle, ready to paste into Origin |
| `best50_metrics.txt` | Per-cycle Vset, Vreset, Ireset, R_LRS, R_HRS, ON/OFF (read at 0.2 V) |
| `cycle_metrics_all.txt` | Metrics, valid flag and score for all 96 cycles |
| `best50_IV_semilog.png` | Overlay of the 50 I-V loops, \|I\| on a log scale |
| `best50_endurance_cdf.png` | LRS/HRS against cycle number, plus CDFs of R and V |
| `per_run_selected_vs_rejected.png` | Each run with the selected cycles in blue and the rest in grey |

## Best-50 statistics (read at 0.2 V)
| | mean | median | min | max |
|---|---|---|---|---|
| Vset (V) | 1.69 ± 0.36 | 1.70 | 0.90 | 2.40 |
| Vreset (V) | −0.96 ± 0.35 | −0.90 | −2.40 | −0.40 |
| Ireset (mA) | 0.34 | 0.30 | 0.10 | 0.84 |
| R_LRS (kΩ) | 10.4 | 5.6 | 1.4 | 54 |
| R_HRS (MΩ) | 21.6 | 10.8 | 1.1 | 223 |
| ON/OFF | — | ≈ 1.3 × 10³ | 140 | 1.2 × 10⁵ |

Run 2_21 gives HRS ≈ 1–4 MΩ, and run TE_SET gives HRS ≈ 10–50 MΩ, a wider window. The 2_21 run degrades after about cycle 27, when the device gets stuck in LRS.
