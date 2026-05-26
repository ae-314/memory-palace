"""
Sprite loading from Kenney 1-Bit Pack (CC0).

Two sheets are used:
  SHEET_PATH       — monochrome-transparent.png — for in-game rendering (tintable)
  COLOR_SHEET_PATH — colored-transparent.png    — for the tile picker display only

Sheet layout (both sheets): 49 cols × 22 rows, 16 × 16 px tiles, 1 px gap (step = 17).
Total tiles: 1078.

Tile names:
  Named items  — keys in ITEM_TILES  (e.g. "chest", "potion")
  Raw tiles    — "t_COL_ROW" strings (e.g. "t_5_3")  — covers all 1078 tiles
"""

import pygame

SHEET_PATH       = "assets/sprites/kenney_1bit.png"
COLOR_SHEET_PATH = "assets/sprites/kenney_1bit_color.png"

TILE_PX   = 16
TILE_STEP = 17   # 16 px + 1 px gap
TILE_COLS = 49
TILE_ROWS = 22

# ---------------------------------------------------------------------------
# Named item → (col, row) mapping  (monochrome sheet coordinates)
# ---------------------------------------------------------------------------
ITEM_TILES: dict[str, tuple[int, int]] = {
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

# Reverse map — (col, row) → name — for tile_name() lookup
_POS_TO_NAME: dict[tuple[int, int], str] = {v: k for k, v in ITEM_TILES.items()}

# Ordered named items for UI reference
ITEMS: list[str] = list(ITEM_TILES.keys())

# ---------------------------------------------------------------------------
# Architectural tiles used for room floor rendering (not shown in picker)
# ---------------------------------------------------------------------------
FLOOR_TILE  = ( 8,  4)   # stone-grid floor tile (tinted per room)
FLOOR_TILE2 = ( 9,  4)   # wood-like floor tile  (alternate rows)

# ---------------------------------------------------------------------------
# Module-level caches
# ---------------------------------------------------------------------------
_sheet:       pygame.Surface | None = None
_color_sheet: pygame.Surface | None = None
_cache:       dict = {}


def _load_sheet() -> pygame.Surface:
    global _sheet
    if _sheet is None:
        _sheet = pygame.image.load(SHEET_PATH).convert_alpha()
    return _sheet


def _load_color_sheet() -> pygame.Surface:
    global _color_sheet
    if _color_sheet is None:
        _color_sheet = pygame.image.load(COLOR_SHEET_PATH).convert_alpha()
    return _color_sheet


def _raw_tile(col: int, row: int) -> pygame.Surface:
    """Extract a 16×16 tile from the MONOCHROME sheet (SRCALPHA)."""
    sh   = _load_sheet()
    surf = pygame.Surface((TILE_PX, TILE_PX), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    surf.blit(sh, (0, 0), (col * TILE_STEP, row * TILE_STEP, TILE_PX, TILE_PX))
    return surf


# ---------------------------------------------------------------------------
# Public sprite API
# ---------------------------------------------------------------------------

def get_sprite(name: str, color: tuple = (255, 255, 255), size: int = 16) -> pygame.Surface:
    """
    Return a tinted, scaled Surface (cached).
    name can be a key in ITEM_TILES ("chest") or a raw "t_COL_ROW" string.
    """
    key = (name, size, color)
    if key in _cache:
        return _cache[key]

    if name in ITEM_TILES:
        col, row = ITEM_TILES[name]
    elif name.startswith("t_"):
        parts = name.split("_")
        try:
            col, row = int(parts[1]), int(parts[2])
        except (IndexError, ValueError):
            col, row = ITEM_TILES["coin"]
    else:
        col, row = ITEM_TILES["coin"]   # graceful fallback for old shape names

    raw    = _raw_tile(col, row)
    tinted = raw.copy()
    tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    if size != TILE_PX:
        tinted = pygame.transform.scale(tinted, (size, size))
    _cache[key] = tinted
    return tinted


def draw_sprite(surface: pygame.Surface, name: str,
                color: tuple, cx: int, cy: int, size: int = 16) -> None:
    """Blit a tinted sprite centred at (cx, cy)."""
    sp = get_sprite(name, color, size)
    surface.blit(sp, (cx - size // 2, cy - size // 2))


def get_colored_tile(col: int, row: int, size: int = 12) -> pygame.Surface:
    """
    Return a tile from the COLORED sheet at the given display size (cached).
    Used only for the picker — no tinting applied.
    """
    key = (f"c_{col}_{row}", size, None)
    if key in _cache:
        return _cache[key]
    sh   = _load_color_sheet()
    surf = pygame.Surface((TILE_PX, TILE_PX), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    surf.blit(sh, (0, 0), (col * TILE_STEP, row * TILE_STEP, TILE_PX, TILE_PX))
    if size != TILE_PX:
        surf = pygame.transform.scale(surf, (size, size))
    _cache[key] = surf
    return surf


def tile_name(col: int, row: int) -> str:
    """Human-readable name for a tile position (named items shown by name)."""
    return _POS_TO_NAME.get((col, row), f"t_{col}_{row}")


def tile_key(col: int, row: int) -> str:
    """Storage key for a tile — named item key or 't_COL_ROW'."""
    return _POS_TO_NAME.get((col, row), f"t_{col}_{row}")
