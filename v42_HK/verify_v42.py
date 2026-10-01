# executed inside build_v42.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c, r) for c, r, p in ovl).most_common(): print('      ', k, 'x', v)

ai = list(top.each_inst())
blocks = [k for k in ai if not k.cell.name.startswith('TEXT')]
texts = [k for k in ai if k.cell.name.startswith('TEXT')]
fl = {}
for k in ai: fl[id(k)] = flat(k)
tk = [k for k in blocks if k.cell.name == '1T1R'][0]   # re-fetch: the earlier `tk` reference predates
                                                         # the each_inst() re-iteration above and its id()
                                                         # may not match a fresh wrapper object
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
gaps = []
for B_ in blocks:
    if B_ is tk or not tk.bbox().enlarged(u(60), u(60)).overlaps(B_.bbox()): continue
    e_ = fl[id(tk)].separation_check(fl[id(B_)], u(60), False, db.Region.Projection, None, None, None)
    if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
print('   1T1R gaps < 60 um to neighbours:', sorted(gaps) if gaps else 'none')
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
old = db.Layout(); old.read(SRC); LO = names(old)
chg = []
for cc in old.each_cell():
    dd = ly.cell(cc.name)
    if dd is None: continue
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells whose geometry changed vs v41:', chg)

# ---------------- space-availability report for the four blocks that could NOT be moved -----------------
print('\n   -- space check for STEP_COVERAGE / XBAR_4X4 / SPLIT_CV / PERF_TFT --')
def bb(name): return inst(name).bbox()
for name in ('STEP_COVERAGE', 'XBAR_4X4', 'SPLIT_CV', 'PERF_TFT'):
    b = bb(name); print(f'   {name:14s} needs {b.width()*dbu:.0f} x {b.height()*dbu:.0f} um')
mem_b = bb('Memristors'); perf_b = bb('PERF_TFT')
clearance = (perf_b.bottom - mem_b.top) * dbu
print(f'   PERF_TFT->Memristors clearance today: {clearance:.0f} um (PERF_TFT needs {perf_b.height()*dbu:.0f} um of it to move down flush)')
new_1t1r_bottom = tk.bbox().bottom * dbu
ts_top = bb('TestStructures').top * dbu
print(f'   space freed below the NEW 1T1R position: {new_1t1r_bottom - ts_top:.0f} um tall (bounded above by CBKR_Structures/MEM_HIGH_VALUE, not just TestStructures)')

ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
