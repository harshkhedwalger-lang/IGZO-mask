"""build_v48.py -- v47 -> v48   (klayout.db only; OASIS + GDS copy)

A. Memristors_Gated (14 devices): compact pad-out. v47 regrew 100x100 pads from the OUTER edge of
   the old 81um-pad footprint, so the TE and Gate arms still carried an 80x80um stub where the old
   pad used to be, plus a 75um taper that only widened 80->100um. Now every device is clipped back
   to its junction core (x 80..176, y 80..220 local -- the old small tapers + junction, untouched)
   and each terminal gets its 100x100 pad straight off the core edge with a 30um taper.
   526x427um -> ~356x277um per device. Block re-gridded, top-left corner kept in place.

B. MEM_HIGH_VALUE (8 devices): outer arms rebuilt around byte-identical device cores.
   - pads 150 -> 100 (90 window), taper 40um, pad pitch from the device centre 305 -> 180um
   - 5th terminal (series-resistor gate on M1 / guard ring on M3) moved to a diagonal corner pad
     on a straight 45-deg-ish route inside the free quadrant. The old L-routes ran under the S pad
     (M1, series column) and INTO the S taper (M3, guard column -> guard shorted to TE since at
     least v38 -- checked).
   - device pitch 680/800 -> 540/540; titles/labels moved with their devices.

C. TestStructures as one left-aligned column (top->bottom):
   TLM back-bias | gated VdP + gated Greek cross (side by side) + their label | Gate Oxide 1 | Gate Oxide 2
   - the Greek cross was loose TOP-own geometry; moved into TestStructures under the TLM as asked
   - TEXT$127 ('GATED VDP & GREEK CROSS') is the real label for the pair -> moved with them; the
     duplicate title I added in v45 is deleted
   - FIX: all 4 S/D contact windows (Isolation_1) of BOTH gated structures sat fully on the M1
     gate plate. By this process's own rule an Iso1 window on M1 etches Al2O3 AND HfO2, so IGZO and
     the M3 pad land on the gate -> every contact shorted to the gate. Those 8 windows are removed;
     the M3 pads now contact IGZO directly, exactly like every other TFT on this reticle. The two
     gate-pad windows (on M1, no IGZO, M3-capped) are kept.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v47_HK', 'v47_HK.oas')
OUT = os.path.join(HERE, 'v48_HK')
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
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500
def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(min(x0, x1)), u(min(y0, y1)), u(max(x0, x1)), u(max(y0, y1))))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
def pad_lead(c, met, ax, ay, d, w, llen, PAD, PW, TAPER):
    """this mask's own recipe (lead + taper + pad); M1/M2 pad: Iso1 window + M3 cap + passivation"""
    sx, sy = {'N': (0, 1), 'S': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[d]
    def pt(a, b): return (ax + sx * a - sy * b, ay + sy * a + sx * b)
    if llen > 0: poly(c, met, [pt(0, -w / 2), pt(llen, -w / 2), pt(llen, w / 2), pt(0, w / 2)])
    a0 = llen; a1 = llen + TAPER
    poly(c, met, [pt(a0, -w / 2), pt(a1, -PAD / 2), pt(a1, PAD / 2), pt(a0, w / 2)])
    (x0, y0), (x1, y1) = pt(a1, -PAD / 2), pt(a1 + PAD, PAD / 2)
    bx(c, met, x0, y0, x1, y1)
    e = (PAD - PW) / 2
    xa, xb, ya, yb = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
    if met in ('Metal_1', 'Metal_2'):
        bx(c, 'Isolation_1', xa + e, ya + e, xb - e, yb - e); bx(c, 'Metal_3', xa, ya, xb, yb)
    bx(c, PASS, xa + e, ya + e, xb - e, yb - e)
def pad_at(c, met, cx, cy, PAD, PW):
    x0, y0, x1, y1 = cx - PAD / 2, cy - PAD / 2, cx + PAD / 2, cy + PAD / 2
    bx(c, met, x0, y0, x1, y1); e = (PAD - PW) / 2
    if met in ('Metal_1', 'Metal_2'):
        bx(c, 'Isolation_1', x0 + e, y0 + e, x1 - e, y1 - e); bx(c, 'Metal_3', x0, y0, x1, y1)
    bx(c, PASS, x0 + e, y0 + e, x1 - e, y1 - e)
def route(c, met, sx, sy, px, py, w=10.0, back=3.0):
    dx, dy = px - sx, py - sy; n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
    nx, ny = -uy * w / 2, ux * w / 2; ax, ay = sx - ux * back, sy - uy * back
    poly(c, met, [(ax + nx, ay + ny), (px + nx, py + ny), (px - nx, py - ny), (ax - nx, ay - ny)])
def other_layer_shapes(c):
    return sum(c.shapes(i).size() for n, i in L.items() if n not in LAY)

# =================================================================================== A
print('== A. Memristors_Gated: compact pad-out')
GROUPS = [('2', ['G2', 'O2', 'V2', 'A3']), ('3', ['G3', 'O3', 'V3', 'T3']), ('4', ['G4', 'O4', 'V4']), ('6', ['G6', 'O6', 'V6'])]
DEV14 = [f'MEM_{ty}_1' for _, tys in GROUPS for ty in tys]
A_PAD, A_PW, A_TAPER = 100.0, 90.0, 30.0
CORE_A = db.Region(db.Box(u(80), u(80), u(176), u(220)))
for name in DEV14:
    c = ly.cell(name)
    assert other_layer_shapes(c) == 0, name
    labels = []; keep = {n: db.Region() for n in LAY}
    for n in LAY:
        for s in c.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            p = s.polygon
            if n == 'Metal_1' and isglyph(p) and p.bbox().bottom * dbu > 200: labels.append(p); continue
            keep[n].insert(p)
    for n in LAY: keep[n] = keep[n] & CORE_A
    for n in LAY: c.shapes(L[n]).clear()
    for n in LAY:
        for p in keep[n].each(): c.shapes(L[n]).insert(p)
    for p in labels: c.shapes(L['Metal_1']).insert(p.moved(0, u(-25.0)))
    pad_lead(c, 'Metal_1', 128.0, 80.0, 'S', 80.0, 0.0, A_PAD, A_PW, A_TAPER)   # Gate
    pad_lead(c, 'Metal_2', 80.0, 128.0, 'W', 80.0, 0.0, A_PAD, A_PW, A_TAPER)   # BE
    pad_lead(c, 'Metal_3', 176.0, 128.0, 'E', 80.0, 0.0, A_PAD, A_PW, A_TAPER)  # TE
ub = db.Box()
for n in DEV14: ub += ly.cell(n).bbox()
DEV_X0, DEV_Y0 = ub.left * dbu, ub.bottom * dbu
DEV_W, DEV_H = (ub.right - ub.left) * dbu, (ub.top - ub.bottom) * dbu
print(f'   device footprint {DEV_W:.1f} x {DEV_H:.1f} um (v47: 526 x 427)')

gm = ly.cell('Memristors_Gated')
mgk = [k for k in top.each_inst() if k.cell.name == 'Memristors_Gated'][0]
old_tl = (mgk.bbox().left, mgk.bbox().top)
insts = [k for k in gm.each_inst()]
assert sorted(k.cell.name for k in insts) == sorted(DEV14)
dev_ci = {n: ly.cell(n).cell_index() for n in DEV14}
for k in list(insts): gm.erase(k)
for s in list(gm.shapes(L['Metal_1']).each()):
    if s.is_polygon() and isglyph(s.polygon): gm.shapes(L['Metal_1']).erase(s)
assert all(gm.shapes(L[n]).is_empty() for n in LAY)
COL = DEV_W + 50.0; GGY = 120.0
gy0 = [(3 - gi) * (DEV_H + GGY) for gi in range(4)]
for gi, (lab, tys) in enumerate(GROUPS):
    for tci, ty in enumerate(tys):
        gm.insert(db.CellInstArray(dev_ci[f'MEM_{ty}_1'], db.Trans(u(tci * COL - DEV_X0), u(gy0[gi] - DEV_Y0))))
    txt(gm, f'L = {lab} UM', 0.0, gy0[gi] + DEV_H + 20.0, 24.0)
txt(gm, 'GATED MEMRISTORS - 1X/TYPE, GROUPED BY GAP LENGTH', 0.0, gy0[0] + DEV_H + 70.0, 36.0)
nb = mgk.bbox(); mgk.transform(db.Trans(old_tl[0] - nb.left, old_tl[1] - nb.top))
print('   Memristors_Gated TOP bbox', [round(v * dbu, 1) for v in (mgk.bbox().left, mgk.bbox().bottom, mgk.bbox().right, mgk.bbox().top)])

# =================================================================================== B
print('\n== B. MEM_HIGH_VALUE: compact arms around untouched cores')
hv = ly.cell('MEM_HIGH_VALUE')
assert other_layer_shapes(hv) == 0 and hv.child_instances() == 0
OLDC = [(310, -220), (310, -1020), (310, -1820), (310, -2620), (990, -220), (990, -1020), (990, -1820), (990, -2620)]
NEWC = [(235, -145), (235, -685), (235, -1225), (235, -1765), (775, -145), (775, -685), (775, -1225), (775, -1765)]
B_PAD, B_PW, B_TAPER = 100.0, 90.0, 40.0
CH, HH, VW = 90.0, 35.0, 15.0
D5 = CH + B_TAPER + B_PAD / 2
allp = {n: [s.polygon for s in hv.shapes(L[n]).each() if (s.is_polygon() or s.is_box())] for n in LAY}
def coreboxes(cx, cy):
    return (db.Region(db.Box(u(cx - CH), u(cy - HH), u(cx + CH), u(cy + HH))),
            db.Region(db.Box(u(cx - VW), u(cy - CH), u(cx + VW), u(cy + CH))))
def seg(region, box, along_y):
    r = region & db.Region(box)
    assert not r.is_empty(), 'arm crossing not found'
    b = r.bbox()
    return (((b.bottom + b.top) / 2 * dbu, (b.top - b.bottom) * dbu) if along_y
            else ((b.left + b.right) / 2 * dbu, (b.right - b.left) * dbu))
devs = []
core_union = db.Region()
for (cx, cy) in OLDC:
    bh, bv = coreboxes(cx, cy); core_union += bh + bv
    reg = {n: db.Region(allp[n]) & (bh + bv if n == 'Metal_3' else bh) for n in LAY}
    W = seg(reg['Metal_2'], db.Box(u(cx - CH), u(cy - HH), u(cx - CH + 1), u(cy + HH)), True)
    E = seg(reg['Metal_2'], db.Box(u(cx + CH - 1), u(cy - HH), u(cx + CH), u(cy + HH)), True)
    N = seg(reg['Metal_3'], db.Box(u(cx - VW), u(cy + CH - 1), u(cx + VW), u(cy + CH)), False)
    S = seg(reg['Metal_3'], db.Box(u(cx - VW), u(cy - CH), u(cx + VW), u(cy - CH + 1)), False)
    fifth = None
    if cx < 600:
        st = (cx - 10.0, cy - 30.0); met5 = 'Metal_1'; side = -1
        fifth = (met5, st, side)
    else:
        # guard-ring devices: the ring's right bar has a short stub below the ring (y -35..-28) that fed the
        # old 5th pad. NOTE the ring is drawn CLOSED across the TE line on M3, so ring == TE electrically in
        # the core already; we keep that topology exactly (5th pad on the ring) and flag it, not redesign it.
        stub = reg['Metal_3'] & db.Region(db.Box(u(cx + 10), u(cy - 35), u(cx + 40), u(cy - 33)))  # below the ring bar
        if not stub.is_empty():
            bb = stub.bbox(); st = ((bb.left + bb.right) / 2 * dbu, cy - 34.0); fifth = ('Metal_3', st, +1)
    if fifth:
        met5, st, _ = fifth
        probe = db.Region(db.Box(u(st[0]) - 500, u(st[1]) - 500, u(st[0]) + 500, u(st[1]) + 500))
        assert not (reg[met5] & probe).is_empty(), ('5th-terminal start not on metal', cx, cy)
    devs.append((cx, cy, reg, W, E, N, S, fifth))
    print(f'   core ({cx},{cy}): W w={W[1]:.1f} E w={E[1]:.1f} N w={N[1]:.1f} S w={S[1]:.1f} 5th={fifth[0] if fifth else None}')

labels = []
for p in allp['Metal_1']:
    if not isglyph(p) or not (db.Region(p) & core_union).is_empty(): continue
    b = p.bbox(); yb = b.bottom * dbu; xl = b.left * dbu
    if yb >= 190: sh = (0.0, 0.0)                                 # block title
    elif yb >= 100: sh = (0.0, 0.0) if xl < 600 else (-140.0, 0.0)  # column headers
    else:
        xc, yc = (b.left + b.right) / 2 * dbu, (b.bottom + b.top) / 2 * dbu
        i = min(range(8), key=lambda k: (OLDC[k][0] - xc) ** 2 + (OLDC[k][1] - yc) ** 2)
        sh = (NEWC[i][0] - OLDC[i][0], NEWC[i][1] - OLDC[i][1])
    labels.append((p, sh))
print(f'   {len(labels)} label glyph polygons re-anchored')

for n in LAY: hv.shapes(L[n]).clear()
for (cx, cy, reg, W, E, N, S, fifth), (ncx, ncy) in zip(devs, NEWC):
    dx, dy = ncx - cx, ncy - cy
    for n in LAY:
        for p in reg[n].each(): hv.shapes(L[n]).insert(p.moved(u(dx), u(dy)))
    pad_lead(hv, 'Metal_2', ncx - CH, W[0] + dy, 'W', W[1], 0.0, B_PAD, B_PW, B_TAPER)
    pad_lead(hv, 'Metal_2', ncx + CH, E[0] + dy, 'E', E[1], 0.0, B_PAD, B_PW, B_TAPER)
    pad_lead(hv, 'Metal_3', N[0] + dx, ncy + CH, 'N', N[1], 0.0, B_PAD, B_PW, B_TAPER)
    pad_lead(hv, 'Metal_3', S[0] + dx, ncy - CH, 'S', S[1], 0.0, B_PAD, B_PW, B_TAPER)
    if fifth:
        met5, st, side = fifth
        px, py = ncx + side * D5, ncy - D5
        route(hv, met5, st[0] + dx, st[1] + dy, px, py, 10.0)
        pad_at(hv, met5, px, py, B_PAD, B_PW)
for p, (sx, sy) in labels: hv.shapes(L['Metal_1']).insert(p.moved(u(sx), u(sy)))
hvk = [k for k in top.each_inst() if k.cell.name == 'MEM_HIGH_VALUE'][0]
print('   MEM_HIGH_VALUE TOP bbox', [round(v * dbu, 1) for v in (hvk.bbox().left, hvk.bbox().bottom, hvk.bbox().right, hvk.bbox().top)], '(v47: -3169.5,-5762.1,-1868,-2510)')

# =================================================================================== C
print('\n== C. TestStructures: single column, gated VdP + Greek cross under the TLM')
ts = ly.cell('TestStructures')
tsk = [k for k in top.each_inst() if k.cell.name == 'TestStructures'][0]
DX0, DY0 = tsk.trans.disp.x * dbu, tsk.trans.disp.y * dbu
ALLN = list(L.keys())
def own_in(cell, x0, x1, y0, y1):
    out = []
    for n in ALLN:
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box() or s.is_path()): continue
            b = s.bbox()
            if b.left * dbu >= x0 and b.right * dbu <= x1 and b.bottom * dbu >= y0 and b.top * dbu <= y1:
                out.append((n, s))
    return out
# ---- capture (read-only) ----
tlm = own_in(ts, -2200, 0, 300, 2000)
vdp = own_in(ts, -50, 1600, 300, 2000)
ox1 = own_in(ts, -2200, 2100, -1070, -290)
tlm_i = [k for k in ts.each_inst() if k.bbox().right * dbu <= 0 and k.bbox().bottom * dbu >= 300]
ox1_i = [k for k in ts.each_inst() if k.cell.name.startswith('TEXT') and k.bbox().bottom * dbu >= -1070 and k.bbox().top * dbu <= -290]
gx_win = db.Box(u(1650), u(-5330), u(2930), u(-4380))
greek = [(n, s) for n in ALLN for s in top.shapes(L[n]).each()
         if (s.is_polygon() or s.is_box() or s.is_path()) and gx_win.contains(s.bbox().p1) and gx_win.contains(s.bbox().p2)]
t127 = [k for k in top.each_inst() if k.cell.name == 'TEXT$127'][0]
print(f'   captured: TLM {len(tlm)} shapes + {len(tlm_i)} labels | VdP {len(vdp)} shapes | Gate-Ox-1 {len(ox1)} shapes + {len(ox1_i)} labels | Greek cross {len(greek)} TOP shapes')
assert len(tlm_i) == 10 and len(ox1_i) == 25
def is_v45_title(n, s): return n == 'Metal_1' and isglyph(s.polygon) and s.bbox().bottom * dbu > 1400
vdp_struct = [(n, s) for n, s in vdp if not is_v45_title(n, s)]
vdp_title = [(n, s) for n, s in vdp if is_v45_title(n, s)]
title_area_um2 = sum(s.polygon.area() for _, s in vdp_title) * dbu * dbu
print(f'   duplicate v45 VdP title: {len(vdp_title)} glyph polygons to delete ({title_area_um2:.0f} um2)')
# per-layer shape-area totals of everything in the reorganised zone, BEFORE (for congruence check)
def area_sum(items):
    a = Counter()
    for n, s in items: a[n] += s.polygon.area() * dbu * dbu
    return a
pre_area = area_sum(tlm + vdp + ox1 + greek)
def drop_gate_windows(items, to_local=(0.0, 0.0)):
    ig = db.Region([s.polygon for n, s in items if n == 'IGZO'])
    keepl, dropped = [], 0
    for n, s in items:
        if n == 'Isolation_1' and not (db.Region(s.polygon) & ig).is_empty(): dropped += 1; continue
        keepl.append((n, s))
    return keepl, dropped
vdp_keep, dv = drop_gate_windows(vdp_struct)
greek_keep, dg = drop_gate_windows(greek)
print(f'   S/D contact windows sitting on the gate removed: VdP {dv}, Greek cross {dg}')
assert dv == 4 and dg == 4
tlm_p = [(n, s.polygon) for n, s in tlm]; vdp_p = [(n, s.polygon) for n, s in vdp_keep]
ox1_p = [(n, s.polygon) for n, s in ox1]; gr_p = [(n, s.polygon) for n, s in greek_keep]
tlm_ct = [(k.cell_index, k.trans) for k in tlm_i]; ox1_ct = [(k.cell_index, k.trans) for k in ox1_i]
def bbox_of(polys):
    b = db.Box()
    for n, p in polys:
        if n in LAY: b += p.bbox()
    return b
vb = bbox_of(vdp_p); gb = bbox_of(gr_p); tb = bbox_of(tlm_p)
# ---- layout (local coords); Gate Oxide 2 stays put ----
G = 100.0
OX2_TOP = -1144.0
ox1_bottom_old = -1054.0
ox1_bottom = OX2_TOP + G;           dy_ox1 = ox1_bottom - ox1_bottom_old
row_bottom = ox1_bottom + 746.0 + G
lab_bottom = row_bottom + max(vb.height(), gb.height()) * dbu + 40.0
tlm_bottom = lab_bottom + 70.0 + G; dy_tlm = tlm_bottom - tb.bottom * dbu
LEFT = -2134.0
v_d = (LEFT - vb.left * dbu, row_bottom - vb.bottom * dbu)
g_off = (LEFT + vb.width() * dbu + 200.0, row_bottom)
print(f'   Gate-Ox-1 dy={dy_ox1:+.1f} | VdP+Greek row y {row_bottom:.1f}..{row_bottom + vb.height() * dbu:.1f} | label y {lab_bottom:.1f} | TLM dy={dy_tlm:+.1f}')
# ---- erase ----
for n, s in tlm + vdp + ox1: ts.shapes(L[n]).erase(s)
for k in tlm_i + ox1_i: ts.erase(k)
for n, s in greek: top.shapes(L[n]).erase(s)
# ---- insert ----
for n, p in tlm_p: ts.shapes(L[n]).insert(p.moved(0, u(dy_tlm)))
for ci, tr in tlm_ct: ts.insert(db.CellInstArray(ci, db.Trans(0, u(dy_tlm)) * tr))
for n, p in ox1_p: ts.shapes(L[n]).insert(p.moved(0, u(dy_ox1)))
for ci, tr in ox1_ct: ts.insert(db.CellInstArray(ci, db.Trans(0, u(dy_ox1)) * tr))
for n, p in vdp_p: ts.shapes(L[n]).insert(p.moved(u(v_d[0]), u(v_d[1])))
gx_local_left = gb.left * dbu - DX0; gx_local_bottom = gb.bottom * dbu - DY0
gdx = g_off[0] - gx_local_left - DX0; gdy = g_off[1] - gx_local_bottom - DY0
for n, p in gr_p: ts.shapes(L[n]).insert(p.moved(u(gdx), u(gdy)))
t_old = t127.bbox()
t127.transform(db.Trans(u(LEFT + DX0) - t_old.left, u(lab_bottom + DY0) - t_old.bottom))
tl_top = (tb.top * dbu + dy_tlm)
print(f'   column top (TLM title) local y ~{max(tl_top, 1811.1 + dy_tlm):.1f}; 1T1R bottom is local {-2813.5 - DY0:.1f}')

exec(open(os.path.join(HERE, 'verify_v48.py'), encoding='utf-8').read())
