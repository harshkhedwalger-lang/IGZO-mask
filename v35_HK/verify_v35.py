# executed inside build_v35.py (shares its namespace)
print('\n== E. verification')
A = mkaudit.Audit(ly)
print('   layers in file:', sorted(names(ly).keys()), ' Metal_4 present:', 'Metal_4' in names(ly))
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests', 'RESERVED_AREA'})
con = A.connectivity(blocks_c)
print('   connectivity / fabricability findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay-rule findings (ENC {ENC} um, OVL {OVL} um):', len(ovl))
for k, v in Counter((c, r) for c, r, p in ovl).most_common(): print('      ', k, 'x', v)

def net_report(cell_name):
    """union-find net extraction: M1/M2/M3 polygons, joined where an Iso1 window touches two of them.
       returns {net: probe-pad windows (Passivation) on that net}"""
    c = ly.cell(cell_name); polys = []; par = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    lay_of = []
    for n in ('Metal_1', 'Metal_2', 'Metal_3'):
        for p in A.R(c, n).each():
            if n == 'Metal_1' and A.isglyph(p): continue                  # label text is not a net
            polys.append(p); par.append(len(par)); lay_of.append(n)
    idx = lambda reg: [i for i, p in enumerate(polys) if not db.Region(p).interacting(reg).is_empty()]
    for w in A.R(c, 'Isolation_1').each():
        hit = idx(db.Region(w))
        for i in hit[1:]: par[find(i)] = find(hit[0])
    pads = Counter()
    for w in A.R(c, PASS).each():
        hit = idx(db.Region(w))
        if hit: pads[find(hit[0])] += 1
    nets = {find(i) for i in range(len(polys))}
    return nets, pads
for cn, per_dev, ndev in (('1T1R_WSWEEP', 4, 12), ('1T1R_LSWEEP', 4, 6)):
    nets, pads = net_report(cn)
    dist = Counter(pads.values())
    print(f'   nets {cn}: {len(nets)} (expect {per_dev * ndev} = {ndev} devices x G,S,D/BE,TE)  pads per net {dict(dist)}  (expect {ndev}x1 G, {ndev}x1 S, {ndev}x2 D/BE, {ndev}x1 TE)')
    assert len(nets) == per_dev * ndev and dist == Counter({1: 3 * ndev, 2: ndev}), 'net extraction mismatch in ' + cn
nets, pads = net_report('HFO2_TDDB')
print(f'   nets HFO2_TDDB: {len(nets)} (expect 32 = 30 TE + 2 BE buses)  BE nets carry {sorted(v for v in pads.values() if v > 1)} pads (expect [2, 2])')
assert len(nets) == 32 and sorted(v for v in pads.values() if v > 1) == [2, 2]

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
for a in range(len(blocks)):
    for b in range(a + 1, len(blocks)):
        A_, B_ = blocks[a], blocks[b]
        if not A_.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
        e_ = fl[id(A_)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
        if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), A_.cell.name, B_.cell.name))
for g in sorted(gaps)[:10]: print('   block gap < 60 um:', g)
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
tx = 0
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
    for t2 in texts:
        if id(t2) > id(t) and t.bbox().overlaps(t2.bbox()) and not fl[id(t)].and_(fl[id(t2)]).is_empty(): print('   TEXT on TEXT'); tx += 1
print('   TEXT$ collisions:', tx)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40))
kz_l = db.Region()
for t in texts: kz_l += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = 0
for k in blocks:
    for zn, z in (('mark', kz), ('mark label', kz_l)):
        o = fl[id(k)].and_(z).area() * dbu * dbu
        if o: print('   block in alignment %s zone: %s %.0f um2' % (zn, k.cell.name, o)); viol += 1
print('   alignment-mark clearance violations:', viol)

def isg(p):
    b_ = p.bbox(); return b_.height() * dbu <= 40 and b_.width() * dbu <= 120 and p.area() * dbu * dbu < 1500
tc = 0
for cn in ('1T1R_WSWEEP', '1T1R_LSWEEP', 'HFO2_TDDB', 'RESERVED_AREA', 'MEM_ASYM', 'MEM_HIGH_VALUE', 'MEM_STACK_SPLIT', 'SPLIT_CV'):
    c = ly.cell(cn)
    gl = []; ob = db.Region()
    for s in c.shapes(L['Metal_1']).each():
        if not (s.is_polygon() or s.is_box()): continue
        if isg(s.polygon): gl.append(s.polygon)
        else: ob.insert(s.polygon)
    for n in LAY[1:]: ob += db.Region(c.begin_shapes_rec(L[n]))
    ob.merge()
    if not gl: continue
    words = db.Region(gl).sized(u(20), 0); words.merge()
    for w in words.each():
        grp = db.Region([g for g in gl if db.Region(w).interacting(db.Region(g)).count()])
        if grp.count() >= 3 and not grp.interacting(ob).is_empty():
            tc += 1; print('   label touches structure in', cn, grp.bbox())
print('   in-block label collisions:', tc)

P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r = db.Region(cell_.begin_shapes_rec(L[n])); r.merge()
        tw += len([e_ for e_ in r.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))
for cn in ('1T1R_WSWEEP', '1T1R_LSWEEP', 'HFO2_TDDB'): print('   DRC 2um  %-13s: width %d space %d' % ((cn,) + drc(ly.cell(cn))))

old = db.Layout(); old.read(SRC); LO = names(old)
def oname(n): return 'Isolation_2' if n == PASS else n
def drc_marks(lay, LL, cell_, passname):
    out = set()
    for n in LAY:
        nn = passname if n == PASS else n
        r = db.Region(cell_.begin_shapes_rec(LL[nn])); r.merge()
        for kind, chk in (('W', r.width_check(u(MINF), False, P2, None, None, None)), ('S', r.space_check(u(MINF), False, P2, None, None, None))):
            for e_ in chk.each():
                if .05 < e_.distance() * dbu < lim:
                    b_ = e_.bbox(); out.add((n, kind, round(b_.left * dbu), round(b_.bottom * dbu)))
    return out
m_new = drc_marks(ly, L, top, PASS); m_old = drc_marks(old, LO, old.cell('TOP'), 'Isolation_2')
fresh = sorted(m for m in m_new if m not in m_old and not any(abs(m[2] - o[2]) < 3 and abs(m[3] - o[3]) < 3 and m[:2] == o[:2] for o in m_old))
print('   DRC markers new vs v34 (excluding removed structures): %d' % len(fresh))
for m in fresh[:15]: print('      ', m)
dtop = 0
for n in LAY:
    a = db.Region(top.shapes(L[n])); b = db.Region(old.cell('TOP').shapes(LO[oname(n)])); dtop += a.xor(b).area()
print('   TOP-own geometry differs from v34 by um2:', round(dtop * dbu * dbu))
p_old = {(k.cell.name, k.trans.disp.x, k.trans.disp.y) for k in old.cell('TOP').each_inst() if k.cell.name.startswith('TEXT')}
p_new = {(k.cell.name, k.trans.disp.x, k.trans.disp.y) for k in top.each_inst() if k.cell.name.startswith('TEXT')}
print('   TEXT$ instances differing from v34/v22:', len(p_old ^ p_new))
chg = []
for c in old.each_cell():
    d = ly.cell(c.name)
    if d is None: continue
    tot = 0
    for n in LAY:
        ra = db.Region(c.begin_shapes_rec(LO[oname(n)])); ra.merge()
        rb = db.Region(d.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(c.name)
print('   cells whose geometry changed vs v34:', sorted(chg))
print('   remaining Transistors_BottomGate IGZO islands:', db.Region(ly.cell('Transistors_BottomGate').begin_shapes_rec(L['IGZO'])).count())
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
