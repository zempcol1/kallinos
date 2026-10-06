"""Dialogue state — text box with speaker portrait, name tab and typewriter text."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from systems.sprites import Look, continue_arrow, portrait
from ui.widgets import draw_panel, font, wrap_text

if TYPE_CHECKING:
    from game.game import Game


class Dialogue(State):
    """Displays a sequence of dialogue lines in a text box.

    Push with params:
        {
            "lines": [("Speaker", "Line of text"), ...],   # "" speaker = narration
            "on_complete": str | None,   # optional callback event name
            "looks": {speaker: Look},    # optional, shows that speaker's portrait
        }

    Text types out letter by letter; the first key press finishes the line,
    the next one advances.
    """

    BOX_HEIGHT = 144
    MARGIN = 16
    PORTRAIT_FRAME = 104
    LINE_HEIGHT = 30
    MAX_LINES = 3
    MOUTH_MS = 110          # talking mouth flap while text types
    BLINK_EVERY_MS = 3200
    BLINK_MS = 140
    ARROW_BOB_MS = 250
    NARRATION_COLOR = s.COLOR_SAND
    PORTRAIT_BG = (44, 36, 54)

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._lines: list[tuple[str, str]] = []
        self._looks: dict[str, Look] = {}
        self._index = 0
        self._on_complete: str | None = None
        self._shown = 0.0       # characters revealed of the current line
        self._timer = 0.0

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        self._lines = params.get("lines", [])
        self._looks = params.get("looks", {})
        self._index = 0
        self._on_complete = params.get("on_complete")
        self._shown = 0.0
        self._timer = 0.0

    @property
    def _text(self) -> str:
        return self._lines[self._index][1]

    @property
    def _typing(self) -> bool:
        return self._shown < len(self._text)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._index >= len(self._lines):
            self._finish()   # nothing to show
            return
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key not in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                continue
            if self._typing:
                self._shown = len(self._text)
                continue
            self._index += 1
            self._shown = 0.0
            if self._index >= len(self._lines):
                self._finish()
                return

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
        self._timer += dt
        if self._lines and self._index < len(self._lines) and self._typing:
            self._shown = min(len(self._text), self._shown + dt * s.TEXT_SPEED_CPS / 1000)

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        # Don't clear — draw on top of the state below
        if not self._lines or self._index >= len(self._lines):
            return
        speaker, text = self._lines[self._index]
        box = pygame.Rect(self.MARGIN, s.SCREEN_HEIGHT - self.BOX_HEIGHT - self.MARGIN,
                          s.SCREEN_WIDTH - self.MARGIN * 2, self.BOX_HEIGHT)
        draw_panel(surface, box, ornate=True)

        text_x = box.x + 24
        look = self._looks.get(speaker)
        if look is not None:
            text_x = self._draw_portrait(surface, box, look) + 20
        if speaker:
            self._draw_name_tab(surface, speaker, (text_x - 10, box.y))

        text_font = font(30)
        color = s.COLOR_WHITE if speaker else self.NARRATION_COLOR
        remaining = int(self._shown)
        y = box.y + 28
        for line in wrap_text(text, text_font, box.right - 24 - text_x)[:self.MAX_LINES]:
            visible = line[:remaining]
            remaining -= len(line) + 1   # +1 for the space the wrap swallowed
            if visible:
                shadow = text_font.render(visible, True, s.COLOR_BLACK)
                surface.blit(shadow, (text_x + 2, y + 2))
                surface.blit(text_font.render(visible, True, color), (text_x, y))
            y += self.LINE_HEIGHT

        if not self._typing:
            arrow = continue_arrow()
            bob = round(math.sin(self._timer / self.ARROW_BOB_MS)) * s.SCALE
            surface.blit(arrow, arrow.get_rect(bottomright=(box.right - 18,
                                                            box.bottom - 12 + bob)))

    def _draw_portrait(self, surface: pygame.Surface, box: pygame.Rect, look: Look) -> int:
        """Framed bust at the left of the box; returns the frame's right edge."""
        frame = pygame.Rect(0, 0, self.PORTRAIT_FRAME, self.PORTRAIT_FRAME)
        frame.midleft = (box.x + 18, box.centery)
        pygame.draw.rect(surface, self.PORTRAIT_BG, frame)
        talking = self._typing and int(self._timer // self.MOUTH_MS) % 2 == 1
        blinking = self._timer % self.BLINK_EVERY_MS < self.BLINK_MS
        bust = portrait(look, talking, blinking)
        surface.blit(bust, bust.get_rect(midbottom=frame.midbottom))
        pygame.draw.rect(surface, s.COLOR_ACCENT_GOLD, frame, 2)
        return frame.right

    @staticmethod
    def _draw_name_tab(surface: pygame.Surface, name: str, midleft: tuple[int, int]) -> None:
        name_surf = font(30).render(name, True, s.COLOR_TITLE_GOLD)
        tab = name_surf.get_rect().inflate(28, 12)
        tab.midleft = midleft
        draw_panel(surface, tab, fill=(28, 22, 40, 245))
        surface.blit(name_surf, name_surf.get_rect(center=tab.center))
