"""Exploration state — the main overworld / map mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State

if TYPE_CHECKING:
    from game.game import Game


class Exploration(State):
    """Placeholder exploration state.

    Currently renders a colored background with instructions.
    Will eventually hold the tile map, player movement, and NPC interactions.
    """

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._info_font: pygame.font.Font | None = None
        self._hint_font: pygame.font.Font | None = None

    def enter(self, params: dict | None = None) -> None:
        self._info_font = pygame.font.Font(None, 40)
        self._hint_font = pygame.font.Font(None, 24)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                self.game.state_machine.change("main_menu")

    def update(self, dt: float) -> None:
        pass  # Player movement, NPC logic, triggers will go here

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(s.COLOR_OLIVE_GREEN)

        cx = s.SCREEN_WIDTH // 2
        cy = s.SCREEN_HEIGHT // 2

        info_surf = self._info_font.render("Exploration State", True, s.COLOR_WHITE)
        info_rect = info_surf.get_rect(center=(cx, cy - 20))
        surface.blit(info_surf, info_rect)

        hint_surf = self._hint_font.render("Press ESC to return to Main Menu", True, s.COLOR_SAND)
        hint_rect = hint_surf.get_rect(center=(cx, cy + 25))
        surface.blit(hint_surf, hint_rect)
