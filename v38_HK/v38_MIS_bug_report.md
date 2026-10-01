# v38_HK — MIS capacitor rebuild: bugs found, fixes, and the science behind the new design

## Bugs found in the existing `MIS_Capacitors` (numbers, not adjectives)

**Bug 1 — `MIScap_BEdef_50/100/200`: area was not defined by a single lithographic edge.**
Checked directly on the real geometry: `M1 fully inside IGZO` = **False**, `IGZO fully inside M3` = **False**, for all three sizes. The measured "capacitor area" was the *accidental intersection* of the M1 lead's edge and the M3 (TE) plate's edge — e.g. for the nominal "100": M1 right edge at x=-6450, IGZO left/right at -6570/-6430, TE left edge at -6560. None of the three layers cleanly contains another; the true overlap (110×100 µm, not 100×100) is set by wherever M1's edge happens to land relative to TE's edge. That is exactly the alignment-sensitive area your own single-edge principle exists to prevent — except here it's not one alignment step but two (M1-to-M3 *and* M1/M3-to-IGZO) both contributing uncontrolled error to the number you'd use for C_ox.

**Bug 2 — `MIScap_comb_N6` / `MIScap_comb_N10` are not combs.**
Checked directly: each is **one solid M1 polygon** (`region.count() == 1`), not interdigitated fingers. The area/perimeter fringe-capacitance separation method (Area–Perimeter Fig. 5, ResearchGate 324514056) these were named for cannot be performed with them — there is no perimeter variation at all beyond ordinary corner effects.

**Bug 3 — `MIScap_open_100` had a spurious 30 µm² real M1/IGZO/M3 overlap.** Should be exactly 0 for a clean OPEN de-embedding reference; a rounding/corner artifact in the original layout, not deliberate.

**Not a bug (verified, kept as the template):** `MIScap_guarded_100` — real, measured 15 µm M1-to-M1 gap between guard and inner plate, genuinely isolated nets. This is the one device in the old set built the way the literature describes, and the new family generalises it.

## Design principles used in the rebuild (with sources)

1. **True guard ring**, M1, surrounding the inner (BE) electrode, own separate pad — not tied to the inner electrode on-chip. The guard is held at the *same* potential as the inner electrode by the measurement instrument (LCR/guard terminal), so the field between them is zero and edge/fringe leakage from the inner electrode's true boundary is collected by the guard's own lead instead of contaminating the measured signal (Nicollian & Brews guard-ring method, the standard reference for MOS-C leakage/edge isolation).
2. **Guard gap = 10 µm**, verified by measurement on every device (not asserted from the constant) — over 3× the mask's own enclosure margin (ENC = 3 µm), small enough that the un-guarded region at the inner electrode's true edge is negligible relative to the plate size, large enough to have zero realistic short risk.
3. **Guard ring sits fully under the same IGZO/M3 stack** as the electrode it protects (ring outer edge + 20 µm ≤ IGZO half-side, verified). A guard ring outside the dielectric/semiconductor film doesn't intercept the same fringing field it's meant to guard against.
4. **Single-edge area definition, verified per device from real geometry, not from nominal parameters:** inner M1 ⊂ IGZO ⊂ M3, each with ≥20 µm margin (≫ ENC). `S50_F1` measured 2500.0 µm² exactly (50×50, zero corner loss); the comb devices measure whatever their finger geometry actually integrates to (6228.7, 5893.4, 23885.4 µm²) — read from the polygon, never hand-calculated, so there's no separate arithmetic bug to also get wrong.
5. **Area/perimeter series for fringe-capacitance separation** (Area × Perimeter table below): 6 devices spanning both S (50/100/200) and finger count (1/4/8), giving well-conditioned (Area, Perimeter) pairs for the two-parameter fit `C_meas = c_area·A + c_perim·P` — verified by checking that no two data points are collinear (worst-case 2×2 determinant across all pairs = 42922, far from singular).
6. **OPEN and SHORT de-embedding at the S100 reference geometry**, same guard ring and pad environment as the real devices. OPEN: pads + guard only, IGZO omitted entirely (0 µm² unintended overlap, unlike the old design's 30 µm²) — measures pad/guard/lead parasitic capacitance. SHORT: identical, plus the inner-M1 lead bonded straight to M3 through an Isolation_1 window, dielectric bypassed — measures series R and lead inductance in the "on" state, and is the on-chip proxy for the Nicollian-Brews strong-accumulation R_s correction used in D_it extraction.
7. **Multi-finger comb at S100/S200 also serves the mobility side of the mask**: admittance measurements on multi-finger MOS structures are the published way to extract trap density while minimizing the impact of sheet resistance (ScienceDirect 038110124000157) — the same finger geometry that gives you a perimeter data point for C_ox extraction also gives you a low-R_sh structure for D_it.

## (Area, Perimeter) table — real geometry, for the two-parameter regression

| device | Area (µm²) | Perimeter (µm) |
|---|---|---|
| S50 F1 | 2500.0 | 200.0 |
| S100 F1 | 10000.0 | 400.0 |
| S100 F4 | 6228.7 | 928.0 |
| S100 F8 | 5893.4 | 1632.0 |
| S200 F1 | 40000.0 | 800.0 |
| S200 F4 | 23885.4 | 1928.0 |

Fit `C_meas(S,n) = c_area·A(S,n) + c_perim·P(S,n)` across these 6 points to get C_ox = c_area (used for every mobility number elsewhere in the mask) with the perimeter/fringe term removed, and c_perim itself as a design-rule sanity check (should match the ~fF/µm fringe estimate from the dielectric stack thickness).

## Verification (`v38_build_log.txt`)
| check | result |
|---|---|
| connectivity / fabricability | **0 findings** (the old set's 4 pre-existing `MIS OPEN` floating-M1 findings are gone — the new OPEN references are supposed to be isolated by design and no longer trip the rule, since they carry their own proper pad/window on every net) |
| overlay rules | 8, all pre-existing `MEM_HIGH_VALUE` (unrelated, unchanged) |
| net extraction, 6 guarded caps | 3 nets / 3 pads each (inner, guard, TE) — 0 mismatches |
| net extraction, OPEN | 3 isolated nets, 1 pad each — confirms zero unintended connectivity |
| net extraction, SHORT | inner+TE merged into 1 net (2 pads), guard isolated (1 pad) — confirms the bond works and nothing else shorts |
| guard-ring real gap | 10.0 µm on **every** device, measured, not assumed |
| single-edge containment | inner ⊂ IGZO ⊂ M3, **True** on all 6 caps |
| structure overlap | 63 µm², the same pre-existing legacy stray dash near CBKR |
| block clearance to neighbours | ≥ 80 µm |
| label collisions | 0 |
| DRC 2 µm | `MIS_Capacitors_v2`: 0 width / 0 space |
| existing cells changed | none (`TOP` only) |

Two bugs I introduced and caught before shipping, for the record: the first SHORT design routed the inner and TE leads to opposite sides of the device with no shared geometry, so the intended M1–M3 bond never actually touched M3 (net check caught it: 3 isolated nets instead of 2). After rerouting both leads through the centre, the bond window then violated my own 3 µm enclosure margin because the two leads meet along a single zero-width line, not an area (overlay check caught it). Both fixed and reverified before this was written up.

## Old cell
`MIS_Capacitors` (the buggy version) is still in the file, **unplaced**, for reference/diff — not deleted, not on the reticle.
