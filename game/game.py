"""Game class — owns the main loop, display, clock, and state machine."""

import pygame

import settings as s
from game.session import GameSession
from game.state_machine import StateMachine
from states.main_menu import MainMenu
from states.exploration import Exploration
from states.dialogue import Dialogue
from states.combat import Combat
from states.game_over import GameOver
from states.title_card import TitleCard
from systems import controls
from systems.audio import Audio
from systems.sprites import app_icon


class Game:
    """Top-level object that initializes Pygame and drives the game loop.

    ``audio=False`` skips sound synthesis entirely (tests, screenshots).
    """

    def __init__(self, audio: bool = True) -> None:
        pygame.mixer.pre_init(s.AUDIO_RATE, -16, 1, s.AUDIO_BUFFER)
        pygame.init()
        pygame.display.set_icon(app_icon(s.ICON_SIZE))
        self.screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
        pygame.display.set_caption(s.GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.session = GameSession(s.START_MAP)
        self.audio = Audio(enabled=audio)

        # State machine setup
        self.state_machine = StateMachine()
        self.state_machine.register("main_menu", MainMenu(self))
        self.state_machine.register("exploration", Exploration(self))
        self.state_machine.register("dialogue", Dialogue(self))
        self.state_machine.register("combat", Combat(self))
        self.state_machine.register("game_over", GameOver(self))
        self.state_machine.register("title_card", TitleCard(self))

        # Start on the main menu
        self.state_machine.push("main_menu")

    def run(self) -> None:
        """Main game loop: one ``step`` per frame, then flip."""
        while self.running:
            self.step(pygame.event.get(), self.clock.tick(s.FPS))
            pygame.display.flip()
        pygame.quit()

    def step(self, events: list[pygame.event.Event], dt: float) -> None:
        """One frame: events → update → render (no flip, so it also runs headless)."""
        # Global keys: quit, mute
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()
                return
            if event.type == pygame.KEYDOWN and event.key in controls.MUTE:
                self.audio.toggle_mute()

        state = self.state_machine.current
        if state is None:
            self.quit()
            return

        state.handle_events(events)
        state.update(dt)
        self.audio.update()

        # Render the full stack so overlay states (dialogue) draw
        # on top of the state below them.
        for layer in self.state_machine.stack:
            layer.render(self.screen)

    def new_game(self) -> None:
        """Start a fresh playthrough on the first map."""
        self.session = GameSession(s.START_MAP)
        self.state_machine.change("exploration", {"map": s.START_MAP})

    def quit(self) -> None:
        """Signal the main loop to stop."""
        self.running = False
