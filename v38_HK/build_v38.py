"""build_v38.py -- v37 -> v38   (klayout.db only; OASIS + GDS copy)

Full rebuild of the MIS capacitor block. Three real defects were found and verified in the existing
MIS_Capacitors (see v38_MIS_bug_report.md for the numeric proof, kept alongside this file):

  BUG 1  MIScap_BEdef_50/100/200: the measured area was the accidental intersection of the M1 lead's
         edge and the M3 (TE) plate's edge -- NEITHER layer fully enclosed the other. Area was therefore
         set by M1-to-M3 overlay, an alignment step nothing else in this area-series relied on. Verified:
         "M1 fully inside IGZO" and "M1 fully inside TE" both False for all three sizes.
  BUG 2  MIScap_comb_N6 / MIScap_comb_N10: confirmed to be ONE SOLID M1 polygon each (klayout region
         .count() == 1) -- not interdigitated. The area/perimeter fringe-capacitance separation these
         existed for cannot be performed with them.
  BUG 3  MIScap_open_100 had a spurious 30 um2 real M1/IGZO/M3 overlap -- should be exactly 0 for a
         clean OPEN reference.
  MIScap_guarded_100 was the one correctly-built device (real, verified 15 um M1-to-M1 guard gap,
  genuinely isolated nets) and is the template this rebuild generalises.

New MIS_Capacitors_v2 -- single generator (mis_cap), true single-edge area definition on every device:
  M1 (inner electrode, solid square OR N-finger comb, all within one S x S footprint)
   subset-of  IGZO (S+40, 20 um margin, >= ENC)
   subset-of  TE/M3 (IGZO + 20 um margin)
  Guard ring: M1, annulus around the inner electrode, 10 um gap (>= 3x ENC), own pad, own lead through
  a notch cut in the ring so the inner lead never touches it. Guard ring itself sits fully under the
  same IGZO/M3 stack (guard ring outer edge + 20 um margin <= IGZO half-side), so it experiences the
  same MIS stack as the electrode it guards -- required for the guard to actually intercept fringing
  field from the inner electrode's true edge (Nicollian & Brews guard-ring method).
  3 pads per device (N = inner/BE, W = guard, S = TE), fits the standard N/S/E/W manual probe with one
  side spare.

  Area/perimeter series (regression C_meas = c_area*A + c_perim*P, both extracted from real geometry,
  not from the nominal S/N): (S=50,N=1) (S=100,N=1) (S=100,N=4) (S=100,N=8) (S=200,N=1) (S=200,N=4).
  OPEN_S100:  pads + guard ring only, IGZO omitted entirely, no M1/M3 overlap anywhere -> pad+guard
              parasitic capacitance reference for the S=100 geometry.
  SHORT_S100: same as OPEN, plus the inner-M1 lead is bonded straight to M3 through an Isolation_1
              window -> series R / lead-inductance reference at the SAME S=100 geometry, dielectric
              bypassed. (This is also the Nicollian-Brews strong-accumulation R_s proxy: a real device
              in strong accumulation looks electrically like this short plus C_ox in parallel.)
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v37_HK', 'v37_HK.oas')
OUT = os.path.join(HERE, 'v38_HK')
MINF = 2.0; PAD, PW, TAPER = 160.0, 150.0, 75.0
ENC = mkaudit.ENC; OVL = mkaudit.OVL
GAP = 80.0

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
LABELS = {}
PLATES = {}
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r)
    LABELS.setdefault(c.name, db.Region()).insert(r)
    return r.bbox().width() * dbu
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500

def pad_lead(c, met, ax, ay, d, w, llen):
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

# ---------------------------------------------------------------------------------- MIS cap generator
GGAP = 10.0     # guard-ring <-> inner-electrode gap (M1-to-M1), >= 3x ENC
GW = 30.0       # guard ring width
IGM = 20.0      # IGZO margin beyond the guard ring's outer edge
TEM = 20.0      # M3 (TE) margin beyond IGZO
LEADW = 20.0    # inner-electrode lead width through the guard-ring notch

def mis_cap(name, S, n=1, kind='cap', label=None):
    """S = inner-electrode footprint side (um), n = number of comb fingers (n=1 -> solid square).
       kind: 'cap' (full guarded MIS capacitor), 'open' (pads + guard only, no stack),
             'short' (open + inner lead bonded straight to M3, dielectric bypassed)."""
    c = ly.create_cell(name); hs = S / 2.0
    g_in = hs + GGAP; g_out = g_in + GW
    ig_hs = g_out + IGM; te_hs = ig_hs + TEM
    notch = LEADW / 2 + 10.0

    # guard ring: 4 bars, North bar split around the notch for the inner-electrode lead
    bx(c, 'Metal_1', -g_out, -g_out, g_out, -g_in)                    # S bar
    bx(c, 'Metal_1', -g_out, g_in, -notch, g_out)                     # N bar, left of notch
    bx(c, 'Metal_1', notch, g_in, g_out, g_out)                       # N bar, right of notch
    bx(c, 'Metal_1', -g_out, -g_in, -g_in, g_in)                      # W bar
    bx(c, 'Metal_1', g_in, -g_in, g_out, g_in)                        # E bar
    pad_lead(c, 'Metal_1', -g_out, 0.0, 'W', GW, 20.0)                # guard pad

    if kind == 'cap':
        plate = db.Region()
        if n <= 1:
            bx(c, 'Metal_1', -hs, -hs, hs, hs); plate.insert(db.Box(u(-hs), u(-hs), u(hs), u(hs)))
        else:
            w = S / (2 * n - 1)
            fy0, fy1 = -hs, hs - 12.0
            for k in range(n):
                fx0 = -hs + k * 2 * w
                bx(c, 'Metal_1', fx0, fy0, fx0 + w, fy1); plate.insert(db.Box(u(fx0), u(fy0), u(fx0 + w), u(fy1)))
            bx(c, 'Metal_1', -hs, fy1, hs, hs); plate.insert(db.Box(u(-hs), u(fy1), u(hs), u(hs)))  # top bus
        plate.merge(); PLATES[c.name] = plate
        bx(c, 'IGZO', -ig_hs, -ig_hs, ig_hs, ig_hs)
        bx(c, 'Metal_3', -te_hs, -te_hs, te_hs, te_hs)
        pad_lead(c, 'Metal_1', 0.0, hs, 'N', LEADW, g_out - hs + 20.0)  # inner electrode pad, through notch
        pad_lead(c, 'Metal_3', 0.0, -te_hs, 'S', 2 * te_hs, 20.0)       # TE pad (plate itself IS the lead start)
    else:
        # both leads routed from the true centre (0,0) out to their pads, so a 'short' bond at centre
        # can actually reach both -- the first version routed them to opposite sides (N vs S) with no
        # shared geometry anywhere, so the intended M1-M3 bond never touched M3 at all (caught by the
        # net-extraction check: SHORT came back as 3 isolated nets instead of 2).
        pad_lead(c, 'Metal_1', 0.0, 0.0, 'N', LEADW, g_out + 20.0)      # inner lead, no plate: OPEN reference
        pad_lead(c, 'Metal_3', 0.0, 0.0, 'S', LEADW, g_out + 20.0)      # TE lead, no plate either
        # pad_lead's N lead only exists for y>=0 and the S lead only for y<=0 -- they meet along the
        # single line y=0 with zero width, so a bond window centred there is enclosed by neither.  Give
        # each layer an explicit stub that crosses centre, so both genuinely overlap with real margin.
        bx(c, 'Metal_1', -LEADW / 2, -15.0, LEADW / 2, 15.0)
        bx(c, 'Metal_3', -LEADW / 2, -15.0, LEADW / 2, 15.0)
        if kind == 'short':
            # bond M1 straight to M3 at centre, dielectric bypassed entirely (same Iso1+M3-cap recipe
            # used for every M1 pad in this mask); window sized >= ENC inside both LEADW-wide stubs
            wnd = LEADW - 2 * ENC - 2.0
            bx(c, 'Isolation_1', -wnd / 2, -wnd / 2, wnd / 2, wnd / 2)

    if label:
        # placed from the cell's own current (real, already-drawn) bbox, not a hand-computed offset --
        # a hand offset previously landed the label on the TE pad's 75 um taper cone, which extends much
        # further than the plate/lead geometry alone would suggest.
        yl = c.bbox().bottom * dbu - 40.0
        wl = tg.text(label, dbu, 24.0 * MAG1).bbox().width() * dbu
        txt(c, label, -wl / 2, yl, 24.0)
    return c

# ---------------------------------------------------------------------------------- build the family
DEVICES = [(50, 1, 'S50 F1'), (100, 1, 'S100 F1'), (100, 4, 'S100 F4'), (100, 8, 'S100 F8'),
           (200, 1, 'S200 F1'), (200, 4, 'S200 F4')]
CAPS = [mis_cap(f'MISv2_S{S}_F{n}', S, n, 'cap', lab) for S, n, lab in DEVICES]
OPEN = mis_cap('MISv2_OPEN_S100', 100, 1, 'open', 'OPEN S100')
SHORT = mis_cap('MISv2_SHORT_S100', 100, 1, 'short', 'SHORT S100')

def block(name, cells, heading, sub, maxw):
    blk = ly.create_cell(name); x = y = 0.0; rowh = 0.0
    for c in cells:
        b = c.bbox(); w, h = b.width() * dbu, b.height() * dbu
        if x > 0 and x + w > maxw: x = 0.0; y -= rowh + GAP; rowh = 0.0
        blk.insert(db.CellInstArray(c.cell_index(), db.Trans(u(x) - b.left, u(y - h) - b.bottom)))
        x += w + GAP; rowh = max(rowh, h)
    txt(blk, heading, 0.0, 90.0, 36.0)
    txt(blk, sub, 0.0, 40.0, 24.0)
    return blk
mis = block('MIS_Capacitors_v2', CAPS + [OPEN, SHORT],
            'GUARDED MIS CAPACITORS  M1/AL2O3/IGZO/M3  SINGLE-EDGE, AREA-PERIMETER SERIES',
            'N=INNER(BE) W=GUARD S=TE   OPEN/SHORT AT S100', 5300.0)
print('MIS_Capacitors_v2 block', mis.bbox())

# ---------------------------------------------------------------------------------- replace the placed instance
old_k = [k for k in top.each_inst() if k.cell.name == 'MIS_Capacitors'][0]
old_b = old_k.bbox()
old_k.delete()
b = mis.bbox()
top.insert(db.CellInstArray(mis.cell_index(), db.Trans(u(old_b.left * dbu) - b.left, u(old_b.bottom * dbu) - b.bottom)))
print('placed at', [k for k in top.each_inst() if k.cell.name == 'MIS_Capacitors_v2'][0].bbox())
print('old MIS_Capacitors cell kept in the file, unplaced, for reference/diff')

exec(open(os.path.join(HERE, 'verify_v38.py'), encoding='utf-8').read())
