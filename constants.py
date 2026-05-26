"""
Game-wide constants: resolution, colours, font paths, timing.
All magic values live here — nothing else imports magic numbers.
"""

# --- Resolution ---
INTERNAL_W  = 640
INTERNAL_H  = 360
SCALE       = 2
WINDOW_W    = INTERNAL_W * SCALE   # 1280
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
FONT_SM     = 12
FONT_MD     = 16
FONT_LG     = 28

# --- Gameplay ---
QUIZ_INTERVAL   = 5    # elements between quiz rounds
QUIZ_CHOICES    = 4    # multiple choice options

# --- Available container items (names must match sprites.ITEM_TILES keys) ---
# Imported lazily to avoid circular dependencies; ui.py imports from sprites directly.
# This list is the authoritative order shown in the item picker.
ITEMS = [
    "chest",    "crate",    "barrel",   "lockbox",  "shelf",
    "vase",     "cauldron", "pillar",   "cabinet",  "safe",
    "bomb",     "sword",    "dagger",   "axe",      "staff",
    "shield",   "gem",      "diamond",  "crystal",  "coin",
    "medal",    "target",   "heart",    "skull",    "bones",
    "flower",   "clover",   "blossom",  "key",      "padlock",
    "potion",   "flask",    "vial",     "bottle",   "elixir",
    "tonic",    "gear",     "sprocket", "hourglass","stopwatch",
    "cross",    "question", "warning",  "dice",     "smiley",
    "angry",    "portal",   "sun",
]

# Keep SHAPES as an alias so old save files that stored geometric names degrade gracefully
SHAPES = ITEMS

# --- Category colours (used for element card header tinting) ---
CATEGORY_COLORS = {
    "alkali metal":          (255,  90,  80),
    "alkaline earth metal":  (255, 180,  60),
    "transition metal":      (220, 210,  60),
    "post-transition metal": ( 80, 210, 110),
    "metalloid":             ( 60, 210, 210),
    "nonmetal":              ( 80, 120, 255),
    "halogen":               (190,  70, 255),
    "noble gas":             (255,  80, 190),
    "lanthanide":            (170, 110, 255),
    "actinide":              (255, 120,  70),
    "unknown":               (150, 150, 160),
}

# Room border palette (cycled by room-name hash)
ROOM_PALETTE = [
    (255, 200,  50),   # gold
    ( 80, 220, 200),   # teal
    (100,  80, 220),   # purple
    (220, 140,  40),   # orange
    (220, 100, 160),   # pink
    ( 80, 200, 120),   # green
    (180, 100, 255),   # violet
    (100, 200, 255),   # sky
]

# --- Level definitions ---
# Each level specifies which element fields the quiz tests
LEVELS = [
    {"id": 1, "name": "NAME & GROUP",        "fields": ["name", "group"]},
    {"id": 2, "name": "NAME, GROUP & USE",   "fields": ["name", "group", "uses"]},
    {"id": 3, "name": "FULL RECALL",         "fields": ["name", "group", "uses", "properties"]},
]
