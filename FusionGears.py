"""FusionGears — herringbone/helical and bevel (straight, skew, spiral, Gleason) gear generator, ball bearings."""
import adsk.core
import adsk.fusion
import importlib
import math
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gearmath  # noqa: E402
import bearingmath  # noqa: E402
import presets  # noqa: E402
import gearcheck  # noqa: E402
import strings  # noqa: E402
importlib.reload(strings)
importlib.reload(gearmath)
importlib.reload(bearingmath)
importlib.reload(presets)
importlib.reload(gearcheck)
from gearmath import GearError  # noqa: E402
from strings import t  # noqa: E402

PANEL_ID = 'SolidCreatePanel'
INSPECT_PANEL_ID = 'InspectPanel'
CYL_ID = 'FusionGears_Cylindrical'
BEVEL_ID = 'FusionGears_Bevel'
CHECK_ID = 'FusionGears_Check'
BEARING_ID = 'FusionGears_Bearing'

_app = None
_ui = None
_handlers = []


# --------------------------------------------------------------------------- geometry helpers

def _p(xyz):
    return adsk.core.Point3D.create(xyz[0], xyz[1], xyz[2])


def _nearest(curve, target):
    a, b = curve.startSketchPoint, curve.endSketchPoint
    return a if a.geometry.distanceTo(target) <= b.geometry.distanceTo(target) else b


def _draw_closed(sketch, segs, to_sketch):
    """Draw a closed chain of segments; consecutive segments share sketch points."""
    curves = sketch.sketchCurves
    first = last = None
    for idx, (kind, pts) in enumerate(segs):
        sk = [to_sketch(p) for p in pts]
        start = last if last is not None else sk[0]
        end = first if idx == len(segs) - 1 else sk[-1]
        if kind == 'line':
            c = curves.sketchLines.addByTwoPoints(start, end)
        elif kind == 'arc':
            c = curves.sketchArcs.addByThreePoints(start, sk[1], end)
        else:
            col = adsk.core.ObjectCollection.create()
            col.add(start)
            for q in sk[1:-1]:
                col.add(q)
            col.add(end)
            c = curves.sketchFittedSplines.add(col)
        if first is None:
            first = _nearest(c, sk[0])
        last = _nearest(c, sk[-1])


def _model_to_sketch(sketch):
    def f(xyz):
        q = sketch.modelToSketchSpace(_p(xyz))
        return adsk.core.Point3D.create(q.x, q.y, 0)
    return f


def _largest_profile(sketch):
    best, area = None, -1.0
    for prof in sketch.profiles:
        a = prof.areaProperties(adsk.fusion.CalculationAccuracy.LowCalculationAccuracy).area
        if a > area:
            best, area = prof, a
    if best is None:
        raise GearError('no_profile')
    return best


def _collection(items):
    col = adsk.core.ObjectCollection.create()
    for it in items:
        col.add(it)
    return col


def _matrix(m):
    mat = adsk.core.Matrix3D.create()
    for i in range(4):
        for j in range(4):
            mat.setCell(i, j, m[i][j])
    return mat


def _target_component(design, name, m=None):
    """(component, occurrence) — a new component when the design allows it, otherwise (root, None).

    m places the new occurrence (identity by default).
    """
    root = design.rootComponent
    try:
        occ = root.occurrences.addNewComponent(_matrix(m) if m else adsk.core.Matrix3D.create())
        occ.component.name = name
        return occ.component, occ
    except Exception:
        return root, None


def _combine(target, tools):
    if not tools:
        return
    comb = target.parentComponent.features.combineFeatures
    inp = comb.createInput(target, _collection(tools))
    inp.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    comb.add(inp)


def _cut_bore(comp, body, diameter, length):
    if diameter <= 0:
        return
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = t('sk_bore')
    sk.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), diameter / 2)
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
    inp.setSymmetricExtent(adsk.core.ValueInput.createByReal(length), True)
    inp.participantBodies = [body]
    ext.add(inp)


def _move(comp, body, m):
    if all(abs(m[i][j] - (i == j)) < 1e-12 for i in range(4) for j in range(4)):
        return  # Fusion rejects an identity move
    mv = comp.features.moveFeatures
    inp = mv.createInput2(_collection([body]))
    inp.defineAsFreeMove(_matrix(m))
    mv.add(inp)


def _overlap(pairs):
    tbm = adsk.fusion.TemporaryBRepManager.get()
    a, b = [tbm.copy(body.createForAssemblyContext(occ)) for occ, body in pairs]
    tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return a.volume


def _axis_circle(comp, m, name, radius=0.3):
    """Sketch circle on the gear axis whose normal is m·Z.

    The joint axis follows the circle normal. A plane through three points in a
    fixed order keeps that direction through recomputes; a body edge does not,
    and a flipped axis silently reverses the motion link.
    """
    helper = comp.sketches.add(comp.xYConstructionPlane)
    helper.name = t('sk_axis_points', name=name)
    pts = [gearmath.apply(m, q) for q in ((0, 0, 0), (radius, 0, 0), (0, radius, 0))]
    sp = [helper.sketchPoints.add(_p(q)) for q in pts]
    pin = comp.constructionPlanes.createInput()
    pin.setByThreePoints(sp[0], sp[1], sp[2])
    plane = comp.constructionPlanes.add(pin)
    plane.name = t('pl_axis', name=name)
    plane.isLightBulbOn = False
    sk = comp.sketches.add(plane)
    sk.name = t('sk_axis', name=name)
    centre = _model_to_sketch(sk)(pts[0])
    circle = sk.sketchCurves.sketchCircles.addByCenterRadius(centre, radius)
    helper.isVisible = False
    sk.isVisible = False
    return circle


def add_frame(design, name=None):
    """Grounded empty component the gear joints hang on."""
    frame = design.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    frame.component.name = name or t('name_frame')
    frame.isGrounded = True
    return frame


def add_joint(design, frame, occ, m=None):
    """Revolute as-built joint of a gear occurrence to the frame, about the gear's axis m·Z."""
    root = design.rootComponent
    occ.isGroundToParent = False  # Fusion grounds the first component of a design
    occ.isGrounded = False
    circle = _axis_circle(occ.component, m or gearmath.translation(0, 0, 0), occ.component.name)
    geo = adsk.fusion.JointGeometry.createByCurve(circle.createForAssemblyContext(occ),
                                                   adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
    inp = root.asBuiltJoints.createInput(occ, frame, geo)
    inp.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    joint = root.asBuiltJoints.add(inp)
    joint.name = t('name_joint', name=occ.component.name)
    return joint


def add_link(design, joints, z1, z2, pairs):
    """Motion link z1:z2 between two meshing gears' joints.

    The direction is chosen by turning gear 1 a quarter of its pitch and
    checking that the teeth of pairs = [(occ, body), (occ, body)] do not collide.
    """
    root = design.rootComponent
    inp = root.motionLinks.createInput(joints[0], joints[1])
    inp.valueOne = adsk.core.ValueInput.createByString('360 deg')
    inp.valueTwo = adsk.core.ValueInput.createByString(f'{360 * z1 / z2:.6f} deg')
    inp.isReversed = True
    link = root.motionLinks.add(inp)
    link.name = t('name_link', z1=z1, z2=z2)

    motion = joints[0].jointMotion
    start = motion.rotationValue
    try:
        motion.rotationValue = start + math.pi / (2 * z1)  # a quarter of the pitch
        if _overlap(pairs) > 1e-3 * min(b.physicalProperties.volume for _, b in pairs):
            link.isReversed = False
    finally:
        motion.rotationValue = start
    return link


def add_drive(design, pairs, z1, z2, transforms):
    """Revolute joints for both gears to a new grounded frame and a motion link z1:z2.

    pairs — [(occurrence, body), (occurrence, body)] of the meshed gears;
    transforms — where each gear's own frame was moved to (None for gear 1, built in place).
    """
    frame = add_frame(design)
    joints = [add_joint(design, frame, occ, m) for (occ, _), m in zip(pairs, transforms)]
    return joints, add_link(design, joints, z1, z2, pairs)


# --------------------------------------------------------------------------- gear train check

CHECK_TURN = math.radians(3)
MESH_GAP = 0.05  # cm: bodies closer than this are taken as meshing


def _revolute_joints(design):
    """[(joint, moving occurrence)] for every revolute joint and as-built joint of the design."""
    out = []
    revolute = adsk.fusion.JointTypes.RevoluteJointType
    for comp in design.allComponents:
        for coll in (comp.joints, comp.asBuiltJoints):
            for j in coll:
                try:
                    if j.jointMotion.jointType != revolute:
                        continue
                    occ = j.occurrenceOne
                    if occ is None or occ.isGrounded:
                        occ = j.occurrenceTwo
                    if occ is not None:
                        out.append((j, occ))
                except Exception:
                    continue
    return out


def _bodies(occ):
    return [b for b in occ.bRepBodies if b.isSolid]


def _occ_overlap(occ_a, occ_b, tol):
    tbm = adsk.fusion.TemporaryBRepManager.get()
    for a in _bodies(occ_a):
        for b in _bodies(occ_b):
            ta, tb = tbm.copy(a), tbm.copy(b)
            tbm.booleanOperation(ta, tb, adsk.fusion.BooleanTypes.IntersectionBooleanType)
            if ta and ta.volume > tol:
                return True
    return False


def _occ_gap(occ_a, occ_b):
    gap = math.inf
    measure = _app.measureManager
    for a in _bodies(occ_a):
        for b in _bodies(occ_b):
            gap = min(gap, measure.measureMinimumDistance(a, b).value)
    return gap


def check_system(design):
    """Check every gear train of the design. Returns (problems, summary).

    Logical: each motion link's signed ratio is measured by turning one of its
    joints with all other links suppressed; chains of links that disagree on a
    joint's speed or direction are reported. Physical: gears that intersect,
    gears in mesh without a link, and links that drive meshing teeth into each other.
    """
    rotors = _revolute_joints(design)
    by_token = {j.entityToken: (j, occ) for j, occ in rotors}
    label = lambda tok: f'{by_token[tok][1].name} ({by_token[tok][0].name})'

    links = {}
    for j, _ in rotors:
        for link in j.motionLinks:
            links.setdefault(link.entityToken, [link, []])[1].append(j.entityToken)
    links = {tok: (l, js) for tok, (l, js) in links.items() if len(set(js)) == 2}

    problems = []
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    for link, _ in links.values():
        if link.healthState != healthy:
            problems.append(t('chk_link_unhealthy', link=link.name, msg=link.errorOrWarningMessage or t('chk_fusion_error')))

    tol = 1e-3 * min((b.physicalProperties.volume for _, o in rotors for b in _bodies(o)), default=1.0)
    start = {}
    for j, _ in rotors:
        try:
            start[j.entityToken] = j.jointMotion.rotationValue
        except Exception:
            pass
    suppressed = {tok: l.isSuppressed for tok, (l, _) in links.items()}
    edges, linked = [], set()
    try:
        for l, _ in links.values():
            l.isSuppressed = True
        for tok, (link, (ta, tb)) in links.items():
            if suppressed[tok]:
                continue
            (ja, oa), (jb, ob) = by_token[ta], by_token[tb]
            link.isSuppressed = False
            a0, b0 = ja.jointMotion.rotationValue, jb.jointMotion.rotationValue
            meshing = oa != ob and _occ_gap(oa, ob) < MESH_GAP
            try:
                ja.jointMotion.rotationValue = a0 + CHECK_TURN
                k = (jb.jointMotion.rotationValue - b0) / CHECK_TURN
                bad_turn = meshing and _occ_overlap(oa, ob, tol)
                if meshing and not bad_turn:
                    ja.jointMotion.rotationValue = a0 - CHECK_TURN
                    bad_turn = _occ_overlap(oa, ob, tol)
            finally:
                ja.jointMotion.rotationValue = a0
                link.isSuppressed = True
            linked.add(frozenset((oa.entityToken, ob.entityToken)))
            if abs(k) < 1e-9:
                problems.append(t('chk_no_rotation', link=link.name))
                continue
            if bad_turn:
                problems.append(t('chk_clash', link=link.name, a=oa.name, b=ob.name))
            edges.append((ta, tb, k, link.name))
    finally:
        for tok, (l, _) in links.items():
            l.isSuppressed = suppressed[tok]
        for j, _ in rotors:
            try:
                j.jointMotion.rotationValue = start[j.entityToken]
            except Exception:
                pass

    problems += [gearcheck.describe(c, label, t) for c in gearcheck.find_conflicts(edges)]

    occs = list({occ.entityToken: occ for _, occ in rotors}.values())
    pairs = [(oa, ob) for i, oa in enumerate(occs) for ob in occs[i + 1:]]
    clashing = set()
    for oa, ob in pairs:
        if _occ_overlap(oa, ob, tol):
            problems.append(t('chk_overlap', a=oa.name, b=ob.name))
            clashing |= {oa.entityToken, ob.entityToken}
    for oa, ob in pairs:
        # a gear that already clashes would only add noise here
        if (oa.entityToken in clashing or ob.entityToken in clashing
                or frozenset((oa.entityToken, ob.entityToken)) in linked):
            continue
        if _occ_gap(oa, ob) < MESH_GAP:
            problems.append(t('chk_mesh_no_link', a=oa.name, b=ob.name))

    summary = t('chk_summary', gears=len(occs), links=len(links))
    return problems, summary


def _report_check(design, only_problems=False):
    problems, summary = check_system(design)
    if problems:
        _ui.messageBox(t('chk_found') + '\n\n' +
                       '\n'.join('• ' + p for p in problems) + '\n\n' + summary)
    elif not only_problems:
        _ui.messageBox(t('chk_none') + '\n\n' + summary)
    return problems


def _timeline_count(design):
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        return None
    return design.timeline.count


def _group_timeline(design, start, name):
    if start is None:
        return
    try:
        tl = design.timeline
        if tl.count - 1 > start:
            tl.timelineGroups.add(start, tl.count - 1).name = name
    except Exception:
        pass


# --------------------------------------------------------------------------- builders

def build_cylindrical(comp, gear, kind, name):
    """kind: 0 herringbone, 1 helical, 2 spur. Returns the gear body."""
    feats = comp.features
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = t('sk_profile', name=name)
    sk.isComputeDeferred = True
    _draw_closed(sk, gear.outline(), _p)
    sk.isComputeDeferred = False
    prof = _largest_profile(sk)
    new_body = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

    if kind == 2:
        inp = feats.extrudeFeatures.createInput(prof, new_body)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(gear.width))
        body = feats.extrudeFeatures.add(inp).bodies.item(0)
    else:
        length = gear.width / 2 if kind == 0 else gear.width
        path_sk = comp.sketches.add(comp.xYConstructionPlane)
        path_sk.name = t('sk_path', name=name)
        line = path_sk.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(0, 0, length))
        inp = feats.sweepFeatures.createInput(prof, feats.createPath(line, False), new_body)
        inp.twistAngle = adsk.core.ValueInput.createByReal(gear.twist(length))
        body = feats.sweepFeatures.add(inp).bodies.item(0)
        if kind == 0:
            pin = comp.constructionPlanes.createInput()
            pin.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(length))
            plane = comp.constructionPlanes.add(pin)
            plane.name = t('pl_middle', name=name)
            plane.isLightBulbOn = False
            mir = feats.mirrorFeatures.add(feats.mirrorFeatures.createInput(_collection([body]), plane))
            _combine(body, [mir.bodies.item(0)])

    body.name = name
    _cut_bore(comp, body, gear.bore, gear.width * 4)
    return body


def build_bevel(comp, gear, name):
    feats = comp.features
    planes = comp.constructionPlanes

    # blank: revolve the root-cone half section around Z
    bsk = comp.sketches.add(comp.xZConstructionPlane)
    bsk.name = t('sk_blank', name=name)
    pts = [(x, 0.0, zz) for x, zz in gear.blank_profile()]
    _draw_closed(bsk, [('line', [pts[i], pts[(i + 1) % len(pts)]]) for i in range(len(pts))],
                 _model_to_sketch(bsk))
    rin = feats.revolveFeatures.createInput(_largest_profile(bsk), comp.zConstructionAxis,
                                            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    rin.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    blank = feats.revolveFeatures.add(rin).bodies.item(0)
    blank.name = name

    # one tooth: loft through sections on planes normal to the pitch-cone generator
    helper = comp.sketches.add(comp.xYConstructionPlane)
    helper.name = t('sk_section_points', name=name)
    loft_in = feats.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    for i, R in enumerate(gear.section_distances()):
        sp = [helper.sketchPoints.add(_p(q)) for q in gear.section_plane(R)]
        pin = planes.createInput()
        pin.setByThreePoints(sp[0], sp[1], sp[2])
        plane = planes.add(pin)
        plane.isLightBulbOn = False
        sk = comp.sketches.add(plane)
        sk.name = t('sk_section', name=name, i=i + 1)
        sk.isComputeDeferred = True
        _draw_closed(sk, gear.section(R), _model_to_sketch(sk))
        sk.isComputeDeferred = False
        loft_in.loftSections.add(_largest_profile(sk))
    helper.isVisible = False
    loft_in.isSolid = True
    tooth = feats.loftFeatures.add(loft_in).bodies.item(0)

    pat_in = feats.circularPatternFeatures.createInput(_collection([tooth]), comp.zConstructionAxis)
    pat_in.quantity = adsk.core.ValueInput.createByReal(gear.z)
    pat_in.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    pattern = feats.circularPatternFeatures.add(pat_in)
    teeth = [tooth] + [b for b in pattern.bodies if b != tooth]
    _combine(blank, teeth)
    _cut_bore(comp, blank, gear.bore, gear.Re * 4)
    return blank


def _run_build(builder, gears, transform, drive=False):
    """Build gear (and optional mate) each in its own component/timeline group.

    drive — for a pair, also add revolute joints and a motion link.
    """
    design = adsk.fusion.Design.cast(_app.activeProduct)
    if not design:
        raise GearError('open_design')
    built = []
    for idx, (gear, name) in enumerate(gears):
        start = _timeline_count(design)
        comp, occ = _target_component(design, name)
        body = builder(comp, gear, name)
        if idx > 0:
            _move(comp, body, transform)
        _group_timeline(design, start, name)
        built.append((occ, body))
    if drive and len(built) == 2:
        if any(occ is None for occ, _ in built):
            _ui.messageBox(t('msg_part_no_joints'))
            return
        add_drive(design, built, gears[0][0].z, gears[1][0].z, [None, transform])
        _report_check(design, only_problems=True)


# --------------------------------------------------------------------------- command inputs

CYL_KINDS = ['herringbone', 'helical', 'spur']   # index = kind passed to build_cylindrical
HANDS = ['right', 'left']
BEARING_DETAILS = ['full', 'simple']
DROPDOWNS = {'kind': (CYL_KINDS, 'kind_'), 'line': (list(gearmath.TOOTH_LINES), 'line_'),
             'hand': (HANDS, 'hand_'), 'series': (bearingmath.SERIES_KEYS, 'series_'),
             'detail': (BEARING_DETAILS, 'detail_')}


def _value(inputs, iid):
    return inputs.itemById(iid).value


def _choice(inputs, iid):
    """Key of the selected item of a dropdown from DROPDOWNS."""
    return DROPDOWNS[iid][0][inputs.itemById(iid).selectedItem.index]


def _hand(inputs):
    return 1 if _choice(inputs, 'hand') == 'right' else -1


def _add_dropdown(inputs, iid, label, items):
    dd = inputs.addDropDownCommandInput(iid, label, adsk.core.DropDownStyles.TextListDropDownStyle)
    for i, text in enumerate(items):
        dd.listItems.add(text, i == 0)
    return dd


def _add_choice(inputs, iid, label_key):
    keys, prefix = DROPDOWNS[iid]
    _add_dropdown(inputs, iid, t(label_key), [t(prefix + k) for k in keys])


def _add_common(inputs, module_key):
    inputs.addValueInput('module', t(module_key), 'mm', adsk.core.ValueInput.createByString('2 mm'))
    inputs.addIntegerSpinnerCommandInput('teeth', t('lbl_teeth'), 4, 500, 1, 20)


def _add_presets(inputs, items):
    _add_dropdown(inputs, 'preset', t('lbl_preset'),
                  [t('preset_custom')] + [strings.pick(names) for names, _ in items])


def apply_preset(inputs, values):
    """Fill dialog inputs from a preset (lengths in mm, angles in degrees, dropdowns by key)."""
    for key, val in values.items():
        item = inputs.itemById(key)
        if item is None:
            continue
        if key in DROPDOWNS:
            adsk.core.DropDownCommandInput.cast(item).listItems.item(DROPDOWNS[key][0].index(val)).isSelected = True
        elif key in presets.LENGTH_KEYS:
            item.expression = f'{val} mm'
        elif key in presets.ANGLE_KEYS:
            item.expression = f'{val} deg'
        else:
            item.value = val


def _mm(v):
    return f'{v * 10:.3f} {t("unit_mm")}'


def _deg(a):
    return f'{math.degrees(a):.3f}°'


def cyl_from_inputs(inputs):
    kind = CYL_KINDS.index(_choice(inputs, 'kind'))
    beta = 0.0 if CYL_KINDS[kind] == 'spur' else _value(inputs, 'beta')
    args = dict(mn=_value(inputs, 'module'), beta=beta, alpha_n=_value(inputs, 'alpha'),
                width=_value(inputs, 'width'), backlash=_value(inputs, 'backlash'),
                bore=_value(inputs, 'bore'))
    hand = _hand(inputs)
    g1 = gearmath.CylindricalGear(z=inputs.itemById('teeth').value, hand=hand, **args)
    g2 = None
    if inputs.itemById('pair').value:
        args['bore'] = _value(inputs, 'bore2')
        g2 = gearmath.CylindricalGear(z=inputs.itemById('teeth2').value, hand=-hand, **args)
    return kind, g1, g2


def bevel_from_inputs(inputs):
    g1 = gearmath.BevelGear(
        m=_value(inputs, 'module'), z=inputs.itemById('teeth').value,
        z_mate=inputs.itemById('teeth2').value, sigma=_value(inputs, 'sigma'),
        alpha_n=_value(inputs, 'alpha'), face=_value(inputs, 'width'), tooth_line=_choice(inputs, 'line'),
        beta=_value(inputs, 'beta'), hand=_hand(inputs), backlash=_value(inputs, 'backlash'),
        back=_value(inputs, 'back'), bore=_value(inputs, 'bore'),
        sections=inputs.itemById('sections').value, cutter_radius=_value(inputs, 'cutter'))
    g2 = None
    if inputs.itemById('pair').value:
        g2 = g1.mate(_value(inputs, 'bore2'))
    return g1, g2


def cyl_info(kind, g1, g2):
    i = g1.info()
    lines = [t('info_d', v=_mm(i['d'])), t('info_da', v=_mm(i['da'])), t('info_df', v=_mm(i['df']))]
    if CYL_KINDS[kind] != 'spur':
        lines.append(t('info_mt', v=_mm(i['mt'])))
    if g2:
        lines.append(t('info_gear2_cyl', d=_mm(2 * g2.r), da=_mm(2 * g2.ra)))
        lines.append(t('info_a', v=_mm(g1.center_distance(g2))))
    return '<br>'.join(lines)


def bevel_info(g1, g2):
    i = g1.info()
    lines = [t('info_delta', v=_deg(i['delta'])), t('info_de', v=_mm(i['d'])), t('info_dae', v=_mm(i['da'])),
             t('info_Re', v=_mm(i['Re'])), t('info_zv', v=f'{i["zv"]:.1f}')]
    if g1.tooth_line != 'straight':
        lines.append(t('info_beta_range', toe=_deg(i['beta_toe']), mid=_deg(g1.beta), heel=_deg(i['beta_heel'])))
    if g1.tooth_line == 'gleason':
        lines.append(t('info_rc', v=_mm(i['rc'])))
    if g1.face > i['face_max'] + 1e-9:
        lines.append('<b>' + t('info_face_warn', v=_mm(i['face_max'])) + '</b>')
    if g2:
        lines.append(t('info_gear2_bevel', delta=_deg(g2.delta), de=_mm(2 * g2.r)))
    return '<br>'.join(lines)


def _set_info(inputs, text):
    inputs.itemById('info').formattedText = text


# --------------------------------------------------------------------------- event handlers

class _Created(adsk.core.CommandCreatedEventHandler):
    """changed(inputs, changed_input) reacts to an edited input; preview builds while the dialog is open."""

    def __init__(self, setup, read, info, build, changed, preview=False, fail_key='msg_build_failed'):
        super().__init__()
        self.setup, self.read, self.info, self.build = setup, read, info, build
        self.changed, self.preview, self.fail_key = changed, preview, fail_key

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            self.setup(cmd.commandInputs)
            events = [(cmd.execute, _Execute), (cmd.inputChanged, _Changed), (cmd.validateInputs, _Validate)]
            if self.preview:
                events.append((cmd.executePreview, _Preview))
            for event, cls in events:
                h = cls(self)
                event.add(h)
                _handlers.append(h)
            self.refresh(cmd.commandInputs)
        except Exception:
            _ui.messageBox(t('msg_error') + '\n' + traceback.format_exc())

    def refresh(self, inputs):
        try:
            _set_info(inputs, self.info(*self.read(inputs)))
            return True
        except GearError as e:
            _set_info(inputs, f'<b>{strings.error(e)}</b>')
            return False


class _Changed(adsk.core.InputChangedEventHandler):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def notify(self, args):
        try:
            inputs = args.inputs.command.commandInputs
            self.owner.changed(inputs, args.input)
            self.owner.refresh(inputs)
        except Exception:
            pass


def _gear_changed(preset_list):
    def changed(inputs, changed_input):
        if changed_input.id == 'preset':
            index = changed_input.selectedItem.index
            if index > 0:   # item 0 keeps the current values
                apply_preset(inputs, preset_list[index - 1][1])
        _visibility(inputs)
    return changed


class _Validate(adsk.core.ValidateInputsEventHandler):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def notify(self, args):
        try:
            args.areInputsValid = self.owner.refresh(args.inputs.command.commandInputs)
        except Exception:
            args.areInputsValid = False


class _Execute(adsk.core.CommandEventHandler):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def notify(self, args):
        try:
            self.owner.build(args.command.commandInputs)
        except GearError as e:
            _ui.messageBox(strings.error(e))
        except Exception:
            _ui.messageBox(t(self.owner.fail_key) + '\n' + traceback.format_exc())


class _Preview(adsk.core.CommandEventHandler):
    """Builds into the preview; Fusion rolls it back and runs execute on OK."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def notify(self, args):
        try:
            self.owner.build(args.command.commandInputs)
        except Exception:
            pass   # the dialog's calculation text already explains bad parameters


def _visibility(inputs):
    pair = inputs.itemById('pair').value
    inputs.itemById('bore2').isVisible = pair
    inputs.itemById('drive').isVisible = pair
    if inputs.itemById('kind'):
        inputs.itemById('teeth2').isVisible = pair
        straight = _choice(inputs, 'kind') == 'spur'
    else:
        line = _choice(inputs, 'line')
        straight = line == 'straight'
        inputs.itemById('sections').isVisible = not straight
        inputs.itemById('cutter').isVisible = line == 'gleason'
    inputs.itemById('beta').isVisible = not straight
    inputs.itemById('hand').isVisible = not straight


def cyl_setup(inputs):
    _add_presets(inputs, presets.CYLINDRICAL)
    _add_choice(inputs, 'kind', 'lbl_kind')
    _add_common(inputs, 'lbl_module_normal')
    inputs.addValueInput('beta', t('lbl_beta'), 'deg', adsk.core.ValueInput.createByString('30 deg'))
    _add_choice(inputs, 'hand', 'lbl_hand')
    inputs.addValueInput('alpha', t('lbl_alpha'), 'deg', adsk.core.ValueInput.createByString('20 deg'))
    inputs.addValueInput('width', t('lbl_width'), 'mm', adsk.core.ValueInput.createByString('20 mm'))
    inputs.addValueInput('bore', t('lbl_bore'), 'mm', adsk.core.ValueInput.createByString('6 mm'))
    inputs.addValueInput('backlash', t('lbl_backlash'), 'mm', adsk.core.ValueInput.createByString('0.05 mm'))
    inputs.addBoolValueInput('pair', t('lbl_pair_cyl'), True, '', False)
    inputs.addIntegerSpinnerCommandInput('teeth2', t('lbl_teeth2_cyl'), 4, 500, 1, 40)
    inputs.addValueInput('bore2', t('lbl_bore2_cyl'), 'mm', adsk.core.ValueInput.createByString('8 mm'))
    inputs.addBoolValueInput('drive', t('lbl_drive'), True, '', True)
    inputs.addTextBoxCommandInput('info', t('lbl_info'), '', 7, True)
    _visibility(inputs)


def bevel_setup(inputs):
    _add_presets(inputs, presets.BEVEL)
    _add_choice(inputs, 'line', 'lbl_line')
    _add_common(inputs, 'lbl_module_outer')
    inputs.addIntegerSpinnerCommandInput('teeth2', t('lbl_teeth2_bevel'), 4, 500, 1, 30)
    inputs.addValueInput('sigma', t('lbl_sigma'), 'deg', adsk.core.ValueInput.createByString('90 deg'))
    inputs.addValueInput('beta', t('lbl_beta_mid'), 'deg', adsk.core.ValueInput.createByString('30 deg'))
    _add_choice(inputs, 'hand', 'lbl_hand')
    inputs.addValueInput('cutter', t('lbl_cutter'), 'mm', adsk.core.ValueInput.createByString('0 mm'))
    inputs.addValueInput('alpha', t('lbl_alpha'), 'deg', adsk.core.ValueInput.createByString('20 deg'))
    inputs.addValueInput('width', t('lbl_width'), 'mm', adsk.core.ValueInput.createByString('10 mm'))
    inputs.addValueInput('back', t('lbl_back'), 'mm', adsk.core.ValueInput.createByString('5 mm'))
    inputs.addValueInput('bore', t('lbl_bore'), 'mm', adsk.core.ValueInput.createByString('6 mm'))
    inputs.addValueInput('backlash', t('lbl_backlash'), 'mm', adsk.core.ValueInput.createByString('0.05 mm'))
    inputs.addIntegerSpinnerCommandInput('sections', t('lbl_sections'), 3, 25, 1, 7)
    inputs.addBoolValueInput('pair', t('lbl_pair_bevel'), True, '', False)
    inputs.addValueInput('bore2', t('lbl_bore2_bevel'), 'mm', adsk.core.ValueInput.createByString('8 mm'))
    inputs.addBoolValueInput('drive', t('lbl_drive'), True, '', True)
    inputs.addTextBoxCommandInput('info', t('lbl_info'), '', 9, True)
    _visibility(inputs)


def cyl_build(inputs):
    kind, g1, g2 = cyl_from_inputs(inputs)
    label = t('kind_' + CYL_KINDS[kind]).lower()
    gears = [(g1, t('name_pinion', kind=label, z=g1.z, m=f'{g1.mn * 10:g}'))]
    if g2:
        gears.append((g2, t('name_gear', kind=label, z=g2.z, m=f'{g2.mn * 10:g}')))
    _run_build(lambda c, g, n: build_cylindrical(c, g, kind, n), gears,
               g1.mate_transform(g2) if g2 else None, inputs.itemById('drive').value)


def bevel_build(inputs):
    g1, g2 = bevel_from_inputs(inputs)
    gears = [(g1, t('name_bevel', z=g1.z, zm=g1.z_mate, m=f'{g1.m * 10:g}'))]
    if g2:
        gears.append((g2, t('name_bevel', z=g2.z, zm=g2.z_mate, m=f'{g2.m * 10:g}')))
    _run_build(build_bevel, gears, g1.mate_transform(g2) if g2 else None, inputs.itemById('drive').value)


# --------------------------------------------------------------------------- bearings

_syncing = False   # set while the bearing dialog changes its own inputs


def _g(v_cm):
    return f'{v_cm * 10:g}'


def _edge(inputs):
    sel = inputs.itemById('place')
    return sel.selection(0).entity if sel.selectionCount else None


def _edge_place(edge):
    """Centre, normal, diameter and a point of the adjacent cylinder of a circular edge (cm)."""
    geo = edge.geometry
    toward = None
    for face in edge.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
            p = face.pointOnFace
            toward = (p.x, p.y, p.z)
            break
    c, n = geo.center, geo.normal
    return dict(center=(c.x, c.y, c.z), normal=(n.x, n.y, n.z), dia=2 * geo.radius,
                toward=toward, occ=edge.assemblyContext)


def _fill_sizes(inputs, series, index=None):
    """Sizes of a series in the size dropdown; selects index, else the size in the d/D/B fields, else the first."""
    dd = adsk.core.DropDownCommandInput.cast(inputs.itemById('size'))
    dd.listItems.clear()
    items = bearingmath.sizes(series)
    for name, d, D, B in items:
        dd.listItems.add(t('size_item', name=name, d=f'{d:g}', D=f'{D:g}', B=f'{B:g}'), False)
    if not items:
        dd.listItems.add('—', True)
        return
    if index is None:
        index = bearingmath.find_size(_value(inputs, 'bearing_d'), _value(inputs, 'bearing_D'),
                                      _value(inputs, 'bearing_B'), series) or 0
    dd.listItems.item(index).isSelected = True
    _set_size(inputs, series, index)


def _set_size(inputs, series, index):
    _, d, D, B = bearingmath.sizes(series)[index]
    for iid, v in (('bearing_d', d), ('bearing_D', D), ('bearing_B', B)):
        inputs.itemById(iid).expression = f'{v:g} mm'


def _bearing_visibility(inputs):
    series = _choice(inputs, 'series')
    custom = series in bearingmath.CUSTOM
    inputs.itemById('size').isVisible = not custom
    for iid in ('bearing_d', 'bearing_D', 'bearing_B'):
        inputs.itemById(iid).isEnabled = custom
    inputs.itemById('shields').isVisible = (bearingmath.kind_of(series) == 'radial'
                                            and _choice(inputs, 'detail') == 'full')
    inputs.itemById('fix').isVisible = _edge(inputs) is not None


def bearing_changed(inputs, changed_input):
    global _syncing
    if _syncing:
        return
    _syncing = True
    try:
        iid = changed_input.id
        series = _choice(inputs, 'series')
        if iid == 'series':
            _fill_sizes(inputs, series)
        elif iid == 'size' and series not in bearingmath.CUSTOM:
            _set_size(inputs, series, inputs.itemById('size').selectedItem.index)
        elif iid in ('place', 'match') and inputs.itemById('match').value:
            edge = _edge(inputs)
            if edge is not None:
                size = None if series in bearingmath.CUSTOM else inputs.itemById('size').selectedItem.index
                hit = bearingmath.match_diameter(_edge_place(edge)['dia'], series,
                                                 bearingmath.kind_of(series), size)
                if hit:
                    found, index, _ = hit
                    dd = inputs.itemById('series')
                    dd.listItems.item(bearingmath.SERIES_KEYS.index(found)).isSelected = True
                    _fill_sizes(inputs, found, index)
        _bearing_visibility(inputs)
    finally:
        _syncing = False


def bearing_from_inputs(inputs):
    series = _choice(inputs, 'series')
    d, D, B = (_value(inputs, iid) for iid in ('bearing_d', 'bearing_D', 'bearing_B'))
    full = _choice(inputs, 'detail') == 'full'
    shields = full and inputs.itemById('shields').value
    index = bearingmath.find_size(d, D, B, series)
    if index is None:
        name = t('name_bearing_custom', d=_g(d), D=_g(D), B=_g(B))
    else:
        name = bearingmath.sizes(series)[index][0] + ('-2Z' if shields and bearingmath.kind_of(series) == 'radial' else '')
    b = bearingmath.Bearing(bearingmath.kind_of(series), d, D, B, shields=shields, name=name)
    edge = _edge(inputs)
    return b, full, (_edge_place(edge) if edge is not None else None)


def bearing_info(b, full, place):
    i = b.info()
    w = 'B' if b.kind == 'radial' else 'H'
    lines = [t('info_bearing', name=b.name, d=_mm(i['d']), D=_mm(i['D']), w=w, B=_mm(i['B']))]
    if full:
        lines.append(t('info_balls', z=i['z'], dw=_mm(i['Dw']), dp=_mm(i['dp'])))
    if place is None:
        lines.append(t('info_place_origin'))
    else:
        dia = place['dia']
        key = ('info_place_fit_d' if abs(dia - b.d) <= bearingmath.MATCH_TOL else
               'info_place_fit_D' if abs(dia - b.D) <= bearingmath.MATCH_TOL else 'info_place_nofit')
        lines.append(t(key, v=_mm(dia)))
    if full:
        lines.append(t('info_geometry_note'))
    return '<br>'.join(lines)


def _revolve(comp, segs, name, axis=None):
    """Body of a section revolved a full turn; axis(sketch) picks the axis, default the component Z."""
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = t('sk_section_of', name=name)
    sk.isComputeDeferred = True
    _draw_closed(sk, segs, _model_to_sketch(sk))
    sk.isComputeDeferred = False
    revolves = comp.features.revolveFeatures
    rin = revolves.createInput(_largest_profile(sk), axis(sk) if axis else comp.zConstructionAxis,
                               adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    rin.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    body = revolves.add(rin).bodies.item(0)
    body.name = name
    sk.isVisible = False
    return body


def build_bearing(comp, b, full):
    """Bodies of the bearing in comp, axis Z from z = 0."""
    if not full:
        return [_revolve(comp, b.simple(), b.name)]
    bodies = [_revolve(comp, segs, t(key)) for key, segs in b.rings()]
    ball = _revolve(comp, b.ball(), t('part_ball'), lambda sk: sk.sketchCurves.sketchLines.item(0))
    pat_in = comp.features.circularPatternFeatures.createInput(_collection([ball]), comp.zConstructionAxis)
    pat_in.quantity = adsk.core.ValueInput.createByReal(b.z)
    pat_in.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    pattern = comp.features.circularPatternFeatures.add(pat_in)
    balls = [ball] + [x for x in pattern.bodies if x != ball]
    for i, x in enumerate(balls):
        x.name = f'{t("part_ball")} {i + 1}'
    return bodies + balls


def _fix(design, occ, target):
    """Rigid as-built joint of the bearing to the part of the picked edge; grounds it when there is none."""
    if target is not None:
        try:
            inp = design.rootComponent.asBuiltJoints.createInput(occ, target, None)
            inp.setAsRigidJointMotion()
            joint = design.rootComponent.asBuiltJoints.add(inp)
            joint.name = t('name_bearing_fix', name=occ.component.name)
            return
        except Exception:
            pass
    occ.isGrounded = True


def bearing_build(inputs):
    b, full, place = bearing_from_inputs(inputs)
    design = adsk.fusion.Design.cast(_app.activeProduct)
    if not design:
        raise GearError('open_design')
    p = place or dict(center=(0, 0, 0), normal=(0, 0, 1), toward=None, occ=None)
    m = bearingmath.placement(p['center'], p['normal'], p['toward'], inputs.itemById('flip').value,
                              _value(inputs, 'offset'))
    name = t('name_bearing', name=b.name)
    start = _timeline_count(design)
    comp, occ = _target_component(design, name, m)
    bodies = build_bearing(comp, b, full)
    if occ is None:
        for body in bodies:
            _move(comp, body, m)
    elif place is not None and inputs.itemById('fix').value:
        _fix(design, occ, place['occ'])
    _group_timeline(design, start, name)


def bearing_setup(inputs):
    sel = inputs.addSelectionInput('place', t('lbl_place'), t('lbl_place_tip'))
    sel.addSelectionFilter('CircularEdges')
    sel.setSelectionLimits(0, 1)
    inputs.addBoolValueInput('match', t('lbl_match'), True, '', True)
    inputs.addBoolValueInput('flip', t('lbl_flip'), True, '', False)
    inputs.addValueInput('offset', t('lbl_offset'), 'mm', adsk.core.ValueInput.createByString('0 mm'))
    _add_choice(inputs, 'series', 'lbl_series')
    _add_dropdown(inputs, 'size', t('lbl_size'), [])
    inputs.addValueInput('bearing_d', t('lbl_bearing_d'), 'mm', adsk.core.ValueInput.createByString('8 mm'))
    inputs.addValueInput('bearing_D', t('lbl_bearing_D'), 'mm', adsk.core.ValueInput.createByString('22 mm'))
    inputs.addValueInput('bearing_B', t('lbl_bearing_B'), 'mm', adsk.core.ValueInput.createByString('7 mm'))
    _add_choice(inputs, 'detail', 'lbl_detail')
    inputs.addBoolValueInput('shields', t('lbl_shields'), True, '', False)
    inputs.addBoolValueInput('fix', t('lbl_fix'), True, '', True)
    inputs.addTextBoxCommandInput('info', t('lbl_info'), '', 5, True)
    _fill_sizes(inputs, bearingmath.SERIES_KEYS[0])   # miniature series, 608 from the fields
    _bearing_visibility(inputs)


class _CheckCreated(adsk.core.CommandCreatedEventHandler):
    """Command without inputs: Fusion executes it right after creation."""

    def notify(self, args):
        try:
            h = _CheckExecute()
            args.command.execute.add(h)
            _handlers.append(h)
        except Exception:
            _ui.messageBox(t('msg_error') + '\n' + traceback.format_exc())


class _CheckExecute(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if not design:
                raise GearError('open_design')
            _report_check(design)
        except GearError as e:
            _ui.messageBox(strings.error(e))
        except Exception:
            _ui.messageBox(t('msg_check_failed') + '\n' + traceback.format_exc())


# --------------------------------------------------------------------------- add-in entry points

COMMANDS = [
    (CYL_ID, 'cmd_cyl', lambda: _Created(cyl_setup, cyl_from_inputs, cyl_info, cyl_build,
                                         _gear_changed(presets.CYLINDRICAL))),
    (BEVEL_ID, 'cmd_bevel', lambda: _Created(bevel_setup, bevel_from_inputs, bevel_info, bevel_build,
                                             _gear_changed(presets.BEVEL))),
    (BEARING_ID, 'cmd_bearing', lambda: _Created(bearing_setup, bearing_from_inputs, bearing_info, bearing_build,
                                                 bearing_changed, preview=True, fail_key='msg_bearing_failed')),
]


def _button(cid, text_key):
    # a definition Fusion still holds on to (e.g. a recently used command) is reused
    return (_ui.commandDefinitions.itemById(cid) or
            _ui.commandDefinitions.addButtonDefinition(cid, t(text_key), t(text_key + '_tip'),
                                                       os.path.join(_HERE, 'resources', cid)))


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        strings.set_language(strings.detect(_app))
        panel = _ui.allToolbarPanels.itemById(PANEL_ID)
        _remove_commands()  # leftovers of a previous run
        for cid, text_key, handler in COMMANDS:
            cdef = _button(cid, text_key)
            h = handler()
            cdef.commandCreated.add(h)
            _handlers.append(h)
            if panel:
                panel.controls.addCommand(cdef)
        cdef = _button(CHECK_ID, 'cmd_check')
        h = _CheckCreated()
        cdef.commandCreated.add(h)
        _handlers.append(h)
        inspect = _ui.allToolbarPanels.itemById(INSPECT_PANEL_ID)
        if inspect:
            inspect.controls.addCommand(cdef)
    except Exception:
        if _ui:
            _ui.messageBox(t('msg_start_failed') + '\n' + traceback.format_exc())


def _buttons():
    return [(cid, PANEL_ID) for cid, *_ in COMMANDS] + [(CHECK_ID, INSPECT_PANEL_ID)]


def _remove_commands():
    # all buttons first, then the definitions: deleting them interleaved loses a fresh button
    for cid, panel_id in _buttons():
        panel = _ui.allToolbarPanels.itemById(panel_id)
        ctl = panel.controls.itemById(cid) if panel else None
        if ctl:
            ctl.deleteMe()
    for cid, _ in _buttons():
        cdef = _ui.commandDefinitions.itemById(cid)
        if cdef:
            cdef.deleteMe()


def stop(context):
    try:
        _remove_commands()
        _handlers.clear()
    except Exception:
        if _ui:
            _ui.messageBox(t('msg_stop_failed') + '\n' + traceback.format_exc())
