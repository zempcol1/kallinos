"""Dialogue portraits: a 32×32 head-and-shoulders bust for any ``Look``.

Like the map sprites, every bust is one shared face grid plus a hair-style
overlay, colored by the character's ``Look``. Frames: ``talking`` opens the
mouth, ``blinking`` closes the eyes. Extra legend on top of the character
legend: ``w`` eye white, ``i`` iris, ``I`` glint, ``n`` blush, ``M`` open mouth.
"""

from __future__ import annotations

import pygame

from systems.sprites.characters import Look
from systems.sprites.pixel_art import Color, cached, from_grid, mirrored, scale, shade

PORTRAIT_SIZE = 32

_FACE = mirrored([
    "................",
    "................",
    "................",
    "..........oooooo",
    "........oossssss",
    ".......ossssssss",
    "......osssssssss",
    "......osssssssss",
    ".....ossssssssss",
    ".....ossssssssss",
    ".....ossssssssss",
    ".....osssDDDDsss",
    ".....ossssssssss",
    "....oSssseeeesss",
    "....oSssswIiwsss",
    "....oSssswiiwsss",
    "....oSssssssssss",
    ".....osssnnssssS",
    ".....oSsssssssss",
    "......oBBBBsssmm",
    "......oBBBBBBBBB",
    ".......oBBBBBBBB",
    "........ooBBBBBB",
    "..........oooBBB",
    "............oSss",
    "............oSss",
    "......oooooootrs",
    "....ootttttttUrr",
    "...ottttttttttUt",
    "..oTtttttttttttt",
    "..oTtttttttttttt",
    ".oTTtttttttttttt",
])

_EYE_ROWS = (13, 14, 15)
_EYE_COLS = (9, 10, 11, 12, 19, 20, 21, 22)
_MOUTH = {19: (14, 15, 16, 17), 20: (15, 16)}

_HAIR: dict[str, list[str]] = {
    "short": mirrored([
        "................",
        "................",
        "...........ooooo",
        "........oooHhhhh",
        "......oohhHHhhhh",
        ".....ohhhHHhhhhh",
        "....ohhhHhhhhhhh",
        "....ohhhhhhhhhhh",
        "...ohhhhhhhhhhhh",
        "...ohhhhhDhhhhhD",
        "...ohhDDoohhDDoo",
        "...ohDo.........",
        "....oDo.........",
    ]),
    "tousled": mirrored([
        "..........o....o",
        ".........oho..oh",
        "......o.ohhooohh",
        ".....ohoohhhhhHh",
        "....ohhhhhhHHhhh",
        "...ohhhhhHHhhhhh",
        "...ohhhhHhhhhhhh",
        "..ohhhhhhhhhhhhh",
        "..ohhhhhhhhhhhhh",
        "..ohhDhhhhhDhhhh",
        "..ohDohhhDohhhDh",
        "..ohDo..oo...oDo",
        "...oDo..........",
        "...oDo..........",
        "....o...........",
    ]),
    "curly": mirrored([
        "........oo.oo.oo",
        "......oohhohhohh",
        ".....ohHhDhHhDhH",
        "....ohhDhHhDhHhD",
        "...ohHhhDhHhDhhH",
        "..ohhDhHhhDhHhhD",
        "..ohHhDhhHhDhhHh",
        ".ohhDhhHhDhhHhDh",
        ".ohHhhDhHhhDhHhh",
        ".ohhDhhhhDhhhhDh",
        ".ohhhDhhhDhhhDhh",
        ".ohhDohhDo.ohDo.",
        ".ohDo.oo........",
        "ohhDo...........",
        "ohDDo...........",
        "ohDo............",
        ".oo.............",
    ]),
    "elder": mirrored([
        "................",
        "................",
        "................",
        "................",
        "...........HH...",
        "................",
        "................",
        "..........SSSSSS",
        "....ohH.........",
        "...ohhHh.SSSS...",
        "...ohhhh........",
        "...ohhhho.......",
        "...ohhho........",
        "...ohho.........",
        "...ohho.........",
        "....oo..........",
    ]),
}

_EYE_WHITE: Color = (246, 240, 230)
_IRIS: Color = (70, 46, 32)


def _overlay(base: list[str], top: list[str]) -> list[str]:
    rows = list(base)
    for y, row in enumerate(top):
        rows[y] = "".join(b if t == "." else t for b, t in zip(rows[y], row))
    return rows


def _set(rows: list[str], y: int, cols: tuple[int, ...], ch: str) -> None:
    row = list(rows[y])
    for x in cols:
        row[x] = ch
    rows[y] = "".join(row)


@cached
def portrait(look: Look, talking: bool = False, blinking: bool = False) -> pygame.Surface:
    """Scaled bust of a character for the dialogue box."""
    rows = list(_FACE)
    if blinking:
        for y, ch in zip(_EYE_ROWS, "seS"):
            _set(rows, y, _EYE_COLS, ch)
    if talking:
        for y, cols in _MOUTH.items():
            _set(rows, y, cols, "M")
    rows = _overlay(rows, _HAIR.get(look.hair_style, _HAIR["short"]))

    palette = {
        **look.palette(),
        "w": _EYE_WHITE,
        "i": _IRIS,
        "I": _EYE_WHITE,
        "n": shade((222, 120, 110), 0.2) if not look.bearded else look.skin,
        "M": (92, 40, 40),
    }
    palette["m"] = shade(look.skin, -0.3)
    return scale(from_grid(rows, palette))
