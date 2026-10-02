"""Game Over — shown after losing a fight."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from ui.widgets import font

if TYPE_CHECKING:
    from game.game import Game


class GameOver(State):
    """Offers a retry from the last checkpoint or a return to the title."""

    OPTIONS = ["Retry", "Main Menu"]
    INPUT_DELAY_MS = 800  # Avoid skipping the screen with the key that ended combat

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._selected = 0
        self._timer = 0.0

    def enter(self, params: dict | None = None) -> None:
        self._selected = 0
        self._timer = 0.0

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._timer < self.INPUT_DELAY_MS:
            return
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_UP:
                self._selected = (self._selected - 1) % len(self.OPTIONS)
            elif event.key == pygame.K_DOWN:
                self._selected = (self._selected + 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select()
                return

    def _select(self) -> None:
        machine = self.game.state_machine
        if self.OPTIONS[self._selected] == "Retry":
            map_name = self.game.session.restore_checkpoint()
            machine.change("exploration", {"map": map_name})
        else:
            machine.change("main_menu")

    def update(self, dt: float) -> None:
        self._timer += dt

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(s.COLOR_BLACK)
        cx = s.SCREEN_WIDTH // 2

        title = font(64).render("You have fallen", True, s.COLOR_HP_RED)
        surface.blit(title, title.get_rect(center=(cx, 200)))
        sub = font(26).render("But the Fates are not done with you yet.", True, s.COLOR_TEXT_DIM)
        surface.blit(sub, sub.get_rect(center=(cx, 250)))

        if self._timer < self.INPUT_DELAY_MS:
            return
        for i, option in enumerate(self.OPTIONS):
            selected = i == self._selected
            color = s.COLOR_ACCENT_GOLD if selected else s.COLOR_WHITE
            text = font(36).render(f"> {option}" if selected else option, True, color)
            surface.blit(text, text.get_rect(center=(cx, 340 + i * 50)))
