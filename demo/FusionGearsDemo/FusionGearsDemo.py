"""Demo gear sets for «Проверка зубчатой передачи».

Opens two new documents:
- a correct gear train: a three-gear chain at an angle and a bevel pair — the check finds nothing;
- a faulty gear train: the same chain with a reversed link, a gear in mesh without a link
  and three gears in a triangle (each pair turns, all three together cannot).
Names follow Fusion's interface language, like the add-in.

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


NAMES = {
    'driver': ('Ведущая z15', 'Driver z15'),
    'idler': ('Промежуточная z30', 'Idler z30'),
    'driven': ('Ведомая z20', 'Driven z20'),
    'extra': ('Лишняя z18 (без связи)', 'Extra z18 (no link)'),
    'tri_a': ('Треугольник A z21', 'Triangle A z21'),
    'tri_b': ('Треугольник B z21', 'Triangle B z21'),
    'tri_c': ('Треугольник C z21', 'Triangle C z21'),
    'bevel_15': ('Коническая z15', 'Bevel z15'),
    'bevel_30': ('Коническая z30', 'Bevel z30'),
    'frame_ok': ('Стойка — исправная передача', 'Frame — correct gear train'),
    'frame_bad': ('Стойка — передача с ошибками', 'Frame — faulty gear train'),
    'doc_ok': ('Исправная передача', 'Correct gear train'),
    'doc_bad': ('Передача с ошибками', 'Faulty gear train'),
    'no_problems': ('проблем не найдено', 'no problems found'),
    'done': ('Созданы два документа (вкладки Untitled): последний открытый — исправная передача, '
             'предыдущий — передача с ошибками.\n\nЧто находит проверка:\n',
             'Two documents were opened (Untitled tabs): the last one is the correct gear train, '
             'the one before it is the faulty gear train.\n\nWhat the check finds:\n'),
    'failed': ('FusionGearsDemo: ошибка', 'FusionGearsDemo: error'),
}


def _chain(fg, design, frame, specs, origin):
    """Spur gears placed one after another so that each meshes with its parent.

    specs — [(name key, z, parent index or None, direction from parent in degrees, linked)].
    Returns {name key: (occurrence, body, joint, gear, placement)}.
    """
    gm = fg.gearmath
    built, order = {}, []
    for key, z, parent, theta, linked in specs:
        g = gm.CylindricalGear(M, z, 0.0, D(20), WIDTH, 1, BACKLASH, BORE)
        if parent is None:
            x, y, phi = origin[0], origin[1], 0.0
        else:
            p_occ, p_body, p_joint, p_gear, (px, py, pphi) = built[order[parent]]
            d = p_gear.r + g.r
            x, y = px + d * math.cos(D(theta)), py + d * math.sin(D(theta))
            phi = gm.mesh_phase(p_gear, pphi, D(theta), g)
        m = gm.placement(x, y, phi)
        name = fg.strings.pick(NAMES[key])
        comp, occ = fg._target_component(design, name)
        body = fg.build_cylindrical(comp, g, 2, name)
        fg._move(comp, body, m)
        joint = fg.add_joint(design, frame, occ, m)
        built[key] = (occ, body, joint, g, (x, y, phi))
        order.append(key)
        if parent is not None and linked:
            p_occ, p_body, p_joint, p_gear, _ = built[order[parent]]
            fg.add_link(design, [p_joint, joint], p_gear.z, g.z, [(p_occ, p_body), (occ, body)])
    return built


def _bevel_pair(fg, design):
    gm = fg.gearmath
    g1 = gm.BevelGear(M, 15, 30, D(90), D(20), 0.7, 'straight', 0.0, 1, BACKLASH, 0.4, BORE)
    g2 = g1.mate(0.8)
    built = []
    for g, key in ((g1, 'bevel_15'), (g2, 'bevel_30')):
        name = fg.strings.pick(NAMES[key])
        comp, occ = fg._target_component(design, name)
        body = fg.build_bevel(comp, g, name)
        built.append((occ, body))
    t = g1.mate_transform(g2)
    fg._move(built[1][0].component, built[1][1], t)
    fg.add_drive(design, built, 15, 30, [None, t])


def build_correct(app, fg):
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    frame = fg.add_frame(design, fg.strings.pick(NAMES['frame_ok']))
    _chain(fg, design, frame, [
        ('driver', 15, None, 0, True),
        ('idler', 30, 0, 0, True),
        ('driven', 20, 1, 70, True),
    ], origin=(0.0, -9.0))
    _bevel_pair(fg, design)
    return design


def build_faulty(app, fg):
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    frame = fg.add_frame(design, fg.strings.pick(NAMES['frame_bad']))
    chain = _chain(fg, design, frame, [
        ('driver', 15, None, 0, True),
        ('idler', 30, 0, 0, True),
        ('driven', 20, 1, 70, True),
        ('extra', 18, 0, 200, False),   # mistake 2: in mesh without a link
    ], origin=(0.0, -9.0))
    # mistake 1: the last link of the chain turns both gears the same way
    for link in chain['driven'][2].motionLinks:
        link.isReversed = not link.isReversed
    # mistake 3: three gears meshing in a triangle
    tri = _chain(fg, design, frame, [
        ('tri_a', 21, None, 0, True),
        ('tri_b', 21, 0, 0, True),
        ('tri_c', 21, 0, 60, True),
    ], origin=(9.0, 0.0))
    ob, bb, jb, gb, _ = tri['tri_b']
    oc, bc, jc, gc, _ = tri['tri_c']
    fg.add_link(design, [jb, jc], gb.z, gc.z, [(ob, bb), (oc, bc)])
    return design


def build_all(app, show=True):
    fg = _load_addin()
    fg._app, fg._ui = app, app.userInterface
    fg.strings.set_language(fg.strings.detect(app))
    pick = fg.strings.pick
    lines = []
    for title, builder in (('doc_bad', build_faulty), ('doc_ok', build_correct)):
        design = builder(app, fg)
        problems, summary = fg.check_system(design)
        lines.append(f'{pick(NAMES[title])}: {summary}')
        lines += ['  • ' + p for p in problems] or ['  ' + pick(NAMES['no_problems'])]
    text = '\n'.join(lines)
    if show:
        app.userInterface.messageBox(pick(NAMES['done']) + text)
    return text


def run(context):
    app = adsk.core.Application.get()
    try:
        build_all(app)
    except Exception:
        app.userInterface.messageBox(NAMES['failed'][1] + '\n' + traceback.format_exc())
