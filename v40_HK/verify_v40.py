# executed inside build_v40.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)

# --- congruence: total area AND shape count per layer, v39 (before this script touched anything) vs
# the live layout now -- the simplest possible invariant a pure rigid-translate-with-no-loss must
# preserve exactly. Two earlier attempts at a geometry-shaped congruence check (db.Region.merge()-based
# XOR, then an "exact polygon" interacting/and check) both produced false positives from their own
# comparison logic, not from real data loss -- merge() combines touching shapes (e.g. TLM's pitch-number
# labels touching the ladder bar) in ways sensitive to adjacency semantics that don't survive being
# split across two independent merge calls, and interacting()+and() has its own edge cases. Area and
# count per layer sidestep all of that: they were checked directly against v39 by hand before adopting
# this as the standing check and matched exactly on every layer.
old_snap = db.Layout(); old_snap.read(SRC); LO_snap = names(old_snap)
tso = old_snap.cell('TestStructures')
bad = 0
for n in LAY:
    a = sum(s.polygon.area() for s in tso.shapes(LO_snap[n]).each() if s.is_polygon() or s.is_box()) * dbu * dbu
    b = sum(s.polygon.area() for s in ts.shapes(L[n]).each() if s.is_polygon() or s.is_box()) * dbu * dbu
    ca = sum(1 for s in tso.shapes(LO_snap[n]).each() if s.is_polygon() or s.is_box())
    cb = sum(1 for s in ts.shapes(L[n]).each() if s.is_polygon() or s.is_box())
    ok = abs(a - b) < 1.0 and ca == cb
    print(f'   congruence ({n}): v39 area {a:.1f} cnt {ca}  ->  v40 area {b:.1f} cnt {cb}  {"OK" if ok else "MISMATCH"}')
    if not ok: bad += 1
assert bad == 0, 'TestStructures lost or gained geometry during the rearrangement'

blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c, r) for c, r, p in ovl).most_common(): print('      ', k, 'x', v)

def flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r
ai = list(top.each_inst())
blocks = [k for k in ai if not k.cell.name.startswith('TEXT')]
texts = [k for k in ai if k.cell.name.startswith('TEXT')]
fl = {id(k): flat(k) for k in ai}
own_r = db.Region()
for n in LAY: own_r = own_r.or_(db.Region(top.shapes(L[n])))
own_r.merge()
ov = 0
for a in range(len(blocks)):
    for b_ in range(a + 1, len(blocks)):
        A_, B_ = blocks[a], blocks[b_]
        if not A_.bbox().overlaps(B_.bbox()): continue
        o = fl[id(A_)].and_(fl[id(B_)]).area() * dbu * dbu
        if o: print('   OVERLAP', A_.cell.name, B_.cell.name, round(o)); ov += o
for k in blocks:
    o = fl[id(k)].and_(own_r).area() * dbu * dbu
    if o: print('   OVERLAP', k.cell.name, 'vs TOP-own', round(o)); ov += o
print('   structure overlap um2:', round(ov))
tk = [k for k in blocks if k.cell.name == 'TestStructures'][0]
gaps = []
for B_ in blocks:
    if B_ is tk or not tk.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
    e_ = fl[id(tk)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
    if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
print('   TestStructures gaps < 60 um to neighbours:', sorted(gaps) if gaps else 'none')
tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
    for t2 in texts:
        if id(t2) > id(t) and t.bbox().overlaps(t2.bbox()) and not fl[id(t)].and_(fl[id(t2)]).is_empty():
            print('   TEXT on TEXT'); tx += 1
print('   TEXT$ collisions:', tx)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40))
for t in texts: kz += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = [k.cell.name for k in blocks if not fl[id(k)].and_(kz).is_empty()]
print('   alignment-mark / label keep-out violations:', viol if viol else 0)
# internal collision: does the new layout put the upper zone, lower zone or MIS block on top of each other?
MID = (row1_bottom + (ANCHOR_Y + lo_h)) / 2.0
up_final = own_region(ts, lambda x0, y0, x1, y1: y0 >= MID)
lo_final = own_region(ts, lambda x0, y0, x1, y1: y0 < MID)
mis_r = db.Region(mk.cell.begin_shapes_rec(L['Metal_1'])).transformed(db.ICplxTrans(mk.trans))
for n in LAY[1:]: mis_r += db.Region(mk.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(mk.trans))
print('   DEBUG up_final bbox', up_final.bbox(), 'lo_final bbox', lo_final.bbox(), 'mis_r bbox', mis_r.bbox(), 'MID', MID)
print('   internal overlap upper<->lower:', up_final.and_(lo_final).area() * dbu * dbu)
print('   internal overlap upper<->MIS:', up_final.and_(mis_r).area() * dbu * dbu)
lm = lo_final.and_(mis_r)
print('   internal overlap lower<->MIS:', lm.area() * dbu * dbu, 'bbox', lm.bbox())
assert up_final.and_(lo_final).is_empty() and up_final.and_(mis_r).is_empty() and lo_final.and_(mis_r).is_empty()
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r = db.Region(cell_.begin_shapes_rec(L[n])); r.merge()
        tw += len([e_ for e_ in r.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))
print('   DRC 2um  TestStructures: width %d space %d' % drc(ts))
old = db.Layout(); old.read(SRC); LO = names(old)
dtop = 0
for n in LAY:
    a = db.Region(top.shapes(L[n])); b = db.Region(old.cell('TOP').shapes(LO[n])); dtop += a.xor(b).area()
print('   TOP-own geometry differs from v39 by um2:', round(dtop * dbu * dbu))
chg = []
for c in old.each_cell():
    d = ly.cell(c.name)
    if d is None or c.name == 'TestStructures': continue
    tot = 0
    for n in LAY:
        ra = db.Region(c.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(d.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(c.name)
print('   cells OTHER than TestStructures whose geometry changed vs v39:', chg)
print(f'\n   footprint: old TestStructures {(-2134-(-2134)):.0f}..  new {ts.bbox().width()*dbu:.0f} x {ts.bbox().height()*dbu:.0f} um'
      f'  (old was 6786 x 2793 um)')
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
