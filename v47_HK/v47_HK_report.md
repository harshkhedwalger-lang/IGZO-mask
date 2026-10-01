# v47_HK — change report (from v46_HK)

## 1. Memristors_Gated redesigned onto 100x100um pads (90x90 windows)
Per explicit request, every device keeps its own 3 independent pads (BE, Gate, TE) rather
than sharing bus pads — but the initial 150x150 pass (matching the mask-wide standard
exactly) made each device 626x477um and the 42-device grid 5568x3303um, which **did not fit
anywhere on the die** (checked by a full-die search, not assumed). Reduced to **100x100 pads
/ 90x90 windows** per follow-up request — device footprint is now 526x427um.

Also reduced from 3 repeats/type to **1 repeat/type (14 devices instead of 42)** — confirmed
with you as the way to make the independent-pad approach fit, since even at 100x100 the
3-repeat version doesn't reliably clear the die alongside everything else already placed.

**How the redesign works** (same recipe on all 14 devices — checked first that all device
types share byte-identical pad-region geometry, only the channel/gap between the pads
differs): each device's 3 old 81x81 pads + their 75x75 windows are removed, and each terminal
is regrown from the boundary of its still-intact channel-side lead using this mask's own
`pad_lead()` recipe (75um taper) — BE grows west, Gate grows south, TE grows east, so the
three new pads can't collide with each other or the channel geometry between them. The IGZO
channel itself was never touched (verified byte-identical in all 14 devices).

**New layout**: single column, one row per gap length (L2/L3/L4/L6 top to bottom) — the old
2x2-of-3-repeats grid doesn't make sense with only 1 repeat, so this reads better as 4 rows.
Grid footprint 2284x2308um.

**New placement**: the block no longer fits back in the old top-right corner (was 2284x1439,
now taller). Found by a full-die clear-space search with an 80um clearance margin required
from every neighbor, not just zero-overlap — lands well clear of the "active 3D" logo (the
original complaint) and everything else, gaps to nearest neighbors all >= 60um.

## 2. TestStructures row1 tidied up (TLM_BACK_BIAS + Greek-cross baseline-aligned)
TLM_BACK_BIAS and the Greek-cross structure sat 151um off from each other at the bottom —
TLM bottom at y=643.1, Greek-cross bottom at y=492.0 (local coords), making the "row" look
uneven. Shifted the Greek-cross structure (and its title, added in v45) up by 151.1um to
match TLM's bottom edge. Checked real headroom before doing it: new top clears the nearest
real obstacle (`1T1R`) by 67um, still positive.

## Verification (`v47_build_log.txt`)
| check | result |
|---|---|
| device-to-device overlaps (new grid) | 0 |
| label-to-device collisions | 0 |
| device set unchanged (14 placed, matches selection) | confirmed |
| IGZO channel geometry unchanged in all 14 devices | confirmed (byte-identical) |
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 um², same pre-existing legacy stray dash near CBKR, unchanged |
| Memristors_Gated gaps to neighbours | none < 60um |
| TEXT$ collisions | 0 |
| alignment keep-out violations | 0 |
| DRC 2um TOP | width 25 / space 61 — identical to v42–v46 baseline |
| cells other than Memristors_Gated/TestStructures/its devices changed | none |

## Bugs caught during this pass (fixed before shipping, not after)
- First redesign attempt at 150x150 pads left 28 old-scale device instances still
  instantiated alongside the 14 new ones (only erased the ones being replaced, not the full
  original 42) — caused 14 false M1-M2 shorts and 38 false floating-island findings. Fixed by
  erasing all 42 original instances up front, then placing only the selected 14.
- The scaled-up title text (cap=48) exceeded the fabricability checker's 40um glyph-height
  threshold and got flagged as real floating metal instead of recognized as text. Reverted to
  the same cap sizes (36/24) used successfully elsewhere on this mask.
- The block-placement search used a relative transform but computed the delta as if setting
  an absolute position, landing the block outside the die entirely on the first attempt.
  Fixed by computing the candidate region from the block's actual current position.
