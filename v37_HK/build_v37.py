"""build_v37.py -- v36 -> v37   (klayout.db only; OASIS + GDS copy)

Adds two publication-oriented blocks, nothing else changes:

  SYN_1T1R   gate-set-compliance analog synapse.  Compact 4-pad cell (N/S/E/W):
             W = gate, N = source, S = drain / memristor-BE node, E = memristor TE.
             The S pad on the internal node lets the SAME junction be measured as a bare 1R
             (TE <-> node) and as 1T1R (TE <-> source, gate = compliance knob) -> direct proof that
             transistor compliance cuts variability / enables analog levels.
             Driver W/L fixed at 25 (owner requirement) while the footprint shrinks:
             W500/L20 (4 fingers), W250/L10 (2), W125/L5 (1), W50/L2 (1)  x  junction 2x2 and 4x4 um.
  PERF_TFT   high-Id / mobility / footprint study, 3 pads (W gate, N source, S drain):
             - interdigitated W1000/L10, W1000/L5, W2000/L10 vs straight W100/L10  (Id per um2)
             - contact-overlap (Lov = finger width) sweep 2/5/10/20/40 um at W100/L10 (R_c, transfer length)
             - channel-length ladder L = 2/3/5/10/20/50/100 um at W100 (R_c*W and intrinsic mobility)

Device rules used (6-layer flow M1|Al2O3|M2|HfO2|[Iso1]|IGZO|M3|Passivation):
  - W defined by the IGZO island edge (fingers overshoot it by 5 um), L by the M3 finger gap: single edge.
  - gate M1 encloses IGZO + fingers by 5 um; no M2 anywhere near a channel.
  - memristor = M2 / HfO2 / IGZO / M3 cross-point, area = neck x neck (both necks run >=10 um past the
    crossing); drain -> BE through an Iso1 window on an M2 plate clear of M1 (60 um from the gate).
  - every pad is the standard 160 um pad with a 75 um taper; M1 pad = M1 + Iso1 + M3 cap + passivation.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v36_HK', 'v36_HK.oas')
OUT = os.path.join(HERE, 'v37_HK')
MINF = 2.0; PAD, PW, TAPER = 160.0, 150.0, 75.0
ENC = mkaudit.ENC; OVL = mkaudit.OVL
GAP = 80.0                                                                 # cell-to-cell edge gap

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')

def bx(c, l, x0, y0, x1, y1):
    c.shapes(L[l]).insert(db.Box(u(min(x0, x1)), u(min(y0, y1)), u(max(x0, x1)), u(max(y0, y1))))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
LABELS = {}                                       # cell name -> exact label polygons written (for verification)
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r)
    LABELS.setdefault(c.name, db.Region()).insert(r)
    return r.bbox().width() * dbu
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500

def pad_lead(c, met, ax, ay, d, w, llen):
    """lead of width w from anchor (ax,ay) in direction d ('N','S','E','W'), llen straight + 75 um taper
       + 160 um pad. M1/M2 pad gets Iso1 window, M3 cap and passivation window; M3 pad gets passivation."""
    sx, sy = {'N': (0, 1), 'S': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[d]
    def pt(a, b):                                   # a = along the lead, b = across it
        return (ax + sx * a - sy * b, ay + sy * a + sx * b)
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

def tft_cell(name, W, Lg, n, wf=10.0, s=None, label=None):
    """bottom-gate staggered TFT, n channels of width Wf = W/n between interdigitated M3 fingers of width wf.
       If s is given, an M2/HfO2/IGZO/M3 s x s memristor hangs off the drain (1T1R synapse cell)."""
    c = ly.create_cell(name); Wf = W / n
    cx = (n + 1) * wf + n * Lg; x0 = -cx / 2; eg = 5.0
    busw = 30.0 if W >= 1000 else 20.0
    bx(c, 'IGZO', x0, -Wf / 2, -x0, Wf / 2)                                           # W set by IGZO edge
    bx(c, 'Metal_1', x0 - eg, -Wf / 2 - eg, -x0 + eg, Wf / 2 + eg)                    # gate
    yS0, yS1 = Wf / 2 + 20, Wf / 2 + 20 + busw                                        # source bus (top)
    yD1, yD0 = -(Wf / 2 + 20), -(Wf / 2 + 20 + busw)                                  # drain bus (bottom)
    for k in range(n + 1):
        fx0 = x0 + k * (wf + Lg)
        if k % 2 == 0: bx(c, 'Metal_3', fx0, -Wf / 2 - 5, fx0 + wf, yS0)             # S finger, tip 5 um past IGZO
        else:          bx(c, 'Metal_3', fx0, yD1, fx0 + wf, Wf / 2 + 5)              # D finger
    bx(c, 'Metal_3', x0, yS0, -x0, yS1)
    xm = -x0 + eg + 90.0                                                              # memristor column
    bx(c, 'Metal_3', x0, yD0, (xm + 30.0) if s else -x0, yD1)
    gw = min(20.0, Wf + 2 * eg)
    pad_lead(c, 'Metal_1', x0 - eg, 0.0, 'W', gw, 20.0)                               # gate  (W)
    pad_lead(c, 'Metal_3', 0.0, yS1, 'N', 30.0, 20.0)                                 # source (N)
    pad_lead(c, 'Metal_3', 0.0, yD0, 'S', 30.0, 20.0)                                 # drain / BE node (S)
    if s:
        yp1 = -40.0; yp0 = min(-100.0, yD0)
        bx(c, 'Metal_3', xm - 30, yp0, xm + 30, yp1)                                  # drain plate (M3)
        bx(c, 'Metal_2', xm - 30, -100.0, xm + 30, yp1)                               # BE plate (M2)
        bx(c, 'Isolation_1', xm - 20, -90.0, xm + 20, yp1 - 10)                       # D -> BE contact
        poly(c, 'Metal_2', [(xm - 30, yp1), (xm + 30, yp1), (xm + s / 2, -10.0), (xm - s / 2, -10.0)])
        bx(c, 'Metal_2', xm - s / 2, -10.0, xm + s / 2, 15.0)                         # BE neck (vertical)
        bx(c, 'IGZO', xm - 12, -12, xm + 12, 12)                                      # switching island
        bx(c, 'Metal_3', xm - 15, -s / 2, xm + 40, s / 2)                             # TE neck (horizontal)
        pad_lead(c, 'Metal_3', xm + 40, 0.0, 'E', s, 0.0)                             # TE (E)
    if label:                                    # lower-left quadrant: under the gate pad, right-aligned 15 um
        yl = min(-PAD / 2, yD0) - 20.0           # below the gate pad AND below the drain bus
        xr = min(-PAD / 2, x0) - 15.0            # left of the south pad column AND of the comb/bus
        for line in label.split('|'):
            wl = tg.text(line, dbu, 24.0 * MAG1).bbox().width() * dbu
            yl -= 24.0 + 8.0
            txt(c, line, xr - wl, yl, 24.0)
    return c

# ============================================================== build the cells
SYN = []
for (W, Lg, n) in ((500, 20, 4), (250, 10, 2), (125, 5, 1), (50, 2, 1)):
    for s in (2, 4):
        SYN.append(tft_cell(f'SYN_W{W}_L{Lg}_J{s}', W, Lg, n, 10.0, s, f'W{W} L{Lg}|J{s}X{s}'))
PERF = []
for (W, Lg, n, wf, lab) in ((100, 10, 1, 10, 'REF|W100 L10'), (1000, 10, 10, 10, 'IDT|W1000 L10'),
                            (1000, 5, 10, 10, 'IDT|W1000 L5'), (2000, 10, 10, 10, 'IDT|W2000 L10')):
    PERF.append(tft_cell(f'PT_{lab.replace('|', '_').replace(' ', '_')}', W, Lg, n, wf, None, lab))
for wf in (2, 5, 20, 40):
    PERF.append(tft_cell(f'PT_LOV{wf}', 100, 10, 1, wf, None, f'LOV{wf}|W100 L10'))
for Lg in (2, 3, 5, 20, 50, 100):
    PERF.append(tft_cell(f'PT_L{Lg}', 100, Lg, 1, 10, None, f'L{Lg}|W100'))

def block(name, cells, heading, sub, maxw):
    """pack cells left->right, top->bottom with GAP between cell bboxes; heading on top"""
    blk = ly.create_cell(name)
    x = y = 0.0; rowh = 0.0
    for c in cells:
        b = c.bbox(); w, h = b.width() * dbu, b.height() * dbu
        if x > 0 and x + w > maxw: x = 0.0; y -= rowh + GAP; rowh = 0.0
        blk.insert(db.CellInstArray(c.cell_index(), db.Trans(u(x) - b.left, u(y - h) - b.bottom)))
        x += w + GAP; rowh = max(rowh, h)
    txt(blk, heading, 0.0, 90.0, 36.0)
    txt(blk, sub, 0.0, 40.0, 24.0)
    return blk
syn = block('SYN_1T1R', SYN, 'GATE-SET COMPLIANCE ANALOG SYNAPSE 1T1R  W/L=25',
            'W=GATE N=SOURCE S=DRAIN/BE NODE E=TE', 4000.0)
perf = block('PERF_TFT', PERF, 'HIGH-ID TFT: INTERDIGITATED, LOV SWEEP, L LADDER',
             'W=GATE N=SOURCE S=DRAIN', 5200.0)
print('SYN_1T1R block', syn.bbox(), '   PERF_TFT block', perf.bbox())

# ============================================================== place in the free areas
def place(c, x_left, y_top):
    b = c.bbox()
    return top.insert(db.CellInstArray(c.cell_index(), db.Trans(u(x_left) - b.left, u(y_top) - b.top)))
ks = place(syn, -1100.0, 4545.0)                     # below the HfO2-only TFT block, above 1T1R
kp = place(perf, -6600.0, 4545.0)                    # left of it, below Transistors_BottomGate
for k in (ks, kp):
    b = k.bbox(); print('   placed', k.cell.name, [round(v * dbu) for v in (b.left, b.bottom, b.right, b.top)])

exec(open(os.path.join(HERE, 'verify_v37.py'), encoding='utf-8').read())


