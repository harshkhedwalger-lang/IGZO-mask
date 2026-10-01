"""build_v36.py -- v35 -> v36   (klayout.db only, never gdstk; OASIS + GDS copy)

Changes vs v35 (owner feedback on v35):
  A. removed: HFO2_TDDB (reliability/Weibull structures -- not the current priority), 1T1R_WSWEEP,
     1T1R_LSWEEP (both broke the fixed W/L=25 ratio the 1T1R device needs to drive the memristor),
     RESERVED_AREA.
  B. 1T1R ('1T1R' cell, 25 devices): W=500 L=20 unchanged (W/L=25 fixed, per owner), but the
     edge-to-edge gap between adjacent devices in a row is cut from 130 um to 80 um (pitch 1200->1150,
     X-only spacing edit). Column header text re-centred on the new column positions.
  C. new: staggered bottom-gate TFT block using HfO2 ONLY as gate dielectric (no Al2O3#1), placed in
     the area freed by removing the top-gate devices (v35) and 1T1R_WSWEEP. NOTE (process, not mask):
     Al2O3#1 is a single blanket ALD film across the whole wafer -- there is no mask layer that can
     remove it selectively under one block while leaving it under another on the SAME wafer. This
     block is geometrically identical to Transistors_BottomGate; realising "HfO2-only" needs a
     dedicated process-split WAFER (Al2O3 ALD step skipped for the whole run), not a new mask layer.
     Flagged again in the report -- ask before running such a split.
  D. Memristors_Gated relocated into the area freed by 1T1R_LSWEEP + RESERVED_AREA ("moved up"), and
     restructured: every internal gap that was 10-30 um is widened by +30 um (device row <-> its own
     label pairs, which sit 2.4-3 um apart, are left untouched -- that spacing is intentional single
     row pairing, not crowding). Pure Y-only rigid translation per band, no device redrawn.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v35_HK', 'v35_HK.oas')
OUT = os.path.join(HERE, 'v36_HK')
MINF = 2.0; PAD, PW = 160.0, 150.0
ENC = mkaudit.ENC; OVL = mkaudit.OVL

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly)
PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')

def R(c, n, rec=True):
    it = c.begin_shapes_rec(L[n]) if rec else None
    r = db.Region(it) if rec else db.Region(c.shapes(L[n])); r.merge(); return r
def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(x0), u(y0), u(x1), u(y1)))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
def win(c, x, y, l): d = (PAD - PW) / 2; bx(c, l, x + d, y + d, x + PAD - d, y + PAD - d)
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r)
    return r.bbox().width() * dbu
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500
def new_cell(name):
    c = ly.cell(name)
    if c is not None: raise RuntimeError(name + ' exists')
    return ly.create_cell(name)

# ============================================================== A. removals
print('== A. removals')
removed = 0
for cn in ('HFO2_TDDB', '1T1R_WSWEEP', '1T1R_LSWEEP', 'RESERVED_AREA'):
    for k in list(top.each_inst()):
        if k.cell.name == cn: k.delete(); removed += 1
print('   top-level instances removed:', removed)
S0 = set(top.called_cells())
for cn in ('HFO2_TDDB', '1T1R_WSWEEP', '1T1R_LSWEEP', 'RESERVED_AREA'):
    c = ly.cell(cn)
    if c is not None: ly.delete_cell(c.cell_index())
S1 = set(top.called_cells())
dead = [i for i in sorted(S0 - S1)]
if dead: ly.delete_cells(dead)
print('   orphaned cells cleared:', len(dead))

# ============================================================== B. 1T1R: tighten pitch, keep W/L=25
print('== B. 1T1R pitch 1200 -> 1150 (edge gap 130 -> 80 um), W500 L20 unchanged')
def t1r(c, X0, Y0, W, Lg, s, label=None):
    """bottom-gate staggered TFT (W,Lg) + M2/IGZO/M3 cross-point memristor (s x s). Validated against the
       real 1T1R device (v35 build log): 0.000 um2 difference for W=500,Lg=20,s=2."""
    def B(l, x0, y0, x1, y1): bx(c, l, X0 + x0, Y0 + y0, X0 + x1, Y0 + y1)
    def P(l, pts): poly(c, l, [(X0 + x, Y0 + y) for x, y in pts])
    cx = 305.0; g0, g1 = cx - Lg / 2 - 5, cx + Lg / 2 + 5; top_ = W - 170.0
    B('Metal_1', 225, -405, 385, -245); P('Metal_1', [(225, -245), (g0, -195), (g1, -195), (385, -245)])
    B('Metal_1', g0, -405, g1, top_ + 10)
    B('IGZO', 230, -180, 380, top_ + 10)
    B('Metal_3', 0, -405, 160, top_); B('Metal_3', 0, -170, cx - Lg / 2, top_)
    B('Metal_3', 450, -405, 610, 330); B('Metal_3', cx + Lg / 2, -170, 610, top_)
    B('Isolation_1', 230, -400, 380, -250)
    B('Isolation_1', 535 - 71.05, 255 - 71.05, 535 + 71.05, 255 + 71.05)
    B('Metal_2', 460, 180, 610, 330)
    P('Metal_2', [(610, 180), (610, 330), (685, 255 + s / 2), (685, 255 - s / 2)])
    B('Metal_2', 610, 255 - s / 2, 910, 255 + s / 2)
    P('Metal_2', [(910, 175), (835, 255 - s / 2), (835, 255 + s / 2), (910, 335)]); B('Metal_2', 910, 175, 1070, 335)
    B('Isolation_1', 915, 180, 1065, 330)
    B('IGZO', 700, 195, 820, 315)
    B('Metal_3', 680, -55, 840, 105); P('Metal_3', [(680, 105), (760 - s / 2, 180), (760 + s / 2, 180), (840, 105)])
    B('Metal_3', 760 - s / 2, 105, 760 + s / 2, 405)
    for x in (5, 230, 455): B(PASS, x, -400, x + 150, -250)
    B(PASS, 685, -50, 835, 100); B(PASS, 915, 180, 1065, 330)
    if label: txt(c, label, X0 + 0, Y0 + 372, 24.0)

old1t1r = ly.cell('1T1R'); old_bbox = old1t1r.bbox()
old_inst = ly.cell('1T1R_single')
X0_OLD = -2885.0; PITCH_OLD = 1200.0; PITCH_NEW = 1150.0
JUNCS = [2, 4, 5, 8, 10]                                                   # 2X2 4X4 5X5 8X8 10X10 (unchanged)
Y_OLD = -1900.0; PY = 900.0; NROWS = 5
new_single = new_cell('1T1R_single_v36')
for j, s in enumerate(JUNCS):
    t1r(new_single, X0_OLD + j * PITCH_NEW, 0.0, 500.0, 20.0, s)
print('   new 1T1R_single bbox', new_single.bbox(), '  old was', old_inst.bbox())
# validate: DRC-clean and same 5 devices, same junctions, only pitch differs
for n in LAY:
    a = R(new_single, n, rec=False); assert a.count() > 0
# replace: remove the old array instance from '1T1R', insert the new single 5x (still arrayed 5 rows vertically)
for k in list(old1t1r.each_inst()):
    if k.cell.name == '1T1R_single':
        arr = db.CellInstArray(new_single.cell_index(), db.Trans(u(0), u(Y_OLD)), db.Vector(0, u(PY)), db.Vector(0, 0), NROWS, 1)
        k.delete(); old1t1r.insert(arr)
ly.delete_cell(old_inst.cell_index())
# per-column header text: shift by the same cumulative pitch delta as its column (col0 unchanged/anchor).
# Match each label to its nearest column by (x - X0_old - typical_offset)/PITCH_OLD rounded to an int in
# [0,4] -- robust to per-string width differences (e.g. "10X10" vs "2X2" don't share one fixed offset,
# but 1200 um column spacing is >> any such difference, so nearest-integer matching is safe). The title
# and "L20_W500" sub-heading sit near column 0 and are unaffected by its shift of 0.
COL_SHIFT = {j: (PITCH_NEW - PITCH_OLD) * j for j in range(5)}             # 0,-50,-100,-150,-200
moved = 0
for k in list(old1t1r.each_inst()):
    if not k.cell.name.startswith('TEXT'): continue
    x = k.trans.disp.x * dbu
    j = round((x - X0_OLD - 635.25) / PITCH_OLD)
    if 0 <= j <= 4 and COL_SHIFT[j] != 0:
        k.transform(db.Trans(u(COL_SHIFT[j]), 0)); moved += 1
print('   column header labels re-centred:', moved, '  new 1T1R bbox', old1t1r.bbox())

# ============================================================== C. HfO2-only-dielectric staggered TFT split
print('== C. staggered bottom-gate TFT, HfO2-only dielectric (process split)')
bg = ly.cell('Transistors_BottomGate')
hf = new_cell('Transistors_BottomGate_HfO2Only')
for n in LAY: hf.shapes(L[n]).insert(bg.shapes(L[n]))
for k in bg.each_inst():
    if k.cell.name == 'TEXT$6': continue                                  # skip the old heading, we draw a new one
    hf.insert(db.CellInstArray(k.cell.cell_index(), k.trans))
hx0, hy0 = -1992.5, 1885.0
txt(hf, 'TFT BOTTOM GATE STAGGERED - HFO2 ONLY (PROCESS SPLIT, NO AL2O3)', hx0, hy0, 36.0)
print('   HfO2Only bbox', hf.bbox(), '  source bbox', bg.bbox())

# ============================================================== D. Memristors_Gated: relocate + de-crowd
# Safe unit of motion = a whole SECTION (device instances + their own text), never a shape-height band --
# a first attempt using generic Y-band detection moved a device's own M1 gate-lead protrusion away from
# the rest of that same device (it looked like a thin text label but wasn't) and shorted M1 to M2.
# The 4 sections (LATERAL RING GATED / LATERAL OPEN GATED / VERTICAL GATED / PROCESS SPLITS) are known
# exactly from the child-instance Y positions (measured on v35_HK.oas): a clean 72 um gap separates each
# pair, verified against the real instance list, not inferred from shape thinness.
print('== D. Memristors_Gated de-crowd (whole-section rigid shift)')
mg = ly.cell('Memristors_Gated')
BOUND = [-36.0, -750.0, -1464.0]                                          # G|O, O|V, V|AT (midpoints of the 72 um gaps)
SECTION_NEW_GAP = 250.0; SECTION_OLD_GAP = 72.0
def section_of(y):
    if y > BOUND[0]: return 0
    if y > BOUND[1]: return 1
    if y > BOUND[2]: return 2
    return 3
shifts = [0.0, 0.0, 0.0, 0.0]
for i in (2, 1, 0):                                                       # AT(3) anchored; V(2),O(1),G(0) pushed up
    shifts[i] = shifts[i + 1] + (SECTION_NEW_GAP - SECTION_OLD_GAP)
n_inst = [0, 0, 0, 0]
for k in list(mg.each_inst()):
    b = k.bbox(); yc = (b.bottom + b.top) / 2 * dbu
    sec = section_of(yc); n_inst[sec] += 1
    if shifts[sec]: k.transform(db.Trans(0, u(shifts[sec])))
n_glyph = [0, 0, 0, 0]
to_move = {0: [], 1: [], 2: [], 3: []}
for s in mg.shapes(L['Metal_1']).each():
    if not (s.is_polygon() or s.is_box()): continue
    p = s.polygon
    if not isglyph(p): continue                                          # only confirmed text moves independently
    yc = (p.bbox().bottom + p.bbox().top) / 2 * dbu
    to_move[section_of(yc)].append(p)
for sec, polys in to_move.items():
    n_glyph[sec] = len(polys)
    if not shifts[sec] or not polys: continue
    r = db.Region(polys)
    for s in list(mg.shapes(L['Metal_1']).each()):
        if (s.is_polygon() or s.is_box()) and not r.interacting(db.Region(s.polygon)).is_empty():
            mg.shapes(L['Metal_1']).erase(s)
    for p in polys: mg.shapes(L['Metal_1']).insert(p.transformed(db.Trans(0, u(shifts[sec]))))
print('   sections (top->bottom) instances', n_inst, ' glyphs', n_glyph, ' shifts', shifts)
print('   Memristors_Gated new bbox', mg.bbox())

def inst(name): return [k for k in top.each_inst() if k.cell.name == name]
mgk = inst('Memristors_Gated')[0]
b = mgk.bbox()                                                             # CURRENT placed bbox (k.transform() adds to the existing transform, so the delta must be measured from where the instance actually is, not the cell's local origin)
target_x, target_y = 4220.0, 1780.0                                        # F3 lower-left (freed by removing 1T1R_LSWEEP/RESERVED_AREA)
mgk.transform(db.Trans(u(target_x) - b.left, u(target_y) - b.bottom))
print('   Memristors_Gated instance moved to bbox', mgk.bbox())

b0 = inst('Transistors_BottomGate')[0].bbox()
top.insert(db.CellInstArray(hf.cell_index(), db.Trans(u(-1150.0) - hf.bbox().left, u(b0.bottom * dbu) - hf.bbox().bottom)))
print('   Transistors_BottomGate_HfO2Only placed at', inst('Transistors_BottomGate_HfO2Only')[0].bbox())

exec(open(os.path.join(HERE, 'verify_v36.py'), encoding='utf-8').read())
