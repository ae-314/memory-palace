# Memory Palace
Memory Palace (Periodic Table Edition) - Memorize the Periodic Table of Elements by building your own Memory Palace. Choose containers and rooms to store the elements you discover, and then try to recall the elements later via flashcard multiple choice quiz, or just go through the card deck. 
## Setup

```bash
pip install -r requirements.txt
```

### Font (required for the pixel look)

Download **Press Start 2P** from Google Fonts:
https://fonts.google.com/specimen/Press+Start+2P

Place `PressStart2P-Regular.ttf` in `assets/fonts/`.
The game falls back to a system monospace font if the file is missing.

## Run

```bash
python main.py
```

## How to play

1. **New Game** — an element card is shown with its key facts
2. Type a container description (e.g. *"a shiny diamond"*)
3. Pick a shape from the visual grid
4. Name the room where the container should live (e.g. *"the ballroom"*)
5. Every 5 elements you are quizzed on what you have learned

### Modes
- **Memory Palace** — main game, build and quiz
- **Flashcards** — browse all 118 elements freely (no quiz)

### Levels
| Level | Must recall |
|---|---|
| 1 | Name + group |
| 2 | Name + group + one use |
| 3 | Name + group + use + property |

## Project structure

```
main.py        entry point
game.py        state machine & quiz scheduling
palace.py      data model + save/load
elements.py    element data access
ui.py          all Pygame rendering (screens + shapes)
constants.py   colours, sizes, shape list
data/          elements.json
saves/         player palace (git-ignored)
assets/fonts/  pixel font (git-ignored)
```
