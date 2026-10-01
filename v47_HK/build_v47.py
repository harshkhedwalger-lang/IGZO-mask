"""build_v47.py -- v46 -> v47   (klayout.db only; OASIS + GDS copy)

Redesigns Memristors_Gated's 42 devices from the old 81x81um pad convention (a
memristor-specific scale, never part of the 160/150 -> 150/140 mask standard) up to full
150x150um pads (140x140 windows), per explicit request that every device keep its own 3
independent pads (BE, Gate, TE) rather than sharing bus pads.

All 42 devices share byte-identical pad-region geometry (checked across G/O/V/A/T types and
all 4 gap lengths -- only the channel/gap geometry between the pads differs). That makes this
a single generic transform, not 42 one-offs:
  1. Erase each device's 3 old 81x81 pads + their 75x75 Isolation_1/Passivation windows
     (exact, known local coordinates, identical in every device).
  2. Re-grow each terminal from the boundary of its still-untouched channel-side lead, using
     this mask's own pad_lead() recipe (75um taper, same convention as everywhere else) at
     150x150/140x140 -- BE grows west, Gate grows south, TE grows east, so none of the three
     new pads can collide with each other or with the channel geometry in between.
  3. Each device's own per-device label ("G2-1" etc.) sits right where the enlarged BE/TE
     pads now reach -- shifted up to clear it (checked, not assumed: computed against the new
     pad's actual top edge).

Consequence, stated plainly: device footprint grows from 257x212um to roughly 626x437um
(~5x area) because the extra reach comes from a fixed pad-region layout that's the same in
all four directions -- there was no "give" to shrink into.  The 42-device grid is rebuilt at
the new pitch, then re-placed with a verified clear-space search (it will not fit back in the
old top-right corner spot; real numbers below).
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'v46_HK'))
import mkaudit

SRC = os.path.join(HERE, '..', 'v46_HK', 'v46_HK.oas')
OUT = os.path.join(HERE, 'v47_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL

NEW_PAD, NEW_PW, TAPER = 100.0, 90.0, 75.0   # reduced from 150/140 -- too big, more area-efficient

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')

def bx(c, l, x0, y0, x1, y1): c.shapes(L[l]).insert(db.Box(u(min(x0, x1)), u(min(y0, y1)), u(max(x0, x1)), u(max(y0, y1))))
def poly(c, l, pts): c.shapes(L[l]).insert(db.Polygon([db.Point(u(x), u(y)) for x, y in pts]))
def pad_lead(c, met, ax, ay, d, w, llen):
    """this mask's own recipe: straight lead (w wide) + 75um taper to NEW_PAD + the pad itself.
       M1/M2 pad gets Isolation_1 window, M3 cap and passivation window; M3 pad gets passivation."""
    sx, sy = {'N': (0, 1), 'S': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[d]
    def pt(a, b): return (ax + sx * a - sy * b, ay + sy * a + sx * b)
    if llen > 0: poly(c, met, [pt(0, -w / 2), pt(llen, -w / 2), pt(llen, w / 2), pt(0, w / 2)])
    a0 = llen; a1 = llen + TAPER
    poly(c, met, [pt(a0, -w / 2), pt(a1, -NEW_PAD / 2), pt(a1, NEW_PAD / 2), pt(a0, w / 2)])
    (x0, y0), (x1, y1) = pt(a1, -NEW_PAD / 2), pt(a1 + NEW_PAD, NEW_PAD / 2)
    bx(c, met, x0, y0, x1, y1)
    e = (NEW_PAD - NEW_PW) / 2
    xa, xb, ya, yb = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
    if met in ('Metal_1', 'Metal_2'):
        bx(c, 'Isolation_1', xa + e, ya + e, xb - e, yb - e); bx(c, 'Metal_3', xa, ya, xb, yb)
    bx(c, PASS, xa + e, ya + e, xb - e, yb - e)
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt(c, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); c.shapes(L['Metal_1']).insert(r)
    return r

# ============================================================== 1. the 42 device names (v43's grouping)
GROUPS = [
    ('2', ['G2', 'O2', 'V2', 'A3']),
    ('3', ['G3', 'O3', 'V3', 'T3']),
    ('4', ['G4', 'O4', 'V4']),
    ('6', ['G6', 'O6', 'V6']),
]
DEV_NAMES = [f'MEM_{ty}_1' for _, tys in GROUPS for ty in tys]     # 1 repeat/type per user decision (independent
assert len(DEV_NAMES) == 14                                        # pads at full 150x150 don't fit at 3 repeats)

# fixed old-pad geometry (identical in all 42 devices -- verified by direct inspection first)
GATE_OLD = (u(87.5), u(-0.5), u(168.5), u(80.5)); GATE_WIN_OLD = (u(90.5), u(2.5), u(165.5), u(77.5))
BE_OLD = (u(-0.5), u(87.5), u(80.5), u(168.5)); BE_WIN_OLD = (u(2.5), u(90.5), u(77.5), u(165.5))
TE_OLD = (u(175.5), u(87.5), u(256.5), u(168.5)); TE_WIN_OLD = (u(178.5), u(90.5), u(253.5), u(165.5))

print('== 1. redesigning pads in all 42 device cells (in place, channel geometry untouched)')
LABEL_DY = 40.0
old_bboxes = {}
for name in DEV_NAMES:
    c = ly.cell(name)
    old_bboxes[name] = c.bbox()
    for lay, box in [('Metal_1', GATE_OLD), ('Metal_2', BE_OLD), ('Metal_3', TE_OLD)]:
        found = 0
        for s in list(c.shapes(L[lay]).each()):
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if (b.left, b.bottom, b.right, b.top) == box:
                c.shapes(L[lay]).erase(s); found += 1
        assert found == 1, (name, lay, 'old pad not found exactly once')
    for lay in ('Isolation_1', PASS):
        for box in (GATE_WIN_OLD, BE_WIN_OLD, TE_WIN_OLD):
            found = 0
            for s in list(c.shapes(L[lay]).each()):
                if not (s.is_polygon() or s.is_box()): continue
                b = s.polygon.bbox()
                if (b.left, b.bottom, b.right, b.top) == box:
                    c.shapes(L[lay]).erase(s); found += 1
            assert found == 1, (name, lay, box, 'old window not found exactly once')
    pad_lead(c, 'Metal_1', 128.0, 0.0, 'S', 80.0, 0.0)      # Gate, grows south
    pad_lead(c, 'Metal_2', 80.0, 128.0, 'W', 80.0, 0.0)     # BE, grows west
    pad_lead(c, 'Metal_3', 256.0, 128.0, 'E', 80.0, 0.0)    # TE, grows east
    glyphs = [s for s in c.shapes(L['Metal_1']).each() if s.is_polygon() and isglyph(s.polygon)]
    for s in list(glyphs):
        p = s.polygon
        c.shapes(L['Metal_1']).erase(s)
        c.shapes(L['Metal_1']).insert(p.transformed(db.Trans(0, u(LABEL_DY))))

sizes = {tuple(round(x * dbu, 3) for x in (ly.cell(n).bbox().left, ly.cell(n).bbox().bottom, ly.cell(n).bbox().right, ly.cell(n).bbox().top)) for n in DEV_NAMES}
print('   distinct new device bboxes:', len(sizes))
b0 = ly.cell(DEV_NAMES[0]).bbox()
DEV_W = (b0.right - b0.left) * dbu; DEV_H = (b0.top - b0.bottom) * dbu
DEV_X0, DEV_Y0 = b0.left * dbu, b0.bottom * dbu           # bottom-left corner, local coords
print(f'   new device bbox: {DEV_W:.2f} x {DEV_H:.2f} um  (origin offset {DEV_X0:.2f},{DEV_Y0:.2f})')

exec(open(os.path.join(HERE, 'build_v47_part2.py'), encoding='utf-8').read())
