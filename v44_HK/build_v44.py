"""build_v44.py -- v43 -> v44   (klayout.db only; OASIS + GDS copy)

Two changes per request:

1. REMOVE 4 blocks that duplicate/are superseded by the 'GATE OXIDE 1 TESTS' family
   living inside TestStructures (a 6-device, 4-terminal guard-cross sweep, area varying
   per device -- BE=Metal_1, TE=Metal_2, Al2O3 dielectric):
     - AL2O3_INTEGRITY  (top-level block)  -- simple 2-terminal Al2O3 MIM sweep, same
       purpose as GATE OXIDE 1 TESTS but inferior (no 4-terminal guarding)
     - HFO2_MIM         (top-level block)  -- simple 2-terminal HfO2 MIM sweep
     - MIS_CV_Block      (inside TestStructures) -- 'GUARDED MIS CAPACITORS' combined
       Al2O3+HfO2-in-series MIS stack (M2 absent -> Isolation_1 etches both dielectrics)
     - SPLIT_CV         (top-level block)  -- W=L=400um split MIS capacitor with IGZO

2. ADD 'GATE OXIDE 2 TESTS' (HfO2 version) as a sibling of the existing Al2O3 row,
   built by copying the 6 existing devices' actual geometry (not re-derived from
   assumed numbers, so whatever area sweep is baked into the Al2O3 row is preserved
   exactly) and retyping the electrode metals up one level:
     Metal_1 (BE) -> Metal_2   (was landing on M1 -> etched both dielectrics;
                                 now lands on M2 -> etches HfO2 only. Correct: BE
                                 is now the buried M2/HfO2 interface.)
     Metal_2 (TE) -> Metal_3   (M3 pads take Passivation-only per this mask's own
                                 pad convention -- no Isolation_1 contact window.)
     Isolation_1 -- kept ONLY under the (former M1) BE pads; the windows that sat
                    under the (former M2) TE pads are dropped, since M3 pads never
                    get an Isolation_1 window here.
     Passivation -- kept under both BE and TE pads, unchanged (both still need the
                    final probe opening).
     BE/TE per-device labels -- reused verbatim (same TEXT$109 'BE' / TEXT$110 'TE'
     cells, just placed at the shifted positions); title is freshly drawn.

Placement: the die's structured area already ends ~43um above the alignment-mark
keepout directly below TestStructures -- there is NO room to add a second row
literally underneath (checked, not assumed). Instead the new row goes into the space
freed by deleting MIS_CV_Block, immediately to the right of the Al2O3 row at the same
y-band -- reusing freed floorplan instead of growing the die, which is the actual
'optimize' ask.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'v43_HK'))
import mkaudit

SRC = os.path.join(HERE, '..', 'v43_HK', 'v43_HK.oas')
OUT = os.path.join(HERE, 'v44_HK')
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

print('== 1. removing AL2O3_INTEGRITY, HFO2_MIM, SPLIT_CV (top-level), MIS_CV_Block (in TestStructures)')
removed = []
for k in list(top.each_inst()):
    if k.cell.name in ('AL2O3_INTEGRITY', 'HFO2_MIM', 'SPLIT_CV'):
        removed.append((k.cell.name, k.bbox()))
        top.erase(k)
for k in list(ts.each_inst()):
    if k.cell.name == 'MIS_CV_Block':
        mis_bbox_local = k.bbox()
        removed.append((k.cell.name, mis_bbox_local))
        ts.erase(k)
for nm, b in removed:
    print(f'   removed {nm}  bbox(um) {[round(x*dbu,1) for x in (b.left,b.bottom,b.right,b.top)]}')
assert len(removed) == 4

print('\n== 2. build GATE OXIDE 2 TESTS (HfO2) from the existing 6-device Al2O3 row')
# ---- locate the existing row's geometry (read-only capture) ----
ROW_YLO, ROW_YHI = -1890.0, -1144.0   # device bodies + title, local TestStructures coords
DEV_PITCH = 700.0; DEV_W = 620.0; N_DEV = 6
ROW_X0 = -2134.0   # device 0's BE-left-pad left edge
BE_YMID = -1571.0                       # BE pad y-center (device-local, shared by whole row)
TE_YMID_LIST = [-1801.0, -1341.0]       # TE pad y-centers (bottom, top)
BAND_TOL = 40.0                          # um, band-matching tolerance

src_shapes = {n: [] for n in ('Metal_1', 'Isolation_1', 'Metal_2', 'Passivation')}
for n in src_shapes:
    for s in ts.shapes(L[n]).each():
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        if b.bottom * dbu >= ROW_YLO - 1 and b.top * dbu <= ROW_YHI + 1 and b.left * dbu >= ROW_X0 - 1:
            src_shapes[n].append(s.polygon)
print('   captured', {n: len(v) for n, v in src_shapes.items()}, 'source shapes from the Al2O3 row')

be_labels = [k for k in ts.each_inst() if k.cell.name == 'TEXT$109']
te_labels = [k for k in ts.each_inst() if k.cell.name == 'TEXT$110']
print(f'   {len(be_labels)} BE labels, {len(te_labels)} TE labels found (expect 12 each: 2/device x 6)')
assert len(be_labels) == 12 and len(te_labels) == 12

# ---- the freed MIS_CV_Block space (2272 x 1804 um) is NOT wide enough for a single 4120-um-wide
# 6-device row -- checked, not assumed (a first attempt at a single row put it 2382um past the freed
# area's right edge, into ResolutionTests). Split 3+3 into two sub-rows stacked in the freed space instead.
X0_NEW = 2530.0             # first sub-row device-0 BE-left-pad left edge (102um clear of freed edge 4652)
ROW1_DY = 770.0             # device height 620 + 150 gap between the two sub-rows

def dev_index(xc):
    n = round((xc - (ROW_X0 + DEV_W / 2.0)) / DEV_PITCH)
    return max(0, min(N_DEV - 1, n))

def shape_shift(xc):
    n = dev_index(xc)
    local_n, row = (n, 0) if n < 3 else (n - 3, 1)
    ddx = (X0_NEW - ROW_X0) + (local_n - n) * DEV_PITCH
    ddy = 0.0 if row == 0 else ROW1_DY
    return ddx, ddy

def classify_iso(poly):
    b = poly.bbox(); yc = (b.bottom + b.top) * dbu / 2.0
    if abs(yc - BE_YMID) <= BAND_TOL: return 'BE'
    for tm in TE_YMID_LIST:
        if abs(yc - tm) <= BAND_TOL: return 'TE'
    return '?'

new_m2 = new_m3 = new_iso = new_pass = 0
for p in src_shapes['Metal_1']:
    b = p.bbox(); ddx, ddy = shape_shift((b.left + b.right) * dbu / 2.0)
    ts.shapes(L['Metal_2']).insert(p.transformed(db.Trans(u(ddx), u(ddy)))); new_m2 += 1
for p in src_shapes['Metal_2']:
    b = p.bbox(); ddx, ddy = shape_shift((b.left + b.right) * dbu / 2.0)
    ts.shapes(L['Metal_3']).insert(p.transformed(db.Trans(u(ddx), u(ddy)))); new_m3 += 1
iso_unclassified = 0
for p in src_shapes['Isolation_1']:
    cls = classify_iso(p)
    b = p.bbox(); ddx, ddy = shape_shift((b.left + b.right) * dbu / 2.0)
    if cls == 'BE':
        ts.shapes(L['Isolation_1']).insert(p.transformed(db.Trans(u(ddx), u(ddy)))); new_iso += 1
    elif cls == '?':
        iso_unclassified += 1
for p in src_shapes['Passivation']:
    b = p.bbox(); ddx, ddy = shape_shift((b.left + b.right) * dbu / 2.0)
    ts.shapes(L[PASS]).insert(p.transformed(db.Trans(u(ddx), u(ddy)))); new_pass += 1
print(f'   inserted: Metal_2(BE) {new_m2}, Metal_3(TE) {new_m3}, Isolation_1(BE-only) {new_iso}, Passivation {new_pass}')
print(f'   Isolation_1 shapes dropped as TE-band (no longer needed under M3 pads): {len(src_shapes["Isolation_1"]) - new_iso - iso_unclassified}')
assert iso_unclassified == 0, 'found an Isolation_1 shape that could not be band-classified'
assert new_iso == 12, f'expected 12 BE Isolation_1 windows (2/device x 6), got {new_iso}'

for k in be_labels + te_labels:
    b = k.bbox(); ddx, ddy = shape_shift((b.left + b.right) * dbu / 2.0)
    ts.insert(db.CellInstArray(k.cell_index, k.trans * db.Trans(u(ddx), u(ddy))))
print(f'   duplicated {len(be_labels)} BE + {len(te_labels)} TE per-device labels at new positions')

title_y = ROW_YHI + ROW1_DY + 70.0
txt(ts, 'GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)', X0_NEW, title_y, 24.0)
print('   title drawn: GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)')

exec(open(os.path.join(HERE, 'verify_v44.py'), encoding='utf-8').read())
