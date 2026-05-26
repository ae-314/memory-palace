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
    INTERNAL_W, INTERNAL_H, ITEMS,
    CATEGORY_COLORS, ROOM_PALETTE,
)
import sprites as _sprites
from sprites import draw_sprite, get_colored_tile, tile_key, TILE_COLS, TILE_ROWS

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
    return ITEMS[h % len(ITEMS)]


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

# Mini panel (left 288px of ElementScreen)
MINI = dict(cols=2, rw=132, rh=80, pad=5, ox=5, oy=28)
# Full-screen palace view — 3 cols × 3 rows fit above the 50px minimap strip
# Width:  8 + 3*190 + 2*5 = 588 ≤ 640 ✓
# Height: 22 + 3*88 + 2*5 = 296 ≤ (360-52=308) ✓
FULL = dict(cols=3, rw=190, rh=88, pad=5, ox=8, oy=22)

# Ambient room-decoration sprites (from Kenney sheet, placed in room corners)
DECO_SPRITES = [
    "shelf", "vase", "cauldron", "pillar",
    "t_14_6", "t_10_7", "t_9_7", "chest",
    "t_14_5", "t_8_7",  "t_15_7", "t_13_7",
]

# 4-sprite sets for room corners (TL, TR, BL, BR) — indexed by room name hash
DECO_SETS = [
    ["chest",    "shelf",     "barrel",   "pillar"],
    ["crate",    "cabinet",   "vase",     "cauldron"],
    ["safe",     "lockbox",   "pillar",   "vase"],
    ["barrel",   "chest",     "shelf",    "cauldron"],
    ["cabinet",  "crate",     "vase",     "pillar"],
    ["shelf",    "safe",      "cauldron", "chest"],
    ["vase",     "barrel",    "crate",    "shelf"],
    ["cauldron", "pillar",    "safe",     "cabinet"],
]

_ROOMS_PW  = 182   # left panel width in RoomsScreen
_ROOMS_CH  = 38    # height of each room card in the left panel


# ---------------------------------------------------------------------------
# Top-down room renderer  (Stardew Valley-inspired 3/4 perspective)
# ---------------------------------------------------------------------------

def draw_topdown_room(surface, rx, ry, rw, rh, base_col, room_name, t=0.0,
                      highlighted=False):
    """
    Flat 8-bit top-down room.  Returns interior rect (ix, iy, iw, ih).
    highlighted=True draws a gold selection border.
    """
    wall_n  = max(8,  rh // 5)   # north wall (thick – 3/4 perspective)
    wall_ew = max(2,  rw // 24)  # east/west walls (thin strips)
    wall_s  = max(2,  rh // 18)  # south wall

    col_wall  = lerp_color(base_col, BLACK, 0.42)
    col_wallt = lerp_color(base_col, BLACK, 0.26)
    col_trim  = lerp_color(base_col, WHITE, 0.60)
    col_shad  = lerp_color(base_col, BLACK, 0.75)
    col_floor = lerp_color(base_col, BG,    0.74)
    col_grid  = lerp_color(base_col, BG,    0.56)
    col_door  = lerp_color(BG, base_col, 0.12)

    ix = rx + wall_ew
    iy = ry + wall_n
    iw = rw - wall_ew * 2
    ih = rh - wall_n - wall_s

    # 1. Plain floor + subtle grid (NOT Kenney tiles — they obscure objects)
    if iw > 0 and ih > 0:
        pygame.draw.rect(surface, col_floor, (ix, iy, iw, ih))
        gs = max(8, min(16, iw // 6))   # grid step
        for ty in range(iy, iy + ih + 1, gs):
            pygame.draw.line(surface, col_grid, (ix, ty), (ix + iw, ty), 1)
        for tx in range(ix, ix + iw + 1, gs):
            pygame.draw.line(surface, col_grid, (tx, iy), (tx, iy + ih), 1)

    # 2. North wall: two-tone + wainscoting
    pygame.draw.rect(surface, col_wall, (rx, ry, rw, wall_n))
    band = max(2, wall_n // 3)
    pygame.draw.rect(surface, col_wallt, (rx, ry + band, rw, wall_n - band))
    wc = lerp_color(base_col, BLACK, 0.58)
    for wx in range(rx + wall_ew + 8, rx + rw - wall_ew, 14):
        pygame.draw.line(surface, wc, (wx, ry + 2), (wx, ry + wall_n - 3), 1)
    pygame.draw.rect(surface, col_trim, (ix, ry + wall_n - 2, iw, 2))   # baseboard
    pygame.draw.rect(surface, col_shad, (ix, iy, iw, 2))                # shadow

    # 3. Side walls
    pygame.draw.rect(surface, col_wall, (rx,            iy, wall_ew, rh - wall_n))
    pygame.draw.rect(surface, col_wall, (rx + rw - wall_ew, iy, wall_ew, rh - wall_n))

    # 4. South wall + door cutout
    pygame.draw.rect(surface, col_wall, (rx, ry + rh - wall_s, rw, wall_s))
    door_w = max(6, rw // 5)
    pygame.draw.rect(surface, col_door,
                     (rx + rw // 2 - door_w // 2, ry + rh - wall_s, door_w, wall_s))

    # 5. Ambient decoration sprite (top-right corner of interior)
    if iw >= 18 and ih >= 18:
        h    = sum(ord(c) for c in room_name.lower())
        deco = DECO_SPRITES[h % len(DECO_SPRITES)]
        dc   = lerp_color(base_col, WHITE, 0.30)
        dsz  = max(10, min(16, iw // 6))
        draw_sprite(surface, deco, dc, ix + iw - dsz // 2 - 2, iy + dsz // 2 + 2, dsz)

    # 6. Room name on north wall
    text(surface, room_name.upper()[:12],
         rx + rw // 2, ry + wall_n // 2,
         max(6, FONT_SM - 3), col_trim, "center")

    # 7. Border: gold if selected, subtle glow otherwise
    if highlighted:
        t2 = get_t()
        pulse = lerp_color(GOLD, WHITE, (math.sin(t2 * 5) + 1) / 2)
        pygame.draw.rect(surface, pulse, (rx, ry, rw, rh), 2)
    else:
        glow_border(surface, (rx, ry, rw, wall_n), t, base_col,
                    lerp_color(base_col, WHITE, 0.45), width=1)
        pixel_corners(surface, (rx, ry, rw, rh), col_trim, size=3)

    return (ix, iy, max(0, iw), max(0, ih))


def draw_floor_map(surface, palace, cat, mx, my, mw, mh):
    """Compact floor-plan minimap strip."""
    rooms = palace.rooms
    if not rooms:
        return
    n    = len(rooms)
    cols = FULL["cols"]
    rows = (n + cols - 1) // cols
    cell_w = max(8, (mw - 4) // max(cols, 1))
    cell_h = max(6, (mh - 4) // max(rows, 1))

    pygame.draw.rect(surface, PANEL_BG, (mx, my, mw, mh))
    pygame.draw.line(surface, lerp_color(GRAY, BG, 0.55), (mx, my), (mx + mw, my), 1)
    text(surface, "MAP", mx + 3, my + 2, max(5, FONT_SM - 5), GRAY)

    for i, room in enumerate(rooms):
        col_i = i % cols
        row_i = i // cols
        rx = mx + 2 + col_i * cell_w
        ry = my + 2 + row_i * cell_h
        rw = cell_w - 2
        rh = cell_h - 2
        if rw < 2 or rh < 2:
            continue
        rc = room_color(room.name)
        sel = (cat is not None and cat.room_idx == i)
        pygame.draw.rect(surface, lerp_color(rc, BG, 0.70), (rx, ry, rw, rh))
        bc  = GOLD if sel else lerp_color(rc, BG, 0.30)
        pygame.draw.rect(surface, bc, (rx, ry, rw, rh), 1 + (1 if sel else 0))
        # Cat dot
        if sel:
            t = get_t()
            pc = lerp_color(GOLD, WHITE, (math.sin(t * 6) + 1) / 2)
            pygame.draw.circle(surface, pc, (rx + rw // 2, ry + rh // 2), max(2, rh // 3))


def draw_palace_panel(surface, palace, cat, layout_params, offset_x=0, offset_y=0):
    """Draw rooms + containers + cat. offset_x/y shift all drawing."""
    rooms  = palace.rooms
    layout = palace_layout(len(rooms), **layout_params)
    t      = get_t()
    sel    = cat.room_idx if (cat and cat.player_controlled) else -1

    for i, room in enumerate(rooms):
        rx, ry, rw, rh = layout[i]
        rx, ry = rx + offset_x, ry + offset_y
        rc   = room_color(room.name)
        high = (i == sel)

        ix, iy, iw, ih = draw_topdown_room(
            surface, rx, ry, rw, rh, rc, room.name, t + i, highlighted=high)

        if iw > 0 and ih > 0 and room.containers:
            n_cont = min(len(room.containers), 6)
            cols_c = min(3, n_cont)
            rows_c = (n_cont + cols_c - 1) // cols_c
            cell_w = max(1, iw // cols_c)
            cell_h = max(1, ih // rows_c)
            sp_sz  = max(10, min(16, min(cell_w, cell_h) - 6))

            for j, cont in enumerate(room.containers[:6]):
                ccx = ix + (j % cols_c) * cell_w + cell_w // 2
                ccy = iy + (j // cols_c) * cell_h + cell_h // 2
                pulse = lerp_color(TEAL, WHITE, (math.sin(t * 2 + j) + 1) / 4)
                draw_sprite(surface, cont.shape, pulse, ccx, ccy, sp_sz)
                text(surface, cont.description[:6].upper(),
                     ccx, ccy + sp_sz // 2 + 2,
                     max(6, min(8, cell_w // 6)),
                     lerp_color(TEAL, WHITE, 0.40), "center")

    if cat is not None and layout:
        cx, cy = cat.pixel_pos(layout, offset_x, offset_y)
        draw_cat(surface, cx, cy, GOLD, cat.frame, cat.facing)


# ---------------------------------------------------------------------------
# Cat
# ---------------------------------------------------------------------------

class Cat:
    def __init__(self):
        self.room_idx          = 0
        self.local_x           = 0.5
        self.local_y           = 0.7
        self.frame             = 0
        self.anim              = 0.0
        self.wait              = 60
        self.facing            = 1
        self.player_controlled = False

    def update(self, palace, dt=1/60):
        self.anim += dt
        if self.anim >= 0.28:
            self.frame ^= 1
            self.anim = 0.0
        if self.player_controlled:
            return          # keep animating but no random wandering
        if self.wait > 0:
            self.wait -= 1
        else:
            n = len(palace.rooms)
            self.room_idx = random.randrange(n) if n else 0
            self.local_x  = random.uniform(0.15, 0.85)
            self.local_y  = random.uniform(0.4,  0.88)
            self.facing   = random.choice([-1, 1])
            self.wait     = random.randint(80, 160)

    def move_room(self, direction, n_rooms, cols):
        """Shift one step in direction within the room grid."""
        if n_rooms == 0:
            return
        if direction == "right":
            new_idx = self.room_idx + 1
            self.facing = 1
        elif direction == "left":
            new_idx = self.room_idx - 1
            self.facing = -1
        elif direction == "down":
            new_idx = self.room_idx + cols
        elif direction == "up":
            new_idx = self.room_idx - cols
        else:
            return
        if 0 <= new_idx < n_rooms:
            self.room_idx = new_idx

    def pixel_pos(self, layout, ox=0, oy=0):
        if not layout or self.room_idx >= len(layout):
            return (ox + 50, oy + 100)
        rx, ry, rw, rh = layout[self.room_idx]
        if self.player_controlled:
            return (int(rx + rw * 0.50), int(ry + rh * 0.60))
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
        ("MY ROOMS",   "rooms"),
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

    def __init__(self, game, element):
        super().__init__(game)
        self.element        = element
        self.stage          = self.STAGE_INFO
        self.input_text     = ""
        self.container_desc = ""
        self.picker_col     = 0   # column in 49×22 sprite sheet (0-48)
        self.picker_row     = 0   # row in 49×22 sprite sheet (0-21)

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
                        self.picker_col = (self.picker_col + 1) % TILE_COLS
                    elif e.key == pygame.K_LEFT:
                        self.picker_col = (self.picker_col - 1) % TILE_COLS
                    elif e.key == pygame.K_DOWN:
                        self.picker_row = (self.picker_row + 1) % TILE_ROWS
                    elif e.key == pygame.K_UP:
                        self.picker_row = (self.picker_row - 1) % TILE_ROWS
                    elif e.key == pygame.K_RETURN:
                        self.stage = self.STAGE_ROOM
                        pygame.key.start_text_input()

                elif self.stage == self.STAGE_ROOM:
                    if e.key == pygame.K_RETURN and self.input_text.strip():
                        self._commit(self.input_text.strip())
                        return {"action": "element_stored"}
                    elif e.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif e.key == pygame.K_1:
                        self._commit("kitchen")
                        return {"action": "element_stored"}
                    elif e.key == pygame.K_2:
                        self._commit("bedroom")
                        return {"action": "element_stored"}
                    elif e.key == pygame.K_3:
                        self._commit("garage")
                        return {"action": "element_stored"}

            elif e.type == pygame.TEXTINPUT:
                if self.stage in (self.STAGE_DESC, self.STAGE_ROOM):
                    self.input_text += e.text
        return None

    def _commit(self, room_name):
        from palace import Container
        name = tile_key(self.picker_col, self.picker_row)
        c = Container(description=self.container_desc, shape=name)
        self.game.palace.store_element(self.element["name"], c, room_name)

    # --- drawing ---

    def draw(self, surface):
        draw_bg(surface)
        if self.stage == self.STAGE_SHAPE:
            self._draw_shape_picker(surface)
        else:
            self._draw_right_card(surface)
        draw_scanlines(surface)

    def _draw_right_card(self, surface):
        # Full-screen card — no palace mini-panel any more
        CX = 4
        CW = INTERNAL_W - 8
        CC = INTERNAL_W // 2   # horizontal centre
        el   = self.element
        t    = get_t()
        cat  = el["category"]
        cc   = category_color(cat)   # unique colour per element type

        # Panel background
        pygame.draw.rect(surface, PANEL_BG,
                         (CX, 2, CW, INTERNAL_H - 4), border_radius=4)

        # Coloured header strip
        pygame.draw.rect(surface, lerp_color(cc, BG, 0.6),
                         (CX, 2, CW, 46), border_radius=4)

        # Animated glow border keyed to category colour
        glow_border(surface, (CX, 2, CW, INTERNAL_H - 4), t, cc,
                    lerp_color(cc, WHITE, 0.5))
        pixel_corners(surface, (CX, 2, CW, INTERNAL_H - 4), cc, size=6)

        # Element info
        text(surface, el["name"].upper(), CC, 10, FONT_LG, WHITE, "center")
        text(surface, el["symbol"],       CX + 8, 10, FONT_LG, cc)
        text(surface, f"#{el['number']}", CX + CW - 8, 10,
             FONT_MD, GRAY, "topright")

        # Divider
        pygame.draw.line(surface, lerp_color(cc, BG, 0.4),
                         (CX + 6, 50), (CX + CW - 6, 50), 1)

        text(surface, f"GROUP {el['group']}   PERIOD {el['period']}",
             CC, 56, FONT_SM, WHITE, "center")
        text(surface, f"MASS  {el['mass']}", CC, 76, FONT_SM, GRAY, "center")
        text(surface, cat.upper(), CC, 96, FONT_SM, cc, "center")

        # Properties
        for i, prop in enumerate(el["properties"][:2]):
            wrap_text(surface, prop, CX + 10, 120 + i * 38,
                      CW - 20, FONT_SM, WHITE, 20)

        # Animated atomic number orbiting decoration
        angle = t * 1.5
        ox = CX + CW - 22
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
                 CC, INTERNAL_H - 18, FONT_SM, GRAY, "center")
        elif self.stage in (self.STAGE_DESC, self.STAGE_ROOM):
            label = ("WHAT IS YOUR CONTAINER?"
                     if self.stage == self.STAGE_DESC
                     else "PLACE IN WHICH ROOM?")
            text(surface, label, CX + 8, INTERNAL_H - 64, FONT_SM, GOLD)
            glow_border(surface, (CX + 4, INTERNAL_H - 46, CW - 8, 26),
                        t, GOLD, TEAL, width=1)
            text(surface, (self.input_text + "_")[:54],
                 CX + 10, INTERNAL_H - 42, FONT_SM, WHITE)
            if self.stage == self.STAGE_ROOM:
                # Quick-pick hints for prebuilt rooms
                hint_c = lerp_color(GRAY, WHITE, 0.4)
                text(surface, "1=KITCHEN   2=BEDROOM   3=GARAGE",
                     CC, INTERNAL_H - 16, FONT_SM - 2, hint_c, "center")

    def _draw_shape_picker(self, surface):
        """Full 49×22 sprite sheet browser using the COLOURED sheet."""
        draw_bg(surface)
        t = get_t()

        # --- layout ---
        # Fit 49 cols in 640px: 640 / 49 ≈ 13 → use 12px per tile + 1px gap = 13px step
        CELL  = 13   # pixels per cell (display)
        TDISPLAY = 12   # tile display size within cell
        ox    = (INTERNAL_W - TILE_COLS * CELL) // 2   # ≈ 2
        oy    = 22   # top of grid (below header)

        title_c = lerp_color(GOLD, TEAL, (math.sin(t * 1.4) + 1) / 2)
        text(surface, "ALL 1078 TILES  –  ARROWS TO BROWSE", MX, 8, FONT_SM - 2, title_c, "center")

        # Draw every tile from the coloured sheet
        for row in range(TILE_ROWS):
            for col in range(TILE_COLS):
                dx = ox + col * CELL
                dy = oy + row * CELL
                tile = get_colored_tile(col, row, TDISPLAY)
                surface.blit(tile, (dx, dy))

        # Cursor over selected tile
        sel_dx = ox + self.picker_col * CELL - 1
        sel_dy = oy + self.picker_row * CELL - 1
        pulse_c = lerp_color(GOLD, WHITE, (math.sin(t * 6) + 1) / 2)
        pygame.draw.rect(surface, pulse_c, (sel_dx, sel_dy, CELL + 1, CELL + 1), 2)

        # Large preview of selected tile (bottom-right)
        preview_size = 48
        px_off = INTERNAL_W - preview_size - 6
        py_off = INTERNAL_H - preview_size - 22
        preview = get_colored_tile(self.picker_col, self.picker_row, preview_size)
        pygame.draw.rect(surface, PANEL_BG, (px_off - 2, py_off - 2, preview_size + 4, preview_size + 4))
        pygame.draw.rect(surface, GOLD,     (px_off - 2, py_off - 2, preview_size + 4, preview_size + 4), 1)
        surface.blit(preview, (px_off, py_off))

        # Selected tile name / position
        name = tile_key(self.picker_col, self.picker_row)
        label = name.replace("t_", "").replace("_", ",") if name.startswith("t_") else name.upper()
        glow_border(surface, (2, INTERNAL_H - 36, INTERNAL_W - preview_size - 16, 20), t, GOLD, TEAL, 1)
        text(surface, label, 10, INTERNAL_H - 32, FONT_SM, GOLD)
        text(surface, "ARROWS · ENTER CONFIRM",
             INTERNAL_W - preview_size - 10, INTERNAL_H - 12, FONT_SM - 2, GRAY, "topright")


# ---------------------------------------------------------------------------
# Palace View Screen  (full-screen schematic + cat)
# ---------------------------------------------------------------------------

class PalaceScreen(Screen):
    _MAP_H = 50   # minimap strip height at bottom

    def __init__(self, game):
        super().__init__(game)
        game.cat.player_controlled = True
        n = len(game.palace.rooms)
        if n > 0:
            game.cat.room_idx = max(0, min(game.cat.room_idx, n - 1))

    def update(self, events):
        cat    = self.game.cat
        n      = len(self.game.palace.rooms)
        cols   = FULL["cols"]
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return {"action": "home"}
                elif e.key == pygame.K_RIGHT:
                    cat.move_room("right", n, cols)
                elif e.key == pygame.K_LEFT:
                    cat.move_room("left", n, cols)
                elif e.key == pygame.K_DOWN:
                    cat.move_room("down", n, cols)
                elif e.key == pygame.K_UP:
                    cat.move_room("up", n, cols)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if n > 0:
                        return {"action": "view_room", "room_idx": cat.room_idx}
        return None

    def draw(self, surface):
        draw_bg(surface)
        t       = get_t()
        palace  = self.game.palace
        map_y   = INTERNAL_H - self._MAP_H

        title_c = lerp_color(GOLD, TEAL, (math.sin(t * 1.5) + 1) / 2)
        text(surface, "MEMORY PALACE", MX, 7, FONT_MD, title_c, "center")

        if not palace.rooms:
            text(surface, "PALACE IS EMPTY — ADD AN ELEMENT FIRST",
                 MX, MY, FONT_SM, GRAY, "center")
        else:
            draw_palace_panel(surface, palace, self.game.cat, FULL, 0, 0)
            draw_floor_map(surface, palace, self.game.cat,
                           0, map_y, INTERNAL_W, self._MAP_H - 14)

        text(surface, "ARROWS MOVE  ENTER INSPECT  ESC HOME",
             MX, INTERNAL_H - 10, FONT_SM - 2, GRAY, "center")
        draw_scanlines(surface)


# ---------------------------------------------------------------------------
# Rooms Browser  (two-panel: room list left | full room detail right)
# ---------------------------------------------------------------------------

class RoomsScreen(Screen):
    """
    Two-panel rooms browser.
    Left: scrollable room list.
    Right: full-screen wireframe 3D room (Manim aesthetic).
    """
    # Viewport for the wireframe render (right panel)
    _VP_X = _ROOMS_PW + 4
    _VP_Y = 4
    _VP_W = INTERNAL_W - _ROOMS_PW - 8
    _VP_H = INTERNAL_H - 28   # leave room for hint strip

    def __init__(self, game, room_idx=0):
        super().__init__(game)
        import wireframe as wf
        self._wf = wf
        n = len(game.palace.rooms)
        self.room_idx = max(0, min(room_idx, n - 1)) if n else 0
        self.cont_idx = 0
        self.scroll   = 0
        self._after_quiz = False   # flag: show CONTINUE button

    # ---- navigation ----

    def update(self, events):
        rooms = self.game.palace.rooms
        n     = len(rooms)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return {"action": "home"}
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return {"action": "continue"}
                elif e.key in (pygame.K_UP, pygame.K_w):
                    if n:
                        self.room_idx = (self.room_idx - 1) % n
                        self.cont_idx = 0
                        self._fix_scroll(n)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    if n:
                        self.room_idx = (self.room_idx + 1) % n
                        self.cont_idx = 0
                        self._fix_scroll(n)
                elif e.key == pygame.K_LEFT:
                    if n and rooms[self.room_idx].containers:
                        nc = len(rooms[self.room_idx].containers)
                        self.cont_idx = (self.cont_idx - 1) % nc
                elif e.key == pygame.K_RIGHT:
                    if n and rooms[self.room_idx].containers:
                        nc = len(rooms[self.room_idx].containers)
                        self.cont_idx = (self.cont_idx + 1) % nc
        return None

    def _fix_scroll(self, n):
        vis = max(1, (INTERNAL_H - 22) // _ROOMS_CH)
        self.scroll = max(0, min(self.scroll, n - vis))
        if self.room_idx < self.scroll:
            self.scroll = self.room_idx
        elif self.room_idx >= self.scroll + vis:
            self.scroll = self.room_idx - vis + 1

    # ---- drawing ----

    def draw(self, surface):
        # Dark Manim-style background for the right panel
        surface.fill(BG)
        pygame.draw.rect(surface, (4, 4, 12),
                         (self._VP_X, self._VP_Y, self._VP_W, self._VP_H))

        t     = get_t()
        rooms = self.game.palace.rooms

        if not rooms:
            text(surface, "NO ROOMS YET — ADD AN ELEMENT FIRST",
                 MX, MY, FONT_SM, GRAY, "center")
            text(surface, "ESC HOME", MX, INTERNAL_H - 12, FONT_SM - 2, GRAY, "center")
            draw_scanlines(surface)
            return

        self._draw_left(surface, rooms, t)
        self._draw_wireframe(surface, rooms, t)
        self._draw_containers_overlay(surface, rooms, t)
        self._draw_hints(surface, t)
        draw_scanlines(surface)

    # ---- left panel ----

    def _draw_left(self, surface, rooms, t):
        pygame.draw.rect(surface, PANEL_BG, (0, 0, _ROOMS_PW, INTERNAL_H))
        pygame.draw.line(surface, GRAY, (_ROOMS_PW, 0), (_ROOMS_PW, INTERNAL_H), 1)
        tc = lerp_color(GOLD, TEAL, (math.sin(t * 1.4) + 1) / 2)
        text(surface, "MY ROOMS", _ROOMS_PW // 2, 6, FONT_SM, tc, "center")

        vis = max(1, (INTERNAL_H - 22) // _ROOMS_CH)
        for slot in range(vis):
            i = self.scroll + slot
            if i >= len(rooms):
                break
            room = rooms[i]
            sel  = (i == self.room_idx)
            ry   = 20 + slot * _ROOMS_CH
            rc   = room_color(room.name)
            bg   = lerp_color(rc, BG, 0.55) if sel else lerp_color(rc, BG, 0.84)
            pygame.draw.rect(surface, bg, (3, ry, _ROOMS_PW - 6, _ROOMS_CH - 3),
                             border_radius=3)
            bw = 2 if sel else 1
            bc = lerp_color(GOLD, WHITE, (math.sin(t * 5) + 1) / 2) if sel \
                 else lerp_color(rc, BG, 0.35)
            pygame.draw.rect(surface, bc, (3, ry, _ROOMS_PW - 6, _ROOMS_CH - 3),
                             bw, border_radius=3)
            nc_col = GOLD if sel else lerp_color(rc, WHITE, 0.80)
            text(surface, room.name.upper()[:16], 8, ry + 5,
                 max(6, FONT_SM - 2), nc_col)
            for j, cont in enumerate(room.containers[:4]):
                draw_sprite(surface, cont.shape, lerp_color(rc, WHITE, 0.55),
                            10 + j * 16, ry + _ROOMS_CH - 10, 11)
            nc = len(room.containers)
            if nc:
                text(surface, str(nc), _ROOMS_PW - 8, ry + 5,
                     max(5, FONT_SM - 3), GRAY, "topright")

    # ---- wireframe right panel ----

    def _draw_wireframe(self, surface, rooms, t):
        if self.room_idx >= len(rooms):
            return
        room      = rooms[self.room_idx]
        rt        = room.room_type or ""
        wire_room = self._wf.get_room(rt)
        if wire_room is None:
            # Custom / unknown room type — fall back to a label
            rc = room_color(room.name)
            cx = self._VP_X + self._VP_W // 2
            cy = self._VP_Y + self._VP_H // 2
            text(surface, room.name.upper(), cx, cy - 10, FONT_MD,
                 lerp_color(rc, WHITE, 0.7), "center")
            text(surface, "CUSTOM ROOM", cx, cy + 14, FONT_SM, GRAY, "center")
            return

        # Which slots are occupied?
        occupied = {cont.description.split()[0].lower()
                    for cont in room.containers}
        wire_room.draw(surface, t,
                       vp_x=self._VP_X, vp_y=self._VP_Y,
                       vp_w=self._VP_W, vp_h=self._VP_H,
                       active_slots=occupied)

        # Room name at top of viewport
        rc = (wire_room.ROOM_COLOR[0]//2 + 128,
              wire_room.ROOM_COLOR[1]//2 + 128,
              wire_room.ROOM_COLOR[2]//2 + 128)
        text(surface, wire_room.NAME.upper(),
             self._VP_X + self._VP_W // 2, self._VP_Y + 6,
             FONT_MD, rc, "center")

    # ---- container sprites overlaid on wireframe ----

    def _draw_containers_overlay(self, surface, rooms, t):
        if self.room_idx >= len(rooms):
            return
        room = rooms[self.room_idx]
        if not room.containers:
            return
        rt        = room.room_type or ""
        wire_room = self._wf.get_room(rt)

        conts  = room.containers
        n      = len(conts)
        # Lay out containers in a row near the bottom of the viewport
        cy_base = self._VP_Y + self._VP_H - 44
        cell_w  = min(80, self._VP_W // max(n, 1))
        start_x = self._VP_X + (self._VP_W - cell_w * n) // 2

        for j, cont in enumerate(conts):
            ccx = start_x + j * cell_w + cell_w // 2
            sel = (j == self.cont_idx)
            sp_sz = 22 if sel else 18
            pulse = lerp_color(TEAL, WHITE, (math.sin(t * 2 + j) + 1) / 4)
            spr_col = lerp_color(GOLD, WHITE, 0.30) if sel else pulse
            draw_sprite(surface, cont.shape, spr_col, ccx, cy_base, sp_sz)
            if sel:
                pc = lerp_color(GOLD, WHITE, (math.sin(t * 6) + 1) / 2)
                pygame.draw.rect(surface, pc,
                                 (ccx - sp_sz//2 - 2, cy_base - sp_sz//2 - 2,
                                  sp_sz + 4, sp_sz + 4), 1, border_radius=2)
            dy = cy_base + sp_sz // 2 + 4
            text(surface, cont.description[:10].upper(),
                 ccx, dy, max(5, FONT_SM - 2), GOLD if sel else TEAL, "center")
            for k, el in enumerate(cont.elements[:2]):
                text(surface, el[:10].upper(), ccx, dy + 9 + k * 8,
                     max(4, FONT_SM - 3), WHITE, "center")

    # ---- hint bar ----

    def _draw_hints(self, surface, t):
        hint_y = INTERNAL_H - 14
        # CONTINUE button (prominent after quiz)
        cont_c = lerp_color(GOLD, WHITE, (math.sin(t * 4) + 1) / 2)
        text(surface, "ENTER CONTINUE",
             self._VP_X + self._VP_W // 2, hint_y,
             FONT_SM - 2, cont_c, "center")
        text(surface, "W/S ROOM  < > CONTAINER  ESC HOME",
             self._VP_X + self._VP_W // 2, hint_y - 10,
             max(5, FONT_SM - 3), GRAY, "center")


# ---------------------------------------------------------------------------
# Room Inspection Screen  (zoomed view: full room + all containers)
# ---------------------------------------------------------------------------

class RoomScreen(Screen):
    """Full-screen zoom into one room — see every container and its element."""
    _HDR_H = 22   # header height
    _MAP_H = 46   # minimap strip at bottom

    def __init__(self, game, room_idx=0):
        super().__init__(game)
        game.cat.player_controlled = True
        self.room_idx = max(0, min(room_idx, len(game.palace.rooms) - 1))
        game.cat.room_idx = self.room_idx
        self.cont_idx = 0

    # ---- navigation ----

    def update(self, events):
        palace = self.game.palace
        rooms  = palace.rooms
        if not rooms:
            return {"action": "palace"}
        room   = rooms[self.room_idx]
        n_cont = len(room.containers)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return {"action": "palace"}
                elif e.key == pygame.K_RIGHT:
                    if n_cont > 0:
                        self.cont_idx = (self.cont_idx + 1) % n_cont
                elif e.key == pygame.K_LEFT:
                    if n_cont > 0:
                        self.cont_idx = (self.cont_idx - 1) % n_cont
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    nr = min(len(rooms) - 1, self.room_idx + 1)
                    if nr != self.room_idx:
                        self.room_idx = nr
                        self.game.cat.room_idx = nr
                        self.cont_idx = 0
                elif e.key in (pygame.K_UP, pygame.K_w):
                    nr = max(0, self.room_idx - 1)
                    if nr != self.room_idx:
                        self.room_idx = nr
                        self.game.cat.room_idx = nr
                        self.cont_idx = 0
        return None

    # ---- drawing ----

    def draw(self, surface):
        draw_bg(surface)
        t      = get_t()
        palace = self.game.palace
        rooms  = palace.rooms
        if not rooms:
            text(surface, "PALACE IS EMPTY", MX, MY, FONT_SM, GRAY, "center")
            draw_scanlines(surface)
            return

        room = rooms[self.room_idx]
        rc   = room_color(room.name)

        # --- Room area (fills between header and minimap) ---
        rx = 4
        ry = self._HDR_H
        rw = INTERNAL_W - 8
        rh = INTERNAL_H - self._HDR_H - self._MAP_H - 4
        ix, iy, iw, ih = draw_topdown_room(
            surface, rx, ry, rw, rh, rc, room.name, t, highlighted=False)

        # --- Containers ---
        if iw > 0 and ih > 0 and room.containers:
            self._draw_containers(surface, room, ix, iy, iw, ih, t)

        # --- Header bar ---
        title_c = lerp_color(rc, WHITE, 0.75)
        text(surface, room.name.upper(), MX, 5, FONT_MD, title_c, "center")
        text(surface, f"{self.room_idx+1}/{len(rooms)}",
             INTERNAL_W - 6, 5, FONT_SM, GRAY, "topright")

        # --- Minimap ---
        map_y = INTERNAL_H - self._MAP_H
        draw_floor_map(surface, palace, self.game.cat,
                       0, map_y, INTERNAL_W, self._MAP_H - 12)
        text(surface, "< > CONTAINER   W/S ROOM   ESC BACK",
             MX, INTERNAL_H - 10, FONT_SM - 2, GRAY, "center")
        draw_scanlines(surface)

    def _draw_containers(self, surface, room, ix, iy, iw, ih, t):
        """Lay out containers in a grid inside the room interior."""
        conts  = room.containers
        n      = len(conts)
        cols_c = min(6, n)
        rows_c = (n + cols_c - 1) // cols_c
        cell_w = max(1, iw // cols_c)
        cell_h = max(1, ih // rows_c)
        sp_sz  = max(22, min(32, min(cell_w, cell_h) - 18))

        for j, cont in enumerate(conts):
            col_j = j % cols_c
            row_j = j // cols_c
            ccx   = ix + col_j * cell_w + cell_w // 2
            ccy   = iy + row_j * cell_h + max(sp_sz, cell_h // 3)
            sel   = (j == self.cont_idx)

            # Sprite
            pulse   = lerp_color(TEAL, WHITE, (math.sin(t * 2 + j) + 1) / 4)
            spr_col = lerp_color(GOLD, WHITE, 0.30) if sel else pulse
            draw_sprite(surface, cont.shape, spr_col, ccx, ccy, sp_sz)

            # Selection box
            if sel:
                bx = ccx - sp_sz // 2 - 3
                by = ccy - sp_sz // 2 - 3
                bs = sp_sz + 6
                pulse_c = lerp_color(GOLD, WHITE, (math.sin(t * 6) + 1) / 2)
                pygame.draw.rect(surface, pulse_c, (bx, by, bs, bs), 1,
                                 border_radius=2)

            # Description label
            desc_y = ccy + sp_sz // 2 + 3
            text(surface, cont.description[:12].upper(),
                 ccx, desc_y, max(5, FONT_SM - 2),
                 GOLD if sel else TEAL, "center")

            # Element names (one per line, small font)
            for k, el_name in enumerate(cont.elements[:3]):
                text(surface, el_name[:10].upper(),
                     ccx, desc_y + 10 + k * 9,
                     max(4, FONT_SM - 3), WHITE, "center")


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
