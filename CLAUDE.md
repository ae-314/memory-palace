# CLAUDE.md — Memory Palace

## Project overview
A chunky-pixel Pygame game (320×240 internal res, scaled 3×) for memorising the periodic table via the memory palace technique.

## Stack
- Python 3.11+
- pygame-ce (community edition)
- No other runtime dependencies

## File responsibilities (strict)
| File | Owns |
|---|---|
| `main.py` | Pygame init, game loop only |
| `game.py` | State machine, screen transitions, quiz scheduling |
| `palace.py` | Data model (Palace / Room / Container) + JSON save/load |
| `elements.py` | Element data loading and lookup helpers |
| `ui.py` | All rendering — screens, shapes, text helpers |
| `constants.py` | Every magic value — colours, sizes, shape names, level defs |

**Never mix concerns across files.** ui.py never touches JSON. palace.py never calls pygame.

## Conventions
- Internal resolution: 320×240. All coordinates are in this space.
- Fonts: `font(size)` helper in ui.py handles caching + fallback.
- Shapes: 25 named shapes in `constants.SHAPES`. `draw_shape(surface, name, colour, cx, cy, size)` in ui.py.
- Screen protocol: each screen has `update(events) -> dict|None` and `draw(surface)`. Return a dict with `"action"` key to trigger navigation.
- Palace auto-saves after every `store_element()` call.

## Style
- Short functions — if a function exceeds ~20 lines, split it.
- No defensive checks for things that can't happen.
- Prefer clarity over cleverness; prefer fewer lines over more.
- No type annotations on internal helpers (keep it light).
- `FONT_SM=6  FONT_MD=8  FONT_LG=12` — use these, don't invent new sizes.

## Run
```bash
python main.py
```
