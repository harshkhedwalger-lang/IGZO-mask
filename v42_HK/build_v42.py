"""build_v42.py -- v41 -> v42   (klayout.db only; OASIS + GDS copy)

Attempted: move STEP_COVERAGE, XBAR_4X4, SPLIT_CV, PERF_TFT down toward TestStructures, and take 1T1R up.

What's actually done here, and why the rest isn't: 1T1R's only real headroom is bounded by SYN_1T1R,
which sits directly above it (X-ranges overlap over most of 1T1R's width) and was not part of this
request -- so 1T1R moves up by the verified-clear amount (about 580 um), not further. For the four
"move down" blocks, a real space check (not a guess) shows there is nowhere for them to land without
displacing a block that wasn't asked for: PERF_TFT's own width needs ~1706 um of clearance below it,
and Memristors already occupies that column up to within 1501 um of PERF_TFT's current position; every
area near TestStructures is already filled by MEM_REDUNDANT/MEM_HIGH_VALUE/CBKR_Structures/
MEM_STACK_SPLIT. This is reported with real numbers in v42_HK_report.md rather than forced.
"""
import klayout.db as db, math, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit

SRC = os.path.join(HERE, '..', 'v41_HK', 'v41_HK.oas')
OUT = os.path.join(HERE, 'v42_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL

ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); PASS = 'Passivation'
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS]
top = ly.cell('TOP')

def flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r
def inst(name): return [k for k in top.each_inst() if k.cell.name == name][0]

# ============================================================== move 1T1R up, bounded by SYN_1T1R
print('== 1T1R: move up, bounded by the real clearance to SYN_1T1R')
tk = inst('1T1R'); sk = inst('SYN_1T1R')
tb = tk.bbox(); sb = sk.bbox()
gap_now = (sb.bottom - tb.top) * dbu
print(f'   1T1R top {tb.top*dbu:.0f}  SYN_1T1R bottom {sb.bottom*dbu:.0f}  current gap {gap_now:.0f} um')
MARGIN = 120.0                                                       # keep this much clearance after the move
dy = gap_now - MARGIN
assert dy > 0, 'no room to move 1T1R up at all'
crosses = [p for p in db.Region(top.shapes(L['Metal_1'])).each() if p.bbox().width() * dbu == 540]
kz = db.Region(crosses).sized(u(40.0))
own_top = db.Region()
for n in LAY: own_top = own_top.or_(db.Region(top.shapes(L[n])))
own_top.merge()
other_blocks = [k for k in top.each_inst() if not k.cell.name.startswith('TEXT') and k.cell.name != '1T1R']
tr_now = flat(tk)
tr_moved = tr_now.transformed(db.Trans(0, u(dy)))
clash = []
for k in other_blocks:
    if not tr_moved.bbox().overlaps(k.bbox()): continue
    o = tr_moved.and_(flat(k)).area() * dbu * dbu
    if o: clash.append((k.cell.name, round(o)))
print('   candidate move by dy=%.1f um -- overlap check vs every other block:' % dy, clash if clash else 'none')
assert not clash, f'moving 1T1R by {dy} would overlap {clash}'
assert tr_moved.and_(kz).is_empty(), 'moved 1T1R would clip an alignment-mark keep-out'
tk.transform(db.Trans(0, u(dy)))
print(f'   1T1R moved up by {dy:.1f} um -> new bbox', tk.bbox())

exec(open(os.path.join(HERE, 'verify_v42.py'), encoding='utf-8').read())
