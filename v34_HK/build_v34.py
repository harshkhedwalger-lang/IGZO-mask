"""build_v34.py -- v33 -> v34.  klayout.db only (never gdstk).  Output: OASIS (+GDS copy).

What changes vs v33 (everything else is left untouched and checked at the end):
  1. TOP-own geometry (alignment crosses, headings, logo) and every TEXT$ instance restored to v22.
  2. Memristors column headings (2X2 .. 10X10) moved back to the top of the array.
  3. MEM_ASYM / MEM_STACK_SPLIT / MEM_REDUNDANT labels restored from v32 (v33 shredded them), then any
     label touching a pad is nudged clear.
  4. MEM_HIGH_VALUE / SPLIT_CV labels moved off the pads; Memristors_Gated headings de-crowded.
  5. STEP_COVERAGE rebuilt as a real serpentine (v33 shorted all five rows at the right end).
  6. Block placement: STEP/XBAR stack, ResolutionTests legend, clearance from the alignment marks.
"""
import klayout.db as db, math, os, sys
from collections import Counter

DL = r'C:\Users\HAKH012F\Downloads'
SRC = DL + r'\v33_HK (2).oas'; V22 = DL + r'\v22_HK.oas'; V32 = DL + r'\v32_HK.oas'
OUTDIR = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(OUTDIR, 'v34_HK')
MINF = 2.0; PAD, PW = 160.0, 150.0; PITCH = 680.0

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
l22 = db.Layout(); l22.read(V22)
l32 = db.Layout(); l32.read(V32)
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L, L22, L32 = names(ly), names(l22), names(l32)
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', 'Isolation_2', 'Metal_4']
top = ly.cell('TOP')

def R(c, n, rec=True):
    r = db.Region(c.begin_shapes_rec(L[n])) if rec else db.Region(c.shapes(L[n])); r.merge(); return r
def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(x0), u(y0), u(x1), u(y1)))
def win(c, x, y, l): d = (PAD - PW) / 2; bx(c, l, x + d, y + d, x + PAD - d, y + PAD - d)
def ppad(c, x, y, met):
    bx(c, met, x, y, x + PAD, y + PAD)
    if met in ('Metal_1', 'Metal_2'):
        win(c, x, y, 'Isolation_1'); bx(c, 'Metal_3', x, y, x + PAD, y + PAD)
    win(c, x, y, 'Isolation_2')

# ---------------------------------------------------------------- text helpers
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500
def own_m1(c):
    return [s for s in c.shapes(L['Metal_1']).each() if s.is_polygon() or s.is_box() or s.is_path()]
def glyph_shapes(c): return [s for s in own_m1(c) if isglyph(s.polygon)]
def text_clusters(c, dx=40.0):
    """group a cell's own glyph polygons into words/lines (horizontal growth only)"""
    gl = [s.polygon for s in glyph_shapes(c)]
    if not gl: return []
    big = db.Region(gl).sized(u(dx / 2), 0); big.merge()
    out = []
    for cp in big.each():
        grp = [p for p in gl if db.Region(cp).interacting(db.Region(p)).count()]
        if grp: out.append(grp)
    return out
def cl_bbox(g):
    b = db.Box()
    for p in g: b += p.bbox()
    return b
def shift_cluster(c, grp, dx, dy):
    """move one cluster (its polygons must currently be own M1 glyph shapes of c)"""
    keys = {(p.bbox().left, p.bbox().bottom, p.area()) for p in grp}
    for s in glyph_shapes(c):
        p = s.polygon
        if (p.bbox().left, p.bbox().bottom, p.area()) in keys:
            c.shapes(L['Metal_1']).erase(s)
    for p in grp: c.shapes(L['Metal_1']).insert(p.transformed(db.Trans(u(dx), u(dy))))

def nontext(c):
    """everything in the cell that is not a text glyph"""
    o = db.Region()
    for s in own_m1(c):
        if not isglyph(s.polygon): o.insert(s.polygon)
    it = c.begin_shapes_rec(L['Metal_1'])
    while not it.at_end():      # M1 of child cells counts as structure
        if it.path():
            s = it.shape()
            if s.is_polygon() or s.is_box() or s.is_path(): o.insert(s.polygon.transformed(it.trans()))
        it.next()
    for n in LAY[1:] + ['Alignment']: o += db.Region(c.begin_shapes_rec(L[n]))
    o.merge(); return o

def decrowd(c, halo=4.0, maxdy=80, minpolys=2):
    """nudge any real text cluster that touches structure (or other text) to the nearest free spot"""
    moved = 0
    cls = [g for g in text_clusters(c) if len(g) >= minpolys]
    obst = nontext(c).sized(u(halo))
    placed = db.Region()
    bad = []
    for g in cls:
        r = db.Region(g)
        if r.interacting(obst).is_empty() and r.sized(u(halo)).and_(placed).is_empty(): placed += r.sized(u(halo))
        else: bad.append(g)
    for g in bad:
        r = db.Region(g); done = False
        cand = [(0, d) for d in range(2, maxdy + 1, 2)] + [(0, -d) for d in range(2, 41, 2)]
        cand += [(sx * dx_, d) for dx_ in range(10, 61, 10) for sx in (1, -1) for d in range(0, maxdy + 1, 4)]
        for dx_, dy_ in cand:
            m = r.transformed(db.Trans(u(dx_), u(dy_)))
            if m.interacting(obst).is_empty() and m.sized(u(halo)).and_(placed).is_empty():
                shift_cluster(c, g, dx_, dy_); placed += m.sized(u(halo)); moved += 1; done = True; break
        if not done: print('   !! could not clear a label in', c.name, cl_bbox(g))
    return moved

# ==================================================================== 1. TOP restore from v22
print('== 1. restore TOP-own geometry and TEXT instances from v22')
for n in list(LAY) + ['Alignment', '63']:
    top.shapes(L[n]).clear()
    top.shapes(L[n]).insert(l22.cell('TOP').shapes(L22[n]))
for k in list(top.each_inst()):
    if k.cell.name.startswith('TEXT'): k.delete()
n_txt = 0
for k in l22.cell('TOP').each_inst():
    if not k.cell.name.startswith('TEXT'): continue
    assert not k.is_regular_array()
    tc = ly.cell(k.cell.name)
    for n in LAY:   # the text cell itself must be identical in both versions
        a = db.Region(l22.cell(k.cell.name).begin_shapes_rec(L22[n])); b = db.Region(tc.begin_shapes_rec(L[n]))
        assert a.xor(b).is_empty(), k.cell.name
    top.insert(db.CellInstArray(tc.cell_index(), k.trans)); n_txt += 1
print('   TEXT instances restored:', n_txt)

# ==================================================================== 2. Memristors heading row
print('== 2. Memristors headings back to the top of the array')
mc = ly.cell('Memristors')
for k in list(mc.each_inst()):
    if k.cell.name.startswith('TEXT'):
        want = 4400.0 if k.cell.name == 'TEXT$115' else 4290.0        # v22 heights
        k.transform(db.Trans(0, u(want) - k.trans.disp.y))

# ==================================================================== 3. labels of the split/asym/redundant blocks
print('== 3. restore v33-shredded labels from v32')
for cn in ('MEM_ASYM', 'MEM_STACK_SPLIT', 'MEM_REDUNDANT'):
    c = ly.cell(cn); c32 = l32.cell(cn)
    old = [s.polygon for s in c32.shapes(L32['Metal_1']).each() if isglyph(s.polygon)]
    r32 = db.Region(c32.shapes(L32['Metal_1'])); r32.merge()
    r33 = db.Region(c.shapes(L['Metal_1'])); r33.merge()
    ng32 = db.Region([p for p in r32.each() if not isglyph(p)]); ng33 = db.Region([p for p in r33.each() if not isglyph(p)])
    assert ng32.xor(ng33).area() * dbu * dbu < 1, (cn, ng32.xor(ng33).area() * dbu * dbu)   # non-text M1 unchanged
    c.shapes(L['Metal_1']).clear()
    for p in ng33.each(): c.shapes(L['Metal_1']).insert(p)
    for p in old: c.shapes(L['Metal_1']).insert(p)
    print(f'   {cn}: {len(old)} glyph polygons restored, labels nudged: {decrowd(c)}')

# ==================================================================== 4. label placement in rebuilt / crowded blocks
print('== 4. HIGH_VALUE, SPLIT_CV, Memristors_Gated labels')
hv = ly.cell('MEM_HIGH_VALUE')
for g in text_clusters(hv):
    if len(g) < 2: continue                        # single M1 boxes are the gate plates, not text
    b = cl_bbox(g); bb, bl = b.bottom * dbu, b.left * dbu
    if bb > 0:                                     # title and the two column headings sit above the N pads
        shift_cluster(hv, g, 0, 50.0)
    else:                                          # per-device label: park it right of the N pad, above the E pad
        col = 0.0 if bl < 600 else PITCH
        y0 = bb - 172.0
        shift_cluster(hv, g, col + 410.0 - bl, y0 + 250.0 - bb)
sv = ly.cell('SPLIT_CV')
for x_ in (328.5, 388.5):                          # the font has no '=': draw the two missing ones in "W=L=400UM"
    for y_ in (667.5, 677.5): bx(sv, 'Metal_1', x_ + .5, y_, x_ + 17.5, y_ + 3.0)
for g in text_clusters(sv): shift_cluster(sv, g, 0, 70.0)
gm = ly.cell('Memristors_Gated')
for g in text_clusters(gm):
    b = cl_bbox(g)
    if b.bottom * dbu > 700: shift_cluster(gm, g, 0, 34.0)           # block title
    else: shift_cluster(gm, g, 0, 16.0)                               # section headings
print('   labels nudged in Memristors_Gated:', decrowd(gm))

# ==================================================================== 5. STEP_COVERAGE: real serpentine
print('== 5. STEP_COVERAGE rebuilt as serpentine with four-wire pads')
sc = ly.cell('STEP_COVERAGE')
keep = [s.polygon for s in glyph_shapes(sc)
        if not (abs(s.polygon.bbox().width() * dbu - 10) < .5 and abs(s.polygon.bbox().height() * dbu - 30) < .5)]
for n in LAY: sc.shapes(L[n]).clear()
for p in keep: sc.shapes(L['Metal_1']).insert(p)
for gy, steps in ((0.0, True), (-800.0, False)):
    for r in range(5):
        yy = gy - 120 * r
        bx(sc, 'Metal_3', 0, yy, 600, yy + 6)
        if steps:
            for k in range(20): bx(sc, 'Metal_1', 8 + k * 30, yy - 12, 18 + k * 30, yy + 18)
    for r in range(4):                                              # alternate ends -> one continuous serpentine
        yy = gy - 120 * r
        if r % 2 == 0: bx(sc, 'Metal_3', 594, yy - 120, 600, yy + 6)
        else: bx(sc, 'Metal_3', 0, yy - 120, 6, yy + 6)
    # force (F) at the two ends, sense (S) pads tapped at the same nodes
    ppad(sc, -240, gy + 3 - PAD / 2, 'Metal_3');            bx(sc, 'Metal_3', -80, gy, 0, gy + 6)                 # F+
    ppad(sc, -240, gy - 237 - PAD / 2, 'Metal_3');          bx(sc, 'Metal_3', -80, gy - 240, -14, gy - 234)       # S+
    bx(sc, 'Metal_3', -20, gy - 240, -14, gy + 6)
    ppad(sc, 680, gy - 480 + 3 - PAD / 2, 'Metal_3');       bx(sc, 'Metal_3', 600, gy - 480, 680, gy - 474)       # F-
    ppad(sc, 680, gy - 237 - PAD / 2, 'Metal_3');           bx(sc, 'Metal_3', 614, gy - 240, 680, gy - 234)       # S-
    bx(sc, 'Metal_3', 614, gy - 480, 620, gy - 234)
    bx(sc, 'Metal_3', 600, gy - 480, 620, gy - 474)

# ==================================================================== 6. placement
print('== 6. block placement')
def inst(name): return [k for k in top.each_inst() if k.cell.name == name]
def move_to(k, x=None, y=None):
    b = k.bbox(); dxm = 0 if x is None else u(x) - b.left; dym = 0 if y is None else u(y) - b.bottom
    k.transform(db.Trans(dxm, dym))
xb = inst('XBAR_4X4')[0]; st = inst('STEP_COVERAGE')[0]
move_to(st, y=xb.bbox().top * dbu + 100.0)
print('   STEP_COVERAGE bbox', st.bbox(), ' XBAR', xb.bbox())
for k in inst('ResolutionTests'):
    if k.bbox().left * dbu > 0: k.transform(db.Trans(u(-380.0), 0))   # clear of the bottom-right cross and its label

def _flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r
def keepout():
    """alignment crosses (+20 um) and every alignment label box (+10 um)"""
    crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
    kz = db.Region(crosses).sized(u(40))
    for t in top.each_inst():
        if t.cell.name.startswith('TEXT'): kz += db.Region(t.bbox().enlarged(u(10), u(10)))
    return kz
def place_clear(k, dxs=(0,), dys=(0,), gap=30.0):
    """slide instance k to the nearest offset where it hits no alignment keep-out and no other block"""
    kz = keepout(); base = _flat(k)
    others = db.Region()
    for o in top.each_inst():
        if o != k and not o.cell.name.startswith('TEXT'): others += _flat(o)
    others.merge(); others = others.sized(u(gap)) + kz
    for dxm, dym in sorted(((a, b) for a in dxs for b in dys), key=lambda t: t[0] ** 2 + t[1] ** 2):
        if base.transformed(db.Trans(u(dxm), u(dym))).and_(others).is_empty():
            k.transform(db.Trans(u(dxm), u(dym))); return dxm, dym
    return None
inst('Memristors')[0].transform(db.Trans(u(-60.0), 0))            # 2 um -> 62 um to the MEM_ASYM column
inst('Memristors_Gated')[0].transform(db.Trans(0, u(-40.0)))      # keep its title clear of the 1T1R 'BOTTOM GATE' label
ss = inst('MEM_STACK_SPLIT')[0]
print('   MEM_STACK_SPLIT moved by', place_clear(ss, dxs=range(-100, 1, 10), dys=range(-700, 701, 10)))

# ==================================================================== 7. verification
LAYA = LAY
def audit(cells):
    bad = []
    for cn in cells:
        c = ly.cell(cn)
        m1, m2, m3, m4 = R(c, 'Metal_1'), R(c, 'Metal_2'), R(c, 'Metal_3'), R(c, 'Metal_4')
        ig, i1, i2 = R(c, 'IGZO'), R(c, 'Isolation_1'), R(c, 'Isolation_2')
        met = m1.or_(m2).or_(m3).or_(m4)
        o1 = i1.not_(met.or_(ig)); o2 = i2.not_(met.or_(ig))
        if o1.area(): bad.append((cn, 'Isolation_1 window off metal'))
        if o2.area(): bad.append((cn, 'Isolation_2 window off metal'))
        for p in i2.each():
            pr = db.Region(p)
            if not pr.and_(m1.or_(m2)).is_empty() and pr.not_(m3).area() > 0.2 * p.area():
                bad.append((cn, 'pad on M1/M2 not capped by Metal_3'))
        for p in i1.each():
            pr = db.Region(p)
            if not pr.and_(m1).is_empty() and not pr.and_(m2).is_empty(): bad.append((cn, 'Isolation_1 window shorts M1 to M2'))
        for p in ig.each():
            pr = db.Region(p)
            if pr.and_(m3).is_empty() and i1.interacting(pr).count() == 0: bad.append((cn, 'IGZO island with no contact'))
        for nm, reg in (('Metal_1', m1), ('Metal_2', m2), ('Metal_3', m3)):
            for p in reg.each():
                if p.area() * dbu * dbu < 400: continue
                pr = db.Region(p)
                if pr.width_check(u(6.0), False, db.Region.Projection, None, None, None).count(): continue
                if i2.interacting(pr).count() or i1.interacting(pr).count(): continue
                if nm in ('Metal_2', 'Metal_3') and not pr.and_(ig).is_empty(): continue
                bad.append((cn, nm + ' island floating'))
    return bad
CHECK = ['SPLIT_CV', 'XBAR_4X4', 'STEP_COVERAGE', 'HFO2_MIM', 'AL2O3_INTEGRITY', 'MEM_STACK_SPLIT', 'MEM_ASYM', 'MEM_HIGH_VALUE', 'MEM_REDUNDANT']
print('\n== 7. verification')
aud = audit(CHECK); print('   fabricability audit findings:', len(aud))
for k, v in Counter(aud).items(): print('     ', k, 'x', v)
# net extraction on the rebuilt serpentine: each row group must be ONE M3 net carrying 4 pads
m3s = R(sc, 'Metal_3'); i2s = R(sc, 'Isolation_2')
print('   STEP_COVERAGE M3 nets:', m3s.count(), '(expect 2)  pad windows:', i2s.count(), '(expect 8)')
for p in m3s.each():
    print('      net bbox', round(p.bbox().left * dbu), round(p.bbox().bottom * dbu), round(p.bbox().right * dbu), round(p.bbox().top * dbu),
          ' pads on it:', i2s.interacting(db.Region(p)).count())

def flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r
ai = [k for k in top.each_inst()]
blocks = [k for k in ai if not k.cell.name.startswith('TEXT')]
texts = [k for k in ai if k.cell.name.startswith('TEXT')]
fl = {id(k): flat(k) for k in ai}
own = db.Region()
for n in LAY: own = own.or_(db.Region(top.shapes(L[n])))
own.merge()
ov = 0
for a in range(len(blocks)):
    for b in range(a + 1, len(blocks)):
        A, B = blocks[a], blocks[b]
        if not A.bbox().overlaps(B.bbox()): continue
        o = fl[id(A)].and_(fl[id(B)]).area() * dbu * dbu
        if o: print('   OVERLAP', A.cell.name, B.cell.name, round(o)); ov += o
for k in blocks:
    o = fl[id(k)].and_(own).area() * dbu * dbu
    if o: print('   OVERLAP', k.cell.name, 'vs TOP-own', round(o)); ov += o
print('   structure overlap um2:', round(ov))
# closest approach between different top-level blocks (bbox neighbours only)
gaps = []
for a in range(len(blocks)):
    for b in range(a + 1, len(blocks)):
        A, B = blocks[a], blocks[b]
        if not A.bbox().enlarged(u(30), u(30)).overlaps(B.bbox()): continue
        e = fl[id(A)].separation_check(fl[id(B)], u(30), False, db.Region.Projection, None, None, None)
        if e.count():
            d = min(x.distance() for x in e.each()) * dbu; gaps.append((round(d, 1), A.cell.name, B.cell.name))
for g in sorted(gaps)[:12]: print('   block gap < 30 um:', g)
print('   block pairs closer than 30 um:', len(gaps))
# text vs structure / other text (block-level bbox pairs, then geometry)
allb = db.Region()
for k in blocks: allb = allb.or_(fl[id(k)])
allb = allb.or_(own)
allb.merge()
tx = 0
for t in texts:
    ft = fl[id(t)]
    o = ft.and_(allb).area() * dbu * dbu
    if o: print('   TEXT on structure:', t.cell.name, t.trans.disp.x * dbu, t.trans.disp.y * dbu, round(o)); tx += 1
    for t2 in texts:
        if t2 is t or id(t2) < id(t): continue
        if t.bbox().overlaps(t2.bbox()) and not ft.and_(fl[id(t2)]).is_empty():
            print('   TEXT on TEXT:', t.cell.name, t2.cell.name); tx += 1
print('   text collisions (TEXT$ cells):', tx)
# clearance to the alignment crosses (crosses are the 540 um M1 polygons in TOP)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40))
kz_lbl = db.Region()
for t in texts: kz_lbl += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = 0
for k in blocks:
    o = fl[id(k)].and_(kz).area() * dbu * dbu
    if o: print('   block inside alignment-mark zone:', k.cell.name, round(o)); viol += 1
    o = fl[id(k)].and_(kz_lbl).area() * dbu * dbu
    if o: print('   block inside alignment label box:', k.cell.name, round(o)); viol += 1
print('   alignment-mark clearance violations:', viol)
# block-level text (cell-own glyph clusters) vs structure of the same cell
tcnt = 0
for cn in ('MEM_ASYM', 'MEM_STACK_SPLIT', 'MEM_REDUNDANT', 'MEM_HIGH_VALUE', 'SPLIT_CV', 'Memristors_Gated', 'MIS_Capacitors', 'CBKR_Structures', 'HFO2_MIM', 'AL2O3_INTEGRITY', 'XBAR_4X4'):
    c = ly.cell(cn); ob = nontext(c)
    for g in text_clusters(c):
        if len(g) < 2: continue
        if not db.Region(g).interacting(ob).is_empty(): tcnt += 1; print('   label touches structure in', cn, cl_bbox(g))
print('   in-block label collisions:', tcnt)
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001; tw = ts = 0
for n in LAY:
    r = db.Region(top.begin_shapes_rec(L[n])); r.merge()
    tw += len([e for e in r.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e.distance() * dbu < lim])
    ts += len([e for e in r.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e.distance() * dbu < lim])
print('   DRC 2um: width', tw, 'space', ts)
# preservation vs v22
d = 0
for n in LAY + ['Alignment', '63']:
    a = db.Region(top.shapes(L[n])); b = db.Region(l22.cell('TOP').shapes(L22[n]))
    d += a.xor(b).area()
print('   TOP-own geometry differs from v22 by um2:', round(d * dbu * dbu))
p22 = {(k.cell.name, k.trans.disp.x, k.trans.disp.y) for k in l22.cell('TOP').each_inst() if k.cell.name.startswith('TEXT')}
p34 = {(k.cell.name, k.trans.disp.x, k.trans.disp.y) for k in top.each_inst() if k.cell.name.startswith('TEXT')}
print('   TEXT instances differing from v22:', len(p22 ^ p34))

ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
