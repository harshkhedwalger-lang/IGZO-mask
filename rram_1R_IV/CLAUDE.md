# RRAM / 1T1R I-V data — start here

This folder is separate from the mask work in the repo root. It holds raw SMU I-V data, analysis scripts and plots.
Full per-dataset notes: `README.md` (same folder). Every script runs standalone: `python <script>.py`
(needs numpy, pandas and matplotlib; `numpy.trapezoid`, not `trapz`).

## Datasets
| Folder | Device | Files | Script | Output |
|---|---|---|---|---|
| `raw/` | 1R, runs 2_21 (Aug 11) + TE_SET (Aug 24), CC 0.1 mA | `*_ID2_forming`, `*_ID3_set`, `*_ID4_reset` | `analyze_best50.py` → `endurance_read_voltages.py`, `stable50.py`, `publication_plots.py`, `onoff_raw_table.py` | `out/` |
| `raw_5_5/` | 1R device 5_5, CC 0.1 mA, SET 0→3 V, RESET 0→−2 V | ID2 forming, ID3 set, ID4 reset | `plot_device.py 5_5` | `out_5_5/` |
| `raw_8_81/` | 1R device 8_81, CC 0.5 mA (530 µA plateau), no abrupt forming | ID2 forming, ID3 set, ID4 reset | `plot_device.py 8_81` | `out_8_81/` |
| `raw_L20_2_2_3/` | 1T1R L20, 150 cycles, V_G 4.5 V SET / 6→7 V RESET | ID4-3 set, ID5-4 reset | `onoff_stats_L20.py` | `out_L20_2_2_3/` |
| `raw_1T1R_2x2/` | 1T1R IGZO 2 × 2 overlap, 2026-06-18, V_G 6.69 V SET / 7.0 V RESET | `TE_SET_ID3-2` set, `TE_SET_ID4-3` reset | `plot_1T1R_2x2.py` | `out_1T1R_2x2/` (+ `journal_*`, `journal_data/`, zip) |

Not used: `*_ID1*` files (timestamp only); `raw_1T1R_2x2/TE_SET_ID3-2_20260914_180932.txt`, a separate session
with 4 SET loops at V_G 5.8 V, no RESET file and its last loop cut off.

## Raw file format
Tab-separated. Line 1 is the header, line 2 the units, line 3 blank, then data (`skiprows=[1, 2]`); `--` means NaN.
Columns: `Time elapsed`, `Time stamp`, `Loop Index` / `Loop2 Index`, `SMU_BE_<set|reset> Voltage/Current`,
(1T1R only) `SMU_G[2] Voltage/Current`, `SMU_TE_<set|reset> Voltage/Current`.
Use the TE voltage and current. SET loop n is followed in time by RESET loop n, and the pair makes one cycle.

## Conventions settled with the owner (keep them)
- **Read rules** at |V_read| = 0.1 V (also 0.05 V):
  - SET sweep: HRS = up branch before switching, LRS = down branch.
  - RESET sweep: LRS = out branch before switching, HRS = back branch.
  - Only accept a measured point within 10 mV of V_read; never interpolate.
- **Compliance:** on 1R SET sweeps, a point at ≥ 0.95 × CC is NaN (R is then only an upper bound). RESET sweeps have no limit.
- **Report the median** ON/OFF, not the mean: the mean is skewed by a few cycles near the noise floor.
  Quote the read voltage and polarity, and give P10–P90 for spread.
- **Cycle exclusions are rule-based and listed in the figure caption or a file.** 1T1R 2 × 2 drops cycle 1
  (forming: pristine 237 MΩ, abrupt at ≈ 3.05 V) and cycles 21 and 36 (failed SET: LRS > 2 × median LRS), leaving 47.
- **"Selected" cycles are never called consecutive.** The stable50 and best50 sets in `out/` are selections.
- **Highlighted I-V cycle:** in 1T1R 2 × 2 it is the *best* cycle (34, largest loop area plus window), labelled as such.
- **Plot style:** serif font, inward ticks on all sides, SET blue `#1f5fa8`, RESET red `#c62828`, other cycles grey.
  Endurance: HRS open, LRS filled, circles = SET sweep, squares = RESET sweep. `journal_*` figures carry no
  annotations (no V_GS, arrows or captions). Current axis 1e-7 to 1e-2 A.
- **1T1R resistances** include the TFT channel in series, so LRS differs between the SET and RESET sweeps.
- Ask the owner before guessing anything process-related, for example what "2 × 2" refers to and its units.
