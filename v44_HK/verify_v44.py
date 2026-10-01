# executed inside build_v44.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)

# --- 1. the 4 removed blocks are actually gone ---
remaining_top = {k.cell.name for k in top.each_inst()}
remaining_ts = {k.cell.name for k in ts.each_inst()}
for nm in ('AL2O3_INTEGRITY', 'HFO2_MIM', 'SPLIT_CV'):
    assert nm not in remaining_top, f'{nm} still present in TOP'
assert 'MIS_CV_Block' not in remaining_ts, 'MIS_CV_Block still present in TestStructures'
print('   confirmed absent: AL2O3_INTEGRITY, HFO2_MIM, SPLIT_CV, MIS_CV_Block')

# --- 2. new GATE OXIDE 2 TESTS row doesn't overlap anything, incl. the Al2O3 row itself ---
def flat_region(cell_, layers_):
    r = db.Region()
    for n in layers_: r = r.or_(db.Region(cell_.begin_shapes_rec(L[n])))
    r.merge(); return r
new_r = db.Region()
# re-scan the target zone directly (two stacked 3-device sub-rows in the freed MIS_CV_Block space)
NEW_X0, NEW_X1 = X0_NEW - 10, X0_NEW + (2 * DEV_PITCH + DEV_W) + 10
NEW_Y0, NEW_Y1 = ROW_YLO - 10, ROW_YHI + ROW1_DY + 90
for n in ('Metal_2', 'Metal_3', 'Isolation_1', PASS):
    for s in ts.shapes(L[n]).each():
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        if b.left*dbu >= NEW_X0 and b.right*dbu <= NEW_X1 and b.bottom*dbu >= NEW_Y0 and b.top*dbu <= NEW_Y1:
            new_r.insert(s.polygon)
new_r.merge()
old_r = flat_region(ts, ('Metal_1', 'Isolation_1', 'Metal_2', PASS)).and_(
    db.Region(db.Box(u(ROW_X0 - 10), u(ROW_YLO - 10), u(ROW_X0 + 4130), u(ROW_YHI + 10))))
ov_self = new_r.and_(old_r).area() * dbu * dbu
print('   new row vs old Al2O3 row overlap um2:', ov_self)
assert ov_self == 0

blocks_now = [k for k in top.each_inst() if not k.cell.name.startswith('TEXT') and k.cell.name != 'ResolutionTests']
new_r_top = new_r  # already in TestStructures-local coords; need TOP coords for cross-block check
ts_inst = [k for k in top.each_inst() if k.cell.name == 'TestStructures'][0]
new_r_top = new_r.transformed(db.ICplxTrans(ts_inst.trans))
clash = 0
for k in blocks_now:
    if k.cell.name == 'TestStructures': continue
    fk = db.Region()
    for n in LAY: fk += db.Region(k.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(k.trans))
    o = new_r_top.and_(fk).area() * dbu * dbu
    if o: print('   NEW ROW OVERLAP vs', k.cell.name, o); clash += o
print('   new row overlap vs other TOP blocks um2:', clash)
assert clash == 0

crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
kzo = new_r_top.and_(kz).area() * dbu * dbu
print('   new row overlap vs alignment keepout um2:', kzo)
assert kzo == 0

# --- 3. congruence: Al2O3 row itself untouched, other cells untouched except TOP/TestStructures ---
old = db.Layout(); old.read(SRC); LO = names(old)
chg = []
for cc in old.each_cell():
    if cc.name in ('TOP', 'TestStructures'): continue
    dd = ly.cell(cc.name)
    if dd is None:
        continue
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells other than TOP/TestStructures whose geometry changed vs v43:', chg)
assert chg == []

old_row = flat_region(old.cell('TestStructures'), ('Metal_1', 'Isolation_1', 'Metal_2', PASS)).and_(
    db.Region(db.Box(u(ROW_X0 - 10), u(ROW_YLO - 10), u(ROW_X0 + 4130), u(ROW_YHI + 10))))
diff = old_row.xor(old_r).area() * dbu * dbu
print('   Al2O3 row geometry unchanged (xor area um2):', diff)
assert diff == 0

# --- 4. full standard suite ---
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
print('   DRC 2um  TOP: width %d space %d' % drc(top))
print('   DRC 2um  TestStructures: width %d space %d' % drc(ts))

ly.cleanup()
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
