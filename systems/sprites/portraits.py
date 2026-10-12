"""Dialogue portraits: a 48×48 head-and-shoulders bust, turned slightly right.

Busts are drawn at a finer pixel size than the map (2× instead of 3×) so
faces can carry expression. Each ``Look.face`` is its own face: head shape,
eyes, brows, nose and mouth come from small hand-drawn grids, so Kallinos,
Doros, Niko and Theron differ in more than their hair. Frames: ``talking``
opens the mouth, ``blinking`` closes the eyes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from systems.sprites.characters import Look
from systems.sprites.pixel_art import Color, cached, lerp, scale, seeded, shade, stamp

PORTRAIT_SIZE = 48
PORTRAIT_SCALE = 2

OUTLINE = (40, 28, 24)
EYE_WHITE = (246, 240, 230)
IRIS = (86, 58, 38)
PUPIL = (36, 24, 20)
LASH = (40, 28, 24)
LIPS = (172, 96, 84)
MOUTH = (92, 38, 40)
TEETH = (246, 240, 230)
BLUSH = (226, 128, 112)

# Shared head geometry (logical pixels): the face is turned a little to the
# right, so the ear shows on the left and the nose shades to the right.
_CRANIUM = pygame.Rect(11, 4, 26, 28)
_NECK = [(19, 31), (30, 31), (31, 42), (18, 42)]
_EAR = pygame.Rect(9, 20, 5, 8)
_NEAR_EYE = (16, 20)                # top-left of the left eye grid
_FAR_EYE = (27, 20)
_NOSE = (23, 22)
_MOUTH = (21, 31)
_BROW_GAP = 4                       # rows between a brow and its eye


@dataclass(frozen=True)
class _Face:
    """One character's face: shape and features (grids use the legend below).

    e lash · W eye white · i iris · p pupil · I glint · S skin shade · L skin
    light · n nostril · h brow (hair color) · D brow shadow · m lip line ·
    M open mouth · T teeth
    """

    jaw: tuple[tuple[int, int], ...]
    eyes: tuple[list[str], list[str]]           # left, right
    brows: tuple[list[str], list[str]]
    brow_lift: tuple[int, int]                   # rows up (+) or down (-), left/right
    nose: list[str]
    mouth: list[str]
    mouth_open: list[str]
    blush: int = 2                               # blush width, 0 for none


_FACES: dict[str, _Face] = {
    # Kallinos: round young face, big bright eyes, one brow up, crooked grin
    "cheeky": _Face(
        jaw=((12, 22), (13, 29), (16, 34), (21, 37), (27, 37), (32, 34), (35, 29),
             (36, 22), (36, 16)),
        eyes=([".eeee.", "eWiiIe", "eWippe", ".Wiiw."],
              [".eeee.", "eWiIWe", "eWppWe", ".wiiW."]),
        brows=(["..hhh.", ".h...h"], [".hhhh.", "h....."]),
        brow_lift=(1, 0),
        nose=["..S.", "..S.", ".LSS", "..n."],
        mouth=[".....m", "mmmmm.", "..SS.."],
        mouth_open=["....mm", "mMMMMm", ".MTTM.", "..mm.."],
    ),
    # Doros: long narrow face, wide anxious eyes, brows up in the middle
    "worried": _Face(
        jaw=((13, 22), (14, 30), (17, 36), (22, 39), (27, 39), (31, 36), (34, 30),
             (35, 22), (35, 16)),
        eyes=(["..eee.", ".WWiIe", "eWWipe", ".WWWw."],
              [".eee..", "eWiIWW", "eWpiWe", ".wWWW."]),
        brows=(["....hh", "hhhhD."], ["hh....", ".Dhhhh"]),
        brow_lift=(1, 1),
        nose=["..S.", "..S.", "..S.", "..SS", ".LSS", "..n."],
        mouth=[".mmmm.", "m....m"],
        mouth_open=[".mmmm.", "mMMMMm", ".mmmm."],
        blush=0,
    ),
    # Niko: square jaw, low determined brows, narrowed eyes, wide toothy grin
    "bold": _Face(
        jaw=((12, 22), (12, 30), (15, 35), (20, 38), (29, 38), (34, 35), (36, 29),
             (37, 22), (36, 16)),
        eyes=(["eeeeee", "eWiIie", ".Wppw."], ["eeeeee", "eiIiWe", ".wppW."]),
        brows=(["hhh...", "DhhhhD"], ["...hhh", "DhhhhD"]),
        brow_lift=(0, 0),
        nose=["..S..", "..SS.", "LLSSS", ".n.n."],
        mouth=["m....m", "mTTTTm", ".mmmm."],
        mouth_open=["mTTTTm", "mMMMMm", ".mmmm."],
        blush=3,
    ),
    # Theron: gaunt and long, kind narrowed eyes with crow's feet, a big
    # aquiline nose, mouth half hidden by the beard
    "wise": _Face(
        jaw=((13, 22), (14, 30), (17, 35), (22, 38), (27, 39), (31, 37), (34, 31),
             (35, 24), (35, 16)),
        eyes=(["S.eee.", "SeWiIe", "S.eee."], [".eee.S", "eiIWeS", ".eee.S"]),
        brows=(["hhhhhh", "DhhhhD"], ["hhhhhh", "DhhhhD"]),
        brow_lift=(0, 0),
        nose=["..S..", "..SS.", "..SSS", "..SSS", ".LSSS", "..nS."],
        mouth=[".mmmm."],
        mouth_open=[".mmmm.", ".MMMM.", "..mm.."],
        blush=0,
    ),
    "plain": _Face(
        jaw=((12, 22), (13, 29), (16, 34), (21, 37), (27, 37), (32, 34), (35, 29),
             (36, 22), (36, 16)),
        eyes=([".eee..", "eWiIe.", ".Wpw.."], ["..eee.", ".eiIWe", "..wpW."]),
        brows=([".hhhh.", "......"], [".hhhh.", "......"]),
        brow_lift=(0, 0),
        nose=["..S.", "..S.", ".LSS", "..n."],
        mouth=[".mmmm."],
        mouth_open=[".mmmm.", ".MMMM.", "..mm.."],
    ),
}
_CLOSED_EYE = ["......", "......", "eeeeee", ".SSSS."]


# ── Hair ─────────────────────────────────────────────────────────────────────

def _hair_tones(look: Look) -> tuple[Color, Color, Color, Color]:
    """(deep, shade, base, light) for the hair, with a visible highlight even on dark hair."""
    base = look.hair
    light = shade(base, 0.35) if sum(base) > 200 else lerp(base, (150, 140, 136), 0.45)
    return shade(base, -0.45), shade(base, -0.22), base, light


def _strand(surf: pygame.Surface, color: Color, points: list[tuple[float, float]],
            width: int = 1) -> None:
    pygame.draw.lines(surf, color, False, [(round(x), round(y)) for x, y in points], width)


def _hair_back(surf: pygame.Surface, look: Look) -> None:
    """Hair behind the head: curls framing the face."""
    deep, dark, base, light = _hair_tones(look)
    if look.hair_style == "curly":
        rng = seeded("curls_back", look.hair)
        for _ in range(26):
            a = rng.uniform(math.pi * 0.55, math.pi * 1.45)
            x = _CRANIUM.centerx + math.cos(a) * rng.uniform(11, 15)
            y = _CRANIUM.centery + 3 + math.sin(a) * rng.uniform(11, 16)
            r = rng.randint(3, 4)
            pygame.draw.circle(surf, dark, (round(x), round(y)), r)
            pygame.draw.circle(surf, base, (round(x) - 1, round(y) - 1), r - 1)


def _hair_front(surf: pygame.Surface, look: Look) -> None:
    """The hair on top of the head, per style, lit from the top-left."""
    deep, dark, base, light = _hair_tones(look)
    rng = seeded("hair", look.hair_style, look.hair)
    cx, cy = _CRANIUM.center
    style = look.hair_style
    if style == "elder":
        # Bald crown with a shine; white hair above the ear and round the back
        pygame.draw.ellipse(surf, shade(look.skin, 0.25), (cx - 7, _CRANIUM.top + 3, 8, 4))
        back = [(9, 14), (12, 11), (15, 13), (15, 20), (14, 28), (10, 30), (8, 24)]
        pygame.draw.polygon(surf, base, back)
        far = [(36, 15), (37, 16), (37, 20), (36, 21)]
        pygame.draw.polygon(surf, base, far)
        for i in range(4):
            _strand(surf, light if i % 2 else dark, [(9 + i, 15 + i), (11 + i, 27)])
        return

    cap = [(9, 23), (9, 12), (13, 6), (20, 2), (29, 2), (35, 5), (39, 11), (39, 20)]
    if style == "short":
        # Neat, swept from a side parting over to the left
        fringe = [(39, 20), (37, 15), (33, 12), (28, 12), (23, 13), (18, 15), (14, 18),
                  (12, 21), (10, 23)]
    elif style == "curly":
        fringe = [(40, 20), (37, 17), (34, 14), (31, 16), (28, 13), (25, 16), (21, 14),
                  (18, 17), (14, 17), (12, 21), (10, 24)]
    else:  # tousled: strands falling into the forehead
        fringe = [(39, 20), (37, 15), (35, 18), (32, 13), (29, 17), (26, 13), (23, 17),
                  (20, 13), (17, 17), (14, 15), (12, 20), (10, 23)]
    pygame.draw.polygon(surf, base, cap + fringe)

    if style == "curly":
        # A mop of curls: overlapping rings, each with a lit top-left
        curls = []
        for _ in range(34):
            a = rng.uniform(math.pi * 0.95, math.pi * 2.05)
            d = rng.uniform(4, 15)
            curls.append((cx + math.cos(a) * d * 1.05, cy - 4 + math.sin(a) * d * 0.9,
                          rng.randint(3, 4)))
        for x, y, r in sorted(curls, key=lambda c: c[1]):
            pygame.draw.circle(surf, dark, (round(x), round(y)), r)
            pygame.draw.circle(surf, base, (round(x) - 1, round(y) - 1), r - 1)
            surf.set_at((round(x) - 2, round(y) - 2), light)
        return

    # Strands: dark partings and light sheen following the hair's flow
    for i in range(7):
        x0 = 13 + i * 3.8
        _strand(surf, dark, [(x0, 4 + abs(i - 3)), (x0 + 2, 9), (x0 + 1, 13)])
    for i in range(4):
        x0 = 15 + i * 4.5
        _strand(surf, light, [(x0, 5 + abs(i - 1)), (x0 + 3, 8)], 2 if i == 1 else 1)
    if style == "short":
        _strand(surf, deep, [(31, 3), (33, 7), (34, 12)])       # the parting
    if style == "tousled":
        # Spikes sticking out of the crown, and a cowlick
        for tip in ((12, 3), (18, 0), (25, 0), (32, 1), (38, 7)):
            base_pts = [(tip[0] - 3, tip[1] + 6), (tip[0] + 3, tip[1] + 5)]
            pygame.draw.polygon(surf, base, [tip, *base_pts])
            _strand(surf, light, [(tip[0], tip[1] + 1), (tip[0] - 1, tip[1] + 4)])
        _strand(surf, base, [(26, 3), (29, 0), (31, -1)], 2)
        _strand(surf, light, [(27, 2), (29, 0)])


# ── Bust ─────────────────────────────────────────────────────────────────────

def _bust(surf: pygame.Surface, look: Look, face: _Face) -> None:
    """Shoulders and tunic (exomis bares the left shoulder), neck, head, ear."""
    skin, skin_shade = look.skin, shade(look.skin, -0.18)
    skin_light = shade(look.skin, 0.12)
    tunic, tunic_shade = look.tunic, shade(look.tunic, -0.2)
    trim = look.trim or shade(look.tunic, -0.35)

    shoulders = [(1, 48), (4, 42), (12, 38), (19, 36), (30, 36), (38, 38), (45, 43), (47, 48)]
    pygame.draw.polygon(surf, tunic, shoulders)
    pygame.draw.polygon(surf, tunic_shade, [(30, 36), (38, 38), (45, 43), (47, 48), (33, 48)])
    if look.outfit == "exomis":
        # Bare left shoulder and chest; the cloth runs over the right shoulder
        pygame.draw.polygon(surf, skin, [(1, 48), (4, 42), (12, 38), (19, 36), (25, 37),
                                         (17, 48)])
        pygame.draw.polygon(surf, skin_shade, [(11, 48), (19, 41), (25, 37), (17, 48)])
        pygame.draw.line(surf, tunic_shade, (25, 37), (16, 48), 2)
        pygame.draw.line(surf, skin_light, (5, 42), (12, 39))
    else:
        pygame.draw.polygon(surf, trim, [(19, 36), (30, 36), (27, 41), (22, 41)])
        pygame.draw.polygon(surf, skin, [(20, 36), (29, 36), (26, 39), (23, 39)])
        pygame.draw.line(surf, shade(tunic, 0.15), (5, 42), (12, 39))

    pygame.draw.polygon(surf, skin_shade, _NECK)
    pygame.draw.line(surf, skin, (21, 34), (21, 40), 2)
    pygame.draw.ellipse(surf, skin, _CRANIUM)
    pygame.draw.polygon(surf, skin, face.jaw)
    # Light from the top-left: shade down the right side and under the jaw
    jaw = list(face.jaw)
    pygame.draw.lines(surf, skin_shade, False, jaw[4:], 2)
    pygame.draw.lines(surf, skin_shade, False, jaw[1:5], 1)
    pygame.draw.ellipse(surf, skin_light, (15, 25, 6, 3))        # cheekbone
    pygame.draw.ellipse(surf, skin_light, (18, 8, 12, 5))        # forehead
    pygame.draw.ellipse(surf, skin, _EAR)
    pygame.draw.ellipse(surf, skin_shade, _EAR.inflate(-2, -4).move(1, 0))


def _features(surf: pygame.Surface, look: Look, face: _Face, talking: bool,
              blinking: bool) -> None:
    hair = _hair_tones(look)
    skin_shade = shade(look.skin, -0.2)
    palette = {"e": LASH, "W": EYE_WHITE, "w": lerp(EYE_WHITE, look.skin, 0.4), "i": IRIS,
               "p": PUPIL, "I": EYE_WHITE, "S": skin_shade, "L": shade(look.skin, 0.15),
               "n": shade(look.skin, -0.42), "h": hair[1] if look.face != "wise" else hair[3],
               "D": hair[0] if look.face != "wise" else hair[2], "m": shade(LIPS, -0.25),
               "M": MOUTH, "T": TEETH}
    left_eye, right_eye = (_CLOSED_EYE, _CLOSED_EYE) if blinking else face.eyes
    stamp(surf, left_eye, palette, _NEAR_EYE)
    stamp(surf, right_eye, palette, _FAR_EYE)
    for (x, y), brow, lift in zip((_NEAR_EYE, _FAR_EYE), face.brows, face.brow_lift):
        stamp(surf, brow, palette, (x, y - _BROW_GAP + 1 - lift))
    stamp(surf, face.nose, palette, _NOSE)
    stamp(surf, face.mouth_open if talking else face.mouth, palette, _MOUTH)

    blush = lerp(BLUSH, look.skin, 0.35)
    for x in range(face.blush):
        surf.set_at((15 + x, 28), blush)
        surf.set_at((31 + x, 28), blush)
    if look.freckles:
        for x, y in ((18, 26), (20, 27), (22, 26), (28, 27), (30, 26), (24, 28)):
            surf.set_at((x, y), shade(look.skin, -0.22))
    if look.face == "wise":   # forehead lines and hollow cheeks
        for y in (11, 13):
            pygame.draw.line(surf, skin_shade, (19, y), (29, y - 1))
        pygame.draw.line(surf, skin_shade, (32, 26), (31, 31))
    if look.face == "worried":   # tired shadows under the eyes
        pygame.draw.line(surf, skin_shade, (17, 24), (20, 24))
        pygame.draw.line(surf, skin_shade, (28, 24), (31, 24))
    if look.bearded:
        _, dark, base, light = hair
        beard = [(13, 27), (16, 33), (21, 38), (27, 39), (32, 37), (35, 31), (35, 27),
                 (32, 30), (28, 30), (24, 30), (20, 30), (16, 28)]
        pygame.draw.polygon(surf, base, beard)
        for i in range(7):
            _strand(surf, light if i % 2 else dark, [(15 + i * 3, 30 + i % 2),
                                                     (16 + i * 3, 36 - abs(i - 3))])
        mustache = [(19, 30), (23, 29), (27, 29), (31, 30), (29, 32), (21, 32)]
        pygame.draw.polygon(surf, light, mustache)
        stamp(surf, face.mouth_open if talking else face.mouth, palette, (_MOUTH[0], 32))


def _accessories(surf: pygame.Surface, look: Look) -> None:
    if look.headband:
        band, band_shade = look.headband, shade(look.headband, -0.25)
        pygame.draw.line(surf, band, (10, 16), (38, 13), 3)
        pygame.draw.line(surf, band_shade, (10, 18), (38, 15))
        pygame.draw.line(surf, shade(band, 0.2), (13, 15), (28, 13))
        # Knot and tails behind the ear
        pygame.draw.circle(surf, band, (10, 17), 2)
        pygame.draw.line(surf, band_shade, (9, 18), (6, 24), 2)
        pygame.draw.line(surf, band, (10, 18), (8, 25))
    if look.charm:
        cord = (70, 48, 32)
        pygame.draw.lines(surf, cord, False, [(19, 36), (23, 43), (28, 36)])
        pygame.draw.ellipse(surf, (176, 136, 82), (21, 42, 4, 5))
        surf.set_at((22, 43), (214, 180, 120))


@cached
def portrait(look: Look, talking: bool = False, blinking: bool = False,
             factor: int = PORTRAIT_SCALE) -> pygame.Surface:
    """Bust of a character for the dialogue box, scaled by ``factor``."""
    face = _FACES.get(look.face, _FACES["plain"])
    surf = pygame.Surface((PORTRAIT_SIZE, PORTRAIT_SIZE), pygame.SRCALPHA)
    _hair_back(surf, look)
    _bust(surf, look, face)
    _features(surf, look, face, talking, blinking)
    _hair_front(surf, look)
    _accessories(surf, look)
    # A dark outline around the whole silhouette, kept off the bottom edge
    mask = pygame.mask.from_surface(surf)
    edge = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    sil = mask.to_surface(setcolor=OUTLINE, unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((-1, 0), (1, 0), (0, -1)):
        edge.blit(sil, (dx, dy))
    edge.blit(surf, (0, 0))
    return scale(edge, factor)
