"""
All Pygame rendering.
Each screen has update(events) -> dict|None and draw(surface).
No game logic or persistence lives here.
"""

import pygame
import math
import random
from constants import (
    BG, PANEL_BG, WHITE, BLACK, GOLD, TEAL, RED, GREEN, GRAY,
    HIGHLIGHT, PURPLE, ORANGE, PINK,
    FONT_SM, FONT_MD, FONT_LG, PIXEL_FONT,
    INTERNAL_W, INTERNAL_H, SHAPES,
    CATEGORY_COLORS, ROOM_PALETTE,
)

# ---------------------------------------------------------------------------
# Pre-generated ambient effects  (created once at import time)
# ---------------------------------------------------------------------------

_STARS = [
    (int(random.random() * INTERNAL_W),
     int(random.random() * INTERNAL_H),
     random.random() * math.pi * 2,      # twinkle phase
     random.random() * 0.5 + 0.5)        # twinkle speed
    for _ in range(55)
]

_SCANLINES = None   # lazy-init on first draw (needs pygame display to be up)
_floor_cache = {}   # (room_name, fw, fh) → pygame.Surface


def _get_scanlines():
    global _SCANLINES
    if _SCANLINES is None:
        _SCANLINES = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        for y in range(0, INTERNAL_H, 3):
            pygame.draw.line(_SCANLINES, (0, 0, 0, 45), (0, y), (INTERNAL_W, y))
    return _SCANLINES


def get_t():
    """Seconds since pygame start — drives all animations."""
    return pygame.time.get_ticks() / 1000.0


def draw_bg(surface):
    """Twinkling starfield background."""
    surface.fill(BG)
    t = get_t()
    for sx, sy, phase, speed in _STARS:
        bright = int((math.sin(t * speed * 2 + phase) + 1) / 2 * 180) + 40
        c = (bright, bright, bright)
        pygame.draw.circle(surface, c, (sx, sy), 1)


def draw_scanlines(surface):
    """Subtle CRT scanline overlay — call last before flip."""
    surface.blit(_get_scanlines(), (0, 0))


def lerp_color(a, b, alpha):
    return tuple(int(a[i] + (b[i] - a[i]) * alpha) for i in range(3))


def glow_border(surface, rect, t, c1=GOLD, c2=TEAL, width=2):
    """Animated border that pulses between two colours."""
    alpha = (math.sin(t * 3) + 1) / 2
    col   = lerp_color(c1, c2, alpha)
    r     = pygame.Rect(rect)
    pygame.draw.rect(surface, col, r, width, border_radius=4)
    dim   = lerp_color(col, BG, 0.6)
    pygame.draw.rect(surface, dim, r.inflate(-width*2, -width*2), 1, border_radius=3)


def category_color(cat_str):
    return CATEGORY_COLORS.get(cat_str.lower(), GRAY)


def room_color(name):
    h = sum(ord(c) for c in name.lower())
    return ROOM_PALETTE[h % len(ROOM_PALETTE)]


def room_shape(name):
    h = sum(ord(c) * (i+1) for i, c in enumerate(name.lower()))
    return SHAPES[h % len(SHAPES)]


def pixel_corners(surface, rect, colour, size=6):
    """Draw chunky 8-bit style corner decorations on a rect."""
    x, y, w, h = rect[0], rect[1], rect[2], rect[3]
    corners = [(x, y), (x+w, y), (x, y+h), (x+w, y+h)]
    for cx, cy in corners:
        pygame.draw.rect(surface, colour,
                         (cx - size//2, cy - size//2, size, size))

MX = INTERNAL_W // 2    # 320  (horizontal centre)
MY = INTERNAL_H // 2    # 180  (vertical centre)

# Split-screen layout constants
PALACE_W  = 288         # width of the left palace panel
CARD_X    = PALACE_W + 8          # 296  — right panel starts here
CARD_W    = INTERNAL_W - CARD_X - 4   # 340  — right panel width
CARD_CX   = CARD_X + CARD_W // 2  # 466  — centre of right panel


# ---------------------------------------------------------------------------
# Font / text helpers
# ---------------------------------------------------------------------------

_font_cache = {}

def font(size):
    if size not in _font_cache:
        try:
            _font_cache[size] = pygame.font.Font(PIXEL_FONT, size)
        except FileNotFoundError:
            _font_cache[size] = pygame.font.SysFont("monospace", size)
    return _font_cache[size]


def text(surface, msg, x, y, size=FONT_MD, colour=WHITE, anchor="topleft"):
    img = font(size).render(str(msg), False, colour)
    r   = img.get_rect(**{anchor: (x, y)})
    surface.blit(img, r)


def wrap_text(surface, msg, x, y, max_w, size=FONT_SM, colour=WHITE, line_h=18):
    words, line, lines = msg.split(), [], []
    f = font(size)
    for w in words:
        test = " ".join(line + [w])
        if f.size(test)[0] <= max_w:
            line.append(w)
        else:
            lines.append(" ".join(line))
            line = [w]
    lines.append(" ".join(line))
    for i, l in enumerate(lines):
        text(surface, l, x, y + i * line_h, size, colour)


def panel(surface, rect, colour=PANEL_BG, border=GOLD, radius=4):
    pygame.draw.rect(surface, colour, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 1, border_radius=radius)


# ---------------------------------------------------------------------------
# Palace layout helper  (shared between mini panel and full-screen view)
# ---------------------------------------------------------------------------

def palace_layout(num_rooms, cols, rw, rh, pad, ox, oy):
    """Return list of (rx, ry, rw, rh) for each room."""
    return [
        (ox + (i % cols) * (rw + pad),
         oy + (i // cols) * (rh + pad),
         rw, rh)
        for i in range(num_rooms)
    ]

# Mini panel (left 288px)
MINI = dict(cols=2, rw=120, rh=68, pad=6, ox=8, oy=30)
# Full-screen palace view
FULL = dict(cols=3, rw=188, rh=110, pad=8, ox=10, oy=36)


# ---------------------------------------------------------------------------
# 3-D room helpers  (floor patterns · math ornaments · fake isometric box)
# ---------------------------------------------------------------------------

def _draw_floor_pattern(surf, fw, fh, pattern, base_col):
    """Render one of 5 tile patterns onto surf sized (fw, fh)."""
    dark  = lerp_color(base_col, BG, 0.70)
    light = lerp_color(base_col, WHITE, 0.10)
    tile  = max(4, fw // 14)
    if pattern == 0:            # checkerboard
        for row in range(0, fh, tile):
            for col in range(0, fw, tile):
                c = light if (row // tile + col // tile) % 2 == 0 else dark
                pygame.draw.rect(surf, c, (col, row, tile, tile))
    elif pattern == 1:          # brick
        for row in range(0, fh, tile):
            off = tile // 2 if (row // tile) % 2 else 0
            for col in range(-off, fw + tile, tile):
                pygame.draw.rect(surf, dark,  (col, row, tile - 1, tile - 1))
                pygame.draw.rect(surf, light, (col, row, tile - 1, tile - 1), 1)
    elif pattern == 2:          # diagonal stripes
        surf.fill(dark)
        step = tile * 2
        for i in range(-fh, fw + fh, step):
            pygame.draw.line(surf, light, (i, 0), (i + fh, fh), max(1, tile // 2))
    elif pattern == 3:          # dot grid
        surf.fill(dark)
        step = max(4, tile)
        for row in range(step // 2, fh, step):
            for col in range(step // 2, fw, step):
                pygame.draw.circle(surf, light, (col, row), max(1, step // 4))
    else:                       # stone grid
        surf.fill(dark)
        for row in range(0, fh + 1, tile):
            pygame.draw.line(surf, light, (0, row), (fw, row), 1)
        for col in range(0, fw + 1, tile):
            pygame.draw.line(surf, light, (col, 0), (col, fh), 1)


def _get_floor_surf(room_name, fw, fh, base_col):
    key = (room_name, fw, fh)
    if key not in _floor_cache:
        h       = sum(ord(c) for c in room_name.lower())
        pattern = h % 5
        surf    = pygame.Surface((max(1, fw), max(1, fh)))
        surf.fill(PANEL_BG)
        _draw_floor_pattern(surf, fw, fh, pattern, base_col)
        _floor_cache[key] = surf
    return _floor_cache[key]


def draw_room_ornament(surface, cx, cy, size, deco_type, color):
    """Dim mathematical decoration inside a room (spirograph/Lissajous/rose/star)."""
    dim  = lerp_color(color, BG, 0.78)
    pts  = []
    if deco_type == 0:          # spirograph
        R, r, d = size, max(1, size // 3), size // 2
        for i in range(200):
            t2 = i * math.pi / 40
            x  = int(cx + (R - r) * math.cos(t2) + d * math.cos((R - r) / r * t2))
            y  = int(cy + (R - r) * math.sin(t2) - d * math.sin((R - r) / r * t2))
            pts.append((x, y))
    elif deco_type == 1:        # Lissajous (3:2)
        for i in range(200):
            t2 = i * math.pi / 50
            pts.append((int(cx + size * math.sin(3 * t2 + math.pi / 4)),
                        int(cy + int(size * 0.7) * math.sin(2 * t2))))
    elif deco_type == 2:        # rose curve n=3
        for i in range(200):
            a  = i * math.pi / 40
            rr = size * math.cos(3 * a)
            pts.append((int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a))))
    else:                       # 7-point star polygon
        pts = _star_pts(cx, cy, size, size // 2, 7)
    if len(pts) >= 2:
        pygame.draw.lines(surface, dim, deco_type == 3, pts, 1)


def draw_3d_room(surface, rx, ry, rw, rh, base_col):
    """Fake isometric 3-face box. Returns (front_rect, depth)."""
    depth = max(4, rh // 6)
    # Front face
    front_rect = (rx, ry + depth, rw - depth, rh - depth)
    pygame.draw.rect(surface, lerp_color(base_col, BG, 0.82), front_rect)
    # Top face
    pygame.draw.polygon(surface, lerp_color(base_col, WHITE, 0.22),
                        [(rx,             ry + depth),
                         (rx + depth,     ry),
                         (rx + rw,        ry),
                         (rx + rw - depth, ry + depth)])
    # Side face (right)
    pygame.draw.polygon(surface, lerp_color(base_col, BLACK, 0.55),
                        [(rx + rw - depth, ry + depth),
                         (rx + rw,         ry),
                         (rx + rw,         ry + rh - depth),
                         (rx + rw - depth, ry + rh)])
    return front_rect, depth


def draw_palace_panel(surface, palace, cat, layout_params, offset_x=0, offset_y=0):
    """Draw rooms + containers + cat. offset_x/y shift all drawing."""
    rooms  = palace.rooms
    layout = palace_layout(len(rooms), **layout_params)
    t      = get_t()
    shape_size = max(8, min(12, layout_params["rw"] // 12))

    for i, room in enumerate(rooms):
        rx, ry, rw, rh = layout[i]
        rx, ry = rx + offset_x, ry + offset_y
        rc = room_color(room.name)

        # Fake-3D box shell
        front_rect, depth = draw_3d_room(surface, rx, ry, rw, rh, rc)
        fx, fy, fw, fh    = front_rect

        if fw > 0 and fh > 0:
            # Cached floor pattern inside front face
            surface.blit(_get_floor_surf(room.name, fw, fh, rc), (fx, fy))
            # Dim math ornament centred in front face
            h = sum(ord(c) for c in room.name.lower())
            draw_room_ornament(surface, fx + fw // 2, fy + fh // 2,
                               min(fw, fh) // 3, h % 4, rc)

        # Room name on top face
        top_cx = rx + (rw + depth) // 2 - depth // 2
        text(surface, room.name.upper()[:12], top_cx, ry + depth // 2,
             max(6, FONT_SM - 3), lerp_color(rc, WHITE, 0.75), "center")

        # Animated border + corner squares on front face
        glow_border(surface, front_rect, t + i, rc,
                    lerp_color(rc, WHITE, 0.4), width=2)
        pixel_corners(surface, front_rect, rc, size=4)

        # Containers: shape + short description label
        cell_w = max(1, fw // 3)
        for j, cont in enumerate(room.containers[:6]):
            ccx = fx + (j % 3) * cell_w + cell_w // 2
            ccy = fy + 14 + (j // 3) * max(1, (fh - 14) // 2)
            pulse = lerp_color(TEAL, WHITE, (math.sin(t * 2 + j) + 1) / 4)
            draw_shape(surface, cont.shape, pulse, ccx, ccy, shape_size)
            text(surface, cont.description[:7].upper(),
                 ccx, ccy + shape_size + 2,
                 max(6, min(8, cell_w // 5)),
                 lerp_color(TEAL, WHITE, 0.3), "center")

    # Cat
    if cat is not None and layout:
        cx, cy = cat.pixel_pos(layout, offset_x, offset_y)
        draw_cat(surface, cx, cy, GOLD, cat.frame, cat.facing)


# ---------------------------------------------------------------------------
# Cat
# ---------------------------------------------------------------------------

class Cat:
    def __init__(self):
        self.room_idx  = 0
        self.local_x   = 0.5
        self.local_y   = 0.7
        self.frame     = 0
        self.anim      = 0.0
        self.wait      = 60
        self.facing    = 1

    def update(self, palace, dt=1/60):
        self.anim += dt
        if self.anim >= 0.28:
            self.frame ^= 1
            self.anim = 0.0
        if self.wait > 0:
            self.wait -= 1
        else:
            n = len(palace.rooms)
            self.room_idx = random.randrange(n) if n else 0
            self.local_x  = random.uniform(0.15, 0.85)
            self.local_y  = random.uniform(0.4,  0.88)
            self.facing   = random.choice([-1, 1])
            self.wait     = random.randint(80, 160)

    def pixel_pos(self, layout, ox=0, oy=0):
        if not layout or self.room_idx >= len(layout):
            return (ox + 50, oy + 100)
        rx, ry, rw, rh = layout[self.room_idx]
        return (int(rx + self.local_x * rw), int(ry + self.local_y * rh))


def draw_cat(surface, x, y, colour=GOLD, frame=0, facing=1):
    """Pixel-art cat: ~12px wide, 14px tall at internal resolution."""
    x, y = int(x), int(y)
    d    = facing            # 1 = right, -1 = left

    # body
    pygame.draw.ellipse(surface, colour, (x - 6, y - 3, 12, 7))

    # head (offset to front)
    hx = x + d * 5
    pygame.draw.circle(surface, colour, (hx, y - 7), 5)

    # ears
    pygame.draw.polygon(surface, colour, [(hx + d*1, y-11), (hx + d*3, y-11), (hx + d*2, y-8)])
    pygame.draw.polygon(surface, colour, [(hx - d*1, y-11), (hx - d*3, y-11), (hx - d*2, y-8)])

    # eye
    pygame.draw.circle(surface, BG, (hx + d * 2, y - 7), 1)

    # tail (opposite side from head)
    tx = x - d * 6
    pygame.draw.lines(surface, colour, False,
                      [(tx, y - 2), (tx - d*4, y - 5), (tx - d*3, y - 9)], 2)

    # legs (animate)
    spread = 3 if frame else 0
    pygame.draw.line(surface, colour, (x - 2, y + 3), (x - 2 - spread, y + 8), 2)
    pygame.draw.line(surface, colour, (x + 2, y + 3), (x + 2 + spread, y + 8), 2)


# ---------------------------------------------------------------------------
# Shape drawing
# ---------------------------------------------------------------------------

def draw_shape(surface, shape, colour, cx, cy, size=20):
    s = size
    if shape == "diamond":
        pygame.draw.polygon(surface, colour,
                            [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)])
    elif shape == "triangle":
        pygame.draw.polygon(surface, colour,
                            [(cx, cy-s), (cx+s, cy+s), (cx-s, cy+s)])
    elif shape == "star":
        pygame.draw.polygon(surface, colour, _star_pts(cx, cy, s, s//2, 5))
    elif shape == "pentagon":
        pygame.draw.polygon(surface, colour, _poly_pts(cx, cy, s, 5))
    elif shape == "hexagon":
        pygame.draw.polygon(surface, colour, _poly_pts(cx, cy, s, 6))
    elif shape == "heart":
        r = max(3, s//2)
        pygame.draw.circle(surface, colour, (cx-r//2, cy-r//2), r)
        pygame.draw.circle(surface, colour, (cx+r//2, cy-r//2), r)
        pygame.draw.polygon(surface, colour,
                            [(cx-s, cy-r//2), (cx, cy+s), (cx+s, cy-r//2)])
    elif shape == "cross":
        t = max(3, s//3)
        pygame.draw.rect(surface, colour, (cx-t, cy-s, t*2, s*2))
        pygame.draw.rect(surface, colour, (cx-s, cy-t, s*2, t*2))
    elif shape == "crown":
        pygame.draw.polygon(surface, colour, [
            (cx-s, cy+s//2), (cx-s, cy-s//2), (cx-s//2, cy),
            (cx, cy-s), (cx+s//2, cy), (cx+s, cy-s//2), (cx+s, cy+s//2)])
    elif shape == "shield":
        pygame.draw.polygon(surface, colour, [
            (cx-s, cy-s), (cx+s, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)])
    elif shape in ("circle", "orb"):
        pygame.draw.circle(surface, colour, (cx, cy), s)
    elif shape == "ring":
        pygame.draw.circle(surface, colour, (cx, cy), s, max(3, s//4))
    elif shape == "moon":
        pygame.draw.circle(surface, colour, (cx, cy), s)
        pygame.draw.circle(surface, BG, (cx+s//3, cy-s//4), int(s*0.75))
    elif shape == "drop":
        pygame.draw.polygon(surface, colour, [
            (cx, cy-s), (cx+s//2, cy), (cx+s//3, cy+s//2),
            (cx, cy+s), (cx-s//3, cy+s//2), (cx-s//2, cy)])
    elif shape == "flame":
        pygame.draw.polygon(surface, colour, [
            (cx, cy-s), (cx+s//2, cy-s//3), (cx+s//3, cy+s//2),
            (cx, cy+s), (cx-s//3, cy+s//2), (cx-s//2, cy-s//3)])
    elif shape == "leaf":
        pygame.draw.polygon(surface, colour,
                            [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)])
    elif shape == "bolt":
        pygame.draw.polygon(surface, colour, [
            (cx, cy-s), (cx+s//3, cy-s//4),
            (cx, cy+s//4), (cx+s//2, cy+s)])
    elif shape == "spiral":
        pts = [(int(cx + i*s/60*math.cos(i*0.2)),
                int(cy + i*s/60*math.sin(i*0.2))) for i in range(60)]
        if len(pts) >= 2:
            pygame.draw.lines(surface, colour, False, pts, 2)
    elif shape == "flask":
        pygame.draw.rect(surface, colour, (cx-s//4, cy-s, s//2, s//2))
        pygame.draw.polygon(surface, colour, [
            (cx-s//4, cy-s//2), (cx-s, cy+s//2),
            (cx+s, cy+s//2), (cx+s//4, cy-s//2)])
    elif shape in ("crystal", "gem"):
        pygame.draw.polygon(surface, colour, [
            (cx, cy-s), (cx+s, cy-s//3), (cx+s//2, cy+s),
            (cx-s//2, cy+s), (cx-s, cy-s//3)])
    elif shape == "cube":
        pygame.draw.rect(surface, colour, (cx-s//2, cy, s, s))
        pygame.draw.rect(surface, colour, (cx, cy-s//2, s, s))
        pygame.draw.line(surface, BG, (cx, cy), (cx, cy-s//2), 2)
    elif shape == "square":
        pygame.draw.rect(surface, colour, (cx-s, cy-s, s*2, s*2))
    elif shape == "chest":
        pygame.draw.rect(surface, colour, (cx-s, cy, s*2, s))
        pygame.draw.rect(surface, colour, (cx-s, cy-s//2, s*2, s//2))
        pygame.draw.rect(surface, GOLD, (cx-s//6, cy-s//8, s//3, s//4))
    elif shape == "cage":
        pygame.draw.rect(surface, colour, (cx-s, cy-s, s*2, s*2), 2)
        for i in (-1, 0, 1):
            pygame.draw.line(surface, colour,
                             (cx+i*(s//2), cy-s), (cx+i*(s//2), cy+s), 1)
        pygame.draw.line(surface, colour, (cx-s, cy), (cx+s, cy), 1)
    else:
        pygame.draw.rect(surface, colour, (cx-s, cy-s, s*2, s*2))


def _poly_pts(cx, cy, r, n):
    return [(int(cx + r*math.cos(math.pi/2 + 2*math.pi*i/n)),
             int(cy - r*math.sin(math.pi/2 + 2*math.pi*i/n))) for i in range(n)]

def _star_pts(cx, cy, ro, ri, n=5):
    pts = []
    for i in range(n*2):
        r = ro if i % 2 == 0 else ri
        a = math.pi/2 + math.pi*i/n
        pts.append((int(cx + r*math.cos(a)), int(cy - r*math.sin(a))))
    return pts


# ---------------------------------------------------------------------------
# Base Screen
# ---------------------------------------------------------------------------

class Screen:
    def __init__(self, game):
        self.game = game

    def update(self, events):
        return None

    def draw(self, surface):
        surface.fill(BG)


# ---------------------------------------------------------------------------
# Home Screen
# ---------------------------------------------------------------------------

class HomeScreen(Screen):
    MENU = [
        ("NEW GAME",   "new_game"),
        ("CONTINUE",   "continue"),
        ("FLASHCARDS", "flashcard"),
        ("QUIT",       "quit"),
    ]

    def __init__(self, game):
        super().__init__(game)
        self.selected = 0

    def update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected - 1) % len(self.MENU)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected + 1) % len(self.MENU)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return {"action": self.MENU[self.selected][1]}
        return None

    def draw(self, surface):
        draw_bg(surface)
        t = get_t()
        # Animated title
        t1 = lerp_color(GOLD, TEAL,   (math.sin(t * 1.2) + 1) / 2)
        t2 = lerp_color(TEAL, PURPLE, (math.sin(t * 1.2 + 1) + 1) / 2)
        text(surface, "MEMORY", MX, 62,  FONT_LG, t1, "center")
        text(surface, "PALACE", MX, 100, FONT_LG, t2, "center")
        # Decorative divider
        div_y = 140
        for dx in range(0, INTERNAL_W, 8):
            c = lerp_color(GOLD, BG, abs(math.sin(t * 2 + dx * 0.05)))
            pygame.draw.rect(surface, c, (dx, div_y, 4, 2))
        for i, (label, _) in enumerate(self.MENU):
            y   = 155 + i * 40
            col = TEAL if i == self.selected else GRAY
            pre = "> " if i == self.selected else "  "
            text(surface, pre + label, MX, y, FONT_MD, col, "center")
            if i == self.selected:
                # Animated selector brackets
                bx = MX - 80
                pulse = lerp_color(TEAL, GOLD, (math.sin(t * 4) + 1) / 2)
                text(surface, "<<", bx - 30, y, FONT_MD, pulse, "center")
                text(surface, ">>", bx + 190, y, FONT_MD, pulse, "center")
        text(surface, "UP / DOWN     ENTER", MX, INTERNAL_H - 18, FONT_SM, GRAY, "center")
        draw_scanlines(surface)


# ---------------------------------------------------------------------------
# Element Card Screen  (split: palace left | card right)
# ---------------------------------------------------------------------------

class ElementScreen(Screen):
    STAGE_INFO  = "info"
    STAGE_DESC  = "desc"
    STAGE_SHAPE = "shape"
    STAGE_ROOM  = "room"
    COLS = 5

    def __init__(self, game, element):
        super().__init__(game)
        self.element        = element
        self.stage          = self.STAGE_INFO
        self.input_text     = ""
        self.container_desc = ""
        self.chosen_shape   = 0

    # --- input handling ---

    def update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if self.stage == self.STAGE_INFO:
                    if e.key == pygame.K_RETURN:
                        self.stage = self.STAGE_DESC
                        pygame.key.start_text_input()

                elif self.stage == self.STAGE_DESC:
                    if e.key == pygame.K_RETURN and self.input_text.strip():
                        self.container_desc = self.input_text.strip()
                        self.input_text     = ""
                        self.stage          = self.STAGE_SHAPE
                        pygame.key.stop_text_input()
                    elif e.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]

                elif self.stage == self.STAGE_SHAPE:
                    if e.key == pygame.K_RIGHT:
                        self.chosen_shape = (self.chosen_shape + 1) % len(SHAPES)
                    elif e.key == pygame.K_LEFT:
                        self.chosen_shape = (self.chosen_shape - 1) % len(SHAPES)
                    elif e.key == pygame.K_DOWN:
                        self.chosen_shape = (self.chosen_shape + self.COLS) % len(SHAPES)
                    elif e.key == pygame.K_UP:
                        self.chosen_shape = (self.chosen_shape - self.COLS) % len(SHAPES)
                    elif e.key == pygame.K_RETURN:
                        self.stage = self.STAGE_ROOM
                        pygame.key.start_text_input()

                elif self.stage == self.STAGE_ROOM:
                    if e.key == pygame.K_RETURN and self.input_text.strip():
                        self._commit(self.input_text.strip())
                        return {"action": "element_stored"}
                    elif e.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]

            elif e.type == pygame.TEXTINPUT:
                if self.stage in (self.STAGE_DESC, self.STAGE_ROOM):
                    self.input_text += e.text
        return None

    def _commit(self, room_name):
        from palace import Container
        c = Container(description=self.container_desc, shape=SHAPES[self.chosen_shape])
        self.game.palace.store_element(self.element["name"], c, room_name)

    # --- drawing ---

    def draw(self, surface):
        draw_bg(surface)
        if self.stage == self.STAGE_SHAPE:
            self._draw_shape_picker(surface)
        else:
            self._draw_left_palace(surface)
            self._draw_right_card(surface)
        draw_scanlines(surface)

    def _draw_left_palace(self, surface):
        panel(surface, (2, 2, PALACE_W, INTERNAL_H - 4))
        text(surface, "PALACE", PALACE_W // 2, 8, FONT_SM, GOLD, "center")
        if not self.game.palace.rooms:
            text(surface, "EMPTY", PALACE_W // 2, MY, FONT_SM - 2, GRAY, "center")
        else:
            draw_palace_panel(surface, self.game.palace, self.game.cat, MINI, 2, 2)

    def _draw_right_card(self, surface):
        el   = self.element
        t    = get_t()
        cat  = el["category"]
        cc   = category_color(cat)   # unique colour per element type

        # Panel background
        pygame.draw.rect(surface, PANEL_BG,
                         (CARD_X, 2, CARD_W, INTERNAL_H - 4), border_radius=4)

        # Coloured header strip
        pygame.draw.rect(surface, lerp_color(cc, BG, 0.6),
                         (CARD_X, 2, CARD_W, 46), border_radius=4)

        # Animated glow border keyed to category colour
        glow_border(surface, (CARD_X, 2, CARD_W, INTERNAL_H - 4), t, cc,
                    lerp_color(cc, WHITE, 0.5))
        pixel_corners(surface, (CARD_X, 2, CARD_W, INTERNAL_H - 4), cc, size=6)

        # Element info
        text(surface, el["name"].upper(), CARD_CX, 10, FONT_LG, WHITE, "center")
        text(surface, el["symbol"],       CARD_X + 8, 10, FONT_LG, cc)
        text(surface, f"#{el['number']}", CARD_X + CARD_W - 8, 10,
             FONT_MD, GRAY, "topright")

        # Divider
        pygame.draw.line(surface, lerp_color(cc, BG, 0.4),
                         (CARD_X + 6, 50), (CARD_X + CARD_W - 6, 50), 1)

        text(surface, f"GROUP {el['group']}   PERIOD {el['period']}",
             CARD_CX, 56, FONT_SM, WHITE, "center")
        text(surface, f"MASS  {el['mass']}", CARD_CX, 76, FONT_SM, GRAY, "center")
        text(surface, cat.upper(), CARD_CX, 96, FONT_SM, cc, "center")

        # Properties
        for i, prop in enumerate(el["properties"][:2]):
            wrap_text(surface, prop, CARD_X + 10, 120 + i * 38,
                      CARD_W - 20, FONT_SM, WHITE, 20)

        # Animated atomic number orbiting decoration
        angle = t * 1.5
        ox = CARD_X + CARD_W - 22
        oy = 80
        for orbit_r, orbit_speed, orbit_col in [
            (10, 1.5, cc), (15, -1.0, lerp_color(cc, WHITE, 0.5))
        ]:
            ex = int(ox + orbit_r * math.cos(angle * orbit_speed))
            ey = int(oy + orbit_r * math.sin(angle * orbit_speed) * 0.5)
            pygame.draw.circle(surface, orbit_col, (ex, ey), 2)

        # Stage-specific bottom section
        if self.stage == self.STAGE_INFO:
            text(surface, "ENTER TO CONTINUE",
                 CARD_CX, INTERNAL_H - 18, FONT_SM, GRAY, "center")
        elif self.stage in (self.STAGE_DESC, self.STAGE_ROOM):
            label = ("WHAT IS YOUR CONTAINER?"
                     if self.stage == self.STAGE_DESC
                     else "PLACE IN WHICH ROOM?")
            text(surface, label, CARD_X + 8, INTERNAL_H - 52, FONT_SM, GOLD)
            glow_border(surface, (CARD_X + 4, INTERNAL_H - 34, CARD_W - 8, 26),
                        t, GOLD, TEAL, width=1)
            text(surface, (self.input_text + "_")[:34],
                 CARD_X + 10, INTERNAL_H - 30, FONT_SM, WHITE)

    def _draw_shape_picker(self, surface):
        text(surface, "CHOOSE A CONTAINER SHAPE", MX, 12, FONT_MD, GOLD, "center")
        cell = 54
        ox   = (INTERNAL_W - self.COLS * cell) // 2
        oy   = 40
        for i, shape in enumerate(SHAPES):
            row, col = divmod(i, self.COLS)
            cx = ox + col * cell + cell // 2
            cy = oy + row * cell + cell // 2
            if i == self.chosen_shape:
                pygame.draw.rect(surface, HIGHLIGHT,
                                 (cx - cell//2, cy - cell//2, cell, cell),
                                 border_radius=3)
            draw_shape(surface, shape,
                       TEAL if i == self.chosen_shape else GRAY,
                       cx, cy, 15)
        text(surface, SHAPES[self.chosen_shape].upper(),
             MX, INTERNAL_H - 28, FONT_SM, WHITE, "center")
        text(surface, "ARROWS     ENTER TO CONFIRM",
             MX, INTERNAL_H - 12, FONT_SM, GRAY, "center")


# ---------------------------------------------------------------------------
# Palace View Screen  (full-screen schematic + cat)
# ---------------------------------------------------------------------------

class PalaceScreen(Screen):
    def update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return {"action": "home"}
        return None

    def draw(self, surface):
        draw_bg(surface)
        t = get_t()
        title_c = lerp_color(GOLD, TEAL, (math.sin(t * 1.5) + 1) / 2)
        text(surface, "MEMORY PALACE", MX, 8, FONT_MD, title_c, "center")
        palace = self.game.palace
        if not palace.rooms:
            text(surface, "PALACE IS EMPTY", MX, MY, FONT_SM, GRAY, "center")
        else:
            draw_palace_panel(surface, palace, self.game.cat, FULL, 0, 0)
        text(surface, "ESC = HOME", MX, INTERNAL_H - 12, FONT_SM, GRAY, "center")
        draw_scanlines(surface)


# ---------------------------------------------------------------------------
# Flashcard Screen
# ---------------------------------------------------------------------------

class FlashcardScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.elements = game.elements
        self.index    = 0
        self.flipped  = False

    def update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RIGHT:
                    self.index = (self.index + 1) % len(self.elements)
                    self.flipped = False
                elif e.key == pygame.K_LEFT:
                    self.index = (self.index - 1) % len(self.elements)
                    self.flipped = False
                elif e.key == pygame.K_SPACE:
                    self.flipped = not self.flipped
                elif e.key == pygame.K_ESCAPE:
                    return {"action": "home"}
        return None

    def draw(self, surface):
        draw_bg(surface)
        t  = get_t()
        el = self.elements[self.index]
        cc = category_color(el["category"])
        title_c = lerp_color(GOLD, TEAL, (math.sin(t * 1.5) + 1) / 2)
        text(surface, "FLASHCARD MODE", MX, 8, FONT_MD, title_c, "center")
        pygame.draw.rect(surface, PANEL_BG,
                         (14, 28, INTERNAL_W - 28, INTERNAL_H - 52), border_radius=4)
        pygame.draw.rect(surface, lerp_color(cc, BG, 0.6),
                         (14, 28, INTERNAL_W - 28, 50), border_radius=4)
        glow_border(surface, (14, 28, INTERNAL_W - 28, INTERNAL_H - 52), t, cc,
                    lerp_color(cc, WHITE, 0.5))
        pixel_corners(surface, (14, 28, INTERNAL_W - 28, INTERNAL_H - 52), cc, size=6)
        text(surface, el["name"].upper(), MX,   36, FONT_LG, WHITE, "center")
        text(surface, el["symbol"],        28,  36, FONT_LG, cc)
        text(surface, f"#{el['number']}", INTERNAL_W - 28, 36, FONT_MD, GRAY, "topright")
        if not self.flipped:
            text(surface, "SPACE TO REVEAL", MX, MY, FONT_SM, GRAY, "center")
        else:
            text(surface, f"GROUP {el['group']}   PERIOD {el['period']}",
                 MX, 82, FONT_SM, WHITE, "center")
            text(surface, f"MASS  {el['mass']}", MX, 102, FONT_SM, GRAY, "center")
            text(surface, el["category"].upper(), MX, 122, FONT_SM, TEAL, "center")
            for i, prop in enumerate(el["properties"][:3]):
                wrap_text(surface, prop, 28, 148 + i * 22,
                          INTERNAL_W - 56, FONT_SM, WHITE, 20)
            text(surface, "USES:", 28, 218, FONT_SM, GOLD)
            for i, use in enumerate(el["uses"][:2]):
                wrap_text(surface, use, 28, 238 + i * 22,
                          INTERNAL_W - 56, FONT_SM, GRAY, 20)
            wrap_text(surface, el["fun_fact"], 28, 288,
                      INTERNAL_W - 56, FONT_SM - 2, PURPLE, 16)
        text(surface, f"{self.index+1}/{len(self.elements)}    < >   SPACE   ESC",
             MX, INTERNAL_H - 16, FONT_SM, GRAY, "center")
        draw_scanlines(surface)


# ---------------------------------------------------------------------------
# Quiz Screen
# ---------------------------------------------------------------------------

class QuizScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.level    = game.level
        self.selected = 0
        self.answered = None
        self.score    = 0
        self._build_questions()
        self.q_index  = 0

    def _build_questions(self):
        from elements import get_by_name, wrong_choices
        self.questions = []
        for name in self.game.palace.learned[-5:]:
            el = get_by_name(name)
            if not el:
                continue
            opts = [el] + wrong_choices(el, 3)
            random.shuffle(opts)
            self.questions.append({"element": el, "options": opts, "correct": el["name"]})

    def update(self, events):
        if not self.questions or self.q_index >= len(self.questions):
            return {"action": "quiz_done"}
        q = self.questions[self.q_index]
        for e in events:
            if e.type == pygame.KEYDOWN:
                if self.answered is None:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.selected = (self.selected - 1) % len(q["options"])
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected = (self.selected + 1) % len(q["options"])
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        chosen = q["options"][self.selected]["name"]
                        self.answered = (chosen == q["correct"])
                        if self.answered:
                            self.score += 1
                else:
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.q_index += 1
                        self.selected = 0
                        self.answered = None
                        if self.q_index >= len(self.questions):
                            return {"action": "quiz_done"}
        return None

    def draw(self, surface):
        surface.fill(BG)
        if not self.questions or self.q_index >= len(self.questions):
            return
        q  = self.questions[self.q_index]
        el = q["element"]
        text(surface, f"QUIZ   {self.q_index+1}/{len(self.questions)}   SCORE {self.score}",
             MX, 10, FONT_SM, GOLD, "center")
        prompt = (f"WHICH GROUP IS  {el['name'].upper()}  IN?"
                  if self.level == 1
                  else f"NAME A USE FOR  {el['name'].upper()}")
        wrap_text(surface, prompt, 20, 38, INTERNAL_W - 40, FONT_MD, WHITE, 24)
        for i, opt in enumerate(q["options"]):
            y = 110 + i * 48
            if self.answered is not None:
                col = (GREEN if opt["name"] == q["correct"]
                       else RED if i == self.selected else GRAY)
            else:
                col = TEAL if i == self.selected else WHITE
            pre   = "> " if i == self.selected else "  "
            label = (f"GROUP {opt['group']}" if self.level == 1
                     else opt["uses"][0][:36])
            text(surface, pre + label, 30, y, FONT_SM, col)
        if self.answered is not None:
            col = GREEN if self.answered else RED
            text(surface, "CORRECT!" if self.answered else "WRONG!",
                 MX, INTERNAL_H - 32, FONT_MD, col, "center")
        text(surface, "UP / DOWN     ENTER", MX, INTERNAL_H - 12, FONT_SM, GRAY, "center")
