"""build_v41.py -- v40 -> v41   (klayout.db only; OASIS + GDS copy)

Corrects the HfO2-only-dielectric TFT process split's gate metal from Metal_1 to Metal_2, per the owner's
own read of the stack:

    M1 -> Al2O3#1 -> M2 -> HfO2 -> [Isolation_1 contact etch] -> IGZO -> M3 -> Passivation

The v36 version of this block used M1 for the gate -- geometrically identical to the standard TFT, which
I flagged at the time as unbuildable on the same wafer (Al2O3#1 is a blanket ALD film under M1's own gate
stack; there's no way to remove it under one M1-gated device while keeping it under another on one wafer).

Putting the gate on **Metal_2** instead solves this with zero process change: M2's OWN gate dielectric,
going up toward the channel, is HfO2 only -- Al2O3#1 sits BELOW M2 (between M1 and M2), not between M2
and the channel. A real, single-edge HfO2-only-dielectric TFT, buildable on the exact same wafer as every
other structure on this reticle, using layers that already exist.

Implementation: every Metal_1 shape in Transistors_BottomGate_HfO2Only that isn't a text glyph (the gate
pad + lead + plate of all 12 devices -- channel length, width, IGZO and Metal_3 S/D geometry are untouched)
is moved from layer 1/0 (Metal_1) to layer 3/0 (Metal_2). The pad recipe (Isolation_1 window + Metal_3
cap + Passivation window) already treats M1 and M2 identically, so no other shape needs to change --
the SAME Isolation_1 window that used to open both Al2O3 and HfO2 over an M1 pad now opens only HfO2
over the M2 pad, which is exactly the physics this block exists to test.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v40_HK', 'v40_HK.oas')
OUT = os.path.join(HERE, 'v41_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500

print('== retype the gate: Metal_1 -> Metal_2, Transistors_BottomGate_HfO2Only')
c = ly.cell('Transistors_BottomGate_HfO2Only')
old_m2 = sum(1 for _ in c.shapes(L['Metal_2']).each())
assert old_m2 == 0, 'cell already has Metal_2 content -- would corrupt an existing layer, aborting'
gate_polys = []
for s in list(c.shapes(L['Metal_1']).each()):
    if not (s.is_polygon() or s.is_box()): continue
    if isglyph(s.polygon): continue
    gate_polys.append(s.polygon)
    c.shapes(L['Metal_1']).erase(s)
for p in gate_polys: c.shapes(L['Metal_2']).insert(p)
print(f'   {len(gate_polys)} gate shapes moved Metal_1 -> Metal_2')
remaining_m1 = sum(1 for _ in c.shapes(L['Metal_1']).each())
print(f'   Metal_1 shapes remaining in cell (should be only the 12 heading/label glyphs): {remaining_m1}')

# ---------------------------------------------------------------- fix the heading (old wording implied
# a same-wafer M1 trick; the real story is a different gate metal, not "no Al2O3 anywhere")
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt_region(s, cap): return tg.text(s, dbu, cap * MAG1)
old_heading_text = None
# the heading is ALL own-M1 glyphs sharing its Y-band -- a first attempt grabbed only the single widest
# word-cluster (20 um dilation wasn't enough to bridge every inter-word gap at this cap height, so the
# one heading line split into 3 separate clusters) and left the other two glyph clusters behind as a
# stale, now-incorrect "(PROCESS SPLIT, NO AL2O3)" fragment in the rendered output. Selecting by Y-band
# instead of by cluster catches the whole line regardless of how many pieces it merges into.
glyphs = [s for s in c.shapes(L['Metal_1']).each() if s.is_polygon() and isglyph(s.polygon)]
# Metal_1's own shapes are now ALL text (every real gate shape was just retyped to Metal_2), so using it
# here would include the heading itself in "body top", making bottom > body_top0 false for the heading
# and erasing nothing -- exclude Metal_1, use only layers that are unambiguously real device geometry.
body_top0 = max(s.bbox().top for n in LAY if n != 'Metal_1' for s in c.shapes(L[n]).each())
# not a fixed +-3 um tolerance (punctuation -- hyphens, commas -- sits at a different baseline than
# letters and slipped through that on the first pass, leaving stray "-" and "," fragments in the
# render): anything above the real device body is the heading, full stop, regardless of exact height.
to_erase = [s for s in glyphs if s.polygon.bbox().bottom > body_top0]
hb = db.Box()
for s in to_erase: hb += s.polygon.bbox()
print(f'   old heading bbox {hb.left*dbu:.0f},{hb.bottom*dbu:.0f},{hb.right*dbu:.0f},{hb.top*dbu:.0f}  ({len(to_erase)} glyphs)')
for s in to_erase: c.shapes(L['Metal_1']).erase(s)
new_heading = 'TFT BOTTOM GATE STAGGERED - GATE = M2, HFO2 ONLY (AL2O3 BELOW M2, SAME WAFER)'
# place from the cell's OWN current geometry extent (not the old heading's bbox): the new wording is
# longer than the old one, so reusing the old position risks running into the device row below it if
# the extra length isn't accounted for -- the earlier version of this fix did exactly that and clipped
# the topmost device by <10 um, caught by the label-clearance check before shipping.
# cell.bbox() (recursive) after the heading glyphs are erased -- own-shape-only scans (used for the
# erase-selection above) miss the per-device "L150_W500" column labels, which are CHILD TEXT$ instances,
# not own shapes; those sit above the device rows and the first placement attempt landed the new heading
# right on top of them.
body_top = c.bbox().top   # DB units
r = txt_region(new_heading, 36.0).moved(hb.left, body_top + u(40.0))
c.shapes(L['Metal_1']).insert(r)
print('   new heading:', new_heading, '  placed at y >=', round((body_top + u(40.0)) * dbu), 'body top was', round(body_top * dbu))

exec(open(os.path.join(HERE, 'verify_v41.py'), encoding='utf-8').read())
