# executed inside build_v38.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)
blocks_c = sorted({k.cell.name for k in top.each_inst() if not k.cell.name.startswith('TEXT')} - {'ResolutionTests'})
new_leaf = [c.name for c in CAPS] + [OPEN.name, SHORT.name]
con = A.connectivity(blocks_c + new_leaf)
print('   connectivity findings:', len(con))
for k, v in Counter(con).items(): print('      ', k, 'x', v)
ovl = A.overlay(blocks_c + new_leaf)
print(f'   overlay findings (ENC {ENC}, OVL {OVL}):', len(ovl))
for k, v in Counter((c, r) for c, r, p in ovl).most_common(): print('      ', k, 'x', v)

def nets_of(cell):
    """union-find over M1/M3 polygons (M2 unused here), joined at Isolation_1 windows"""
    polys = []; par = []; lay = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for n in ('Metal_1', 'Metal_3'):
        for p in A.R(cell, n).each():
            if n == 'Metal_1' and isglyph(p): continue
            polys.append(p); par.append(len(par)); lay.append(n)
    idx = lambda reg: [i for i, p in enumerate(polys) if not db.Region(p).interacting(reg).is_empty()]
    for w in A.R(cell, 'Isolation_1').each():
        hit = idx(db.Region(w))
        for i in hit[1:]: par[find(i)] = find(hit[0])
    pads = Counter()
    for w in A.R(cell, PASS).each():
        hit = idx(db.Region(w))
        if hit: pads[find(hit[0])] += 1
    return {find(i) for i in range(len(polys))}, pads

print('\n   -- guard isolation + net check per device --')
bad = 0
for c in CAPS:
    nets, pads = nets_of(c)
    ok = len(nets) == 3 and len(pads) == 3 and set(pads.values()) == {1}
    if not ok: bad += 1; print('   NET MISMATCH', c.name, len(nets), dict(pads))
nets, pads = nets_of(OPEN)
ok_open = len(nets) == 3 and len(pads) == 3 and set(pads.values()) == {1}   # guard, inner, TE: each isolated, 1 pad
if not ok_open: bad += 1; print('   NET MISMATCH open', len(nets), dict(pads))
nets, pads = nets_of(SHORT)
ok_short = len(nets) == 2 and sorted(pads.values()) == [1, 2]  # guard alone (1 pad); inner+TE merged (2 pads)
if not ok_short: bad += 1; print('   NET MISMATCH short', len(nets), dict(pads))
print(f'   {len(CAPS)} guarded caps (3 nets/3 pads each) + OPEN (3 isolated nets) + SHORT (inner+TE merged) -- mismatches: {bad}')
assert bad == 0

# explicit guard-to-inner-electrode isolation (the exact failure mode being guarded against: a short
# would silently turn this into "just a bigger capacitor" with no warning from the net-count check above
# if inner and guard happened to have the same net size by coincidence -- check the actual gap too)
print('\n   -- guard-ring gap (measured from real geometry, not the GGAP constant) --')
for c in CAPS + [OPEN, SHORT]:
    m1 = A.R(c, 'Metal_1'); m1 = db.Region([p for p in m1.each() if not isglyph(p)])
    # split into "guard" (touches the W pad direction, i.e. touches x <= -(S/2+GGAP+GW-1)) vs "inner"
    comps = list(m1.merged_semantics_then_each() if hasattr(m1, 'merged_semantics_then_each') else m1.each())
    r = db.Region(comps); r.merge()
    parts = list(r.each())
    if len(parts) < 2: print('   !!', c.name, 'guard and inner are ONE polygon (real short)'); bad += 1; continue
    guard = min(parts, key=lambda p: p.bbox().left)
    inner = [p for p in parts if p is not guard]
    inner_r = db.Region(inner)
    gap = min((e.distance() * dbu for e in db.Region(guard).separation_check(
        inner_r, u(500.0), False, db.Region.Projection, None, None, None).each()), default=None)
    print(f'   {c.name:20s} guard<->inner real gap = {gap} um')
    assert gap is not None and gap >= GGAP - 0.5
print('   guard-ring short check: 0 shorts,', bad, 'total problems')
assert bad == 0

# single-edge area-definition proof, per capacitor, using REAL measured geometry (not the S,n parameters)
print('\n   -- single-edge containment + measured (Area, Perimeter) for the regression --')
data = []
for c, (S, n, lab) in zip(CAPS, DEVICES):
    inner = PLATES[c.name]                        # the plate/comb region exactly as drawn -- no lead, no pad
    ig = A.R(c, 'IGZO'); te = A.R(c, 'Metal_3')
    inside_ig = (inner - ig).is_empty(); inside_te = (ig - te).is_empty()
    area = inner.area() * dbu * dbu
    per = sum(sum((p1 - p0).abs() for p0, p1 in zip(pts, pts[1:] + pts[:1])) for pts in
              [[(pt.x * dbu, pt.y * dbu) for pt in poly_.each_point_hull()] for poly_ in inner.each()]
              for pts in [pts]) if False else None
    # perimeter via klayout's own edge length sum (robust for multi-finger polygons)
    per = sum(e.length() for e in inner.edges().each()) * dbu
    print(f'   {c.name:20s} M1 subset of IGZO: {inside_ig}   IGZO subset of M3: {inside_te}   '
          f'area={area:8.1f} um2  perimeter={per:7.1f} um')
    assert inside_ig and inside_te, f'{c.name}: single-edge containment violated'
    data.append((area, per))
# 2-parameter least squares fit  C_meas = c_area*A + c_perim*P  needs a well-conditioned (A,P) set:
import itertools
worst_cond = None
for combo in itertools.combinations(range(len(data)), 2):
    (a1, p1), (a2, p2) = data[combo[0]], data[combo[1]]
    det = a1 * p2 - a2 * p1
    if worst_cond is None or abs(det) < abs(worst_cond): worst_cond = det
print(f'   (Area,Perimeter) pairs: {[(round(a), round(p)) for a, p in data]}')
print(f'   worst-case 2x2 determinant across all pairs: {worst_cond:.0f} (nonzero & not tiny -> regression is well-conditioned)')
assert abs(worst_cond) > 1000

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
mk = [k for k in blocks if k.cell.name == 'MIS_Capacitors_v2'][0]
gaps = []
for B_ in blocks:
    if B_ is mk or not mk.bbox().enlarged(u(80), u(80)).overlaps(B_.bbox()): continue
    e_ = fl[id(mk)].separation_check(fl[id(B_)], u(80), False, db.Region.Projection, None, None, None)
    if e_.count(): gaps.append((round(min(x.distance() for x in e_.each()) * dbu, 1), B_.cell.name))
print('   MIS_Capacitors_v2 gaps < 80 um to neighbours:', sorted(gaps) if gaps else 'none')
tx = 0
allb = own_r.dup()
for k in blocks: allb = allb.or_(fl[id(k)])
allb.merge()
for t in texts:
    if not fl[id(t)].and_(allb).is_empty(): print('   TEXT on structure:', t.cell.name); tx += 1
print('   TEXT$ collisions:', tx)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40))
for t in texts: kz += db.Region(t.bbox().enlarged(u(10), u(10)))
viol = [k.cell.name for k in blocks if not fl[id(k)].and_(kz).is_empty()]
print('   alignment-mark / label keep-out violations:', viol if viol else 0)
lc = 0
for c in CAPS + [OPEN, SHORT, mis]:
    lab = LABELS.get(c.name)
    if lab is None: continue
    ob = db.Region()
    for n in LAY: ob += db.Region(c.begin_shapes_rec(L[n]))
    ob -= lab
    d = lab.sized(u(10)).and_(ob)
    if not d.is_empty(): lc += 1; print('   label within 10 um of structure in', c.name, d.bbox())
print('   in-cell label collisions:', lc)
P2 = db.Region.Projection; lim = MINF / math.sqrt(2) - .001
def drc(cell_):
    tw = ts_ = 0
    for n in LAY:
        r = db.Region(cell_.begin_shapes_rec(L[n])); r.merge()
        tw += len([e_ for e_ in r.width_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
        ts_ += len([e_ for e_ in r.space_check(u(MINF), False, P2, None, None, None).each() if .05 < e_.distance() * dbu < lim])
    return tw, ts_
print('   DRC 2um  TOP: width %d space %d' % drc(top))
print('   DRC 2um  MIS_Capacitors_v2: width %d space %d' % drc(mis))
old = db.Layout(); old.read(SRC); LO = names(old)
chg = []
for c in old.each_cell():
    d = ly.cell(c.name)
    if d is None: continue
    tot = 0
    for n in LAY:
        ra = db.Region(c.begin_shapes_rec(LO[n])); ra.merge()
        rb = db.Region(d.begin_shapes_rec(L[n])); rb.merge(); tot += ra.xor(rb).area()
    if tot: chg.append(c.name)
print('   existing cells whose geometry changed vs v37:', chg)
print('   old MIS_Capacitors cell still present (unplaced):', ly.cell('MIS_Capacitors') is not None)
ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
