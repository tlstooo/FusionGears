"""Offline checks of gearmath (no Fusion needed): python tests/test_gearmath.py"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import gearmath as gm  # noqa: E402
import presets  # noqa: E402
import gearcheck  # noqa: E402

gm.FLANK_POINTS = 40
D = math.radians


def close(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def check_chain(segs, tol=1e-9):
    for (_, a), (_, b) in zip(segs, segs[1:] + segs[:1]):
        assert close(a[-1], b[0], tol), (a[-1], b[0])


def arc_points(p0, pm, p1, n=40):
    """Densify a 2D arc through three points."""
    ax, ay = p0; bx, by = pm; cx, cy = p1
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (p0, pm, p1))
    span = (a1 - a0) % (2 * math.pi)
    if (am - a0) % (2 * math.pi) > span:   # goes clockwise
        span -= 2 * math.pi
    return [(ux + r * math.cos(a0 + span * i / n), uy + r * math.sin(a0 + span * i / n)) for i in range(n + 1)]


def polygon(segs2d):
    out = []
    for kind, pts in segs2d:
        out += arc_points(*pts) if kind == 'arc' else pts
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def min_gap(poly_a, poly_b):
    return min(seg_dist(p, a, b) for p in poly_a for a, b in zip(poly_b, poly_b[1:] + poly_b[:1]))


def near(poly, centre, radius):
    """Keep only the part of a polygon close to the contact zone (keeps the check fast)."""
    return [p for p in poly if math.dist(p, centre) < radius]


def mesh_check(poly1, poly2, what, centre=None, radius=None):
    if centre is not None:
        a, b = near(poly1, centre, radius), near(poly2, centre, radius)
        bad = sum(inside(p, poly2) for p in a) + sum(inside(p, poly1) for p in b)
        assert bad == 0, f'{what}: interference ({bad} points)'
        return min(seg_dist(p, q, r) for p in a for q, r in zip(b, b[1:]) if math.dist(q, r) < radius)
    bad = sum(inside(p, poly2) for p in poly1) + sum(inside(p, poly1) for p in poly2)
    assert bad == 0, f'{what}: interference ({bad} points)'
    return min_gap(poly1, poly2)


def rot2(p, a, c=(0, 0)):
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def test_cylindrical():
    for kind_beta in (0.0, D(20), D(30)):
        g1 = gm.CylindricalGear(0.2, 17, kind_beta, D(20), 2.0, backlash=0.005)
        g2 = gm.CylindricalGear(0.2, 31, kind_beta, D(20), 2.0, hand=-1, backlash=0.005)
        o1, o2 = g1.outline(), g2.outline()
        check_chain(o1); check_chain(o2)
        assert abs(g1.center_distance(g2) - 0.2 * 48 / 2 / math.cos(kind_beta)) < 1e-12
        m = g1.mate_transform(g2)
        p1 = polygon([(k, [p[:2] for p in pts]) for k, pts in o1])
        p2 = polygon([(k, [gm.apply(m, p)[:2] for p in pts]) for k, pts in o2])
        a = g1.center_distance(g2)
        gaps = []
        for step in range(12):   # rotate through one pitch of gear 1
            t = 2 * math.pi / g1.z * step / 12
            q1 = [rot2(p, t) for p in p1]
            q2 = [rot2(p, -t * g1.z / g2.z, (a, 0)) for p in p2]
            gaps.append(mesh_check(q1, q2, f'cyl beta={math.degrees(kind_beta)}', (g1.r, 0), 4 * g1.mn))
        assert max(gaps) < 0.01, gaps   # flanks stay in contact (within backlash)
        # helix: twist over width equals width*tan(beta)/r, opposite on the mate
        assert abs(g1.twist(1) + g2.twist(1) * g2.r / g1.r) < 1e-12
    print('cylindrical: ok')


def plane_coords(origin, ex, ey, p):
    d = [p[i] - origin[i] for i in range(3)]
    return (sum(d[i] * ex[i] for i in range(3)), sum(d[i] * ey[i] for i in range(3)))


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v]


def test_bevel():
    for line, beta in (('straight', 0.0), ('skew', D(25)), ('spiral', D(35))):
        g1 = gm.BevelGear(0.2, 18, 27, D(90), D(20), 0.9, line, beta, backlash=0.005, back=0.5, bore=0.6)
        g2 = g1.mate()
        assert abs(g1.delta + g2.delta - D(90)) < 1e-12
        assert abs(g1.Re - g2.Re) < 1e-12
        m = g1.mate_transform(g2)
        assert close(gm.apply(m, (0, 0, g2.apex_z)), (0, 0, g1.apex_z), 1e-12)   # common apex
        # pitch point of gear 1 (heel, azimuth 0) lies on gear 2's pitch circle
        best = min(math.dist(gm.apply(m, (g2.r * math.cos(a), g2.r * math.sin(a), 0)), (g1.r, 0, 0))
                   for a in [i * 2 * math.pi / 3600 for i in range(3600)])
        assert best < 3e-3, best
        for R in g1.section_distances():
            segs = g1.section(R)
            check_chain(segs)
            o, a_, b_ = g1.section_plane(R)
            n = unit(cross([a_[i] - o[i] for i in range(3)], [b_[i] - o[i] for i in range(3)]))
            for _, pts in segs:
                for p in pts:   # section is planar
                    assert abs(sum((p[i] - o[i]) * n[i] for i in range(3))) < 1e-9
        # gear 1 tooth (azimuth 0) sits in the middle of a gear 2 tooth gap at mid face
        R = g1.Rm
        tip = g1._point(R, g1.rv, 0.0)
        d = sorted(math.dist(tip, gm.apply(m, gm.apply(gm.rot_z(2 * math.pi * k / g2.z), g2._point(R, g2.rv, 0.0))))
                   for k in range(g2.z))
        assert abs(d[0] - d[1]) < 1e-9 and d[2] > d[1] * 1.5, d[:3]
        # mesh of the virtual (back-cone) spur gears: no interference, flanks in contact
        def virtual(g, c, centre=(0, 0)):
            segs = gm._tooth_chain(g.flank, g.ra_v)
            return polygon([(k, [rot2((p[0] * math.cos(p[1] + c), p[0] * math.sin(p[1] + c)), 0)
                                 for p in pts]) for k, pts in segs])
        a = g1.rv + g2.rv
        gaps = []
        for step in range(8):
            t = 2 * math.pi / g1.zv * (step / 8 - 0.5)
            poly1 = virtual(g1, t)
            for k in (-1, 0):
                c2 = math.pi + math.pi / g2.zv + 2 * math.pi * k / g2.zv - t * g1.zv / g2.zv
                poly2 = [(a + x, y) for x, y in virtual(g2, c2)]
                gaps.append(mesh_check(poly1, poly2, f'bevel {line}', (g1.rv, 0), 4 * g1.m))
        assert max(min(gaps[i:i + 2]) for i in range(0, len(gaps), 2)) < 0.01, gaps
        x = g1.blank_profile()
        assert x[1][0] > 0.3 and x[3][1] < x[0][1] < x[1][1]
        print(f'bevel {line}: ok  delta={math.degrees(g1.delta):.2f}/{math.degrees(g2.delta):.2f} virtual mesh gap {min(gaps):.4f}')


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def test_errors():
    for kw in (dict(mn=0.2, z=3, beta=0, alpha_n=D(20), width=1),
               dict(mn=0.2, z=20, beta=0, alpha_n=D(20), width=1, bore=5)):
        try:
            gm.CylindricalGear(**kw)
        except gm.GearError:
            continue
        raise AssertionError(kw)
    try:
        gm.BevelGear(0.2, 20, 20, D(90), D(20), 5.0)
    except gm.GearError:
        pass
    else:
        raise AssertionError('too wide face accepted')
    print('errors: ok')


CYL_IDS = {'kind', 'module', 'teeth', 'beta', 'hand', 'alpha', 'width', 'bore', 'backlash',
           'pair', 'teeth2', 'bore2', 'drive'}
BEVEL_IDS = {'line', 'module', 'teeth', 'teeth2', 'sigma', 'beta', 'hand', 'alpha', 'width', 'back',
             'bore', 'backlash', 'sections', 'pair', 'bore2', 'drive'}
KINDS = {'Шевронный': 0, 'Косозубый': 1, 'Прямозубый': 2}
LINES = {'Прямой': 'straight', 'Косой (тангенциальный)': 'skew', 'Спиральный (круговой)': 'spiral'}


def test_presets():
    """Every preset gives valid gears whose pair meshes (as in the dialog, mm -> cm)."""
    cm = lambda v: v / 10
    for name, p in presets.CYLINDRICAL:
        assert set(p) <= CYL_IDS, set(p) - CYL_IDS
        beta = 0.0 if KINDS[p['kind']] == 2 else D(p['beta'])
        args = dict(mn=cm(p['module']), beta=beta, alpha_n=D(p['alpha']), width=cm(p['width']),
                    backlash=cm(p['backlash']))
        g1 = gm.CylindricalGear(z=p['teeth'], bore=cm(p['bore']), **args)
        g2 = gm.CylindricalGear(z=p['teeth2'], hand=-1, bore=cm(p['bore2']), **args)
        m = g1.mate_transform(g2)
        p1 = polygon([(k, [q[:2] for q in pts]) for k, pts in g1.outline()])
        p2 = polygon([(k, [gm.apply(m, q)[:2] for q in pts]) for k, pts in g2.outline()])
        a = g1.center_distance(g2)
        for step in range(6):
            t = 2 * math.pi / g1.z * step / 6
            mesh_check([rot2(q, t) for q in p1], [rot2(q, -t * g1.z / g2.z, (a, 0)) for q in p2],
                       name, (g1.r, 0), 4 * g1.mn)
        print(f'  preset ok: {name}  a={a * 10:.2f} mm')
    for name, p in presets.BEVEL:
        assert set(p) <= BEVEL_IDS, set(p) - BEVEL_IDS
        g1 = gm.BevelGear(cm(p['module']), p['teeth'], p['teeth2'], D(p['sigma']), D(p['alpha']),
                          cm(p['width']), LINES[p['line']], D(p.get('beta', 30)), 1, cm(p['backlash']),
                          cm(p['back']), cm(p['bore']), p.get('sections', 7))
        g2 = g1.mate(cm(p['bore2']))
        assert p['width'] <= g1.Re * 10 / 3 + 1e-9, f'{name}: face wider than Re/3'
        print(f'  preset ok: {name}  Re={g1.Re * 10:.2f} mm, b<=Re/3')


def test_gearcheck():
    fc = gearcheck.find_conflicts
    assert fc([('A', 'B', -17 / 31, 'p'), ('B', 'C', -31 / 20, 'q')]) == []          # chain
    assert fc([('A', 'B', -1, '1'), ('B', 'C', -1, '2'), ('C', 'D', -1, '3'), ('D', 'A', -1, '4')]) == []
    tri = fc([('A', 'B', -1, 'AB'), ('B', 'C', -1, 'BC'), ('C', 'A', -1, 'CA')])     # odd loop
    assert len(tri) == 1 and tri[0]['opposite']
    dup = fc([('A', 'B', -0.5, 'x'), ('A', 'B', 0.5, 'y')])                          # duplicate, reversed
    assert len(dup) == 1 and dup[0]['opposite']
    speed = fc([('A', 'B', -0.5, 'x'), ('B', 'C', -2, 'y'), ('A', 'C', 1.5, 'z')])  # wrong ratio
    assert len(speed) == 1 and not speed[0]['opposite']
    two = fc([('A', 'B', -1, '1'), ('B', 'C', -1, '2'), ('C', 'A', -1, '3'),       # two separate faults
              ('D', 'E', -1, '4'), ('D', 'E', 1, '5')])
    assert len(two) == 2
    assert 'в разные стороны' in gearcheck.describe(tri[0])
    print('gearcheck: ok')


def test_mesh_phase():
    """A chain at an angle and an equal-gear triangle mesh without interference."""
    def poly(g, m):
        return polygon([(k, [gm.apply(m, q)[:2] for q in pts]) for k, pts in g.outline()])
    G = [gm.CylindricalGear(0.15, z, 0, D(20), 0.8, 1, 0.01) for z in (15, 30, 20)]
    place = [(0.0, 0.0, 0.0)]
    for (i, j), th in (((0, 1), 0.0), ((1, 2), D(70))):
        d = G[i].r + G[j].r
        x, y, phi = place[i]
        place.append((x + d * math.cos(th), y + d * math.sin(th), gm.mesh_phase(G[i], phi, th, G[j])))
    polys = [poly(g, gm.placement(*p)) for g, p in zip(G, place)]
    for i, j in ((0, 1), (1, 2)):
        c = tuple((place[i][k] * G[j].r + place[j][k] * G[i].r) / (G[i].r + G[j].r) for k in (0, 1))
        assert mesh_check(polys[i], polys[j], 'chain', c, 4 * 0.15) < 0.01
    print('mesh_phase: ok')


if __name__ == '__main__':
    test_mesh_phase()
    test_gearcheck()
    test_presets()
    test_cylindrical()
    test_bevel()
    test_errors()
