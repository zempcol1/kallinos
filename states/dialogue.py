"""Dialogue state — displays text boxes with speaker names."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from ui.widgets import draw_panel, font, wrap_text

if TYPE_CHECKING:
    from game.game import Game


class Dialogue(State):
    """Displays a sequence of dialogue lines in a text box.

    Push with params:
        {
            "lines": [("Speaker", "Line of text"), ...],
            "on_complete": str | None,   # optional callback event name
        }
    """

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._lines: list[tuple[str, str]] = []
        self._index = 0
        self._on_complete: str | None = None

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        self._lines = params.get("lines", [])
        self._index = 0
        self._on_complete = params.get("on_complete")

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self._index += 1
                if self._index >= len(self._lines):
                    self._finish()

    def _finish(self) -> None:
        """Pop this state and optionally signal an event."""
        callback = self._on_complete
        self.game.state_machine.pop()
        # If there's a callback, tell the exploration state
        if callback:
            current = self.game.state_machine.current
            if hasattr(current, "on_dialogue_complete"):
                current.on_dialogue_complete(callback)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        # Don't clear — draw on top of the state below
        if not self._lines or self._index >= len(self._lines):
            return

        speaker, text = self._lines[self._index]

        box_h = 130
        box_rect = pygame.Rect(20, s.SCREEN_HEIGHT - box_h - 10, s.SCREEN_WIDTH - 40, box_h)
        draw_panel(surface, box_rect)

        name_surf = font(32).render(speaker, True, s.COLOR_ACCENT_GOLD)
        surface.blit(name_surf, (box_rect.x + 15, box_rect.y + 10))

        text_font = font(28)
        y = box_rect.y + 42
        for line_str in wrap_text(text, text_font, box_rect.width - 30)[:3]:  # max 3 lines
            surface.blit(text_font.render(line_str, True, s.COLOR_WHITE), (box_rect.x + 15, y))
            y += 26

        hint = f"[Enter] ({self._index + 1}/{len(self._lines)})"
        hint_surf = font(20).render(hint, True, s.COLOR_TEXT_DIM)
        surface.blit(hint_surf, (box_rect.right - hint_surf.get_width() - 15,
                                 box_rect.bottom - 22))
