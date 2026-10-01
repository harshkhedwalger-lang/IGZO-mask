"""mkaudit.py -- fabricability audit + overlay-enclosure rules for the HK mask series (klayout.db only).

Process flow the rules encode:  M1 | Al2O3#1 | M2 | HfO2 | [Iso1 etch] | IGZO | M3 | Passivation | [Iso2/Passivation open]
Layer names are looked up by NAME; the passivation layer is called 'Passivation' (6/0), older files 'Isolation_2'.
"""
import klayout.db as db

OVL = 2.0     # assumed worst-case layer-to-layer overlay of the laser writer [um]  (set to your measured value)
ENC = 3.0     # minimum enclosure  = OVL + 1 um process margin                        [um]

def names(ly):
    return {(ly.get_info(i).name or '63'): i for i in ly.layer_indexes()}

class Audit:
    def __init__(self, ly, enc=ENC):
        self.ly = ly; self.dbu = ly.dbu; self.L = names(ly); self.enc = enc
        self.P = 'Passivation' if 'Passivation' in self.L else 'Isolation_2'
        self.has4 = 'Metal_4' in self.L
    def u(self, x): return int(round(x / self.dbu))
    def R(self, c, n):
        """merged geometry of layer n, recursive, WITHOUT the text cells (TEXT*) and without own glyph polygons"""
        if n not in self.L: return db.Region()
        it = c.begin_shapes_rec(self.L[n])
        it.unselect_cells([x.cell_index() for x in self.ly.each_cell() if x.name.startswith('TEXT')])
        r = db.Region(it)
        if n == 'Metal_1':
            r = db.Region([p for p in r.each() if not self.isglyph(p)]) if False else r
        r.merge(); return r
    def isglyph(self, p):
        b = p.bbox(); d = self.dbu
        return b.height() * d <= 40 and b.width() * d <= 120 and p.area() * d * d < 1500

    # ---------------------------------------------------------------- connectivity / fabricability
    def connectivity(self, cells):
        out = []; u = self.u; dbu = self.dbu
        for cn in cells:
            c = self.ly.cell(cn)
            m1, m2, m3 = self.R(c, 'Metal_1'), self.R(c, 'Metal_2'), self.R(c, 'Metal_3')
            m4 = self.R(c, 'Metal_4'); ig = self.R(c, 'IGZO'); i1 = self.R(c, 'Isolation_1'); i2 = self.R(c, self.P)
            met = m1 + m2 + m3 + m4
            if (i1 - (met + ig)).area(): out.append((cn, 'Iso1 window off metal/IGZO'))
            if (i2 - (met + ig)).area(): out.append((cn, 'Passivation window off metal'))
            for p in i2.each():      # probe window on M1/M2 needs the pad exposed: Iso1 window under it OR an M3 cap over it
                pr = db.Region(p)
                if not pr.and_(m1 + m2).is_empty() and pr.not_(m3 + i1).area() > 0.2 * p.area():
                    out.append((cn, 'pad on M1/M2 buried (no Iso1 window, no M3 cap)'))
            for p in i1.each():                                    # one etch opens Al2O3#1 AND HfO2 -> never M1+M2
                pr = db.Region(p)
                if not pr.and_(m1).is_empty() and not pr.and_(m2).is_empty(): out.append((cn, 'Iso1 window shorts M1 to M2'))
            for p in ig.each():
                pr = db.Region(p)
                if pr.and_(m3).is_empty() and i1.interacting(pr).count() == 0: out.append((cn, 'IGZO island with no contact'))
            for nm, reg in (('Metal_1', m1), ('Metal_2', m2), ('Metal_3', m3)):
                for p in reg.each():
                    if p.area() * dbu * dbu < 400: continue
                    pr = db.Region(p)
                    if self.isglyph(p): continue
                    if pr.width_check(u(6.0), False, db.Region.Projection, None, None, None).count(): continue
                    if i2.interacting(pr).count() or i1.interacting(pr).count(): continue
                    if nm in ('Metal_2', 'Metal_3') and not pr.and_(ig).is_empty(): continue
                    out.append((cn, nm + ' island floating'))
        return out

    # ---------------------------------------------------------------- overlay / enclosure rules
    def overlay(self, cells):
        """O1 Iso1 window inside the M1 or M2 it lands on by >= ENC
           O2 M3 encloses every Iso1 window it contacts by >= ENC
           O3 Passivation window inside M3 by >= ENC
           O4 Passivation window and Iso1 window never closer than ENC to a foreign metal edge of a different net layer"""
        out = []; u = self.u; e = u(self.enc)
        for cn in cells:
            c = self.ly.cell(cn)
            m1, m2, m3 = self.R(c, 'Metal_1'), self.R(c, 'Metal_2'), self.R(c, 'Metal_3')
            i1 = self.R(c, 'Isolation_1'); i2 = self.R(c, self.P)
            for p in i1.each():
                pr = db.Region(p); big = pr.sized(e)
                if not pr.and_(m1).is_empty():
                    if not (big - m1).is_empty(): out.append((cn, 'O1 Iso1 window not enclosed by M1', self._pos(p)))
                elif not pr.and_(m2).is_empty():
                    if not (big - m2).is_empty(): out.append((cn, 'O1 Iso1 window not enclosed by M2', self._pos(p)))
                if not pr.and_(m3).is_empty() and not (big - m3).is_empty():
                    out.append((cn, 'O2 M3 does not enclose Iso1 window', self._pos(p)))
            ovl = u(OVL)
            for p in i2.each():
                pr = db.Region(p)
                if (pr.sized(e) - m3).is_empty(): continue                       # M3 pad, enclosed by >= ENC
                # direct exposure of an M1/M2 pad: metal must enclose the window by ENC and the
                # Iso1 window must still cover the window after a worst-case shift (window shrunk by OVL)
                metal = m1 if not pr.and_(m1).is_empty() else m2
                if not (pr.sized(e) - metal).is_empty(): out.append((cn, 'O3 passivation window not enclosed by its pad metal', self._pos(p)))
                elif not (pr.sized(-ovl) - i1).is_empty(): out.append((cn, 'O3 Iso1 window does not cover the probe window', self._pos(p)))
        return out
    def _pos(self, p):
        b = p.bbox(); return f'({b.left * self.dbu:.0f},{b.bottom * self.dbu:.0f})'
