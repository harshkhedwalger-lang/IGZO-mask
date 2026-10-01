"""build_v51.py -- v50 -> v51   (klayout.db only; OASIS + GDS copy)

1. PERF_TFT: L ladder removed (duplicated the W500 main set). Keeps REF + IDT x3 + LOV sweep, retitled,
   re-packed column-first; SYN_1T1R follows it.
2. Transistors_BottomGate and Transistors_BottomGate_HfO2Only: third row L3, L3, L2, L2 at W500, copied
   from each block's own L5 device (only the channel narrowed, pads untouched); labels spliced from the
   existing label font (same cells' glyphs).
3. NOVEL_DEVICES (all on the 5 um overlap / 45 um IGZO convention):
   4PR_M1, 4PR_M2      gated four-probe TFT, W100 L60, gated IGZO probe tabs at L/3 and 2L/3
   SPLIT_M1S, SPLIT_M2S  split dual-EOT gate: M1 half + M2 half, overlapping 4 um (no ungated gap)
   FG_R0/R2/R5, FG_R2_PAD  floating gate: M1 CG / Al2O3 / isolated M2 FG / HfO2 / IGZO; CG inside FG
   GC2T_L10/L50, GC2T_CAL  2T0C gain cell: M1 write TFT -> Iso1 landing -> M2 gate of read TFT
4. OVL_VERNIERS: 0.25 um verniers, +/-3 um, for M1/M2, M1/IGZO, M1/M3, M2/IGZO, M2/M3, IGZO/M3.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v50_HK', 'v50_HK.oas')
OUT = os.path.join(HERE, 'v51_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL
ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
old = db.Layout(); old.read(SRC)
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); LO = names(old); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r); return r
def txtw(s, cap=24.0): return tg.text(s, dbu, cap * MAG1).bbox().width() * dbu
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500
def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(min(x0, x1)), u(min(y0, y1)), u(max(x0, x1)), u(max(y0, y1))))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
PAD, PW, TAPER = 150.0, 140.0, 75.0
def pad_lead(c, met, ax, ay, d, w, llen):
    sx, sy = {'N': (0, 1), 'S': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[d]
    def pt(a, b): return (ax + sx * a - sy * b, ay + sy * a + sx * b)
    if llen > 0: poly(c, met, [pt(0, -w / 2), pt(llen, -w / 2), pt(llen, w / 2), pt(0, w / 2)])
    a0 = llen; a1 = llen + TAPER
    poly(c, met, [pt(a0, -w / 2), pt(a1, -PAD / 2), pt(a1, PAD / 2), pt(a0, w / 2)])
    (x0, y0), (x1, y1) = pt(a1, -PAD / 2), pt(a1 + PAD, PAD / 2)
    bx(c, met, x0, y0, x1, y1); e = (PAD - PW) / 2
    xa, xb, ya, yb = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
    if met in ('Metal_1', 'Metal_2'):
        bx(c, 'Isolation_1', xa + e, ya + e, xb - e, yb - e); bx(c, 'Metal_3', xa, ya, xb, yb)
    bx(c, PASS, xa + e, ya + e, xb - e, yb - e)
def label(c, text, y_low, x_left):
    yl = min(-PAD / 2, y_low) - 20.0; xr = min(-PAD / 2, x_left) - 15.0
    for line in text.split('|'):
        yl -= 32.0; txt(c, line, xr - txtw(line), yl, 24.0)
def inst(name): return [k for k in top.each_inst() if k.cell.name == name][0]
def bbum(b): return [round(v * dbu, 1) for v in (b.left, b.bottom, b.right, b.top)]
def flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r
LOV, EXT, EOUT, WOV = 5.0, 45.0, 10.0, 10.0

# ================================================================== 1. PERF_TFT without the L ladder
print('== 1. PERF_TFT: drop the L ladder')
perf = ly.cell('PERF_TFT')
DROP = ['PT_L2', 'PT_L3', 'PT_L5', 'PT_L20', 'PT_L50', 'PT_L100']
for k in list(perf.each_inst()):
    if k.cell.name in DROP: perf.erase(k)
for n in DROP: ly.delete_cell(ly.cell(n).cell_index())
for s in list(perf.shapes(L['Metal_1']).each()):
    if s.is_polygon() and isglyph(s.polygon) and s.bbox().bottom * dbu >= 80: perf.shapes(L['Metal_1']).erase(s)
txt(perf, 'HIGH-ID TFT: IDT AND LOV SWEEP', 0.0, 90.0, 36.0)
GAP_Y, GAP_X, BLOCK_GAP = 50.0, 60.0, 120.0
BOTTOM_LIMIT = 1338.0 + 60.0
ORDER = {'PERF_TFT': ['PT_REF_W100_L10', 'PT_IDT_W1000_L10', 'PT_IDT_W1000_L5', 'PT_IDT_W2000_L10',
                      'PT_LOV2', 'PT_LOV10', 'PT_LOV20', 'PT_LOV40'],
         'SYN_1T1R': ['SYN_W500_L20_J2', 'SYN_W500_L20_J4', 'SYN_W250_L10_J2', 'SYN_W250_L10_J4',
                      'SYN_W125_L5_J2', 'SYN_W125_L5_J4', 'SYN_W50_L2_J2', 'SYN_W50_L2_J4']}
def pack_columns(c, order, H, x0=5.0, ytop=-5.0):
    ins = {i.cell.name: i for i in c.each_inst()}
    assert sorted(ins) == sorted(order), (c.name, sorted(ins))
    cols, col, h = [], [], 0.0
    for n in order:
        bh = ins[n].bbox().height() * dbu
        need = bh if not col else h + GAP_Y + bh
        if col and need > H: cols.append(col); col, h = [], 0.0; need = bh
        col.append(n); h = need
    cols.append(col)
    x = x0
    for cl in cols:
        y = ytop; w = max(ins[n].bbox().width() * dbu for n in cl)
        for n in cl:
            b = ins[n].bbox(); ins[n].transform(db.Trans(u(x) - b.left, u(y) - b.top)); y -= b.height() * dbu + GAP_Y
        x += w + GAP_X
    return [len(cl) for cl in cols]
for bname in ('PERF_TFT', 'SYN_1T1R'):
    k = inst(bname); H = (k.trans.disp.y * dbu - 5.0) - BOTTOM_LIMIT
    print(f'   {bname}: columns {pack_columns(ly.cell(bname), ORDER[bname], H)}')
pk, sk = inst('PERF_TFT'), inst('SYN_1T1R'); pb, sb = pk.bbox(), sk.bbox()
sk.transform(db.Trans(pb.right + u(BLOCK_GAP) - sb.left, pb.top - sb.top))
print('   PERF_TFT', bbum(pk.bbox()), ' SYN_1T1R', bbum(sk.bbox()))

# ================================================================== 2. third row L3/L3/L2/L2 at W500
print('\n== 2. W500 blocks: third row L3, L3, L2, L2')
def spliced_label(name, src_cell, src_slot, dst_slot=1, base='TEXT$5'):
    """copy the 'L5_W500' label and replace character 1 with a glyph from another label (monospace, pitch 60)"""
    if ly.cell(name): return ly.cell(name)
    t = ly.create_cell(name); PITCH = 60.0
    for s in ly.cell(base).shapes(L['Metal_1']).each():
        p = s.polygon; xc = (p.bbox().left + p.bbox().right) / 2 * dbu
        if not (dst_slot * PITCH <= xc < (dst_slot + 1) * PITCH): t.shapes(L['Metal_1']).insert(p)
    for s in ly.cell(src_cell).shapes(L['Metal_1']).each():
        p = s.polygon; xc = (p.bbox().left + p.bbox().right) / 2 * dbu
        if src_slot * PITCH <= xc < (src_slot + 1) * PITCH:
            t.shapes(L['Metal_1']).insert(p.moved(u((dst_slot - src_slot) * PITCH), 0))
    return t
lab2 = spliced_label('TEXT_L2_W500', 'TEXT$3', 1)      # '2' from 'L20_W500'
lab3 = spliced_label('TEXT_L3_W500', 'TEXT$163', 0)    # '3' from the TLM label '30'
C5, ROWDY = 1062.5, -905.0
NEWROW = [(-287.5, 3.0, lab3), (387.5, 3.0, lab3), (1062.5, 2.0, lab2), (1737.5, 2.0, lab2)]
def add_third_row(cname):
    c = ly.cell(cname)
    tmpl = []
    for n in LAY:
        for s in c.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.bbox()
            if b.left * dbu >= C5 - 337.5 and b.right * dbu <= C5 + 337.5 and b.bottom * dbu >= 60 and b.top * dbu <= 840:
                tmpl.append((n, s.polygon))
    for colc, Lnew, lab in NEWROW:
        d = (5.0 - Lnew) / 2.0
        for n, p in tmpl:
            b = p.bbox()
            if b.top * dbu <= 290 and b.left * dbu < C5 < b.right * dbu: q = p        # gate pad + taper: unchanged
            else: q = db.Polygon([db.Point(pt.x + (u(d) if pt.x * dbu < C5 else -u(d)), pt.y) for pt in p.each_point_hull()])
            c.shapes(L[n]).insert(q.moved(u(colc - C5), u(ROWDY)))
        c.insert(db.CellInstArray(lab.cell_index(), db.Trans(u(colc - 255.0), u(860.0 + ROWDY))))
    print(f'   {cname}: template {len(tmpl)} shapes -> 4 devices added; TOP bbox {bbum(inst(cname).bbox())}')
    return len(tmpl)
add_third_row('Transistors_BottomGate')
add_third_row('Transistors_BottomGate_HfO2Only')

# ================================================================== 3. novel devices
print('\n== 3. novel devices')
def body(c, cx, W, Lg, cy=0.0):
    hg = Lg / 2 + LOV; yi = hg + EXT; ye = yi + EOUT; xi = W / 2 + WOV
    bx(c, 'IGZO', cx - xi, cy - yi, cx + xi, cy + yi)
    bx(c, 'Metal_3', cx - W / 2, cy + Lg / 2, cx + W / 2, cy + ye)
    bx(c, 'Metal_3', cx - W / 2, cy - ye, cx + W / 2, cy - Lg / 2)
    return hg, yi, ye, xi
def dev_4pr(name, gate):
    c = ly.create_cell(name); W, Lg = 100.0, 60.0
    hg, yi, ye, xi = body(c, 0.0, W, Lg)
    xt = xi + 30.0
    for sgn in (1, -1):
        bx(c, 'IGZO', xi, sgn * 8, xt, sgn * 12)                       # gated probe tab at y = +/-L/6
        bx(c, 'IGZO', xt - 10, sgn * 4, xt, sgn * 16)                  # tab head: IGZO encloses the M3 tip by 2 um,
                                                                        # so M3 never sits on bare gate dielectric
        bx(c, 'Metal_3', xt - 5, sgn * 6, xt + 55, sgn * 14)           # probe contact: 5 um on the tab/gate
        bx(c, 'Metal_3', xt + 47, sgn * 6, xt + 55, sgn * 114)
        pad_lead(c, 'Metal_3', xt + 55, sgn * 110, 'E', 8.0, 20.0)
    bx(c, gate, -xi - 20, -hg, xt, hg)                                  # gate also under the tabs
    pad_lead(c, gate, -xi - 20, 0.0, 'W', 2 * hg, 20.0)
    pad_lead(c, 'Metal_3', 0.0, ye, 'N', W, 20.0); pad_lead(c, 'Metal_3', 0.0, -ye, 'S', W, 20.0)
    label(c, f'4PR {"M1" if gate == "Metal_1" else "M2"} GATE|W100 L60', -ye, -xi)
    return c
def dev_split(name, src_gate):
    c = ly.create_cell(name); W, Lg = 100.0, 20.0
    hg, yi, ye, xi = body(c, 0.0, W, Lg)
    drn_gate = 'Metal_2' if src_gate == 'Metal_1' else 'Metal_1'
    span = {src_gate: (-2.0, hg), drn_gate: (-hg, 2.0)}                 # 4 um M2-over-M1 overlap at the split
    for g, (y0, y1) in span.items():
        if g == 'Metal_1': bx(c, g, -xi - 20, y0, xi, y1); pad_lead(c, g, -xi - 20, (y0 + y1) / 2, 'W', y1 - y0, 20.0)
        else:              bx(c, g, -xi, y0, xi + 20, y1); pad_lead(c, g, xi + 20, (y0 + y1) / 2, 'E', y1 - y0, 20.0)
    pad_lead(c, 'Metal_3', 0.0, ye, 'N', W, 20.0); pad_lead(c, 'Metal_3', 0.0, -ye, 'S', W, 20.0)
    label(c, f'SPLIT {"M1" if src_gate == "Metal_1" else "M2"}-SRC|W100 L20', -ye, -xi)
    return c
FGINFO = {}
def dev_fg(name, R, fg_pad=False):
    c = ly.create_cell(name); W, Lg = 100.0, 10.0
    hg, yi, ye, xi = body(c, 0.0, W, Lg)
    fg = db.Region(db.Box(u(-xi), u(-hg), u(xi), u(hg)))
    wing = {0: None, 2: (80.0, 30.0), 5: (100.0, 60.0)}[R]              # (length, half-height): area = R x strip
    if wing: fg += db.Region(db.Box(u(-xi - wing[0]), u(-wing[1]), u(-xi), u(wing[1])))
    fg.merge()
    for p in fg.each(): c.shapes(L['Metal_2']).insert(p)
    cg = fg.sized(u(-3.0)); cg.merge()                                   # control gate strictly inside the FG
    for p in cg.each(): c.shapes(L['Metal_1']).insert(p)
    xw = cg.bbox().left * dbu
    pad_lead(c, 'Metal_1', xw, 0.0, 'W', 10.0, 20.0)
    if fg_pad: pad_lead(c, 'Metal_2', xi, 0.0, 'E', 10.0, 20.0)
    pad_lead(c, 'Metal_3', 0.0, ye, 'N', W, 20.0); pad_lead(c, 'Metal_3', 0.0, -ye, 'S', W, 20.0)
    a_ch = (2 * xi) * (2 * hg); FGINFO[name] = (cg.area() * dbu * dbu, a_ch)
    label(c, f'FG R{R}{" FG-PAD" if fg_pad else ""}|W100 L10', -ye, xw)
    return c
def dev_2t0c(name, Lr, sn_pad=False):
    c = ly.create_cell(name)
    hgw, yiw, yew, xiw = body(c, 0.0, 50.0, 10.0)                      # write TFT, M1 gate
    bx(c, 'Metal_1', -xiw - 20, -hgw, xiw, hgw); pad_lead(c, 'Metal_1', -xiw - 20, 0.0, 'W', 2 * hgw, 20.0)
    pad_lead(c, 'Metal_3', 0.0, yew, 'N', 50.0, 20.0)
    bx(c, 'Metal_3', -5, -yew - 20, 5, -yew)                           # storage node route: WT drain ->
    bx(c, 'Metal_3', -5, -yew - 20, 155, -yew - 10)
    bx(c, 'Metal_3', 145, -yew - 20, 155, 15)
    bx(c, 'Metal_2', 135, -15, 165, 15); bx(c, 'Isolation_1', 145, -5, 155, 5); bx(c, 'Metal_3', 135, -15, 165, 15)
    cxr = 320.0
    hgr, yir, yer, xir = body(c, cxr, 100.0, Lr)                        # read TFT, M2 gate (HfO2 only)
    bx(c, 'Metal_2', 150, -hgr, cxr + xir, hgr)                          # ... landing -> read-TFT gate
    pad_lead(c, 'Metal_3', cxr, yer, 'N', 100.0, 20.0); pad_lead(c, 'Metal_3', cxr, -yer, 'S', 100.0, 20.0)
    if sn_pad: pad_lead(c, 'Metal_3', 0.0, -yew - 20, 'S', 10.0, 20.0)
    label(c, f'2T0C RT L{int(Lr)}|{"SN PAD" if sn_pad else "WT W50 L10"}', -yew - 20, -xiw)
    return c
NOVEL_ORDER = [dev_4pr('NV_4PR_M1', 'Metal_1'), dev_4pr('NV_4PR_M2', 'Metal_2'),            # column 1: 4PR + FG family
               dev_fg('NV_FG_R0', 0), dev_fg('NV_FG_R2', 2), dev_fg('NV_FG_R5', 5), dev_fg('NV_FG_R2_PAD', 2, True),
               dev_split('NV_SPLIT_M1S', 'Metal_1'), dev_split('NV_SPLIT_M2S', 'Metal_2'),  # column 2: split + 2T0C
               dev_2t0c('NV_2T0C_L10', 10.0), dev_2t0c('NV_2T0C_L50', 50.0), dev_2t0c('NV_2T0C_CAL', 10.0, True)]
nv = ly.create_cell('NOVEL_DEVICES')
for d in NOVEL_ORDER: nv.insert(db.CellInstArray(d.cell_index(), db.Trans()))
NV_H = 4300.0
cols = pack_columns(nv, [d.name for d in NOVEL_ORDER], NV_H)
txt(nv, 'NOVEL DEVICES - 5UM GATE OVERLAP, IGZO 45UM PAST GATE', 0.0, 90.0, 36.0)
txt(nv, 'LEFT: 4PR GATED 4-PROBE, FG FLOATING M2 GATE ON M1 CG', 0.0, 50.0, 24.0)
txt(nv, 'RIGHT: SPLIT M1/M2 DUAL-EOT GATE, 2T0C GAIN CELL', 0.0, 16.0, 24.0)
for d in NOVEL_ORDER: print(f'   {d.name:14s} {d.bbox().width()*dbu:6.1f} x {d.bbox().height()*dbu:6.1f} um')
print(f'   NOVEL_DEVICES: columns {cols}, {nv.bbox().width()*dbu:.0f} x {nv.bbox().height()*dbu:.0f} um')

# ================================================================== 4. overlay verniers
print('\n== 4. overlay verniers')
vn = ly.create_cell('OVL_VERNIERS')
PAIRS = [('Metal_1', 'Metal_2'), ('Metal_1', 'IGZO'), ('Metal_1', 'Metal_3'), ('Metal_2', 'IGZO'), ('Metal_2', 'Metal_3'), ('IGZO', 'Metal_3')]
ABBR = {'Metal_1': 'M1', 'Metal_2': 'M2', 'Metal_3': 'M3', 'IGZO': 'IGZO'}
def vernier(c, la, lb, ox, oy, rot):
    for i in range(-12, 13):
        la_len = 45.0 if i == 0 else 30.0
        for lay, pitch, y0, y1 in ((la, 10.0, 2.0, 2.0 + la_len), (lb, 10.25, -2.0 - la_len, -2.0)):
            x = pitch * i
            box = (x - 2, y0, x + 2, y1)
            if rot: box = (box[1], box[0], box[3], box[2])
            bx(c, lay, ox + box[0], oy + box[1], ox + box[2], oy + box[3])
for j, (la, lb) in enumerate(PAIRS):
    ox, oy = (j % 3) * 480.0, -(j // 3) * 420.0
    vernier(vn, la, lb, ox + 130, oy - 200, False)       # X vernier (reads x offset)
    vernier(vn, la, lb, ox + 340, oy - 200, True)        # Y vernier (reads y offset)
    txt(vn, f'{ABBR[la]} OVER {ABBR[lb]}', ox, oy - 60, 24.0)
txt(vn, 'OVERLAY VERNIERS 0.25UM/STEP +/-3UM, FIRST LAYER TOP/RIGHT', 0.0, 20.0, 24.0)
print(f'   OVL_VERNIERS {vn.bbox().width()*dbu:.0f} x {vn.bbox().height()*dbu:.0f} um')

# ================================================================== 5. placement by clearance search
print('\n== 5. placement')
MARGIN = 80.0
def obstacles(exclude):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(top.shapes(L[n])))
    for k in top.each_inst():
        if k.cell.name in exclude: continue
        if k.cell.name.startswith('TEXT'): r += db.Region(k.bbox().enlarged(u(10), u(10))); continue
        r += flat(k)
    crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
    r += db.Region(crosses).sized(u(40.0)); r.merge(); return r.sized(u(MARGIN))
def place(cell, x0, y0, x1, y1, step=20.0):
    """top-left corner scanned from (x0, y1) rightwards/downwards; first fully clear spot inside [x0..x1]x[y0..y1]"""
    k = top.insert(db.CellInstArray(cell.cell_index(), db.Trans()))
    obs = obstacles({cell.name}); r0 = flat(k); b = r0.bbox()
    W_, H_ = b.width() * dbu, b.height() * dbu
    ny = int((y1 - y0 - H_) / step); nx = int((x1 - x0 - W_) / step)
    for iy in range(max(ny, 0) + 1):
        for ix in range(max(nx, 0) + 1):
            dx, dy = u(x0 + ix * step) - b.left, u(y1 - iy * step) - b.top
            if r0.moved(dx, dy).and_(obs).is_empty():
                k.transform(db.Trans(dx, dy)); print(f'   {cell.name:15s} placed at {bbum(k.bbox())}'); return k
    raise AssertionError(f'no clear spot for {cell.name} in [{x0},{y0}]..[{x1},{y1}]')
place(nv, 4160.0, 1700.0, 6650.0, 6250.0)   # >= 170 um below the logo
try:
    place(vn, -1200.0, 2849.0, 220.0, 4600.0)
except AssertionError:
    top.erase([k for k in top.each_inst() if k.cell.name == 'OVL_VERNIERS'][0]); place(vn, 2900.0, 1700.0, 6650.0, 6360.0)

exec(open(os.path.join(HERE, 'verify_v51.py'), encoding='utf-8').read())
