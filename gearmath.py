"""Gear geometry without Fusion dependencies.

All lengths are in one consistent unit (the add-in passes centimetres, Fusion's
internal unit); all angles are in radians. Geometry is returned as closed chains
of segments: ``(kind, points)`` where kind is ``'line'``, ``'arc'`` (start, mid,
end) or ``'spline'`` (fit points), and each segment starts where the previous
one ends.
"""
import math

HA = 1.0        # addendum coefficient
HF = 1.25       # dedendum coefficient
FLANK_POINTS = 10


class GearError(ValueError):
    pass


def inv(a):
    return math.tan(a) - a


def _flank(rb, ra, r_low, psi, alpha, n=None):
    """One tooth flank as polar points (rho, theta), bottom to tip.

    theta is the half angle from the tooth centre line, psi the half angle of
    the tooth thickness on the pitch circle. Below the base circle the flank is
    continued by a radial line down to r_low (returned separately).
    """
    def theta(rho):
        return psi + inv(alpha) - inv(math.acos(min(1.0, rb / rho)))

    n = n or FLANK_POINTS
    rho0 = max(rb, r_low)
    t0 = math.sqrt(max(0.0, (rho0 / rb) ** 2 - 1))
    t1 = math.sqrt((ra / rb) ** 2 - 1)
    pts = []
    for i in range(n):
        t = t0 + (t1 - t0) * i / (n - 1)
        rho = rb * math.sqrt(1 + t * t)
        pts.append((rho, theta(rho)))
    radial = (r_low, theta(rb)) if rb > r_low else None
    return radial, pts


def _check_flank(flank, tooth_angle, what):
    radial, pts = flank
    if pts[-1][1] <= 0.02 * tooth_angle:
        raise GearError(f'{what}: заострённый зуб — уменьшите угол или увеличьте число зубьев')
    bottom = radial[1] if radial else pts[0][1]
    if tooth_angle - 2 * bottom <= 0.02 * tooth_angle:
        raise GearError(f'{what}: зубья пересекаются у основания')


def _tooth_chain(flank, ra):
    """Tooth outline from the bottom of the right flank to the bottom of the left one."""
    radial, pts = flank
    right = [(rho, -th) for rho, th in pts]
    left = [(rho, th) for rho, th in reversed(pts)]
    segs = []
    if radial:
        segs.append(('line', [(radial[0], -radial[1]), right[0]]))
    segs.append(('spline', right))
    segs.append(('arc', [right[-1], (ra, 0.0), left[0]]))
    segs.append(('spline', left))
    if radial:
        segs.append(('line', [left[-1], (radial[0], radial[1])]))
    return segs


def _map(segs, fn):
    return [(kind, [fn(p) for p in pts]) for kind, pts in segs]


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translation(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]


def apply(m, p):
    return tuple(m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3] for i in range(3))


class CylindricalGear:
    """Spur, helical or herringbone gear; axis Z, face from z=0 to z=width.

    mn — normal module, beta — helix angle (0 for spur), hand — +1 right, -1 left,
    backlash — normal backlash of the pair (each gear is thinned by half of it).
    """

    def __init__(self, mn, z, beta, alpha_n, width, hand=1, backlash=0.0, bore=0.0):
        if mn <= 0 or width <= 0:
            raise GearError('Модуль и ширина должны быть больше нуля')
        if z < 4:
            raise GearError('Слишком мало зубьев (минимум 4)')
        if not 0 <= beta < math.radians(60):
            raise GearError('Угол наклона зуба должен быть от 0 до 60°')
        self.mn, self.z, self.beta, self.width, self.hand = mn, z, beta, width, hand
        self.mt = mn / math.cos(beta)
        self.alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
        self.r = self.mt * z / 2
        self.rb = self.r * math.cos(self.alpha_t)
        self.ra = self.r + HA * mn
        self.rf = self.r - HF * mn
        if self.rf <= 0:
            raise GearError('Окружность впадин меньше нуля')
        if bore and bore / 2 >= self.rf * 0.9:
            raise GearError('Отверстие слишком большое для этого колеса')
        self.bore = bore
        s = math.pi * self.mt / 2 - backlash / math.cos(beta) / 2
        self.flank = _flank(self.rb, self.ra, self.rf, s / (2 * self.r), self.alpha_t)
        _check_flank(self.flank, 2 * math.pi / z, 'Колесо')

    def twist(self, length):
        """Rotation of the tooth over an axial length (signed by hand)."""
        return self.hand * length * math.tan(self.beta) / self.r

    def outline(self):
        """Closed outline of the whole gear in the XY plane (3D points, z=0)."""
        tooth = _tooth_chain(self.flank, self.ra)
        radial, pts = self.flank
        th_b = radial[1] if radial else pts[0][1]
        pitch = 2 * math.pi / self.z
        segs = []
        for i in range(self.z):
            c = i * pitch

            def xy(p, c=c):
                return (p[0] * math.cos(c + p[1]), p[0] * math.sin(c + p[1]), 0.0)

            segs += _map(tooth, xy)
            segs.append(('arc', [xy((self.rf, th_b)), xy((self.rf, pitch / 2)),
                                 xy((self.rf, pitch - th_b))]))
        return segs

    def center_distance(self, other):
        return self.r + other.r

    def mate_transform(self, other):
        """Placement of the mating gear (built at the origin) so that it meshes with self."""
        a = self.center_distance(other)
        return matmul(translation(a, 0, 0), rot_z(math.pi + math.pi / other.z))

    def info(self):
        return {'mt': self.mt, 'd': 2 * self.r, 'da': 2 * self.ra, 'df': 2 * self.rf,
                'db': 2 * self.rb, 'alpha_t': self.alpha_t}


def mesh_phase(gi, phi_i, theta, gj):
    """Rotation of gear gj placed in direction theta from gear gi so that the two mesh.

    phi_i — rotation of gi (a tooth of an unrotated gear points along +X).
    A tooth of gi lying u pitches clockwise of the contact point must face a
    gap of gj lying u pitches counter-clockwise of it on gj.
    """
    u = ((theta - phi_i) * gi.z / (2 * math.pi)) % 1.0
    if u > 0.5:
        u -= 1.0
    return theta + math.pi + 2 * math.pi * u / gj.z - math.pi / gj.z


def placement(x, y, phi):
    """Transform of a gear built at the origin: turn by phi, then move to (x, y)."""
    return matmul(translation(x, y, 0), rot_z(phi))


class BevelGear:
    """Bevel gear with straight, skew (tangential) or spiral teeth.

    Built with the axis along Z, pitch circle (heel) in the plane z=0 and the
    pitch-cone apex on +Z. m — outer transverse module, beta — spiral angle at
    the middle of the face, tooth_line — 'straight' | 'skew' | 'spiral'.
    Profiles use Tredgold's back-cone approximation.
    """

    def __init__(self, m, z, z_mate, sigma, alpha_n, face, tooth_line='straight', beta=0.0,
                 hand=1, backlash=0.0, back=0.0, bore=0.0, sections=7):
        if m <= 0 or face <= 0:
            raise GearError('Модуль и ширина венца должны быть больше нуля')
        if z < 4 or z_mate < 4:
            raise GearError('Слишком мало зубьев (минимум 4)')
        if not math.radians(10) <= sigma <= math.radians(170):
            raise GearError('Межосевой угол должен быть от 10 до 170°')
        if tooth_line not in ('straight', 'skew', 'spiral'):
            raise GearError('Неизвестный тип линии зуба')
        if tooth_line == 'straight':
            beta = 0.0
        elif not math.radians(1) <= beta < math.radians(60):
            raise GearError('Угол наклона зуба должен быть от 1 до 60°')
        self.m, self.z, self.z_mate, self.sigma = m, z, z_mate, sigma
        self.alpha_n, self.face, self.tooth_line = alpha_n, face, tooth_line
        self.beta, self.hand, self.backlash, self.back = beta, hand, backlash, back
        self.sections = 2 if tooth_line == 'straight' else max(3, int(sections))

        self.delta = math.atan2(math.sin(sigma), z_mate / z + math.cos(sigma))
        if not 0 < self.delta < math.radians(89):
            raise GearError('Угол делительного конуса ≥ 89° (плоское/внутреннее колесо не поддерживается)')
        self.r = m * z / 2
        self.Re = self.r / math.sin(self.delta)
        self.Ri = self.Re - face
        self.Rm = self.Re - face / 2
        if self.Ri < 0.4 * self.Re:
            raise GearError('Ширина венца больше 0.6 конусного расстояния')
        if tooth_line == 'skew' and self.Rm * math.sin(beta) >= self.Ri * 0.99:
            raise GearError('Для косого зуба угол слишком велик при такой ширине венца')
        self.alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
        cd, sd = math.cos(self.delta), math.sin(self.delta)
        self.apex_z = self.Re * cd
        self.g = (sd, 0.0, -cd)   # pitch-cone generator, apex -> heel
        self.b = (cd, 0.0, sd)    # back-cone direction, outward
        self.ha, self.hf = HA * m, HF * m
        self.rv = self.r / cd     # virtual (back-cone) spur gear
        self.zv = z / cd
        self.ra_v = self.rv + self.ha
        self.r_low = self.rv - self.hf - 0.3 * m   # tooth bodies dip into the blank
        rbv = self.rv * math.cos(self.alpha_t)
        s = math.pi * m / 2 - backlash / 2
        self.flank = _flank(rbv, self.ra_v, self.r_low, s / (2 * self.rv), self.alpha_t)
        _check_flank(self.flank, 2 * math.pi / self.zv, 'Коническое колесо')
        self.bore = bore
        if bore and bore / 2 >= self.blank_profile()[1][0] * 0.9:
            raise GearError('Отверстие слишком большое для этого колеса')

    # --- tooth line -------------------------------------------------------
    def phi(self, R):
        """Rotation about the axis of the tooth section at cone distance R."""
        if self.tooth_line == 'straight':
            return 0.0
        if self.tooth_line == 'skew':
            e = self.Rm * math.sin(self.beta)
            crown = math.acos(e / R) - math.acos(e / self.Rm)
        else:
            crown = math.tan(self.beta) * math.log(R / self.Rm)
        return self.hand * crown / math.sin(self.delta)

    def section_distances(self):
        n = self.sections
        return [self.Ri + (self.Re - self.Ri) * i / (n - 1) for i in range(n)]

    def _point(self, R, rho, ang):
        """Map polar point of the virtual gear tooth to 3D at cone distance R."""
        k = R / self.Re
        u = rho * math.sin(ang)
        v = rho * math.cos(ang) - self.rv
        x = R * self.g[0] + k * v * self.b[0]
        z = self.apex_z + R * self.g[2] + k * v * self.b[2]
        y = k * u
        f = self.phi(R)
        c, s = math.cos(f), math.sin(f)
        return (x * c - y * s, x * s + y * c, z)

    def section(self, R):
        """Closed tooth section (3D points) at cone distance R."""
        radial, pts = self.flank
        th_b = radial[1] if radial else pts[0][1]
        segs = _tooth_chain(self.flank, self.ra_v)
        segs.append(('arc', [(self.r_low, th_b), (self.r_low, 0.0), (self.r_low, -th_b)]))
        return _map(segs, lambda p: self._point(R, p[0], p[1]))

    def section_plane(self, R):
        """Three non-collinear points of the section plane."""
        return (self._point(R, self.rv, 0.0), self._point(R, self.ra_v, 0.0),
                self._point(R, self.rv, 0.2))

    # --- blank ------------------------------------------------------------
    def blank_profile(self):
        """Half section of the blank in the XZ plane: list of (x, z), closed."""
        def root(R):
            k = R / self.Re
            return (R * self.g[0] - k * self.hf * self.b[0],
                    self.apex_z + R * self.g[2] - k * self.hf * self.b[2])
        heel, toe = root(self.Re), root(self.Ri)
        z_bottom = heel[1] - self.back
        return [heel, toe, (0.0, toe[1]), (0.0, z_bottom), (heel[0], z_bottom)]

    def mate(self, bore=None):
        return BevelGear(self.m, self.z_mate, self.z, self.sigma, self.alpha_n, self.face,
                         self.tooth_line, self.beta, -self.hand, self.backlash, self.back,
                         self.bore if bore is None else bore, self.sections)

    def mate_transform(self, other):
        """Placement of the mating gear (built in its own frame) so the apexes coincide."""
        return matmul(matmul(matmul(translation(0, 0, self.apex_z), rot_y(-self.sigma)),
                             rot_z(math.pi + math.pi / other.z)),
                      translation(0, 0, -other.apex_z))

    def info(self):
        return {'delta': self.delta, 'd': 2 * self.r,
                'da': 2 * (self.r + self.ha * math.cos(self.delta)),
                'Re': self.Re, 'zv': self.zv, 'face_max': self.Re / 3}
