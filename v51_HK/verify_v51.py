# executed inside build_v51.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
def R(c, n, box=None, rec=False):
    r = db.Region(c.begin_shapes_rec(L[n])) if rec else db.Region(c.shapes(L[n])); r.merge()
    return r if box is None else r & db.Region(box)
def B(x0, y0, x1, y1): return db.Box(u(x0), u(y0), u(x1), u(y1))

# ---- third rows: every new device measured against your convention ----
for cname, gl in (('Transistors_BottomGate', 'Metal_1'), ('Transistors_BottomGate_HfO2Only', 'Metal_2')):
    c = ly.cell(cname)
    for colc, Lnew, lab in NEWROW:
        win = B(colc - 337.5, 60 + ROWDY, colc + 337.5, 840 + ROWDY)
        g = R(c, gl, B(colc - 337.5, 400 + ROWDY, colc + 337.5, 700 + ROWDY)).bbox()   # gate strip inside the channel
        ig = R(c, 'IGZO', win).bbox()
        el = sorted([p.bbox() for p in R(c, 'Metal_3', B(colc - 337.5, 310 + ROWDY, colc + 337.5, 815 + ROWDY)).each()
                     if p.bbox().height() * dbu >= 490], key=lambda b: b.left)
        s_in, d_in = el[0].right * dbu, el[-1].left * dbu
        Lm, gw = d_in - s_in, g.width() * dbu
        ovl_s, ovl_d = s_in - g.left * dbu, g.right * dbu - d_in
        ext = (g.left - ig.left) * dbu
        assert abs(Lm - Lnew) < 1e-3 and abs(gw - (Lnew + 10)) < 1e-3 and abs(ovl_s - 5) < 1e-3 and abs(ovl_d - 5) < 1e-3 and abs(ext - 45) < 1e-3, (cname, colc)
        print(f'   {cname:32s} col {colc:7.1f}: L={Lm:.1f} gate={gw:.1f} overlap {ovl_s:.1f}/{ovl_d:.1f} IGZO past gate {ext:.1f} W={el[0].height()*dbu:.0f}')

# ---- novel devices: structure-specific checks ----
def dev(name): return ly.cell(name)
for nm_ in ('NV_4PR_M1', 'NV_4PR_M2'):
    c = dev(nm_); gl = 'Metal_1' if nm_.endswith('M1') else 'Metal_2'
    m3, ig, g = R(c, 'Metal_3'), R(c, 'IGZO'), R(c, gl)
    bare = (m3 & g) - ig - R(c, 'Isolation_1').sized(u(10))  # M3 on the gate with no IGZO in between (pad caps excluded)
    assert bare.is_empty(), (nm_, 'M3 directly over gate')
    assert (ig & R(c, 'Metal_3', B(85, -20, 95, 20))).area() > 0, nm_
    print(f'   {nm_}: probe tips on gated IGZO tabs, no M3 on bare gate dielectric')
for nm_ in ('NV_SPLIT_M1S', 'NV_SPLIT_M2S'):
    c = dev(nm_); ov = (R(c, 'Metal_1') & R(c, 'Metal_2')).bbox()
    assert abs(ov.height() * dbu - 4.0) < 1e-3, nm_
    assert ((R(c, 'Metal_3') & R(c, 'Metal_2')) - R(c, 'IGZO') - R(c, 'Isolation_1').sized(u(10))).is_empty(), (nm_, 'M3/HfO2/M2 junction')
    print(f'   {nm_}: M1/M2 gates overlap {ov.height()*dbu:.1f} um at the split (no ungated gap), no stray M3-on-M2')
for nm_ in ('NV_FG_R0', 'NV_FG_R2', 'NV_FG_R5', 'NV_FG_R2_PAD'):
    c = dev(nm_); fg = R(c, 'Metal_2', B(-400, -100, 70, 100)); cg = R(c, 'Metal_1', B(-400, -100, 70, 100))
    inside = (cg - fg).bbox().right * dbu <= fg.bbox().left * dbu   # CG leaves the FG only westwards (its lead)
    floating = R(c, 'Isolation_1').interacting(R(c, 'Metal_2').interacting(fg)).is_empty()
    assert inside and (floating != nm_.endswith('PAD')), nm_
    acg, ach = FGINFO[nm_]
    print(f'   {nm_:13s}: CG inside FG, FG {"floating" if floating else "on its own pad"}; A(CG-FG)/A(channel strip) = {acg/ach:.2f}')
for nm_ in ('NV_2T0C_L10', 'NV_2T0C_L50', 'NV_2T0C_CAL'):
    c = dev(nm_); m3 = R(c, 'Metal_3'); m2 = R(c, 'Metal_2'); i1 = R(c, 'Isolation_1', B(140, -10, 160, 10))
    sn_m3 = m3.interacting(db.Region(B(-1, -70, 1, -66)))           # net of the write-TFT drain
    assert not (sn_m3 & i1).is_empty() and not (m2.interacting(i1) & db.Region(B(300, -1, 340, 1))).is_empty(), nm_
    assert R(c, 'Metal_1', B(100, -200, 500, 200)).is_empty(), (nm_, 'M1 under the landing / read TFT')
    print(f'   {nm_}: write-TFT drain -> Iso1 landing on M2 -> read-TFT gate: connected; no M1 under the landing')

# ---- full standard suite (verniers excluded from the device rules, like ResolutionTests) ----
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests', 'OVL_VERNIERS'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c_, r) for c_, r, p in ovl).most_common(): print('      ', k, 'x', v)
# stack rule from v48: no Iso1 window may expose M1 under IGZO
bad = 0
for cn in blocks_c:
    c = ly.cell(cn); m1, ig = R(c, 'Metal_1', rec=True), R(c, 'IGZO', rec=True)
    for p in db.Region(c.begin_shapes_rec(L['Isolation_1'])).each():
        if not (db.Region(p) & m1 & ig).is_empty(): bad += 1
print('   Iso1 windows exposing M1 under IGZO:', bad); assert bad == 0
for bname in ('PERF_TFT', 'SYN_1T1R', 'NOVEL_DEVICES'):
    c = ly.cell(bname); regs = {i.cell.name: flat(i) for i in c.each_inst() if not i.cell.name.startswith('TEXT')}; nm = list(regs); bad = 0
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
for nm_ in ('PERF_TFT', 'SYN_1T1R', 'Transistors_BottomGate', 'Transistors_BottomGate_HfO2Only', 'NOVEL_DEVICES', 'OVL_VERNIERS'):
    kk = [k for k in blocks if k.cell.name == nm_][0]; gaps = []
    for B_ in blocks:
        if B_ is kk or not kk.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
        e_ = fl[id(kk)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
        if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
    print(f'   {nm_:32s} gaps < 60 um:', sorted(gaps) if gaps else 'none')
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
for nm_ in ('NOVEL_DEVICES', 'OVL_VERNIERS', 'Transistors_BottomGate', 'Transistors_BottomGate_HfO2Only', 'PERF_TFT'):
    print(f'   DRC 2um  {nm_}: width %d space %d' % drc(ly.cell(nm_)))
intended = {'PERF_TFT', 'SYN_1T1R', 'TOP', 'Transistors_BottomGate', 'Transistors_BottomGate_HfO2Only'} | set(DROP)
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
# original 12 devices of both W500 blocks untouched
for cname in ('Transistors_BottomGate', 'Transistors_BottomGate_HfO2Only'):
    for n in LAY:
        ra = db.Region(old.cell(cname).shapes(LO[n])); ra.merge()
        rb = db.Region(ly.cell(cname).shapes(L[n])) & db.Region(B(-3000, 60, 3000, 3000)); rb.merge()
        assert ra.xor(rb).is_empty(), (cname, n, 'original rows changed')
print('   original 12 devices of both W500 blocks unchanged')
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
