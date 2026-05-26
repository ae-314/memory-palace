"""
Game-wide constants: resolution, colours, font paths, timing.
All magic values live here — nothing else imports magic numbers.
"""

# --- Resolution ---
INTERNAL_W  = 320
INTERNAL_H  = 240
SCALE       = 3
WINDOW_W    = INTERNAL_W * SCALE   # 960
WINDOW_H    = INTERNAL_H * SCALE   # 720
FPS         = 60
TITLE       = "MEMORY PALACE"

# --- Colours (8-bit inspired palette) ---
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
BG          = ( 15,  15,  35)   # deep navy
PANEL_BG    = ( 25,  25,  55)
GOLD        = (255, 200,  50)
TEAL        = ( 80, 220, 200)
RED         = (220,  60,  60)
GREEN       = ( 80, 200, 120)
GRAY        = (100, 100, 120)
HIGHLIGHT   = (100,  80, 220)
PURPLE      = ( 80,  40, 160)
ORANGE      = (220, 140,  40)
PINK        = (220, 100, 160)

# --- Fonts ---
FONT_DIR    = "assets/fonts"
PIXEL_FONT  = f"{FONT_DIR}/PressStart2P.ttf"
FONT_SM     = 6
FONT_MD     = 8
FONT_LG     = 12

# --- Gameplay ---
QUIZ_INTERVAL   = 5    # elements between quiz rounds
QUIZ_CHOICES    = 4    # multiple choice options

# --- Available container shapes ---
SHAPES = [
    "diamond", "circle",  "star",    "triangle", "square",
    "pentagon","hexagon",  "heart",   "cross",    "crown",
    "flask",   "crystal",  "gem",     "flame",    "moon",
    "shield",  "bolt",     "orb",     "ring",     "cube",
    "leaf",    "spiral",   "drop",    "chest",    "cage",
]

# --- Level definitions ---
# Each level specifies which element fields the quiz tests
LEVELS = [
    {"id": 1, "name": "NAME & GROUP",        "fields": ["name", "group"]},
    {"id": 2, "name": "NAME, GROUP & USE",   "fields": ["name", "group", "uses"]},
    {"id": 3, "name": "FULL RECALL",         "fields": ["name", "group", "uses", "properties"]},
]
