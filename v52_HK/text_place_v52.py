# text placement for build_v52.py (executed in its namespace)
# A 'unit' is a list of lines that move together: a block title group, a device-label stack, or a single line.
# Rules (the mask-wide standard):
#   * labels / notes: start at their old place (centre kept, or the shared left / right edge of a column or stack),
#     then nudge (vertical first) until >= CLR_GEO um from structures and >= CLR_TXT um from other text
#   * block titles: title on top, its notes below, the lowest line TITLE_GAP um above the content under the group
CLR_GEO, CLR_TXT, TITLE_GAP = 10.0, 8.0, 20.0
tcs = [c.cell_index() for c in ly.each_cell() if is_text(c)]
TO_TOP = defaultdict(list)                 # every placement of a cell, as transformation to TOP
def _walk(c, t):
    for k in c.each_inst():
        if is_text(k.cell): continue
        for el in k.cell_inst.each_cplx_trans():
            TO_TOP[k.cell.name].append(t * el); _walk(k.cell, t * el)
TO_TOP['TOP'].append(db.ICplxTrans()); _walk(top, db.ICplxTrans())
KEEPOUT = db.Region([p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]).sized(u(40.0))
_geo = {}
def geo(cname):
    if cname not in _geo:
        c = ly.cell(cname); r = db.Region()
        for n in LAY:
            it = c.begin_shapes_rec(L[n]); it.unselect_cells(tcs); r += db.Region(it)
        for t in TO_TOP[cname]: r += KEEPOUT.transformed(t.inverted())     # alignment-cross keep-out, wherever placed
        if cname == 'TOP':                                   # die-title text (kept) is an obstacle too
            for k in top.each_inst():
                if is_text(k.cell): r += db.Region(k.bbox())
        r.merge(); _geo[cname] = r
    return _geo[cname]
placed_boxes = defaultdict(list)
def line_box(t, dx=0.0, dy=0.0):
    l0, r0 = tb(t['s'], MAG[t['tier']])
    return db.Box(u(t['x'] + l0 + dx), u(t['y'] + dy), u(t['x'] + r0 + dx), u(t['y'] + th(MAG[t['tier']]) + dy))
def clear(unit, dx, dy):
    g = geo(unit[0]['cell'])
    for t in unit:
        b = line_box(t, dx, dy)
        if not g.interacting(db.Region(b.enlarged(u(CLR_GEO), u(CLR_GEO)))).is_empty(): return False
        for pb in placed_boxes[t['cell']]:
            if pb.overlaps(b.enlarged(u(CLR_TXT - 0.01), u(CLR_TXT - 0.01))): return False
    return True
CAND = sorted([(dx, dy) for dx in range(-60, 61, 5) for dy in range(-60, 61, 5)], key=lambda d: (abs(d[1]) + 2 * abs(d[0]), d[1] < 0, abs(d[0])))
CAND_WIDE = sorted([(dx, dy) for dx in range(-300, 301, 10) for dy in range(-120, 121, 5)], key=lambda d: (abs(d[1]) + abs(d[0]), abs(d[0])))
unresolved = []; widened = []
def settle(unit, cand=CAND):
    if cand is CAND and not any(clear(unit, dx, dy) for dx, dy in CAND):
        cand = CAND_WIDE; widened.append((unit[0]['cell'], [t['s'] for t in unit]))
    for dx, dy in cand:
        if clear(unit, dx, dy):
            for t in unit: t['x'] += dx; t['y'] += dy
            break
    else:
        unresolved.append((unit[0]['cell'], [t['s'] for t in unit]))
    for t in unit: placed_boxes[t['cell']].append(line_box(t))

# ---- 1. units from labels / notes (everything not consumed by a title group)
used = set()
title_jobs = []
for key, (olds, news) in TITLES.items():
    cname = key if isinstance(key, str) else key[0]
    grp = [i for i in items if i['cell'] == cname and i['s'] in olds and id(i) not in used]
    assert sorted(i['s'] for i in grp) == sorted(olds), (key, [i['s'] for i in items if i['cell'] == cname])
    for i in grp: used.add(id(i))
    title_jobs.append((cname, grp, news))
units = []
bycell = defaultdict(list)
for i in items:
    if id(i) not in used: bycell[i['cell']].append(i)
for cname, lst in bycell.items():
    lst.sort(key=lambda i: -i['box'].top)
    stacks, seen = [], set()
    for a in lst:
        if id(a) in seen: continue
        st = [a]; seen.add(id(a))
        for b in lst:
            if id(b) in seen: continue
            last = st[-1]['box']; bb = b['box']
            same_r = abs(bb.right - last.right) * dbu <= 6.0; same_l = abs(bb.left - last.left) * dbu <= 6.0
            if (same_r or same_l) and 0 <= (last.bottom - bb.top) * dbu <= 15.0:
                st.append(b); seen.add(id(b))
        stacks.append(st)
    lefts = Counter(round(i['box'].left * dbu) for i in lst); rights = Counter(round(i['box'].right * dbu) for i in lst)
    for st in stacks:
        tiers = [tier_of(cname, i['s']) for i in st]
        unit = []
        if len(st) > 1:
            right = abs(st[0]['box'].right - st[1]['box'].right) * dbu <= 6.0
            edge = max(i['box'].right for i in st) * dbu if right else min(i['box'].left for i in st) * dbu
            y = st[0]['box'].top * dbu
            for i, t in zip(st, tiers):
                y -= th(MAG[t]); l0, r0 = tb(i['s'], MAG[t])
                unit.append(dict(cell=cname, layer=i['layer'], s=i['s'], tier=t, x=(edge - r0) if right else edge - l0, y=y))
                y -= GAP[t]
        else:
            i = st[0]; t = tiers[0]; b = i['box']; l0, r0 = tb(i['s'], MAG[t]); h = th(MAG[t])
            if t == 'T' or lefts[round(b.left * dbu)] > 1: x = b.left * dbu - l0
            elif rights[round(b.right * dbu)] > 1: x = b.right * dbu - r0
            else: x = (b.left + b.right) / 2 * dbu - (l0 + r0) / 2
            y = b.bottom * dbu if t == 'T' else (b.bottom + b.top) / 2 * dbu - h / 2
            unit.append(dict(cell=cname, layer=i['layer'], s=i['s'], tier=t, x=x, y=y))
        units.append(unit)
newtext = [t for un in units for t in un]
exec(open(os.path.join(HERE, 'text_fixups_v52.py'), encoding='utf-8').read())
# titles that keep their place (original headings) first, then labels (big first), then notes
order = sorted(units, key=lambda un: {'T': 0, 'L': 1, 'N': 2}[un[0]['tier']])
for un in order:
    if un[0]['tier'] == 'T': settle(un, [(0, dy) for dy in range(0, 201, 5)])
    else: settle(un)

# ---- 2. block title groups: lowest line TITLE_GAP above the content directly below the group
for cname, grp, news in title_jobs:
    x0 = min(i['box'].left for i in grp) * dbu; oldtop = max(i['box'].top for i in grp) * dbu
    lay = grp[0]['layer']
    width = max(tb(s, MAG[t])[1] for s, t in news)
    strip = db.Region(db.Box(u(x0), u(-1e5), u(x0 + width), u(oldtop + 5)))
    below = geo(cname) & strip
    for pb in placed_boxes[cname]:
        if pb.overlaps(strip.bbox()) and pb.top <= u(oldtop + 5): below += db.Region(pb)
    y = below.bbox().top * dbu + TITLE_GAP if not below.is_empty() else min(i['box'].bottom for i in grp) * dbu
    unit = []
    for s, t in reversed(news):
        unit.append(dict(cell=cname, layer=lay, s=s, tier=t, x=x0 - tb(s, MAG[t])[0], y=y)); y += th(MAG[t]) + GAP[t]
    settle(unit, [(0, dy) for dy in range(0, 201, 5)])
    newtext += unit
print('   unresolved text placements:', unresolved, '  needed the wide search:', widened)
for t in newtext:
    c = ly.cell(t['cell'])
    c.insert(db.CellInstArray(tcell(t['s'], t['layer'], MAG[t['tier']]).cell_index(), db.Trans(u(t['x']), u(t['y']))))
print('   placed:', Counter(t['tier'] for t in newtext), ' distinct text cells:', len(_tc))
