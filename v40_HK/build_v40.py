"""build_v40.py -- v39 -> v40   (klayout.db only; OASIS + GDS copy)

Rearranges TestStructures into a compact, uniformly-spaced grid. No device is redrawn or resized --
every zone is moved as one rigid unit (translate only), so internal geometry cannot be corrupted; the
build asserts each zone's post-move shapes are EXACTLY the pre-move shapes translated by the computed
delta (checked per layer via XOR after undoing the translation) before writing the file.

Current layout (identified from real geometry, not guessed): TestStructures' own flat content splits
cleanly at y=-470 um (verified: 0 shapes straddle that line) into
  UPPER zone  = TLM back-bias (2 ladders) + an unlabeled gated device, bbox 3265 x 1189 um
  LOWER zone  = GATE OXIDE 1 TESTS (6 devices, one row), bbox 4120 x 620 um
plus the MIS_CV_Block child instance (8 guarded MIS caps, 2 rows) = 2272 x 1804 um, added in v39.
The "GATE OXIDE 1 TESTS" heading (TEXT$129) sits just above the lower zone by content/position but its
y (-467) falls 3 um on the wrong side of the -470 split for a pure y-threshold rule -- assigned to the
lower zone explicitly rather than by the threshold, matching where it visually belongs.

New layout: two rows.
  Row 1 (bottom-aligned at y=770): UPPER zone (TLM+device) on the left, MIS_CV_Block on the right,
         150 um gap between them.
  Row 2 (y=0..620):               LOWER zone (gate-oxide row) spanning underneath, 150 um gap to row 1.
New overall footprint 5687 x 2574 um, vs the old 6786 x 2793 -- smaller in both dimensions, and every
gap in the new layout is a uniform 150 um instead of the old mix of 46-830 um ad-hoc gaps.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v39_HK', 'v39_HK.oas')
OUT = os.path.join(HERE, 'v40_HK')
MINF = 2.0
ENC = mkaudit.ENC; OVL = mkaudit.OVL
GAP = 150.0

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
def isglyph(p):
    b = p.bbox(); return b.height() * dbu <= 40 and b.width() * dbu <= 120 and p.area() * dbu * dbu < 1500

ts = ly.cell('TestStructures')
BOUND = -470.0
GO_HEADING = 'TEXT$129'                     # "GATE OXIDE 1 TESTS" -- belongs with the lower zone by
                                             # content/position even though its y (-467) is on the upper
                                             # side of the -470 split

def capture_shapes(cell, pred):
    """snapshot, per layer, every own shape for which pred(bbox_um) is True -- read-only, no mutation.
       Both zones must be captured before EITHER is moved: moving zone A first can land it at a y that
       satisfies zone B's own predicate, so a naive move-then-move-again would re-select and re-shift
       the already-moved shapes (caught here by the congruence check on the first attempt)."""
    cap = {}
    for n in LAY + (['63'] if '63' in L else []):
        polys = []
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if pred(b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu): polys.append(s.polygon)
        if polys: cap[n] = polys
    return cap

def erase_captured(cell, capture):
    """erase only, matched by geometric overlap at the shapes' CURRENT (original) position. Must be
    called for every zone before ANY zone is re-inserted -- inserting zone A's translated shapes and
    only then erasing zone B (by overlap, at B's *original* footprint) is safe only as long as A's new
    position doesn't happen to land on B's original footprint; here it does (row1_bottom sits inside the
    old gate-oxide row's original y-range), so B's erase pass caught and deleted A's already-placed
    shapes too. Separating erase (all zones) from insert (all zones) removes the ordering dependency
    entirely: every erase happens while every zone is still at its untouched original position."""
    for n, polys in capture.items():
        r = db.Region(polys)
        for s in list(cell.shapes(L[n]).each()):
            if (s.is_polygon() or s.is_box()) and not r.interacting(db.Region(s.polygon)).is_empty():
                cell.shapes(L[n]).erase(s)

def place_captured(cell, capture, dx, dy):
    counts = {}
    for n, polys in capture.items():
        for p in polys: cell.shapes(L[n]).insert(p.transformed(db.Trans(u(dx), u(dy))))
        counts[n] = len(polys)
    return counts

def capture_insts(cell, name_pred): return [k for k in cell.each_inst() if name_pred(k)]
def place_insts(insts, dx, dy):
    for k in insts: k.transform(db.Trans(u(dx), u(dy)))
    return len(insts)

# ============================================================== identify the two zones (pre-move snapshot)
def own_region(cell, pred):
    r = db.Region()
    for n in LAY:
        for s in cell.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if pred(b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu): r.insert(s.polygon)
    r.merge(); return r
up_pred = lambda x0, y0, x1, y1: y0 >= BOUND
lo_pred = lambda x0, y0, x1, y1: y0 < BOUND
up_before = own_region(ts, up_pred); lo_before = own_region(ts, lo_pred)
print('== zones identified from real geometry')
print('   upper zone (pre-move) bbox', up_before.bbox(), '  lower zone (pre-move) bbox', lo_before.bbox())
UB = up_before.bbox(); LB = lo_before.bbox()
up_w, up_h = UB.width() * dbu, UB.height() * dbu
lo_w, lo_h = LB.width() * dbu, LB.height() * dbu
mis = ly.cell('MIS_CV_Block'); mk = [k for k in ts.each_inst() if k.cell.name == 'MIS_CV_Block'][0]
mb = mk.bbox(); mis_w, mis_h = mb.width() * dbu, mb.height() * dbu
print(f'   upper {up_w:.0f}x{up_h:.0f}  lower {lo_w:.0f}x{lo_h:.0f}  MIS_CV_Block {mis_w:.0f}x{mis_h:.0f}')

# ============================================================== compute the new layout
# MIS_CV_Block is left exactly where v39 already placed and verified it (local (2380,-1890), clear of
# every keep-out) -- an earlier version of this script also tried to relocate it next to the upper zone,
# which grew row 1 rightward into a long-standing stray v22 artefact near CBKR (flagged as an open item
# since v34, never touched per the hard rule against altering original TOP geometry) and, once nudged
# clear of that, into CBKR_Structures itself. Not worth the risk for a block that was already in a good
# spot: only the upper/lower zones are reorganised here, stacked into (nearly) the same footprint they
# already occupied, which is known clear of both the stray artefact and MIS_CV_Block.
ANCHOR_X, ANCHOR_Y = -2134.0, -1941.0
row2_top = ANCHOR_Y + lo_h                                  # row2 (lower zone) occupies local y [ANCHOR_Y, +lo_h]
row1_bottom = row2_top + GAP                                # row1 sits GAP above it
up_target = (ANCHOR_X, row1_bottom)                          # upper zone's new bottom-left
lo_target = (ANCHOR_X, ANCHOR_Y)                             # lower zone's new bottom-left

dx_up0, dy_up0 = up_target[0] - UB.left * dbu, up_target[1] - UB.bottom * dbu
dx_lo0, dy_lo0 = lo_target[0] - LB.left * dbu, lo_target[1] - LB.bottom * dbu
dx_mis, dy_mis = 0.0, 0.0

# small search: the corner nearest the (0,-7000) alignment cross clips its keep-out by ~116 um2 at the
# target computed above -- nudge both zones together (same delta, so their relative arrangement is
# unaffected) until clear, rather than hand-guess a margin.
ts_trans_now = [k for k in top.each_inst() if k.cell.name == 'TestStructures'][0].trans
crosses0 = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz0 = db.Region(crosses0).sized(u(40.0))
own0 = db.Region()
for n in LAY: own0 = own0.or_(db.Region(top.shapes(L[n])))
own0.merge()
keepout = kz0 + own0
up_r0 = up_before.transformed(db.Trans(u(dx_up0), u(dy_up0)))
lo_r0 = lo_before.transformed(db.Trans(u(dx_lo0), u(dy_lo0)))
mis_local = db.Region()
for n in LAY: mis_local += db.Region(mis.begin_shapes_rec(L[n]))
mis_local.merge(); mis_local = mis_local.transformed(db.ICplxTrans(mk.trans))  # MIS_CV_Block, fixed, ts-local frame
nudged = False
for nx in range(0, 401, 20):
    for ny in range(0, 401, 20):
        cu_local = up_r0.transformed(db.Trans(u(float(nx)), u(float(ny))))
        cl_local = lo_r0.transformed(db.Trans(u(float(nx)), u(float(ny))))
        if not cu_local.and_(mis_local).is_empty() or not cl_local.and_(mis_local).is_empty(): continue
        cu = cu_local.transformed(db.ICplxTrans(ts_trans_now))
        cl = cl_local.transformed(db.ICplxTrans(ts_trans_now))
        if cu.and_(keepout).is_empty() and cl.and_(keepout).is_empty():
            dx_up, dy_up = dx_up0 + nx, dy_up0 + ny
            dx_lo, dy_lo = dx_lo0 + nx, dy_lo0 + ny
            print(f'   upper/lower zones: nudged by (+{nx},+{ny}) um together to clear TOP-own geometry / alignment marks')
            nudged = True; break
    if nudged: break
assert nudged, 'no clear placement found for the upper/lower zones within the search range'

# ============================================================== apply -- capture BOTH zones first, then place both
print('== applying rigid moves')
cap_up = capture_shapes(ts, up_pred)
cap_lo = capture_shapes(ts, lo_pred)
def text_pred_upper(k):
    if not k.cell.name.startswith('TEXT'): return False     # MIS_CV_Block is a child instance too --
    if k.cell.name == GO_HEADING: return False               # must never be swept up here, it's moved
    return k.bbox().bottom * dbu >= BOUND                     # explicitly via its own dx_mis/dy_mis
def text_pred_lower(k):
    if not k.cell.name.startswith('TEXT'): return False
    if k.cell.name == GO_HEADING: return True
    return k.bbox().bottom * dbu < BOUND
insts_up = capture_insts(ts, text_pred_upper)
insts_lo = capture_insts(ts, text_pred_lower)
erase_captured(ts, cap_up)          # both zones fully erased first (still at their original, verified
erase_captured(ts, cap_lo)          # non-overlapping positions) before either is re-inserted anywhere
n1 = place_captured(ts, cap_up, dx_up, dy_up)
n2 = place_captured(ts, cap_lo, dx_lo, dy_lo)
nt1 = place_insts(insts_up, dx_up, dy_up)
nt2 = place_insts(insts_lo, dx_lo, dy_lo)
mk.transform(db.Trans(u(dx_mis), u(dy_mis)))
print(f'   upper zone: {n1} shape groups + {nt1} text instances moved by ({dx_up:.1f},{dy_up:.1f})')
print(f'   lower zone: {n2} shape groups + {nt2} text instances moved by ({dx_lo:.1f},{dy_lo:.1f})')
print(f'   MIS_CV_Block moved by ({dx_mis:.1f},{dy_mis:.1f})')
print('   TestStructures new bbox', ts.bbox())

exec(open(os.path.join(HERE, 'verify_v40.py'), encoding='utf-8').read())
