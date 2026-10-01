# executed inside build_v46.py (shares its namespace)
print('\n== verification')
A = mkaudit.Audit(ly)

# --- 1. shape count per (cell, layer) preserved exactly -- nothing added or dropped, only resized ---
old = db.Layout(); old.read(SRC); LO = names(old)
count_mismatches = []
for cc in old.each_cell():
    dd = ly.cell(cc.name)
    if dd is None:
        count_mismatches.append((cc.name, 'MISSING')); continue
    for n in LAY:
        ca = cc.shapes(LO[n]).size()
        cb = dd.shapes(L[n]).size()
        if ca != cb:
            count_mismatches.append((cc.name, n, ca, cb))
print('   shape-count mismatches (old vs new, per cell/layer):', len(count_mismatches))
for m in count_mismatches[:15]: print('     ', m)
assert count_mismatches == []

# --- 2. no 160x160 pad squares remain anywhere; no 150x150 windows remain among the paired set ---
remaining_160 = 0; remaining_paired_150win = 0
for cell in ly.each_cell():
    pad_centers_now = []
    for n in METAL_LAYERS:
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if is_square(b, PAD_DBU, TOL): remaining_160 += 1
            if is_square(b, u(NEW_PAD), TOL): pad_centers_now.append(((b.left + b.right)//2, (b.bottom+b.top)//2))
    for n in WINDOW_LAYERS:
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if is_square(b, WIN_DBU, TOL):
                cx, cy = (b.left+b.right)//2, (b.bottom+b.top)//2
                if any(abs(cx-pcx) <= CTOL and abs(cy-pcy) <= CTOL for pcx, pcy in pad_centers_now):
                    remaining_paired_150win += 1
print('   160x160 pad squares remaining anywhere:', remaining_160)
print('   150x150 windows still paired with a (new) 150x150 pad:', remaining_paired_150win)
assert remaining_160 == 0
assert remaining_paired_150win == 0

# --- 3. new sizes present in the expected counts ---
new_pad_count = new_win_count = 0
for cell in ly.each_cell():
    for n in METAL_LAYERS:
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            if is_square(s.polygon.bbox(), u(NEW_PAD), TOL): new_pad_count += 1
    for n in WINDOW_LAYERS:
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            if is_square(s.polygon.bbox(), u(NEW_PW), TOL): new_win_count += 1
print(f'   150x150 pad squares now present: {new_pad_count} (built {n_pads})')
print(f'   140x140 window squares now present: {new_win_count} (built {n_windows})')
assert new_pad_count >= n_pads
assert new_win_count >= n_windows

# --- 4. spot-check: a handful of known pads in different blocks, confirm new size + unmoved center ---
def spot(cellname, approx_old_center_um, layer):
    c = ly.cell(cellname)
    cx0, cy0 = approx_old_center_um
    for s in c.shapes(L[layer]).each():
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        cx, cy = (b.left+b.right)*dbu/2, (b.bottom+b.top)*dbu/2
        if abs(cx-cx0) < 5 and abs(cy-cy0) < 5:
            w = (b.right-b.left)*dbu
            print(f'   spot-check {cellname}/{layer} near ({cx0},{cy0}): found size {w:.2f} at center ({cx:.2f},{cy:.2f})')
            return w
    print(f'   spot-check {cellname}/{layer} near ({cx0},{cy0}): NOT FOUND'); return None

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
print('   DRC 2um  TOP: width %d space %d' % drc(top))

ly.write(OUT + '.oas'); ly.write(OUT + '.gds')
print('written', OUT + '.oas')
