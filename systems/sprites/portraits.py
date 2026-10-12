"""Dialogue portraits: a 48×48 head-and-shoulders bust in 3/4 view.

Busts face right, toward the dialogue text, and are drawn at a finer pixel
size than the map (2× instead of 3×) so faces can carry expression. The
head, hair and clothes are shapes colored by the character's ``Look``; the
eyes, brows and mouth come from small hand-drawn grids chosen by
``Look.face``. Frames: ``talking`` opens the mouth, ``blinking`` closes the
eyes.
"""

from __future__ import annotations

import math

import pygame

from systems.sprites.characters import Look
from systems.sprites.pixel_art import Color, cached, lerp, scale, seeded, shade, stamp

PORTRAIT_SIZE = 48
PORTRAIT_SCALE = 2

OUTLINE = (40, 28, 24)
EYE_WHITE = (246, 240, 230)
IRIS = (78, 52, 34)
LASH = (44, 30, 26)
LIPS = (176, 98, 86)
MOUTH = (96, 40, 42)
TEETH = (246, 240, 230)
BLUSH = (226, 128, 112)

# Head geometry (logical pixels), facing right
_CRANIUM = pygame.Rect(11, 5, 27, 27)
_JAW = [(14, 21), (17, 29), (22, 34), (28, 37), (33, 36), (36, 33), (37, 31),
        (38, 29), (38, 28), (41, 26), (39, 22), (38, 19), (37, 14)]
_NECK = [(20, 31), (31, 33), (31, 42), (19, 42)]
_EAR = pygame.Rect(15, 20, 6, 8)
_NEAR_EYE = (23, 20)          # top-left of the near (screen-left) eye grid
_FAR_EYE = (32, 20)
_MOUTH_AT = (28, 30)

# ── Faces: eyes, brows and mouths per expression ─────────────────────────────
# Grids: e lash, w white, i iris, I glint, s skin (lid), S shade, m lip line,
# M open mouth, T teeth, h brow (hair color), D brow shadow

_EYES = {
    "near": [".eeee.",
             "ewiiIw",
             "ewiiiw",
             ".wwiw.",
             "..SS.."],
    "far": ["eeee",
            "wiIe",
            "wiie",
            ".wS."],
    "near_closed": ["......",
                    "......",
                    "eeeeee",
                    ".SSSS.",
                    "......"],
    "far_closed": ["....",
                   "....",
                   "eeee",
                   ".SS."],
}

# face → (near brow, far brow, brow offsets (dy near, dy far), mouth closed, mouth open)
_FACES: dict[str, tuple] = {
    "plain": (["hhhhh.", ".hhhhh"], ["hhhh", "Dhhh"], (0, 0),
              ["mmmmmm"], ["mmmmmm", ".MMMM.", "..mm.."]),
    "cheeky": (["..hhhh", "hhD..."], ["hhhh", "Dh.."], (-2, 0),
               [".....m", "mmmmm.", "..SS.."], ["....mm", "mMMMMm", ".MTTM.", "..mm.."]),
    "bold": (["hhh...", "DhhhhD"], ["hhhh", "hhhD"], (1, 1),
             ["m....m", ".mmmm."], ["mTTTTm", "mMMMMm", ".mmmm."]),
    "worried": (["....hh", ".hhhD."], ["hh..", "Dhhh"], (-1, -1),
                [".mmm..", "m...m."], [".mmm..", "mMMMm.", ".mmm.."]),
    "wise": (["hhhhhh", "DhhhhD"], ["hhhh", "hhhh"], (1, 1),
             ["mmmmm."], ["mmmmm.", ".MMM..", "..m..."]),
}


def _face_rows(look: Look, talking: bool) -> tuple:
    near_brow, far_brow, (dy_near, dy_far), closed, opened = _FACES.get(look.face,
                                                                        _FACES["plain"])
    return near_brow, far_brow, dy_near, dy_far, opened if talking else closed


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
    """Hair behind the head: curls framing the face, the elder's fringe of white."""
    deep, dark, base, light = _hair_tones(look)
    if look.hair_style == "curly":
        rng = seeded("curls_back", look.hair)
        for _ in range(26):
            a = rng.uniform(math.pi * 0.55, math.pi * 1.6)
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
        # Bald crown with a shine; white hair from the ear round the back
        pygame.draw.ellipse(surf, light, (cx - 6, _CRANIUM.top + 3, 7, 4))
        back = [(11, 15), (14, 12), (17, 14), (19, 21), (20, 28), (16, 31), (11, 26)]
        pygame.draw.polygon(surf, base, back)
        for i in range(5):
            _strand(surf, light if i % 2 else dark, [(12 + i, 15 + i), (14 + i, 28)])
        return

    # Common cap: covers the cranium top and back, hairline across the forehead
    cap = [(10, 20), (10, 12), (14, 6), (21, 3), (29, 3), (35, 6), (39, 12), (39, 16)]
    if style == "short":
        fringe = [(39, 16), (36, 15), (31, 13), (26, 14), (22, 17), (20, 21), (17, 22),
                  (14, 26), (11, 25)]
    elif style == "curly":
        fringe = [(40, 17), (37, 17), (34, 15), (31, 17), (28, 15), (25, 18), (21, 17),
                  (19, 22), (16, 25), (11, 27)]
    else:  # tousled
        fringe = [(39, 17), (37, 15), (35, 19), (33, 14), (30, 18), (28, 13), (25, 17),
                  (22, 15), (20, 21), (17, 22), (14, 26), (11, 24)]
    pygame.draw.polygon(surf, base, cap + fringe)

    if style == "curly":
        # A mop of curls: overlapping rings, each with a lit top-left
        curls = []
        for _ in range(34):
            a = rng.uniform(math.pi * 0.95, math.pi * 2.05)
            d = rng.uniform(4, 15)
            curls.append((cx + math.cos(a) * d * 1.05, cy - 3 + math.sin(a) * d * 0.9,
                          rng.randint(3, 4)))
        for x, y, r in sorted(curls, key=lambda c: c[1]):
            pygame.draw.circle(surf, dark, (round(x), round(y)), r)
            pygame.draw.circle(surf, base, (round(x) - 1, round(y) - 1), r - 1)
            surf.set_at((round(x) - 2, round(y) - 2), light)
        return

    # Strands: dark partings and light sheen following the hair flow
    for i in range(7):
        x0 = 15 + i * 3.5
        _strand(surf, dark, [(x0, 5 + abs(i - 3)), (x0 + 3, 11), (x0 + 1, 16)])
    for i in range(4):
        x0 = 17 + i * 4
        _strand(surf, light, [(x0, 6 + abs(i - 1)), (x0 + 3, 9)], 2 if i == 1 else 1)
    if style == "tousled":
        # Spikes sticking out of the crown, and a cowlick
        for tip in ((14, 3), (20, 0), (26, 1), (33, 2), (38, 7)):
            base_pts = [(tip[0] - 3, tip[1] + 6), (tip[0] + 3, tip[1] + 5)]
            pygame.draw.polygon(surf, base, [tip, *base_pts])
            _strand(surf, light, [(tip[0], tip[1] + 1), (tip[0] - 1, tip[1] + 4)])
        _strand(surf, base, [(28, 3), (31, 0), (33, -1)], 2)
        _strand(surf, light, [(29, 2), (31, 0)])


# ── Bust ─────────────────────────────────────────────────────────────────────

def _bust(surf: pygame.Surface, look: Look) -> None:
    """Shoulders and tunic (exomis bares the near shoulder), neck, head, ear."""
    skin, skin_shade = look.skin, shade(look.skin, -0.18)
    skin_light = shade(look.skin, 0.12)
    tunic, tunic_shade = look.tunic, shade(look.tunic, -0.2)
    trim = look.trim or shade(look.tunic, -0.35)

    shoulders = [(2, 48), (5, 42), (13, 38), (21, 36), (31, 36), (40, 39), (46, 44), (47, 48)]
    pygame.draw.polygon(surf, tunic, shoulders)
    pygame.draw.polygon(surf, tunic_shade, [(31, 36), (40, 39), (46, 44), (47, 48), (34, 48)])
    if look.outfit == "exomis":
        # Bare near shoulder and chest; the cloth crosses from the far shoulder
        pygame.draw.polygon(surf, skin, [(2, 48), (5, 42), (13, 38), (21, 36), (26, 37),
                                         (18, 48)])
        pygame.draw.polygon(surf, skin_shade, [(12, 48), (20, 41), (26, 37), (18, 48)])
        pygame.draw.line(surf, tunic_shade, (26, 37), (17, 48), 2)
        pygame.draw.line(surf, skin_light, (6, 42), (13, 39))
    else:
        pygame.draw.polygon(surf, trim, [(21, 36), (31, 36), (28, 41), (24, 41)])
        pygame.draw.polygon(surf, skin, [(22, 36), (30, 36), (27, 39), (25, 39)])
    pygame.draw.line(surf, shade(tunic, 0.15), (6, 42), (13, 39))

    pygame.draw.polygon(surf, skin_shade, _NECK)
    pygame.draw.line(surf, skin, (28, 34), (28, 40), 2)
    pygame.draw.ellipse(surf, skin, _CRANIUM)
    pygame.draw.polygon(surf, skin, _JAW)
    # Shading: jaw and neck in shadow, cheekbone and forehead catching light
    pygame.draw.lines(surf, skin_shade, False, [(17, 29), (22, 34), (28, 37), (33, 36)], 2)
    pygame.draw.ellipse(surf, skin_light, (27, 22, 7, 4))
    pygame.draw.ellipse(surf, skin_light, (24, 9, 10, 5))
    pygame.draw.ellipse(surf, skin, _EAR)
    pygame.draw.ellipse(surf, skin_shade, _EAR.inflate(-3, -3).move(1, 0))


def _features(surf: pygame.Surface, look: Look, talking: bool, blinking: bool) -> None:
    near_brow, far_brow, dy_near, dy_far, mouth = _face_rows(look, talking)
    hair = _hair_tones(look)
    skin_shade = shade(look.skin, -0.18)
    palette = {"e": LASH, "w": EYE_WHITE, "i": IRIS, "I": EYE_WHITE, "S": skin_shade,
               "s": look.skin, "h": hair[1], "D": hair[0], "m": shade(LIPS, -0.25),
               "M": MOUTH, "T": TEETH}
    near = _EYES["near_closed" if blinking else "near"]
    far = _EYES["far_closed" if blinking else "far"]
    stamp(surf, near, palette, _NEAR_EYE)
    stamp(surf, far, palette, _FAR_EYE)
    stamp(surf, near_brow, palette, (_NEAR_EYE[0], _NEAR_EYE[1] - 4 + dy_near))
    stamp(surf, far_brow, palette, (_FAR_EYE[0], _FAR_EYE[1] - 4 + dy_far))
    # Nose: a shadow under the tip, a lit bridge
    for x, y in ((39, 27), (38, 28), (37, 28)):
        surf.set_at((x, y), skin_shade)
    surf.set_at((37, 23), shade(look.skin, 0.12))
    stamp(surf, mouth, palette, _MOUTH_AT)
    if look.face != "wise":
        surf.set_at((26, 28), BLUSH)
        surf.set_at((27, 28), lerp(BLUSH, look.skin, 0.5))
    if look.freckles:
        for x, y in ((29, 26), (31, 27), (33, 26), (27, 26), (35, 27)):
            surf.set_at((x, y), shade(look.skin, -0.2))
    if look.bearded:
        _, dark, base, light = hair
        beard = [(17, 29), (22, 34), (28, 38), (34, 37), (37, 33), (37, 31), (33, 33),
                 (28, 33), (24, 30), (20, 26)]
        pygame.draw.polygon(surf, base, beard)
        for i in range(6):
            _strand(surf, light if i % 2 else dark, [(20 + i * 3, 29 + i // 2),
                                                     (21 + i * 3, 35 + i // 3)])
        stamp(surf, mouth, palette, _MOUTH_AT)


def _accessories(surf: pygame.Surface, look: Look) -> None:
    if look.headband:
        band, band_shade = look.headband, shade(look.headband, -0.25)
        pygame.draw.line(surf, band, (11, 17), (39, 13), 3)
        pygame.draw.line(surf, band_shade, (11, 19), (39, 15))
        pygame.draw.line(surf, shade(band, 0.2), (14, 16), (30, 13))
        # Knot and tails behind the ear
        pygame.draw.circle(surf, band, (11, 18), 2)
        pygame.draw.line(surf, band_shade, (10, 19), (7, 25), 2)
        pygame.draw.line(surf, band, (11, 19), (9, 26))
    if look.charm:
        cord = (70, 48, 32)
        pygame.draw.lines(surf, cord, False, [(21, 37), (25, 43), (29, 37)])
        pygame.draw.ellipse(surf, (176, 136, 82), (23, 42, 4, 5))
        surf.set_at((24, 43), (214, 180, 120))


@cached
def portrait(look: Look, talking: bool = False, blinking: bool = False,
             factor: int = PORTRAIT_SCALE) -> pygame.Surface:
    """Bust of a character for the dialogue box, scaled by ``factor``."""
    surf = pygame.Surface((PORTRAIT_SIZE, PORTRAIT_SIZE), pygame.SRCALPHA)
    _hair_back(surf, look)
    _bust(surf, look)
    _features(surf, look, talking, blinking)
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
