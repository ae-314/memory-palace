"""
Entry point. Initialises Pygame, creates the scaled canvas, runs the game loop.
Nothing but wiring lives here.
"""

import pygame
from constants import WINDOW_W, WINDOW_H, INTERNAL_W, INTERNAL_H, FPS, TITLE
from game import Game


def main():
    pygame.init()
    window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(TITLE)

    # All drawing happens on this small canvas; it is scaled up each frame.
    canvas = pygame.Surface((INTERNAL_W, INTERNAL_H))
    clock  = pygame.time.Clock()
    game   = Game(canvas)

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game.update(events)
        game.draw()

        scaled = pygame.transform.scale(canvas, (WINDOW_W, WINDOW_H))
        window.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
