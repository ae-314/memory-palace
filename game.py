"""
Game state machine.
Owns the active screen, player progress, and quiz scheduling.
Delegates all rendering to ui.py and all persistence to palace.py.
"""

import sys
import random
import pygame
from elements import load_elements
from palace import Palace
from constants import QUIZ_INTERVAL


class Game:
    """Top-level controller — update/draw called every frame from main.py."""

    def __init__(self, canvas):
        self.canvas   = canvas
        self.elements = load_elements()
        self.palace   = Palace.load()
        self.screen   = None          # active Screen instance (set by _go_to)
        self.level    = 1             # current difficulty level (1-3)
        from ui import Cat
        self.cat = Cat()
        self._go_to("home")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self, events):
        import ui
        # Global ESC: save palace and return to home from any gameplay screen
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                if not isinstance(self.screen, ui.HomeScreen):
                    self.palace.save()
                    self._go_to("home")
                    return
        self.cat.update(self.palace)
        if self.screen:
            result = self.screen.update(events)
            if result:
                self._handle(result)

    def draw(self):
        if self.screen:
            self.screen.draw(self.canvas)

    # ------------------------------------------------------------------
    # Navigation / event handling
    # ------------------------------------------------------------------

    def _go_to(self, screen_name, **kwargs):
        """Swap the active screen."""
        import ui
        screens = {
            "home":      ui.HomeScreen,
            "element":   ui.ElementScreen,
            "palace":    ui.PalaceScreen,
            "flashcard": ui.FlashcardScreen,
            "quiz":      ui.QuizScreen,
        }
        cls = screens.get(screen_name)
        if cls:
            self.screen = cls(self, **kwargs)

    def _handle(self, result):
        """Process navigation signals returned by screens."""
        action = result.get("action")
        if action == "new_game":
            self._next_element()
        elif action == "continue":
            self._next_element()
        elif action == "flashcard":
            self._go_to("flashcard")
        elif action == "element_stored":
            self.palace.save()
            count = len(self.palace.learned)
            if count > 0 and count % QUIZ_INTERVAL == 0:
                self._go_to("quiz")
            else:
                self._next_element()
        elif action == "quiz_done":
            self._next_element()
        elif action == "home":
            self._go_to("home")
        elif action == "quit":
            self.palace.save()
            pygame.quit()
            sys.exit()

    def _next_element(self):
        """Pick a random unlearned element and show its card."""
        learned = {e.lower() for e in self.palace.learned}
        remaining = [e for e in self.elements if e["name"].lower() not in learned]
        if not remaining:
            self._go_to("home")   # TODO: victory screen
            return
        element = random.choice(remaining)
        self._go_to("element", element=element)
