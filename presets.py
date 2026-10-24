"""Typical gear sets offered in the dialogs. Pure data, no Fusion dependencies.

Each preset is ((russian name, english name), values). Keys of values are
command input ids. Lengths are in mm, angles in degrees, dropdowns by their
key (kind: herringbone | helical | spur; line: straight | skew | spiral | gleason;
hand: right | left); fields a preset does not mention keep their current value.
"""

LENGTH_KEYS = {'module', 'width', 'bore', 'bore2', 'backlash', 'back', 'cutter'}
ANGLE_KEYS = {'beta', 'alpha', 'sigma'}

CYLINDRICAL = [
    (('Шеврон 1:2, 3D-печать (m2, 20/40)', 'Herringbone 1:2, 3D printing (m2, 20/40)'), dict(
        kind='herringbone', module=2, teeth=20, teeth2=40, beta=30, alpha=20, width=20,
        bore=5, bore2=8, backlash=0.15, pair=True, drive=True)),
    (('Шеврон 1:3, редуктор NEMA17 (m1.5, 15/45)', 'Herringbone 1:3, NEMA17 gearbox (m1.5, 15/45)'), dict(
        kind='herringbone', module=1.5, teeth=15, teeth2=45, beta=25, alpha=20, width=15,
        bore=5, bore2=8, backlash=0.1, pair=True, drive=True)),
    (('Шеврон 1:3, крупный (m3, 18/54)', 'Herringbone 1:3, large (m3, 18/54)'), dict(
        kind='herringbone', module=3, teeth=18, teeth2=54, beta=30, alpha=20, width=30,
        bore=8, bore2=12, backlash=0.2, pair=True, drive=True)),
    (('Косозубая 1:2 (m1, 20/40)', 'Helical 1:2 (m1, 20/40)'), dict(
        kind='helical', module=1, teeth=20, teeth2=40, beta=20, alpha=20, width=10,
        bore=3, bore2=5, backlash=0.05, pair=True, drive=True)),
    (('Прямозубая 1:2 (m1, 17/34)', 'Spur 1:2 (m1, 17/34)'), dict(
        kind='spur', module=1, teeth=17, teeth2=34, alpha=20, width=8,
        bore=3, bore2=5, backlash=0.05, pair=True, drive=True)),
    (('Прямозубая 1:4 (m0.5, 15/60)', 'Spur 1:4 (m0.5, 15/60)'), dict(
        kind='spur', module=0.5, teeth=15, teeth2=60, alpha=20, width=5,
        bore=2, bore2=3, backlash=0.03, pair=True, drive=True)),
]

BEVEL = [
    (('Угловая 1:1, прямой зуб (m2, 20/20)', 'Bevel 1:1, straight teeth (m2, 20/20)'), dict(
        line='straight', module=2, teeth=20, teeth2=20, sigma=90, alpha=20, width=8,
        back=4, bore=5, bore2=5, backlash=0.1, pair=True, drive=True)),
    (('Угловая 1:2, прямой зуб (m1.5, 15/30)', 'Bevel 1:2, straight teeth (m1.5, 15/30)'), dict(
        line='straight', module=1.5, teeth=15, teeth2=30, sigma=90, alpha=20, width=7,
        back=4, bore=5, bore2=8, backlash=0.1, pair=True, drive=True)),
    (('Угловая 1:1, спиральный зуб 35° (m2, 20/20)', 'Bevel 1:1, spiral teeth 35° (m2, 20/20)'), dict(
        line='spiral', module=2, teeth=20, teeth2=20, sigma=90, beta=35,
        hand='right', alpha=20, width=8, back=4, bore=5, bore2=5, backlash=0.1,
        sections=7, pair=True, drive=True)),
    (('Угловая 1:2, косой зуб 25° (m2, 16/32)', 'Bevel 1:2, skew teeth 25° (m2, 16/32)'), dict(
        line='skew', module=2, teeth=16, teeth2=32, sigma=90, beta=25,
        hand='right', alpha=20, width=8, back=4, bore=5, bore2=8, backlash=0.1,
        sections=7, pair=True, drive=True)),
    (('Угловая 1:3, спиральный зуб 35° (m1.5, 14/42)', 'Bevel 1:3, spiral teeth 35° (m1.5, 14/42)'), dict(
        line='spiral', module=1.5, teeth=14, teeth2=42, sigma=90, beta=35,
        hand='right', alpha=20, width=10, back=4, bore=4, bore2=8, backlash=0.1,
        sections=7, pair=True, drive=True)),
    (('Угловая 1:2, круговой зуб Gleason 35° (m2, 16/32)', 'Bevel 1:2, Gleason circular teeth 35° (m2, 16/32)'), dict(
        line='gleason', module=2, teeth=16, teeth2=32, sigma=90, beta=35, cutter=0,
        hand='right', alpha=20, width=10, back=4, bore=5, bore2=8, backlash=0.1,
        sections=9, pair=True, drive=True)),
]
