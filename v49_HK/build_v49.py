"""build_v49.py -- v48 -> v49   (klayout.db only; OASIS + GDS copy)

1. PERF_TFT (14 high-Id TFTs) and SYN_1T1R (8 gate-set-compliance synapses) re-packed column-first:
   devices stacked top->bottom in the existing order (REF, IDT, LOV sweep, L ladder / W500, W250,
   W125, W50), a new column starts only when the next device would not fit above the Memristor
   block. PERF_TFT keeps its top-left corner; SYN_1T1R sits directly to its right, titles aligned.
   Every device is a self-contained instance carrying its own label -> rigid instance moves only,
   no device geometry touched. Frees the strip the synapses used to occupy.
2. STEP_COVERAGE moved from the top-right corner down next to the TestStructures column (right of
   the TLM / gated VdP + Greek cross), placed by a clearance search (>= 80 um to everything).
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v48_HK', 'v48_HK.oas')
OUT = os.path.join(HERE, 'v49_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL
ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
old = db.Layout(); old.read(SRC)
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); LO = names(old); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')
def inst(name): return [k for k in top.each_inst() if k.cell.name == name][0]
def bbum(b): return [round(v * dbu, 1) for v in (b.left, b.bottom, b.right, b.top)]
def flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r

# ============================================================== 1. column-first re-pack
GAP_Y, GAP_X, BLOCK_GAP = 50.0, 60.0, 120.0
BOTTOM_LIMIT = 1338.0 + 60.0      # TOP y: Memristors block top + 60 um
ORDER = {
    'PERF_TFT': ['PT_REF_W100_L10', 'PT_IDT_W1000_L10', 'PT_IDT_W1000_L5', 'PT_IDT_W2000_L10',
                 'PT_LOV2', 'PT_LOV5', 'PT_LOV20', 'PT_LOV40', 'PT_L2', 'PT_L3', 'PT_L5', 'PT_L20', 'PT_L50', 'PT_L100'],
    'SYN_1T1R': ['SYN_W500_L20_J2', 'SYN_W500_L20_J4', 'SYN_W250_L10_J2', 'SYN_W250_L10_J4',
                 'SYN_W125_L5_J2', 'SYN_W125_L5_J4', 'SYN_W50_L2_J2', 'SYN_W50_L2_J4'],
}
def repack(bname):
    c = ly.cell(bname); k = inst(bname)
    ins = {i.cell.name: i for i in c.each_inst()}
    assert sorted(ins) == sorted(ORDER[bname]), bname
    x0, ytop = 5.0, -5.0                                   # device area origin (titles sit above y=0)
    H = (k.trans.disp.y * dbu + ytop) - BOTTOM_LIMIT       # usable column height
    cols, col, h = [], [], 0.0
    for n in ORDER[bname]:
        bh = ins[n].bbox().height() * dbu
        need = bh if not col else h + GAP_Y + bh
        if col and need > H: cols.append(col); col, h = [], 0.0; need = bh
        col.append(n); h = need
    cols.append(col)
    x = x0
    for cl in cols:
        y = ytop
        w = max(ins[n].bbox().width() * dbu for n in cl)
        for n in cl:
            b = ins[n].bbox()
            ins[n].transform(db.Trans(u(x) - b.left, u(y) - b.top))
            y -= b.height() * dbu + GAP_Y
        x += w + GAP_X
    print(f'   {bname}: {len(ORDER[bname])} devices in {len(cols)} columns {[len(cl) for cl in cols]}, column height limit {H:.0f} um')
    return k

print('== 1. column-first re-pack of PERF_TFT and SYN_1T1R')
pk = repack('PERF_TFT')
sk = repack('SYN_1T1R')
pb = pk.bbox(); sb = sk.bbox()
sk.transform(db.Trans(pb.right + u(BLOCK_GAP) - sb.left, pb.top - sb.top))
print('   PERF_TFT TOP bbox', bbum(pk.bbox()), ' (v48:', [-6600.0, 2844.0, -1573.0, 4545.0], ')')
print('   SYN_1T1R TOP bbox', bbum(sk.bbox()), ' (v48:', [-1100.0, 2914.0, 2750.0, 4545.0], ')')

# ============================================================== 2. STEP_COVERAGE -> next to TestStructures
print('\n== 2. STEP_COVERAGE next to the TestStructures column')
stk = inst('STEP_COVERAGE'); st_old = stk.bbox()
tsk = inst('TestStructures'); DX0, DY0 = tsk.trans.disp.x * dbu, tsk.trans.disp.y * dbu
ANCHOR_X = 166.0 + 120.0 + DX0          # 120 um right of the Greek cross (local x 166)
ANCHOR_TOP = 1900.0 + DY0               # top aligned with the TLM title (local y 1900)
MARGIN = 80.0
obst = db.Region()
for n in LAY: obst = obst.or_(db.Region(top.shapes(L[n])))
for k in top.each_inst():
    if k.cell.name == 'STEP_COVERAGE': continue
    if k.cell.name.startswith('TEXT'): obst += db.Region(k.bbox().enlarged(u(10), u(10))); continue
    obst += flat(k)
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
obst += db.Region(crosses).sized(u(40.0))
obst.merge(); obst_m = obst.sized(u(MARGIN))
sr = flat(stk)
best = None
for dyi in range(0, 41):
    for dxi in range(0, 41):
        for sx in ((1,) if dxi == 0 else (1, -1)):
            cx, cy = ANCHOR_X + sx * dxi * 20.0, ANCHOR_TOP - dyi * 20.0
            d = (u(cx) - st_old.left, u(cy) - st_old.top)
            if sr.moved(d[0], d[1]).and_(obst_m).is_empty():
                cost = (dxi * 20.0) ** 2 + (dyi * 20.0) ** 2
                if best is None or cost < best[0]: best = (cost, d)
    if best is not None and best[0] <= (dyi * 20.0) ** 2: break
assert best is not None, 'no clear spot for STEP_COVERAGE next to TestStructures'
stk.transform(db.Trans(best[1][0], best[1][1]))
print('   STEP_COVERAGE TOP bbox', bbum(stk.bbox()), ' (v48:', bbum(st_old), ')')

exec(open(os.path.join(HERE, 'verify_v49.py'), encoding='utf-8').read())
