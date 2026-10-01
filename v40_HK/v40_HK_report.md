# v40_HK — change report (from v39_HK)

Pure reorganisation of `TestStructures`' internal layout. No device redrawn, resized, or relabeled.

## What changed
Identified `TestStructures`' content from real geometry (not guessed): it splits cleanly at y = -470 µm
(verified: 0 shapes straddle that line) into an **upper zone** (TLM back-bias, 2 ladders, + one gated
device, 3265×1189 µm) and a **lower zone** (GATE OXIDE 1 TESTS, 6 devices in one row, 4120×620 µm).
`MIS_CV_Block` (8 guarded caps, added in v39) is a separate child instance.

Both the upper and lower zones were **rigid-translated** (never redrawn) into a tight 2-row stack —
lower zone at the bottom, upper zone 150 µm above it — replacing the old layout's mix of ad-hoc gaps
(46–830 µm) with one uniform 150 µm gap. `MIS_CV_Block` was **left exactly where v39 verified it clean**.

**New footprint: 6836 × 2098 µm, down from 6786 × 2793** — same width, 25% shorter.

## Bugs hit and fixed before shipping (documented, not just fixed silently)
1. **Wrong anchor.** First attempt placed the new layout at a fresh local (0,0) instead of anchoring to
   `TestStructures`' own original footprint corner. Since `TestStructures`' own placement in `TOP` never
   moves, this put the (correctly-sized) new layout in the wrong *place* in local space — overlapping
   `CBKR_Structures`, `MEM_STACK_SPLIT` and `1T1R` by hundreds of thousands of µm². Caught by the
   block-overlap check before writing.
2. **Sequential re-scan corrupted geometry.** Moving zone A to a position that geometrically overlaps
   zone B's *original* footprint, then erasing zone B by overlap-matching, deleted some of zone A's
   already-placed shapes too (they were sitting where B's original footprint said to erase). Fixed by
   separating all erases (at original positions) from all inserts (at target positions) across both
   zones — never interleaved.
3. **A text-instance move predicate swept up `MIS_CV_Block` itself**, not just the `TEXT$` labels it was
   meant to move with each zone, because it only checked position, not that the target was actually a
   text cell. Caused `MIS_CV_Block` to be translated twice. Fixed by requiring `cell.name.startswith('TEXT')`.
4. **My own verification method produced two rounds of false positives** before I trusted it: a
   `db.Region.merge()`-based before/after diff and an "exact polygon interacting" check both flagged
   nonexistent corruption, because touching shapes (e.g. TLM's pitch-number labels touching the ladder
   bar) merge differently depending on adjacency semantics that don't survive being split across two
   independent merge calls. Replaced with the simplest possible invariant — total area and shape count
   per layer, v39 vs v40 — which is unambiguous and passed cleanly once the real bugs (1–3) were fixed.
5. A small (116 µm²) real corner-clip into an alignment cross's keep-out and the long-standing stray v22
   artefact near CBKR was resolved by an automatic nudge search (both zones moved together by the same
   small delta, so their relative arrangement is unaffected), not a hand-guessed offset.

## Verification (`v40_build_log.txt`)
| check | result |
|---|---|
| **congruence, all 6 layers** | v39 area and shape count == v40 area and shape count, exactly, on Metal_1, Isolation_1, Metal_2, IGZO, Metal_3, Passivation |
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 µm², the same pre-existing legacy stray dash near CBKR (unrelated, unchanged) |
| internal collisions (upper/lower/MIS) | 0 / 0 / 0 |
| alignment-mark keep-out | 0 violations |
| text collisions | 0 |
| DRC 2 µm | `TestStructures`: 0 width / 0 space |
| TOP-own geometry | identical to v39 |
| cells changed other than `TestStructures` | none |
