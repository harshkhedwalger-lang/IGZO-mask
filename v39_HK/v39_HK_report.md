# v39_HK — change report (from v38_HK)

Pure reorganisation, no new or resized devices.

## What changed
1. **Removed `FGTFT_L30_W380_N8`** (2 device copies + heading) from `TestStructures`. Verified before
   deletion: this geometry is flat (not a sub-cell), confined exactly to local x[2366,4955] y[-1941,-657]
   inside `TestStructures`, and nothing else `TestStructures` owns shares that rectangle (checked against
   the cell's full footprint) — a clean, non-straddling cut, same method used for the v35 coplanar-TFT
   removal.
2. **Relocated the whole MIS capacitor family** (`MISv2_S50_F1` … `MISv2_SHORT_S100`, 8 cells, unchanged
   from v38) out of its old standalone block at the upper-left of the die, repacked into `MIS_CV_Block`,
   and inserted as an actual **child instance of `TestStructures`**, in the space FGTFT vacated — so the
   MIS capacitors are now physically part of the same block as TLM, gated Van der Pauw/Greek cross and
   the gate-oxide-1 caps, per "all the test structures in the bottom, more organised."
3. First placement attempt clipped 300 µm² of one pad's corner into the alignment cross keep-out zone at
   (3000,−7000); fixed by an automatic search for the nearest offset that clears every alignment mark
   (not a guessed nudge).

## Verification (`v39_build_log.txt`)
| check | result |
|---|---|
| connectivity / fabricability | 0 findings |
| overlay rules | 8, all pre-existing `MEM_HIGH_VALUE` (unrelated, unchanged) |
| MIS device net topology | unchanged by the move — 0 mismatches across all 8 devices |
| structure overlap | 63 µm², the same pre-existing legacy stray dash near CBKR |
| gaps to neighbours | none < 60 µm |
| text collisions | 0 |
| alignment-mark keep-out | 0 violations |
| DRC 2 µm | `TestStructures`: 0 width / 0 space |
| TOP-own geometry | identical to v38 |
| cells changed other than `TestStructures` | none |

## Note
`MIS_Capacitors` (the pre-rebuild, buggy version from before v38) and the now-empty former
`MIS_Capacitors_v2` container are unplaced housekeeping only; the 8 device cells themselves are the
same ones verified in v38 and are untouched here — only their container and placement changed.
