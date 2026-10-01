"""build_v43.py -- v42 -> v43   (klayout.db only; OASIS + GDS copy)

Regroups Memristors_Gated: currently 4 TYPE sections (LATERAL RING GATED / LATERAL OPEN GATED /
VERTICAL GATED / PROCESS SPLITS), each internally already ordered by gap length (2,3,4,6 um) as its
4 columns. Per the request, transposed so length is the PRIMARY grouping instead: every device of a
given gap length (regardless of type) now sits in one contiguous cluster, with type as the
sub-column inside it.

Each of the 42 devices is already its own self-contained child instance (own per-device label baked
into its own cell, confirmed: "G2-1" etc. lives inside MEM_G2_1 itself, not as a separate parent-level
shape) -- so this is a plain per-instance rigid move, not the flat-geometry surgery TestStructures
needed. No device geometry is touched, only which instance sits where.

The 4 old TYPE-section headers (own M1 glyphs of the parent cell) described the OLD grouping and would
be wrong for the new one; they're replaced with 4 new LENGTH-group headers. The block's own title
("GATED MEMRISTORS 3X") is kept, repositioned above the new layout.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v42_HK', 'v42_HK.oas')
OUT = os.path.join(HERE, 'v43_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
tg = db.TextGenerator.default_generator(); MAG1 = 1.0 / 0.7
def txt(cell, s, x, y, cap=24.0):
    r = tg.text(s, dbu, cap * MAG1).moved(u(x), u(y)); cell.shapes(L['Metal_1']).insert(r)
    return r
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500

c = ly.cell('Memristors_Gated')

# ============================================================== 1. capture current state (read-only)
DEV_W, DEV_H = 257.0, 212.622    # measured from MEM_G2_1
insts = {k.cell.name: k for k in c.each_inst()}
print('== 1. Memristors_Gated: 42 devices found:', len(insts))

# old title line: the parent's own glyphs at the topmost Y-band, x < 200 (left-aligned block title,
# distinguished from the 2nd, slightly lower sub-band which was the old "LATERAL RING GATED" section
# header -- verified separately below by rendering, not assumed)
glyphs = [s for s in c.shapes(L['Metal_1']).each() if s.is_polygon() and isglyph(s.polygon)]
band_top = max(s.polygon.bbox().top for s in glyphs)
print(f'   {len(glyphs)} own header glyphs, topmost y {band_top*dbu:.0f}')
for s in list(glyphs): c.shapes(L['Metal_1']).erase(s)   # clear ALL old section headers + title; redrawn below
print('   old headers cleared (all 4 type-section headers + title -- title text is redrawn fresh below)')

# ============================================================== 2. new layout: length is the primary group
# 2x2 grid of length-groups (not 1x4): a single row came out 4178 um wide, wider than the space
# available anywhere near a die corner. 2x2 gives a roughly square footprint that actually fits.
COL_PITCH = 270.0; ROW_PITCH = 216.0; GROUP_GAP_X = 150.0; GROUP_GAP_Y = 150.0
GROUPS = [
    ('2', ['G2', 'O2', 'V2', 'A3']),   # A3 sits in the length-2 column in the original layout
    ('3', ['G3', 'O3', 'V3', 'T3']),   # T3 sits in the length-3 column in the original layout
    ('4', ['G4', 'O4', 'V4']),
    ('6', ['G6', 'O6', 'V6']),
]
GRID = [[GROUPS[0], GROUPS[1]], [GROUPS[2], GROUPS[3]]]   # row0 (top): L2,L3   row1 (bottom): L4,L6
def group_width(types): return (len(types) - 1) * COL_PITCH + DEV_W
GROUP_H = 2 * ROW_PITCH + DEV_H
col_w = [max(group_width(GRID[r][ci][1]) for r in range(2)) for ci in range(2)]
row_y0 = [GROUP_H + GROUP_GAP_Y, 0.0]   # row0 sits above row1
col_x0 = [0.0, col_w[0] + GROUP_GAP_X]
total_width = col_x0[1] + col_w[1]
total_height = row_y0[0] + GROUP_H
print(f'   2x2 length-group grid, total footprint {total_width:.0f} x {total_height:.0f} um')

targets = {}   # cell name -> (x, y) bottom-left target
for r in range(2):
    for ci in range(2):
        lab, types = GRID[r][ci]
        gx, gy = col_x0[ci], row_y0[r]
        for tci, ty in enumerate(types):
            for row in (1, 2, 3):
                name = f'MEM_{ty}_{row}'
                assert name in insts, f'missing device {name}'
                tx = gx + tci * COL_PITCH
                ty_y = gy + (3 - row) * ROW_PITCH        # row 1 on top (highest y), row 3 on bottom
                targets[name] = (tx, ty_y)
print(f'   {len(targets)} target positions computed for {len(insts)} devices')
assert set(targets) == set(insts), 'target/instance name mismatch'

# ============================================================== 3. apply -- independent instance moves,
# no zone-overlap risk (each device is a discrete, separately-placed instance, not flat geometry that
# could accidentally re-select an already-moved neighbour the way TestStructures' flat shapes could)
moved = 0
for name, (tx, ty_y) in targets.items():
    k = insts[name]; b = k.bbox()
    dx = u(tx) - b.left; dy = u(ty_y) - b.bottom
    k.transform(db.Trans(dx, dy)); moved += 1
print(f'   {moved} devices moved to their new grouped position')

# ============================================================== 4. new labels
row0_top = row_y0[0] + GROUP_H
txt(c, 'GATED MEMRISTORS 3X - GROUPED BY GAP LENGTH', 0.0, row0_top + 70.0, 36.0)
for ci in range(2):
    lab, _ = GRID[0][ci]
    txt(c, f'L = {lab} UM', col_x0[ci], row0_top + 25.0, 24.0)
for ci in range(2):
    lab, _ = GRID[1][ci]
    txt(c, f'L = {lab} UM', col_x0[ci], row_y0[1] + GROUP_H + 25.0, 24.0)
print('   title + 4 length-group headers drawn')

# ============================================================== 5. relocate the whole block to fit the die
# a single-row layout was 4178 um wide -- wider than any corner has room for. The 2x2 grid above is a
# roughly square ~total_width x total_height footprint; find a placement near a die corner that clears
# every neighbour and every alignment mark, rather than leaving it anchored where the old, much
# narrower block used to sit (which is what put part of it off the die edge in the first attempt).
mgk = [k for k in top.each_inst() if k.cell.name == 'Memristors_Gated'][0]
mg_r = db.Region()
for n in LAY: mg_r += db.Region(c.begin_shapes_rec(L[n]))
mg_r.merge()
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
own_top_r = db.Region()
for n in LAY: own_top_r = own_top_r.or_(db.Region(top.shapes(L[n])))
own_top_r.merge()
other_blocks = [k for k in top.each_inst() if not k.cell.name.startswith('TEXT') and k.cell.name != 'Memristors_Gated']
# search anchored near the top-right die corner (the "top corner" asked for), scanning left/down from
# the corner until a clear spot is found
CORNER_X, CORNER_Y = 6900.0, 6900.0
placed = False
for dx in range(0, 4001, 100):
    for dy in range(0, 3001, 100):
        x = CORNER_X - total_width - dx; y = CORNER_Y - total_height - dy
        cand = mg_r.transformed(db.Trans(u(x), u(y)))
        if not cand.and_(kz).is_empty(): continue
        if not cand.and_(own_top_r).is_empty(): continue
        clash = False
        for k in other_blocks:
            if cand.bbox().overlaps(k.bbox()):
                fk = db.Region()
                for n in LAY: fk += db.Region(k.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(k.trans))
                if not cand.and_(fk).is_empty(): clash = True; break
        if clash: continue
        b0 = mgk.bbox()
        mgk.transform(db.Trans(u(x) - b0.left, u(y) - b0.bottom))
        print(f'   Memristors_Gated relocated to TOP bbox', mgk.bbox())
        placed = True; break
    if placed: break
assert placed, 'no clear corner placement found for the regrouped Memristors_Gated block'

exec(open(os.path.join(HERE, 'verify_v43.py'), encoding='utf-8').read())
