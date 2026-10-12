"""Humanoid character sprites: 16×24 logical, 8 directions × 4 walk frames.

Every person is a shared body grid plus a hair-style overlay, colored by a
``Look``; a new NPC is just a new ``Look``. The five drawn views are down,
down_right, right, up_right and up; the left-facing views are mirrored.
Outfit details (the exomis' bare shoulder, a headband, a charm) are small
per-view rules applied on top. Grid legend:

    o outline   h hair   H hair highlight   D hair shadow
    s skin      S skin shadow   e eye   m mouth   f freckle   B beard
    t tunic     T tunic shadow  U tunic light   r tunic trim
    b belt      l sandal / bare foot            . transparent (overlay: keep)
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import settings as s
from systems.sprites.pixel_art import Color, cached, from_grid, scale, shade

DIRECTIONS = ("down", "down_right", "right", "up_right", "up",
              "up_left", "left", "down_left")
WALK_FRAMES = 4  # stand, step A, stand, step B
HAIR_STYLES = ("short", "tousled", "curly", "elder")

# Mirrored views: drawn as their right-facing twin, flipped
_MIRRORED = {"left": "right", "down_left": "down_right", "up_left": "up_right"}

# ── Heads (rows 0-12) ────────────────────────────────────────────────────────

_HEAD_DOWN = [
    "................",
    "................",
    ".....oooooo.....",
    "...oossssssoo...",
    "..osssssssssso..",
    "..osssssssssso..",
    "..oshhsssshhso..",
    ".oSssessssessSo.",
    ".oSssessssessSo.",
    "..osfssssssfso..",
    "..oSBBsmmsBBSo..",
    "...oSBBBBBBSo...",
    "....ooSSSSoo....",
]

_HEAD_DOWN_RIGHT = [
    "................",
    "................",
    ".....oooooo.....",
    "...oossssssoo...",
    "..osssssssssso..",
    "..osssssssssso..",
    "..ossshhssshho..",
    ".oSssssesssesso.",
    ".oSssssesssesso.",
    "..osssfsssssSo..",
    "..oSsBBBsmmBso..",
    "....oSBBBBBSo...",
    ".....ooSSSSo....",
]

_HEAD_RIGHT = [
    "................",
    "................",
    "......oooooo....",
    "....oossssssoo..",
    "...osssssssssso.",
    "...osssssssssso.",
    "...osssssshhsso.",
    "...ossSSsssesso.",
    "...ossSSsssessso",
    "...oSsssssfssso.",
    "....oSssssBBmo..",
    ".....oSsBBBBo...",
    "......oSSSo.....",
]

_HEAD_BACK = [
    "................",
    "................",
    ".....oooooo.....",
    "...oossssssoo...",
    "..osssssssssso..",
    "..osssssssssso..",
    "..osssssssssso..",
    ".oSssssssssssSo.",
    ".oSssssssssssSo.",
    "..osssssssssso..",
    "..oSssssssssSo..",
    "...oSssssssSo...",
    "....ooSSSSoo....",
]

# ── Torsos (rows 13-20) ──────────────────────────────────────────────────────

_TORSO_FRONT = [
    "...oottssttoo...",
    "..otTUttttUTto..",
    "..otTttttttTto..",
    "..osTttttttTso..",
    "..osbbbbbbbbso..",
    "..oSTttttttTSo..",
    "...oTttttttTo...",
    "...orrrrrrrro...",
]

_TORSO_BACK = [
    "...oottttttoo...",
    "..otTUttttUTto..",
    "..otTttttttTto..",
    "..osTttttttTso..",
    "..osbbbbbbbbso..",
    "..oSTttttttTSo..",
    "...oTttttttTo...",
    "...orrrrrrrro...",
]

_TORSO_RIGHT = [
    ".....otUUtto....",
    ".....oTUttto....",
    ".....oTttTto....",
    ".....oTssTto....",
    ".....obssbbo....",
    ".....oTsSTto....",
    ".....oTooTtto...",
    ".....orrrrrro...",
]

# Arm swing, by walk frame: replacement rows (indexed from the sprite top)
_FRONT_ARMS = [
    {},
    {15: "..osTttttttTto..", 16: "..osTttttttTto..", 17: "..oSbbbbbbbbso..",
     18: "...oTttttttTso..", 19: "...oTttttttTSo.."},
    {},
    {15: "..otTttttttTso..", 16: "..otTttttttTso..", 17: "..osbbbbbbbbSo..",
     18: "..osTttttttTo...", 19: "..oSTttttttTo..."},
]
_SIDE_ARMS = [
    {},
    {14: ".....oUTttto....", 15: "....oUTtttto....", 16: "....osTtttto....",
     17: "....oSbbbbbo....", 18: ".....oTtttto....", 19: ".....oTttttto..."},
    {},
    {14: ".....otTUUto....", 15: ".....otttUUo....", 16: ".....otttTsso...",
     17: ".....obbbbSso...", 18: ".....otttttoo...", 19: ".....oTttttto..."},
]

# ── Legs (rows 21-23): stand, step A, step B ─────────────────────────────────

_FRONT_LEGS = [
    ["....ossoosso....",
     "....olloollo....",
     "....oooooooo...."],
    ["....ossoollo....",
     "....olloooo.....",
     "....oooo........"],
    ["....olloosso....",
     ".....oooollo....",
     "........oooo...."],
]
_DIAGONAL_LEGS = [
    [".....ossoosso...",
     ".....ollooollo..",
     ".....ooooooooo.."],
    [".....ossoolllo..",
     "....olloooooo...",
     "....oooo........"],
    ["....olllosso....",
     "....oooooollo...",
     "........ooooo..."],
]
_SIDE_LEGS = [
    ["......ossSo.....",
     "......ollllo....",
     "......oooooo...."],
    [".....oSo.osso...",
     "....ollo..ollo..",
     "....oooo..oooo.."],
    [".....oso.oSSo...",
     "....ollo..ollo..",
     "....oooo..oooo.."],
]

# Frame index -> leg pose index (stand, step A, stand, step B)
_WALK_POSES = (0, 1, 0, 2)

# ── Hair overlays (rows 0-12) ────────────────────────────────────────────────

_HAIR: dict[str, dict[str, list[str]]] = {
    # Kallinos: a messy mop with a cowlick, strands falling over the forehead
    "tousled": {
        "down": [
            "..........o.....",
            "....o.oo..oHo...",
            "...ohohhoohHho..",
            "..ohhHhhhhhHhho.",
            ".ohhhHhhhhhhHhho",
            ".ohhhhhhhhhhhhDo",
            ".oDh....h...hDo.",
            ".oD..........Do.",
        ],
        "down_right": [
            "...........o....",
            ".....o.oo..oHo..",
            "...oohohhoohHho.",
            "..ohhHhhhhhhHhho",
            ".ohhhhHhhhhhhhHo",
            ".ohhhhhhhhhhhhDo",
            ".oDhhh....h...o.",
            ".oDD...........o",
        ],
        "right": [
            ".........o......",
            ".....o.oohoo....",
            "....oohhhHhhoo..",
            "...ohhhhHHhhhho.",
            "..ohhhhhhhhhhhDo",
            "..ohhhhhhhhhhoo.",
            "..ohhhhhhDho....",
            "..oDhhhoo.o.....",
            "..oDhDo.........",
            "...oDo..........",
        ],
        "up_right": [
            "...........o....",
            ".....o.oo..oHo..",
            "...oohohhoohHho.",
            "..ohhHhhhhhhHhho",
            ".ohhhhHhhhhhhhho",
            ".ohhhhhhhhhhhhDo",
            ".ohhhhhhhhhhhhDo",
            ".ohhhhhhhhhhDo..",
            "..ohhhhhhhhDo...",
            "..oDhDhhDhDo....",
            "...oDoDDoDo.....",
        ],
        "up": [
            "..........o.....",
            "....o.oo..oHo...",
            "...ohohhoohHho..",
            "..ohhHhhhhhHhho.",
            ".ohhhHhhhhhhHhho",
            ".ohhhhhhhhhhhhDo",
            ".ohhhhhhhhhhhhDo",
            "..oDhhhhhhhhDo..",
            "..oDhhhhhhhhDo..",
            "..oDhDhhDhhDDo..",
            "...oDoDDoDDoo...",
        ],
    },
    # Doros: neat short hair swept to one side, forehead showing
    "short": {
        "down": [
            "................",
            "................",
            ".....oooooo.....",
            "...oohHhhHhoo...",
            "..ohhHhhHhhhHho.",
            "..ohHhhHhhDo....",
            "..oDhhho........",
            ".oD..........Do.",
        ],
        "down_right": [
            "................",
            "................",
            ".....oooooo.....",
            "...oohHhhhHoo...",
            "..ohhHhhhHhhHho.",
            "..ohhhHhhhhhDo..",
            "..oDhhhhho......",
            ".oDD............",
        ],
        "right": [
            "................",
            "......oooooo....",
            "....oohhhhhhoo..",
            "...ohhhhhHHhhho.",
            "..ohhhhhhHhhhho.",
            "..ohhhhhhhhhDo..",
            "..ohhhhhhhDo....",
            "..oDhh..........",
            "...oDD..........",
            "....o...........",
        ],
        "up_right": [
            "................",
            "................",
            ".....oooooo.....",
            "...oohhhhhHoo...",
            "..ohhhhhhHHhhho.",
            "..ohhhhhhhhhhho.",
            "..ohhhhhhhhhhho.",
            "..oDhhhhhhhhDo..",
            "..oDhhhhhhhDo...",
            "...oDDhhhhDo....",
            "....oDDDDDo.....",
        ],
        "up": [
            "................",
            "................",
            ".....oooooo.....",
            "...oohhhhHhoo...",
            "..ohhhhhHHhhho..",
            "..ohhhhhhhhhho..",
            "..ohhhhhhhhhho..",
            "..oDhhhhhhhhDo..",
            "..oDhhhhhhhhDo..",
            "...oDDhhhhDDo...",
            "....oDDDDDDo....",
        ],
    },
    # Niko: a big mop of curls, curl texture all over, covering the ears
    "curly": {
        "down": [
            "....oo.oo.oo....",
            "...ohHohHohHo...",
            "..ohDhhDhhDhhDo.",
            ".ohHhDhHhDhHhDho",
            "ohDhhHhDhhHhDhho",
            "ohhDhhhhDhhhhDDo",
            "ohDho.....ohDDo.",
            "oDDo.......oDDo.",
            ".oo.........oo..",
        ],
        "down_right": [
            "....oo.oo.oo....",
            "...ohHohHohHo...",
            "..ohDhhDhhDhhDo.",
            ".ohHhDhHhDhHhDho",
            "ohDhhHhDhhHhDhho",
            "ohhDhhhhDhhhhDDo",
            "ohDhDho.....ohDo",
            "oDDhDo.......oo.",
            ".oDDo...........",
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
        "up_right": [
            "....oo.oo.oo....",
            "...ohHohHohHo...",
            "..ohDhhDhhDhhDo.",
            ".ohHhDhHhDhHhDho",
            "ohDhhHhDhhHhDhho",
            "ohhDhhhhDhhhhDDo",
            "ohHhhDhHhhDhhHDo",
            "ohhDhhHhhDhhDo..",
            "oDhhDhhDhhDDo...",
            ".oDDhDDhDDDo....",
            "..oDDooDDoo.....",
        ],
        "up": [
            "....oo.oo.oo....",
            "...ohHohHohHo...",
            "..ohDhhDhhDhhDo.",
            ".ohHhDhHhDhHhDho",
            "ohDhhHhDhhHhDhho",
            "ohhDhhhhDhhhhDDo",
            "ohHhhDhHhhDhhHDo",
            "ohhDhhHhhDhhHhDo",
            "oDhhDhhDhhDhhDDo",
            ".oDDhDDhDDhDDDo.",
            "..oDDooDDooDDo..",
        ],
    },
    # Elder: bald crown with a shine, white hair around the sides and back
    "elder": {
        "down": [
            "................",
            "................",
            "................",
            "......HH........",
            "................",
            "................",
            ".oh..........ho.",
            ".ohh........hho.",
            ".ohh........hho.",
            "..oh........ho..",
        ],
        "down_right": [
            "................",
            "................",
            "................",
            ".......HH.......",
            "................",
            "................",
            ".ohh............",
            ".ohhh...........",
            ".ohhh...........",
            "..ohh...........",
        ],
        "right": [
            "................",
            "................",
            "................",
            "........HH......",
            "...oHH..........",
            "..ohhHH.........",
            "..ohhhh.........",
            "..ohhhh.........",
            "..ohhhD.........",
            "...ohD..........",
            "....o...........",
        ],
        "up_right": [
            "................",
            "................",
            "................",
            "......HH........",
            "................",
            "..oh.........o..",
            ".ohhhhhhhhhhho..",
            "..ohhhhhhhhhDo..",
            "..ohhhhhhhhDo...",
            "..oDhhhhhhDo....",
            "...oDDDDDDo.....",
        ],
        "up": [
            "................",
            "................",
            "................",
            "......HH........",
            "................",
            "..oh........ho..",
            ".ohhhhhhhhhhhho.",
            "..ohhhhhhhhhho..",
            "..ohhhhhhhhhho..",
            "..oDhhhhhhhhDo..",
            "...oDDDDDDDDo...",
        ],
    },
}

# ── Outfit and accessory rules, per drawn view ───────────────────────────────

# Exomis: the worker's tunic leaves one shoulder bare. (cols, rows) region
# where cloth becomes skin, then the cloth's diagonal edge.
_EXOMIS = {
    "down": ((range(2, 7), range(13, 17)), [(7, 14), (6, 15), (5, 16)]),
    "down_right": ((range(3, 8), range(13, 17)), [(8, 14), (7, 15), (6, 16)]),
    "right": ((range(6, 10), range(13, 16)), [(10, 15)]),
    "up_right": ((range(9, 15), range(13, 17)), [(9, 14), (10, 15), (11, 16)]),
    "up": ((range(9, 14), range(13, 17)), [(8, 14), (9, 15), (10, 16)]),
}
_TO_SKIN = {"t": "s", "U": "s", "T": "S"}

# Charm: a cord ("k") and an olive-wood pendant ("c")
_CHARM = {
    "down": [(6, 13, "k"), (9, 13, "k"), (7, 14, "c"), (8, 14, "c")],
    "down_right": [(7, 13, "k"), (10, 13, "k"), (8, 14, "c"), (9, 14, "c")],
    "right": [(10, 13, "k"), (10, 14, "c")],
}

# Headband: the hair on this row becomes the band; knot tails hang behind
_HEADBAND_ROW = {"down": 4, "down_right": 4, "right": 4, "up_right": 4, "up": 4}
_HEADBAND_KNOT = {
    "right": [(2, 5, "w"), (2, 6, "W"), (1, 7, "W")],
    "up_right": [(6, 5, "w"), (7, 6, "W"), (6, 7, "W")],
    "up": [(7, 5, "w"), (8, 6, "W"), (7, 7, "W")],
}


@dataclass(frozen=True)
class Look:
    """Palette and accessories for one character. Must be hashable (cached).

    ``outfit`` is ``"chiton"`` (default) or ``"exomis"`` (one bare shoulder).
    """

    tunic: Color
    hair: Color = (70, 48, 30)
    skin: Color = (226, 186, 146)
    belt: Color = (139, 94, 52)
    sandal: Color = (110, 74, 44)
    trim: Color | None = None          # tunic hem; defaults to a darker tunic
    hair_style: str = "short"
    bearded: bool = False
    outfit: str = "chiton"
    headband: Color | None = None
    charm: bool = False
    barefoot: bool = False
    freckles: bool = False
    face: str = "plain"                # portrait expression set

    def palette(self) -> dict[str, Color]:
        hair_light = shade(self.hair, 0.3)
        skin_shadow = shade(self.skin, -0.18)
        band = self.headband or self.hair
        return {
            "o": (40, 28, 24),
            "h": self.hair,
            "H": hair_light,
            "D": shade(self.hair, -0.3),
            "s": self.skin,
            "S": skin_shadow,
            "e": (34, 24, 20),
            "m": shade(self.skin, -0.32),
            "f": shade(self.skin, -0.14) if self.freckles else self.skin,
            "B": hair_light if self.bearded else self.skin,
            "t": self.tunic,
            "T": shade(self.tunic, -0.2),
            "U": shade(self.tunic, 0.2),
            "r": self.trim or shade(self.tunic, -0.35),
            "b": self.belt,
            "l": self.skin if self.barefoot else self.sandal,
            "w": band,
            "W": shade(band, -0.25),
            "k": (70, 48, 32),
            "c": (176, 136, 82),
        }


PLAYER_LOOK = Look(tunic=(196, 188, 164), hair=(92, 58, 32), skin=(214, 166, 120),
                   belt=(150, 118, 76),
                   hair_style="tousled", outfit="exomis", headband=(192, 92, 60),
                   charm=True, barefoot=True, freckles=True, face="cheeky")


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


def _shift(rows: list[str], dx: int) -> list[str]:
    """Shift rows right by ``dx`` pixels, keeping the width."""
    return [("." * dx + row)[:len(row)] for row in rows]


def _set(rows: list[str], x: int, y: int, ch: str) -> None:
    rows[y] = rows[y][:x] + ch + rows[y][x + 1:]


def _dress(rows: list[str], look: Look, view: str) -> list[str]:
    """Apply outfit rules: bare shoulder, headband, charm."""
    rows = list(rows)
    if look.outfit == "exomis" and view in _EXOMIS:
        (cols, ys), edge = _EXOMIS[view]
        for y in ys:
            for x in cols:
                ch = rows[y][x]
                if ch in _TO_SKIN:
                    _set(rows, x, y, _TO_SKIN[ch])
        for x, y in edge:
            if rows[y][x] in "tU":
                _set(rows, x, y, "T")
    if look.headband and view in _HEADBAND_ROW:
        y = _HEADBAND_ROW[view]
        right_side = len(rows[y]) * 2 // 3
        for x, ch in enumerate(rows[y]):
            if ch in "hHD":
                _set(rows, x, y, "W" if x >= right_side else "w")
        for x, ky, ch in _HEADBAND_KNOT.get(view, ()):
            _set(rows, x, ky, ch)
    if look.charm:
        for x, y, ch in _CHARM.get(view, ()):
            _set(rows, x, y, ch)
    return rows


def _grid(look: Look, view: str, frame: int) -> list[str]:
    pose = _WALK_POSES[frame % WALK_FRAMES]
    arms = frame % WALK_FRAMES
    hair = _HAIR.get(look.hair_style, _HAIR["short"])[view]
    if view == "right":
        top = _patch(_HEAD_RIGHT + _TORSO_RIGHT, _SIDE_ARMS[arms])
        legs = _SIDE_LEGS[pose]
    else:
        back = view.startswith("up")
        head = _HEAD_BACK if back else (_HEAD_DOWN_RIGHT if view == "down_right" else _HEAD_DOWN)
        torso = _patch(_HEAD_DOWN + (_TORSO_BACK if back else _TORSO_FRONT),
                       _FRONT_ARMS[arms])[13:]
        if view in ("down_right", "up_right"):
            torso = _shift(torso, 1)
            legs = _DIAGONAL_LEGS[pose]
        else:
            legs = _FRONT_LEGS[pose]
        top = head + torso
    rows = _overlay(top + legs, hair)
    return _dress(rows, look, view)


@cached
def character(look: Look, direction: str = "down", frame: int = 0,
              factor: int = s.SCALE) -> pygame.Surface:
    """A walk-cycle frame for a character facing ``direction``, scaled by ``factor``."""
    view = _MIRRORED.get(direction, direction)
    surf = from_grid(_grid(look, view, frame), look.palette())
    if direction in _MIRRORED:
        surf = pygame.transform.flip(surf, True, False)
    return scale(surf, factor)


# ── Battle poses (side view, facing right) ──────────────────────────────────

# Rows 13-20 for each pose; the near arm reaches forward to hold a weapon
_POSES = {
    "ready": [
        ".....otUUtto....",
        ".....oTUtUUUoo..",
        ".....oTttTsssso.",
        ".....oTtttoSSso.",
        ".....obbbbbooo..",
        ".....oTtttto....",
        ".....oTttttto...",
        ".....orrrrrro...",
    ],
    "strike": [
        ".....otUUtto....",
        ".....oTUttto....",
        ".....oTttUUUo...",
        ".....oTttTssso..",
        ".....obbbbossso.",
        ".....oTtttooSo..",
        ".....oTttttto...",
        ".....orrrrrro...",
    ],
}
# Where the weapon's grip goes, in logical pixels of the pose sprite
POSE_HANDS = {"ready": (13, 15), "strike": (12, 17)}
_POSE_EXOMIS = (range(6, 14), range(13, 18))


@cached
def battle_pose(look: Look, pose: str = "ready", factor: int = s.COMBAT_SCALE) -> pygame.Surface:
    """Kallinos (or anyone) in a fighting stance, side view, arm out for a weapon."""
    hair = _HAIR.get(look.hair_style, _HAIR["short"])["right"]
    rows = _overlay(_HEAD_RIGHT + _POSES[pose] + _SIDE_LEGS[1], hair)
    rows = _dress(rows, look, "right")
    if look.outfit == "exomis":
        cols, ys = _POSE_EXOMIS
        for y in ys:
            for x in cols:
                if rows[y][x] in "tU" and x > 8:
                    _set(rows, x, y, "s")
    return scale(from_grid(rows, look.palette()), factor)


@cached
def character_shadow() -> pygame.Surface:
    """Soft oval under a character's feet, on the same pixel grid as the sprite."""
    surf = pygame.Surface((12, 4), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (36, 30, 52, 80), surf.get_rect())
    return scale(surf)
