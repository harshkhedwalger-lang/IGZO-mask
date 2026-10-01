"""build_v46.py -- v45 -> v46   (klayout.db only; OASIS + GDS copy)

Mask-wide pad standard change, per request:
  OLD: 160x160 pad, 150x150 contact/passivation window (5um inset)
  NEW: 150x150 pad, 140x140 contact/passivation window (5um inset -- same ratio, just smaller)

This touches every standard pad on the reticle (392 pad squares across Metal_1/2/3, 708
window squares across Isolation_1/Passivation, found by direct survey -- not estimated).
There is no single from-scratch generator script left in this project (the mask was built by
successive diff scripts across v34..v45, several without their own source present), so this
is done as a direct geometric transform on the current v45_HK.oas: every shape whose role is
identifiable by its own size and position is resized in place, centered on the same node, so
no probe coordinate or electrical connection moves -- only the pad/window edges shrink by 5um.

Three categories, all processed per-cell (own shapes only -- coordinates are cell-local):
  1. Pad squares (Metal_1/2/3, 160x160): box shrunk to 150x150, same center.
  2. Window squares (Isolation_1/Passivation, 150x150) CONCENTRIC with a pad found in (1):
     shrunk to 140x140, same center. A 150x150 square NOT concentric with any pad is left
     alone and reported (there is a known, deliberate exception -- see the survey note).
  3. Tapers (the 75um lead-to-pad cone drawn by this mask's own pad_lead() helper, and any
     other shape touching a pad's edge): rather than trying to detect "is this a taper"
     structurally, every OTHER polygon on the same layer in the same cell that has a vertex
     exactly coincident with one of a pad's OLD corners gets that vertex moved to the pad's
     NEW corner. This is a generic "follow the pad" rule -- it fixes tapers without needing
     to recognize them specifically, and it can't silently miss an unusual pad-adjacent shape
     the way a taper-shape-matching heuristic could.

Read-only survey first (found, not assumed):
  - 10 Metal_2 squares at 150x150 are NOT pads -- they are the memristor bottom-electrode
    plate inside 1T1R_single_v36 and 1T1R (a device-area dimension, coincidentally close to
    the old window size). They don't match the 160x160 pad filter so step (1) never touches
    them; noted here so the exclusion isn't mistaken for an oversight.
  - A handful of squares at other sizes (210, 200, 142.1, 140, 130, 120, 117, 180, 160-on-a-
    window-layer) exist and are deliberately left alone -- they belong to MIS_CV_Block's own
    area-perimeter capacitor sweep and similar non-pad geometry, not the pad standard.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'v45_HK'))
import mkaudit

SRC = os.path.join(HERE, '..', 'v45_HK', 'v45_HK.oas')
OUT = os.path.join(HERE, 'v46_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL

OLD_PAD, OLD_PW = 160.0, 150.0
NEW_PAD, NEW_PW = 150.0, 140.0
DELTA = (OLD_PAD - NEW_PAD) / 2.0            # 5.0, same as (OLD_PW - NEW_PW) / 2.0

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
METAL_LAYERS = ['Metal_1', 'Metal_2', 'Metal_3']
WINDOW_LAYERS = ['Isolation_1', PASS]
top = ly.cell('TOP')

PAD_DBU = u(OLD_PAD); WIN_DBU = u(OLD_PW); DELTA_DBU = u(DELTA)
TOL = u(0.6)
# center-matching tolerance for window<->pad pairing. Found (not assumed) a real, consistent
# 0.75um y-offset between pads and their windows in Transistors_BottomGate(_HfO2Only) -- an
# old-block quirk, not a different feature (the next-nearest real candidate is 225um away, so
# there's no risk of this widened tolerance mis-pairing something else).
CTOL = u(1.0)

def is_square(box, size_dbu, tol):
    w = box.right - box.left; h = box.top - box.bottom
    return abs(w - size_dbu) <= tol and abs(h - size_dbu) <= tol

def shrink_box(b, d):
    return db.Box(b.left + d, b.bottom + d, b.right - d, b.top - d)

n_pads = n_windows = n_windows_unpaired = n_taper_vertices = n_taper_polys = 0
unpaired_examples = []
cells_touched = set()

for cell in ly.each_cell():
    # ---- 1. find pad squares per metal layer (own shapes only) ----
    pad_shapes = {n: [] for n in METAL_LAYERS}       # layer -> [(shape, old_box)]
    for n in METAL_LAYERS:
        li = L[n]
        for s in list(cell.shapes(li).each()):
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if is_square(b, PAD_DBU, TOL):
                pad_shapes[n].append((s, b))
    total_pads_here = sum(len(v) for v in pad_shapes.values())
    if total_pads_here == 0:
        continue

    # per-pad edge list: (fixed_axis 'x'/'y', old_coord, new_coord, span_lo, span_hi) x4 sides.
    # A touching shape's vertex needs to move if it sits exactly ON one of these edge lines
    # within the edge's span -- covers both corner-sharing tapers AND a shape that taps into
    # the middle of a pad's side (found in STEP_COVERAGE: a plain connector box butted against
    # the pad's edge, not its corners -- pure corner-matching silently left a 5um gap there).
    pad_edges = []      # list of (axis, old_coord, new_coord, span_lo, span_hi)
    pad_centers = []    # (cx, cy) in dbu
    for n in METAL_LAYERS:
        for s, b in pad_shapes[n]:
            nb = shrink_box(b, DELTA_DBU)
            pad_edges.append(('x', b.left, nb.left, b.bottom, b.top))
            pad_edges.append(('x', b.right, nb.right, b.bottom, b.top))
            pad_edges.append(('y', b.bottom, nb.bottom, b.left, b.right))
            pad_edges.append(('y', b.top, nb.top, b.left, b.right))
            pad_centers.append(((b.left + b.right) // 2, (b.bottom + b.top) // 2))

    # ---- 2. windows (150x150) concentric with a pad center -> shrink to 140, same center ----
    for n in WINDOW_LAYERS:
        li = L[n]
        for s in list(cell.shapes(li).each()):
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if not is_square(b, WIN_DBU, TOL): continue
            cx, cy = (b.left + b.right) // 2, (b.bottom + b.top) // 2
            paired = any(abs(cx - pcx) <= CTOL and abs(cy - pcy) <= CTOL for pcx, pcy in pad_centers)
            if not paired:
                n_windows_unpaired += 1
                if len(unpaired_examples) < 10:
                    unpaired_examples.append((cell.name, n, [round(v * dbu, 2) for v in (b.left, b.bottom, b.right, b.top)]))
                continue
            nb = shrink_box(b, DELTA_DBU)
            cell.shapes(li).erase(s)
            cell.shapes(li).insert(db.Box(nb.left, nb.bottom, nb.right, nb.top))
            n_windows += 1
            cells_touched.add(cell.name)

    # ---- 3. any OTHER polygon on a metal layer sharing a vertex with an old pad corner ----
    # (content-based exclusion of the pad squares themselves -- Shape wrapper identity is not
    # stable across separate .each() iterations, so id() can't be trusted here)
    pad_bboxes = {n: {(b.left, b.bottom, b.right, b.top) for s, b in pad_shapes[n]} for n in METAL_LAYERS}
    for n in METAL_LAYERS:
        li = L[n]
        for s in list(cell.shapes(li).each()):
            if not (s.is_polygon() or s.is_box()): continue
            bb = s.polygon.bbox()
            if (bb.left, bb.bottom, bb.right, bb.top) in pad_bboxes[n]: continue
            p = s.polygon
            pts = list(p.each_point_hull())
            changed = False
            moved_here = 0
            newpts = []
            for pt in pts:
                vx, vy = pt.x, pt.y
                for axis, old_c, new_c, lo, hi in pad_edges:
                    if axis == 'x' and vx == old_c and lo <= vy <= hi:
                        vx = new_c; changed = True; moved_here += 1
                    elif axis == 'y' and vy == old_c and lo <= vx <= hi:
                        vy = new_c; changed = True; moved_here += 1
                newpts.append(db.Point(vx, vy))
            if changed:
                cell.shapes(li).erase(s)
                cell.shapes(li).insert(db.Polygon(newpts))
                n_taper_polys += 1
                n_taper_vertices += moved_here
                cells_touched.add(cell.name)

    # ---- 1b. now actually shrink the pad squares themselves ----
    for n in METAL_LAYERS:
        for s, b in pad_shapes[n]:
            nb = shrink_box(b, DELTA_DBU)
            cell.shapes(L[n]).erase(s)
            cell.shapes(L[n]).insert(db.Box(nb.left, nb.bottom, nb.right, nb.top))
            n_pads += 1
            cells_touched.add(cell.name)

print(f'pads resized (160->150): {n_pads}')
print(f'windows resized (150->140): {n_windows}')
print(f'windows NOT paired with any pad (left untouched): {n_windows_unpaired}')
for ex in unpaired_examples: print('   unpaired window example:', ex)
print(f'touching polygons (tapers etc.) adjusted: {n_taper_polys}  ({n_taper_vertices} vertices moved)')
print(f'cells touched: {len(cells_touched)}')

exec(open(os.path.join(HERE, 'verify_v46.py'), encoding='utf-8').read())
