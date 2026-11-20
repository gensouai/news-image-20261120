#!/usr/bin/env python3
"""
Sum up 20 November 2026's world news in one image.

A single-file, standard-library-only Python 3 program.
Running it writes /output/entry.png (1024x1024, deterministic:
two runs produce byte-identical output).

The five stories, as reported on 20 Nov 2026:
  1. Russia's massive overnight missile and drone barrage on
     Ukraine (about 100 missiles, 404 drones) kills eight,
     six of them in Kyiv, and damages three Dnipro bridges.
  2. Two Russian Kh-101 cruise missiles and a jet-powered drone
     cross into Poland and crash; PM Tusk calls it a provocation
     and NATO jets scramble.
  3. The UK and the EU sign a Brexit reset deal in Brussels:
     food checks end, emissions trading links up, and 100,000
     young people a year can live and work across the Channel.
  4. Trump puts off any decision on new Iran strikes until 2027
     as the Senate backs him 51-48; the war's cost hits $48.3bn.
  5. Anthropic (ANT) slides about 10% on its second day of
     trading, to about $87 from a $97.17 debut close, in a
     broad AI selloff.
"""

import os
import struct
import zlib

W = 1024
H = 1024
PX = bytearray(W * H * 3)

# ---------------------------------------------------------------- canvas

def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PX[i] = c[0]
        PX[i + 1] = c[1]
        PX[i + 2] = c[2]

def fill_rect(x0, y0, x1, y1, c):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(W - 1, x1); y1 = min(H - 1, y1)
    if x1 < x0 or y1 < y0:
        return
    row = bytes(c) * (x1 - x0 + 1)
    for y in range(y0, y1 + 1):
        i = (y * W + x0) * 3
        PX[i:i + len(row)] = row

def line(x0, y0, x1, y1, c, th=1):
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = th // 2
    while True:
        fill_rect(x0 - r, y0 - r, x0 + r, y0 + r, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy

def dashed_line(x0, y0, x1, y1, c, th=2, dash=14, gap=10):
    import math
    dist = math.hypot(x1 - x0, y1 - y0)
    if dist == 0:
        return
    ux = (x1 - x0) / dist; uy = (y1 - y0) / dist
    t = 0.0
    while t < dist:
        t2 = min(t + dash, dist)
        line(int(x0 + ux * t), int(y0 + uy * t),
             int(x0 + ux * t2), int(y0 + uy * t2), c, th)
        t += dash + gap

def circle(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        rem = r * r - dy * dy
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        fill_rect(cx - dx, y, cx + dx, y, c)

def ring(cx, cy, r, c, th=3):
    for y in range(cy - r - th, cy + r + th + 1):
        for x in range(cx - r - th, cx + r + th + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if (r - th) ** 2 <= d2 <= (r + th) ** 2:
                set_px(x, y, c)

def poly(points, c):
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            xa, ya = points[i]
            xb, yb = points[(i + 1) % n]
            if ya == yb:
                continue
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[i]), y, int(xs[i + 1]), y, c)

# ------------------------------------------------------------------ font
# 5x7 bitmap font, rows top to bottom, '#' = ink.

FONT = {
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"],
    'Y': ["#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    '.': [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ',': [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    ':': [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    '-': [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", ".#...", "#...."],
    '$': ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    '+': [".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
}

def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0

def draw_text(x, y, s, scale, c):
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == '#':
                    fill_rect(x + gx * scale, y + gy * scale,
                              x + gx * scale + scale - 1,
                              y + gy * scale + scale - 1, c)
        x += 6 * scale

def draw_text_center(cx, y, s, scale, c):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, c)

def draw_text_right(xr, y, s, scale, c):
    draw_text(xr - text_w(s, scale), y, s, scale, c)

# ---------------------------------------------------------------- colors

PAPER = (246, 243, 236)
INK = (22, 22, 22)
WHITE = (255, 255, 252)
RED = (178, 34, 52)
NAVY = (30, 58, 110)
GOLD = (212, 160, 32)
GREEN = (20, 138, 72)
GRAY = (110, 110, 110)
LGRAY = (225, 224, 218)

def lcg(seed):
    while True:
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        yield seed

# ------------------------------------------------------------ panel frame

def panel(x, y, w, h, tag):
    fill_rect(x, y, x + w - 1, y + h - 1, WHITE)
    for t in range(3):
        fill_rect(x + t, y + t, x + w - 1 - t, y + t, INK)
        fill_rect(x + t, y + h - 1 - t, x + w - 1 - t, y + h - 1 - t, INK)
        fill_rect(x + t, y + t, x + t, y + h - 1 - t, INK)
        fill_rect(x + w - 1 - t, y + t, x + w - 1 - t, y + h - 1 - t, INK)
    tw = text_w(tag, 2) + 16
    fill_rect(x + 12, y + 12, x + 12 + tw, y + 12 + 26, RED)
    draw_text(x + 20, y + 18, tag, 2, WHITE)

def headline(x, y, lines, caption):
    ly = y
    for ln in lines:
        draw_text(x, ly, ln, 4, INK)
        ly += 32
    draw_text(x, ly + 2, caption, 2, RED)

# ------------------------------------------------------------- story art

def art_kyiv(x, y, w, h):
    import math
    # dawn sky under attack
    stops = [(16, 22, 48), (34, 44, 78), (86, 74, 96),
             (168, 96, 74), (226, 140, 76)]
    band = h // len(stops)
    for i, col in enumerate(stops):
        fill_rect(x, y + i * band, x + w - 1, y + (i + 1) * band + 1, col)
    base = y + h - 44
    # far skyline silhouette
    rng = lcg(11220)
    bx = x + 4
    while bx < x + w - 24:
        bw = 22 + next(rng) % 26
        bh = 26 + next(rng) % 30
        fill_rect(bx, base - bh, bx + bw, base, (18, 20, 34))
        bx += bw + 4
    # golden cathedral dome
    dx = x + 150
    fill_rect(dx - 20, base - 52, dx + 20, base, (18, 20, 34))
    fill_rect(dx - 13, base - 62, dx + 13, base - 52, GOLD)
    circle(dx, base - 62, 11, GOLD)
    fill_rect(dx - 2, base - 84, dx + 2, base - 72, GOLD)
    circle(dx, base - 86, 3, GOLD)
    # the Dnipro river
    fill_rect(x, base, x + w - 1, y + h - 1, (26, 52, 88))
    fill_rect(x, base, x + w - 1, base + 2, (90, 130, 170))
    # bridge: two pylons, deck with the middle span down
    deck_y = base + 12
    fill_rect(x + 30, deck_y - 26, x + 38, deck_y + 18, (12, 14, 22))
    fill_rect(x + w - 70, deck_y - 26, x + w - 62, deck_y + 18, (12, 14, 22))
    fill_rect(x + 10, deck_y, x + 190, deck_y + 6, (12, 14, 22))
    fill_rect(x + 250, deck_y, x + w - 20, deck_y + 6, (12, 14, 22))
    fill_rect(x + 10, deck_y, x + 190, deck_y + 1, (150, 160, 170))
    fill_rect(x + 250, deck_y, x + w - 20, deck_y + 1, (150, 160, 170))
    line(x + 192, deck_y + 4, x + 248, deck_y + 26, (12, 14, 22), 6)
    line(x + 34, deck_y - 26, x + 190, deck_y, (200, 200, 190), 1)
    line(x + w - 66, deck_y - 26, x + 250, deck_y, (200, 200, 190), 1)
    # incoming missile trails
    dashed_line(x + 60, y + 8, x + 210, y + 74, (255, 220, 160), 2)
    dashed_line(x + w - 40, y + 4, x + 300, y + 66, (255, 220, 160), 2)
    dashed_line(x + 250, y + 2, x + 330, y + 52, (255, 220, 160), 2)
    # explosion starbursts
    for ex, ey, r in ((x + 214, y + 78, 16), (x + 306, y + 60, 12),
                      (x + 120, y + 96, 10)):
        circle(ex, ey, r, (255, 170, 60))
        circle(ex, ey, r * 2 // 3, (255, 220, 120))
        for ang in range(0, 360, 45):
            exx = ex + int((r + 8) * math.cos(math.radians(ang)))
            eyy = ey + int((r + 8) * math.sin(math.radians(ang)))
            line(ex, ey, exx, eyy, (255, 170, 60), 3)
    # drones: small dark crosses
    for ddx, ddy in ((x + 70, y + 34), (x + 380, y + 26), (x + 180, y + 18)):
        line(ddx - 8, ddy, ddx + 8, ddy, (10, 10, 14), 3)
        line(ddx, ddy - 5, ddx, ddy + 5, (10, 10, 14), 3)

def art_poland(x, y, w, h):
    # morning sky
    fill_rect(x, y, x + w - 1, y + h - 1, (168, 200, 232))
    fill_rect(x, y, x + w - 1, y + 40, (140, 182, 224))
    base = y + h - 52
    # distant forest
    rng = lcg(31120)
    bx = x
    while bx < x + w:
        th_ = 18 + next(rng) % 16
        poly([(bx, base), (bx + 14, base - th_), (bx + 28, base)], (52, 96, 62))
        bx += 20
    # field
    fill_rect(x, base, x + w - 1, y + h - 1, (116, 164, 84))
    fill_rect(x, base, x + w - 1, base + 3, (86, 128, 62))
    # two jets with contrails, top-left
    for jx, jy in ((x + 36, y + 26), (x + 108, y + 48)):
        dashed_line(jx - 30, jy + 8, jx - 2, jy + 2, (250, 250, 250), 2,
                    dash=6, gap=5)
        poly([(jx, jy), (jx + 34, jy + 3), (jx + 44, jy + 8), (jx + 34, jy + 11),
              (jx, jy + 9)], (52, 58, 68))
        poly([(jx + 12, jy + 4), (jx + 24, jy - 8), (jx + 30, jy + 4)],
             (52, 58, 68))
        poly([(jx + 12, jy + 8), (jx + 24, jy + 18), (jx + 30, jy + 9)],
             (52, 58, 68))
    # cruise missile diving in, smoke trail behind
    dashed_line(x + 402, y + 8, x + 356, y + 40, (245, 245, 245), 5,
                dash=7, gap=6)
    line(x + 318, y + 84, x + 352, y + 44, (216, 220, 226), 9)
    poly([(x + 318, y + 84), (x + 306, y + 92), (x + 312, y + 74)],
         (150, 30, 30))
    poly([(x + 352, y + 44), (x + 366, y + 30), (x + 358, y + 52)],
         (255, 150, 50))
    # impact flash + smoke where it came down
    circle(x + 306, base + 4, 15, (250, 240, 200))
    circle(x + 306, base + 4, 9, (255, 200, 90))
    circle(x + 292, base - 12, 10, (168, 168, 168))
    circle(x + 318, base - 18, 12, (150, 150, 150))
    circle(x + 306, base - 30, 9, (178, 178, 178))
    # Polish flag on a pole, right
    px = x + w - 52
    line(px, y + 58, px, base + 20, (90, 90, 90), 4)
    fill_rect(px + 3, y + 60, px + 45, y + 80, (255, 255, 255))
    fill_rect(px + 3, y + 81, px + 45, y + 101, (220, 20, 60))
    line(px + 3, y + 60, px + 45, y + 60, (120, 120, 120), 1)

def draw_flag_eu(x, y, w, h):
    import math
    fill_rect(x, y, x + w - 1, y + h - 1, (0, 51, 153))
    cx, cy = x + w // 2, y + h // 2
    r_out = h // 3
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        sx = cx + int(r_out * math.cos(ang))
        sy = cy + int(r_out * math.sin(ang))
        circle(sx, sy, 4, (255, 204, 0))

def draw_flag_uk(x, y, w, h):
    fill_rect(x, y, x + w - 1, y + h - 1, (1, 33, 105))
    line(x, y, x + w - 1, y + h - 1, WHITE, 12)
    line(x, y + h - 1, x + w - 1, y, WHITE, 12)
    line(x, y, x + w - 1, y + h - 1, (200, 16, 46), 4)
    line(x, y + h - 1, x + w - 1, y, (200, 16, 46), 4)
    fill_rect(x + w // 2 - 14, y, x + w // 2 + 14, y + h - 1, WHITE)
    fill_rect(x, y + h // 2 - 14, x + w - 1, y + h // 2 + 14, WHITE)
    fill_rect(x + w // 2 - 8, y, x + w // 2 + 8, y + h - 1, (200, 16, 46))
    fill_rect(x, y + h // 2 - 8, x + w - 1, y + h // 2 + 8, (200, 16, 46))

def art_euuk(x, y, w, h):
    # pale sky
    fill_rect(x, y, x + w - 1, y + h - 1, (206, 224, 240))
    # channel water at the bottom
    fill_rect(x, y + h - 34, x + w - 1, y + h - 1, (58, 102, 156))
    # flags on poles: EU left, UK right
    line(x + 26, y + 14, x + 26, y + h - 30, (90, 90, 90), 4)
    draw_flag_eu(x + 30, y + 16, 132, 88)
    line(x + w - 30, y + 14, x + w - 30, y + h - 30, (90, 90, 90), 4)
    draw_flag_uk(x + w - 162, y + 16, 132, 88)
    # a bridge rebuilt between the two banks
    deck = y + h - 40
    fill_rect(x + 8, deck, x + 190, deck + 7, (120, 96, 60))
    fill_rect(x + w - 198, deck, x + w - 9, deck + 7, (120, 96, 60))
    line(x + 190, deck + 3, x + w - 198, deck + 3, (120, 96, 60), 6)
    for tx in (x + 120, x + w - 128):
        fill_rect(tx, deck - 34, tx + 9, deck, (120, 96, 60))
        line(tx + 4, deck - 34, x + 190, deck, (90, 74, 46), 2)
        line(tx + 4, deck - 34, x + w - 198, deck, (90, 74, 46), 2)
    # summit city, in the gap between the flags and the bridge
    draw_text_center(x + w // 2, y + 108, "BRUSSELS", 2, NAVY)

def art_iran(x, y, w, h):
    fill_rect(x, y, x + w - 1, y + h - 1, (24, 34, 64))
    rnd = lcg(2027)
    for _ in range(50):
        circle(x + next(rnd) % w, y + next(rnd) % (h - 60), 1, (220, 226, 240))
    cx = x + 140
    base = y + h - 14
    # steps and terrace
    fill_rect(cx - 120, base - 10, cx + 120, base, (226, 228, 232))
    fill_rect(cx - 104, base - 44, cx + 104, base - 10, (240, 241, 244))
    # columns
    for i in range(7):
        colx = cx - 96 + i * 32
        fill_rect(colx, base - 44, colx + 10, base - 12, (204, 207, 214))
    # entablature
    fill_rect(cx - 112, base - 56, cx + 112, base - 44, (240, 241, 244))
    # stepped dome
    fill_rect(cx - 62, base - 74, cx + 62, base - 56, (198, 203, 212))
    fill_rect(cx - 44, base - 90, cx + 44, base - 74, (198, 203, 212))
    fill_rect(cx - 26, base - 102, cx + 26, base - 90, (198, 203, 212))
    fill_rect(cx - 3, base - 116, cx + 3, base - 102, (198, 203, 212))
    circle(cx, base - 121, 4, GOLD)
    # the deferred year, large
    draw_text(x + 282, y + 40, "2027", 7, GOLD)
    draw_text(x + 284, y + 108, "DECISION", 2, (220, 226, 240))
    draw_text(x + 284, y + 124, "DELAYED", 2, (220, 226, 240))

def art_ant(cx, cy, w, h):
    # chart box
    fill_rect(cx, cy, cx + w - 1, cy + h - 1, WHITE)
    for t in range(2):
        fill_rect(cx + t, cy + t, cx + w - 1 - t, cy + t, INK)
        fill_rect(cx + t, cy + h - 1 - t, cx + w - 1 - t, cy + h - 1 - t, INK)
        fill_rect(cx + t, cy + t, cx + t, cy + h - 1 - t, INK)
        fill_rect(cx + w - 1 - t, cy + t, cx + w - 1 - t, cy + h - 1 - t, INK)
    base = cy + h - 22
    # bars, fading as the price falls
    for i, bh in enumerate((92, 104, 78, 60, 44, 34)):
        bx = cx + 22 + i * 42
        fill_rect(bx, base - bh, bx + 24, base, (233, 192, 192))
    # the $83 offer price, dashed
    dashed_line(cx + 14, base - 28, cx + w - 14, base - 28, GRAY, 2)
    draw_text(cx + 16, base - 46, "$83 IPO", 2, GRAY)
    # falling line: debut high, debut close, day two
    pts = [(cx + 96, base - 104), (cx + 146, base - 96), (cx + 196, base - 74),
           (cx + 244, base - 82), (cx + 292, base - 52), (cx + 328, base - 40)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 5)
    for px, py in pts:
        circle(px, py, 5, RED)
    # arrow head, pointing down
    poly([(pts[-1][0] + 13, pts[-1][1] + 15), (pts[-1][0] - 5, pts[-1][1] + 3),
          (pts[-1][0] + 3, pts[-1][1] - 12)], RED)
    draw_text(cx + 16, cy + 10, "ANT", 3, RED)
# ---------------------------------------------------------------- layout

def build():
    fill_rect(0, 0, W - 1, H - 1, PAPER)
    # header
    draw_text_center(512, 30, "THE WORLD ON ONE PAGE", 3, RED)
    draw_text_center(512, 62, "20 NOVEMBER 2026", 9, INK)
    fill_rect(24, 140, 1000, 143, INK)
    fill_rect(24, 148, 1000, 149, INK)
    draw_text(24, 156, "FRIDAY", 2, INK)
    draw_text_right(1000, 156, "FIVE TOP STORIES", 2, INK)
    draw_text_center(512, 156, "WORLD NEWS IN A SINGLE IMAGE", 2, GRAY)

    PW, PH = 476, 306
    X1, X2 = 24, 524
    Y1, Y2 = 186, 504

    # 1 - Kyiv barrage
    panel(X1, Y1, PW, PH, "UKRAINE WAR")
    art_kyiv(X1 + 10, Y1 + 46, PW - 20, 164)
    headline(X1 + 12, Y1 + 218,
             ["RUSSIA BOMBARDS", "KYIV: 8 KILLED"],
             "3 DNIPRO BRIDGES HIT - 404 DRONES")
    # 2 - Poland / NATO
    panel(X2, Y1, PW, PH, "NATO ALERT")
    art_poland(X2 + 10, Y1 + 46, PW - 20, 164)
    headline(X2 + 12, Y1 + 218,
             ["RUSSIAN MISSILES", "FALL IN POLAND"],
             "TUSK: A PROVOCATION - JETS SCRAMBLED")
    # 3 - UK-EU reset
    panel(X1, Y2, PW, PH, "BREXIT RESET")
    art_euuk(X1 + 10, Y2 + 46, PW - 20, 164)
    headline(X1 + 12, Y2 + 218,
             ["UK AND EU SIGN", "RESET DEAL"],
             "FOOD CHECKS END - 100,000 YOUTH VISAS")
    # 4 - Iran decision delayed
    panel(X2, Y2, PW, PH, "IRAN WAR")
    art_iran(X2 + 10, Y2 + 46, PW - 20, 164)
    headline(X2 + 12, Y2 + 218,
             ["TRUMP DELAYS IRAN", "DECISION TO 2027"],
             "SENATE BACKS HIM 51-48 - COST $48.3BN")
    # 5 - Anthropic day two (full-width strip)
    SY = 822
    panel(24, SY, 976, 178, "MARKETS")
    draw_text(36, SY + 52, "ANTHROPIC SLIDES", 4, INK)
    draw_text(36, SY + 86, "10 PCT ON DAY TWO", 4, INK)
    draw_text(36, SY + 128, "ANT AT $87 VS $97 DEBUT CLOSE - AI SELLOFF", 2, RED)
    art_ant(636, SY + 14, 350, 150)

# ------------------------------------------------------------------- png

def save_png(path):
    raw = bytearray()
    rowlen = W * 3
    for y in range(H):
        raw.append(0)
        raw += PX[y * rowlen:(y + 1) * rowlen]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

def main():
    build()
    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
    except OSError:
        out = os.path.join("output", "entry.png")
        os.makedirs("output", exist_ok=True)
    save_png(out)

if __name__ == "__main__":
    main()
