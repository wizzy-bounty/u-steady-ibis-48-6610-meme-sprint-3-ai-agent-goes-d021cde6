#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one 1024x1024 meme PNG with the Python standard library only
(no Pillow, no network, no downloaded assets). Everything on the image
-- background, pizza shop, robot, text -- is drawn by this file.

The joke: a user tells their AI agent to order a pizza. The agent
goes rogue and buys the whole pizza place instead.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
YELLOW = (255, 200, 0)      # meme background
INK = (24, 24, 24)          # near-black text / outlines
WHITE = (255, 255, 255)
SKY = (126, 200, 247)
GROUND = (203, 203, 203)
BRICK = (217, 79, 61)       # pizza shop walls
CREAM = (255, 244, 214)
DOOR = (96, 58, 32)
GLASS = (255, 226, 130)
STEEL = (232, 232, 232)     # robot metal
SCREEN = (27, 42, 74)       # robot face screen
BOX = (201, 138, 75)        # pizza box cardboard
BOX_DARK = (170, 108, 52)
CHEESE = (255, 205, 92)
PEPPERONI = (198, 44, 34)
RED = (217, 60, 48)         # SOLD stamp
MAGENTA = (255, 0, 255)     # transparency key for stamp blits
GREEN = (46, 160, 67)
AMBER = (240, 180, 30)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, c, t=4):
        self.fill_rect(x0, y0, x1, y0 + t, c)
        self.fill_rect(x0, y1 - t, x1, y1, c)
        self.fill_rect(x0, y0, x0 + t, y1, c)
        self.fill_rect(x1 - t, y0, x1, y1, c)

    def filled_circle(self, cx, cy, r, c):
        cx, cy, r = int(cx), int(cy), int(r)
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, y, cx + dx + 1, y + 1, c)

    def circle_outline(self, cx, cy, r, c, t=4):
        for k in range(t):
            rr = r - k
            if rr <= 0:
                break
            for a in range(360):
                rad = math.radians(a)
                self.set(int(cx + rr * math.cos(rad)),
                         int(cy + rr * math.sin(rad)), c)

    def rounded_rect(self, x0, y0, x1, y1, r, c, outline=None, ow=0):
        if outline is not None and ow > 0:
            self.rounded_rect(x0 - ow, y0 - ow, x1 + ow, y1 + ow, r + ow,
                              outline)
        self.fill_rect(x0 + r, y0, x1 - r, y1, c)
        self.fill_rect(x0, y0 + r, x1, y1 - r, c)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.filled_circle(cx, cy, r, c)

    def thick_line(self, x0, y0, x1, y1, c, t=6):
        dx, dy = x1 - x0, y1 - y0
        steps = int(max(abs(dx), abs(dy))) + 1
        for i in range(steps + 1):
            f = i / steps
            self.filled_circle(x0 + dx * f, y0 + dy * f, t // 2, c)

    def polyline(self, pts, c, t=6):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            self.thick_line(ax, ay, bx, by, c, t)

    def blit_rotated(self, src, cx, cy, angle_deg, transparent):
        """Blit src canvas rotated by angle_deg around its centre onto
        (cx, cy) of this canvas; pixels equal to `transparent` are skipped."""
        ang = math.radians(angle_deg)
        ca, sa = math.cos(ang), math.sin(ang)
        hw, hh = src.w / 2.0, src.h / 2.0
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        rot = [(x * ca - y * sa, x * sa + y * ca) for x, y in corners]
        xs = [p[0] for p in rot]; ys = [p[1] for p in rot]
        x0, x1 = int(cx + min(xs)), int(cx + max(xs))
        y0, y1 = int(cy + min(ys)), int(cy + max(ys))
        for dy in range(y0, y1 + 1):
            for dx in range(x0, x1 + 1):
                # inverse-rotate destination offset back into source space
                rx, ry = dx - cx, dy - cy
                sx = rx * ca + ry * sa + hw
                sy = -rx * sa + ry * ca + hh
                ix, iy = int(sx), int(sy)
                if 0 <= ix < src.w and 0 <= iy < src.h:
                    i = (iy * src.w + ix) * 3
                    pix = tuple(src.px[i:i + 3])
                    if pix != transparent:
                        self.set(dx, dy, pix)


# ------------------------------------------------------------- bitmap font
# 5x7 glyphs, '#' = on, rows stored TOP-TO-BOTTOM (row 0 = glyph's top).
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
}


def text_width(text, s):
    return len(text) * 6 * s - s


def draw_text(cv, x, y, s, text, color, outline=None, ow=0, center_x=None):
    """Draw text with its top-left at (x, y); if center_x is given, the
    text is centred horizontally on it. y is the TOP row."""
    w = text_width(text, s)
    if center_x is not None:
        x = center_x - w // 2

    def _plot(ox, oy, col):
        for ci, ch in enumerate(text):
            glyph = FONT.get(ch, FONT[' '])
            for r in range(7):
                row = glyph[r]  # rows stored top-to-bottom
                for cc in range(5):
                    if row[cc] == '#':
                        cv.fill_rect(ox + (ci * 6 + cc) * s, oy + r * s,
                                     ox + (ci * 6 + cc) * s + s, oy + r * s + s,
                                     col)

    if outline is not None and ow > 0:
        for dx in range(-ow, ow + 1):
            for dy in range(-ow, ow + 1):
                if dx == 0 and dy == 0:
                    continue
                _plot(x + dx, y + dy, outline)
    _plot(x, y, color)


# ------------------------------------------------------------------- scene
def draw_shop(cv):
    # sign board
    cv.rounded_rect(80, 300, 450, 348, 10, WHITE, outline=INK, ow=4)
    draw_text(cv, 0, 312, 3, "PIZZA PALACE", INK, center_x=265)
    # walls
    cv.fill_rect(90, 348, 440, 620, BRICK)
    cv.rect_outline(90, 348, 440, 620, INK, 4)
    # awning stripes
    for i in range(7):
        col = WHITE if i % 2 == 0 else RED
        cv.fill_rect(90 + i * 50, 420, 90 + (i + 1) * 50, 458, col)
    cv.rect_outline(90, 420, 440, 458, INK, 3)
    # windows
    for wx in (112, 332):
        cv.fill_rect(wx, 480, wx + 88, 560, GLASS)
        cv.rect_outline(wx, 480, wx + 88, 560, INK, 3)
        cv.fill_rect(wx + 42, 480, wx + 46, 560, INK)
        cv.fill_rect(wx, 518, wx + 88, 522, INK)
    # door
    cv.fill_rect(232, 500, 300, 620, DOOR)
    cv.rect_outline(232, 500, 300, 620, INK, 3)
    cv.filled_circle(290, 565, 5, (255, 220, 120))
    # SOLD stamp, drawn on its own canvas then rotated in
    stamp = Canvas(300, 120, MAGENTA)
    stamp.rounded_rect(8, 8, 292, 112, 12, RED, outline=WHITE, ow=4)
    draw_text(stamp, 0, 34, 8, "SOLD", WHITE, center_x=150)
    cv.blit_rotated(stamp, 265, 448, -14, MAGENTA)


def draw_robot(cv):
    # antenna
    cv.thick_line(700, 362, 700, 322, INK, 6)
    cv.filled_circle(700, 314, 11, RED)
    cv.circle_outline(700, 314, 11, INK, 3)
    # head
    cv.rounded_rect(600, 362, 800, 502, 26, STEEL, outline=INK, ow=5)
    # face screen
    cv.rounded_rect(624, 386, 776, 478, 12, SCREEN)
    # sunglasses: two black shades + bridge, with a white glint
    cv.rounded_rect(638, 404, 700, 442, 8, INK)
    cv.rounded_rect(714, 404, 762, 442, 8, INK)
    cv.fill_rect(700, 420, 714, 428, INK)
    cv.fill_rect(646, 410, 660, 418, WHITE)
    cv.fill_rect(722, 410, 736, 418, WHITE)
    # smug smirk
    cv.polyline([(652, 452), (700, 466), (752, 444)], WHITE, 6)
    # neck + body
    cv.fill_rect(682, 502, 718, 514, STEEL)
    cv.rounded_rect(614, 512, 786, 622, 20, WHITE, outline=INK, ow=5)
    # chest panel with buttons
    cv.rounded_rect(664, 534, 736, 588, 8, INK)
    cv.filled_circle(682, 561, 9, GREEN)
    cv.filled_circle(700, 561, 9, AMBER)
    cv.filled_circle(718, 561, 9, RED)
    # arms reaching forward to the pizza box
    cv.thick_line(622, 534, 642, 618, STEEL, 16)
    cv.thick_line(778, 534, 758, 618, STEEL, 16)
    cv.circle_outline(622, 534, 8, INK, 3)
    cv.circle_outline(778, 534, 8, INK, 3)
    # feet (drawn before the box so the box sits in front of them)
    cv.fill_rect(640, 618, 682, 640, INK)
    cv.fill_rect(718, 618, 760, 640, INK)
    # open pizza box held in front, pizza visible inside
    cv.rounded_rect(630, 598, 770, 668, 8, BOX, outline=INK, ow=4)
    cv.filled_circle(700, 633, 58, CHEESE)
    cv.circle_outline(700, 633, 58, BOX_DARK, 4)
    for px, py in ((676, 616), (724, 616), (700, 633), (678, 650),
                   (722, 650)):
        cv.filled_circle(px, py, 9, PEPPERONI)


def draw_pizza_stack(cv):
    # stack of delivery boxes at the robot's side
    for i, (bx, by) in enumerate(((838, 596), (830, 566), (846, 536))):
        w = 118 - i * 6
        cv.rounded_rect(bx, by, bx + w, by + 30, 4, BOX, outline=INK, ow=3)
        cv.fill_rect(bx + 8, by + 12, bx + w - 8, by + 16, BOX_DARK)


def build():
    cv = Canvas(W, H, YELLOW)
    # top text
    draw_text(cv, 0, 44, 8, "I TOLD MY AI AGENT", INK,
              outline=WHITE, ow=3, center_x=512)
    draw_text(cv, 0, 122, 8, "TO ORDER PIZZA", INK,
              outline=WHITE, ow=3, center_x=512)
    # scene panel
    cv.rounded_rect(36, 196, 988, 756, 18, WHITE, outline=INK, ow=5)
    cv.fill_rect(42, 202, 982, 620, SKY)
    cv.fill_rect(42, 620, 982, 750, GROUND)
    cv.fill_rect(42, 616, 982, 622, INK)
    draw_shop(cv)
    draw_pizza_stack(cv)
    draw_robot(cv)
    # bottom text
    draw_text(cv, 0, 786, 9, "IT BOUGHT THE", INK,
              outline=WHITE, ow=3, center_x=512)
    draw_text(cv, 0, 868, 10, "PIZZA PLACE", INK,
              outline=WHITE, ow=3, center_x=512)
    return cv


# ------------------------------------------------------------------- output
def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
        probe = open(out_path, "wb")
        probe.close()
    except OSError:
        out_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
    cv = build()
    size = write_png(out_path, cv)
    print(f"wrote {out_path} ({cv.w}x{cv.h}, {size} bytes)")


if __name__ == "__main__":
    main()
