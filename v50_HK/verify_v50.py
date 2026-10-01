# executed inside build_v50.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
def R(c, n, box=None):
    r = db.Region(c.shapes(L[n])); r.merge()
    return r if box is None else r & db.Region(box)
def B(x0, y0, x1, y1): return db.Box(u(x0), u(y0), u(x1), u(y1))
# ---- the overlap convention, measured from the drawn geometry ----
for name, (kind, a) in SPEC.items():
    c = ly.cell(name)
    if kind == 's':
        W, Lg, lov, _ = a; xi = W / 2 + WOV; yi = Lg / 2 + lov + EXT
        gate = R(c, 'Metal_1', B(-xi, -yi, xi, yi)).bbox()
        src = R(c, 'Metal_3', B(-W / 2, 0, W / 2, yi)).bbox(); drn = R(c, 'Metal_3', B(-W / 2, -yi, W / 2, 0)).bbox()
        ig = R(c, 'IGZO').bbox()
        ov_s = (gate.top - src.bottom) * dbu; ov_d = (drn.top - gate.bottom) * dbu
        Lm = (src.bottom - drn.top) * dbu; ext = (ig.top - gate.top) * dbu; Wm = src.width() * dbu
        assert abs(ov_s - lov) < 1e-3 and abs(ov_d - lov) < 1e-3 and abs(Lm - Lg) < 1e-3 and abs(ext - EXT) < 1e-3 and abs(Wm - W) < 1e-3, name
        # gate never under an electrode outside the overlap strips
        s_el = R(c, 'Metal_3', B(-W / 2, Lg / 2, W / 2, yi + EOUT)); d_el = R(c, 'Metal_3', B(-W / 2, -yi - EOUT, W / 2, -Lg / 2))
        g_all = R(c, 'Metal_1')
        assert abs((g_all & s_el).area() * dbu * dbu - lov * W) < 1 and abs((g_all & d_el).area() * dbu * dbu - lov * W) < 1, (name, 'extra gate/electrode overlap')
        print(f'   {name:18s} L={Lm:5.1f}  W={Wm:5.1f}  overlap S/D = {ov_s:.1f}/{ov_d:.1f} um  IGZO past gate = {ext:.1f} um')
    else:
        W, Lg, n, _ = a; Wf = W / n
        m3 = R(c, 'Metal_3', B(-2000, -Wf / 2 + 1, 2000, Wf / 2 - 1))
        ws = sorted(round(p.bbox().width() * dbu, 2) for p in m3.each())
        gate = R(c, 'Metal_1', B(-2000, -Wf / 2, 2000, Wf / 2)).bbox(); ig = R(c, 'IGZO').bbox()
        assert ws.count(5.0) == 2 and ws.count(10.0) == n - 1 and gate.left < ig.left and gate.right > ig.right, (name, ws)
        print(f'   {name:18s} {n} channels, fingers {ws[0]:.0f}/{ws[-1]:.0f} um (outer/inner) all on the gate -> 5 um per channel side')
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
for bname in ('PERF_TFT', 'SYN_1T1R'):
    c = ly.cell(bname); regs = {i.cell.name: flat(i) for i in c.each_inst()}; nm = list(regs); bad = 0
    for a_ in range(len(nm)):
        for b_ in range(a_ + 1, len(nm)):
            if not (regs[nm[a_]] & regs[nm[b_]]).is_empty() or regs[nm[a_]].separation_check(regs[nm[b_]], u(20), False, db.Region.Projection, None, None, None).count(): bad += 1
    print(f'   {bname}: device pairs overlapping or < 20 um apart: {bad}'); assert bad == 0
ai = list(top.each_inst())
blocks = [k for k in ai if not k.cell.name.startswith('TEXT')]
texts = [k for k in ai if k.cell.name.startswith('TEXT')]
fl = {id(k): flat(k) for k in ai}
own_r = db.Region()
for n in LAY: own_r = own_r.or_(db.Region(top.shapes(L[n])))
own_r.merge()
ov = 0
for a_ in range(len(blocks)):
    for b_ in range(a_ + 1, len(blocks)):
        A_, B_ = blocks[a_], blocks[b_]
        if not A_.bbox().overlaps(B_.bbox()): continue
        o = fl[id(A_)].and_(fl[id(B_)]).area() * dbu * dbu
        if o: print('   OVERLAP', A_.cell.name, B_.cell.name, round(o)); ov += o
for k in blocks:
    o = fl[id(k)].and_(own_r).area() * dbu * dbu
    if o: print('   OVERLAP', k.cell.name, 'vs TOP-own', round(o)); ov += o
print('   structure overlap um2:', round(ov))
for nm_ in ('PERF_TFT', 'SYN_1T1R'):
    kk = [k for k in blocks if k.cell.name == nm_][0]; gaps = []
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
print('   DRC 2um  TOP: width %d space %d   (baseline 25 / 61)' % drc(top))
print('   DRC 2um  PERF_TFT: width %d space %d' % drc(ly.cell('PERF_TFT')))
intended = set(SPEC) | {'PT_LOV5', 'PERF_TFT', 'TOP'}
chg = []
for cc in old.each_cell():
    if cc.name in intended: continue
    dd = ly.cell(cc.name); tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells changed outside the intended set:', chg)
assert chg == []
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
