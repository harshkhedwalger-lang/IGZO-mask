# executed inside build_v49.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
for bname in ('PERF_TFT', 'SYN_1T1R'):
    c = ly.cell(bname)
    assert sorted(i.cell.name for i in c.each_inst()) == sorted(ORDER[bname])
    regs = {i.cell.name: flat(i) for i in c.each_inst()}
    nm = list(regs); ov = 0
    for a in range(len(nm)):
        for b_ in range(a + 1, len(nm)):
            e_ = regs[nm[a]].separation_check(regs[nm[b_]], u(20), False, db.Region.Projection, None, None, None)
            if not (regs[nm[a]] & regs[nm[b_]]).is_empty() or e_.count(): ov += 1; print('   too close:', bname, nm[a], nm[b_])
    print(f'   {bname}: {len(nm)} devices, device pairs overlapping or < 20 um apart: {ov}')
    assert ov == 0
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c_, r) for c_, r, p in ovl).most_common(): print('      ', k, 'x', v)
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
for nm_ in ('PERF_TFT', 'SYN_1T1R', 'STEP_COVERAGE'):
    kk = [k for k in blocks if k.cell.name == nm_][0]
    gaps = []
    for B_ in blocks:
        if B_ is kk or not kk.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
        e_ = fl[id(kk)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
        if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
    print(f'   {nm_} gaps < 60 um to neighbours:', sorted(gaps) if gaps else 'none')
tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
print('   TEXT$ collisions:', tx)
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
print('   DRC 2um  TOP: width %d space %d   (baseline 25 / 61)' % drc(top))
intended = {'PERF_TFT', 'SYN_1T1R', 'TOP'}
chg = []
for cc in old.each_cell():
    if cc.name in intended: continue
    dd = ly.cell(cc.name)
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells changed outside the intended set:', chg)
assert chg == []
for bname in ('PERF_TFT', 'SYN_1T1R'):
    a_ = db.Region(old.cell(bname).begin_shapes_rec(LO['Metal_1'])).area(); b2 = db.Region(ly.cell(bname).begin_shapes_rec(L['Metal_1'])).area()
    assert a_ == b2, (bname, 'M1 area changed')
print('   PERF_TFT / SYN_1T1R content congruent (rigid instance moves only)')
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
