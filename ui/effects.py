"""Screen effects shared by the states: easing, veils, fades and golden motes."""

from __future__ import annotations

import functools
import math
from collections.abc import Callable

import pygame

import settings as s

FADE_SPEED = 0.5       # veil alpha per ms: a full fade takes about half a second
_MOTE_SPREAD = 0.618   # golden-ratio step: spreads motes evenly without a pattern
_GLINT_EVERY = 3       # with ``glints``, every third mote is white


def ease_out(t: float) -> float:
    """Cubic ease-out of a 0–1 progress (clamped): fast start, soft landing."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


@functools.cache
def _veil(size: tuple[int, int], color: tuple) -> pygame.Surface:
    veil = pygame.Surface(size)
    veil.fill(color)
    return veil


def draw_veil(surface: pygame.Surface, alpha: float, color: tuple = s.COLOR_BLACK) -> None:
    """Cover the whole surface with one color at ``alpha`` (0–255): fades, flashes."""
    if alpha <= 0:
        return
    veil = _veil(surface.get_size(), color)
    veil.set_alpha(min(255, int(alpha)))
    surface.blit(veil, (0, 0))


class ScreenFade:
    """A black veil that fades the screen in or out, then calls back.

    While ``active`` the owner should skip its normal update and input.
    After a fade-out the screen stays black until the next ``fade_in``.
    """

    def __init__(self, speed: float = FADE_SPEED) -> None:
        self._speed = speed
        self._alpha = 0
        self._direction = 0     # -1 fading in (veil lifts), 1 fading out, 0 idle
        self._then: Callable[[], None] | None = None

    @property
    def active(self) -> bool:
        return self._direction != 0

    def fade_in(self, then: Callable[[], None] | None = None) -> None:
        """Start from black and lift the veil; ``then`` runs once it is gone."""
        self._alpha, self._direction, self._then = 255, -1, then

    def fade_out(self, then: Callable[[], None] | None = None) -> None:
        """Darken to black; ``then`` runs once the screen is covered."""
        self._alpha, self._direction, self._then = 0, 1, then

    def update(self, dt: float) -> None:
        if not self.active:
            return
        target = 255 if self._direction > 0 else 0
        self._alpha = max(0, min(255, self._alpha + self._direction * int(dt * self._speed)))
        if self._alpha == target:
            self._direction = 0
            then, self._then = self._then, None
            if then:
                then()

    def render(self, surface: pygame.Surface) -> None:
        draw_veil(surface, self._alpha)


def draw_motes(surface: pygame.Surface, origin: tuple[float, float],
               size: tuple[float, float], time: float, *, count: int, rise_ms: float,
               sway: float, alpha: int = 255, glints: bool = False,
               snap: bool = False) -> None:
    """Golden motes drifting up through a box: Athena's sign.

    Args:
        origin: bottom-left corner of the box the motes rise through.
        size: (width, height) of that box.
        time: animation clock in ms.
        count: number of motes.
        rise_ms: time one mote takes from the bottom to the top.
        sway: how far a mote drifts sideways, in pixels.
        alpha: opacity at the middle of the rise (motes fade in and out).
        glints: make some motes white instead of gold.
        snap: keep the motes on the world's pixel grid.
    """
    left, bottom = origin
    width, height = size
    mote = pygame.Surface((s.SCALE, s.SCALE))
    for i in range(count):
        life = (time / rise_ms + i / count) % 1.0
        x = left + width * ((i * _MOTE_SPREAD) % 1.0) + math.sin(life * math.tau + i) * sway
        y = bottom - life * height
        if snap:
            x, y = round(x / s.SCALE) * s.SCALE, round(y / s.SCALE) * s.SCALE
        mote.fill(s.COLOR_WHITE if glints and i % _GLINT_EVERY == 0 else s.COLOR_TITLE_GOLD)
        mote.set_alpha(int(math.sin(life * math.pi) * alpha))
        surface.blit(mote, (round(x), round(y)))
