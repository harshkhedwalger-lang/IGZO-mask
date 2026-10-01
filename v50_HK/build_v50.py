"""build_v50.py -- v49 -> v50   (klayout.db only; OASIS + GDS copy)

High-Id TFT block (PERF_TFT) redrawn to the SAME source/drain-overlap convention as the main
TFTs (Transistors_BottomGate, measured, identical in all 12 devices):
    gate = L + 2 x 5 um        -> gate overlaps each S/D electrode by exactly 5 um
    IGZO extends 45 um beyond each gate edge under the electrode (ungated contact region)
    electrode runs past the IGZO edge; W = electrode width, IGZO 10 um wider on each W side
    gate runs out along W, flush with the IGZO at the far end, never under an electrode

  REF W100 L10 + L ladder (2,3,5,20,50,100): exactly that cross-section (rotated 90 deg so the pads
      stay gate W / source N / drain S) -> Rc and dL extracted here apply to the main TFTs.
  LOV sweep: IGZO extension fixed at 45 um, only the gated overlap per side varies:
      2 / 5 (= REF) / 10 / 20 / 40 um.  PT_LOV5 duplicated REF -> becomes PT_LOV10.
  IDT W1000 L10, W1000 L5, W2000 L10: inner fingers stay 10 um under the continuous gate (= 5 um per
      channel side); the two outer fingers 10 -> 5 um so every channel edge gets 5 um. A 45 um ungated
      extension is NOT added here: it would force the gate lead under an electrode (dense IDTs keep
      all-gated contacts -- stated trade-off).
Block re-packed column-first again (cell sizes changed); SYN_1T1R kept right beside it.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v49_HK', 'v49_HK.oas')
OUT = os.path.join(HERE, 'v50_HK')
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
def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(min(x0, x1)), u(min(y0, y1)), u(max(x0, x1)), u(max(y0, y1))))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
PAD, PW, TAPER = 150.0, 140.0, 75.0          # mask standard since v46
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
    """same placement rule as the original cells: below the gate pad, right-aligned left of the drain pad"""
    yl = min(-PAD / 2, y_low) - 20.0; xr = min(-PAD / 2, x_left) - 15.0
    for line in text.split('|'):
        wl = tg.text(line, dbu, 24.0 * MAG1).bbox().width() * dbu
        yl -= 32.0
        txt(c, line, xr - wl, yl, 24.0)

LOV_STD, EXT, EOUT, WOV = 5.0, 45.0, 10.0, 10.0
def single_tft(c, W, Lg, lov, text):
    """main-TFT cross-section, channel along y: source on top, drain below, gate strip exits west"""
    hg = Lg / 2 + lov; yi = hg + EXT; ye = yi + EOUT; xi = W / 2 + WOV; xg0 = -xi - 20.0
    bx(c, 'IGZO', -xi, -yi, xi, yi)
    bx(c, 'Metal_3', -W / 2, Lg / 2, W / 2, ye)              # source electrode (W wide)
    bx(c, 'Metal_3', -W / 2, -ye, W / 2, -Lg / 2)            # drain electrode
    bx(c, 'Metal_1', xg0, -hg, xi, hg)                       # gate: L + 2*lov, flush with IGZO at the far end
    pad_lead(c, 'Metal_1', xg0, 0.0, 'W', 2 * hg, 20.0)
    pad_lead(c, 'Metal_3', 0.0, ye, 'N', W, 20.0)
    pad_lead(c, 'Metal_3', 0.0, -ye, 'S', W, 20.0)
    label(c, text, -ye, -xi)
def idt_tft(c, W, Lg, n, text, wf=10.0, wf_out=5.0):
    """interdigitated: continuous gate, inner fingers wf (5 um per channel side), outer fingers wf_out"""
    Wf = W / n; widths = [wf_out] + [wf] * (n - 1) + [wf_out]
    cx = sum(widths) + n * Lg; x0 = -cx / 2; eg = 5.0
    busw = 30.0 if W >= 1000 else 20.0
    bx(c, 'IGZO', x0, -Wf / 2, -x0, Wf / 2)
    bx(c, 'Metal_1', x0 - eg, -Wf / 2 - eg, -x0 + eg, Wf / 2 + eg)
    yS0, yS1 = Wf / 2 + 20, Wf / 2 + 20 + busw; yD1, yD0 = -(Wf / 2 + 20), -(Wf / 2 + 20 + busw)
    fx = x0
    for k, w in enumerate(widths):
        if k % 2 == 0: bx(c, 'Metal_3', fx, -Wf / 2 - 5, fx + w, yS0)
        else:          bx(c, 'Metal_3', fx, yD1, fx + w, Wf / 2 + 5)
        fx += w + Lg
    bx(c, 'Metal_3', x0, yS0, -x0, yS1); bx(c, 'Metal_3', x0, yD0, -x0, yD1)
    pad_lead(c, 'Metal_1', x0 - eg, 0.0, 'W', min(20.0, Wf + 2 * eg), 20.0)
    pad_lead(c, 'Metal_3', 0.0, yS1, 'N', 30.0, 20.0)
    pad_lead(c, 'Metal_3', 0.0, yD0, 'S', 30.0, 20.0)
    label(c, text, yD0, x0)

SPEC = {  # cell -> (kind, args)
    'PT_REF_W100_L10':  ('s', (100, 10, 5.0, 'REF|W100 L10')),
    'PT_IDT_W1000_L10': ('i', (1000, 10, 10, 'IDT|W1000 L10')),
    'PT_IDT_W1000_L5':  ('i', (1000, 5, 10, 'IDT|W1000 L5')),
    'PT_IDT_W2000_L10': ('i', (2000, 10, 10, 'IDT|W2000 L10')),
    'PT_LOV2':  ('s', (100, 10, 2.0, 'LOV2|W100 L10')),
    'PT_LOV10': ('s', (100, 10, 10.0, 'LOV10|W100 L10')),
    'PT_LOV20': ('s', (100, 10, 20.0, 'LOV20|W100 L10')),
    'PT_LOV40': ('s', (100, 10, 40.0, 'LOV40|W100 L10')),
    **{f'PT_L{l}': ('s', (100, l, 5.0, f'L{l}|W100')) for l in (2, 3, 5, 20, 50, 100)},
}
print('== 1. redraw the 14 high-Id TFT cells to the main-TFT overlap convention')
ly.cell('PT_LOV5').name = 'PT_LOV10'
for name, (kind, a) in SPEC.items():
    c = ly.cell(name)
    assert sum(c.shapes(i).size() for n, i in L.items() if n not in LAY) == 0 and c.child_instances() == 0
    for n in LAY: c.shapes(L[n]).clear()
    (single_tft if kind == 's' else idt_tft)(c, *a)
    b = c.bbox(); print(f'   {name:18s} {b.width()*dbu:6.1f} x {b.height()*dbu:6.1f} um')

# ============================================================== 2. re-pack column-first (same rule as v49)
GAP_Y, GAP_X, BLOCK_GAP = 50.0, 60.0, 120.0
BOTTOM_LIMIT = 1338.0 + 60.0
ORDER = {
    'PERF_TFT': ['PT_REF_W100_L10', 'PT_IDT_W1000_L10', 'PT_IDT_W1000_L5', 'PT_IDT_W2000_L10',
                 'PT_LOV2', 'PT_LOV10', 'PT_LOV20', 'PT_LOV40', 'PT_L2', 'PT_L3', 'PT_L5', 'PT_L20', 'PT_L50', 'PT_L100'],
    'SYN_1T1R': ['SYN_W500_L20_J2', 'SYN_W500_L20_J4', 'SYN_W250_L10_J2', 'SYN_W250_L10_J4',
                 'SYN_W125_L5_J2', 'SYN_W125_L5_J4', 'SYN_W50_L2_J2', 'SYN_W50_L2_J4'],
}
def inst(name): return [k for k in top.each_inst() if k.cell.name == name][0]
def bbum(b): return [round(v * dbu, 1) for v in (b.left, b.bottom, b.right, b.top)]
def repack(bname):
    c = ly.cell(bname); k = inst(bname)
    ins = {i.cell.name: i for i in c.each_inst()}
    assert sorted(ins) == sorted(ORDER[bname]), bname
    x0, ytop = 5.0, -5.0
    H = (k.trans.disp.y * dbu + ytop) - BOTTOM_LIMIT
    cols, col, h = [], [], 0.0
    for n in ORDER[bname]:
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
    print(f'   {bname}: {len(cols)} columns {[len(cl) for cl in cols]}')
print('\n== 2. re-pack')
pk = [k for k in top.each_inst() if k.cell.name == 'PERF_TFT'][0]
repack('PERF_TFT')
sk = inst('SYN_1T1R'); pb = pk.bbox(); sb = sk.bbox()
sk.transform(db.Trans(pb.right + u(BLOCK_GAP) - sb.left, pb.top - sb.top))
print('   PERF_TFT TOP bbox', bbum(pk.bbox()), '  SYN_1T1R TOP bbox', bbum(sk.bbox()))

exec(open(os.path.join(HERE, 'verify_v50.py'), encoding='utf-8').read())
