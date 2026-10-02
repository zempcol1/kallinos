"""Item sprites for world pickups and combat weapons."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from systems.sprites.pixel_art import cached, from_grid, outline, scale

_OLIVE_BRANCH = [
    "................",
    "...........gg...",
    "..........gLg...",
    "...........wg...",
    "..........ww....",
    ".........wW.....",
    "........wwgg....",
    ".......wW.gL....",
    "......wW........",
    ".....wW.........",
    "....wW..........",
    "...wW...........",
    "..wW............",
    "..W.............",
    "................",
    "................",
]

_OLIVE_BRANCH_PALETTE = {
    "w": (150, 116, 70),
    "W": (108, 80, 46),
    "g": (100, 132, 74),
    "L": (156, 176, 122),
}


_FIGS = [
    "................",
    "................",
    "................",
    ".......g........",
    "......gG........",
    ".....ppp..g.....",
    "....pPppp.gG....",
    "....pPppp.ppp...",
    "....ppppppPppp..",
    ".....pppppPppp..",
    "......pp.pppp...",
    "..........pp....",
    "................",
    "................",
    "................",
    "................",
]

_FIGS_PALETTE = {
    "p": (112, 58, 98),
    "P": (160, 100, 140),
    "g": (100, 132, 74),
    "G": (74, 98, 58),
}


def _olive_branch() -> pygame.Surface:
    return outline(from_grid(_OLIVE_BRANCH, _OLIVE_BRANCH_PALETTE), (45, 34, 28))


def _figs() -> pygame.Surface:
    return outline(from_grid(_FIGS, _FIGS_PALETTE), (45, 34, 28))


ITEM_GENERATORS: dict[str, Callable[[], pygame.Surface]] = {
    "olive_branch": _olive_branch,
    "figs": _figs,
}


@cached
def item(item_id: str, factor: int | None = None) -> pygame.Surface | None:
    """Scaled sprite for an item id, or None if the item has no art yet."""
    gen = ITEM_GENERATORS.get(item_id)
    if gen is None:
        return None
    return scale(gen()) if factor is None else scale(gen(), factor)
