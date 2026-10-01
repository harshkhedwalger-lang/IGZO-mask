# executed inside build_v41.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
con = A.connectivity(blocks_c)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c_, r) for c_, r, p in ovl).most_common(): print('      ', k, 'x', v)

# --- geometric congruence: the retyped M2 shapes must be EXACTLY where the erased M1 shapes were
old = db.Layout(); old.read(SRC); LO = names(old)
co = old.cell('Transistors_BottomGate_HfO2Only')
old_gate = db.Region([s.polygon for s in co.shapes(LO['Metal_1']).each() if (s.is_polygon() or s.is_box()) and not isglyph(s.polygon)])
old_gate.merge()
new_gate = db.Region(c.shapes(L['Metal_2'])); new_gate.merge()
diff = old_gate.xor(new_gate)
print(f'   gate geometry congruence (old M1 vs new M2, position/shape only): diff = {diff.area() * dbu * dbu:.4f} um2 (must be 0)')
assert diff.area() == 0, 'retyped gate geometry does not exactly match the original M1 gate shapes'

def nets_of(cell):
    """union-find over M1/M2/M3 polygons, merged where (a) they directly touch/overlap another polygon
    on the SAME layer -- same-layer metal touching is electrically one net regardless of any via -- or
    (b) two polygons (any layer) jointly touch the same Isolation_1 window.
    Glyphs are filtered PER-CHARACTER, before any merge: mkaudit.Audit.R() merges first, which can fuse
    two adjacent heading characters (tight kerning) into one word-sized blob that no longer looks like a
    small glyph to isglyph() -- it then survives the filter and shows up as a real, pad-less "net". Not
    a device defect, a check-ordering bug: recursing the cell's own (unmerged) shapes and classifying
    each polygon before any merge avoids it entirely."""
    polys = []; par = []; lay = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for n in ('Metal_1', 'Metal_2', 'Metal_3'):
        it = cell.begin_shapes_rec(L[n])
        it.unselect_cells([x.cell_index() for x in ly.each_cell() if x.name.startswith('TEXT')])
        raw = []
        while not it.at_end():
            s = it.shape()
            if s.is_polygon() or s.is_box():
                p = s.polygon.transformed(it.trans())
                if not (n == 'Metal_1' and isglyph(p)): raw.append(p)   # filter PER-SHAPE, pre-merge
            it.next()
        merged_check = db.Region(raw); merged_check.merge()
        for p in merged_check.each():
            polys.append(p); par.append(len(par)); lay.append(n)
    for i in range(len(polys)):                       # (a) same-layer direct touch
        for j in range(i + 1, len(polys)):
            if lay[i] == lay[j] and not db.Region(polys[i]).interacting(db.Region(polys[j])).is_empty():
                par[find(i)] = find(j)
    idx = lambda reg: [i for i, p in enumerate(polys) if not db.Region(p).interacting(reg).is_empty()]
    for w in A.R(cell, 'Isolation_1').each():          # (b) shared Iso1 window
        hit = idx(db.Region(w))
        for i in hit[1:]: par[find(i)] = find(hit[0])
    pads = Counter()
    for w in A.R(cell, PASS).each():
        hit = idx(db.Region(w))
        if hit: pads[find(hit[0])] += 1
    return {find(i) for i in range(len(polys))}, pads
nets_new, pads_new = nets_of(c)
nets_ref, pads_ref = nets_of(ly.cell('Transistors_BottomGate'))
print(f'   net topology: {c.name} {len(nets_new)} nets  vs  reference Transistors_BottomGate {len(nets_ref)} nets')
assert len(nets_new) == len(nets_ref)
print('   pad distribution match:', Counter(pads_new.values()) == Counter(pads_ref.values()))
assert Counter(pads_new.values()) == Counter(pads_ref.values())

# no stray Metal_2 anywhere else changed
old_m2_all = 0
for cc in old.each_cell():
    if cc.name in ('Transistors_BottomGate_HfO2Only', 'TOP'): continue  # TOP recursively contains the
        # intentional change, so it trivially "differs" -- checking every OTHER cell's OWN (non-
        # recursive) shapes is what actually catches an unintended stray change elsewhere
    dd = ly.cell(cc.name)
    if dd is None: continue
    a = db.Region(cc.shapes(LO['Metal_2'])); a.merge()
    b = db.Region(dd.shapes(L['Metal_2'])); b.merge()
    diff_area = a.xor(b).area() * dbu * dbu
    if diff_area:
        print('   Metal_2 diff in', cc.name, diff_area, 'um2')
        old_m2_all += 1
print('   other cells with a Metal_2 change:', old_m2_all)
assert old_m2_all == 0

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
    for b_ in range(a + 1, len(blocks)):
        A_, B_ = blocks[a], blocks[b_]
        if not A_.bbox().overlaps(B_.bbox()): continue
        o = fl[id(A_)].and_(fl[id(B_)]).area() * dbu * dbu
        if o: print('   OVERLAP', A_.cell.name, B_.cell.name, round(o)); ov += o
for k in blocks:
    o = fl[id(k)].and_(own_r).area() * dbu * dbu
    if o: print('   OVERLAP', k.cell.name, 'vs TOP-own', round(o)); ov += o
print('   structure overlap um2:', round(ov))
lc = 0
lab = r.dup(); ob = db.Region()
for n in LAY: ob += db.Region(c.begin_shapes_rec(L[n]))
ob -= lab
d = lab.sized(u(10)).and_(ob)
if not d.is_empty(): lc += 1; print('   new heading label within 10 um of structure', d.bbox())
print('   heading label collisions:', lc)
assert lc == 0
tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
print('   TEXT$ collisions:', tx)
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r_ = db.Region(cell_.begin_shapes_rec(L[n])); r_.merge()
        tw += len([e_ for e_ in r_.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r_.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))
print('   DRC 2um  Transistors_BottomGate_HfO2Only: width %d space %d' % drc(c))
chg = []
for cc in old.each_cell():
    dd = ly.cell(cc.name)
    if dd is None or cc.name == 'Transistors_BottomGate_HfO2Only': continue
    tot = 0
    for n in LAY:
        ra = db.Region(cc.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(dd.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(cc.name)
print('   cells OTHER than Transistors_BottomGate_HfO2Only whose geometry changed vs v40:', chg)
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
