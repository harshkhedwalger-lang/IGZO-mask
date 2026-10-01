"""build_v39.py -- v38 -> v39   (klayout.db only; OASIS + GDS copy)

Reorganisation only, no new devices:
  1. Remove FGTFT_L30_W380_N8 (2 copies + heading) from TestStructures. Verified as flat geometry
     confined exactly to local x[2366,4955] y[-1941,-657] inside TestStructures, with nothing else
     of TestStructures' own geometry sharing that region (checked against the full cell footprint
     before deleting) -- a clean, non-straddling cut.
  2. MIS_Capacitors_v2 (the guarded MIS capacitor family from v38) is removed from its old location
     (upper-left of the die) and re-packed narrower to fit inside the space FGTFT vacated, then
     inserted as an actual child instance of TestStructures -- so it is now physically part of the
     same block as TLM, gated vdP/Greek-cross and gate-oxide-1, per "all the test structures in the
     bottom, more organised". The 8 device cells themselves (MISv2_S50_F1 ... MISv2_SHORT_S100) are
     untouched; only their packing/placement changes.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v38_HK', 'v38_HK.oas')
OUT = os.path.join(HERE, 'v39_HK')
MINF = 2.0
ENC = mkaudit.ENC; OVL = mkaudit.OVL
GAP = 80.0

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r)
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500

# ============================================================== 1. remove FGTFT from TestStructures
print('== 1. remove FGTFT_L30_W380_N8 from TestStructures')
ts = ly.cell('TestStructures')
CUT = db.Box(u(2350.0), u(-1950.0), u(4960.0), u(-650.0))
# safety: confirm every non-text shape TestStructures owns either lies fully inside CUT or fully
# outside it -- refuse (assert) if anything straddles the boundary, exactly the same check used for
# the v35 coplanar-TFT removal.
n_removed = 0
for n in LAY:
    for s in list(ts.shapes(L[n]).each()):
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        inside = CUT.contains(db.Point(b.left, b.bottom)) and CUT.contains(db.Point(b.right, b.top))
        overlaps = b.overlaps(CUT) or b.touches(CUT)
        assert inside or not overlaps, f'shape straddles the FGTFT cut boundary on {n}: {b}'
        if inside: ts.shapes(L[n]).erase(s); n_removed += 1
for k in list(ts.each_inst()):
    if k.cell.name.startswith('TEXT') and CUT.contains(k.bbox().p1) and CUT.contains(k.bbox().p2):
        k.delete(); n_removed += 1
print(f'   removed {n_removed} shapes/instances; TestStructures bbox now', ts.bbox())

# ============================================================== 2. relocate MIS_Capacitors_v2 into TestStructures
print('== 2. relocate the MIS capacitor family into the freed area')
DEVICE_NAMES = ['MISv2_S50_F1', 'MISv2_S100_F1', 'MISv2_S100_F4', 'MISv2_S100_F8',
                'MISv2_S200_F1', 'MISv2_S200_F4', 'MISv2_OPEN_S100', 'MISv2_SHORT_S100']
CAPS_CELLS = [ly.cell(n) for n in DEVICE_NAMES]
assert all(c is not None for c in CAPS_CELLS)
old_mis = [k for k in top.each_inst() if k.cell.name == 'MIS_Capacitors_v2'][0]
old_container = old_mis.cell
old_mis.delete()                                                    # drop the old TOP-level placement
ly.delete_cell(old_container.cell_index())                          # its packing container is no longer needed

def block(name, cells, heading, sub, maxw):
    blk = ly.create_cell(name); x = y = 0.0; rowh = 0.0
    for c in cells:
        b = c.bbox(); w, h = b.width() * dbu, b.height() * dbu
        if x > 0 and x + w > maxw: x = 0.0; y -= rowh + GAP; rowh = 0.0
        blk.insert(db.CellInstArray(c.cell_index(), db.Trans(u(x) - b.left, u(y - h) - b.bottom)))
        x += w + GAP; rowh = max(rowh, h)
    txt(blk, heading, 0.0, 60.0, 24.0)
    txt(blk, sub, 0.0, 25.0, 20.0)
    return blk
mis2 = block('MIS_CV_Block', CAPS_CELLS, 'GUARDED MIS CAPACITORS  AREA-PERIMETER SERIES',
             'N=INNER(BE) W=GUARD S=TE', 2550.0)
print('   MIS_CV_Block repacked bbox', mis2.bbox())

# find a placement, anchored near the freed area's lower-left corner, that clears the alignment-mark
# keep-out (a first placement clipped 300 um2 of a pad's corner into the (3000,-7000) cross's zone)
LAY_ALL = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
def flat_here(cell_): return db.Region(cell_.begin_shapes_rec(L['Metal_1'])) if False else None
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
ts_trans = [k for k in top.each_inst() if k.cell.name == 'TestStructures'][0].trans
b = mis2.bbox(); base_dx, base_dy = u(2380.0) - b.left, u(-1930.0) - b.bottom
mis_r = db.Region()
for n in LAY_ALL: mis_r += db.Region(mis2.begin_shapes_rec(L[n]))
mis_r.merge()
placed = False
for dx in range(0, -401, -20):
    for dy in range(0, 401, 20):
        cand = mis_r.transformed(db.Trans(base_dx + u(float(dx)), base_dy + u(float(dy))))
        cand_top = cand.transformed(db.ICplxTrans(ts_trans))
        if cand_top.and_(kz).is_empty():
            ts.insert(db.CellInstArray(mis2.cell_index(), db.Trans(base_dx + u(float(dx)), base_dy + u(float(dy)))))
            print(f'   placed with offset ({dx},{dy}) um from the target corner -- clears the alignment keep-out')
            placed = True; break
    if placed: break
assert placed, 'could not find a placement clear of the alignment-mark keep-out'
print('   placed at (local to TestStructures)', [k for k in ts.each_inst() if k.cell.name == 'MIS_CV_Block'][0].bbox())
print('   TestStructures final bbox', ts.bbox())

exec(open(os.path.join(HERE, 'verify_v39.py'), encoding='utf-8').read())
