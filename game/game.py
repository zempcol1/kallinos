"""Game class — owns the main loop, display, clock, and state machine."""

import sys

import pygame

import settings as s
from game.state_machine import StateMachine
from states.main_menu import MainMenu
from states.exploration import Exploration


class Game:
    """Top-level object that initializes Pygame and drives the game loop."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
        pygame.display.set_caption(s.GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # State machine setup
        self.state_machine = StateMachine()
        self.state_machine.register("main_menu", MainMenu(self))
        self.state_machine.register("exploration", Exploration(self))

        # Start on the main menu
        self.state_machine.push("main_menu")

    def run(self) -> None:
        """Main game loop: events → update → render → flip."""
        while self.running:
            dt = self.clock.tick(s.FPS)
            events = pygame.event.get()

            # Global quit check
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()
                    return

            state = self.state_machine.current
            if state is None:
                self.quit()
                return

            state.handle_events(events)
            state.update(dt)
            state.render(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def quit(self) -> None:
        """Signal the main loop to stop."""
        self.running = False
