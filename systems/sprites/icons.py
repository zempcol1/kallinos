"""Small UI sprites drawn on the same pixel grid as the world."""

from __future__ import annotations

import pygame

from systems.sprites.characters import PLAYER_LOOK
from systems.sprites.pixel_art import cached, from_grid, lerp, scale
from systems.sprites.portraits import PORTRAIT_SIZE, portrait

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


_ICON_SKY = ((44, 28, 78), (148, 66, 108), (232, 128, 88), (250, 192, 122))
_ICON_FRAME = (176, 128, 30)


@cached
def app_icon(size: int) -> pygame.Surface:
    """Kallinos against a sunset in a gold frame: the window and .exe icon."""
    n = PORTRAIT_SIZE
    surf = pygame.Surface((n, n), pygame.SRCALPHA)
    for y in range(n):
        t = y / (n - 1) * (len(_ICON_SKY) - 1)
        i = min(int(t), len(_ICON_SKY) - 2)
        pygame.draw.line(surf, lerp(_ICON_SKY[i], _ICON_SKY[i + 1], t - i), (0, y), (n, y))
    surf.blit(portrait(PLAYER_LOOK, factor=1), (0, 1))
    # Round the corners, then frame in gold
    shape = pygame.Surface((n, n), pygame.SRCALPHA)
    pygame.draw.rect(shape, (255, 255, 255, 255), shape.get_rect(), border_radius=6)
    surf.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    pygame.draw.rect(surf, _ICON_FRAME, surf.get_rect(), 1, border_radius=6)
    if size % n == 0:
        return pygame.transform.scale(surf, (size, size))   # crisp pixels
    return pygame.transform.smoothscale(surf, (size, size))
