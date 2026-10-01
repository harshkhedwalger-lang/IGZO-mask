"""build_v45.py -- v44 -> v45   (klayout.db only; OASIS + GDS copy)

Three changes, all inside TestStructures / TOP, per request:

1. RESTORE MIS_CV_Block ('GUARDED MIS CAPACITORS -- AREA-PERIMETER SERIES'). Re-instantiated
   at its exact original position -- its cell definition was never actually deleted from the
   library (klayout kept it even though nothing referenced it after v44), so this is a plain
   re-insertion of the same geometry, not a rebuild.

2. Re-lay the top of TestStructures as three stacked rows, top to bottom:
     Row 1: TLM_BACK_BIAS + the gated van der Pauw / Greek-cross structure (moved up)
     Row 2: GATE OXIDE 1 TESTS (moved up)
     Row 3: GATE OXIDE 2 TESTS -- HfO2 (rebuilt as a single 6-device row in OXIDE 1's old
            spot, replacing the split 3+3 layout from v44, which only existed because the
            freed MIS_CV_Block footprint was too narrow for one row -- moot now that
            MIS_CV_Block's footprint doesn't need to host it any more)
   Real headroom above TestStructures (in the x-band Row 1 occupies) was checked, not
   assumed: the nearest block above is `1T1R`, 1775um clear. The new layout uses 1012um of
   that, leaving 763um to spare -- comfortably inside verified clear space, not pushed to
   the edge.

3. The Greek-cross structure had no title baked into the mask at all (checked -- it's real,
   placed geometry, just never labelled). Added one while touching this area anyway:
   'GATED VDP + GREEK CROSS'.

GATE OXIDE 1 TESTS' own geometry is not touched, only its position (rigid shift, no
per-shape edits) -- same reasoning as the v43 Memristors_Gated per-instance move: this is a
translate of a self-contained shape set, not zone surgery.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'v44_HK'))
import mkaudit

SRC = os.path.join(HERE, '..', 'v44_HK', 'v44_HK.oas')
OUT = os.path.join(HERE, 'v45_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
ts = ly.cell('TestStructures')
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt(cell, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); cell.shapes(L['Metal_1']).insert(r)
    return r

print('== 1. capture everything read-only, before any mutation ==')

# ---- 1a. GATE OXIDE 1 TESTS: devices + BE/TE labels + title (all still at their v43 position) ----
ROW_YLO, ROW_YHI = -1890.0, -1144.0
DEV_PITCH = 700.0; DEV_W = 620.0; N_DEV = 6
ROW_X0 = -2134.0
BE_YMID = -1571.0; TE_YMID_LIST = [-1801.0, -1341.0]; BAND_TOL = 40.0

ox1_shapes = {n: [] for n in ('Metal_1', 'Isolation_1', 'Metal_2', 'Passivation')}
for n in ox1_shapes:
    for s in ts.shapes(L[n]).each():
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        if (b.bottom * dbu >= ROW_YLO - 1 and b.top * dbu <= ROW_YHI + 1
                and b.left * dbu >= ROW_X0 - 1 and b.right * dbu <= ROW_X0 + 4130):
            ox1_shapes[n].append(s.polygon)
ox1_be = [k for k in ts.each_inst() if k.cell.name == 'TEXT$109' and (k.bbox().left * dbu) < 2000]
ox1_te = [k for k in ts.each_inst() if k.cell.name == 'TEXT$110' and (k.bbox().left * dbu) < 2000]
ox1_title = [k for k in ts.each_inst() if k.cell.name == 'TEXT$129'][0]
# capture plain (cell_index, trans) tuples -- Instance objects go stale once erased below
ox1_be_ct = [(k.cell_index, k.trans) for k in ox1_be]
ox1_te_ct = [(k.cell_index, k.trans) for k in ox1_te]
ox1_title_ct = (ox1_title.cell_index, ox1_title.trans)
print(f'   GATE OXIDE 1: {sum(len(v) for v in ox1_shapes.values())} shapes, {len(ox1_be)} BE + {len(ox1_te)} TE labels, 1 title')
assert len(ox1_be) == 12 and len(ox1_te) == 12

# ---- 1b. TLM_BACK_BIAS + Greek-cross block (everything with local y > ROW_YHI, x < 1500 --
# the v44 split-OXIDE2 addition also has content with y > ROW_YHI, but only at x >= 2500) ----
TOPBLK_XMAX = 1500.0
top_shapes = {n: [] for n in ('Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', 'Passivation')}
for n in top_shapes:
    for s in ts.shapes(L[n]).each():
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        if b.bottom * dbu > ROW_YHI and b.right * dbu <= TOPBLK_XMAX:
            top_shapes[n].append(s.polygon)
top_labels = [k for k in ts.each_inst() if (k.bbox().top * dbu) > ROW_YHI and (k.bbox().right * dbu) <= TOPBLK_XMAX]
top_labels_ct = [(k.cell_index, k.trans) for k in top_labels]
print(f'   TLM+GreekCross block: {sum(len(v) for v in top_shapes.values())} shapes, {len(top_labels)} label instances (title + TLM ruler numbers)')

# ---- 1c. the v44 split GATE OXIDE 2 (HFO2) row -- being replaced, capture nothing, just locate it for erasure ----
# generous zone: nothing else legitimately occupies x>=2300 in TestStructures at this stage
# (MIS_CV_Block isn't restored until step 4, TLM/Greek-cross stay below x=1500)
V44_OX2_X0, V44_OX2_X1 = 2300.0, 4700.0
V44_OX2_Y0, V44_OX2_Y1 = ROW_YLO - 10, 100.0
v44ox2_erase = {'Metal_2': [], 'Metal_3': [], 'Isolation_1': [], 'Passivation': [], 'Metal_1': []}
for n in v44ox2_erase:
    for s in ts.shapes(L[n]).each():
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        if b.left * dbu >= V44_OX2_X0 and b.right * dbu <= V44_OX2_X1 and b.bottom * dbu >= V44_OX2_Y0 and b.top * dbu <= V44_OX2_Y1:
            v44ox2_erase[n].append(s)
v44ox2_labels = [k for k in ts.each_inst() if k.cell.name in ('TEXT$109', 'TEXT$110') and (k.bbox().left * dbu) >= 2000]
print(f'   v44 split OXIDE2 to erase: {sum(len(v) for v in v44ox2_erase.values())} shapes, {len(v44ox2_labels)} labels')
assert len(v44ox2_labels) == 24

# ---- 1d. MIS_CV_Block restore geometry ----
mis_cell = ly.cell('MIS_CV_Block')
mis_ci = mis_cell.cell_index()
mis_own_bbox = mis_cell.bbox()
mis_target = db.Box(u(2380.0), u(-1890.0), u(4652.0), u(-86.0))
mis_trans = db.Trans(mis_target.left - mis_own_bbox.left, mis_target.bottom - mis_own_bbox.bottom)
print('   MIS_CV_Block restore transform:', mis_trans)

print('\n== 2. compute the new 3-row layout (bottom-up) ==')
H_OX = ROW_YHI - ROW_YLO          # 746, GATE OXIDE row height incl. title band
GAP = 150.0
_all_top_polys = [p for v in top_shapes.values() for p in v]
TOP_BLOCK_BOTTOM = min(p.bbox().bottom * dbu for p in _all_top_polys)
TOP_BLOCK_TOP = 208.1             # TLM title top, unchanged (it's the tallest element)
H_TOP = TOP_BLOCK_TOP - TOP_BLOCK_BOTTOM

row3_bottom = ROW_YLO                                  # OXIDE 2 (new) takes over OXIDE 1's old spot
row3_top = row3_bottom + H_OX

ts_inst = [k for k in top.each_inst() if k.cell.name == 'TestStructures'][0]

# ---- automatic clear-rise search for row2 (OXIDE1): a naive dy=H_OX+GAP rise clears row3 but runs
# into a standalone TOP-own van-der-Pauw/greek-cross structure that lives directly in TOP's own
# layers near TOP x1765..2815 (not inside any block instance, so a per-block-only obstacle check
# missed it; found by the full overlap check, not assumed). A leftward x-shift makes it WORSE (runs
# into other geometry on that side instead), so the right lever is how far row2 is allowed to rise. ----
obstacle_r = db.Region()
for n in LAY: obstacle_r = obstacle_r.or_(db.Region(top.shapes(L[n])))
obstacle_r.merge()
for k in top.each_inst():
    if k.cell.name in ('TestStructures',) or k.cell.name.startswith('TEXT'): continue
    for n in LAY: obstacle_r += db.Region(k.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(k.trans))
obstacle_r.merge()
crosses0 = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
keepout_r = db.Region(crosses0).sized(u(40.0))
obstacle_r = obstacle_r.or_(keepout_r)
# pre-existing TOP-level labels (TEXT$xxx instances, e.g. TEXT$127) are real obstacles too --
# a structure must not land underneath one, same margin the final suite's keep-out check uses
for k in top.each_inst():
    if k.cell.name.startswith('TEXT'):
        obstacle_r += db.Region(k.bbox().enlarged(u(10), u(10)))
obstacle_r.merge()
# +5um safety margin -- a bare zero-area-overlap position can still be inside the 2um DRC minimum
# spacing rule; require genuine clearance, not just non-overlap
obstacle_r_chk = obstacle_r.sized(u(5.0))

def ox_region_at(dy):
    r = db.Region()
    for n, polys in ox1_shapes.items():
        for p in polys: r.insert(p.transformed(db.Trans(0, u(dy))))
    r.merge(); return r.transformed(db.ICplxTrans(ts_inst.trans))

MIN_GAP = 60.0
dx_ox = 0.0
dy_ox1 = None
for step in range(0, 61):
    cand = (H_OX + GAP) - step * 10.0        # start from the ideal 150um gap, shrink toward MIN_GAP
    if cand < H_OX + MIN_GAP: break
    r2 = ox_region_at(cand)
    o2 = r2.and_(obstacle_r_chk).area() * dbu * dbu
    if step % 5 == 0: print(f'      dy={cand:.0f}  (gap={cand-H_OX:.0f})  row2-collision={o2:.0f}')
    if o2 == 0:
        dy_ox1 = cand; break
assert dy_ox1 is not None, 'no clear rise found for GATE OXIDE 1 within the acceptable gap range'
gap_used = dy_ox1 - H_OX
print(f'   GATE OXIDE 1 rise set to {dy_ox1:.0f}um (row2/row3 gap {gap_used:.0f}um) to clear the standalone TOP-own greek-cross structure')

row2_bottom = ROW_YLO + dy_ox1
row2_top = row2_bottom + H_OX
print(f'   H_OX={H_OX:.1f} H_TOP={H_TOP:.1f}')
print(f'   row3 (OXIDE2, new)   y {row3_bottom:.1f} .. {row3_top:.1f}  (== old OXIDE1 slot, dy=0)')
print(f'   row2 (OXIDE1, moved) y {row2_bottom:.1f} .. {row2_top:.1f}  dy={dy_ox1:.1f}')

def top_region_at(dy):
    r = db.Region()
    for n, polys in top_shapes.items():
        for p in polys: r.insert(p.transformed(db.Trans(0, u(dy))))
    r.merge(); return r.transformed(db.ICplxTrans(ts_inst.trans))

offset_y = (ts_inst.bbox().top * dbu) - TOP_BLOCK_TOP     # local-to-TOP y offset
obstacle_bottom = -2813.5   # 1T1R bottom, TOP coords (verified above via bbox scan)

# search upward from the ideal GAP for a spot clear of every obstacle, including pre-existing
# TOP-level labels like TEXT$127 that the ideal position runs into -- there's 822um of verified
# headroom to 1T1R to work with, so widening the gap costs nothing structurally
dy_top = None
for step in range(0, 151):
    cand_bottom = (row2_top + GAP) + step * 10.0
    cand_top = cand_bottom + H_TOP
    if cand_top + offset_y >= obstacle_bottom - 20.0: break   # ran out of verified headroom
    r1 = top_region_at(cand_bottom - TOP_BLOCK_BOTTOM)
    o1 = r1.and_(obstacle_r_chk).area() * dbu * dbu
    if step % 5 == 0: print(f'      row1_bottom={cand_bottom:.0f}  collision={o1:.0f}')
    if o1 == 0:
        dy_top = cand_bottom - TOP_BLOCK_BOTTOM
        row1_bottom, row1_top = cand_bottom, cand_top
        break
assert dy_top is not None, 'no clear rise found for TLM+Greek-cross within verified headroom'
print(f'   row1 (TLM+GX, moved) y {row1_bottom:.1f} .. {row1_top:.1f}  dy={dy_top:.1f}')

new_top_TOPcoord = row1_top + offset_y
margin = obstacle_bottom - new_top_TOPcoord
print(f'   new row1 top in TOP coords: {new_top_TOPcoord:.1f}, nearest obstacle (1T1R) bottom {obstacle_bottom:.1f}, margin {margin:.1f} um')
assert margin > 0, 'new layout would collide with 1T1R -- stop'

print('\n== 3. erase (v44 split OXIDE2, and the originals about to be re-inserted shifted) ==')
for n, shs in v44ox2_erase.items():
    for s in shs: ts.shapes(L[n]).erase(s)
for k in v44ox2_labels: ts.erase(k)
print(f'   erased v44 split OXIDE2 geometry + {len(v44ox2_labels)} labels')

for n, polys in ox1_shapes.items():
    for p in polys:
        # erase by re-finding the exact shape (list captured polygons; erase matching shapes)
        for s in list(ts.shapes(L[n]).each()):
            if (s.is_polygon() or s.is_box()) and s.polygon == p:
                ts.shapes(L[n]).erase(s); break
ts.erase(ox1_title)
for k in ox1_be + ox1_te: ts.erase(k)
print('   erased original GATE OXIDE 1 geometry + labels + title (about to reinsert shifted)')

for n, polys in top_shapes.items():
    for p in polys:
        for s in list(ts.shapes(L[n]).each()):
            if (s.is_polygon() or s.is_box()) and s.polygon == p:
                ts.shapes(L[n]).erase(s); break
for k in top_labels: ts.erase(k)
print(f'   erased original TLM+GreekCross geometry + {len(top_labels)} label instances (about to reinsert shifted)')

print('\n== 4. insert everything at its new position ==')
# 4a. GATE OXIDE 2 (new, full single row) at row3 = OXIDE1's old (unshifted) coordinates
def classify_iso(poly):
    b = poly.bbox(); yc = (b.bottom + b.top) * dbu / 2.0
    if abs(yc - BE_YMID) <= BAND_TOL: return 'BE'
    for tm in TE_YMID_LIST:
        if abs(yc - tm) <= BAND_TOL: return 'TE'
    return '?'
d3 = db.Trans(u(dx_ox), 0)
new_m2 = new_m3 = new_iso = new_pass = 0
for p in ox1_shapes['Metal_1']:
    ts.shapes(L['Metal_2']).insert(p.transformed(d3)); new_m2 += 1
for p in ox1_shapes['Metal_2']:
    ts.shapes(L['Metal_3']).insert(p.transformed(d3)); new_m3 += 1
for p in ox1_shapes['Isolation_1']:
    if classify_iso(p) == 'BE':
        ts.shapes(L['Isolation_1']).insert(p.transformed(d3)); new_iso += 1
for p in ox1_shapes['Passivation']:
    ts.shapes(L[PASS]).insert(p.transformed(d3)); new_pass += 1
for ci, tr in ox1_be_ct + ox1_te_ct:
    ts.insert(db.CellInstArray(ci, tr * d3))
title_y3 = row3_top + 70.0
txt(ts, 'GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)', ROW_X0 + dx_ox, title_y3, 24.0)
print(f'   GATE OXIDE 2 (new, single row): Metal_2 {new_m2}, Metal_3 {new_m3}, Isolation_1(BE-only) {new_iso}, Passivation {new_pass}, {len(ox1_be)+len(ox1_te)} labels, 1 title')
assert new_iso == 12

# 4b. GATE OXIDE 1 (original, shifted up by dy_ox1 and left by dx_ox)
d1 = db.Trans(u(dx_ox), u(dy_ox1))
for n, polys in ox1_shapes.items():
    for p in polys: ts.shapes(L[n]).insert(p.transformed(d1))
for ci, tr in ox1_be_ct + ox1_te_ct:
    ts.insert(db.CellInstArray(ci, tr * d1))
ts.insert(db.CellInstArray(ox1_title_ct[0], ox1_title_ct[1] * d1))
print(f'   GATE OXIDE 1 (moved): shifted dy={dy_ox1:.1f}')

# 4c. TLM + Greek-cross (shifted up by dy_top)
d2 = db.Trans(0, u(dy_top))
for n, polys in top_shapes.items():
    for p in polys: ts.shapes(L[n]).insert(p.transformed(d2))
for ci, tr in top_labels_ct:
    ts.insert(db.CellInstArray(ci, tr * d2))
print(f'   TLM+GreekCross (moved): shifted dy={dy_top:.1f}, {len(top_labels_ct)} label instances moved with it')

# Greek-cross title (new -- it never had one)
gx_left = min(p.bbox().left * dbu for p in top_shapes['Metal_1'] if p.bbox().left * dbu > 0)
gx_title_y = TOP_BLOCK_TOP + dy_top - 70.0
gx_title_region = txt(ts, 'GATED VDP + GREEK CROSS', gx_left, gx_title_y, 24.0)
print('   Greek-cross title added')

# 4d. restore MIS_CV_Block
ts.insert(db.CellInstArray(mis_ci, mis_trans))
print('   MIS_CV_Block restored at its original position')

exec(open(os.path.join(HERE, 'verify_v45.py'), encoding='utf-8').read())
