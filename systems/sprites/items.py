"""Item sprites for world pickups and combat weapons."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from systems.sprites.pixel_art import cached, from_grid, outline, scale

_OLIVE_BRANCH = [
    "................",
    ".............LL.",
    "............Lg..",
    "...........wg...",
    ".......LL.w.....",
    "........gLwgLL..",
    ".........wWg....",
    ".........wW.....",
    "....LLg.wWd.p...",
    "......gwWd.pPp..",
    "......wWd...pp..",
    ".....wWd........",
    "....wkWd........",
    "...wWWd.........",
    "..wWkd..........",
    "..dWd...........",
]

_OLIVE_BRANCH_PALETTE = {
    "w": (176, 140, 92),
    "W": (128, 96, 60),
    "d": (88, 64, 42),
    "k": (64, 46, 32),
    "g": (110, 136, 84),
    "G": (76, 98, 62),
    "L": (178, 194, 150),
    "p": (66, 52, 74),
    "P": (120, 104, 128),
}


_FIGS = [
    "................",
    "................",
    "....g...........",
    "....gG..........",
    "...pPp..........",
    "..pPPpp.........",
    ".pPPpppp.qqqq...",
    ".pPppppqqccccq..",
    ".ppppppqcRyRRcq.",
    ".pppppqcRRRRyRq.",
    "..pppdqcRyRRRRq.",
    "...pddqcRRRyRcq.",
    "....d..qcRRRcq..",
    ".........qqqq...",
    "................",
    "................",
]

_FIGS_PALETTE = {
    "p": (112, 58, 98),
    "P": (164, 104, 146),
    "d": (78, 38, 70),
    "q": (96, 64, 92),
    "c": (236, 222, 196),
    "R": (206, 74, 92),
    "y": (244, 210, 140),
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
