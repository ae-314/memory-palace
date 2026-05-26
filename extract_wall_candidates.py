"""
Extract candidate floor/wall tiles from monochrome-transparent.png.
Grid: 49 cols x 22 rows, 16px tiles, 1px gap, step=17px.
Shows cols 0-20, rows 3-9 at 400% zoom with grid labels.
Highlights specific candidate tiles.
"""

import pygame
import sys
import os

TILESHEET = r"c:\Users\Elche\claude_projects\memory_palace\assets\kenney_1bit_raw\Tilesheet\monochrome-transparent.png"
OUTPUT    = r"c:\Users\Elche\claude_projects\memory_palace\assets\wall_candidates.png"

TILE_SIZE = 16
GAP       = 1
STEP      = 17   # TILE_SIZE + GAP
ZOOM      = 4

# Region to display
COL_START, COL_END = 0, 21   # cols 0..20 inclusive
ROW_START, ROW_END = 3, 10   # rows 3..9 inclusive

COLS = COL_END - COL_START   # 21
ROWS = ROW_END - ROW_START   # 7

# Labelled candidate tiles: (col, row, label)
CANDIDATES = [
    (8,  4, "8,4"),
    (9,  4, "9,4"),
    (10, 4, "10,4"),
    (11, 4, "11,4"),
    (12, 5, "12,5\ncarpet?"),
    (13, 7, "13,7\ndoor?"),
]

TILE_Z   = TILE_SIZE * ZOOM      # 64
LABEL_H  = 14                    # pixels for col/row header text
MARGIN   = LABEL_H

def tile_rect_in_sheet(col, row):
    x = col * STEP
    y = row * STEP
    return pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

def zoomed_rect_in_canvas(col, row):
    x = MARGIN + (col - COL_START) * TILE_Z
    y = MARGIN + (row - ROW_START) * TILE_Z
    return pygame.Rect(x, y, TILE_Z, TILE_Z)

def main():
    pygame.init()

    sheet = pygame.image.load(TILESHEET).convert_alpha()
    print(f"Sheet size: {sheet.get_size()}")

    # Canvas size
    W = MARGIN + COLS * TILE_Z + 1
    H = MARGIN + ROWS * TILE_Z + 1
    canvas = pygame.Surface((W, H), pygame.SRCALPHA)
    canvas.fill((40, 40, 40, 255))

    font = pygame.font.SysFont("consolas", 10)

    # Draw each tile
    for row in range(ROW_START, ROW_END):
        for col in range(COL_START, COL_END):
            src  = tile_rect_in_sheet(col, row)
            dest = zoomed_rect_in_canvas(col, row)

            # Extract and zoom the tile
            tile_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            tile_surf.blit(sheet, (0, 0), src)
            zoomed = pygame.transform.scale(tile_surf, (TILE_Z, TILE_Z))

            # Tint background white so dark pixels show up on dark canvas
            bg = pygame.Surface((TILE_Z, TILE_Z))
            bg.fill((200, 200, 200))
            canvas.blit(bg, dest)
            canvas.blit(zoomed, dest)

            # Grid line
            pygame.draw.rect(canvas, (80, 80, 80), dest, 1)

    # Draw column headers (every other col for readability)
    for col in range(COL_START, COL_END):
        x = MARGIN + (col - COL_START) * TILE_Z + TILE_Z // 2
        label = font.render(str(col), True, (200, 200, 200))
        canvas.blit(label, (x - label.get_width() // 2, 1))

    # Draw row headers
    for row in range(ROW_START, ROW_END):
        y = MARGIN + (row - ROW_START) * TILE_Z + TILE_Z // 2
        label = font.render(str(row), True, (200, 200, 200))
        canvas.blit(label, (1, y - label.get_height() // 2))

    # Highlight candidate tiles
    COLOURS = {
        "floor_wood":  (255, 200,  50, 180),
        "floor_stone": ( 50, 200, 255, 180),
        "wall_solid":  (255,  80,  80, 180),
        "wall_window": (180,  80, 255, 180),
        "door":        ( 80, 255, 120, 180),
        "carpet":      (255, 140,   0, 180),
    }
    highlight_colours = [
        (255, 200,  50),  # 8,4
        ( 50, 200, 255),  # 9,4
        (255,  80,  80),  # 10,4
        (180,  80, 255),  # 11,4
        (255, 140,   0),  # 12,5
        ( 80, 255, 120),  # 13,7
    ]

    for i, (col, row, label) in enumerate(CANDIDATES):
        if COL_START <= col < COL_END and ROW_START <= row < ROW_END:
            dest  = zoomed_rect_in_canvas(col, row)
            colour = highlight_colours[i % len(highlight_colours)]
            # Coloured border (3px)
            pygame.draw.rect(canvas, colour, dest, 3)
            # Small label below the tile
            lines = label.split("\n")
            for li, line in enumerate(lines):
                lbl = font.render(line, True, colour)
                canvas.blit(lbl, (dest.x, dest.bottom + 1 + li * 11))

    pygame.image.save(canvas, OUTPUT)
    print(f"Saved: {OUTPUT}  ({W}x{H}px)")

    # Also print pixel-level description for each candidate
    print("\n--- Candidate tile pixel content summary ---")
    for col, row, label in CANDIDATES:
        src = tile_rect_in_sheet(col, row)
        tile_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        tile_surf.blit(sheet, (0, 0), src)
        # Count non-transparent pixels and their brightness
        pixels = []
        for py in range(TILE_SIZE):
            for px in range(TILE_SIZE):
                r, g, b, a = tile_surf.get_at((px, py))
                if a > 10:
                    pixels.append((r + g + b) // 3)
        total = TILE_SIZE * TILE_SIZE
        opaque = len(pixels)
        if pixels:
            avg_bright = sum(pixels) // len(pixels)
        else:
            avg_bright = 0
        print(f"  ({col:2d},{row:2d}) [{label:12s}]  opaque={opaque:3d}/{total}  avg_brightness={avg_bright:3d}")

    pygame.quit()

if __name__ == "__main__":
    main()
