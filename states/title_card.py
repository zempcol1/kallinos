"""Title card — a full-screen chapter/milestone card between scenes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from ui.widgets import font

if TYPE_CHECKING:
    from game.game import Game


class TitleCard(State):
    """Shows a title and subtitle, then continues on Enter.

    Change to it with params:
        {
            "title": str,
            "subtitle": str,
            "next_state": str,         # state to change to afterwards
            "next_params": dict | None,
        }
    """

    HINT_DELAY_MS = 1000

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._params: dict = {}
        self._timer = 0.0

    def enter(self, params: dict | None = None) -> None:
        self._params = params or {}
        self._timer = 0.0

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._timer < self.HINT_DELAY_MS:
            return
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game.state_machine.change(self._params["next_state"],
                                               self._params.get("next_params"))
                return

    def update(self, dt: float) -> None:
        self._timer += dt

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(s.COLOR_BLACK)
        cx, cy = s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT // 2
        lines = [
            (self._params.get("title", ""), font(48), s.COLOR_TITLE_GOLD, -40),
            (self._params.get("subtitle", ""), font(26), s.COLOR_ACCENT_GOLD, 0),
        ]
        if self._timer >= self.HINT_DELAY_MS:
            lines.append(("Press Enter to continue", font(26), s.COLOR_TEXT_DIM, 40))
        for text, text_font, color, dy in lines:
            text_surf = text_font.render(text, True, color)
            surface.blit(text_surf, text_surf.get_rect(center=(cx, cy + dy)))
