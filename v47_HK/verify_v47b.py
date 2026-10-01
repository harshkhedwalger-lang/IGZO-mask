# executed inside build_v47_part3.py (shares its namespace)
print('\n== final verification (device redesign + row1 tidy-up together)')

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
fl = {}
for k in ai: fl[id(k)] = flat(k)
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

tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
print('   TEXT$ collisions:', tx)
crosses2 = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz2 = db.Region(crosses2).sized(u(40.0))
for t in texts: kz2 += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = [k.cell.name for k in blocks if not fl[id(k)].and_(kz2).is_empty()]
print('   alignment-mark keep-out violations:', viol if viol else 0)

P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r_ = db.Region(cell_.begin_shapes_rec(L[n])); r_.merge()
        tw += len([e_ for e_ in r_.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r_.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))

chg = []
for cc in old.each_cell():
    if cc.name in ('Memristors_Gated', 'TestStructures', 'TOP') or cc.name in DEV_NAMES: continue
    dd = ly.cell(cc.name)
    if dd is None: continue
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells other than Memristors_Gated/TestStructures/its devices whose geometry changed vs v46:', chg)

ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
