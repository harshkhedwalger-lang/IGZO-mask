# executed inside build_v45.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)

def flat_region(cell_, layers_):
    r = db.Region()
    for n in layers_: r = r.or_(db.Region(cell_.begin_shapes_rec(L[n])))
    r.merge(); return r

# --- 1. MIS_CV_Block is back ---
assert 'MIS_CV_Block' in {k.cell.name for k in ts.each_inst()}, 'MIS_CV_Block was not restored'
print('   MIS_CV_Block present: yes')

# --- 2. no internal overlaps among the 4 moved/new pieces, or vs MIS_CV_Block, within TestStructures ---
def region_in_zone(x0, x1, y0, y1, layers_):
    r = db.Region()
    for n in layers_:
        for s in ts.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if b.left*dbu >= x0 and b.right*dbu <= x1 and b.bottom*dbu >= y0 and b.top*dbu <= y1:
                r.insert(s.polygon)
    r.merge(); return r

r_row1 = region_in_zone(-2200, 1600, row1_bottom - 5, row1_top + 5, ('Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS))
r_row2 = region_in_zone(ROW_X0 + dx_ox - 5, ROW_X0 + dx_ox + 4130, row2_bottom - 5, row2_top + 5, ('Metal_1', 'Isolation_1', 'Metal_2', PASS))
r_row3 = region_in_zone(ROW_X0 + dx_ox - 5, ROW_X0 + dx_ox + 4130, row3_bottom - 5, row3_top + 5, ('Metal_2', 'Isolation_1', 'Metal_3', PASS))
r_mis = flat_region(ly.cell('MIS_CV_Block'), LAY).transformed(mis_trans)
pairs = [('row1(TLM+GX)', r_row1, 'row2(OXIDE1)', r_row2), ('row2(OXIDE1)', r_row2, 'row3(OXIDE2)', r_row3),
         ('row3(OXIDE2)', r_row3, 'MIS_CV_Block', r_mis), ('row2(OXIDE1)', r_row2, 'MIS_CV_Block', r_mis),
         ('row1(TLM+GX)', r_row1, 'MIS_CV_Block', r_mis)]
bad = 0
for na, ra, nb, rb in pairs:
    o = ra.and_(rb).area() * dbu * dbu
    print(f'   {na} vs {nb} overlap um2:', o)
    if o: bad += 1
assert bad == 0

# --- 3. congruence: GATE OXIDE 1's own geometry is bit-for-bit the same shape, just moved ---
old = db.Layout(); old.read(SRC); LO = names(old)
old_ts = old.cell('TestStructures')
def own_region_in_zone(cell_, x0, x1, y0, y1, layers_, layermap):
    r = db.Region()
    for n in layers_:
        for s in cell_.shapes(layermap[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if b.left * dbu >= x0 and b.right * dbu <= x1 and b.bottom * dbu >= y0 and b.top * dbu <= y1:
                r.insert(s.polygon)
    r.merge(); return r
# own-shapes-only on both sides (labels are separate child-cell instances, moved by construction,
# not compared here -- they're identical cell instances by design, just re-transformed)
old_ox1 = own_region_in_zone(old_ts, ROW_X0 - 10, ROW_X0 + 4130, ROW_YLO - 10, ROW_YHI + 10,
                              ('Metal_1', 'Isolation_1', 'Metal_2', PASS), LO)
new_ox1 = r_row2.transformed(db.Trans(-u(dx_ox), -u(dy_ox1)))   # shift back to compare like-for-like
diff = old_ox1.xor(new_ox1).area() * dbu * dbu
print('   GATE OXIDE 1 geometry congruent after un-shifting (xor area um2):', diff)
if diff:
    print('   DEBUG old_ox1 bbox', old_ox1.bbox(), 'area', old_ox1.area()*dbu*dbu)
    print('   DEBUG new_ox1 bbox', new_ox1.bbox(), 'area', new_ox1.area()*dbu*dbu)
    xr = old_ox1.xor(new_ox1)
    only_old = old_ox1.and_(xr)
    only_new = new_ox1.and_(xr)
    print('   DEBUG only-in-old area', only_old.area()*dbu*dbu, 'bbox', only_old.bbox())
    print('   DEBUG only-in-new area', only_new.area()*dbu*dbu, 'bbox', only_new.bbox())
    for p in list(only_old.each())[:5]: print('      old-only poly bbox', p.bbox())
    for p in list(only_new.each())[:5]: print('      new-only poly bbox', p.bbox())
assert diff == 0

old_top = own_region_in_zone(old_ts, -2200, 1600, ROW_YHI, 300,
                              ('Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS), LO)
# live shifted geometry minus the brand-new Greek-cross title (which has no old-baseline
# counterpart by definition), shifted back down -- should exactly match the old baseline
new_top_live = r_row1 - gx_title_region
new_top_shifted_back = new_top_live.transformed(db.Trans(0, -u(dy_top)))
diff2 = old_top.xor(new_top_shifted_back).area() * dbu * dbu
print('   TLM+GreekCross geometry congruent after un-shifting (xor area um2):', diff2)
if diff2:
    xr2 = old_top.xor(captured_r)
    o2 = old_top.and_(xr2); n2 = captured_r.and_(xr2)
    print('   DEBUG only-in-old area', o2.area()*dbu*dbu)
    for p in list(o2.each())[:8]: print('      old-only poly bbox', p.bbox())
    print('   DEBUG only-in-new area', n2.area()*dbu*dbu)
    for p in list(n2.each())[:8]: print('      new-only poly bbox', p.bbox())
assert diff2 == 0

chg = []
for cc in old.each_cell():
    if cc.name in ('TOP', 'TestStructures'): continue
    dd = ly.cell(cc.name)
    if dd is None: continue
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells other than TOP/TestStructures whose geometry changed vs v44:', chg)
assert chg == []

# --- 4. TestStructures vs the rest of the die: no new collisions, no keepout violation ---
ts_r_all = flat_region(ts, LAY)
ts_r_top = ts_r_all.transformed(db.ICplxTrans(ts_inst.trans))
blocks_now = [k for k in top.each_inst() if not k.cell.name.startswith('TEXT') and k.cell.name not in ('ResolutionTests', 'TestStructures')]
clash = 0
for k in blocks_now:
    fk = db.Region()
    for n in LAY: fk += db.Region(k.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(k.trans))
    o = ts_r_top.and_(fk).area() * dbu * dbu
    if o: print('   TestStructures OVERLAP vs', k.cell.name, o); clash += o
print('   TestStructures overlap vs other TOP blocks um2:', clash)
assert clash == 0
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
kzo = ts_r_top.and_(kz).area() * dbu * dbu
print('   TestStructures overlap vs alignment keepout um2:', kzo)
assert kzo == 0

# --- 5. full standard suite ---
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

ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
