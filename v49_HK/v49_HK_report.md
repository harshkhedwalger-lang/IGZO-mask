# v49_HK — change report (from v48_HK)

## 1. High-Id TFTs + gate-set-compliance synapses packed column-first
Devices stacked top->bottom, a new column only when the next device would not fit above the
Memristor block (60 um clearance). Order kept: REF -> IDT x3 -> LOV 2/5/20/40 -> L 2/3/5/20/50/100,
and W500 -> W250 -> W125 -> W50 (J2, J4 each). Synapses sit directly right of the TFTs, titles aligned.

| block | v48 | v49 |
|---|---|---|
| PERF_TFT | 5027 x 1701 um, 2 rows | **1890 x 3121 um**, 4 columns (3/4/4/3) |
| SYN_1T1R | 3850 x 1631 um, 2 rows | **1460 x 3101 um**, 2 columns (4/4) |

Rigid instance moves only (each device carries its own label); device cells untouched.

**Freed for new devices:** a strip ~5.9 mm wide x ~1.7 mm tall above 1T1R (x -3070..2920,
y 2850..4565 TOP), plus the top-right corner STEP_COVERAGE vacated (1070 x 1514 um at
x 2985..4055, y 5048..6562).

## 2. STEP_COVERAGE moved next to the TestStructures column
Now right of the TLM / gated VdP + Greek cross, top aligned with the TLM title
(TOP 620..1690, -4411..-2897), clearance-searched: >= 80 um to everything.

## Verification (`v49_build_log.txt`)
connectivity 0 · overlay 8 (same pre-existing MEM_HIGH_VALUE windows) · structure overlap 63 um²
(legacy) · gaps < 60 um for all 3 moved blocks: none · TEXT collisions 0 · keep-out 0 ·
DRC 25 / 61 (baseline) · cells changed outside PERF_TFT / SYN_1T1R / TOP: none.
