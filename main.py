#!/usr/bin/env python3
"""
Sum up 20 November 2026's world news in one image.

Draws a newspaper front page (1024x1024 PNG) using only the Python
standard library: a tiny RGB canvas, a hand-made 5x7 bitmap font and a
minimal PNG encoder.  No network, no randomness without a fixed seed,
so two runs produce byte-identical output.

Writes /output/entry.png, falling back to ./output/entry.png when
/output is not writable.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs.  Each glyph is 7 rows; each row is an int whose
# 5 low bits are the pixels, bit 4 (16) being the leftmost column.

FONT = {
    ' ': (0, 0, 0, 0, 0, 0, 0),
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (14, 17, 16, 16, 16, 17, 14),
    'D': (28, 18, 17, 17, 17, 18, 28),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (14, 17, 16, 23, 17, 17, 15),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 17, 25, 21, 19, 17, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 21, 10),
    'X': (17, 10, 4, 4, 4, 10, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    'a': (0, 0, 14, 1, 15, 17, 15),
    'b': (16, 16, 22, 25, 17, 17, 30),
    'c': (0, 0, 14, 17, 16, 17, 14),
    'd': (1, 1, 13, 19, 17, 17, 15),
    'e': (0, 0, 14, 17, 31, 16, 14),
    'f': (6, 9, 8, 30, 8, 8, 8),
    'g': (0, 15, 17, 17, 15, 1, 14),
    'h': (16, 16, 22, 25, 17, 17, 17),
    'i': (4, 0, 12, 4, 4, 4, 14),
    'j': (2, 0, 6, 2, 2, 18, 12),
    'k': (16, 16, 18, 20, 24, 20, 18),
    'l': (12, 4, 4, 4, 4, 4, 14),
    'm': (0, 0, 26, 21, 21, 21, 21),
    'n': (0, 0, 22, 25, 17, 17, 17),
    'o': (0, 0, 14, 17, 17, 17, 14),
    'p': (0, 0, 30, 17, 30, 16, 16),
    'q': (0, 0, 13, 19, 15, 1, 3),
    'r': (0, 0, 22, 25, 16, 16, 16),
    's': (0, 0, 15, 16, 14, 1, 30),
    't': (8, 8, 28, 8, 8, 17, 6),
    'u': (0, 0, 17, 17, 17, 19, 13),
    'v': (0, 0, 17, 17, 17, 10, 4),
    'w': (0, 0, 17, 21, 21, 21, 10),
    'x': (0, 0, 17, 10, 4, 10, 17),
    'y': (0, 0, 17, 17, 15, 1, 14),
    'z': (0, 0, 31, 2, 4, 8, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 6, 8, 16, 31),
    '3': (31, 2, 4, 2, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (6, 8, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 8, 8, 8),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 13, 1, 2, 12),
    '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    '-': (0, 0, 0, 14, 0, 0, 0),
    ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 4, 8),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 6, 4, 0, 4),
    '$': (4, 15, 20, 14, 5, 30, 4),
    '%': (25, 26, 2, 4, 8, 11, 19),
    '+': (0, 4, 4, 14, 4, 4, 0),
    '/': (1, 2, 2, 4, 8, 8, 16),
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    '&': (12, 18, 20, 8, 21, 18, 13),
    '*': (0, 4, 21, 14, 21, 4, 0),
    '=': (0, 0, 14, 0, 14, 0, 0),
    '•': (0, 0, 0, 12, 12, 0, 0),
}

_TRANSLATE = {
    '‘': "'", '’': "'", '“': '"', '”': '"',
    '–': '-', '—': '-', '…': '...', ' ': ' ',
}


def sanitize(text):
    """Map fancy punctuation onto glyphs the font actually has."""
    out = []
    for ch in text:
        rep = _TRANSLATE.get(ch, ch)
        for c in rep:
            out.append(c if c in FONT else ' ')
    return ''.join(out)


def text_width(text, scale):
    """Pixel width of a string at the given integer scale."""
    text = sanitize(text)
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    current = ''
    for word in sanitize(text).split(' '):
        if not word:
            continue
        trial = word if not current else current + ' ' + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------- rng
class Rng:
    """Tiny deterministic linear congruential generator."""

    def __init__(self, seed):
        self.state = seed & 0x7FFFFFFF

    def next(self, lo, hi):
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return lo + self.state % (hi - lo + 1)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.px = bytearray(bg) * (width * height)

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.w, int(x) + int(w))
        y1 = min(self.h, int(y) + int(h))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect_outline(self, x, y, w, h, color, thick=1):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def gradient_y(self, x, y, w, h, top, bottom):
        for i in range(h):
            t = i / max(1, h - 1)
            col = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
            self.fill_rect(x, y + i, w, 1, col)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, 1px."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, color, width):
        steps = max(abs(int(x1 - x0)), abs(int(y1 - y0)), 1)
        r = max(1, int(round(width / 2)))
        for i in range(steps + 1):
            t = i / steps
            self.circle(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, color)

    def circle(self, cx, cy, r, color):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = math.isqrt(r * r - dy * dy)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def poly(self, pts, color):
        """Scanline polygon fill (even-odd)."""
        pts = [(float(px), float(py)) for px, py in pts]
        ys = [p[1] for p in pts]
        y_lo = max(0, int(min(ys)))
        y_hi = min(self.h - 1, int(max(ys)))
        n = len(pts)
        for yy in range(y_lo, y_hi + 1):
            nodes = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= yy < y2) or (y2 <= yy < y1):
                    nodes.append(x1 + (yy - y1) * (x2 - x1) / (y2 - y1))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                self.fill_rect(int(nodes[i]), yy,
                               int(nodes[i + 1]) - int(nodes[i]) + 1, 1, color)

    # ------------------------------------------------------------ text
    def text(self, x, y, s, scale, color, bold=False):
        s = sanitize(s)
        off = max(1, scale // 2) if bold else 0
        cx = int(x)
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for r in range(7):
                bits = glyph[r]
                for col in range(5):
                    if bits >> (4 - col) & 1:
                        self.fill_rect(cx + col * scale, y + r * scale,
                                       scale, scale, color)
                        if bold:
                            self.fill_rect(cx + col * scale + off, y + r * scale,
                                           scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, cx, y, s, scale, color, bold=False):
        return self.text(cx - text_width(s, scale) // 2, y, s, scale, color, bold)

    def text_right(self, right, y, s, scale, color, bold=False):
        return self.text(right - text_width(s, scale), y, s, scale, color, bold)


# ---------------------------------------------------------------- colours
PAPER = (246, 241, 231)
INK = (26, 26, 30)
BODY = (44, 44, 48)
ACCENT = (166, 30, 36)
RULE = (26, 26, 30)


def burst(c, cx, cy, r):
    """Explosion star: spiky polygon + hot core."""
    pts = []
    for i in range(16):
        ang = math.pi * i / 8.0
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    c.poly(pts, (255, 138, 42))
    c.circle(cx, cy, max(2, r // 2), (255, 206, 92))
    c.circle(cx, cy, 3, (255, 246, 220))


# ---------------------------------------------------------------- scenes
def scene_ukraine(c, x, y, w, h):
    """Night sky, missile trails, skyline, river and a bridge."""
    rng = Rng(20261120)
    c.gradient_y(x, y, w, h, (10, 14, 40), (34, 44, 84))
    for _ in range(70):
        sx = rng.next(x, x + w - 2)
        sy = rng.next(y, y + h - 60)
        c.fill_rect(sx, sy, rng.next(1, 2), 1, (210, 216, 235))
    # crescent moon
    c.circle(x + w - 96, y + 30, 15, (232, 228, 196))
    c.circle(x + w - 87, y + 23, 13, (26, 35, 70))
    # missile trails (glow pass, then hot core)
    trails = [((x + w - 30, y + 4), (x + 300, y + 102)),
              ((x + w - 150, y + 0), (x + 470, y + 98)),
              ((x + w - 290, y + 8), (x + 610, y + 104))]
    for (ax, ay), (bx, by) in trails:
        c.thick_line(ax, ay, bx, by, (198, 108, 48), 5)
    for (ax, ay), (bx, by) in trails:
        c.thick_line(ax, ay, bx, by, (255, 220, 160), 2)
    # skyline
    base = y + h - 24
    bx = x
    while bx < x + w - 20:
        bw = rng.next(24, 50)
        bh = rng.next(16, 42)
        c.fill_rect(bx, base - bh, bw, bh, (9, 10, 17))
        for _ in range(rng.next(0, 4)):
            wx = rng.next(bx + 3, bx + bw - 5)
            wy = rng.next(base - bh + 3, base - 6)
            c.fill_rect(wx, wy, 2, 3, (255, 186, 92))
        bx += bw + rng.next(2, 7)
    # river
    c.gradient_y(x, base, w, 24, (14, 26, 52), (6, 12, 28))
    for _ in range(26):
        rx = rng.next(x + 4, x + w - 20)
        ry = rng.next(base + 4, y + h - 3)
        c.fill_rect(rx, ry, rng.next(6, 16), 1, (70, 100, 150))
    # bridge: deck, posts, truss diagonals
    deck = base + 2
    c.thick_line(x, deck, x + w, deck, (22, 28, 42), 4)
    px = x + 10
    while px < x + w - 6:
        c.fill_rect(px, deck - 12, 3, 12, (22, 28, 42))
        c.line(px + 1, deck - 12, px + 29, deck, (22, 28, 42))
        px += 58
    # impacts
    for _, (bx2, by2) in trails:
        burst(c, bx2, by2, 15)


def scene_poland(c, x, y, w, h):
    """Day sky over fields: a falling missile, a jet, the Polish flag."""
    c.gradient_y(x, y, w, 46, (116, 168, 218), (196, 220, 242))
    c.fill_rect(x, y + 46, w, h - 46, (88, 142, 64))
    c.fill_rect(x, y + 54, w, 2, (70, 118, 52))
    c.fill_rect(x, y + 62, w, 2, (70, 118, 52))
    c.circle(x + 120, y + 12, 7, (255, 240, 180))
    # NATO jet silhouette, top left
    jet = [(0, 4), (14, 0), (30, 2), (38, 6), (30, 7), (40, 12),
           (30, 10), (14, 9), (6, 13), (2, 9)]
    c.poly([(x + 30 + dx, y + 6 + dy) for dx, dy in jet], (44, 48, 56))
    # small quadcopter drone, centre sky
    dx0, dy0 = x + 214, y + 18
    c.line(dx0 - 8, dy0 - 5, dx0 + 8, dy0 + 5, (44, 48, 56))
    c.line(dx0 - 8, dy0 + 5, dx0 + 8, dy0 - 5, (44, 48, 56))
    c.circle(dx0, dy0, 3, (44, 48, 56))
    for rx, ry in ((-9, -6), (9, -6), (-9, 6), (9, 6)):
        c.circle(dx0 + rx, dy0 + ry, 2, (44, 48, 56))
    # smoke puffs trailing the missile
    tail = (x + w - 92, y + 18)
    head = (x + w - 152, y + 42)
    for i in range(7):
        t = i / 6.0
        sx = tail[0] + (x + w - 30 - tail[0]) * t + 6 * math.sin(t * 5)
        sy = tail[1] + (y + 2 - tail[1]) * t - 4 * t
        c.circle(int(sx), int(sy), 3 + i, (208, 213, 220))
    # flame, fins, body, nose
    c.poly([(tail[0], tail[1]), (tail[0] + 18, tail[1] - 6),
            (tail[0] + 20, tail[1] + 6)], (255, 150, 50))
    c.poly([(tail[0], tail[1]), (tail[0] + 12, tail[1] - 11),
            (tail[0] + 18, tail[1] + 1)], (90, 90, 100))
    c.poly([(tail[0], tail[1]), (tail[0] + 3, tail[1] + 13),
            (tail[0] + 15, tail[1] + 9)], (90, 90, 100))
    c.thick_line(tail[0], tail[1], head[0], head[1], (148, 150, 158), 6)
    c.circle(head[0], head[1], 4, (104, 104, 114))
    # Polish flag on a pole
    pole_x = x + w - 42
    c.fill_rect(pole_x, y + 6, 2, 48, (60, 60, 60))
    c.fill_rect(pole_x + 2, y + 6, 30, 9, (245, 245, 245))
    c.fill_rect(pole_x + 2, y + 15, 30, 9, (206, 40, 48))
    c.rect_outline(pole_x + 2, y + 6, 30, 18, (120, 120, 120), 1)


def scene_ukeu(c, x, y, w, h):
    """EU stars beside a simplified Union Jack, a golden bridge between."""
    half = w // 2
    c.fill_rect(x, y, half, h, (18, 38, 118))
    c.fill_rect(x + half, y, w - half, h, (30, 34, 96))
    # EU circle of stars
    ecx, ecy = x + half // 2, y + h // 2
    for i in range(12):
        ang = -math.pi / 2 + i * math.pi / 6
        c.circle(int(ecx + 17 * math.cos(ang)), int(ecy + 17 * math.sin(ang)),
                 2, (255, 214, 64))
    c.circle(ecx, ecy, 2, (255, 214, 64))
    # Union Jack (simplified): white diagonals, white cross, red cross
    ux, uw = x + half, w - half
    c.thick_line(ux, y, ux + uw, y + h, (240, 240, 240), 6)
    c.thick_line(ux + uw, y, ux, y + h, (240, 240, 240), 6)
    c.fill_rect(ux + uw // 2 - 6, y, 12, h, (240, 240, 240))
    c.fill_rect(ux, y + h // 2 - 6, uw, 12, (240, 240, 240))
    c.fill_rect(ux + uw // 2 - 3, y, 7, h, (198, 40, 48))
    c.fill_rect(ux, y + h // 2 - 3, uw, 7, (198, 40, 48))
    # golden bridge arc across the divide
    cx = x + half
    prev = None
    for i in range(21):
        t = i / 20.0
        px = cx - 52 + 104 * t
        py = y + h - 8 - 30 * 4 * t * (1 - t)
        if prev is not None:
            c.thick_line(prev[0], prev[1], px, py, (232, 182, 66), 3)
        prev = (px, py)
    c.fill_rect(cx - 31, y + h - 26, 3, 18, (232, 182, 66))
    c.fill_rect(cx + 28, y + h - 26, 3, 18, (232, 182, 66))
    c.thick_line(cx - 56, y + h - 8, cx + 56, y + h - 8, (232, 182, 66), 3)


def scene_iran(c, x, y, w, h):
    """Capitol dome on the left; a 2027 calendar page on the right."""
    c.gradient_y(x, y, w, h, (198, 214, 236), (238, 240, 232))
    c.fill_rect(x, y + h - 8, w, 8, (168, 172, 150))
    cx = x + 86
    c.circle(cx, y + 40, 25, (110, 120, 142))            # dome rim
    c.circle(cx, y + 40, 24, (158, 170, 196))            # dome
    c.fill_rect(cx - 1, y + 8, 3, 10, (90, 96, 110))     # spire
    c.poly([(cx + 2, y + 8), (cx + 13, y + 10), (cx + 2, y + 13)], (200, 50, 55))
    c.fill_rect(x + 30, y + 40, 112, 20, (198, 204, 218))  # body hides dome base
    for lx in range(x + 40, x + 136, 13):
        c.fill_rect(lx, y + 43, 2, 14, (110, 120, 142))  # columns
    c.fill_rect(x + 22, y + 58, 128, 5, (150, 158, 176))  # steps
    # calendar
    kx, ky, kw, kh = x + w - 158, y + 6, 104, 54
    c.fill_rect(kx, ky, kw, kh, (250, 250, 248))
    c.rect_outline(kx, ky, kw, kh, (120, 120, 120), 1)
    c.fill_rect(kx, ky, kw, 12, (198, 44, 48))
    c.fill_rect(kx + 16, ky + 2, 5, 8, (90, 90, 90))
    c.fill_rect(kx + kw - 21, ky + 2, 5, 8, (90, 90, 90))
    c.text_centered(kx + kw // 2, ky + 22, '2027', 4, INK, bold=True)


def scene_anthropic(c, x, y, w, h):
    """Dark trading screen: grid, falling red chart line, -10% tag."""
    c.fill_rect(x, y, w, h, (13, 17, 25))
    for gx in range(x + 38, x + w, 38):
        c.fill_rect(gx, y, 1, h, (30, 38, 52))
    for gy in range(y + 17, y + h, 17):
        c.fill_rect(x, gy, w, 1, (30, 38, 52))
    pts = [(x + 12, y + 12), (x + 54, y + 18), (x + 96, y + 15),
           (x + 138, y + 28), (x + 180, y + 33), (x + 222, y + 45),
           (x + 264, y + 52), (x + 300, y + 58)]
    for a, b in zip(pts, pts[1:]):
        c.thick_line(a[0], a[1], b[0], b[1], (96, 30, 30), 6)
    for a, b in zip(pts, pts[1:]):
        c.thick_line(a[0], a[1], b[0], b[1], (236, 84, 74), 3)
    # arrow head at the end of the line
    ex, ey = pts[-1]
    c.poly([(ex - 4, ey - 8), (ex + 16, ey + 6), (ex - 6, ey + 8)], (236, 84, 74))
    c.fill_rect(x, y + h - 2, w, 2, (90, 100, 116))
    c.text(x + w - 96, y + 8, '-10%', 3, (255, 96, 84), bold=True)
    c.text(x + 14, y + 27, '$97', 1, (150, 160, 175))
    c.text(x + 248, y + 28, '$87', 1, (150, 160, 175))


# ---------------------------------------------------------------- panels
def panel(c, x, y, w, h, scene, scene_h, kicker, headline, summary, head_scale):
    c.rect_outline(x, y, w, h, RULE, 2)
    sx, sy, sw = x + 10, y + 10, w - 20
    scene(c, sx, sy, sw, scene_h)
    c.fill_rect(sx, sy + scene_h + 5, sw, 1, RULE)
    ty = sy + scene_h + 12
    c.fill_rect(x + 10, ty + 3, 8, 8, ACCENT)
    c.text(x + 24, ty, kicker, 2, ACCENT, bold=True)
    ty += 22
    head_lh = 7 * head_scale + (8 if head_scale >= 4 else 5)
    for ln in wrap_text(headline, head_scale, sw):
        c.text(x + 10, ty, ln, head_scale, INK, bold=True)
        ty += head_lh
    ty += 4
    for ln in wrap_text(summary, 2, sw):
        c.text(x + 10, ty, ln, 2, BODY)
        ty += 19


# ---------------------------------------------------------------- page
def build_page():
    c = Canvas(W, H, PAPER)
    c.rect_outline(12, 12, W - 24, H - 24, RULE, 1)
    # masthead
    c.fill_rect(36, 30, W - 72, 4, RULE)
    c.fill_rect(36, 38, W - 72, 1, RULE)
    c.text_centered(W // 2, 52, 'THE WORLD TODAY', 9, INK, bold=True)
    c.fill_rect(36, 124, W - 72, 1, RULE)
    c.fill_rect(36, 128, W - 72, 4, RULE)
    c.text(36, 140, 'FRIDAY', 2, INK, bold=True)
    c.text_centered(W // 2, 136, '20 NOVEMBER 2026', 3, INK, bold=True)
    c.text_right(W - 36, 140, 'LATE EDITION', 2, INK, bold=True)

    # lead story
    panel(c, 36, 168, W - 72, 336, scene_ukraine, 146,
          'UKRAINE WAR - LEAD STORY',
          "RUSSIA'S MASSIVE OVERNIGHT STRIKE POUNDS UKRAINE",
          'Some 100 missiles and 404 drones struck Ukraine overnight, '
          'killing 8 people, 6 in Kyiv. Three Dnipro bridges were damaged, '
          'an embassy was hit, and France sought a UN Security Council session.',
          4)

    pw = (W - 72 - 16) // 2
    panel(c, 36, 518, pw, 232, scene_poland, 68,
          'POLAND - NATO ON ALERT',
          'RUSSIAN MISSILES FALL INSIDE POLAND',
          'Kh-101 missiles and a drone fell on Polish soil. PM Tusk called '
          'it a provocation; NATO jets scrambled.',
          3)
    panel(c, 36 + pw + 16, 518, pw, 232, scene_ukeu, 68,
          'BRUSSELS - BREXIT RESET',
          'UK AND EU SEAL BREXIT RESET DEAL',
          'Food checks scrapped, emissions trading linked, and youth '
          'mobility for 100,000 young people a year.',
          3)
    panel(c, 36, 764, pw, 232, scene_iran, 68,
          'WASHINGTON - IRAN',
          'TRUMP DEFERS IRAN STRIKE DECISION TO 2027',
          'Trump put off deciding on more Iran strikes until 2027. The '
          'Senate backed him 51-48; war cost hits $48.3bn.',
          3)
    panel(c, 36 + pw + 16, 764, pw, 232, scene_anthropic, 68,
          'MARKETS - AI STOCKS',
          'ANTHROPIC SHARES SLIDE 10% ON DAY TWO',
          'ANT fell about 10% to near $87, down from a $97.17 debut close, '
          'as a broad selloff swept AI stocks.',
          3)

    c.text_centered(W // 2, 1004,
                    'COMPILED FROM REUTERS, AL JAZEERA, KYIV INDEPENDENT, '
                    'CNN AND MARKET REPORTS - PRINTED BY GENSOUAI', 1, BODY)
    return c


# ---------------------------------------------------------------- png out
def encode_png(c):
    raw = bytearray()
    stride = c.w * 3
    for yy in range(c.h):
        raw.append(0)
        raw += c.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data +
                struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', c.w, c.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', zlib.compress(bytes(raw), 9)) +
            chunk(b'IEND', b''))


def main():
    data = encode_png(build_page())
    try:
        os.makedirs('/output', exist_ok=True)
        path = '/output/entry.png'
        with open(path, 'wb') as f:
            f.write(data)
    except OSError:
        os.makedirs(os.path.join('.', 'output'), exist_ok=True)
        path = os.path.join('.', 'output', 'entry.png')
        with open(path, 'wb') as f:
            f.write(data)
    print('wrote %s (%d bytes)' % (path, len(data)))


if __name__ == '__main__':
    main()
