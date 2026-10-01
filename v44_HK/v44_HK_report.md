# v44_HK — change report (from v43_HK)

## What was removed
All 4 mapped exactly to the images sent, by actual layer composition (not by visual
similarity — a real inspection of each block's drawn geometry):

| removed block | where | what it was |
|---|---|---|
| `AL2O3_INTEGRITY` | top-level | 2-terminal Al2O3 MIM pinhole sweep (400/200/100 um) |
| `HFO2_MIM` | top-level | 2-terminal HfO2 MIM area sweep (400/200/100/50 um) |
| `MIS_CV_Block` | inside `TestStructures` | "GUARDED MIS CAPACITORS — AREA-PERIMETER SERIES": Al2O3+HfO2-in-series MIS stack (M2 absent, so Isolation_1 etches through both dielectrics) |
| `SPLIT_CV` | top-level | W=L=400um split MIS capacitor with an IGZO channel |

**Reasoning:** `TestStructures` already contains a superior version of the same
measurement — "GATE OXIDE 1 TESTS", 6 devices, 4-terminal (BE/TE force+sense) guard-cross
structures with a built-in area sweep, testing the Al2O3 (M1/Isolation_1/M2) stack. The 4
removed blocks were all simpler 2-terminal variants of the same underlying measurement
(dielectric pinhole/leakage vs. area), just for different dielectric combinations. Keeping
both the simple and the guarded version was the actual redundancy — not "3 different CV
structures testing different things" as I concluded last time (I was checking whether they
tested different things, which they do, but not whether a better structure already covers
the same ground within `TestStructures` — that comparison is what you were actually asking
for, and it's correct: these are worth cutting).

**Trade-off, stated plainly:** `MIS_CV_Block` and `SPLIT_CV` were the only structures with
an actual IGZO channel present in a MIS capacitor — i.e. the only ones measuring the real
gate-stack C_ox including the channel, not just the isolated dielectric. Removing both means
this reticle no longer has a device-level (channel-present) MIS C-V measurement anywhere.
The new GATE OXIDE 2 TESTS below, like GATE OXIDE 1 TESTS, tests the dielectric alone
(M2/M3, no IGZO) — same as what it replaces functionally (`HFO2_MIM`), not a channel-present
substitute for `MIS_CV_Block`. Flagging this so it's a decision made with the full picture,
not a silent loss.

## What was added: GATE OXIDE 2 TESTS (HfO2)
Built by copying the **actual** geometry of the 6 GATE OXIDE 1 TESTS devices (whatever area
sweep is baked into them is preserved exactly — not re-derived from assumed numbers) and
retyping the electrode stack up one metal level:

| | GATE OXIDE 1 (existing, untouched) | GATE OXIDE 2 (new) |
|---|---|---|
| BE (bottom electrode) | Metal_1 | Metal_2 |
| TE (top electrode) | Metal_2 | Metal_3 |
| Isolation_1 under BE pads | kept — was M1 (etches both dielectrics), now lands on M2 (etches HfO2 only) | kept, same reasoning |
| Isolation_1 under TE pads | present (M2 pad needs it) | **dropped** — M3 pads take Passivation-only per this mask's own pad convention, no contact-etch window |
| Passivation | under both BE and TE | unchanged, under both |

Labels: the 12 "BE"/"TE" per-device labels were duplicated verbatim at the new positions
(same text cells). A fresh title was drawn: `GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)`.
`GATE OXIDE 1 TESTS`'s own geometry and title were not touched (confirmed by XOR-area diff
= 0).

## Placement — real numbers, not the literal "underneath"
Checked before building: `TestStructures` already sits at the very bottom of the die, 43 um
from the nearest alignment-mark keep-out below it. There is **no room** to add a second row
literally underneath GATE OXIDE 1 TESTS anywhere on this die.

Instead, the new row went into the space freed by deleting `MIS_CV_Block` (2272 x 1804 um),
immediately to the right of GATE OXIDE 1 TESTS, same test-structure area. Even that space
wasn't wide enough for a single 6-device row (4120 um needed vs. 2272 um available — a first
attempt at one row landed 382 um into `ResolutionTests`, caught by the overlap check before
shipping), so it's arranged as two stacked 3-device sub-rows instead, still comfortably
inside the freed footprint (largest sub-row width 2020 um vs. 2272 available).

## Verification (`v44_build_log.txt`)
| check | result |
|---|---|
| removed blocks confirmed absent | all 4 |
| new row vs. old Al2O3 row overlap | 0 |
| new row vs. every other TOP block | 0 |
| new row vs. alignment keep-out | 0 |
| GATE OXIDE 1 TESTS geometry unchanged | confirmed (xor area = 0) |
| cells other than `TOP`/`TestStructures` changed | none |
| connectivity / fabricability | 0 findings |
| overlay rules | 8, same pre-existing `MEM_HIGH_VALUE` findings, unchanged |
| structure overlap | 63 um², same pre-existing legacy stray dash near CBKR, unchanged |
| TEXT$ collisions | 0 |
| alignment keep-out violations | 0 |
| DRC 2um TOP | width 25 / space 61 — identical to v42/v43 baseline |
| DRC 2um TestStructures | width 0 / space 0 |
