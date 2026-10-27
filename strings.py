"""User-facing texts of FusionGears in Russian and English. No Fusion dependencies.

The language follows Fusion's interface language: Russian for a Russian
interface, English for any other. FUSIONGEARS_LANG=ru|en overrides it.
"""
import os

LANG = 'en'

TEXT = {
    # commands
    'cmd_cyl': ('Шевронная / косозубая шестерня', 'Herringbone / helical gear'),
    'cmd_cyl_tip': ('Цилиндрическое колесо с шевронным, косым или прямым эвольвентным зубом',
                    'Cylindrical involute gear with herringbone, helical or spur teeth'),
    'cmd_bevel': ('Коническая шестерня', 'Bevel gear'),
    'cmd_bevel_tip': ('Коническое колесо с прямым, косым, спиральным или круговым (Gleason) зубом',
                      'Bevel gear with straight, skew, spiral or Gleason circular-arc teeth'),
    'cmd_check': ('Проверка зубчатой передачи', 'Gear train check'),
    'cmd_check_tip': ('Ищет противоречивые связи движения (колесо должно крутиться в разные стороны), '
                      'пересечения колёс и зацепления без связи',
                      'Finds contradictory motion links (a gear that would have to turn both ways), '
                      'intersecting gears and gears in mesh without a link'),

    'cmd_bearing': ('Подшипник', 'Bearing'),
    'cmd_bearing_tip': ('Радиальный или упорный шариковый подшипник стандартного размера; '
                        'выберите кромку отверстия или вала — размер подберётся по диаметру',
                        'Standard size deep groove or thrust ball bearing; pick the edge of a hole '
                        'or shaft and the size is matched to its diameter'),

    # dialog fields
    'lbl_preset': ('Типовой вариант', 'Typical set'),
    'preset_custom': ('Свои параметры', 'Custom'),
    'lbl_kind': ('Тип зуба', 'Tooth type'),
    'kind_herringbone': ('Шевронный', 'Herringbone'),
    'kind_helical': ('Косозубый', 'Helical'),
    'kind_spur': ('Прямозубый', 'Spur'),
    'lbl_module_normal': ('Нормальный модуль', 'Normal module'),
    'lbl_module_outer': ('Внешний торцовый модуль', 'Outer transverse module'),
    'lbl_teeth': ('Число зубьев', 'Number of teeth'),
    'lbl_beta': ('Угол наклона зуба', 'Helix angle'),
    'lbl_beta_mid': ('Угол наклона зуба (в середине)', 'Spiral angle (mid-face)'),
    'lbl_hand': ('Направление', 'Hand'),
    'hand_right': ('Правый', 'Right'),
    'hand_left': ('Левый', 'Left'),
    'lbl_alpha': ('Угол профиля', 'Pressure angle'),
    'lbl_width': ('Ширина венца', 'Face width'),
    'lbl_bore': ('Диаметр отверстия', 'Bore diameter'),
    'lbl_backlash': ('Боковой зазор', 'Backlash'),
    'lbl_pair_cyl': ('Создать сопряжённое колесо', 'Create mating gear'),
    'lbl_teeth2_cyl': ('Зубьев у колеса 2', 'Teeth of gear 2'),
    'lbl_bore2_cyl': ('Отверстие колеса 2', 'Bore of gear 2'),
    'lbl_drive': ('Шарниры и связь движения', 'Joints and motion link'),
    'lbl_info': ('Расчёт', 'Calculation'),
    'lbl_line': ('Линия зуба', 'Tooth line'),
    'line_straight': ('Прямой', 'Straight'),
    'line_skew': ('Косой (тангенциальный)', 'Skew (tangential)'),
    'line_spiral': ('Спиральный (логарифмический)', 'Spiral (logarithmic)'),
    'line_gleason': ('Круговой (Gleason)', 'Circular arc (Gleason)'),
    'lbl_teeth2_bevel': ('Зубьев у парного колеса', 'Teeth of the mating gear'),
    'lbl_sigma': ('Межосевой угол', 'Shaft angle'),
    'lbl_back': ('Толщина основания', 'Back thickness'),
    'lbl_sections': ('Сечений по длине зуба', 'Sections along the tooth'),
    'lbl_cutter': ('Радиус резцовой головки (0 — авто)', 'Cutter radius (0 = auto)'),
    'lbl_pair_bevel': ('Создать парное колесо', 'Create mating gear'),
    'lbl_bore2_bevel': ('Отверстие парного колеса', 'Bore of the mating gear'),
    'lbl_place': ('Место (круговая кромка)', 'Location (circular edge)'),
    'lbl_place_tip': ('Кромка отверстия или вала; без выбора подшипник ставится в начало координат',
                      'Edge of a hole or shaft; with none the bearing goes to the origin'),
    'lbl_match': ('Подобрать размер по кромке', 'Match size to the edge'),
    'lbl_flip': ('Перевернуть', 'Flip'),
    'lbl_offset': ('Смещение вдоль оси', 'Offset along the axis'),
    'lbl_series': ('Серия', 'Series'),
    'series_mini': ('Миниатюрные 6xx, MR', 'Miniature 6xx, MR'),
    'series_618': ('Сверхлёгкая 618 (68xx)', 'Extra light 618 (68xx)'),
    'series_619': ('Особо лёгкая 619 (69xx)', 'Extra light 619 (69xx)'),
    'series_60': ('Особо лёгкая 60xx', 'Extra light 60xx'),
    'series_62': ('Лёгкая 62xx', 'Light 62xx'),
    'series_63': ('Средняя 63xx', 'Medium 63xx'),
    'series_511': ('Упорные 511xx', 'Thrust 511xx'),
    'series_512': ('Упорные 512xx', 'Thrust 512xx'),
    'series_custom_radial': ('Радиальный, свои размеры', 'Radial, custom size'),
    'series_custom_thrust': ('Упорный, свои размеры', 'Thrust, custom size'),
    'lbl_size': ('Типоразмер', 'Size'),
    'size_item': ('{name}  ({d}×{D}×{B})', '{name}  ({d}×{D}×{B})'),
    'lbl_bearing_d': ('Внутренний диаметр d', 'Bore d'),
    'lbl_bearing_D': ('Наружный диаметр D', 'Outside diameter D'),
    'lbl_bearing_B': ('Ширина B (высота H)', 'Width B (height H)'),
    'lbl_detail': ('Исполнение', 'Detail'),
    'detail_full': ('Подробное: кольца и шарики', 'Detailed: rings and balls'),
    'detail_simple': ('Упрощённое: одно тело', 'Simplified: one body'),
    'lbl_shields': ('Защитные шайбы (2Z)', 'Shields (2Z)'),
    'lbl_fix': ('Закрепить на детали', 'Fix to the part'),

    # calculation
    'unit_mm': ('мм', 'mm'),
    'info_d': ('Делительный диаметр d = {v}', 'Pitch diameter d = {v}'),
    'info_da': ('Диаметр вершин da = {v}', 'Tip diameter da = {v}'),
    'info_df': ('Диаметр впадин df = {v}', 'Root diameter df = {v}'),
    'info_mt': ('Торцовый модуль mt = {v}', 'Transverse module mt = {v}'),
    'info_gear2_cyl': ('Колесо 2: d = {d}, da = {da}', 'Gear 2: d = {d}, da = {da}'),
    'info_a': ('Межосевое расстояние a = {v}', 'Centre distance a = {v}'),
    'info_delta': ('Угол делительного конуса δ = {v}', 'Pitch cone angle δ = {v}'),
    'info_de': ('Внешний делительный диаметр de = {v}', 'Outer pitch diameter de = {v}'),
    'info_dae': ('Диаметр вершин dae = {v}', 'Outer tip diameter dae = {v}'),
    'info_Re': ('Внешнее конусное расстояние Re = {v}', 'Outer cone distance Re = {v}'),
    'info_zv': ('Эквивалентное число зубьев zv = {v}', 'Virtual number of teeth zv = {v}'),
    'info_beta_range': ('Угол наклона: носок {toe}, середина {mid}, пятка {heel}',
                        'Spiral angle: toe {toe}, mid {mid}, heel {heel}'),
    'info_rc': ('Радиус резцовой головки rc = {v}', 'Cutter radius rc = {v}'),
    'info_face_warn': ('Ширина венца больше рекомендуемой Re/3 = {v}',
                       'Face width exceeds the recommended Re/3 = {v}'),
    'info_gear2_bevel': ('Колесо 2: δ = {delta}, de = {de}', 'Gear 2: δ = {delta}, de = {de}'),
    'info_bearing': ('Подшипник {name}: d = {d}, D = {D}, {w} = {B}', 'Bearing {name}: d = {d}, D = {D}, {w} = {B}'),
    'info_balls': ('Шарики: {z} шт. Ø{dw} на диаметре {dp}', 'Balls: {z} × Ø{dw} on a {dp} pitch circle'),
    'info_place_origin': ('Место: начало координат', 'Location: origin'),
    'info_place_edge': ('Кромка Ø{v}', 'Edge Ø{v}'),
    'info_place_fit_d': ('Кромка Ø{v} — посадка по внутреннему диаметру', 'Edge Ø{v} — fits the bore'),
    'info_place_fit_D': ('Кромка Ø{v} — посадка по наружному диаметру', 'Edge Ø{v} — fits the outside diameter'),
    'info_place_nofit': ('Кромка Ø{v} не совпадает с d и D подшипника', 'Edge Ø{v} matches neither d nor D'),
    'info_geometry_note': ('Внутренняя геометрия приближённая; сепаратор не моделируется',
                           'Internal geometry is approximate; no cage is modelled'),

    # parameter errors (gearmath.GearError keys)
    'what_gear': ('Колесо', 'Gear'),
    'what_bevel': ('Коническое колесо', 'Bevel gear'),
    'err_zero_size': ('Модуль и ширина должны быть больше нуля', 'Module and width must be greater than zero'),
    'err_too_few_teeth': ('Слишком мало зубьев (минимум 4)', 'Too few teeth (at least 4)'),
    'err_helix_range': ('Угол наклона зуба должен быть от 0 до 60°', 'The helix angle must be between 0 and 60°'),
    'err_root_negative': ('Окружность впадин меньше нуля', 'The root circle is below zero'),
    'err_bore_too_big': ('Отверстие слишком большое для этого колеса', 'The bore is too large for this gear'),
    'err_pointed_tooth': ('{what}: заострённый зуб — уменьшите угол или увеличьте число зубьев',
                          '{what}: pointed tooth — reduce the angle or add teeth'),
    'err_root_overlap': ('{what}: зубья пересекаются у основания', '{what}: teeth overlap at the root'),
    'err_shaft_angle_range': ('Межосевой угол должен быть от 10 до 170°', 'The shaft angle must be between 10 and 170°'),
    'err_unknown_line': ('Неизвестный тип линии зуба', 'Unknown tooth line'),
    'err_spiral_range': ('Угол наклона зуба должен быть от 1 до 60°', 'The spiral angle must be between 1 and 60°'),
    'err_cone_too_flat': ('Угол делительного конуса ≥ 89° (плоское/внутреннее колесо не поддерживается)',
                          'Pitch cone angle ≥ 89° (crown and internal bevel gears are not supported)'),
    'err_face_too_wide': ('Ширина венца больше 0.6 конусного расстояния', 'The face width exceeds 0.6 of the cone distance'),
    'err_skew_too_steep': ('Для косого зуба угол слишком велик при такой ширине венца',
                           'The skew angle is too large for this face width'),
    'err_cutter_too_small': ('Радиус резцовой головки {rc:.1f} мм слишком мал для этого венца — '
                             'увеличьте его (обычно около Rm = {rm:.1f} мм) или задайте 0',
                             'The cutter radius {rc:.1f} mm is too small for this face — '
                             'increase it (usually about Rm = {rm:.1f} mm) or set 0'),
    'err_no_profile': ('Не удалось построить замкнутый профиль', 'Could not build a closed profile'),
    'err_bearing_kind': ('Неизвестный тип подшипника', 'Unknown bearing type'),
    'err_bearing_zero': ('Внутренний диаметр и ширина должны быть больше нуля',
                         'The bore and width must be greater than zero'),
    'err_bearing_outer_small': ('Наружный диаметр должен быть больше внутреннего',
                                'The outside diameter must exceed the bore'),
    'err_bearing_too_thin': ('Подшипник слишком тонкий для шариков', 'The bearing is too thin for balls'),
    'err_bearing_axis': ('Не удалось определить ось по кромке', 'Could not get an axis from the edge'),
    'err_open_design':('Откройте проект в рабочем пространстве Design', 'Open a design in the Design workspace'),

    # messages
    'msg_part_no_joints': ('Колёса построены, но соединения не созданы: в дизайне типа Part нет компонентов.',
                           'The gears are built, but no joints were made: a Part design has no components.'),
    'msg_error': ('Ошибка:', 'Error:'),
    'msg_build_failed': ('Не удалось построить шестерню:', 'Could not build the gear:'),
    'msg_bearing_failed': ('Не удалось построить подшипник:', 'Could not build the bearing:'),
    'msg_check_failed': ('Не удалось проверить передачу:', 'Could not check the gear train:'),
    'msg_start_failed': ('FusionGears: ошибка запуска', 'FusionGears: start-up error'),
    'msg_stop_failed': ('FusionGears: ошибка остановки', 'FusionGears: stop error'),

    # gear train check
    'chk_link_unhealthy': ('Связь {link}: {msg}', 'Link {link}: {msg}'),
    'chk_fusion_error': ('ошибка в Fusion', 'error in Fusion'),
    'chk_no_rotation': ('Связь {link} не передаёт вращение', 'Link {link} does not transmit rotation'),
    'chk_clash': ('Связь {link}: при вращении зубья {a} и {b} врезаются — неверное направление '
                  'или передаточное отношение',
                  'Link {link}: the teeth of {a} and {b} collide when turning — wrong direction or ratio'),
    'chk_overlap': ('{a} и {b} пересекаются в текущем положении', '{a} and {b} intersect in the current position'),
    'chk_mesh_no_link': ('{a} и {b} в зацеплении, но не связаны связью движения',
                         '{a} and {b} are in mesh but have no motion link'),
    'chk_opposite': ('в разные стороны', 'in opposite directions'),
    'chk_speed': ('с разной скоростью', 'at different speeds'),
    'chk_conflict': ('{joint}: связи заставляют вращаться {kind} (через {first}: {s1}; через {second}: {s2})',
                     '{joint}: the links make it turn {kind} (via {first}: {s1}; via {second}: {s2})'),
    'chk_driver': ('ведущее соединение', 'the driving joint'),
    'chk_summary': ('Колёс на шарнирах: {gears}, связей движения: {links}.',
                    'Gears on joints: {gears}, motion links: {links}.'),
    'chk_found': ('Проверка зубчатой передачи: найдены проблемы', 'Gear train check: problems found'),
    'chk_none': ('Проверка зубчатой передачи: проблем не найдено.', 'Gear train check: no problems found.'),

    # names of what is created in the design
    'name_pinion': ('Шестерня {kind} z{z} m{m}', 'Pinion {kind} z{z} m{m}'),
    'name_gear': ('Колесо {kind} z{z} m{m}', 'Gear {kind} z{z} m{m}'),
    'name_bevel': ('Коническая z{z}-{zm} m{m}', 'Bevel z{z}-{zm} m{m}'),
    'name_frame': ('Стойка передачи', 'Gear frame'),
    'name_joint': ('Вращение {name}', 'Rotation {name}'),
    'name_link': ('Передача {z1}:{z2}', 'Gear ratio {z1}:{z2}'),
    'sk_profile': ('{name} — профиль', '{name} — profile'),
    'sk_path': ('{name} — ось', '{name} — axis'),
    'pl_middle': ('{name} — середина', '{name} — middle'),
    'sk_blank': ('{name} — заготовка', '{name} — blank'),
    'sk_section_points': ('{name} — точки сечений', '{name} — section points'),
    'sk_section': ('{name} — сечение {i}', '{name} — section {i}'),
    'sk_bore': ('Отверстие', 'Bore'),
    'sk_axis_points': ('{name} — точки оси', '{name} — axis points'),
    'pl_axis': ('{name} — плоскость оси', '{name} — axis plane'),
    'sk_axis': ('{name} — ось вращения', '{name} — rotation axis'),
    'name_bearing': ('Подшипник {name}', 'Bearing {name}'),
    'name_bearing_custom': ('{d}×{D}×{B}', '{d}×{D}×{B}'),
    'name_bearing_fix': ('Посадка {name}', 'Fit {name}'),
    'sk_section_of': ('{name} — сечение', '{name} — section'),
    'part_outer_ring': ('Наружное кольцо', 'Outer ring'),
    'part_inner_ring': ('Внутреннее кольцо', 'Inner ring'),
    'part_shield': ('Защитная шайба', 'Shield'),
    'part_shaft_washer': ('Тугое кольцо (на вал)', 'Shaft washer'),
    'part_housing_washer': ('Свободное кольцо (в корпус)', 'Housing washer'),
    'part_ball': ('Шарик', 'Ball'),
}


def detect(app):
    """'ru' for a Russian Fusion interface, otherwise 'en'; FUSIONGEARS_LANG overrides."""
    forced = os.environ.get('FUSIONGEARS_LANG', '').lower()
    if forced in ('ru', 'en'):
        return forced
    try:
        import adsk.core
        lang = app.preferences.generalPreferences.userLanguage
        return 'ru' if lang == adsk.core.UserLanguages.RussianLanguage else 'en'
    except Exception:
        return 'en'


def set_language(lang):
    global LANG
    LANG = 'ru' if lang == 'ru' else 'en'


def pick(pair):
    """The text of a (russian, english) pair for the current language."""
    return pair[0] if LANG == 'ru' else pair[1]


def t(key, **params):
    text = pick(TEXT[key])
    return text.format(**params) if params else text


def error(e):
    """Message for a gearmath.GearError."""
    params = dict(e.params)
    if 'what' in params:
        params['what'] = t('what_' + params['what'])
    try:
        return t('err_' + e.key, **params)
    except KeyError:
        return str(e)
