"""Fusion smoke test: builds every gear variant in a new document and logs the result.

Run from Fusion: Utilities > Scripts and Add-Ins > Scripts > FusionGearsSmoke.
The log is written next to the add-in: tests/fusion_smoke_log.txt
"""
import adsk.core
import adsk.fusion
import importlib
import importlib.util
import math
import os
import sys
import time
import traceback

ADDIN = os.environ.get('FUSIONGEARS_DIR',
                       os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOG = os.path.join(ADDIN, 'tests', 'fusion_smoke_log.txt')
D = math.radians


def run(context):
    app = adsk.core.Application.get()
    lines = []
    log = lines.append
    docs = []  # every document this test opens is closed again at the end
    try:
        if ADDIN not in sys.path:
            sys.path.insert(0, ADDIN)
        # a private copy: reloading the module the running add-in uses would orphan its buttons
        spec = importlib.util.spec_from_file_location('FusionGears_smoke', os.path.join(ADDIN, 'FusionGears.py'))
        fg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fg)
        gearmath = fg.gearmath
        fg._app, fg._ui = app, app.userInterface

        docs.append(app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType))
        design = adsk.fusion.Design.cast(app.activeProduct)
        log(f'design intent: {getattr(design, "designIntent", "?")}')
        tbm = adsk.fusion.TemporaryBRepManager.get()

        def body_report(name, body):
            vol = body.physicalProperties.volume
            log(f'  {name}: solid={body.isSolid} valid={body.isValid} faces={body.faces.count} '
                f'volume={vol:.4f} cm3')
            return body

        def overlap(b1, b2):
            t1, t2 = tbm.copy(b1), tbm.copy(b2)
            tbm.booleanOperation(t1, t2, adsk.fusion.BooleanTypes.IntersectionBooleanType)
            return t1.volume if t1 else 0.0

        def case(title, builder, gears, transform, shift):
            nonlocal design
            t0 = time.time()
            log(title)
            docs.append(app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType))
            design = adsk.fusion.Design.cast(app.activeProduct)
            bodies, built = [], []
            for idx, (gear, name) in enumerate(gears):
                comp, occ = fg._target_component(design, name)
                body = builder(comp, gear, name)
                if idx > 0:
                    fg._move(comp, body, transform)
                bodies.append(body_report(name, body))
                built.append((occ, body))
            if len(bodies) == 2:
                log(f'  pair overlap volume = {overlap(bodies[0], bodies[1]):.6f} cm3')
                (j1, j2), link = fg.add_drive(design, built, gears[0][0].z, gears[1][0].z, [None, transform])
                turns = []
                for deg in (0.0, 4.0, 9.0, 13.0):
                    j1.jointMotion.rotationValue = math.radians(deg)
                    turns.append(f'{deg:g}->{math.degrees(j2.jointMotion.rotationValue):.3f}/{fg._overlap(built):.6f}')
                j1.jointMotion.rotationValue = 0.0
                log(f'  drive reversed={link.isReversed}: gear1 deg->gear2 deg/overlap ' + ', '.join(turns))
            log(f'  time {time.time() - t0:.1f} s')

        m = 0.2  # 2 mm
        x = 0.0
        for kind, beta in ((0, D(30)), (1, D(20)), (2, 0.0)):
            g1 = gearmath.CylindricalGear(m, 17, beta, D(20), 2.0, 1, 0.005, 0.6)
            g2 = gearmath.CylindricalGear(m, 31, beta, D(20), 2.0, -1, 0.005, 0.8)
            case(f'cylindrical kind={kind} beta={math.degrees(beta):.0f}',
                 lambda c, g, n, k=kind: fg.build_cylindrical(c, g, k, n),
                 [(g1, f'cyl{kind}_a'), (g2, f'cyl{kind}_b')], g1.mate_transform(g2), x)
            x += 12
        for line, beta in (('straight', 0.0), ('skew', D(25)), ('spiral', D(35))):
            g1 = gearmath.BevelGear(m, 18, 27, D(90), D(20), 0.9, line, beta, 1, 0.005, 0.5, 0.6, 7)
            g2 = g1.mate(0.8)
            case(f'bevel {line}', fg.build_bevel,
                 [(g1, f'bevel_{line}_a'), (g2, f'bevel_{line}_b')], g1.mate_transform(g2), x)
            x += 12
        g = gearmath.BevelGear(m, 20, 20, D(70), D(20), 0.8, 'spiral', D(30), -1, 0.0, 0.4, 0.0, 5)
        case('bevel spiral, shaft angle 70, left, no bore', fg.build_bevel, [(g, 'bevel_70')], None, x)
        log('DONE')
    except Exception:
        log('FAILED\n' + traceback.format_exc())
    finally:
        for doc in docs:
            try:
                doc.close(False)
            except Exception:
                pass
        with open(LOG, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
