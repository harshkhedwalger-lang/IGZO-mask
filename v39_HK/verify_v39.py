# executed inside build_v39.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
con = A.connectivity(blocks_c + DEVICE_NAMES)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c + DEVICE_NAMES)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c, r) for c, r, p in ovl).most_common(): print('      ', k, 'x', v)

def nets_of(cell):
    polys = []; par = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for n in ('Metal_1', 'Metal_3'):
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
for n in DEVICE_NAMES[:6]:
    nets, pads = nets_of(ly.cell(n))
    if not (len(nets) == 3 and len(pads) == 3 and set(pads.values()) == {1}): bad += 1; print('   NET MISMATCH', n)
n_o, p_o = nets_of(ly.cell('MISv2_OPEN_S100'))
if not (len(n_o) == 3 and set(p_o.values()) == {1}): bad += 1; print('   NET MISMATCH open')
n_s, p_s = nets_of(ly.cell('MISv2_SHORT_S100'))
if not (len(n_s) == 2 and sorted(p_s.values()) == [1, 2]): bad += 1; print('   NET MISMATCH short')
print('   MIS device net topology unchanged by the move -- mismatches:', bad)
assert bad == 0

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
print('   TestStructures gaps < 60 um to neighbours after growing:', sorted(gaps) if gaps else 'none')
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
print('   TOP-own geometry differs from v38 by um2:', round(dtop * dbu * dbu))
chg = []
for c in old.each_cell():
    d = ly.cell(c.name)
    if d is None or c.name in ('TestStructures', 'MIS_Capacitors_v2'): continue
    tot = 0
    for n in LAY:
        ra = db.Region(c.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(d.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(c.name)
print('   cells OTHER than TestStructures/MIS_Capacitors_v2 whose geometry changed vs v38:', chg)
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
