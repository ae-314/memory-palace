"""
All Pygame rendering.
Each screen is a self-contained class with update(events) -> dict|None and draw(surface).
No game logic or persistence lives here.
"""

import pygame
import math
from constants import (
    BG, PANEL_BG, WHITE, BLACK, GOLD, TEAL, RED, GREEN, GRAY,
    HIGHLIGHT, PURPLE, ORANGE, PINK,
    FONT_SM, FONT_MD, FONT_LG, PIXEL_FONT,
    INTERNAL_W, INTERNAL_H, SHAPES,
)


# ---------------------------------------------------------------------------
# Font helper
# ---------------------------------------------------------------------------

_font_cache = {}

def font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        try:
            _font_cache[size] = pygame.font.Font(PIXEL_FONT, size)
        except FileNotFoundError:
            _font_cache[size] = pygame.font.SysFont("monospace", size)
    return _font_cache[size]


def text(surface, msg: str, x: int, y: int, size: int = FONT_MD,
         colour=WHITE, anchor="topleft"):
    img = font(size).render(msg, False, colour)
    r = img.get_rect(**{anchor: (x, y)})
    surface.blit(img, r)


def wrap_text(surface, msg: str, x: int, y: int, max_w: int,
              size: int = FONT_SM, colour=WHITE, line_h: int = 10):
    words = msg.split()
    line, lines = [], []
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


def panel(surface, rect, colour=PANEL_BG, border=GOLD, radius=3):
    pygame.draw.rect(surface, colour, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 1, border_radius=radius)


# ---------------------------------------------------------------------------
# Shape drawing
# ---------------------------------------------------------------------------

def draw_shape(surface, shape: str, colour, cx: int, cy: int, size: int = 12):
    """Draw a named container shape centred at (cx, cy)."""
    s = size
    pts = None

    if shape == "diamond":
        pts = [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)]
    elif shape == "triangle":
        pts = [(cx, cy-s), (cx+s, cy+s), (cx-s, cy+s)]
    elif shape == "star":
        pts = _star_points(cx, cy, s, s//2, 5)
    elif shape == "pentagon":
        pts = _poly_points(cx, cy, s, 5)
    elif shape == "hexagon":
        pts = _poly_points(cx, cy, s, 6)
    elif shape == "heart":
        _draw_heart(surface, colour, cx, cy, s)
        return
    elif shape == "cross":
        t = max(2, s//3)
        pygame.draw.rect(surface, colour, (cx-t, cy-s, t*2, s*2))
        pygame.draw.rect(surface, colour, (cx-s, cy-t, s*2, t*2))
        return
    elif shape == "crown":
        pts = [(cx-s, cy+s//2), (cx-s, cy-s//2), (cx-s//2, cy),
               (cx, cy-s), (cx+s//2, cy), (cx+s, cy-s//2), (cx+s, cy+s//2)]
    elif shape == "shield":
        pts = [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)]
    elif shape == "circle" or shape == "orb":
        pygame.draw.circle(surface, colour, (cx, cy), s)
        return
    elif shape == "ring":
        pygame.draw.circle(surface, colour, (cx, cy), s, max(2, s//4))
        return
    elif shape == "moon":
        pygame.draw.circle(surface, colour, (cx, cy), s)
        pygame.draw.circle(surface, BG, (cx+s//3, cy-s//4), int(s*0.75))
        return
    elif shape == "drop":
        pts = _drop_points(cx, cy, s)
    elif shape == "flame":
        pts = _flame_points(cx, cy, s)
    elif shape == "leaf":
        pts = _leaf_points(cx, cy, s)
    elif shape == "bolt":
        pts = [(cx, cy-s), (cx+s//3, cy-s//4),
               (cx, cy+s//4), (cx+s//2, cy+s)]
    elif shape == "spiral":
        _draw_spiral(surface, colour, cx, cy, s)
        return
    elif shape == "flask":
        _draw_flask(surface, colour, cx, cy, s)
        return
    elif shape == "crystal" or shape == "gem":
        pts = [(cx, cy-s), (cx+s, cy-s//3), (cx+s//2, cy+s),
               (cx-s//2, cy+s), (cx-s, cy-s//3)]
    elif shape == "cube":
        _draw_cube(surface, colour, cx, cy, s)
        return
    elif shape == "square":
        pygame.draw.rect(surface, colour, (cx-s, cy-s, s*2, s*2))
        return
    elif shape == "chest":
        _draw_chest(surface, colour, cx, cy, s)
        return
    elif shape == "cage":
        _draw_cage(surface, colour, cx, cy, s)
        return
    else:
        # fallback
        pygame.draw.rect(surface, colour, (cx-s, cy-s, s*2, s*2))
        return

    if pts:
        pygame.draw.polygon(surface, colour, pts)


# --- Shape helpers ---

def _poly_points(cx, cy, r, n):
    return [(int(cx + r * math.cos(math.pi/2 + 2*math.pi*i/n)),
             int(cy - r * math.sin(math.pi/2 + 2*math.pi*i/n))) for i in range(n)]

def _star_points(cx, cy, r_out, r_in, n=5):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi / 2 + math.pi * i / n
        pts.append((int(cx + r * math.cos(a)), int(cy - r * math.sin(a))))
    return pts

def _draw_heart(surface, colour, cx, cy, s):
    r = max(2, s // 2)
    pygame.draw.circle(surface, colour, (cx - r//2, cy - r//2), r)
    pygame.draw.circle(surface, colour, (cx + r//2, cy - r//2), r)
    pts = [(cx - s, cy - r//2), (cx, cy + s), (cx + s, cy - r//2)]
    pygame.draw.polygon(surface, colour, pts)

def _drop_points(cx, cy, s):
    return [(cx, cy - s), (cx + s//2, cy), (cx + s//3, cy + s//2),
            (cx, cy + s), (cx - s//3, cy + s//2), (cx - s//2, cy)]

def _flame_points(cx, cy, s):
    return [(cx, cy - s), (cx + s//2, cy - s//3), (cx + s//3, cy + s//2),
            (cx, cy + s), (cx - s//3, cy + s//2), (cx - s//2, cy - s//3)]

def _leaf_points(cx, cy, s):
    return [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]

def _draw_spiral(surface, colour, cx, cy, s):
    pts = []
    for i in range(60):
        a = i * 0.2
        r = i * s / 60
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    if len(pts) >= 2:
        pygame.draw.lines(surface, colour, False, pts, 1)

def _draw_flask(surface, colour, cx, cy, s):
    # neck
    pygame.draw.rect(surface, colour, (cx - s//4, cy - s, s//2, s//2))
    # body
    pts = [(cx - s//4, cy - s//2), (cx - s, cy + s//2),
           (cx + s, cy + s//2), (cx + s//4, cy - s//2)]
    pygame.draw.polygon(surface, colour, pts)

def _draw_cube(surface, colour, cx, cy, s):
    # front face
    pygame.draw.rect(surface, colour, (cx - s//2, cy, s, s))
    # top face
    top = [(cx - s//2, cy), (cx, cy - s//2), (cx + s//2, cy), (cx, cy + s//2 - s)]
    # simplify: just draw offset square
    pygame.draw.rect(surface, colour, (cx, cy - s//2, s, s))
    pygame.draw.line(surface, BG, (cx, cy), (cx, cy - s//2), 1)

def _draw_chest(surface, colour, cx, cy, s):
    # body
    pygame.draw.rect(surface, colour, (cx - s, cy, s*2, s))
    # lid (arc suggestion with a rect)
    pygame.draw.rect(surface, colour, (cx - s, cy - s//2, s*2, s//2))
    # clasp
    pygame.draw.rect(surface, GOLD, (cx - s//6, cy - s//8, s//3, s//4))

def _draw_cage(surface, colour, cx, cy, s):
    pygame.draw.rect(surface, colour, (cx - s, cy - s, s*2, s*2), 1)
    # bars
    for i in range(-1, 2):
        pygame.draw.line(surface, colour, (cx + i*(s//2), cy - s), (cx + i*(s//2), cy + s), 1)
    pygame.draw.line(surface, colour, (cx - s, cy), (cx + s, cy), 1)


# ---------------------------------------------------------------------------
# Base Screen
# ---------------------------------------------------------------------------

class Screen:
    def __init__(self, game):
        self.game = game

    def update(self, events) -> dict | None:
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
        text(surface, "MEMORY", INTERNAL_W//2, 40, FONT_LG, GOLD, "center")
        text(surface, "PALACE", INTERNAL_W//2, 58, FONT_LG, GOLD, "center")
        for i, (label, _) in enumerate(self.MENU):
            y = 110 + i * 24
            col = TEAL if i == self.selected else GRAY
            prefix = "> " if i == self.selected else "  "
            text(surface, prefix + label, INTERNAL_W//2, y, FONT_MD, col, "center")
        text(surface, "UP/DOWN  ENTER", INTERNAL_W//2, INTERNAL_H - 14, FONT_SM, GRAY, "center")


# ---------------------------------------------------------------------------
# Element Card Screen
# ---------------------------------------------------------------------------

class ElementScreen(Screen):
    """Show element info, prompt for container description and shape."""

    STAGE_INFO      = "info"       # reading the card
    STAGE_DESC      = "desc"       # typing container description
    STAGE_SHAPE     = "shape"      # picking shape from grid
    STAGE_ROOM      = "room"       # typing room name

    COLS, ROWS = 5, 5              # shape picker grid

    def __init__(self, game, element: dict):
        super().__init__(game)
        self.element    = element
        self.stage      = self.STAGE_INFO
        self.input_text = ""
        self.container_desc  = ""
        self.chosen_shape    = 0
        self.room_name       = ""

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
                        self.input_text = ""
                        self.stage = self.STAGE_SHAPE
                        pygame.key.stop_text_input()
                    elif e.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]

                elif self.stage == self.STAGE_SHAPE:
                    cols = self.COLS
                    if e.key == pygame.K_RIGHT:
                        self.chosen_shape = (self.chosen_shape + 1) % len(SHAPES)
                    elif e.key == pygame.K_LEFT:
                        self.chosen_shape = (self.chosen_shape - 1) % len(SHAPES)
                    elif e.key == pygame.K_DOWN:
                        self.chosen_shape = (self.chosen_shape + cols) % len(SHAPES)
                    elif e.key == pygame.K_UP:
                        self.chosen_shape = (self.chosen_shape - cols) % len(SHAPES)
                    elif e.key == pygame.K_RETURN:
                        self.stage = self.STAGE_ROOM
                        pygame.key.start_text_input()

                elif self.stage == self.STAGE_ROOM:
                    if e.key == pygame.K_RETURN and self.input_text.strip():
                        self.room_name = self.input_text.strip()
                        self._commit()
                        return {"action": "element_stored"}
                    elif e.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]

            elif e.type == pygame.TEXTINPUT:
                if self.stage in (self.STAGE_DESC, self.STAGE_ROOM):
                    self.input_text += e.text

        return None

    def _commit(self):
        from palace import Container
        container = Container(
            description=self.container_desc,
            shape=SHAPES[self.chosen_shape],
        )
        self.game.palace.store_element(self.element["name"], container, self.room_name)

    def draw(self, surface):
        surface.fill(BG)
        el = self.element

        if self.stage == self.STAGE_INFO:
            self._draw_card(surface, el)
            text(surface, "PRESS ENTER TO CONTINUE", INTERNAL_W//2,
                 INTERNAL_H - 12, FONT_SM, GRAY, "center")

        elif self.stage == self.STAGE_DESC:
            self._draw_card(surface, el)
            text(surface, "CONTAINER DESCRIPTION:", 8, INTERNAL_H - 32, FONT_SM, GOLD)
            panel(surface, (6, INTERNAL_H - 20, INTERNAL_W - 12, 14))
            display = self.input_text + "_"
            text(surface, display[:38], 10, INTERNAL_H - 18, FONT_SM, WHITE)

        elif self.stage == self.STAGE_SHAPE:
            self._draw_shape_picker(surface)

        elif self.stage == self.STAGE_ROOM:
            self._draw_preview(surface)
            text(surface, "PLACE IN ROOM:", 8, INTERNAL_H - 32, FONT_SM, GOLD)
            panel(surface, (6, INTERNAL_H - 20, INTERNAL_W - 12, 14))
            display = self.input_text + "_"
            text(surface, display[:38], 10, INTERNAL_H - 18, FONT_SM, WHITE)

    def _draw_card(self, surface, el):
        panel(surface, (4, 4, INTERNAL_W - 8, 100))
        text(surface, el["name"].upper(), INTERNAL_W//2, 12, FONT_LG, GOLD, "center")
        text(surface, el["symbol"], 14, 12, FONT_LG, TEAL)
        text(surface, f"#{el['number']}", INTERNAL_W - 14, 12, FONT_MD, GRAY, "topright")
        text(surface, f"GROUP {el['group']}  PERIOD {el['period']}", INTERNAL_W//2, 30, FONT_SM, WHITE, "center")
        text(surface, f"MASS {el['mass']}", INTERNAL_W//2, 42, FONT_SM, GRAY, "center")
        text(surface, el["category"].upper(), INTERNAL_W//2, 54, FONT_SM, TEAL, "center")
        for i, prop in enumerate(el["properties"][:2]):
            wrap_text(surface, prop, 10, 68 + i * 14, INTERNAL_W - 20, FONT_SM, WHITE)

    def _draw_shape_picker(self, surface):
        text(surface, "CHOOSE A SHAPE", INTERNAL_W//2, 6, FONT_MD, GOLD, "center")
        cols, cell = self.COLS, 34
        ox = (INTERNAL_W - cols * cell) // 2
        oy = 20
        for i, shape in enumerate(SHAPES):
            row, col = divmod(i, cols)
            cx = ox + col * cell + cell // 2
            cy = oy + row * cell + cell // 2
            if i == self.chosen_shape:
                pygame.draw.rect(surface, HIGHLIGHT,
                                 (cx - cell//2, cy - cell//2, cell, cell), border_radius=2)
            draw_shape(surface, shape, TEAL if i == self.chosen_shape else GRAY, cx, cy, 9)
        sel_name = SHAPES[self.chosen_shape].upper()
        text(surface, sel_name, INTERNAL_W//2, INTERNAL_H - 22, FONT_SM, WHITE, "center")
        text(surface, "ARROWS  ENTER TO CONFIRM", INTERNAL_W//2, INTERNAL_H - 10, FONT_SM, GRAY, "center")

    def _draw_preview(self, surface):
        text(surface, "CONTAINER PREVIEW", INTERNAL_W//2, 8, FONT_SM, GOLD, "center")
        draw_shape(surface, SHAPES[self.chosen_shape], TEAL, INTERNAL_W//2, 80, 20)
        text(surface, self.element["name"].upper(), INTERNAL_W//2, 108, FONT_SM, WHITE, "center")
        text(surface, f'"{self.container_desc}"', INTERNAL_W//2, 120, FONT_SM, GRAY, "center")


# ---------------------------------------------------------------------------
# Palace View Screen
# ---------------------------------------------------------------------------

class PalaceScreen(Screen):
    """Architectural schematic: rooms as labelled boxes, containers as small shapes."""

    def __init__(self, game):
        super().__init__(game)

    def update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return {"action": "home"}
        return None

    def draw(self, surface):
        surface.fill(BG)
        text(surface, "MEMORY PALACE", INTERNAL_W//2, 4, FONT_MD, GOLD, "center")
        rooms = self.game.palace.rooms
        if not rooms:
            text(surface, "PALACE IS EMPTY", INTERNAL_W//2, INTERNAL_H//2, FONT_SM, GRAY, "center")
            text(surface, "ESC = HOME", INTERNAL_W//2, INTERNAL_H - 10, FONT_SM, GRAY, "center")
            return
        self._draw_rooms(surface, rooms)
        text(surface, "ESC = HOME", INTERNAL_W//2, INTERNAL_H - 10, FONT_SM, GRAY, "center")

    def _draw_rooms(self, surface, rooms):
        cols = 2
        rw, rh = 140, 80
        pad = 6
        ox, oy = 10, 20
        for i, room in enumerate(rooms):
            row, col = divmod(i, cols)
            rx = ox + col * (rw + pad)
            ry = oy + row * (rh + pad)
            panel(surface, (rx, ry, rw, rh), PANEL_BG, GOLD)
            text(surface, room.name.upper()[:16], rx + rw//2, ry + 4, FONT_SM, GOLD, "center")
            for j, cont in enumerate(room.containers[:6]):
                cx = rx + 14 + (j % 3) * 44
                cy = ry + 26 + (j // 3) * 28
                draw_shape(surface, cont.shape, TEAL, cx, cy, 8)
                label = cont.description[:8]
                text(surface, label, cx, cy + 11, FONT_SM - 1, GRAY, "center")


# ---------------------------------------------------------------------------
# Flashcard Screen
# ---------------------------------------------------------------------------

class FlashcardScreen(Screen):
    """Flip through element cards freely — not part of the game loop."""

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
        text(surface, "FLASHCARD MODE", INTERNAL_W//2, 4, FONT_MD, GOLD, "center")
        panel(surface, (10, 18, INTERNAL_W - 20, INTERNAL_H - 36))
        text(surface, el["name"].upper(), INTERNAL_W//2, 28, FONT_LG, GOLD, "center")
        text(surface, el["symbol"], 20, 28, FONT_LG, TEAL)
        text(surface, f"#{el['number']}", INTERNAL_W - 20, 28, FONT_MD, GRAY, "topright")
        if not self.flipped:
            text(surface, "SPACE TO REVEAL", INTERNAL_W//2, INTERNAL_H//2, FONT_SM, GRAY, "center")
        else:
            text(surface, f"GROUP {el['group']}  PERIOD {el['period']}", INTERNAL_W//2, 50, FONT_SM, WHITE, "center")
            text(surface, f"MASS {el['mass']}", INTERNAL_W//2, 62, FONT_SM, GRAY, "center")
            text(surface, el["category"].upper(), INTERNAL_W//2, 74, FONT_SM, TEAL, "center")
            for i, prop in enumerate(el["properties"][:3]):
                wrap_text(surface, prop, 16, 90 + i * 14, INTERNAL_W - 32, FONT_SM)
            text(surface, "USES:", 16, 138, FONT_SM, GOLD)
            for i, use in enumerate(el["uses"][:2]):
                wrap_text(surface, use, 16, 150 + i * 14, INTERNAL_W - 32, FONT_SM, GRAY)
        text(surface, f"{self.index+1}/{len(self.elements)}  < >  SPACE  ESC",
             INTERNAL_W//2, INTERNAL_H - 10, FONT_SM, GRAY, "center")


# ---------------------------------------------------------------------------
# Quiz Screen
# ---------------------------------------------------------------------------

class QuizScreen(Screen):
    """Multiple choice quiz — 4 options, tests based on current level."""

    def __init__(self, game):
        super().__init__(game)
        self.level    = game.level
        self._build_questions()
        self.q_index  = 0
        self.selected = 0
        self.answered = None   # None / True / False
        self.score    = 0

    def _build_questions(self):
        from elements import wrong_choices
        palace   = self.game.palace
        learned  = palace.learned[-self.game.QUIZ_INTERVAL if hasattr(self.game, 'QUIZ_INTERVAL') else -5:]
        from elements import get_by_name
        self.questions = []
        for name in learned:
            el = get_by_name(name)
            if not el:
                continue
            wrongs = wrong_choices(el, 3)
            import random
            options = [el] + wrongs
            random.shuffle(options)
            self.questions.append({
                "element":  el,
                "options":  options,
                "correct":  el["name"],
            })

    def update(self, events):
        if self.q_index >= len(self.questions):
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
        if self.q_index >= len(self.questions):
            return
        q = self.questions[self.q_index]
        el = q["element"]

        text(surface, f"QUIZ  {self.q_index+1}/{len(self.questions)}", INTERNAL_W//2, 4, FONT_SM, GOLD, "center")

        # Prompt — level 1: name the group; level 2+: name the use
        if self.level == 1:
            prompt = f"WHICH GROUP IS  {el['name'].upper()}  IN?"
        else:
            prompt = f"NAME A USE FOR  {el['name'].upper()}"

        wrap_text(surface, prompt, 10, 18, INTERNAL_W - 20, FONT_MD, WHITE, 14)

        for i, opt in enumerate(q["options"]):
            y = 70 + i * 28
            if self.answered is not None:
                if opt["name"] == q["correct"]:
                    col = GREEN
                elif i == self.selected:
                    col = RED
                else:
                    col = GRAY
            else:
                col = TEAL if i == self.selected else WHITE
            prefix = "> " if i == self.selected else "  "
            label = f"GROUP {opt['group']}" if self.level == 1 else opt["uses"][0][:28]
            text(surface, prefix + label, 20, y, FONT_SM, col)

        if self.answered is not None:
            msg = "CORRECT!" if self.answered else "WRONG!"
            col = GREEN if self.answered else RED
            text(surface, msg, INTERNAL_W//2, INTERNAL_H - 22, FONT_MD, col, "center")
            text(surface, "ENTER TO CONTINUE", INTERNAL_W//2, INTERNAL_H - 10, FONT_SM, GRAY, "center")
        else:
            text(surface, "UP/DOWN  ENTER", INTERNAL_W//2, INTERNAL_H - 10, FONT_SM, GRAY, "center")
