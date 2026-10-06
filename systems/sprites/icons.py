"""Small UI sprites drawn on the same pixel grid as the world."""

from __future__ import annotations

import pygame

from systems.sprites.pixel_art import cached, from_grid, scale

_PALETTE = {
    "o": (40, 28, 24),
    "c": (250, 242, 222),
    "C": (220, 204, 170),
    "k": (92, 58, 34),
    "g": (241, 196, 15),
    "G": (176, 128, 30),
    "y": (255, 236, 150),
}

_BUBBLE = [
    ".ooooooo.",
    "occccccco",
    "occkkkcco",
    "occkcccco",
    "occkkccco",
    "occkcccco",
    "occkkkcco",
    "oCCCCCCCo",
    ".oooCooo.",
    "...oCo...",
    "....o....",
]

_LAUREL = [
    "...yy.....yy....",
    "..ygG....ygG....",
    ".ygG....ygG...y.",
    "GGGGGGGGGGGGGGgy",
    ".ygG....ygG...y.",
    "..ygG....ygG....",
    "...yy.....yy....",
]

_ARROW = [
    "ooooooo",
    "oggggGo",
    ".ogggo.",
    "..oGo..",
    "...o...",
]


@cached
def interact_bubble() -> pygame.Surface:
    """Speech bubble with the interact key, shown over whatever is in reach."""
    return scale(from_grid(_BUBBLE, _PALETTE))


@cached
def continue_arrow() -> pygame.Surface:
    """Gold down-arrow: the dialogue line is complete, press to continue."""
    return scale(from_grid(_ARROW, _PALETTE))


@cached
def laurel(flip: bool = False) -> pygame.Surface:
    """Gold laurel sprig framing the selected menu option."""
    surf = from_grid(_LAUREL, _PALETTE)
    return scale(pygame.transform.flip(surf, True, False) if flip else surf)
