# executed inside build_v37.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
new_leaf = [c.name for c in SYN + PERF]
con = A.connectivity(blocks_c + new_leaf)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c + new_leaf)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c, r) for c, r, p in ovl).most_common(): print('      ', k, 'x', v)

def nets_of(cell):
    polys = []; par = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for n in ('Metal_1', 'Metal_2', 'Metal_3'):
        for p in A.R(cell, n).each():
            if n == 'Metal_1' and isglyph(p): continue
            polys.append(p); par.append(len(par))
    idx = lambda reg: [i for i, p in enumerate(polys) if not db.Region(p).interacting(reg).is_empty()]
    for w in A.R(cell, 'Isolation_1').each():
        hit = idx(db.Region(w))
        for i in hit[1:]: par[find(i)] = find(hit[0])
    pads = Counter()
    for w in A.R(cell, PASS).each():
        hit = idx(db.Region(w))
        if hit: pads[find(hit[0])] += 1
    return {find(i) for i in range(len(polys))}, pads
bad = 0
for c in SYN + PERF:
    nets, pads = nets_of(c)
    want = 4 if c in SYN else 3
    ok = len(nets) == want and len(pads) == want and set(pads.values()) == {1}
    if not ok: bad += 1; print('   NET MISMATCH', c.name, len(nets), dict(pads))
print(f'   net extraction: {len(SYN)} synapse cells (4 nets, 1 pad each), {len(PERF)} TFT cells (3 nets, 1 pad each), mismatches {bad}')
assert bad == 0

# memristor area + TFT W, L re-measured from geometry (not from the parameters)
for c in SYN[:2] + PERF[:1]:
    ig = A.R(c, 'IGZO'); islands = sorted(ig.each(), key=lambda p: -p.area())
    ch = islands[0].bbox()
    m1 = A.R(c, 'Metal_1')
    print(f'   {c.name}: channel IGZO {ch.width()*dbu:.0f} x {ch.height()*dbu:.0f} um', end='')
    if c in SYN:
        j = A.R(c, 'Metal_2').and_(A.R(c, 'Metal_3')).and_(ig)
        print(f', memristor junction area {j.area()*dbu*dbu:.1f} um2', end='')
    print()

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
    for b in range(a + 1, len(blocks)):
        A_, B_ = blocks[a], blocks[b]
        if not A_.bbox().overlaps(B_.bbox()): continue
        o = fl[id(A_)].and_(fl[id(B_)]).area() * dbu * dbu
        if o: print('   OVERLAP', A_.cell.name, B_.cell.name, round(o)); ov += o
for k in blocks:
    o = fl[id(k)].and_(own_r).area() * dbu * dbu
    if o: print('   OVERLAP', k.cell.name, 'vs TOP-own', round(o)); ov += o
print('   structure overlap um2:', round(ov))
gaps = []
for k in [b_ for b_ in blocks if b_.cell.name in ('SYN_1T1R', 'PERF_TFT')]:
    for B_ in blocks:
        if B_ is k or not k.bbox().enlarged(u(80), u(80)).overlaps(B_.bbox()): continue
        e_ = fl[id(k)].separation_check(fl[id(B_)], u(80), False, db.Region.Projection, None, None, None)
        if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), k.cell.name, B_.cell.name))
print('   new-block gaps < 80 um to neighbours:', sorted(gaps) if gaps else 'none')
tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
print('   TEXT$ collisions:', tx)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40))
for t in texts: kz += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = [k.cell.name for k in blocks if not fl[id(k)].and_(kz).is_empty()]
print('   alignment-mark / label keep-out violations:', viol if viol else 0)
# labels inside the new cells must not touch device geometry
lc = 0
for c in SYN + PERF + [syn, perf]:
    lab = LABELS.get(c.name)
    if lab is None: continue
    ob = db.Region()
    for n in LAY: ob += db.Region(c.begin_shapes_rec(L[n]))
    ob -= lab                                                     # everything except the label itself
    d = lab.sized(u(10)).and_(ob)                                 # require >= 10 um clearance
    if not d.is_empty(): lc += 1; print('   label within 10 um of structure in', c.name, d.bbox())
print('   in-cell label collisions:', lc)
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r = db.Region(cell_.begin_shapes_rec(L[n])); r.merge()
        tw += len([e_ for e_ in r.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))
for c in (syn, perf): print('   DRC 2um  %-9s: width %d space %d' % ((c.name,) + drc(c)))
old = db.Layout(); old.read(SRC); LO = names(old)
chg = []
for c in old.each_cell():
    d = ly.cell(c.name); tot = 0
    for n in LAY:
        ra = db.Region(c.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(d.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(c.name)
print('   existing cells whose geometry changed vs v36:', chg)
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
