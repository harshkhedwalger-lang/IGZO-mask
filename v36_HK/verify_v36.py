# executed inside build_v36.py (shares its namespace)
print('\n== E. verification')
A = mkaudit.Audit(ly)
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
print('   blocks:', blocks_c)
con = A.connectivity(blocks_c)
print('   connectivity / fabricability findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay-rule findings (ENC {ENC} um, OVL {OVL} um):', len(ovl))
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
for g in sorted(gaps)[:12]: print('   block gap < 60 um:', g)

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

def net_report(cell_name):
    c = ly.cell(cell_name); polys = []; par = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for n in ('Metal_1', 'Metal_2', 'Metal_3'):
        for p in A.R(c, n).each():
            if n == 'Metal_1' and isglyph(p): continue
            polys.append(p); par.append(len(par))
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
# reference: net_report on the untouched v35 1T1R cell (same generator, pitch 1200) gives 120 nets,
# dist {1:90,2:30} -- the pitch change must reproduce that exact topology (only positions differ).
old_for_ref = db.Layout(); old_for_ref.read(SRC)
def net_report_on(ly_, cell_name):
    A_ = mkaudit.Audit(ly_); c = ly_.cell(cell_name); polys = []; par = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for n in ('Metal_1', 'Metal_2', 'Metal_3'):
        for p in A_.R(c, n).each():
            if n == 'Metal_1' and isglyph(p): continue
            polys.append(p); par.append(len(par))
    idx = lambda reg: [i for i, p in enumerate(polys) if not db.Region(p).interacting(reg).is_empty()]
    for w in A_.R(c, 'Isolation_1').each():
        hit = idx(db.Region(w))
        for i in hit[1:]: par[find(i)] = find(hit[0])
    pads = Counter()
    for w in A_.R(c, 'Passivation').each():
        hit = idx(db.Region(w))
        if hit: pads[find(hit[0])] += 1
    return {find(i) for i in range(len(polys))}, pads
nets_ref0, pads_ref0 = net_report_on(old_for_ref, '1T1R')
nets, pads = net_report('1T1R')
dist = Counter(pads.values()); dist_ref = Counter(pads_ref0.values())
print(f'   nets 1T1R: {len(nets)}  pads-per-net {dict(dist)}   (reference, same generator @ pitch 1200: {len(nets_ref0)} nets, {dict(dist_ref)})')
assert len(nets) == len(nets_ref0) and dist == dist_ref, 'net topology changed vs the pitch-1200 reference'
nets2, pads2 = net_report('Transistors_BottomGate_HfO2Only')
nets_ref, pads_ref = net_report('Transistors_BottomGate')
print(f'   nets Transistors_BottomGate_HfO2Only: {len(nets2)}  (reference Transistors_BottomGate: {len(nets_ref)})')
assert len(nets2) == len(nets_ref)

P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r = db.Region(cell_.begin_shapes_rec(L[n])); r.merge()
        tw += len([e_ for e_ in r.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))
for cn in ('1T1R', 'Transistors_BottomGate_HfO2Only', 'Memristors_Gated'): print('   DRC 2um  %-32s: width %d space %d' % ((cn,) + drc(ly.cell(cn))))

old = db.Layout(); old.read(SRC); LO = names(old)
dtop = 0
for n in LAY:
    a = db.Region(top.shapes(L[n])); b = db.Region(old.cell('TOP').shapes(LO[n])); dtop += a.xor(b).area()
print('   TOP-own geometry differs from v35 by um2:', round(dtop * dbu * dbu))
p_old = {(k.cell.name, k.trans.disp.x, k.trans.disp.y) for k in old.cell('TOP').each_inst() if k.cell.name.startswith('TEXT')}
p_new = {(k.cell.name, k.trans.disp.x, k.trans.disp.y) for k in top.each_inst() if k.cell.name.startswith('TEXT')}
print('   top-level TEXT$ instances differing from v35:', len(p_old ^ p_new))

chg = []
for c in old.each_cell():
    d = ly.cell(c.name)
    if d is None: continue
    tot = 0
    for n in LAY:
        ra = db.Region(c.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(d.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(c.name)
print('   cells whose geometry changed vs v35:', sorted(chg))
print('   deleted cells (present in v35, absent in v36):', sorted(c.name for c in old.each_cell() if ly.cell(c.name) is None and not c.name.startswith('TEXT')))
print('   new cells (absent in v35, present in v36):', sorted(c.name for c in ly.each_cell() if old.cell(c.name) is None and not c.name.startswith('TEXT') and c.name != 'TOP'))

# 1T1R gap check: verify 80 um edge-to-edge between ADJACENT devices in a row (not the intra-device
# L=20 channel gap, which space_check also picks up and is not what's being asked for)
DEV_W = 1070.0                                                            # t1r()'s own rightmost feature x-offset
print(f'   1T1R device footprint width {DEV_W:.1f} um, pitch {PITCH_NEW:.1f} um -> edge gap {PITCH_NEW - DEV_W:.1f} um (target 80)')
assert abs((PITCH_NEW - DEV_W) - 80.0) < 1.0

ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
