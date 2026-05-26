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
)

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


def draw_palace_panel(surface, palace, cat, layout_params, offset_x=0, offset_y=0):
    """Draw rooms + containers + cat inside a given layout.
    offset_x/y shift all drawing (used when panel is not at screen origin).
    """
    rooms  = palace.rooms
    layout = palace_layout(len(rooms), **layout_params)

    for i, room in enumerate(rooms):
        rx, ry, rw, rh = layout[i]
        rx, ry = rx + offset_x, ry + offset_y
        panel(surface, (rx, ry, rw, rh), PANEL_BG, GOLD)
        text(surface, room.name.upper()[:14], rx + rw//2, ry + 5, FONT_SM - 2, GOLD, "center")
        for j, cont in enumerate(room.containers[:6]):
            cell_w = rw // 3
            cx = rx + (j % 3) * cell_w + cell_w // 2
            cy = ry + 22 + (j // 3) * (rh // 2 - 8)
            shape_size = max(8, min(12, layout_params["rw"] // 12))
            draw_shape(surface, cont.shape, TEAL, cx, cy, shape_size)

    # Draw cat
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
        surface.fill(BG)
        text(surface, "MEMORY", MX, 62, FONT_LG, GOLD, "center")
        text(surface, "PALACE", MX, 100, FONT_LG, GOLD, "center")
        for i, (label, _) in enumerate(self.MENU):
            y   = 162 + i * 40
            col = TEAL if i == self.selected else GRAY
            pre = "> " if i == self.selected else "  "
            text(surface, pre + label, MX, y, FONT_MD, col, "center")
        text(surface, "UP / DOWN     ENTER", MX, INTERNAL_H - 18, FONT_SM, GRAY, "center")


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
        surface.fill(BG)
        if self.stage == self.STAGE_SHAPE:
            self._draw_shape_picker(surface)
        else:
            self._draw_left_palace(surface)
            self._draw_right_card(surface)

    def _draw_left_palace(self, surface):
        panel(surface, (2, 2, PALACE_W, INTERNAL_H - 4))
        text(surface, "PALACE", PALACE_W // 2, 8, FONT_SM, GOLD, "center")
        if not self.game.palace.rooms:
            text(surface, "EMPTY", PALACE_W // 2, MY, FONT_SM - 2, GRAY, "center")
        else:
            draw_palace_panel(surface, self.game.palace, self.game.cat, MINI, 2, 2)

    def _draw_right_card(self, surface):
        el = self.element
        panel(surface, (CARD_X, 2, CARD_W, INTERNAL_H - 4))

        # element info
        text(surface, el["name"].upper(), CARD_CX, 12, FONT_LG, GOLD, "center")
        text(surface, el["symbol"],        CARD_X + 8, 12, FONT_LG, TEAL)
        text(surface, f"#{el['number']}",  CARD_X + CARD_W - 8, 12, FONT_MD, GRAY, "topright")
        text(surface, f"GROUP {el['group']}   PERIOD {el['period']}",
             CARD_CX, 52, FONT_SM, WHITE, "center")
        text(surface, f"MASS  {el['mass']}", CARD_CX, 72, FONT_SM, GRAY, "center")
        text(surface, el["category"].upper(), CARD_CX, 92, FONT_SM, TEAL, "center")
        for i, prop in enumerate(el["properties"][:2]):
            wrap_text(surface, prop, CARD_X + 10, 116 + i * 38, CARD_W - 20,
                      FONT_SM, WHITE, 20)

        # stage-specific bottom section
        if self.stage == self.STAGE_INFO:
            text(surface, "ENTER TO CONTINUE",
                 CARD_CX, INTERNAL_H - 18, FONT_SM, GRAY, "center")
        elif self.stage in (self.STAGE_DESC, self.STAGE_ROOM):
            label = ("WHAT IS YOUR CONTAINER?"
                     if self.stage == self.STAGE_DESC
                     else "PLACE IN WHICH ROOM?")
            text(surface, label, CARD_X + 8, INTERNAL_H - 52, FONT_SM, GOLD)
            panel(surface, (CARD_X + 4, INTERNAL_H - 34, CARD_W - 8, 26))
            text(surface, (self.input_text + "_")[:34],
                 CARD_X + 10, INTERNAL_H - 30, FONT_SM, WHITE)
        elif self.stage == self.STAGE_ROOM:
            # preview already embedded above for room stage via _draw_preview_small
            pass

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
        surface.fill(BG)
        text(surface, "MEMORY PALACE", MX, 8, FONT_MD, GOLD, "center")
        palace = self.game.palace
        if not palace.rooms:
            text(surface, "PALACE IS EMPTY", MX, MY, FONT_SM, GRAY, "center")
        else:
            draw_palace_panel(surface, palace, self.game.cat, FULL, 0, 0)
        text(surface, "ESC = HOME", MX, INTERNAL_H - 12, FONT_SM, GRAY, "center")


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
        surface.fill(BG)
        el = self.elements[self.index]
        text(surface, "FLASHCARD MODE", MX, 8, FONT_MD, GOLD, "center")
        panel(surface, (14, 28, INTERNAL_W - 28, INTERNAL_H - 52))
        text(surface, el["name"].upper(), MX,   42, FONT_LG, GOLD, "center")
        text(surface, el["symbol"],        28,  42, FONT_LG, TEAL)
        text(surface, f"#{el['number']}", INTERNAL_W - 28, 42, FONT_MD, GRAY, "topright")
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
