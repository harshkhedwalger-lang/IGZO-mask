"""Recover polygon text drawn with KLayout's std_font (TextGenerator / Basic.TEXT) back to strings.
A line is accepted only if re-rendering the decoded string reproduces its polygons exactly (XOR ~ 0)."""
import klayout.db as db
TG = db.TextGenerator.default_generator()
CHARS = [chr(c) for c in range(33, 127)]
_cache = {}
def glyphs(m, dbu):
    key = (round(m, 6), dbu)
    if key not in _cache:
        g = {}
        for ch in CHARS:
            r = TG.text(ch, dbu, m); r.merge(); g[ch] = r
        _cache[key] = g
    return _cache[key]
def _lines(polys, dbu, hmax):
    HB = 1.6 * hmax / dbu
    cand = [p for p in polys if p.bbox().height() * dbu <= hmax and p.bbox().width() * dbu <= hmax]
    n = len(cand); par = list(range(n))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    bs = [p.bbox() for p in cand]
    order = sorted(range(n), key=lambda i: bs[i].left)
    for ii, i in enumerate(order):
        bi = bs[i]
        for j in order[ii + 1:]:
            bj = bs[j]
            h = max(bi.height(), bj.height(), 1)
            if bj.left - bi.right > HB: break
            if bj.left - bi.right > 1.6 * h: continue
            ov = min(bi.top, bj.top) - max(bi.bottom, bj.bottom)
            if ov > 0.3 * min(bi.height(), bj.height()) or (ov >= 0 and min(bi.height(), bj.height()) < 0.2 * h):
                par[f(i)] = f(j)
    groups = {}
    for i in range(n): groups.setdefault(f(i), []).append(cand[i])
    return list(groups.values())
def decode_line(pl, dbu):
    reg = db.Region(pl); reg.merge(); b = reg.bbox()
    yb = b.bottom; H = (b.top - yb) * dbu
    if H <= 0: return None
    for mm in (H / 0.7,):
        p = 0.6 * mm
        gl = glyphs(mm, dbu)
        left = min(q.bbox().left for q in pl)
        for bear in range(0, 11):
            x0 = left - int(round(bear * 0.05 * mm / dbu))
            s = ''; ok = True
            slots = {}
            for q in pl:
                cx = (q.bbox().left + q.bbox().right) / 2
                k = int((cx - x0) // (p / dbu)); slots.setdefault(k, []).append(q)
            kmax = max(slots)
            if min(slots) < 0: continue
            for k in range(kmax + 1):
                if k not in slots: s += ' '; continue
                sr = db.Region(slots[k]); sr.merge()
                sr = sr.moved(-(x0 + int(round(k * p / dbu))), -yb)
                best = None
                for ch, g in gl.items():
                    if g.bbox().height() == 0: continue
                    x = (sr ^ g).area() * dbu * dbu
                    if x < 0.02 * max(g.area() * dbu * dbu, 1):
                        best = ch; break
                if best is None: ok = False; break
                s += best
            if not ok: continue
            full = TG.text(s, dbu, mm).moved(x0, yb); full.merge()
            if (full ^ reg).area() * dbu * dbu < 0.01 * reg.area() * dbu * dbu + 1:
                return s, mm, x0, yb
    return None
def find_text(cell, layer_index, dbu, hmax=100.0):
    """returns list of (string, mag, x0_dbu, ybase_dbu, [shapes]) for polygon text in cell's own shapes"""
    shp = {}
    for s in cell.shapes(layer_index).each():
        if s.is_polygon() or s.is_box() or s.is_path(): shp.setdefault(id(s), s)
    polys = []; back = {}
    for s in cell.shapes(layer_index).each():
        if not (s.is_polygon() or s.is_box()): continue
        p = s.polygon; polys.append(p); back[len(polys) - 1] = s
    idx = {id(p): i for i, p in enumerate(polys)}
    out = []
    for grp in _lines(polys, dbu, hmax):
        r = decode_line(grp, dbu)
        if r: out.append((r[0], r[1], r[2], r[3], [back[idx[id(p)]] for p in grp]))
    return out
