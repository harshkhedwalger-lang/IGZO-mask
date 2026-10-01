"""build_v52.py -- v51 -> v52   (klayout.db + klayout.lib only; OASIS + GDS copy)

1. Text: every piece of text on the die becomes an editable KLayout Basic.TEXT PCell (like the original
   headings), upper case, on its original layer, in three standard sizes:
       T  block title     mag 100  (70 um cap height)
       L  device label    mag  50  (35 um)
       N  note            mag  30  (21 um)  pad legends, subtitles, BE/TE, TLM spacings, coordinates
   Sources converted: polygon text in KLayout std_font (decoded exactly by textocr), polygon text in the old
   'glmfont' (strings read from renders, table GLM below), the two spliced static labels TEXT_L2/L3_W500,
   and all existing Basic.TEXT cells (re-sized).  Exempt: die title (Bxx_xx / IGZO_v16HK / date) and the
   ResolutionTests artwork text (L1..L6 mark IDs, line-width numbers).
2. 1T1R: the flat 6th row (pitch 1200) snapped onto the 5-row array columns (pitch 1150).
3. ResolutionTests (L1..L6 alignment + resolution marks) moved into the top-left and bottom-right die
   corners, next to the corner crosses (diagonal pair kept for rotation).
"""
import klayout.db as db, klayout.lib, math, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mkaudit, textocr

SRC = os.path.join(HERE, '..', 'v51_HK', 'v51_HK.oas')
OUT = os.path.join(HERE, 'v52_HK')
MINF = 2.0; ENC = mkaudit.ENC; OVL = mkaudit.OVL
ly = db.Layout(); ly.read(SRC); dbu = ly.dbu
old = db.Layout(); old.read(SRC)
def u(x): return int(round(x / dbu))
def names(l_): return {(l_.get_info(i).name or '63'): i for i in l_.layer_indexes()}
L = names(ly); LO = names(old)
LAY = ['Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', 'Passivation']
top = ly.cell('TOP')
def bbum(b): return [round(v * dbu, 1) for v in (b.left, b.bottom, b.right, b.top)]
def is_text(c): return c.name.startswith('TEXT')
MAG = {'T': 100.0, 'L': 50.0, 'N': 30.0}
GAP = {'T': 14.0, 'L': 10.0, 'N': 8.0}           # gap below a line of this tier inside a stack
EXEMPT_CELLS = {'ResolutionTests'}
EXEMPT_STR = {'BXX_XX', 'IGZO_V16HK', 'XX.XX.2026'}

placed = set()
def walk(c):
    for ci in c.each_child_cell():
        if ci not in placed: placed.add(ci); walk(ly.cell(ci))
placed.add(top.cell_index()); walk(top)

# ===================================================================== 2. 1T1R flat row
print('== 1T1R: snap the flat 6th row onto the array columns')
t1 = ly.cell('1T1R')
COLS_ARRAY = [-2885.0, -1735.0, -585.0, 565.0, 1715.0]
COLS_FLAT = [-2885.0, -1685.0, -485.0, 715.0, 1915.0]
for n in LAY:
    sh = t1.shapes(L[n])
    for s in list(sh.each()):
        b = s.bbox()
        if b.top * dbu > -2390 or b.bottom * dbu < -3210: continue
        for xa, xf in zip(COLS_ARRAY, COLS_FLAT):
            if b.left * dbu >= xf - 0.01 and b.right * dbu <= xf + 1065.01:
                if xa != xf: sh.transform(s, db.Trans(u(xa - xf), 0))
                break
        else:
            raise AssertionError(f'1T1R flat-row shape not in a column: {bbum(b)}')

# ===================================================================== 3. ResolutionTests to the corners
print('== ResolutionTests -> die corners')
rts = sorted([k for k in top.each_inst() if k.cell.name == 'ResolutionTests'], key=lambda k: k.bbox().left)
CROSS_EDGE, CROSS_CLEAR = 7270.0, 80.0
k = rts[0]; b = k.bbox()                                         # top-left: under the (-7000, 7000) cross
k.transform(db.Trans(u(-CROSS_EDGE) - b.left, u(6640 - 60) - b.top))       # below the Bxx_xx die title (bottom 6640)
k = rts[1]; b = k.bbox()                                         # bottom-right: above the (7000, -7000) cross
k.transform(db.Trans(u(CROSS_EDGE) - b.right, u(-6580) - b.bottom))       # point-symmetric to the top-left one
for k in rts: print('   ResolutionTests at', bbum(k.bbox()))

k = [k for k in top.each_inst() if k.cell.name == 'STEP_COVERAGE'][0]; k.transform(db.Trans(0, u(-40.0)))
print('   STEP_COVERAGE moved 40 um down ->', bbum(k.bbox()))

# ===================================================================== 1. text
print('\n== text -> Basic.TEXT PCells')
TG = db.TextGenerator.default_generator()
_tc = {}
def tcell(s, layer, mag):
    key = (s, layer, mag)
    if key not in _tc:
        _tc[key] = ly.create_cell('TEXT', 'Basic', {'text': s, 'layer': ly.get_info(L[layer]), 'mag': mag})
    return _tc[key]
def tb(s, mag):
    b = TG.text(s, dbu, mag).bbox(); return b.left * dbu, b.right * dbu      # glyph extent from the origin (um)
def tw(s, mag): return tb(s, mag)[1] - tb(s, mag)[0]
def th(mag): return 0.7 * mag

# strings of the old glmfont polygon text, keyed by (cell, left, bottom) of the line bbox in um (read from renders)
GLM = {
    ('MEM_T3_1', 2, 200): 'T3-1', ('MEM_A3_1', 0, 200): 'A3-1', ('MEM_V6_1', 0, 200): '6X6-1', ('MEM_V4_1', 0, 200): '4X4-1',
    ('MEM_V3_1', 1, 200): '3X3-1', ('MEM_V2_1', 0, 200): '2X2-1',
    ('MEM_O6_1', 0, 200): 'O6-1', ('MEM_O4_1', 0, 200): 'O4-1', ('MEM_O3_1', 0, 200): 'O3-1', ('MEM_O2_1', 0, 200): 'O2-1',  # drawn as 'G..' (copy bug)
    ('MEM_G6_1', 0, 200): 'G6-1', ('MEM_G4_1', 0, 200): 'G4-1', ('MEM_G3_1', 0, 200): 'G3-1', ('MEM_G2_1', 0, 200): 'G2-1',
    ('CBKR_M2G_4x20', 2909, -2748): '4X20', ('CBKR_M2G_8x10', 2910, -2748): '8X10', ('CBKR_M2G_4x10', 2909, -2748): '4X10',
    ('CBKR_M2G_2x10', 2910, -3128): '2X10',                     # was 'CBKR M3 GATED 2X10' drawn on the gate plate
    ('XBAR_4X4', -2, 1168): 'PASSIVE CROSSBAR 4X4',
    ('STEP_COVERAGE', -2, 128): 'STEP COVERAGE M3 OVER M1', ('STEP_COVERAGE', -2, 38): 'OVER 20 STEPS PER SEGMENT',
    ('STEP_COVERAGE', -2, -762): 'FLAT REFERENCE',
    ('MEM_STACK_SPLIT', -2, 148): 'MEMRISTOR STACK SPLIT',
    ('MEM_STACK_SPLIT', 678, -2850): 'HF 32X32', ('MEM_STACK_SPLIT', 678, -2170): 'HF 16X16', ('MEM_STACK_SPLIT', 678, -1490): 'HF 8X8',
    ('MEM_STACK_SPLIT', 678, -809): 'HF 4X4', ('MEM_STACK_SPLIT', 678, -130): 'HF 2X2', ('MEM_STACK_SPLIT', 678, 58): 'HFO2 ONLY',
    ('MEM_STACK_SPLIT', 3, -2850): 'IG 32X32', ('MEM_STACK_SPLIT', 3, 58): 'IGZO ONLY', ('MEM_STACK_SPLIT', 3, -810): 'IG 4X4',
    ('MEM_STACK_SPLIT', 3, -2170): 'IG 16X16', ('MEM_STACK_SPLIT', 3, -1490): 'IG 8X8', ('MEM_STACK_SPLIT', 3, -130): 'IG 2X2',
    ('CBKR_Structures', -2, 18): 'CBKR CONTACT RESISTANCE',
    ('TestStructures', -2134, -1074): 'GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)',
    ('MEM_ASYM', 678, -810): 'R10 J4X4', ('MEM_ASYM', 678, 94): 'RESERVOIR SWEEP', ('MEM_ASYM', -2, 148): 'ASYMMETRIC MEMRISTORS 2-10UM',
    ('MEM_ASYM', 678, -130): 'R4 J4X4', ('MEM_ASYM', -2, 94): 'ASYM JUNCTION', ('MEM_ASYM', -1, -810): 'J10X4',
    ('MEM_ASYM', -1, -130): 'J10X2', ('MEM_ASYM', -1, -2170): 'J4X10', ('MEM_ASYM', -1, -1490): 'J4X2', ('MEM_ASYM', -1, -2850): 'J2X10',
    ('MEM_ASYM', 678, -2850): 'R80 J4X4', ('MEM_ASYM', 678, -1490): 'R20 J4X4', ('MEM_ASYM', 678, -2170): 'R40 J4X4',
    ('MEM_HIGH_VALUE', -2, 198): 'HIGH VALUE MEMRISTOR SET', ('MEM_HIGH_VALUE', 538, 108): 'GUARD VS BARE',
    ('MEM_HIGH_VALUE', 875, -516): 'BARE 4X4', ('MEM_HIGH_VALUE', 875, 24): 'GRD 4X4', ('MEM_HIGH_VALUE', -2, 108): 'SERIES RESISTOR',
    ('MEM_HIGH_VALUE', 335, -516): 'SER L60', ('MEM_HIGH_VALUE', 335, 24): 'SER L30', ('MEM_HIGH_VALUE', 335, -1596): 'SER L140',
    ('MEM_HIGH_VALUE', 335, -1056): 'SER L100', ('MEM_HIGH_VALUE', 875, -1596): 'BARE 10X10', ('MEM_HIGH_VALUE', 875, -1056): 'GRD 10X10',
    ('MEM_REDUNDANT', 3, -130): 'IG 4X4 R2', ('MEM_REDUNDANT', 678, -130): 'HF 4X4 R2', ('MEM_REDUNDANT', 678, 58): 'HFO2 ONLY',
    ('MEM_REDUNDANT', 3, 58): 'IGZO ONLY', ('MEM_REDUNDANT', -2, 148): 'REDUNDANT SAMPLES',
}
# block title groups: old lines consumed -> new lines (top to bottom); anchored at the old group's left / lowest bottom
TITLES = {
    'PERF_TFT': (['HIGH-ID TFT: IDT AND LOV SWEEP', 'W=GATE N=SOURCE S=DRAIN'],
                 [('HIGH-ID TFT', 'T'), ('IDT AND LOV SWEEP', 'N'), ('PADS: W=GATE N=SOURCE S=DRAIN', 'N')]),
    'SYN_1T1R': (['GATE-SET COMPLIANCE ANALOG SYNAPSE 1T1R', 'W/L=25', 'W=GATE N=SOURCE S=DRAIN/BE NODE E=TE'],
                 [('SYNAPSE 1T1R', 'T'), ('GATE-SET COMPLIANCE ANALOG SYNAPSE, W/L=25', 'N'),
                  ('PADS: W=GATE N=SOURCE S=DRAIN/BE NODE E=TE', 'N')]),
    'NOVEL_DEVICES': (['NOVEL DEVICES - 5UM GATE OVERLAP, IGZO 45UM PAST GATE',
                       'LEFT: 4PR GATED 4-PROBE, FG FLOATING M2 GATE ON M1 CG', 'RIGHT: SPLIT M1/M2 DUAL-EOT GATE, 2T0C GAIN CELL'],
                      [('NOVEL DEVICES', 'T'), ('5UM GATE OVERLAP, IGZO 45UM PAST GATE', 'N'),
                       ('LEFT: 4PR GATED 4-PROBE, FG FLOATING M2 GATE ON M1 CG', 'N'),
                       ('RIGHT: SPLIT M1/M2 DUAL-EOT GATE, 2T0C GAIN CELL', 'N')]),
    'OVL_VERNIERS': (['OVERLAY VERNIERS 0.25UM/STEP +/-3UM, FIRST LAYER TOP/RIGHT'],
                     [('OVERLAY VERNIERS', 'T'), ('0.25UM/STEP +/-3UM, FIRST LAYER TOP/RIGHT', 'N')]),
    'Memristors_Gated': (['GATED MEMRISTORS - 1X/TYPE, GROUPED BY GAP LENGTH'],
                         [('GATED MEMRISTORS', 'T'), ('1X/TYPE, GROUPED BY GAP LENGTH', 'N')]),
    'Transistors_BottomGate_HfO2Only': (['TFT BOTTOM GATE STAGGERED - GATE = M2, HFO2 ONLY (AL2O3 BELOW M2, SAME WAFER)'],
                                        [('TRANSISTOR W/ BOTTOMGATE - HFO2 ONLY', 'T'),
                                         ('GATE = M2, HFO2 ONLY (AL2O3 BELOW M2, SAME WAFER)', 'N')]),
    'MIS_CV_Block': (['GUARDED MIS CAPACITORS', 'AREA-PERIMETER SERIES', 'N=INNER(BE) W=GUARD S=TE'],
                     [('GUARDED MIS CAPACITORS', 'T'), ('AREA-PERIMETER SERIES', 'N'), ('PADS: N=INNER(BE) W=GUARD S=TE', 'N')]),
    'XBAR_4X4': (['PASSIVE CROSSBAR 4X4'], [('CROSSBAR 4X4', 'T'), ('PASSIVE', 'N')]),
    'STEP_COVERAGE': (['STEP COVERAGE M3 OVER M1'], [('STEP COVERAGE', 'T'), ('M3 OVER M1', 'N')]),
    'MEM_STACK_SPLIT': (['MEMRISTOR STACK SPLIT'], [('MEMRISTOR STACK SPLIT', 'T')]),
    'CBKR_Structures': (['CBKR CONTACT RESISTANCE'], [('CBKR CONTACT RESISTANCE', 'T'), ('M3 GATED', 'N')]),
    'MEM_ASYM': (['ASYMMETRIC MEMRISTORS 2-10UM'], [('ASYMMETRIC MEMRISTORS', 'T'), ('2-10UM', 'N')]),
    'MEM_HIGH_VALUE': (['HIGH VALUE MEMRISTOR SET'], [('HIGH VALUE MEMRISTORS', 'T')]),
    'MEM_REDUNDANT': (['REDUNDANT SAMPLES'], [('REDUNDANT SAMPLES', 'T')]),
    ('TestStructures', 'OX2'): (['GATE OXIDE 2 TESTS (HFO2, BE=M2 TE=M3)'], [('GATE OXIDE 2 TESTS', 'T'), ('HFO2, BE=M2 TE=M3', 'N')]),
    ('TestStructures', 'OX1'): (['GATE OXIDE 1 TESTS'], [('GATE OXIDE 1 TESTS', 'T'), ('AL2O3, BE=M1 TE=M2', 'N')]),
}
TITLE_SINGLE = {'TRANSISTOR W/ BOTTOMGATE - STAGGERED', 'MEMRISTORS', '1-TRANSISTOR-1-MEMRISTOR', 'TLM BACK-BIAS',
                'GATED VDP & GREEK CROSS'}
NOTE_STR = {'BE', 'TE', '30', '60', '90', '120', '150', '180', '210', '240', '270'}
def tier_of(cell, s):
    if s in TITLE_SINGLE: return 'T'
    if s in NOTE_STR or s.startswith('X') and s[1:].strip().lstrip('-').isdigit() or s.startswith('Y') and s[1:].strip().lstrip('-').isdigit():
        return 'N'
    return 'L'

# ---- collect every text line in placed cells
items = []          # dict(cell, layer, s, box(dbu, cell coords), src)
removed = defaultdict(list)     # cell -> list of (layer, polygon) removed (for the preservation diff)
for ci in sorted(placed):
    c = ly.cell(ci)
    if is_text(c) or c.name in EXEMPT_CELLS: continue
    for n in LAY:
        li = L[n]
        if c.shapes(li).is_empty(): continue
        for s, m, x0, yb, shp in textocr.find_text(c, li, dbu):
            items.append(dict(cell=c.name, layer=n, s=s.upper(), box=db.Region([q.polygon for q in shp]).bbox(), src='std'))
            for q in shp: removed[c.name].append((n, q.polygon)); c.shapes(li).erase(q)
        polys = [s_ for s_ in c.shapes(li).each() if s_.is_polygon() or s_.is_box()]
        pl = [s_.polygon for s_ in polys]; back = {id(p): s_ for p, s_ in zip(pl, polys)}
        for grp in textocr._lines(pl, dbu, 45.0):
            b = db.Region(grp).bbox()
            key = (c.name, round(b.left * dbu), round(b.bottom * dbu))
            if key not in GLM: continue
            items.append(dict(cell=c.name, layer=n, s=GLM.pop(key), box=b, src='glm'))
            for p in grp: removed[c.name].append((n, p)); c.shapes(li).erase(back[id(p)])
assert not GLM, ('glm lines not found', list(GLM))
# static spliced labels + existing Basic.TEXT instances
for ci in sorted(placed):
    c = ly.cell(ci)
    if is_text(c) or c.name in EXEMPT_CELLS: continue
    for k in list(c.each_inst()):
        tc_ = k.cell
        if not is_text(tc_): continue
        if tc_.name in ('TEXT_L2_W500', 'TEXT_L3_W500'):
            s, n = tc_.name[5:], 'Metal_1'
        else:
            p = tc_.pcell_parameters_by_name(); s = p['text'].upper(); n = p['layer'].name
            if s in EXEMPT_STR: continue
        assert k.cplx_trans.is_unity() or (k.trans.rot == 0 and not k.trans.is_mirror()), (c.name, s)
        assert not k.is_regular_array(), (c.name, s)
        items.append(dict(cell=c.name, layer=n, s=s, box=k.bbox(), src='pcell'))
        c.erase(k)
for n_ in ('TEXT_L2_W500', 'TEXT_L3_W500'): ly.delete_cell(ly.cell(n_).cell_index())
print('   text lines collected:', Counter(i['src'] for i in items))

exec(open(os.path.join(HERE, 'text_place_v52.py'), encoding='utf-8').read())

# ===================================================================== re-pack blocks whose device cells grew
GAP_Y, GAP_X, BLOCK_GAP = 50.0, 60.0, 120.0
ORDER = {'PERF_TFT': ['PT_REF_W100_L10', 'PT_IDT_W1000_L10', 'PT_IDT_W1000_L5', 'PT_IDT_W2000_L10',
                      'PT_LOV2', 'PT_LOV10', 'PT_LOV20', 'PT_LOV40'],
         'SYN_1T1R': ['SYN_W500_L20_J2', 'SYN_W500_L20_J4', 'SYN_W250_L10_J2', 'SYN_W250_L10_J4',
                      'SYN_W125_L5_J2', 'SYN_W125_L5_J4', 'SYN_W50_L2_J2', 'SYN_W50_L2_J4'],
         'NOVEL_DEVICES': ['NV_4PR_M1', 'NV_4PR_M2', 'NV_FG_R0', 'NV_FG_R2', 'NV_FG_R5', 'NV_FG_R2_PAD',
                           'NV_SPLIT_M1S', 'NV_SPLIT_M2S', 'NV_2T0C_L10', 'NV_2T0C_L50', 'NV_2T0C_CAL']}
def pack_columns(c, order, H, x0=5.0, ytop=-5.0):
    ins = {i.cell.name: i for i in c.each_inst() if not is_text(i.cell)}
    assert sorted(ins) == sorted(order), (c.name, sorted(ins))
    cols, col, h = [], [], 0.0
    for n in order:
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
    return [len(cl) for cl in cols]
def inst(name): return [k for k in top.each_inst() if k.cell.name == name][0]
print('\n== re-pack')
for bname, H in (('PERF_TFT', 4419.0 - 5.0 - 1398.0), ('SYN_1T1R', 4419.0 - 5.0 - 1398.0), ('NOVEL_DEVICES', 4300.0)):
    print(f'   {bname}: columns {pack_columns(ly.cell(bname), ORDER[bname], H)}')
pk, sk = inst('PERF_TFT'), inst('SYN_1T1R'); pb, sb = pk.bbox(), sk.bbox()
sk.transform(db.Trans(pb.right + u(BLOCK_GAP) - sb.left, pb.top - sb.top))
for n_ in ('PERF_TFT', 'SYN_1T1R', 'NOVEL_DEVICES'): print(f'   {n_:14s}', bbum(inst(n_).bbox()))

def flat(i):
    r = db.Region()
    for n in LAY: r = r.or_(db.Region(i.cell.begin_shapes_rec(L[n])).transformed(db.ICplxTrans(i.trans)))
    r.merge(); return r
exec(open(os.path.join(HERE, 'verify_v52.py'), encoding='utf-8').read())
