"""Dialogue state — displays text boxes with speaker names."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State

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
        self._font: pygame.font.Font | None = None
        self._name_font: pygame.font.Font | None = None
        self._hint_font: pygame.font.Font | None = None

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        self._lines = params.get("lines", [])
        self._index = 0
        self._on_complete = params.get("on_complete")
        self._font = pygame.font.Font(None, 28)
        self._name_font = pygame.font.Font(None, 32)
        self._hint_font = pygame.font.Font(None, 20)

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

        # Dialogue box background
        box_h = 130
        box_y = s.SCREEN_HEIGHT - box_h - 10
        box_rect = pygame.Rect(20, box_y, s.SCREEN_WIDTH - 40, box_h)

        # Semi-transparent background
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        box_surf.fill((15, 15, 35, 230))
        surface.blit(box_surf, box_rect)

        # Border
        pygame.draw.rect(surface, s.COLOR_ACCENT_GOLD, box_rect, 2)

        # Speaker name
        name_surf = self._name_font.render(speaker, True, s.COLOR_ACCENT_GOLD)
        surface.blit(name_surf, (box_rect.x + 15, box_rect.y + 10))

        # Text — simple word wrap
        words = text.split()
        line_strs = []
        current_line = ""
        max_w = box_rect.width - 30
        for word in words:
            test = current_line + (" " if current_line else "") + word
            if self._font.size(test)[0] > max_w:
                line_strs.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            line_strs.append(current_line)

        y = box_rect.y + 42
        for line_str in line_strs[:3]:  # max 3 visible lines
            text_surf = self._font.render(line_str, True, s.COLOR_WHITE)
            surface.blit(text_surf, (box_rect.x + 15, y))
            y += 26

        # Hint
        hint = f"[Enter] ({self._index + 1}/{len(self._lines)})"
        hint_surf = self._hint_font.render(hint, True, s.COLOR_TEXT_DIM)
        surface.blit(hint_surf, (box_rect.right - hint_surf.get_width() - 15,
                                 box_rect.bottom - 22))
