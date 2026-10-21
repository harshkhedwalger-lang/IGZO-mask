# Paper context — HfO₂ RRAM (1R) and IGZO-TFT 1T1R electrical results

**Purpose.** This file is the single source of truth for writing the journal paper from the I-V analysis in
`rram_1R_IV/`. Every number below comes from a saved output file, which is named next to it.

**Rules for any assistant using this file:**
1. Use only numbers that appear here or in the named output files. Never round a range into a better-sounding value.
2. Anything tagged `[CONFIRM]` is unverified process or device information. Ask the owner; do not fill it in.
3. Report medians, not means, for resistance and ON/OFF. Always state the read voltage and polarity.
4. Selected cycles are never called "consecutive endurance". Excluded cycles are always stated.
5. 1T1R resistances include the TFT channel in series. Say so whenever 1T1R values are compared with 1R values.

---

## 1. Devices and stack

| Device ID (raw folder) | Type | Notes |
|---|---|---|
| **1T1R 2 × 2** (`raw_1T1R_2x2/`) | IGZO TFT + HfO₂ RRAM, "IGZO 2 × 2 overlap" `[CONFIRM: units (µm?), and whether 2 × 2 is the RRAM cell or the IGZO/TFT overlap]` | **Main journal dataset.** Measured 2026-06-18. |
| L20_2_2_3 (`raw_L20_2_2_3/`) | 1T1R | 150 cycles, measured 2026-09-09. `[CONFIRM: geometry]` |
| 2_21 + TE_SET (`raw/`) | 1R | Measured 2026-08-11 (2_21) and 2026-08-24 (TE_SET). `[CONFIRM: same physical device?]` |
| 5_5 (`raw_5_5/`) | 1R | Measured 2026-09-04 |
| 8_81 (`raw_8_81/`) | 1R | Measured 2026-09-04 |

**Process flow, as documented for the HK mask series** (`v35_HK/CLAUDE.md` §2; `[CONFIRM it applies to the
measured dies, with thicknesses and electrode metals]`):

M1 (bottom gate) → ALD Al₂O₃ #1 (~20 nm, gate dielectric) → M2 (RRAM bottom electrode, TFT S/D) → ALD HfO₂
(switching layer) `[CONFIRM thickness]` → contact etch → IGZO (lift-off) `[CONFIRM thickness / deposition]`
→ M3 (top electrode, top S/D) → Al₂O₃ #2 passivation.

`[CONFIRM: TE / BE metals, HfO₂ thickness, IGZO deposition and anneal, TFT W/L of the 1T1R cells.]`

## 2. Measurement methods (what was done; verified from the raw files)

- **Instrument:** source-measure units on TE, BE and (1T1R) gate. TE swept, BE grounded; voltages and currents are
  TE values. `[CONFIRM: instrument model]`
- **Sweep protocol:** each cycle is one SET sweep followed by one RESET sweep (`Loop Index` n). DC double sweeps
  0 → V_max → 0.

| Device | SET sweep | RESET sweep | Step | Current limit / gate |
|---|---|---|---|---|
| 1T1R 2 × 2 | 0 → +4 V → 0 | 0 → −4 V → 0 | 0.05 V | V_G = 6.69 V (SET), 7.01 V (RESET); SET current set by the TFT; forming hit the 1 mA SMU limit |
| L20_2_2_3 | 0 → +4 V → 0 | 0 → −4.5 V → 0 | 0.1 V | V_G = 4.5 V (SET); 6.0 V (RESET, cycles 1–101) and 7.0 V (cycles 102–150) |
| 2_21 | 0 → +4 V | 0 → −3 V (some −3.5/−4 V) | 0.1 V | CC = 0.1 mA (plateau 110 µA) |
| TE_SET | 0 → +5 V | 0 → −2.5 V | 0.05 V | CC = 0.1 mA |
| 5_5 | 0 → +3 V | 0 → −2 V | 0.05 V | CC = 0.1 mA |
| 8_81 | 0 → +3 V (cycles 1–15), +2 V after | 0 → −2.2 V | 0.05 V | CC = 0.5 mA (plateau 530 µA) |

- **Read rule:** R = |V/I| at the measured point closest to |V_read| = 0.1 V (also 0.05 V), accepted only if
  it lies within 10 mV of V_read. No interpolation.
  - **SET sweep:** HRS on the up branch before switching; LRS on the down branch.
  - **RESET sweep:** LRS on the out branch before switching; HRS on the back branch.
  - **Window:** ON/OFF = R_HRS/R_LRS, computed per cycle and per sweep.
- **Compliance:** on 1R SET sweeps, a read at ≥ 0.95 × CC is discarded, because it only bounds R.
- **Statistics:** median with P10–P90 range. The mean is skewed by a few high cycles, and it is listed in the files for reference only.
- **Cycle exclusion (rule-based):** forming cycle, and failed SET = SET-sweep LRS > 2 × median LRS.

## 3. Results

### 3.1 1T1R, IGZO 2 × 2 (main dataset) — `out_1T1R_2x2/summary.txt`, `cycle_metrics.txt`
- **Forming (cycle 1):**
  - pristine R ≈ 237 MΩ at 0.1 V;
  - abrupt forming at ≈ 3.05 V (current 72 µA → 0.82 mA), then the 1 mA SMU limit.
- **Exclusions:** cycle 1 (forming), and cycles 21 and 36 (failed SET: LRS 37.8 and 18.2 kΩ against a 5.4 kΩ median).
  **47 of 50 cycles** analysed.

| Read | ON/OFF, SET sweep, median (P10–P90) | ON/OFF, RESET sweep, median (P10–P90) | HRS median (SET / RESET sweep) | LRS median (SET / RESET sweep) |
|---|---|---|---|---|
| 50 mV | 7.9× (5.2–12.1) | 9.5× (5.1–11.7) | 41.7 / 46.2 kΩ | 5.32 / 5.05 kΩ |
| 100 mV | 7.4× (5.0–10.4) | 9.1× (4.9–11.3) | 40.1 / 43.5 kΩ | 5.30 / 5.02 kΩ |

- **Range at 100 mV:** min 2.7× (SET) and 3.1× (RESET); max 17.5× and 16.4×.
- **Read-voltage dependence:** 50 mV and 100 mV reads agree within 8% (LRS within 1%, HRS within 6%), so both states are nearly
  ohmic at small bias. All read currents are ≥ 1 µA, far above the noise floor.
- **Most stable stretch:** cycles 37–50, with HRS ≈ 40–45 kΩ, LRS ≈ 5 kΩ and windows ≈ 8–10×.
- **Highlighted I-V:** the *best* cycle (34) is shown, chosen by the largest SET + RESET loop area plus window.
  It sets abruptly at ≈ 1.0 V. The SET is gradual in most cycles, so no Vset statistic is reported.
- **Observation (interpretation, `[CONFIRM]`):** the current at +4 V falls from 0.85 mA (cycle 2) to 0.45 mA
  (cycle 50), while the LRS at 0.1 V stays at about 5 kΩ. This is consistent with degradation of the TFT drive
  (e.g. a threshold shift under bias stress) rather than of the RRAM.

### 3.2 1T1R L20_2_2_3 — `out_L20_2_2_3/onoff_per_cycle.txt`
150 consecutive cycles, read at 100 mV.

| Quantity | Median | P10–P90 | Min–max |
|---|---|---|---|
| ON/OFF, SET sweep | 198× | 106–367× | 53–2104× |
| ON/OFF, RESET sweep | 100× | 59–149× | 24–238× |
| HRS / LRS, SET sweep | 2.58 MΩ / 13.2 kΩ | | |
| HRS / LRS, RESET sweep | 0.59 MΩ / 5.7 kΩ | | |

- All 150 cycles are above 10×.
- The SET-sweep mean (239×) is inflated by cycle 1 (2104×); the median is reported.
- The LRS differs between the sweeps (13.2 against 5.7 kΩ) because of the TFT channel at V_G = 4.5 V against 6–7 V.

### 3.3 1R devices
| Device | Forming | Cycles | ON/OFF median, SET / RESET sweep (100 mV) | HRS | LRS | Source |
|---|---|---|---|---|---|---|
| 2_21 + TE_SET, best-50 *selected* | ≈ 6.7 V (2_21) | 50 selected of 82 valid | 7.0 × 10³ / 2.7 × 10³ | 42 / 21 MΩ | 6.5 / 6.3 kΩ | `out/endurance_read_voltages.txt` |
| 2_21 + TE_SET, stable-50 *selected* | | 50 selected | 5.0 × 10³ / 1.4 × 10³ | | | `out/stable50_metrics.txt` |
| 5_5 | ≈ 5.8 V | 50 consecutive | 24.7× / 26.1× | ≈ 135 kΩ | ≈ 5.5–5.8 kΩ | `out_5_5/cycle_metrics.txt` |
| 8_81 (CC 0.5 mA) | none abrupt (≈ 25 kΩ pristine) | 50 consecutive | 555× / 474× | ≈ 0.5–0.6 MΩ | ≈ 0.72–0.77 kΩ | `out_8_81/cycle_metrics.txt` |

1R caveats:
- **2_21 + TE_SET:**
  - Combining the two runs assumes they are the same device `[CONFIRM]`.
  - The two runs differ in HRS by about one decade, which shows as a step in the endurance plots.
  - At ±0.05 V the HRS current approaches the SMU noise floor (about 0.2 nA). Values above about 10⁸ Ω are unreliable, so ±0.1 V is used.
- **5_5:**
  - The RESET is gradual and incomplete at −2 V: 43 of 50 cycles are still rising at −2 V.
  - This likely explains the low HRS.

## 4. Figures (journal versions: no annotations, PNG 300 dpi + vector PDF)

| File | Content | Draft caption |
|---|---|---|
| `out_1T1R_2x2/journal_IV.pdf` | I-V, 47 cycles in grey, best cycle 34 in colour | "Bipolar I-V characteristics of the IGZO-TFT/HfO₂ 1T1R cell (2 × 2 `[CONFIRM units]`) over 47 DC cycles. SET: V_G = 6.7 V; RESET: V_G = 7.0 V. The best cycle (34) is highlighted. The forming cycle and two failed SET cycles (21, 36) are excluded." |
| `out_1T1R_2x2/journal_endurance_100mV.pdf` | Endurance, read at 0.1 V | "Cycle-to-cycle HRS and LRS read at \|V\| = 100 mV on the SET (+, circles) and RESET (−, squares) sweeps, and the resulting R_HRS/R_LRS. Median window 7.4× (SET) and 9.1× (RESET). Resistances include the TFT channel." |
| `out_1T1R_2x2/journal_endurance_50mV.pdf` | Endurance, read at 0.05 V | Same, at 50 mV: median 7.9× / 9.5×. |
| `out_1T1R_2x2/journal_combined.pdf` | I-V + 100 mV endurance | Combine the two captions above. |
| `out_L20_2_2_3/` (data only) | 150-cycle window statistics | Make a figure on request. |
| `out_5_5/combined.pdf`, `out_8_81/combined.pdf`, `out/pub_*` | 1R figures (annotated style) | Ask for journal (clean) versions before use. |

Plotting data for every journal figure: `out_1T1R_2x2/journal_data/*.txt`, tab-separated, Origin/Excel-ready.

## 5. Draft text blocks (edit the [CONFIRM] parts)

**Methods — electrical characterisation.**
> DC I-V characteristics were measured with source-measure units `[CONFIRM model]` with the bottom electrode
> grounded and the voltage applied to the top electrode. In the 1T1R cells, the compliance was set by the IGZO TFT
> gate voltage (V_G = 6.7 V for SET, 7.0 V for RESET). Each cycle consisted of a SET sweep (0 → +4 V → 0) followed
> by a RESET sweep (0 → −4 V → 0) in 50 mV steps. Resistance states were extracted at |V_read| = 50 and 100 mV
> from the measured points of each sweep, without interpolation. The forming cycle and cycles with a failed SET
> (LRS more than twice the median LRS) were excluded. Statistics are reported as median and 10th–90th percentile.

**Results — 1T1R.**
> After forming at ≈ 3.05 V from a pristine resistance of ≈ 237 MΩ, the 1T1R cell switched bipolarly over 47 of 50
> DC cycles. Read at 100 mV, the median HRS and LRS were 40–44 kΩ and ≈ 5.0–5.3 kΩ, giving median ON/OFF ratios of
> 7.4× (SET sweep) and 9.1× (RESET sweep), with nearly identical values at 50 mV (7.9× and 9.5×), which indicates
> near-ohmic conduction in both states at low bias.

## 6. Limitations to state, and open questions for the owner
1. The 1T1R 2 × 2 window (≈ 7–9×) is small. Many cycles sit just below 10×. Do not claim "> 10×".
2. Only 50 DC cycles (47 analysed). Pulsed endurance and retention were not measured `[CONFIRM]`.
3. TFT current drive decreases over cycling: the +4 V current falls from 0.85 to 0.45 mA. This needs a TFT-only check `[CONFIRM]`.
4. `[CONFIRM]` the units and meaning of "2 × 2"; the stack thicknesses and electrode metals; the instrument;
   whether 2_21 and TE_SET are the same device; and which devices go in the paper.
5. The raw file `TE_SET_ID3-2_20260914_180932.txt` (Sept 14, 4 SET loops at V_G 5.8 V, no RESET) is not used.

## 7. Data and code map
- Raw data: `raw*/`.
- Scripts: `plot_1T1R_2x2.py`, `onoff_stats_L20.py`, `plot_device.py`, `analyze_best50.py`, `publication_plots.py`.
- Every figure and data file regenerates with `python <script>.py` (numpy, pandas, matplotlib).
- Detailed per-dataset notes: `README.md`. Conventions: `CLAUDE.md`.
- Repository: `harshkhedwalger-lang/IGZO-mask`, branch `claude/ecstatic-fermat-lqf97q`, folder `rram_1R_IV/`.
