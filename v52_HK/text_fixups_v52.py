# per-case corrections to the generic text placement (executed inside build_v52.py)
def fix(cell, s, **kw):
    hit = [t for t in newtext if t['cell'] == cell and t['s'] == s]
    assert hit, (cell, s)
    for t in hit: t.update(kw)
# CBKR 2x10: the old label sat on the gate plate; use the same place as its three sibling cells
fix('CBKR_M2G_2x10', '2X10', x=2952.5 - (tb('2X10', 50.0)[0] + tb('2X10', 50.0)[1]) / 2, y=-2734.5 - th(50.0) / 2)
