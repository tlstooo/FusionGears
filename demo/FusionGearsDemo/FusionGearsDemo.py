"""Demo gear sets for «Проверка зубчатой передачи».

Opens two new documents:
- «Исправная передача»: a three-gear chain at an angle and a bevel pair — the check finds nothing;
- «Передача с ошибками»: the same chain with a reversed link, an idler in mesh without a link
  and three gears in a triangle (each pair turns, all three together cannot).

Run from Fusion: Utilities > Scripts and Add-Ins > Scripts > FusionGearsDemo.
"""
import adsk.core
import adsk.fusion
import importlib.util
import math
import os
import traceback

ADDIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = math.radians
M, WIDTH, BACKLASH, BORE = 0.15, 0.8, 0.01, 0.5   # cm: module 1.5 mm, width 8 mm


def _load_addin():
    # a private copy: reloading the module the running add-in uses would orphan its buttons
    spec = importlib.util.spec_from_file_location('FusionGears_demo', os.path.join(ADDIN, 'FusionGears.py'))
    fg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fg)
    return fg


def _chain(fg, design, frame, specs, origin):
    """Spur gears placed one after another so that each meshes with its parent.

    specs — [(name, z, parent index or None, direction from parent in degrees, linked)].
    Returns {name: (occurrence, body, joint, gear)}.
    """
    gm = fg.gearmath
    built, order = {}, []
    for name, z, parent, theta, linked in specs:
        g = gm.CylindricalGear(M, z, 0.0, D(20), WIDTH, 1, BACKLASH, BORE)
        if parent is None:
            x, y, phi = origin[0], origin[1], 0.0
        else:
            p_occ, p_body, p_joint, p_gear, (px, py, pphi) = built[order[parent]]
            d = p_gear.r + g.r
            x, y = px + d * math.cos(D(theta)), py + d * math.sin(D(theta))
            phi = gm.mesh_phase(p_gear, pphi, D(theta), g)
        m = gm.placement(x, y, phi)
        comp, occ = fg._target_component(design, name)
        body = fg.build_cylindrical(comp, g, 2, name)
        fg._move(comp, body, m)
        joint = fg.add_joint(design, frame, occ, m)
        built[name] = (occ, body, joint, g, (x, y, phi))
        order.append(name)
        if parent is not None and linked:
            p_occ, p_body, p_joint, p_gear, _ = built[order[parent]]
            fg.add_link(design, [p_joint, joint], p_gear.z, g.z, [(p_occ, p_body), (occ, body)])
    return built


def _bevel_pair(fg, design):
    gm = fg.gearmath
    g1 = gm.BevelGear(M, 15, 30, D(90), D(20), 0.7, 'straight', 0.0, 1, BACKLASH, 0.4, BORE)
    g2 = g1.mate(0.8)
    built = []
    for g, name in ((g1, 'Коническая z15'), (g2, 'Коническая z30')):
        comp, occ = fg._target_component(design, name)
        body = fg.build_bevel(comp, g, name)
        built.append((occ, body))
    t = g1.mate_transform(g2)
    fg._move(built[1][0].component, built[1][1], t)
    fg.add_drive(design, built, 15, 30, [None, t])


def build_correct(app, fg):
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    frame = fg.add_frame(design, 'Стойка — исправная передача')
    _chain(fg, design, frame, [
        ('Ведущая z15', 15, None, 0, True),
        ('Промежуточная z30', 30, 0, 0, True),
        ('Ведомая z20', 20, 1, 70, True),
    ], origin=(0.0, -9.0))
    _bevel_pair(fg, design)
    return design


def build_faulty(app, fg):
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    frame = fg.add_frame(design, 'Стойка — передача с ошибками')
    chain = _chain(fg, design, frame, [
        ('Ведущая z15', 15, None, 0, True),
        ('Промежуточная z30', 30, 0, 0, True),
        ('Ведомая z20', 20, 1, 70, True),
        ('Лишняя z18 (без связи)', 18, 0, 200, False),
    ], origin=(0.0, -9.0))
    # mistake 1: the last link of the chain turns both gears the same way
    for link in chain['Ведомая z20'][2].motionLinks:
        link.isReversed = not link.isReversed
    # mistake 3: three gears meshing in a triangle
    tri = _chain(fg, design, frame, [
        ('Треугольник A z21', 21, None, 0, True),
        ('Треугольник B z21', 21, 0, 0, True),
        ('Треугольник C z21', 21, 0, 60, True),
    ], origin=(9.0, 0.0))
    ob, bb, jb, gb, _ = tri['Треугольник B z21']
    oc, bc, jc, gc, _ = tri['Треугольник C z21']
    fg.add_link(design, [jb, jc], gb.z, gc.z, [(ob, bb), (oc, bc)])
    return design


def build_all(app, show=True):
    fg = _load_addin()
    fg._app, fg._ui = app, app.userInterface
    lines = []
    for title, builder in (('Передача с ошибками', build_faulty), ('Исправная передача', build_correct)):
        design = builder(app, fg)
        problems, summary = fg.check_system(design)
        lines.append(f'{title}: {summary}')
        lines += ['  • ' + p for p in problems] or ['  проблем не найдено']
    text = '\n'.join(lines)
    if show:
        app.userInterface.messageBox(
            'Созданы два документа (вкладки Untitled): последний открытый — исправная передача, '
            'предыдущий — передача с ошибками.\n\nЧто находит проверка:\n' + text)
    return text


def run(context):
    app = adsk.core.Application.get()
    try:
        build_all(app)
    except Exception:
        app.userInterface.messageBox('FusionGearsDemo: ошибка\n' + traceback.format_exc())
