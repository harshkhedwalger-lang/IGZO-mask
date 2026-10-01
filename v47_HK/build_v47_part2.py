print('\n== 2. rebuild the 42-device grid at the new pitch')
gm = ly.cell('Memristors_Gated')
ALL_42_NAMES = [f'MEM_{ty}_{row}' for _, tys in GROUPS for ty in tys for row in (1, 2, 3)]
old_insts = [k for k in gm.each_inst() if k.cell.name in ALL_42_NAMES]
assert len(old_insts) == 42, f'expected all 42 old device instances present, found {len(old_insts)}'
dev_ci = {name: ly.cell(name).cell_index() for name in DEV_NAMES}

# erase ALL 42 old device instances (only 14 get re-placed -- the other 28 are dropped from the
# die per the reduced-repeat decision, but their cell definitions stay in the library) + old headers/title
glyphs = [s for s in gm.shapes(L['Metal_1']).each() if s.is_polygon() and isglyph(s.polygon)]
print(f'   {len(glyphs)} own header/title glyphs in Memristors_Gated (to redraw)')
print(f'   erasing all {len(old_insts)} old device instances (14 will be re-placed, redesigned; 28 dropped)')
for k in list(old_insts): gm.erase(k)
for s in list(glyphs): gm.shapes(L['Metal_1']).erase(s)

COL_PITCH = DEV_W + 60.0; GROUP_GAP_Y = 200.0
def group_width(types): return (len(types) - 1) * COL_PITCH + DEV_W
col_w = max(group_width(tys) for _, tys in GROUPS)
# single column, 4 length-groups stacked (row=1 only, so a group is now just one row of type-columns --
# no need for the old 2x2-of-3-row layout; a single narrow column fits the die better than a wide 2x2)
group_y0 = [i * (DEV_H + GROUP_GAP_Y) for i in range(len(GROUPS))]
group_y0.reverse()   # L2 group on top
total_width = col_w
total_height = group_y0[0] + DEV_H
print(f'   new grid footprint: {total_width:.0f} x {total_height:.0f} um  (was 2284 x 1439 before this pass)')

targets = {}
for gi, (lab, types) in enumerate(GROUPS):
    gy = group_y0[gi]
    for tci, ty in enumerate(types):
        name = f'MEM_{ty}_1'
        tx = tci * COL_PITCH - DEV_X0
        ty_y = gy - DEV_Y0
        targets[name] = (tx, ty_y)
assert set(targets) == set(DEV_NAMES)

for name, (tx, ty_y) in targets.items():
    gm.insert(db.CellInstArray(dev_ci[name], db.Trans(u(tx), u(ty_y))))
print(f'   {len(targets)} devices placed on the new grid')

txt(gm, 'GATED MEMRISTORS - 1x/TYPE, GROUPED BY GAP LENGTH', 0.0, total_height + 100.0, 36.0)
for gi, (lab, _) in enumerate(GROUPS):
    txt(gm, f'L = {lab} UM', 0.0, group_y0[gi] + DEV_H + 30.0, 24.0)
print('   title + 4 length-group headers redrawn (single-column layout, 1 repeat/type)')

print('\n== 3. find a clear placement for the whole (much bigger) block')
mgk = [k for k in top.each_inst() if k.cell.name == 'Memristors_Gated'][0]
mg_r_local = db.Region()
for n in LAY: mg_r_local += db.Region(gm.begin_shapes_rec(L[n]))
mg_r_local.merge()
mg_r = mg_r_local.transformed(db.ICplxTrans(mgk.trans))   # actual current TOP-coordinate position
print(f'   full flattened block region bbox um: {[round(v*dbu,1) for v in (mg_r.bbox().left,mg_r.bbox().bottom,mg_r.bbox().right,mg_r.bbox().top)]}')

crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
own_top_r = db.Region()
for n in LAY: own_top_r = own_top_r.or_(db.Region(top.shapes(L[n])))
own_top_r.merge()
for k in top.each_inst():
    if k.cell.name.startswith('TEXT'): kz += db.Region(k.bbox().enlarged(u(10), u(10)))
other_blocks = [k for k in top.each_inst() if not k.cell.name.startswith('TEXT') and k.cell.name != 'Memristors_Gated']

DIE_LO, DIE_HI = -6900.0, 6900.0
STEP = 100.0
MARGIN = 80.0    # require genuine clearance, not just zero-overlap, from every neighbour
# precompute every other block's flattened region ONCE (was being rebuilt per candidate -- too slow)
other_flat = []
for k in other_blocks:
    fk = db.Region()
    for n in LAY: fk += db.Region(k.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(k.trans))
    fk.merge()
    other_flat.append((fk.bbox(), fk))
all_others = own_top_r.dup()
for _, fk in other_flat: all_others += fk
all_others.merge()
obstacles = (all_others + kz).sized(u(MARGIN))
placed = False
best = None
for gy in range(int(DIE_LO), int(DIE_HI - total_height) + 1, int(STEP)):
    for gx in range(int(DIE_LO), int(DIE_HI - total_width) + 1, int(STEP)):
        cand = mg_r.transformed(db.Trans(u(gx) - mg_r.bbox().left, u(gy) - mg_r.bbox().bottom))
        if not cand.and_(obstacles).is_empty(): continue
        placed = True; best = (gx, gy); break
    if placed: break

if placed:
    gx, gy = best
    dxm = u(gx) - mg_r.bbox().left; dym = u(gy) - mg_r.bbox().bottom
    mgk.transform(db.Trans(dxm, dym))
    print(f'   placed at TOP bbox', mgk.bbox())
else:
    print('   !! NO CLEAR PLACEMENT FOUND on a', STEP, 'um grid scan of the full die interior')
    print('      block needs', total_width, 'x', total_height, '-- this will need to be reported, not forced')

exec(open(os.path.join(HERE, 'verify_v47.py'), encoding='utf-8').read())
if placed:
    exec(open(os.path.join(HERE, 'build_v47_part3.py'), encoding='utf-8').read())
