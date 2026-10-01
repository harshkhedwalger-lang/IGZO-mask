# v43_HK — change report (from v42_HK)

## 1. The "3 CV structures" — analysed, found NOT redundant, none removed
Checked the actual drawn layer composition of all three (not assumed):

| block | layers used | what it actually tests |
|---|---|---|
| `AL2O3_INTEGRITY` | M1, Isolation_1, M2, M3, Passivation — **no IGZO** | pure M1/Al₂O₃/M2 MIM — Al₂O₃ pinhole/breakdown alone |
| `HFO2_MIM` | Isolation_1, M2, M3, Passivation — **no M1, no IGZO** | pure M2/HfO₂/M3 MIM — HfO₂ pinhole/breakdown alone |
| `MIS_CV_Block` | M1, Isolation_1, **IGZO**, M3, Passivation — **no M2** | M1/(Al₂O₃+HfO₂ in series, since M2 is absent here)/IGZO/M3 — the real TFT gate-stack C-V (C_ox, D_it, V_th) |

These are not duplicates: two test an individual dielectric's integrity with no semiconductor present,
the third tests the combined dielectric stack's device-relevant behaviour with the channel present —
and its C_ox is what every mobility number elsewhere on this reticle depends on. Removing any of them
would cut real characterization capability, not redundancy. **Nothing was deleted.** They look alike
because all three use the same guard-ring-with-pads visual convention, not because they overlap in
purpose.

## 2. Memristors_Gated — regrouped by gap length, moved to the top-right corner
**Before:** 4 TYPE sections stacked vertically (LATERAL RING GATED / LATERAL OPEN GATED / VERTICAL GATED /
PROCESS SPLITS), each already ordered by gap length (2, 3, 4, 6 µm) as its own 4 columns.
**After:** transposed so **gap length is the primary grouping** — every device of a given length,
regardless of type, now sits in one contiguous cluster (type becomes the sub-column inside it). Laid out
as a 2×2 grid of length-groups (L=2, L=3 on top; L=4, L=6 below) — a single-row layout came out 4178 µm
wide, wider than any available space near a corner, so 2×2 was used instead for a roughly square
footprint that actually fits.

Each of the 42 devices is its own self-contained child instance with its own label baked into its own
cell (confirmed: "G2-1" etc. lives inside `MEM_G2_1` itself) — so this was a plain per-instance move, not
flat-geometry surgery. No device geometry was touched, only which instance sits where. The 4 old
type-section headers (now inaccurate for the new grouping) were replaced with 4 new length-group headers;
the block's own title is kept.

**Relocated to the top-right corner**, TOP bbox (4616,5161)–(6900,6706) — found by an automatic search
that verified clearance from every alignment mark and every other block, not placed by eye.

## Verification (`v43_build_log.txt`)
| check | result |
|---|---|
| device-to-device overlaps (new layout) | 0 |
| label-to-device collisions | 0 |
| device set unchanged (still all 42) | confirmed |
| spot-checked device cell definitions | unchanged (own geometry identical) |
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 µm², same pre-existing legacy stray dash near CBKR |
| gaps to neighbours | none < 60 µm |
| alignment-mark keep-out | 0 violations |
| DRC 2 µm | `Memristors_Gated`: 0 width / 0 space |
| cells changed other than `Memristors_Gated` | none |

## Note on the first attempt (not shipped)
A first pass anchored the new 2×2 layout at the block's old (narrow) position without recomputing where
that leaves it — the new layout is wider, so part of it landed off the die edge. Caught by the placement
before committing; fixed by an explicit corner-search step instead of reusing the old anchor.
