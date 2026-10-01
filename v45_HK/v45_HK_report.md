# v45_HK — change report (from v44_HK)

## 1. MIS_CV_Block restored
"GUARDED MIS CAPACITORS — AREA-PERIMETER SERIES" is back, at its original position
(x2380–4652, y-1890–-86 local to `TestStructures`). Its cell definition had never actually
left the library — v44's `cleanup()` didn't prune it since it's harmless to leave unreferenced
cells around — so this is a plain re-instantiation, not a rebuild from scratch. Geometry is
byte-identical to before it was removed.

## 2. TestStructures re-laid out as 3 stacked rows
Top to bottom, as requested:

| Row | Content | Local y-range |
|---|---|---|
| 1 | TLM_BACK_BIAS + gated van der Pauw / Greek-cross | 492 – 1811 |
| 2 | GATE OXIDE 1 TESTS (Al2O3) | -1054 – -308 |
| 3 | GATE OXIDE 2 TESTS (HfO2) | -1890 – -1144 (== OXIDE 1's old spot) |

GATE OXIDE 2 was rebuilt as a single 6-device row (replacing v44's split 3+3 layout, which
only existed because the freed MIS_CV_Block footprint was too narrow for one row — moot now
that MIS_CV_Block no longer needs to share that space with it).

**Both rows above their target position hit real obstacles that weren't visible from the
per-block obstacle list alone — caught by the full collision check, not assumed clear:**

- Row 2 (GATE OXIDE 1)'s naive rise (896um, for a clean 150um gap to Row 3) ran into a
  **second, standalone gated van der Pauw / Greek-cross structure** that lives directly in
  `TOP`'s own layers near TOP-coordinate (1765, -4492)–(2815, -5212) — not inside any block
  instance, so a per-block obstacle scan doesn't see it. A leftward shift made things worse
  (ran into other geometry on that side instead), so the rise was reduced to 836um instead
  (110um gap to Row 3) — the largest rise that stays clear, found by search, not guessed.
- Row 1 (TLM + Greek-cross)'s ideal position (150um above the now-settled Row 2) landed
  underneath `TEXT$127`, a pre-existing label at TOP y -4399/-4330 that isn't part of any
  block either. Row 1 was pushed further up (dy=1603um instead of the naive 953um) until
  clear of it — margin to the real ceiling (`1T1R`, the nearest actual block above) is
  172um, still positive, still real.

Both of these standalone TOP-own obstacles were previously invisible to me because
`TestStructures` had never grown into their vicinity before. Flagging this because it means
the mask has more of this kind of loose, unblocked geometry sitting around than the
per-block bookkeeping suggested — worth keeping in mind for any future reorganization in
this area.

## 3. Greek-cross structure title added
It never had one baked into the mask (checked — real placed geometry, just unlabelled).
Added: `GATED VDP + GREEK CROSS`.

## Verification (`v45_build_log.txt`)
| check | result |
|---|---|
| MIS_CV_Block restored | confirmed present, geometry unchanged |
| GATE OXIDE 1 own geometry | congruent after un-shifting (xor area = 0) |
| TLM+Greek-cross own geometry + all 10 label instances | congruent after un-shifting (xor area = 0) |
| cells other than TOP/TestStructures changed | none |
| TestStructures vs every other TOP block | 0 |
| TestStructures vs alignment keep-out | 0 |
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 um², same pre-existing legacy stray dash near CBKR, unchanged |
| TEXT$ collisions | 0 |
| alignment keep-out violations | 0 |
| DRC 2um TOP | width 25 / space 61 — identical to v42/v43/v44 baseline |
| DRC 2um TestStructures | width 0 / space 0 |
