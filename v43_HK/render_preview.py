import sys, klayout.db as db, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as P
col = {'Metal_1': '#d22', 'Isolation_1': '#888', 'Metal_2': '#36c', 'IGZO': '#2a2', 'Metal_3': '#e90',
       'Isolation_2': '#c6c', 'Passivation': '#c6c', 'Metal_4': '#0aa', 'Alignment': '#000', '': '#c0c'}
def render(f, cell, out, box=None, W=9):
    ly = db.Layout(); ly.read(f); dbu = ly.dbu; c = ly.cell(cell); b = c.bbox()
    if box: x0, y0, x1, y1 = box
    else: x0, y0, x1, y1 = b.left*dbu, b.bottom*dbu, b.right*dbu, b.top*dbu
    w = x1-x0; h = y1-y0
    fig, ax = plt.subplots(figsize=(W, W*h/w), dpi=110)
    for l in ly.layer_indexes():
        n = ly.get_info(l).name or ''
        it = c.begin_shapes_rec(l)
        while not it.at_end():
            s = it.shape()
            if s.is_polygon() or s.is_box() or s.is_path():
                p = s.polygon.transformed(it.trans())
                ax.add_patch(P([(q.x*dbu, q.y*dbu) for q in p.each_point_hull()], fc=col[n], ec='none', alpha=.55))
            it.next()
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(out, bbox_inches='tight'); plt.close(fig)
if __name__ == '__main__':
    f, out = sys.argv[1], sys.argv[2]
    for cell in sys.argv[3:]:
        if ':' in cell:
            cell, bx = cell.split(':'); box = [float(v) for v in bx.split(',')]
        else: box = None
        render(f, cell, out + '_' + cell + '.png', box)

