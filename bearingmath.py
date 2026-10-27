"""Rolling bearings: catalogue of standard sizes and section geometry. No Fusion dependencies.

Sizes are boundary dimensions d x D x B (radial, ISO 15) and d x D x H (thrust,
ISO 104) in mm. Internal geometry (balls, raceways) is not standardised; it is a
proportional approximation good enough for assemblies and clearance checks.
Geometry is in cm (Fusion's internal unit); the bearing axis is Z, from z = 0.
Sections are in the XZ plane as segment chains of (x, 0, z) points, the format
of gearmath outlines: ('line', [p, q]) and ('arc', [p, mid, q]).
"""
import math

from gearmath import GearError

KINDS = ('radial', 'thrust')

# series key -> (kind, [(designation, d, D, B or H) in mm])
SERIES = {
    'mini': ('radial', [
        ('MR85', 5, 8, 2.5), ('MR105', 5, 10, 4), ('623', 3, 10, 4), ('624', 4, 13, 5),
        ('625', 5, 16, 5), ('626', 6, 19, 6), ('627', 7, 22, 7), ('688', 8, 16, 5),
        ('698', 8, 19, 6), ('608', 8, 22, 7), ('609', 9, 24, 7)]),
    '618': ('radial', [
        ('6800', 10, 19, 5), ('6801', 12, 21, 5), ('6802', 15, 24, 5), ('6803', 17, 26, 5),
        ('6804', 20, 32, 7), ('6805', 25, 37, 7), ('6806', 30, 42, 7), ('6807', 35, 47, 7),
        ('6808', 40, 52, 7), ('6810', 50, 65, 7)]),
    '619': ('radial', [
        ('6900', 10, 22, 6), ('6901', 12, 24, 6), ('6902', 15, 28, 7), ('6903', 17, 30, 7),
        ('6904', 20, 37, 9), ('6905', 25, 42, 9), ('6906', 30, 47, 9), ('6908', 40, 62, 12),
        ('6910', 50, 72, 12)]),
    '60': ('radial', [
        ('6000', 10, 26, 8), ('6001', 12, 28, 8), ('6002', 15, 32, 9), ('6003', 17, 35, 10),
        ('6004', 20, 42, 12), ('6005', 25, 47, 12), ('6006', 30, 55, 13), ('6007', 35, 62, 14),
        ('6008', 40, 68, 15), ('6009', 45, 75, 16), ('6010', 50, 80, 16), ('6012', 60, 95, 18)]),
    '62': ('radial', [
        ('6200', 10, 30, 9), ('6201', 12, 32, 10), ('6202', 15, 35, 11), ('6203', 17, 40, 12),
        ('6204', 20, 47, 14), ('6205', 25, 52, 15), ('6206', 30, 62, 16), ('6207', 35, 72, 17),
        ('6208', 40, 80, 18), ('6209', 45, 85, 19), ('6210', 50, 90, 20)]),
    '63': ('radial', [
        ('6300', 10, 35, 11), ('6301', 12, 37, 12), ('6302', 15, 42, 13), ('6303', 17, 47, 14),
        ('6304', 20, 52, 15), ('6305', 25, 62, 17), ('6306', 30, 72, 19), ('6307', 35, 80, 21),
        ('6308', 40, 90, 23), ('6310', 50, 110, 27)]),
    '511': ('thrust', [
        ('51100', 10, 24, 9), ('51101', 12, 26, 9), ('51102', 15, 28, 9), ('51103', 17, 30, 9),
        ('51104', 20, 35, 10), ('51105', 25, 42, 11), ('51106', 30, 47, 11), ('51107', 35, 52, 12),
        ('51108', 40, 60, 13), ('51110', 50, 70, 14)]),
    '512': ('thrust', [
        ('51200', 10, 26, 11), ('51201', 12, 28, 11), ('51202', 15, 32, 12), ('51203', 17, 35, 12),
        ('51204', 20, 40, 14), ('51205', 25, 47, 15), ('51206', 30, 52, 16), ('51208', 40, 68, 19)]),
}

# entries of the series dropdown: catalogue series, then free sizes of each kind
CUSTOM = {'custom_radial': 'radial', 'custom_thrust': 'thrust'}
SERIES_KEYS = list(SERIES) + list(CUSTOM)

GROOVE = 0.52      # raceway radius / ball diameter
DEPTH = 0.18       # raceway depth / ball diameter
BALL_GAP = 1.55    # ball pitch along the pitch circle / ball diameter (room for a cage)
MATCH_TOL = 0.03   # cm: an edge within 0.3 mm of a catalogue diameter selects that size
POPULAR = {'608', '625', '623', '688', 'MR105', '6000', '6200', '6202', '6204'}   # win ties with other sizes


def kind_of(series):
    return CUSTOM[series] if series in CUSTOM else SERIES[series][0]


def sizes(series):
    return [] if series in CUSTOM else SERIES[series][1]


def find_size(d, D, B, series):
    """Index of the size of a series with these dimensions (cm), or None."""
    for i, (_, sd, sD, sB) in enumerate(sizes(series)):
        if max(abs(sd / 10 - d), abs(sD / 10 - D), abs(sB / 10 - B)) < 1e-6:
            return i
    return None


def match_diameter(dia, current=None, kind=None, current_index=None):
    """(series, index, 'd' | 'D') of the catalogue size whose bore or outside diameter
    is nearest to an edge of diameter dia (cm), within MATCH_TOL; None if there is none.

    Ties (608, 627 and 6900 are all 22 mm outside) go to the current size, then
    the current series, then a POPULAR size, then the catalogue order. kind limits the search to
    radial or thrust bearings.
    """
    best = None
    for order, (series, (k, items)) in enumerate(SERIES.items()):
        if kind and k != kind:
            continue
        for i, (name, d, D, _) in enumerate(items):
            for which, size in (('d', d), ('D', D)):
                diff = abs(size / 10 - dia)
                if diff > MATCH_TOL:
                    continue
                rank = (round(diff, 6), (series, i) != (current, current_index), series != current,
                        name not in POPULAR, order)
                if best is None or rank < best[0]:
                    best = (rank, (series, i, which))
    return best[1] if best else None


def _pt(r, z):
    return (r, 0.0, z)


def _chain(points, arcs=None):
    """Closed chain through (r, z) points; arcs maps a point index to the mid point
    of an arc from that point to the next one."""
    arcs = arcs or {}
    segs = []
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        if i in arcs:
            segs.append(('arc', [_pt(*p), _pt(*arcs[i]), _pt(*q)]))
        else:
            segs.append(('line', [_pt(*p), _pt(*q)]))
    return segs


def _ring(r_in, r_out, z0, z1, c):
    """Rectangular section with chamfer c on all four corners."""
    return _chain([(r_in + c, z0), (r_out - c, z0), (r_out, z0 + c), (r_out, z1 - c),
                   (r_out - c, z1), (r_in + c, z1), (r_in, z1 - c), (r_in, z0 + c)])


class Bearing:
    """Deep groove ball bearing (kind 'radial') or single direction thrust ball bearing ('thrust').

    d, D, B — bore, outside diameter and width (height H of a thrust bearing), cm.
    """

    def __init__(self, kind, d, D, B, shields=False, name=''):
        if kind not in KINDS:
            raise GearError('bearing_kind')
        if d <= 0 or B <= 0:
            raise GearError('bearing_zero')
        if D <= d:
            raise GearError('bearing_outer_small')
        self.kind, self.d, self.D, self.B = kind, d, D, B
        self.shields = shields and kind == 'radial'
        self.name = name
        wall = D - d
        self.c = min(0.03 * wall, 0.1 * B)          # edge chamfer
        if kind == 'radial':
            self.Dw = min(0.3 * wall, 0.7 * B)
            self.rc = (d + D) / 4                    # ball centre radius
        else:
            self.Dw = min(0.62 * B, 0.42 * wall)
            self.rc = (d + D) / 4
            self.step = max(0.03 * wall, 0.002)      # washer bore / outside diameter offset
        self.zc = B / 2
        self.z = max(3, int(2 * math.pi * self.rc / (BALL_GAP * self.Dw)))
        if self.Dw < 0.01:
            raise GearError('bearing_too_thin')

    # ------------------------------------------------------------------ sections

    def simple(self):
        """Section of the bearing as one body (envelope)."""
        return _ring(self.d / 2, self.D / 2, 0.0, self.B, self.c)

    def _groove(self):
        """(half width at the shoulder, groove radius, ball centre to shoulder) of a raceway."""
        rg = GROOVE * self.Dw
        h = (0.5 - DEPTH) * self.Dw          # ball centre to shoulder
        return math.sqrt(rg * rg - h * h), rg, h

    def rings(self):
        """[(name key, section)] of the solid parts other than balls."""
        if self.kind == 'thrust':
            return self._washers()
        w, rg, h = self._groove()
        rc, zc, c, B = self.rc, self.zc, self.c, self.B
        r_in, r_out = self.d / 2, self.D / 2
        ri, ro = rc - h, rc + h              # shoulders of the inner and outer ring
        outer = _chain([(ro, 0.0), (r_out - c, 0.0), (r_out, c), (r_out, B - c), (r_out - c, B),
                        (ro, B), (ro, zc + w), (ro, zc - w)], {6: (rc + rg, zc)})
        inner = _chain([(r_in + c, 0.0), (ri, 0.0), (ri, zc - w), (ri, zc + w), (ri, B),
                        (r_in + c, B), (r_in, B - c), (r_in, c)], {2: (rc - rg, zc)})
        parts = [('part_outer_ring', outer), ('part_inner_ring', inner)]
        if self.shields:
            gap = 0.02 * self.Dw
            for z0, z1 in ((0.05 * B, 0.1 * B), (0.9 * B, 0.95 * B)):
                parts.append(('part_shield', _chain([(ri + gap, z0), (ro, z0), (ro, z1), (ri + gap, z1)])))
        return parts

    def _washers(self):
        w, rg, h = self._groove()
        rc, zc, c, H = self.rc, self.zc, self.c, self.B
        tw = zc - h                          # washer thickness

        def washer(r_in, r_out, flip):
            z = (lambda v: H - v) if flip else (lambda v: v)
            pts = [(r_in + c, 0.0), (r_out - c, 0.0), (r_out, c), (r_out, tw),
                   (rc + w, tw), (rc - w, tw), (r_in, tw), (r_in, c)]
            return _chain([(r, z(v)) for r, v in pts], {4: (rc, z(zc - rg))})

        return [('part_shaft_washer', washer(self.d / 2, self.D / 2 - self.step, False)),
                ('part_housing_washer', washer(self.d / 2 + self.step, self.D / 2, True))]

    def ball(self):
        """Section of one ball: a half disc on the line x = rc, which is its revolve axis."""
        r = self.Dw / 2
        top, bottom = _pt(self.rc, self.zc + r), _pt(self.rc, self.zc - r)
        return [('arc', [top, _pt(self.rc + r, self.zc), bottom]), ('line', [bottom, top])]

    def info(self):
        return dict(d=self.d, D=self.D, B=self.B, Dw=self.Dw, z=self.z, dp=2 * self.rc)


# ---------------------------------------------------------------------- placement

def _unit(v):
    n = math.sqrt(sum(x * x for x in v))
    if n < 1e-12:
        raise GearError('bearing_axis')
    return tuple(x / n for x in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def placement(center, normal, toward=None, flip=False, offset=0.0):
    """4x4 matrix putting the bearing face on a circular edge.

    The bearing axis is the edge normal, turned to the side of `toward` (a point
    of the hole or shaft surface at the edge) so the bearing goes into the hole
    or onto the shaft; flip reverses it, offset moves it along the axis.
    """
    z = _unit(normal)
    if toward is not None and _dot([t - c for t, c in zip(toward, center)], z) < 0:
        z = tuple(-v for v in z)
    if flip:
        z = tuple(-v for v in z)
    a = (1.0, 0.0, 0.0) if abs(z[0]) < 0.9 else (0.0, 1.0, 0.0)
    x = _unit([ai - _dot(a, z) * zi for ai, zi in zip(a, z)])
    y = _cross(z, x)
    o = [c + offset * zi for c, zi in zip(center, z)]
    return [[x[i], y[i], z[i], o[i]] for i in range(3)] + [[0, 0, 0, 1]]
