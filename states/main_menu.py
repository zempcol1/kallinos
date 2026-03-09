"""Main Menu state — the first screen the player sees."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State

if TYPE_CHECKING:
    from game.game import Game


class MainMenu(State):
    """Title screen with New Game, Continue, and Quit options."""

    MENU_OPTIONS = ["New Game", "Continue", "Quit"]

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._selected = 0
        self._title_font: pygame.font.Font | None = None
        self._subtitle_font: pygame.font.Font | None = None
        self._option_font: pygame.font.Font | None = None
        self._footer_font: pygame.font.Font | None = None

    def enter(self, params: dict | None = None) -> None:
        self._selected = 0
        self._title_font = pygame.font.Font(None, 64)
        self._subtitle_font = pygame.font.Font(None, 28)
        self._option_font = pygame.font.Font(None, 36)
        self._footer_font = pygame.font.Font(None, 20)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_UP:
                self._selected = (self._selected - 1) % len(self.MENU_OPTIONS)
            elif event.key == pygame.K_DOWN:
                self._selected = (self._selected + 1) % len(self.MENU_OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_option()

    def _select_option(self) -> None:
        choice = self.MENU_OPTIONS[self._selected]
        if choice == "New Game":
            self.game.state_machine.change("exploration")
        elif choice == "Continue":
            pass  # Save/load not implemented yet
        elif choice == "Quit":
            self.game.quit()

    def update(self, dt: float) -> None:
        pass  # Animations (pulsing cursor, background effects) can go here

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(s.COLOR_MENU_BG)

        cx = s.SCREEN_WIDTH // 2

        # Title
        title_surf = self._title_font.render("KALLINOS", True, s.COLOR_TITLE_GOLD)
        title_rect = title_surf.get_rect(center=(cx, 140))
        surface.blit(title_surf, title_rect)

        # Subtitle
        sub_surf = self._subtitle_font.render("~ Rise of a Mortal ~", True, s.COLOR_TEXT_DIM)
        sub_rect = sub_surf.get_rect(center=(cx, 185))
        surface.blit(sub_surf, sub_rect)

        # Menu options
        start_y = 280
        spacing = 50
        for i, option in enumerate(self.MENU_OPTIONS):
            if i == self._selected:
                color = s.COLOR_ACCENT_GOLD
                text = f"> {option}"
            else:
                color = s.COLOR_WHITE
                text = f"  {option}"

            opt_surf = self._option_font.render(text, True, color)
            opt_rect = opt_surf.get_rect(center=(cx, start_y + i * spacing))
            surface.blit(opt_surf, opt_rect)

        # Footer
        ver_surf = self._footer_font.render("v0.1", True, s.COLOR_TEXT_DIM)
        surface.blit(ver_surf, (15, s.SCREEN_HEIGHT - 30))

        copy_surf = self._footer_font.render("Kallinos 2026", True, s.COLOR_TEXT_DIM)
        copy_rect = copy_surf.get_rect(topright=(s.SCREEN_WIDTH - 15, s.SCREEN_HEIGHT - 30))
        surface.blit(copy_surf, copy_rect)
