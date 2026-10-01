print('\n== 4. align TLM_BACK_BIAS and the Greek-cross structure to a common baseline (row1 tidy-up)')
ts = ly.cell('TestStructures')

def own_region_in_zone(cell_, x0, x1, y0, y1, layers_):
    r = db.Region()
    for n in layers_:
        for s in cell_.shapes(L[n]).each():
            if not (s.is_polygon() or s.is_box()): continue
            b = s.polygon.bbox()
            if b.left * dbu >= x0 and b.right * dbu <= x1 and b.bottom * dbu >= y0:
                r.insert(s.polygon)
    return r

TS_LAY = ('Metal_1', 'Isolation_1', 'Metal_2', 'IGZO', 'Metal_3', PASS)
gx_zone_before = own_region_in_zone(ts, -50, 1600, 300, 1e9, TS_LAY)
tlm_zone = own_region_in_zone(ts, -2200, 0, 300, 1e9, TS_LAY)
gx_bottom = gx_zone_before.bbox().bottom * dbu
tlm_bottom = tlm_zone.bbox().bottom * dbu
dy_align = tlm_bottom - gx_bottom
print(f'   TLM bottom {tlm_bottom:.1f}  Greek-cross bottom {gx_bottom:.1f}  -> shifting Greek-cross up by {dy_align:.1f}um to match')

gx_polys = {n: [] for n in TS_LAY}
for n in TS_LAY:
    for s in list(ts.shapes(L[n]).each()):
        if not (s.is_polygon() or s.is_box()): continue
        b = s.polygon.bbox()
        if b.left * dbu >= -50 and b.right * dbu <= 1600 and b.bottom * dbu >= 300:
            gx_polys[n].append(s.polygon)
            ts.shapes(L[n]).erase(s)
d3 = db.Trans(0, u(dy_align))
for n, polys in gx_polys.items():
    for p in polys: ts.shapes(L[n]).insert(p.transformed(d3))
print(f'   moved {sum(len(v) for v in gx_polys.values())} Greek-cross shapes (structure + its title)')

# verify headroom to the nearest real obstacle above (1T1R, per the v45 survey) with the whole
# updated TestStructures content, not just this one structure
ts_inst2 = [k for k in top.each_inst() if k.cell.name == 'TestStructures'][0]
gx_top_new = gx_zone_before.bbox().top * dbu + dy_align
gx_top_TOPcoord = gx_top_new + (ts_inst2.trans.disp.y * dbu)
obstacle_bottom_1t1r = -2813.5
margin = obstacle_bottom_1t1r - gx_top_TOPcoord
print(f'   Greek-cross new top in TOP coords: {gx_top_TOPcoord:.1f}, nearest obstacle (1T1R) bottom {obstacle_bottom_1t1r:.1f}, margin {margin:.1f} um')
assert margin > 0, 'row1 tidy-up would collide with 1T1R -- stop'

exec(open(os.path.join(HERE, 'verify_v47b.py'), encoding='utf-8').read())
