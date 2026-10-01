# v48_HK — change report (from v47_HK)

## A. Gated memristors — compact pad-out (your image 1 vs 2)
v47 regrew the 100x100 pads from the *outer* edge of the old 81um-pad footprint, so the TE and
Gate arms still carried an 80x80um stub where the old pad used to be, plus a 75um taper that
only widened 80->100um. Each device is now clipped back to its junction core (x80..176,
y80..220 local: the original small tapers + the junction) and each terminal gets its 100x100 pad
straight off the core edge with a 30um taper.

| | v47 | v48 |
|---|---|---|
| device footprint | 526 x 427 um | **356 x 277 um** (-56% area) |
| Memristors_Gated block | 2284 x 2308 um | **1574 x 1575 um** |

Junction core verified byte-identical in all 14 devices. Block top-left corner kept in place.

## B. High-Value memristor set — rebuilt around untouched cores (image 3)
- Pads 150 -> **100x100 (90 window)**, same convention as the gated memristors; taper 40um;
  pad-centre distance 305 -> 180um; device pitch 680/800 -> 540/540.
- The 5th terminal (series-resistor gate on M1, guard ring on M3) now goes to a **diagonal
  corner pad on a straight route through the empty quadrant**. The old L-routes ran *under*
  the S pad (series column) and *into* the S taper (guard column).
- Block **1302 x 3252 -> 1051 x 2227 um** (-45%). Titles/labels moved with their devices.
- Verified: all 8 cores unchanged, all 38 probe pads kept (5,5,5,5 / 5,4,5,4), every 5th pad
  on the same net as in v47.

**Correction to what I said mid-way:** I first reported the guard trace as shorting the guard to
the TE. The real situation is that the **guard ring itself is drawn as a closed M3 square whose
top/bottom bars cross the TE line on the same metal**, so ring and TE are one conductor inside
the core already (true since at least v38). v48 keeps that topology exactly — see open items.

## C. TestStructures — single column (image 4)
Top to bottom, left-aligned at the same edge:
**TLM back-bias -> gated VdP + gated Greek cross (side by side) + their label -> Gate Oxide 1 -> Gate Oxide 2**,
MIS_CV_Block stays to the right (the column is 3.8 mm tall already; 83 um to 1T1R above).
- The Greek cross was loose TOP-level geometry; moved into TestStructures as asked.
- `TEXT$127` "GATED VDP & GREEK CROSS" is the pair's real label -> moved with them; the
  duplicate title I added in v45 is deleted.
- **FIX — gate short in both gated structures:** all 4 S/D contact windows (Isolation_1) of the
  VdP *and* of the Greek cross sat fully on the M1 gate plate. By this process's own rule an
  Iso1 window on M1 etches Al2O3 *and* HfO2, so IGZO and the M3 pad would land on the gate ->
  every contact shorted to the gate. Removed those 8 windows; the M3 pads now contact IGZO
  directly, like every other TFT on the reticle. Gate-pad windows (on M1, no IGZO, M3-capped)
  kept. New mask-wide rule added to verification: *no Iso1 window may expose M1 under IGZO* ->
  0 hits.

## Verification (`v48_build_log.txt`)
| check | result |
|---|---|
| connectivity / fabricability | 0 |
| overlay | 8 — the same pre-existing MEM_HIGH_VALUE contact windows (see open items) |
| structure overlap | 63 um², same legacy stray dash near CBKR |
| gaps < 60 um (3 changed blocks) | none |
| TEXT collisions / keep-out | 0 / 0 |
| DRC 2um TOP | 25 / 61 — identical to v42–v47 baseline; 0/0 inside all 3 changed blocks |
| cells changed outside the intended set | none |

## Open items that need your call (not changed)
1. **Guard ring (GRD 4x4, GRD 10x10)** is closed across the TE line on M3 -> it *is* the TE.
   As drawn it can't work as an independent guard, and its bars also cross the BE line
   (M3/HfO2/M2 = two extra parasitic cells). A working guard needs a C-shaped ring with a gap
   where TE passes, plus an M1 bridge under the TE to join the halves. Tell me the intent.
2. **8 series-resistor contact windows** (4x4um Iso1 on the 4um BE line) are not enclosed by
   the 3um overlay margin. Widening M2 into 10x10 landing pads would fix it, but adds M2 area
   under the IGZO contact pads (possible parasitic switching area), and for SER L30 would put
   M2 within 1um of the TE line. Left as is.
3. With the compact memristor, **3 repeats/type (42 devices)** would now fit in roughly
   3300 x 2100 um — say if you want the statistics back.
