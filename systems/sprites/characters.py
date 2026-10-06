"""Humanoid character sprites: 16×24 logical, 4 directions × 4 walk frames.

Every person is a shared body grid plus a hair-style overlay, re-colored by
a ``Look``; a new NPC is just a new ``Look``. The left view is the mirrored
right view. Grid legend:

    o outline   h hair   H hair highlight   D hair shadow
    s skin      S skin shadow   e eye   m mouth   B beard (skin unless bearded)
    t tunic     T tunic shadow  U tunic light   r tunic trim
    b belt      l sandal        . transparent (in an overlay: keep the body)
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import settings as s
from systems.sprites.pixel_art import Color, cached, from_grid, mirrored, scale, shade

DIRECTIONS = ("down", "up", "left", "right")
WALK_FRAMES = 4  # stand, step A, stand, step B
HAIR_STYLES = ("short", "tousled", "curly", "elder")

# ── Body grids ───────────────────────────────────────────────────────────────

_HEAD_FRONT = [
    "........",
    "........",
    ".....ooo",
    "...oosss",
    "..osssss",
    "..osssss",
    "..osssss",
    ".oSssess",
    ".oSssess",
    "..osssss",
    "..oSsBBm",
    "...oSBBB",
    "....ooSS",
]

_HEAD_BACK = [
    "........",
    "........",
    ".....ooo",
    "...oosss",
    "..osssss",
    "..osssss",
    "..osssss",
    ".oSsssss",
    ".oSsssss",
    "..osssss",
    "..oSssss",
    "...oSsss",
    "....ooSS",
]

_TORSO_FRONT = [
    "...oottU",
    "..otTUtt",
    "..otTttt",
    "..osTttt",
    "..osbbbb",
    "..oSTttt",
    "...oTttt",
    "...orrrr",
]

_TORSO_BACK = ["...ootttt"[:8]] + _TORSO_FRONT[1:]

_DOWN_TOP = mirrored(_HEAD_FRONT + _TORSO_FRONT)
_UP_TOP = mirrored(_HEAD_BACK + _TORSO_BACK)

# Front/back arms swing a little: one hand slips behind the body
_FRONT_ARMS = [
    {},
    {15: "..osTttttttTto..", 16: "..osTttttttTto..", 17: "..oSbbbbbbbbso..",
     18: "...oTttttttTso..", 19: "...oTttttttTSo.."},
    {},
    {15: "..otTttttttTso..", 16: "..otTttttttTso..", 17: "..osbbbbbbbbSo..",
     18: "..osTttttttTo...", 19: "..oSTttttttTo..."},
]

_FRONT_LEGS = [
    [  # stand
        "....ossoosso....",
        "....olloollo....",
        "....oooooooo....",
    ],
    [  # step A: right foot lifted
        "....ossoollo....",
        "....olloooo.....",
        "....oooo........",
    ],
    [  # step B: left foot lifted
        "....olloosso....",
        ".....oooollo....",
        "........oooo....",
    ],
]

_SIDE_TOP = [
    "................",
    "................",
    "......oooooo....",
    "....oossssssoo..",
    "...osssssssssso.",
    "...osssssssssso.",
    "...osssssssssso.",
    "...ossSSsssesso.",
    "...ossSSsssessso",
    "...oSssssssssso.",
    "....oSssssBBmo..",
    ".....oSsBBBBo...",
    "......oSSSo.....",
    ".....otUUtto....",
    ".....oTUttto....",
    ".....oTttTto....",
    ".....oTssTto....",
    ".....obssbbo....",
    ".....oTsSTto....",
    ".....oTooTtto...",
    ".....orrrrrro...",
]

# Side-view arm swing (rows 14-19), forward on step B, back on step A
_SIDE_ARMS = [
    {},
    {14: ".....oUTttto....", 15: "....oUTtttto....", 16: "....osTtttto....",
     17: "....oSbbbbbo....", 18: ".....oTtttto....", 19: ".....oTttttto..."},
    {},
    {14: ".....otTUUto....", 15: ".....otttUUo....", 16: ".....otttTsso...",
     17: ".....obbbbSso...", 18: ".....otttttoo...", 19: ".....oTttttto..."},
]

_SIDE_LEGS = [
    [  # stand
        "......ossSo.....",
        "......ollllo....",
        "......oooooo....",
    ],
    [  # stride, near leg forward
        ".....oSo.osso...",
        "....ollo..ollo..",
        "....oooo..oooo..",
    ],
    [  # stride, far leg forward
        ".....oso.oSSo...",
        "....ollo..ollo..",
        "....oooo..oooo..",
    ],
]

# Frame index -> leg pose index (stand, step A, stand, step B)
_WALK_POSES = (0, 1, 0, 2)

# ── Hair overlays (rows 0..12 of the 16-wide sprite) ─────────────────────────

_HAIR: dict[str, dict[str, list[str]]] = {
    "short": {
        "down": mirrored([
            "........",
            ".....ooo",
            "...oohhh",
            "..ohhhhH",
            "..ohhHHh",
            ".ohhhhhh",
            ".ohDhhhh",
            "..oD....",
        ]),
        "up": mirrored([
            "........",
            ".....ooo",
            "...oohhh",
            "..ohhhhH",
            "..ohhHHh",
            ".ohhhhhh",
            ".ohhhhhh",
            "..ohhhhh",
            "..ohDhhh",
            "..oDDhhh",
            "...oDDDD",
        ]),
        "right": [
            "................",
            "......oooooo....",
            "....oohhhhhhoo..",
            "...ohhhhhHHhhho.",
            "..ohhhhhhHhhhho.",
            "..ohhhhhhhhhDo..",
            "..ohhhhhhhhDo...",
            "..oDhh..........",
            "...oDD..........",
            "....o...........",
        ],
    },
    "tousled": {
        "down": [
            "......o..o......",
            "....ooHoohoo....",
            "...ohhhhHhhhoo..",
            "..ohhhHHhhhhhho.",
            ".ohhhHhhhhhhhhho",
            ".ohhhhhhhhhhhhho",
            ".ohDhhohhDhhohDo",
            ".oDo.o.oo.o..oDo",
            "..o...........o.",
        ],
        "up": [
            "......o..o......",
            "....ooHoohoo....",
            "...ohhhhHhhhoo..",
            "..ohhhHHhhhhhho.",
            ".ohhhHhhhhhhhhho",
            ".ohhhhhhhhhhhhho",
            ".ohhhhhhhhhhhhho",
            ".oDhhhhhhhhhhhDo",
            "..ohDhhhhhhhDho.",
            "..oDDhDhhDhDDDo.",
            "...oDoDDoDDoDo..",
        ],
        "right": [
            ".......o..o.....",
            ".....oohoohoo...",
            "....ohhhHHhhhoo.",
            "..oohhhHHhhhhhho",
            ".ohhhhhhhhhhhhDo",
            ".ohhhhhhhhhhhoo.",
            ".ohhhhhhhDhoo...",
            "..oDhhhoo.o.....",
            "..oDhDo.........",
            "...oDo..........",
        ],
    },
    "curly": {
        "down": [
            "....oo.oo.oo....",
            "...ohhohhohho...",
            "..ohHhhHhhhhho..",
            ".ohhhHhhhhHhhhho",
            "ohHhhhhhHhhhhhho",
            "ohhhhhhhhhhhhhDo",
            "ohDhhoDhhDohhDDo",
            "ohDho......ohDDo",
            "oDDo........oDDo",
            ".oo..........oo.",
        ],
        "up": [
            "....oo.oo.oo....",
            "...ohhohhohho...",
            "..ohHhhHhhhhho..",
            ".ohhhHhhhhHhhhho",
            "ohHhhhhhHhhhhhho",
            "ohhhhhhhhhhhhhDo",
            "ohhhHhhhhhHhhhDo",
            "ohhhhhhhhhhhhDDo",
            "ohDhhhhhhhhhhDDo",
            "oDDhDhhDhhDhDDDo",
            ".oDDoDDoDDoDDDo.",
            "..oo.oo.oo.oo...",
        ],
        "right": [
            "....oo.oo.oo....",
            "...ohhohhohhoo..",
            "..ohHhhHhhhhhho.",
            ".ohhhhhhhHhhhho.",
            "ohHhhhhhhhhhhDo.",
            "ohhhhhhhhhhDDo..",
            "ohhhhhhhhDoo....",
            "ohDhhhhDo.......",
            "oDDhDDo.........",
            ".oDDDo..........",
            "..ooo...........",
        ],
    },
    "elder": {
        "down": mirrored([
            "........",
            "........",
            ".....ooo",
            "...oosss",
            "..oHssss",
            ".ohHssss",
            ".ohhssss",
            ".ohh....",
            ".ohh....",
            "..oh....",
        ]),
        "up": mirrored([
            "........",
            "........",
            ".....ooo",
            "...oosss",
            "..osssss",
            ".ohHssss",
            ".ohhHhhh",
            ".ohhhhhh",
            ".ohhhhhh",
            "..ohhhhh",
            "..oDhhhh",
            "...oDDDD",
        ]),
        "right": [
            "................",
            "................",
            "......oooooo....",
            "....oossssssoo..",
            "...oHHssssssss..",
            "..ohhHHsssssss..",
            "..ohhhh.........",
            "..ohhhh.........",
            "..ohhhD.........",
            "...ohD..........",
            "....o...........",
        ],
    },
}
# The elder's fringe-less mirrored rows need even widths; pad any short half rows
for style in _HAIR.values():
    for view, rows in style.items():
        style[view] = [row.ljust(16, ".")[:16] for row in rows]


@dataclass(frozen=True)
class Look:
    """Palette describing how one character looks. Must be hashable (cached)."""

    tunic: Color
    hair: Color = (70, 48, 30)
    skin: Color = (226, 186, 146)
    belt: Color = (139, 94, 52)
    sandal: Color = (110, 74, 44)
    trim: Color | None = None          # tunic hem; defaults to a darker tunic
    hair_style: str = "short"
    bearded: bool = False

    def palette(self) -> dict[str, Color]:
        hair_light = shade(self.hair, 0.3)
        return {
            "o": (40, 28, 24),
            "h": self.hair,
            "H": hair_light,
            "D": shade(self.hair, -0.3),
            "s": self.skin,
            "S": shade(self.skin, -0.18),
            "e": (34, 24, 20),
            "m": shade(self.skin, -0.32),
            "B": hair_light if self.bearded else self.skin,
            "t": self.tunic,
            "T": shade(self.tunic, -0.2),
            "U": shade(self.tunic, 0.2),
            "r": self.trim or shade(self.tunic, -0.35),
            "b": self.belt,
            "l": self.sandal,
        }


PLAYER_LOOK = Look(tunic=(234, 226, 206), hair=(92, 58, 32), trim=(176, 92, 64),
                   hair_style="tousled")


def _overlay(base: list[str], top: list[str]) -> list[str]:
    """Lay ``top`` over ``base`` row by row; '.' in ``top`` keeps the base."""
    rows = list(base)
    for y, row in enumerate(top):
        rows[y] = "".join(b if t == "." else t for b, t in zip(rows[y], row))
    return rows


def _patch(rows: list[str], replacements: dict[int, str]) -> list[str]:
    rows = list(rows)
    for y, row in replacements.items():
        rows[y] = row
    return rows


def _grid(look: Look, direction: str, frame: int) -> list[str]:
    pose = _WALK_POSES[frame % WALK_FRAMES]
    hair = _HAIR.get(look.hair_style, _HAIR["short"])
    if direction in ("down", "up"):
        top = _DOWN_TOP if direction == "down" else _UP_TOP
        rows = _overlay(top, hair[direction])
        rows = _patch(rows, _FRONT_ARMS[frame % WALK_FRAMES])
        return rows + _FRONT_LEGS[pose]
    rows = _overlay(_SIDE_TOP, hair["right"])
    rows = _patch(rows, _SIDE_ARMS[frame % WALK_FRAMES])
    return rows + _SIDE_LEGS[pose]


@cached
def character(look: Look, direction: str = "down", frame: int = 0,
              factor: int = s.SCALE) -> pygame.Surface:
    """A walk-cycle frame for a character facing ``direction``, scaled by ``factor``."""
    surf = from_grid(_grid(look, direction, frame), look.palette())
    if direction == "left":
        surf = pygame.transform.flip(surf, True, False)
    return scale(surf, factor)


@cached
def character_shadow() -> pygame.Surface:
    """Soft oval under a character's feet, on the same pixel grid as the sprite."""
    surf = pygame.Surface((12, 4), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (36, 30, 52, 80), surf.get_rect())
    return scale(surf)
