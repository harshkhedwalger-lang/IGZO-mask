"""build_v35.py -- v34 -> v35   (klayout.db only, never gdstk; OASIS + GDS copy)

6-layer process:  M1 | Al2O3#1 | M2 | HfO2 | [Iso1] | IGZO | M3 | Passivation | [Passivation open]
  1/0 Metal_1  2/0 Isolation_1  3/0 Metal_2  4/0 IGZO  5/0 Metal_3  6/0 Passivation   (Metal_4 / 7/0 removed)

Changes vs v34
  A. removed: all coplanar TFTs, all top-gate TFTs (Transistors_TopGate, Dual_Gate, coplanar rows of
     Transistors_BottomGate), GATE OXIDE 2 tests (Al2O3#2 is now passivation), the L7 row of the litho
     legends, layer Metal_4.  Layer 6/0 renamed Passivation.  Cells orphaned by this are deleted.
  B. added: 1T1R W-sweep, 1T1R L-sweep, HfO2 TDDB / Weibull arrays (10x10 and 30x30 um), reserved area.
  C. overlay rules (mkaudit.py, OVL/ENC): enclosure patches on pad windows and IGZO-stack junction windows.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

DL = r'C:\Users\HAKH012F\Downloads'
SRC = os.path.join(HERE, '..', 'v34_HK', 'v34_HK.oas'); V22 = DL + r'\v22_HK.oas'
OUT = os.path.join(HERE, 'v35_HK')
MINF = 2.0; PAD, PW = 160.0, 150.0
ENC = mkaudit.ENC; OVL = mkaudit.OVL

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
l22 = db.Layout(); l22.read(V22)
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); L22 = names(l22)
top = ly.cell('TOP')
S0 = set(top.called_cells())                       # cells reachable before any edit

# ============================================================== A. removals
print('== A. removals')
for k in list(top.each_inst()):
    if k.cell.name in ('Transistors_TopGate', 'Dual_Gate'): print('   removed instance', k.cell.name); k.delete()

def cut(cell, drop, label):
    """delete every own shape / instance for which drop(bbox_um) is true; refuse if a shape straddles the cut"""
    n = 0
    for name, li in L.items():
        for s in list(cell.shapes(li).each()):
            b = s.bbox(); bb = (b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu)
            if drop(bb): cell.shapes(li).erase(s); n += 1
    for k in list(cell.each_inst()):
        b = k.bbox()
        if drop((b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu)): k.delete(); n += 1
    print(f'   {label}: {n} shapes/instances removed')

# coplanar rows = everything below y=0 in Transistors_BottomGate (staggered rows sit at y>=75, verified)
bg = ly.cell('Transistors_BottomGate')
for li in L.values():
    for s in bg.shapes(li).each():
        assert not (s.bbox().bottom * dbu < 0 < s.bbox().top * dbu), 'shape straddles the staggered/coplanar cut'
cut(bg, lambda b: b[3] <= 0, 'Transistors_BottomGate coplanar rows')
# GATE OXIDE 2 row of TestStructures (M4 top electrode); FGTFT block on the right (x>2100) is untouched
ts = ly.cell('TestStructures')
for li in L.values():
    for s in ts.shapes(li).each():
        b = s.bbox(); assert not (b.left * dbu < 2100 and b.bottom * dbu < -1150 < b.top * dbu), 'straddle'
cut(ts, lambda b: b[3] < -1150 and b[2] < 2100, 'TestStructures GATE OXIDE 2 row')
# L7 row of the litho legend
rt = ly.cell('ResolutionTests')
for li in L.values():
    for s in rt.shapes(li).each():
        assert not (s.bbox().bottom * dbu < -750 < s.bbox().top * dbu), 'straddle'
cut(rt, lambda b: b[3] < -750, 'ResolutionTests L7 row')

# Metal_4: what is left is only the M3-duplicate on the TLM contact bars -> gone with the layer
left = 0
for c in ly.each_cell():
    r = c.shapes(L['Metal_4']); left += r.size(); r.clear()
print('   Metal_4 shapes cleared:', left)
ly.delete_layer(L['Metal_4']); L = names(ly)
ly.set_info(L['Isolation_2'], db.LayerInfo(6, 0, 'Passivation')); L = names(ly)
PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
S1 = set(top.called_cells()); dead = sorted(S0 - S1)
print('   orphaned cells deleted:', len(dead), [ly.cell(i).name for i in dead if not ly.cell(i).name.startswith('TEXT')])
ly.delete_cells(dead)

# ============================================================== helpers
def R(c, n, rec=True):
    it = c.begin_shapes_rec(L[n]) if rec else None
    r = db.Region(it) if rec else db.Region(c.shapes(L[n])); r.merge(); return r
def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(x0), u(y0), u(x1), u(y1)))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
def win(c, x, y, l): d = (PAD - PW) / 2; bx(c, l, x + d, y + d, x + PAD - d, y + PAD - d)
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7                # cap height 1 um per unit
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r)
    return r.bbox().width() * dbu
def new_cell(name):
    c = ly.cell(name)
    if c is not None: raise RuntimeError(name + ' exists')
    return ly.create_cell(name)

# ============================================================== B1. parametric 1T1R device (same topology as 1T1R_single)
def t1r(c, X0, Y0, W, Lg, s, label=None):
    """TFT (bottom gate, M3 S/D, staggered, channel length Lg, width W) + memristor M2/IGZO/M3 cross-point s x s.
       (X0,Y0) = position of local origin (S-pad left edge, y=0).  Reproduces 1T1R_single for W=500, Lg=20, s=2."""
    def B(l, x0, y0, x1, y1): bx(c, l, X0 + x0, Y0 + y0, X0 + x1, Y0 + y1)
    def P(l, pts): poly(c, l, [(X0 + x, Y0 + y) for x, y in pts])
    cx = 305.0; g0, g1 = cx - Lg / 2 - 5, cx + Lg / 2 + 5; top_ = W - 170.0
    B('Metal_1', 225, -405, 385, -245); P('Metal_1', [(225, -245), (g0, -195), (g1, -195), (385, -245)])
    B('Metal_1', g0, -405, g1, top_ + 10)                                            # gate bar
    B('IGZO', 230, -180, 380, top_ + 10)                                             # channel island
    B('Metal_3', 0, -405, 160, top_); B('Metal_3', 0, -170, cx - Lg / 2, top_)       # S column + electrode
    B('Metal_3', 450, -405, 610, 330); B('Metal_3', cx + Lg / 2, -170, 610, top_)    # D column + electrode
    B('Isolation_1', 230, -400, 380, -250)                                            # gate pad window (direct M1)
    B('Isolation_1', 535 - 71.05, 255 - 71.05, 535 + 71.05, 255 + 71.05)              # D -> M2 (memristor BE) contact
    B('Metal_2', 460, 180, 610, 330)
    P('Metal_2', [(610, 180), (610, 330), (685, 255 + s / 2), (685, 255 - s / 2)])
    B('Metal_2', 610, 255 - s / 2, 910, 255 + s / 2)
    P('Metal_2', [(910, 175), (835, 255 - s / 2), (835, 255 + s / 2), (910, 335)]); B('Metal_2', 910, 175, 1070, 335)
    B('Isolation_1', 915, 180, 1065, 330)
    B('IGZO', 700, 195, 820, 315)                                                     # junction island
    B('Metal_3', 680, -55, 840, 105); P('Metal_3', [(680, 105), (760 - s / 2, 180), (760 + s / 2, 180), (840, 105)])
    B('Metal_3', 760 - s / 2, 105, 760 + s / 2, 405)                                  # TE neck over the M2 neck
    for x in (5, 230, 455): B(PASS, x, -400, x + 150, -250)                           # S, G, D pads
    B(PASS, 685, -50, 835, 100); B(PASS, 915, 180, 1065, 330)                         # TE pad, BE (M2) pad
    if label: txt(c, label, X0 + 0, Y0 + 372, 24.0)

# ---- self-check: reproduce device 1 of the existing 1T1R_single (W500 L20 s2) and XOR it
chk = new_cell('_T1R_CHECK'); t1r(chk, -2885, 0, 500, 20, 2)
ref = ly.cell('1T1R_single')
worst = 0
for n in LAY:
    a = R(chk, n); b = R(ref, n).and_(db.Region(db.Box(u(-2890), u(-410), u(-1810), u(410))))
    xr = a.xor(b); worst += xr.area()
    for q in xr.each(): print('      diff', n, [round(v * dbu, 2) for v in (q.bbox().left, q.bbox().bottom, q.bbox().right, q.bbox().top)])
print('   1T1R generator vs existing device: differing area um2 =', round(worst * dbu * dbu, 3))
ly.delete_cell(chk.cell_index())
assert worst == 0, 'generator does not reproduce the existing 1T1R device'

# ============================================================== B2. 1T1R sweeps
def sweep(name, heading, rows, cols, pitch_x=1200.0, pitch_y=900.0):
    """rows = [(W,L)], cols = [s]; device local origin at (col*pitch_x, -row*pitch_y); y=0 row is the top row"""
    c = new_cell(name)
    for ri, (W, Lg) in enumerate(rows):
        for ci, s in enumerate(cols):
            t1r(c, ci * pitch_x, -ri * pitch_y, W, Lg, s, f'W{W:g} L{Lg:g} J{s:g}X{s:g}')
    txt(c, heading, 0, 470, 36.0)
    return c
WROWS = [(100, 20), (50, 20), (20, 20), (10, 20)]
LROWS = [(100, 10), (100, 5), (100, 40)]
c_w = sweep('1T1R_WSWEEP', '1T1R W SWEEP  L20', WROWS, [2, 4, 10])
c_l = sweep('1T1R_LSWEEP', '1T1R L SWEEP  W100', LROWS, [2, 10], pitch_x=1130.0)

# ============================================================== B3. HfO2 TDDB / Weibull arrays (cross-point, single-edge)
def tddb(c, name, n, cw, yc, P=120.0):
    """n identical M2/HfO2/M3 capacitors cw x cw um on a common M2 bus (both ends probed); TE line of each cap goes
       N (even) or S (odd) to its own pad.  Cap area = M2 bus width x M3 line width  ->  independent of overlay."""
    xs = [i * P for i in range(n)]; x0, x1 = xs[0] - 25, xs[-1] + 25
    bx(c, 'Metal_2', x0, yc - cw / 2, x1, yc + cw / 2)                                  # BE bus (width = cw)
    for side, xe, xp in ((-1, x0, x0 - 75 - PAD), (1, x1, x1 + 75)):                    # BE pads on the bus ends (E/W)
        poly(c, 'Metal_2', [(xe, yc - cw / 2), (xe + side * 75, yc - PAD / 2), (xe + side * 75, yc + PAD / 2), (xe, yc + cw / 2)])
        bx(c, 'Metal_2', xp, yc - PAD / 2, xp + PAD, yc + PAD / 2)
        win(c, xp, yc - PAD / 2, 'Isolation_1'); bx(c, 'Metal_3', xp, yc - PAD / 2, xp + PAD, yc + PAD / 2); win(c, xp, yc - PAD / 2, PASS)
    for i, x in enumerate(xs):
        sd = 1 if i % 2 == 0 else -1
        e = cw / 2 + ENC                                                                # TE line starts ENC past the bus edge
        ya = yc - sd * e; yb = yc + sd * (cw / 2 + 60)                                   # straight part up to the taper
        bx(c, 'Metal_3', x - cw / 2, min(ya, yb), x + cw / 2, max(ya, yb))
        pad_y0 = yc + sd * (cw / 2 + 60 + 75)                                            # near edge of the pad
        poly(c, 'Metal_3', [(x - cw / 2, yb), (x + cw / 2, yb), (x + PAD / 2, pad_y0), (x - PAD / 2, pad_y0)])
        py = pad_y0 if sd > 0 else pad_y0 - PAD
        bx(c, 'Metal_3', x - PAD / 2, py, x + PAD / 2, py + PAD); win(c, x - PAD / 2, py, PASS)
    return (xs[-1] - xs[0]) + 2 * (25 + 75 + PAD)
c_t = new_cell('HFO2_TDDB')
wA = tddb(c_t, 'A', 20, 10.0, 0.0)
yB = -900.0
wB = tddb(c_t, 'B', 10, 30.0, yB)
xlab = -25 - 75 - PAD
txt(c_t, 'HFO2 TDDB WEIBULL  M2/HFO2/M3', xlab, 470, 36.0)
txt(c_t, 'A: 20 X 10X10 UM  COMMON BE', xlab, 380, 24.0)
txt(c_t, 'B: 10 X 30X30 UM  AREA SCALING', xlab, yB + 380, 24.0)
print('   TDDB arrays: A width %.0f, B width %.0f' % (wA, wB))

# ============================================================== C. overlay enclosure patches (leaf cells, own shapes)
print('== C. overlay enclosure patches (ENC = %.1f um)' % ENC)
def own(c, n): return R(c, n, rec=False)
patched = Counter()
def patch_cell(c):
    i1 = own(c, 'Isolation_1'); i2 = own(c, PASS)
    if i1.is_empty() and i2.is_empty(): return
    m1, m2, m3, ig = own(c, 'Metal_1'), own(c, 'Metal_2'), own(c, 'Metal_3'), own(c, 'IGZO')
    add = {'Metal_1': db.Region(), 'Metal_2': db.Region(), 'Metal_3': db.Region(), 'IGZO': db.Region()}
    e = u(ENC)
    for p in i1.each():
        pr = db.Region(p); big = pr.sized(e); bb = p.bbox()
        onm1 = not pr.and_(m1).is_empty(); onm2 = not pr.and_(m2).is_empty(); onm3 = not pr.and_(m3).is_empty(); onig = not pr.and_(ig).is_empty()
        big_pad = bb.width() * dbu >= 40 and bb.height() * dbu >= 40
        if big_pad:                                                      # pad / contact window: land inside the pad, M3 cap encloses
            if onm1 and not (big - m1).is_empty(): add['Metal_1'] += big; patched['pad window M1'] += 1
            elif onm2 and not (big - m2).is_empty(): add['Metal_2'] += big; patched['pad window M2'] += 1
            if onm3 and not (big - m3).is_empty(): add['Metal_3'] += big; patched['pad window M3 cap'] += 1
        elif onig and onm2 and onm3:                                     # IGZO-only stack: window defines the junction area
            if not (big - m2).is_empty(): add['Metal_2'] += big
            if not (big - m3).is_empty(): add['Metal_3'] += big
            if not (big - ig).is_empty(): add['IGZO'] += big.sized(0)
            patched['junction window (M2, M3, IGZO)'] += 1
        elif onig and onm2:                                              # series-resistor end window: widen perpendicular to the neck only
            ext = db.Region(db.Box(bb.left, bb.bottom - e, bb.right, bb.top + e))
            if not (big - m2).is_empty(): add['Metal_2'] += ext
            if not (big - ig).is_empty(): add['IGZO'] += big
            patched['resistor end window (M2 wider)'] += 1
    for p in i2.each():                                                  # passivation window inside its pad metal
        pr = db.Region(p); big = pr.sized(e)
        if not (big - m3).is_empty() and not pr.and_(m3).is_empty(): add['Metal_3'] += big; patched['passivation window M3'] += 1
        elif pr.and_(m3).is_empty():
            for nm, mm in (('Metal_1', m1), ('Metal_2', m2)):
                if not pr.and_(mm).is_empty() and not (big - mm).is_empty(): add[nm] += big; patched['passivation window ' + nm] += 1
    for nm, r in add.items():
        if not r.is_empty():
            for q in r.each(): c.shapes(L[nm]).insert(q)
for c in list(ly.each_cell()):
    if c.name.startswith('TEXT') or c.name in ('ResolutionTests', 'TOP', 'TS') or c.name.startswith('MIScap'): continue
    patch_cell(c)
for k, v in sorted(patched.items()): print(f'   patched {v:4d} x {k}')

# ============================================================== D. placement
print('== D. placement')
def inst(name): return [k for k in top.each_inst() if k.cell.name == name]
def place(cell_name, x, y, corner='ll'):
    """put the cell so that its lower-left bbox corner lands on (x, y)"""
    c = ly.cell(cell_name); b = c.bbox()
    top.insert(db.CellInstArray(c.cell_index(), db.Trans(u(x) - b.left, u(y) - b.bottom)))
# free rectangles left by the removals (v34 coordinates): F1 x-1106..2929 y2595..6505 ; F2 x-5260..-1225 y2595..4550 ; F3 x4160..6620 y1720..6610
F1 = (-1106, 2595, 2929, 6505); F2 = (-5260, 2595, -1225, 4550); F3 = (4160, 1720, 6620, 6610)
bw = c_w.bbox(); place('1T1R_WSWEEP', F1[0] + 60, F1[3] - 90 - bw.height() * dbu, 'll')       # top-left inside F1
bl = c_l.bbox(); place('1T1R_LSWEEP', F3[0] + 60, F3[3] - 260 - bl.height() * dbu, 'll')      # below the active3D logo (TOP-own, y>=6490)
bt = c_t.bbox(); place('HFO2_TDDB', F2[0] + 60, F2[3] - 60 - bt.height() * dbu, 'll')         # top-left inside F2
def gb(name, k=0): b = inst(name)[k].bbox(); return b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu
for n in ('1T1R_WSWEEP', '1T1R_LSWEEP', 'HFO2_TDDB'): print('  ', n, [round(v) for v in gb(n)])
# reserved area: what is left of F3 below the L sweep
res_top = gb('1T1R_LSWEEP')[1] - 150
res = (F3[0] + 60, F3[1] + 60, F3[2] - 60, res_top)
rc = new_cell('RESERVED_AREA')
txt(rc, 'RESERVED  FREE AREA', 0, 0, 36.0)
txt(rc, '%d X %d UM  NO STRUCTURES' % (res[2] - res[0], res[3] - res[1]), 0, -60, 24.0)
top.insert(db.CellInstArray(rc.cell_index(), db.Trans(u(res[0]), u(res[3] - 40))))
print('   reserved area (um):', res, ' size', res[2] - res[0], 'x', res[3] - res[1])
print('   TDDB block width', round(bt.width() * dbu), 'height', round(bt.height() * dbu), '  F2 is', F2[2] - F2[0], 'x', F2[3] - F2[1])

exec(open(os.path.join(HERE, 'verify_v35.py'), encoding='utf-8').read())
