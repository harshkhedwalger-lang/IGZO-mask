# executed inside build_v52.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
def B(x0, y0, x1, y1): return db.Box(u(x0), u(y0), u(x1), u(y1))
textcells = [c.cell_index() for c in ly.each_cell() if is_text(c)]

# ---- T1: no polygon text left in any placed cell
left_std = []
for ci in sorted(placed):
    if not ly.is_valid_cell_index(ci): continue
    c = ly.cell(ci)
    if is_text(c) or c.name in EXEMPT_CELLS: continue
    for n in LAY:
        if not c.shapes(L[n]).is_empty():
            left_std += [(c.name, s) for s, *_ in textocr.find_text(c, L[n], dbu)]
print('   polygon text lines left (std_font):', left_std); assert not left_std

# ---- T2: every text instance is an editable Basic.TEXT PCell at a standard size
def text_instances(c, t=db.ICplxTrans(), path=()):
    for k in c.each_inst():
        for el in k.cell_inst.each_cplx_trans():
            tt = t * el
            if is_text(k.cell): yield k.cell, tt, path + (c.name,)
            else: yield from text_instances(k.cell, tt, path + (c.name,))
TI = list(text_instances(top))
bad = [(cc.name, p[-1]) for cc, tt, p in TI if not (cc.is_pcell_variant() and cc.pcell_declaration().name() == 'TEXT')]
print('   text instances:', len(TI), ' non-PCell:', bad); assert not bad
mags = Counter()
for cc, tt, p in TI:
    pr = cc.pcell_parameters_by_name(); m = pr['mag']
    exempt = pr['text'].upper() in EXEMPT_STR or 'ResolutionTests' in p
    mags[('exempt ' if exempt else '') + f'mag {m:g}'] += 1
    assert exempt or m in MAG.values(), (pr['text'], m, p)
    assert exempt or pr['text'] == pr['text'].upper(), pr['text']
print('   sizes:', dict(mags))

# ---- T3: clearance  text <-> structures >= 10 um, text <-> text >= 8 um (ResolutionTests artwork exempt)
it = top.begin_shapes_rec(L['Metal_1'])
nontext = db.Region()
for n in LAY:
    it = top.begin_shapes_rec(L[n]); it.unselect_cells(textcells); nontext += db.Region(it)
nontext.merge()
boxes = []
for cc, tt, p in TI:
    if 'ResolutionTests' in p: continue
    pr = cc.pcell_parameters_by_name()
    r = db.Region(cc.begin_shapes_rec(ly.find_layer(pr['layer']))).transformed(tt)
    boxes.append((pr['text'], p[-1], r))
viol = []
for s, owner, r in boxes:
    near = nontext & db.Region(r.bbox().enlarged(u(12), u(12)))
    if not (r & near).is_empty(): viol.append(('ON STRUCTURE', owner, s))
    elif r.separation_check(near, u(10), False, db.Region.Projection, None, None, None).count(): viol.append(('<10um to structure', owner, s))
tb_ = sorted([(r.bbox(), s, o) for s, o, r in boxes], key=lambda x: x[0].left)
for a in range(len(tb_)):
    for b2 in range(a + 1, len(tb_)):
        if tb_[b2][0].left > tb_[a][0].right + u(8): break
        if tb_[a][0].enlarged(u(3.99), u(3.99)).overlaps(tb_[b2][0].enlarged(u(3.99), u(3.99))):
            viol.append(('text-text <8um', tb_[a][2] + '/' + tb_[b2][2], tb_[a][1] + ' | ' + tb_[b2][1]))
print('   text clearance violations:', len(viol))
for v in viol: print('      ', v)

# ---- 1T1R row and ResolutionTests
fr = sorted({round(s.bbox().left * dbu) for s in ly.cell('1T1R').shapes(L['Metal_3']).each() if s.bbox().top * dbu < -2390 and s.bbox().width() * dbu > 150})
print('   1T1R flat-row M3 electrode lefts:', fr)
print('   ResolutionTests:', [bbum(k.bbox()) for k in top.each_inst() if k.cell.name == 'ResolutionTests'])

# ---- standard suite
blocks_c = sorted({k.cell.name for k in top.each_inst() if not is_text(k.cell)} - {'ResolutionTests', 'OVL_VERNIERS'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k_, v in Counter(con).items(): print('      ', k_, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k_, v in Counter((c_, r_) for c_, r_, p_ in ovl).most_common(): print('      ', k_, 'x', v)
for bname in ('PERF_TFT', 'SYN_1T1R', 'NOVEL_DEVICES'):
    c = ly.cell(bname); regs = {i.cell.name: flat(i) for i in c.each_inst() if not is_text(i.cell)}; nm = list(regs); bad = 0
    for a_ in range(len(nm)):
        for b_ in range(a_ + 1, len(nm)):
            if not (regs[nm[a_]] & regs[nm[b_]]).is_empty() or regs[nm[a_]].separation_check(regs[nm[b_]], u(20), False, db.Region.Projection, None, None, None).count(): bad += 1
    print(f'   {bname}: device pairs overlapping or < 20 um apart: {bad}'); assert bad == 0
ai = list(top.each_inst())
blocks = [k for k in ai if not is_text(k.cell)]
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
gapl = []
for kk in blocks:
    for B_ in blocks:
        if B_ is kk or id(B_) < id(kk) or not kk.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
        e_ = fl[id(kk)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
        if e_.count(): gapl.append((round(min(x.distance() for x in e_.each()) * dbu, 1), kk.cell.name, B_.cell.name))
print('   block pairs closer than 60 um:', sorted(gapl))
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
viol_k = [(k.cell.name, bbum(fl[id(k)].and_(kz).bbox())) for k in blocks if not fl[id(k)].and_(kz).is_empty()]
print('   alignment-cross keep-out violations:', viol_k if viol_k else 0)
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_, layout=ly, LL=L):
    tw_ = ts_ = 0
    for n in LAY:
        r_ = db.Region(cell_.begin_shapes_rec(LL[n])); r_.merge()
        tw_ += len([e_ for e_ in r_.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r_.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw_, ts_
print('   DRC 2um  TOP: width %d space %d   (v51: 25 / 61)' % drc(top))

# ---- preservation: non-text geometry of every old cell unchanged, except the removed text and the 1T1R row shift
def own(c, LL, n): r = db.Region(c.shapes(LL[n])); r.merge(); return r
chg = []
for cc in old.each_cell():
    if is_text(cc): continue
    dd = ly.cell(cc.name)
    if dd is None: chg.append((cc.name, 'missing')); continue
    for n in LAY:
        rmset = Counter(str(p) for nn, p in removed.get(cc.name, []) if nn == n)
        ra = db.Region()
        for s_ in cc.shapes(LO[n]).each():
            if not (s_.is_polygon() or s_.is_box() or s_.is_path()): continue
            ps = str(s_.polygon)
            if rmset[ps] > 0: rmset[ps] -= 1; continue
            ra.insert(s_.polygon)
        if cc.name == '1T1R':
            moved = db.Region()
            for p in ra.each():
                b = p.bbox(); dx = 0
                if b.top * dbu <= -2390 and b.bottom * dbu >= -3210:
                    for xa, xf in zip(COLS_ARRAY, COLS_FLAT):
                        if b.left * dbu >= xf - 0.01 and b.right * dbu <= xf + 1065.01: dx = xa - xf
                moved.insert(p.moved(u(dx), 0))
            ra = moved
        ra.merge()
        if not (ra ^ own(dd, L, n)).is_empty(): chg.append((cc.name, n))
    MOVED = {'TOP': ('ResolutionTests', 'SYN_1T1R', 'STEP_COVERAGE')}
    oi = sorted((k.cell.name, str(k.trans)) for k in cc.each_inst() if not is_text(k.cell) and k.cell.name not in MOVED.get(cc.name, ()))
    ni = sorted((k.cell.name, str(k.trans)) for k in dd.each_inst() if not is_text(k.cell) and k.cell.name not in MOVED.get(cc.name, ()))
    if oi != ni and cc.name not in ('PERF_TFT', 'SYN_1T1R', 'NOVEL_DEVICES'): chg.append((cc.name, 'instances'))
print('   non-text geometry changed outside the intended edits:', chg); assert not chg
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
