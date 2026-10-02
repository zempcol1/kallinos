"""Humanoid character sprites: 16×24 logical, 4 directions × 4 walk frames.

All people share the same pixel grids; only the palette changes, so a new
NPC is just a new ``Look``. Grid legend:

    o outline   h hair   H hair highlight   D hair shadow
    s skin      S skin shadow   e eye   B beard (skin unless bearded)
    t tunic     T tunic shadow  b belt  l sandal   . transparent
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import settings as s
from systems.sprites.pixel_art import Color, cached, from_grid, mirrored, scale, shade

DIRECTIONS = ("down", "up", "left", "right")
WALK_FRAMES = 4  # stand, step A, stand, step B

# ── Grids ────────────────────────────────────────────────────────────────────

_BODY_FRONT = [
    "...otttt",
    "..osTttt",
    "..osTttt",
    "..osbbbb",
    "..oSTttt",
    "...oTttt",
    "...oTTTT",
]

_DOWN_TOP = mirrored([
    "........",
    ".....ooo",
    "....ohhh",
    "...ohhhh",
    "...ohhHh",
    "...ohhhs",
    "...ohsss",
    "...ohses",
    "...ossss",
    "...oSsBB",
    "....oSBB",
    ".....ooS",
] + _BODY_FRONT)

_UP_TOP = mirrored([
    "........",
    ".....ooo",
    "....ohhh",
    "...ohhhh",
    "...ohhHh",
    "...ohhhh",
    "...ohhhh",
    "...ohhhh",
    "...oDhhh",
    "...oDDhh",
    "....oDDD",
    ".....ooS",
] + _BODY_FRONT)

_FRONT_LEGS = [
    [  # stand
        "...ooSSooSSoo...",
        "....ossoosso....",
        "....ossoosso....",
        "....olloollo....",
        "....oooooooo....",
    ],
    [  # step A: right foot lifted
        "...ooSSooSSoo...",
        "....ossoosso....",
        "....ossoollo....",
        "....olloooo.....",
        "....oooo........",
    ],
    [  # step B: left foot lifted
        "...ooSSooSSoo...",
        "....ossoosso....",
        "....olloosso....",
        ".....oooollo....",
        "........oooo....",
    ],
]

_RIGHT_TOP = [
    "................",
    ".....oooooo.....",
    "....ohhhhhho....",
    "...ohhhhhhhho...",
    "...ohHhhhhhho...",
    "...ohhhhhhsso...",
    "...ohhhhhssso...",
    "...ohhhhsseso...",
    "...ohhhSssssso..",
    "...oDhhSsBBBo...",
    "....oDDSBBBo....",
    "......ooSSo.....",
    "....otttttto....",
    "....oTtsstto....",
    "....oTtsstto....",
    "....obbssbbo....",
    "....oTtSStto....",
    "....oTttttto....",
    "....oTTTTTTo....",
]

_SIDE_LEGS = [
    [  # stand
        ".....ooSSoo.....",
        "......osso......",
        "......osso......",
        "......olllo.....",
        "......ooooo.....",
    ],
    [  # stride, front leg light
        ".....ooSSoo.....",
        ".....oSooso.....",
        "....oSo..oso....",
        "...olo...ollo...",
        "...ooo...oooo...",
    ],
    [  # stride, front leg shaded
        ".....ooSSoo.....",
        ".....osooSo.....",
        "....oso..oSo....",
        "...olo...ollo...",
        "...ooo...oooo...",
    ],
]

# Frame index -> leg pose index (stand, step A, stand, step B)
_WALK_POSES = (0, 1, 0, 2)


@dataclass(frozen=True)
class Look:
    """Palette describing how one character looks. Must be hashable (cached)."""

    tunic: Color
    hair: Color = (70, 48, 30)
    skin: Color = (226, 186, 146)
    belt: Color = (139, 94, 52)
    sandal: Color = (110, 74, 44)
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
            "B": hair_light if self.bearded else self.skin,
            "t": self.tunic,
            "T": shade(self.tunic, -0.2),
            "b": self.belt,
            "l": self.sandal,
        }


PLAYER_LOOK = Look(tunic=(234, 226, 206), hair=(92, 58, 32))


def _grid(direction: str, frame: int) -> list[str]:
    pose = _WALK_POSES[frame % WALK_FRAMES]
    if direction == "down":
        return _DOWN_TOP + _FRONT_LEGS[pose]
    if direction == "up":
        return _UP_TOP + _FRONT_LEGS[pose]
    return _RIGHT_TOP + _SIDE_LEGS[pose]


@cached
def character(look: Look, direction: str = "down", frame: int = 0,
              factor: int = s.SCALE) -> pygame.Surface:
    """A walk-cycle frame for a character facing ``direction``, scaled by ``factor``."""
    surf = from_grid(_grid(direction, frame), look.palette())
    if direction == "left":
        surf = pygame.transform.flip(surf, True, False)
    return scale(surf, factor)
