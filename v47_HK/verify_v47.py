# executed inside build_v47.py / build_v47_part2.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)

# --- device-to-device overlap in the new grid, and label collisions ---
def flat_cell(cell_, trans=None):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(cell_.begin_shapes_rec(L[n])))
    r.merge()
    return r if trans is None else r.transformed(db.ICplxTrans(trans))
dev_regions = {name: flat_cell(ly.cell(name), db.Trans(u(tx), u(ty_y))) for name, (tx, ty_y) in targets.items()}
bad = 0
names_list = list(dev_regions)
for i in range(len(names_list)):
    for j in range(i + 1, len(names_list)):
        a, b_ = names_list[i], names_list[j]
        if not dev_regions[a].bbox().overlaps(dev_regions[b_].bbox()): continue
        o = dev_regions[a].and_(dev_regions[b_]).area() * dbu * dbu
        if o: print('   DEVICE OVERLAP', a, b_, o); bad += 1
print('   device-to-device overlaps:', bad)
assert bad == 0
label_r = db.Region()
for s in gm.shapes(L['Metal_1']).each():
    if s.is_polygon() and isglyph(s.polygon): label_r.insert(s.polygon)
lc = 0
for name, r in dev_regions.items():
    if not label_r.sized(u(5.0)).and_(r).is_empty(): print('   label touches', name); lc += 1
print('   label-to-device collisions:', lc)
assert lc == 0

# --- congruence: same 42 devices, channel-region geometry (the part I did NOT touch) unchanged ---
old = db.Layout(); old.read(SRC); LO = names(old)
new_names = {k.cell.name for k in gm.each_inst() if k.cell.name in DEV_NAMES}
print('   device set unchanged:', new_names == set(DEV_NAMES))
assert new_names == set(DEV_NAMES)
# the IGZO channel itself was never touched by the pad redesign -- must be byte-identical
for nm in DEV_NAMES:
    oc = old.cell(nm); nc = ly.cell(nm)
    oa = db.Region(oc.shapes(LO['IGZO'])); oa.merge()
    na = db.Region(nc.shapes(L['IGZO'])); na.merge()
    assert oa.xor(na).is_empty(), (nm, 'IGZO channel changed')
print(f'   IGZO channel geometry unchanged in all {len(DEV_NAMES)} devices')

if not placed:
    print('   !! block was not placed -- skipping die-level checks; not writing output')
else:
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
    mgk2 = [k for k in blocks if k.cell.name == 'Memristors_Gated'][0]
    print('   Memristors_Gated new TOP bbox', mgk2.bbox())
    gaps = []
    for B_ in blocks:
        if B_ is mgk2 or not mgk2.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
        e_ = fl[id(mgk2)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
        if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
    print('   Memristors_Gated gaps < 60 um to neighbours:', sorted(gaps) if gaps else 'none')
    tx = 0
    allb = own_r.dup()
    for k in blocks: allb = allb.or_(fl[id(k)])
    allb.merge()
    for t in texts:
        if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
    print('   TEXT$ collisions:', tx)
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
    print('   DRC 2um  Memristors_Gated: width %d space %d' % drc(gm))
    chg = []
    for cc in old.each_cell():
        if cc.name == 'Memristors_Gated' or cc.name in DEV_NAMES: continue
        dd = ly.cell(cc.name)
        if dd is None: continue
        tot = 0
        for n in LAY:
            ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
            rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
        if tot: chg.append(cc.name)
    print('   cells other than Memristors_Gated/its 42 devices whose geometry changed vs v46:', chg)
    print('   (device-redesign checks passed; continuing to row1 tidy-up before writing output)')
