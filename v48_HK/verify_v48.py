# executed inside build_v48.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
def nonlabel_region(cell, lmap, n):
    r = db.Region()
    for s in cell.shapes(lmap[n]).each():
        if not (s.is_polygon() or s.is_box()): continue
        p = s.polygon
        if n == 'Metal_1' and isglyph(p) and p.bbox().bottom * dbu > 190: continue
        r.insert(p)
    r.merge(); return r

# ---- A: every gated-memristor junction core is byte-identical ----
for name in DEV14:
    for n in LAY:
        oa = nonlabel_region(old.cell(name), LO, n) & CORE_A
        na = nonlabel_region(ly.cell(name), L, n) & CORE_A
        assert oa.xor(na).is_empty(), (name, n, 'junction core changed')
print(f'   A: junction core (x80..176, y80..220) identical in all {len(DEV14)} gated memristors')

# ---- B: High-Value cores preserved, nothing lost; guard no longer on the TE net ----
hv_old = old.cell('MEM_HIGH_VALUE')
for (cx, cy), (ncx, ncy) in zip(OLDC, NEWC):
    bh, bv = coreboxes(cx, cy); nbh, nbv = coreboxes(ncx, ncy)
    for n in LAY:
        clip_o = bh + bv if n == 'Metal_3' else bh
        clip_n = nbh + nbv if n == 'Metal_3' else nbh
        oa = db.Region(hv_old.shapes(LO[n])); oa = oa & clip_o
        na = db.Region(hv.shapes(L[n])); na = (na & clip_n).moved(u(cx - ncx), u(cy - ncy))
        if n in ('Metal_2', 'IGZO', 'Isolation_1', PASS):
            assert oa.xor(na).is_empty(), ('HV core changed', cx, cy, n)
        else:  # M1/M3: the 5th-terminal route overlaps 3um back into its stub -> only require nothing lost
            assert (oa - na).is_empty(), ('HV core lost geometry', cx, cy, n)
# every device keeps exactly its original terminals: one passivation (probe) window per pad
def pads_per_device(cell, lmap, centres):
    cnt = [0] * len(centres)
    for p in db.Region(cell.shapes(lmap[PASS])).each():
        b = p.bbox(); x, y = (b.left + b.right) / 2 * dbu, (b.bottom + b.top) / 2 * dbu
        cnt[min(range(len(centres)), key=lambda k: (centres[k][0] - x) ** 2 + (centres[k][1] - y) ** 2)] += 1
    return cnt
po, pn = pads_per_device(hv_old, LO, OLDC), pads_per_device(hv, L, NEWC)
print('   B: probe pads per device  v47', po, ' v48', pn)
assert po == pn and sum(pn) == 38, 'a High-Value terminal was lost or added'
# the 5th pads stay on the same net as before: M1 gate net (series column), ring/TE net (GRD devices)
m1n = db.Region(hv.shapes(L['Metal_1'])); m1n.merge(); m3n = db.Region(hv.shapes(L['Metal_3'])); m3n.merge()
def probe(x, y): return db.Region(db.Box(u(x) - 500, u(y) - 500, u(x) + 500, u(y) + 500))
for i in range(4):
    ncx, ncy = NEWC[i]
    assert not (m1n.interacting(probe(ncx - 10, ncy - 20)) & probe(ncx - D5, ncy - D5)).is_empty(), ('gate pad disconnected', i)
for i in (4, 6):
    ncx, ncy = NEWC[i]
    assert not (m3n.interacting(probe(ncx, ncy + 50)) & probe(ncx + D5, ncy - D5)).is_empty(), ('guard pad disconnected', i)
print('   B: 8 device cores preserved; all 38 terminals kept, 5th pads on the same nets as in v47')

# ---- C: reorganised zone accounting (only the duplicate title + 8 bad windows may disappear) ----
ts_old = old.cell('TestStructures')
old_tot = Counter(); new_tot = Counter()
for n in LAY:
    for s in ts_old.shapes(LO[n]).each():
        if s.is_polygon() or s.is_box(): old_tot[n] += s.polygon.area() * dbu * dbu
    for s in old.cell('TOP').shapes(LO[n]).each():
        if (s.is_polygon() or s.is_box()) and gx_win.contains(s.bbox().p1) and gx_win.contains(s.bbox().p2):
            old_tot[n] += s.polygon.area() * dbu * dbu
    for s in ts.shapes(L[n]).each():
        if s.is_polygon() or s.is_box(): new_tot[n] += s.polygon.area() * dbu * dbu
exp = Counter(old_tot); exp['Metal_1'] -= title_area_um2; exp['Isolation_1'] -= 8 * 75.0 * 75.0
for n in LAY:
    assert abs(new_tot[n] - exp[n]) < 1.0, ('TestStructures area accounting', n, old_tot[n], new_tot[n], exp[n])
print('   C: TestStructures + Greek-cross shape areas account exactly (minus duplicate title, minus 8 gate-shorting windows)')

# ---- mask-wide: no Iso1 window may expose M1 under IGZO (channel/contact-to-gate short) ----
def R(c, n, rec=True):
    r = db.Region(c.begin_shapes_rec(L[n])) if rec else db.Region(c.shapes(L[n])); r.merge(); return r
bad = 0
for cn in sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')}) + ['__TOP__']:
    c, rec = (top, False) if cn == '__TOP__' else (ly.cell(cn), True)
    m1, ig = R(c, 'Metal_1', rec), R(c, 'IGZO', rec)
    i1 = db.Region(c.begin_shapes_rec(L['Isolation_1'])) if rec else db.Region(c.shapes(L['Isolation_1']))
    for p in i1.each():
        pr = db.Region(p)
        if not (pr & m1).is_empty() and not (pr & ig).is_empty(): bad += 1; print('   gate-short window in', cn, p.bbox())
print('   Iso1 windows exposing M1 under IGZO (mask-wide):', bad)
assert bad == 0

# ---- full standard suite ----
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c_, r) for c_, r, p in ovl).most_common(): print('      ', k, 'x', v)
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
for nm in ('Memristors_Gated', 'MEM_HIGH_VALUE', 'TestStructures'):
    kk = [k for k in blocks if k.cell.name == nm][0]
    gaps = []
    for B_ in blocks:
        if B_ is kk or not kk.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
        e_ = fl[id(kk)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
        if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
    print(f'   {nm} gaps < 60 um to neighbours:', sorted(gaps) if gaps else 'none')
tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
print('   TEXT$ collisions:', tx)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
for t in texts: kz += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = [k.cell.name for k in blocks if not fl[id(k)].and_(kz).is_empty()]
print('   alignment-mark keep-out violations:', viol if viol else 0)
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r_ = db.Region(cell_.begin_shapes_rec(L[n])); r_.merge()
        tw += len([e_ for e_ in r_.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r_.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d   (v42-v47 baseline 25 / 61)' % drc(top))
for nm in ('Memristors_Gated', 'MEM_HIGH_VALUE', 'TestStructures'):
    print(f'   DRC 2um  {nm}: width %d space %d' % drc(ly.cell(nm)))
intended = set(DEV14) | {'Memristors_Gated', 'MEM_HIGH_VALUE', 'TestStructures', 'TOP'}
chg = []
for cc in old.each_cell():
    if cc.name in intended: continue
    dd = ly.cell(cc.name)
    if dd is None: chg.append(cc.name + '(missing)'); continue
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells changed outside the intended set:', chg)
assert chg == []
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
