"""Title card — a full-screen chapter/milestone card between scenes."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from ui.widgets import draw_ornament_rules, font

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
    TITLE_FADE_MS = 700
    RISE = 16             # title drifts up this many pixels while fading in
    MOTES = 24
    MOTE_RISE_MS = 5000

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
        self._render_motes(surface)

        fade = min(1.0, self._timer / self.TITLE_FADE_MS)
        rise = round((1 - fade) * self.RISE)
        title = font(52).render(self._params.get("title", ""), True, s.COLOR_TITLE_GOLD)
        title.set_alpha(int(255 * fade))
        surface.blit(title, title.get_rect(center=(cx, cy - 40 + rise)))

        subtitle = font(28).render(self._params.get("subtitle", ""), True, s.COLOR_SAND)
        subtitle.set_alpha(int(255 * fade))
        sub_rect = subtitle.get_rect(center=(cx, cy + 6 + rise))
        surface.blit(subtitle, sub_rect)
        if fade >= 1:
            draw_ornament_rules(surface, sub_rect)

        if self._timer >= self.HINT_DELAY_MS:
            pulse = 0.55 + 0.45 * math.sin((self._timer - self.HINT_DELAY_MS) / 400)
            hint = font(24).render("Press Enter to continue", True, s.COLOR_TEXT_DIM)
            hint.set_alpha(int(255 * pulse))
            surface.blit(hint, hint.get_rect(center=(cx, cy + 70)))

    def _render_motes(self, surface: pygame.Surface) -> None:
        """Golden motes drifting up, as from Athena's olive."""
        mote = pygame.Surface((s.SCALE, s.SCALE))
        mote.fill(s.COLOR_TITLE_GOLD)
        for i in range(self.MOTES):
            life = (self._timer / self.MOTE_RISE_MS + i / self.MOTES) % 1.0
            x = (i * 0.618 % 1.0) * s.SCREEN_WIDTH + math.sin(life * math.tau + i) * 12
            y = s.SCREEN_HEIGHT * (1 - life)
            mote.set_alpha(int(math.sin(life * math.pi) * 140))
            surface.blit(mote, (round(x), round(y)))
