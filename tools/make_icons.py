"""Draws the toolbar icons (PNG, no dependencies). Usage: python tools/make_icons.py"""
import math, os, struct, zlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')

def png(path, size, inside):
    rows = b''
    for y in range(size):
        rows += b'\x00'
        for x in range(size):
            a = 0
            for sx in range(4):           # 4x4 supersampling
                for sy in range(4):
                    if inside((x + (sx + .5) / 4) / size * 2 - 1, (y + (sy + .5) / 4) / size * 2 - 1):
                        a += 1
            rows += bytes((60, 90, 140, a * 255 // 16))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(data)

def gear(x, y, teeth=10, skew=0.0):
    r, a = math.hypot(x, y), math.atan2(y, x) + skew * y
    edge = 0.72 + 0.2 * (math.cos(a * teeth) > 0)
    return 0.25 < r < edge

def bevel(x, y):
    # gear seen at an angle: squashed vertically, teeth on the top rim
    return gear(x, y * 1.6 + 0.2, 12) or (abs(x) < 0.55 - 0.3 * y and 0.1 < y < 0.75 and abs(x) > 0.15)

def check(x, y):
    # gear outline with a tick inside
    tick = (abs(y - (0.15 + 0.9 * (x + 0.35))) < 0.14 and -0.35 < x < -0.05) or            (abs(y - (0.42 - 1.2 * (x + 0.05))) < 0.14 and -0.08 < x < 0.42)
    return (gear(x, y, 10) and math.hypot(x, y) > 0.55) or tick


for cid, fn in (('FusionGears_Cylindrical', lambda x, y: gear(x, y, 10, 0.8 if y > 0 else -0.8)),
                ('FusionGears_Bevel', bevel), ('FusionGears_Check', check)):
    d = os.path.join(ROOT, cid)
    os.makedirs(d, exist_ok=True)
    for name, size in (('16x16.png', 16), ('32x32.png', 32), ('64x64.png', 64),
                       ('16x16@2x.png', 32), ('32x32@2x.png', 64)):
        png(os.path.join(d, name), size, fn)
