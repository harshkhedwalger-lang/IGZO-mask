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

## Endurance at different read voltages (`endurance_read_voltages.py`)
This reads each of the best-50 cycles at +0.05, −0.05, +0.1 and −0.1 V. Within one cycle (SET n, then RESET n):

| Polarity | HRS read from | LRS read from |
|---|---|---|
| + | SET sweep, before switching (the state left by RESET n−1) | SET return sweep (rejected if still at compliance) |
| − | RESET return sweep | RESET sweep, before switching |

Run 2_21 used 0.1 V steps, so it has no ±0.05 V point. Those reads are left empty, not interpolated, so the 0.05 V panels show the 30 TE_SET cycles only.

| Read | n | LRS median | HRS median | ON/OFF median | ON/OFF min |
|---|---|---|---|---|---|
| +0.05 V | 30 | 13.3 kΩ | 177 MΩ | 1.6 × 10⁴ | 19 |
| −0.05 V | 30 | 13.5 kΩ | 59 MΩ | 5.9 × 10³ | 164 |
| +0.1 V | 50 | 6.5 kΩ | 42 MΩ | 7.0 × 10³ | 19 |
| −0.1 V | 50 | 6.3 kΩ | 21 MΩ | 2.7 × 10³ | 155 |

On the TE_SET cycles alone, the LRS medians are 13.3–13.5 kΩ at 0.05 V and 12.7–12.8 kΩ at 0.1 V, and they are the same on both polarities. So the LRS is close to ohmic (resistive), and the lower 0.1 V median in the table only reflects the 2_21 cycles it adds.

The HRS is higher on the + side and higher at 0.05 V than at 0.1 V, which means it is non-linear. At +0.05 V the HRS current falls to about 0.03–1 nA, close to the SMU noise floor, so ±0.1 V gives the more reliable HRS values. The one dip at + polarity (best no. 47 = TE_SET cycle 40, HRS ≈ 1 MΩ) is the state left by the failed RESET of rejected cycle 39. Cycle 40's own RESET gives a normal HRS of 32–47 MΩ on the − side.

Outputs:
- `out/endurance_read_voltages.txt`: every R and ON/OFF value.
- `out/endurance_read_voltages.png`: the 2 × 2 grid for all 50 cycles.
- `out/endurance_read_voltages_TE_SET.png`: the TE_SET run against its own cycle numbers.

## Most-stable 50 cycles (`stable50.py`)
This is a second selection, made for an endurance plot with little cycle-to-cycle variation. From the 82 valid cycles, it keeps the 50 whose HRS and LRS (at ±0.1 V) fall in the narrowest common band. The band search found a centre of HRS+ ≈ 56 MΩ, HRS− ≈ 14 MΩ and LRS ≈ 9 kΩ, with a half-width of 0.79 decades. The selection takes 25 cycles from each run, plotted in measurement order as "selected cycle no." 1–50.

**These cycles are not consecutive.** The run and original cycle number of every point are in `out/stable50_metrics.txt`. When you publish, call them "50 selected DC cycles", not consecutive endurance.

| Read at 0.1 V | Best-50: spread | Stable-50: spread | Best-50: mean jump between cycles | Stable-50: mean jump between cycles |
|---|---|---|---|---|
| HRS + | 2.85 dec | 1.57 dec | 0.39 dec | 0.27 dec |
| HRS − | 2.58 dec | 1.54 dec | 0.30 dec | 0.21 dec |
| LRS | 1.58 dec | 1.53 dec | 0.32 dec | 0.32 dec |

For the stable set, ON/OFF at +0.1 V has a median of 5.0 × 10³ and a minimum of 270. At −0.1 V the median is 1.4 × 10³ and the minimum 51.

The −0.1 V HRS still steps up by about one decade at selected cycle 25 → 26, where the plot moves from run 2_21 to run TE_SET. This is a real difference between the two runs, and no choice of cycles removes it. To show a plot with no step, show one run only.

Outputs:
- `out/stable50_endurance_0p1V.png`: ±0.1 V endurance.
- `out/stable50_endurance_4reads.png`: ±0.05 V and ±0.1 V endurance.
- `out/stable50_IV_semilog.png`: overlay of the 50 I-V loops.
- `out/stable50_metrics.txt`: values per cycle.
- `out/stable50_IV_data.txt`: raw V-I data of the 50 cycles.

## Publication-style figures (`publication_plots.py`)
These figures copy the style of a standard RRAM paper: serif font, boxed axes with inward ticks on all four sides, and a dashed grid. Each figure is saved as PNG (300 dpi) and as PDF (vector, for journals). The script makes them for both the stable-50 and the best-50 sets.

- `out/pub_<set>_IV`: all 50 cycles in grey, with one typical cycle highlighted (SET in blue, RESET in red) and the CC line. The highlighted cycle is the one closest to the set median in R and switching voltage: 2_21 cycle 9 for stable50, TE_SET cycle 4 for best50.
- `out/pub_<set>_endurance`: R at |V| = 100 mV. The SET sweep (+0.1 V) is drawn as blue circles and the RESET sweep (−0.1 V) as red squares; HRS markers are open and LRS markers filled. Below it is the window R_HRS/R_LRS, with a dashed line at 10×.
- `out/pub_<set>_combined`: both panels side by side.

The LRS reads the same at + and − (it is ohmic), so the blue LRS dots sit inside the red squares.

**Common sweep window (I-V figures):** the I-V panels show only −2.5 V to +4 V, the range both runs covered. Run 2_21 swept to −3 V (one stable-50 cycle to −3.5 V) and TE_SET to +5 V. The trim affects the display only: every R and ON/OFF value is still read from the full sweeps. To change the window, set `V_NEG_LIMIT` / `V_POS_LIMIT` in `publication_plots.py` (for example −2.0). Suggested caption wording: *"RESET sweeps of run 2_21 (to −3 V) are shown to −2.5 V, the common sweep limit."*

## Device 5_5 (2026-09-04) — `plot_5_5.py`
Raw files are in `raw_5_5/`: ID1 is empty (a timestamp only), ID2 is the forming sweep (0 → 10 V), ID3 the SET sweeps (0 → 3 V) and ID4 the RESET sweeps (0 → −2 V). All steps are 0.05 V and CC = 0.1 mA. The 50 consecutive cycles are all plotted in measurement order, with no selection. Outputs go to `out_5_5/`: `forming`, `IV`, `endurance` and `combined` (each as PNG and PDF), plus `cycle_metrics.txt` and `IV_all_cycles.txt`.

On the SET sweep the current limit is active in both directions, so a read at the limit is left out instead of recorded as R = 0.1 V / 110 µA. That applies to the cycle-1 HRS (still LRS after forming) and to the LRS of cycles 1, 16, 18, 19, 25 and 32, which only tells us R ≤ 0.91 kΩ. The RESET sweep has no limit, so all of its reads are kept.

This device differs from 2_21 and TE_SET in four ways:
- **Low HRS:** about 130 kΩ, against 10–300 MΩ for the earlier devices.
- **Small window:** a median of about 25× (SET sweep) and about 26× (RESET sweep).
- **Low SET voltage:** about 0.7 V.
- **Mostly gradual RESET:** in 43 of 50 cycles the current is still rising at −2 V.
