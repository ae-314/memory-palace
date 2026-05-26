"""
Sprite loading from Kenney 1-Bit Pack (CC0).
Maps item names → (col, row) tile positions in assets/sprites/kenney_1bit.png.
Sheet layout: 49 cols × 22 rows, each tile 16 × 16 px with 1 px gap (step = 17).
"""

import pygame

SHEET_PATH = "assets/sprites/kenney_1bit.png"
TILE_PX    = 16
TILE_STEP  = 17   # 16 px tile + 1 px spacing

# (col, row) coordinates identified from monochrome-transparent.png
ITEM_TILES = {
    # --- containers & furniture ---
    "chest":      ( 8,  6),   "crate":      ( 9,  6),
    "barrel":     (10,  6),   "lockbox":    (11,  6),
    "shelf":      (15,  6),   "vase":       (18,  6),
    "cauldron":   (19,  6),   "pillar":     (20,  6),
    "cabinet":    (15,  7),   "safe":       (16,  7),
    "bomb":       (14,  5),
    # --- weapons ---
    "sword":      (33,  8),   "dagger":     (34,  8),
    "axe":        (32,  8),   "staff":      (36,  8),
    "shield":     (35,  8),
    # --- gems & wealth ---
    "gem":        (32, 10),   "diamond":    (33, 10),
    "crystal":    (34, 10),   "coin":       (43, 12),
    "medal":      (44, 12),   "target":     (46, 12),
    # --- life & nature ---
    "heart":      (38, 10),   "skull":      (45,  9),
    "bones":      (32, 12),   "flower":     (45, 13),
    "clover":     (46, 13),   "blossom":    (48, 13),
    # --- keys & locks ---
    "key":        (32, 11),   "padlock":    (31, 11),
    # --- potions & alchemy ---
    "potion":     (38, 11),   "flask":      (40, 11),
    "vial":       (41, 11),   "bottle":     (42, 11),
    "elixir":     (34, 13),   "tonic":      (35, 13),
    # --- gears & time ---
    "gear":       (27, 12),   "sprocket":   (29, 12),
    "hourglass":  (40, 12),   "stopwatch":  (41, 12),
    # --- symbols & misc ---
    "cross":      (43, 10),   "question":   (40, 13),
    "warning":    (38, 13),   "dice":       (33, 14),
    "smiley":     (28, 14),   "angry":      (29, 14),
    "portal":     (48,  9),   "sun":        (40,  9),
}

# Ordered list for the item picker grid (groups kept together)
ITEMS = list(ITEM_TILES.keys())   # 44 items

_sheet: pygame.Surface | None = None
_cache: dict = {}


def _load_sheet() -> pygame.Surface:
    global _sheet
    if _sheet is None:
        _sheet = pygame.image.load(SHEET_PATH).convert_alpha()
    return _sheet


def _raw_tile(col: int, row: int) -> pygame.Surface:
    """Extract a single 16×16 tile (SRCALPHA)."""
    sh   = _load_sheet()
    surf = pygame.Surface((TILE_PX, TILE_PX), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    surf.blit(sh, (0, 0), (col * TILE_STEP, row * TILE_STEP, TILE_PX, TILE_PX))
    return surf


def get_sprite(name: str, color: tuple = (255, 255, 255), size: int = 16) -> pygame.Surface:
    """Return a tinted, scaled Surface for the named item (cached)."""
    key = (name, size, color)
    if key in _cache:
        return _cache[key]
    col, row   = ITEM_TILES.get(name, ITEM_TILES["coin"])
    raw        = _raw_tile(col, row)
    tinted     = raw.copy()
    tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    if size != TILE_PX:
        tinted = pygame.transform.scale(tinted, (size, size))
    _cache[key] = tinted
    return tinted


def draw_sprite(surface: pygame.Surface, name: str,
                color: tuple, cx: int, cy: int, size: int = 16) -> None:
    """Blit a sprite centred at (cx, cy)."""
    sp = get_sprite(name, color, size)
    surface.blit(sp, (cx - size // 2, cy - size // 2))
