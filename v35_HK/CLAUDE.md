# CLAUDE.md — IGZO TFT / HfO₂ RRAM test reticle (HK mask series)

Context for Claude Code. Read this whole file before touching any mask file.
Owner: Harsh (semiconductor researcher). Style: terse, direct. Wants correct-first-time,
no repeated mistakes, no filler structures, and nothing changed that wasn't asked for.

---

## 0. Hard rules (violating any of these has cost whole versions before)

1. **Use `klayout.db` (pip `klayout`) only. NEVER `gdstk`.** gdstk mis-decodes the OASIS
   repetition records in these files and silently merges arrayed pads into phantom polygons.
2. **Always write OASIS (`.oas`)** — it keeps layer names. GDS drops them. A `.gds` copy may be
   written in addition, never instead.
3. **The uploaded source file is ground truth.** Modify only what the request names. Do not
   "clean up", re-space, re-flatten or re-label anything else.
4. **Never delete or move** original alignment marks, litho/vernier artwork, headings, or the flat
   geometry that lives directly in `TOP`. (v25–v27 broke this in a "cleanup" pass and had to be
   rebuilt from `v22_HK__1_.oas`.)
5. **Spacing edits are X-only unless Y is explicitly requested.** Labels stay put unless asked.
6. **2 µm minimum width and space on every layer** (laser direct-write limit).
7. **Every probed node gets a standard manual pad** (§3). No needle-card rows, no pad arrays.
8. **No text overlapping any structure**, and no text-on-text.
9. **Run the full verification suite (§6) before calling anything deliverable.** Geometric DRC
   alone is NOT sufficient — the connectivity audit is mandatory.
10. **Keep the generator script** (`build_vNN.py`) next to every output so the mask can be
    regenerated after editing a string or dimension.
11. Ask before guessing on anything process-related. A wrong assumption about the stack has
    previously made every bottom-gate TFT on the reticle a gate–S/D short.

---

## 1. Files

| file | role |
|---|---|
| `v22_HK__1_.oas` | **Primary ground truth** for original alignment marks, headings, TOP-level geometry and block positions |
| `v17_HK`, `v28_HK` | Topology references (e.g. gated TLM shared ladder) |
| `v35_HK.oas` + `build_v35.py`, `mkaudit.py`, `verify_v35.py` | **Current version.** `mkaudit.py` = fabricability audit + overlay-enclosure rules (OVL/ENC); `build_v35.py` reads `v34_HK/v34_HK.oas` |
| `v34_HK/` | Previous version (alignment text restored to v22, labels repaired, STEP_COVERAGE serpentine) |
| `V18_HM_memristor_mask` | Separate sister mask (see §9) — do not mix conventions blindly |

Status at hand-off (v35): mask is now a **6-layer process**; all coplanar and top-gate devices and
Metal_4 are gone; 1T1R W/L sweeps and HfO₂ TDDB arrays added; a reserved free area is left in the
top-right (see `RESERVED_AREA` cell). Open: owner has not yet given the measured layer-to-layer
overlay (mkaudit assumes OVL 2 µm / ENC 3 µm), nor decided on the stray "20"+dashes in TOP near
CBKR, the 80 µm pads in `Memristors_Gated`, or the 6.5 µm CBKR/1T1R gap. Restore positions by
diffing against `v22_HK.oas`, not by eye.

---

## 2. Process stack, layer map, and the flow that matters

### Layer map (names are stored in the OAS; look layers up by NAME)

| layer | name | physical meaning | drawn polarity |
|---|---|---|---|
| 0/0 | Alignment | field frame / alignment | — |
| 1/0 | Metal_1 | bottom gate / bottom plate / BE | metal (lift-off) |
| 2/0 | Isolation_1 | **combined contact etch** through HfO₂ (and Al₂O₃#1 where over M1) | openings |
| 3/0 | Metal_2 | RRAM bottom electrode, routing (no coplanar TFTs any more) | metal (lift-off) |
| 4/0 | IGZO | channel / switching film | film (lift-off, NOT blanket) |
| 5/0 | Metal_3 | top S/D, top electrode, pad caps | metal (lift-off) |
| 6/0 | **Passivation** (was Isolation_2) | Al₂O₃#2 passivation, **openings** over probe pads | openings |
| ~~7/0~~ | ~~Metal_4~~ | **removed in v35** | — |
| 63/0 | (unnamed) | vernier / CD / resolution artwork | — |

v35 has exactly 6 process layers (1–6). Nothing in the mask may use a top gate, M4 or a coplanar
(M2 S/D under IGZO) transistor. Pad rule (§3) is unchanged; a probe window over M1/M2 is valid if an
Iso1 window sits under it (direct exposure) **or** an M3 cap covers it (mkaudit checks either).

Text in the HK mask is drawn as **polygons on Metal_1** (earlier requirement: text on layer 1),
body 24 µm, headings 36 µm. Previous sessions used a local helper `glmfont.text_region(...)`
(BODY scale 1.5, HEAD 2.5). If it is not available, use
`db.TextGenerator.default_generator().text(s, dbu, mag)` and size to 24/36 µm cap height.
Confirm with the owner if unsure which layer text belongs on.

Legacy note: very early files described 2 = "V1 via", 6 = "V2". The current meaning is the table above.

### Process flow (current, since v17)

```
M1 → ALD Al₂O₃#1 (~20 nm) → M2 → ALD HfO₂ → [2/0 Isolation_1 contact etch] → IGZO (lift-off)
   → M3 → Al₂O₃#2 (passivation) → [6/0 Passivation open over pads]        (v35: no M4)
```

Old flow had the 2/0 etch *before* M2. Moving it after M2 has these consequences — design
every new structure around them:

- **M2 cannot contact M1 anywhere.** Al₂O₃#1 is unbroken under M2.
- **Every M1 contact is made by M3**, through a 2/0 window that is **clear of M2**
  (M2 masks the etch).
- A 2/0 window over M1 opens **both** HfO₂ and Al₂O₃#1. So **a 2/0 window must never touch M1
  and M2 at the same time** — that is a hard M1–M2 short. (This bug existed in every
  series-resistor memristor until v33.)
- **Any pad on M1 or M2 must be capped by M3** through a 2/0 window, else it stays buried under
  HfO₂ + Al₂O₃#2 and cannot be probed.
- Al₂O₃#1 was deliberately kept (two dielectrics) because without it M1/M2 overlaps become
  shorts (141 regions, including the gate–S/D overlap of every bottom-gate TFT).
- v17 decision for 2/0 over M2: "all of M2 minus a 2.5 µm perimeter seal". **Verify against the
  current file** before assuming this still holds everywhere — where HfO₂ must stay on M2
  (e.g. HfO₂ switching junctions), 2/0 must NOT open. Ask if a new structure is ambiguous.

---

## 3. Standard building blocks

### Probe pad (hard constraint)
- Manual four-sided local probing, pads on **N/S/E/W** of the device.
- Metal **160 × 160 µm**, window **150 × 150 µm** (5 µm inset), **75 µm taper** into the lead.
- Pad recipe by layer:
  - M1 or M2 pad → metal pad + 2/0 window + **M3 cap 160×160** + 6/0 window
  - M3 pad → M3 pad + 6/0 window
- Leads ~30 µm wide, necking to device width only at the junction.

Reference implementation (from `build_v33.py`):
```python
PAD, PW = 160.0, 150.0
def win(c,x,y,l): d=(PAD-PW)/2; bx(c,l,x+d,y+d,x+PAD-d,y+PAD-d)
def ppad(c,x,y,met):
    bx(c,met,x,y,x+PAD,y+PAD)
    if met in ('Metal_1','Metal_2'):
        win(c,x,y,'Isolation_1'); bx(c,'Metal_3',x,y,x+PAD,y+PAD)
    win(c,x,y,'Isolation_2')
```

### Design principles
- **Single-edge area definition**: the smallest layer defines device area, so misalignment of
  other layers doesn't change it. Apply to every capacitor, junction and memristor.
- **Gate–S/D overlap 5 µm** on TFTs (and check it doesn't short short-L devices).
- Gate plates must stop ≥ 6 µm short of any 2/0 contact window over M2; bring the gate lead out
  away from S/D pads.
- IGZO must stay inside its intended neck; IGZO spilling under pads creates parasitic paths
  (series resistor length capped at 140 µm for this reason).
- Memristor block column pitch 680 µm (v33).

---

## 4. Device physics rules that decide what is worth drawing

- **Ungated IGZO structures are useless** (TLM, Greek cross/vdP, CBKR): IGZO is too resistive at
  zero bias. Only bottom-gated versions. Ungated CBKR was removed for this reason.
- **Pad-open leakage structures on an insulating substrate are non-functional** — excluded.
- **Gated TLM = shared nine-contact ladder** (one gated channel, 9 contacts, 8 gaps,
  d = 2,3,4,6,8,12,16,24 µm, W = 20 µm, contact pads 240 µm pitch, gate on its own pad), as in
  v17/v28. Not discrete two-contact cells (they add cell-to-cell scatter to the R–d fit).
  Use **4-wire** to remove probe resistance from the 2R_c intercept.
- Contact resistance in staggered TFTs comes from vertical access through un-accumulated IGZO;
  separate it from material mobility with TLM (R_total·W vs L at fixed V_ov).
- µ_FE vs V_G shape distinguishes percolation-limited, series-R-limited and trap-limited regimes.
- **GVM ring memristors switch laterally**, not vertically. True-vertical devices (GVMV) need
  separate peripheral gating.
- MIS structure = BE / Al₂O₃ / IGZO / TE with IGZO patterned by lift-off; BE probed directly on M1
  through a 2/0 opening.
- Split-CV needs S and D tied together (in M3) with a capped gate pad.
- Broader research goal: lateral CF₄ plasma partitioning of a single IGZO film for monolithic
  1T1R. CF₄ layer (8/0) was proposed then removed from the HK mask — don't re-add unasked.

---

## 5. Current structure inventory (cell names)

TFT / transport: `Transistors_BottomGate` (**staggered rows only**), `TFT_Lsweep_W50`, `TFT_Wsweep_L10`,
`gated_TLM`, `gated_vanderPauw`, `gated_4probe_TFT`, gated CBKR block, TLM back-bias, FGTFT.
1T1R: `1T1R` (W500 L20, J = 2/4/5/8/10), **`1T1R_WSWEEP`** (W = 100/50/20/10, L20, J = 2/4/10),
**`1T1R_LSWEEP`** (L = 10/5/40, W100, J = 2/10). Generator `t1r(c,X0,Y0,W,L,s)` in `build_v35.py`
reproduces the original 1T1R device exactly (self-check XOR = 0 µm²).
Reliability: `AL2O3_INTEGRITY`, GATE OXIDE 1 tests (Al₂O₃#1 TDDB), **`HFO2_TDDB`** (A: 20 × 10×10 µm,
B: 10 × 30×30 µm, common M2 bus, cross-point caps → overlay-independent area, TE pad per cap).
**`RESERVED_AREA`**: 2340 × 1709 µm kept empty for future structures (label only).

Capacitors / dielectrics: `MIS_caps_M1_IGZO`, `MIScap_BEdef_100`, `MIScap_short_100`,
`AL2O3_INTEGRITY`, `HFO2_MIM`, `SPLIT_CV`.

Memristors: `Memristors`, `Memristors_individual`, GVM / GVMV blocks (the old `w` parameter
produced **half** the intended geometry — names were corrected), `GVM_ring_*`,
`GLM_2um_block` (gated lateral memristors), `MEM_STACK_SPLIT` (IGZO-only and HfO₂-only stacks),
`MEM_ASYM` (asymmetric junction + reservoir sweeps), `MEM_HIGH_VALUE` (series-resistor
L = 30/60/100/140 µm; guarded vs bare), `MEM_REDUNDANT`, anti-serial CRS pair, `XBAR_4X4`.

Process monitors: `STEP_COVERAGE` (M3 over M1 steps, 4-wire, with flat reference), litho/vernier
artwork (63/0), alignment (0/0). Text cells are named `TEXT*`.

Removed on purpose (do not bring back): ungated TLM/vdP/CBKR, pad-open leakage, layer ladder
("filler"), CF₄ structures, **coplanar TFTs, top-gate TFTs, dual-gate TFTs, GATE OXIDE 2 tests,
Metal_4, L7 legend row** (v35).

---

## 6. Verification — run all of this on every output

1. **Connectivity / fabricability audit** (`mkaudit.Audit.connectivity`, run on **every** block cell,
   text cells excluded). Rules:
   1. every 2/0 and 6/0 window lands on metal or IGZO
   2. a 6/0 probe window over M1/M2 must be ≥ 80 % covered by an Iso1 window (direct exposure) or an M3 cap
   3. a 2/0 window touching both M1 and M2 → **short**
   4. an IGZO island with no M3 and no 2/0 window → dead film (this is how the coplanar TFTs were found non-functional)
   5. a metal island (>400 µm², not a text glyph) with no window and no IGZO contact → floating
   Must return 0 findings except the documented exemptions (MIS OPEN reference plates).
   **Overlay rules** (`Audit.overlay`, parameters `OVL`=2 µm, `ENC`=3 µm — set to the measured overlay):
   O1 Iso1 window inside the M1/M2 it lands on by ≥ ENC; O2 M3 cap encloses its Iso1 window by ≥ ENC;
   O3 passivation window inside its pad metal by ≥ ENC and still covered by the Iso1 window after an OVL shift.
   Junction windows of IGZO-only stacks are enlarged in M2/M3/IGZO (`patch_cell`); series-resistor end
   windows (`MEM_HIGH_VALUE`) stay at 1 µm end enclosure by design (length set by the M2 gap).
2. **Net extraction**: connected-component count per structure matches the intended terminal
   count; each terminal reaches exactly one pad.
3. **Structure overlap**: flatten each TOP instance on all device layers and AND pairwise, plus
   against TOP-own shapes → must be 0 µm².
4. **Text overlap**: no text polygon touches any structure or other text.
5. **DRC 2 µm** width and space per merged layer (projection metric; ignore corner hits below
   2/√2 and intentional sub-resolution rungs in litho artwork):
   ```python
   P=db.Region.Projection; lim=2.0/math.sqrt(2)-.001
   r.width_check(u(2.0),False,P,None,None,None)   # filter .05 < d < lim
   r.space_check(u(2.0),False,P,None,None,None)
   ```
6. **Preservation diff vs source**: alignment layer, 63/0 artwork, headings and TOP-own geometry
   identical to the source unless the request said to change them. Report any diff.
7. **Render a PNG** of changed blocks (matplotlib, per-layer colours) and look at it.

Deliver: `vNN_HK.oas` (+ `.gds`), `build_vNN.py`, audit/change report `.md`, preview PNG.
Report numbers (defects before/after, overlap µm², DRC counts), not adjectives.

---

## 7. Useful klayout.db skeleton

```python
import klayout.db as db, math
ly=db.Layout(); ly.read(SRC); dbu=ly.dbu
u=lambda x:int(round(x/dbu))
L={(ly.get_info(l).name or '63'):l for l in ly.layer_indexes()}
top=ly.cell('TOP')
def R(c,n,rec=True):
    r=db.Region(c.begin_shapes_rec(L[n])) if rec else db.Region(c.shapes(L[n])); r.merge(); return r
def bx(c,l,x0,y0,x1,y1): c.shapes(L[l]).insert(db.Box(u(x0),u(y0),u(x1),u(y1)))
ly.write(OUT+'.oas')
```

---

## 8. Roadmap — high-value additions (owner-approved direction, ranked)

Already identified as missing:
- **Channel-length ladder** L = 2–100 µm at fixed W (contact- vs material-limited mobility).

P1
- **HfO₂ TDDB/Weibull array**: ≥ 20 identical 10×10 µm caps (forming = soft breakdown; compare
  breakdown-field Weibull with forming-voltage distribution).
- **Isolation_2 (Al₂O₃#2) capacitor sweep** M3/Al₂O₃#2/M4, 20/50/100/200/500 µm + TDDB array —
  this film currently has **zero** structures.
- **NBIS pair**: identical TFTs, one with M4 light shield over channel.
- **Heater + 4-wire RTD** next to a memristor and a TFT (true junction temperature, activation energy).
- **Gated Hall bar** (carrier density vs Hall mobility vs V_G).
- **Al₂O₃#1 TDDB array**.

P2
- Caps on flat M1 vs M1 comb (same area, ~50× edge) → ALD step coverage vs intrinsic breakdown.
- Large-area HfO₂ caps with/without IGZO at matched area.
- CBKR with end contact → transfer length L_T.
- Dual-gate TFT, independent gates, L sweep → both C_ox and which interface limits SS.
- 1T1R with transistor W = 10/20/50/100 µm (programmable compliance, LRS vs I_comp).
- GSG pad triplet on 3–4 memristors for pulsed switching speed.

P3
- Gate-line RC meander (2/5/10 mm); cross-bridge CD on M1 and M4; M4 sheet resistance;
  M1–M2 overlap-capacitance ladder (5–100 µm); IGZO W sweep at fixed L (edge conduction);
  mesa isolation pair.

Every addition must: use standard pads, pass the audit, have single-edge area definition, and
state its physical motivation in the change report.

---

## 9. Sister mask (HM series) — different stack, don't cross-apply blindly

`V18_HM_memristor_mask`: 4-layer memristor mask, M1 (1) / ~2 nm HfO₂ opened by etch (6) /
IGZO (4) / M3 (5); layers 0/1/4/5/6 only; no layer-63 text; editable sample/project name cells;
litho test structures grouped inside the alignment-cross perimeter; rows named by mask step
(L1–L4) not GDS layer. Laser direct-write aligns to M1 crosses, so per-plate concentric boxes
were removed there. (That mask was built with gdstk before the gdstk bug was found — use klayout
for any further work on it too.)

---

## 10. Working with the owner

- Short, direct replies; numbers over prose; end with a short "key takeaways" list.
- Ask one precise question when the process is ambiguous instead of guessing.
- Show what changed vs source and prove nothing else changed.
- Physically motivated structures only; he will reject filler.
