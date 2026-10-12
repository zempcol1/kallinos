"""Full-screen backdrops, drawn at low resolution for a chunky pixel look."""

from __future__ import annotations

import math

import pygame

import settings as s
from systems.sprites.pixel_art import cached, lerp, scale, seeded, shade

_BACKDROP_SCALE = 4

# Late afternoon in the garden: warm light from the upper left
_SKY = [(118, 160, 196), (150, 178, 196), (192, 192, 180), (230, 206, 160), (246, 216, 150)]
_SUN = (255, 244, 206)
_HILLS_FAR = (138, 150, 150)
_HILLS_NEAR = (112, 126, 92)
_TREE = (78, 98, 66)
_TREE_DARK = (58, 76, 54)
_CYPRESS = (52, 74, 56)
_GRASS = (118, 134, 70)
_GRASS_DARK = (98, 112, 58)
_GRASS_LIGHT = (146, 156, 88)
_EARTH = (176, 150, 106)
_EARTH_DARK = (150, 124, 86)
_EARTH_LIGHT = (198, 174, 128)
_FENCE = (186, 160, 118)
_FENCE_DARK = (132, 108, 76)


def _olive_silhouette(surf: pygame.Surface, x: int, base: int, size: int, rng) -> None:
    """A distant olive: a short trunk under a round, lumpy crown."""
    pygame.draw.line(surf, _TREE_DARK, (x, base), (x + rng.choice((-1, 1)), base - size // 2), 2)
    for dx, dy in ((-size // 3, -size // 2), (size // 3, -size // 2), (0, -size + 1)):
        r = size // 3 + 1
        pygame.draw.circle(surf, _TREE_DARK, (x + dx, base + dy + 1), r)
        pygame.draw.circle(surf, _TREE, (x + dx, base + dy), r)
    surf.set_at((x - size // 3, base - size + 1), shade(_TREE, 0.25))


@cached
def combat_backdrop(player_pos: tuple[int, int], enemy_pos: tuple[int, int]) -> pygame.Surface:
    """The garden at golden hour: hills, olive groves, the fence, grass and earth.

    Positions are the screen-space feet of each combatant.
    """
    w, h = s.SCREEN_WIDTH // _BACKDROP_SCALE, s.SCREEN_HEIGHT // _BACKDROP_SCALE
    surf = pygame.Surface((w, h))
    horizon = int(h * 0.42)
    rng = seeded("garden_backdrop")

    # Banded sky with dithered seams, and the low sun's glow at the upper left
    for i, color in enumerate(_SKY):
        y0, y1 = horizon * i // len(_SKY), horizon * (i + 1) // len(_SKY)
        pygame.draw.rect(surf, color, (0, y0, w, y1 - y0))
        if i:
            for x in range(y0 % 2, w, 2):
                surf.set_at((x, y0), _SKY[i - 1])
    for r, t in ((22, 0.25), (15, 0.45), (9, 1.0)):
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*_SUN, int(255 * t)), (r, r), r)
        surf.blit(glow, (24 - r, 18 - r))
    for _ in range(3):   # thin clouds
        x, y = rng.randrange(40, w - 40), rng.randrange(8, horizon // 2)
        length = rng.randint(16, 34)
        pygame.draw.line(surf, lerp(_SKY[2], (255, 255, 255), 0.4), (x, y), (x + length, y))
        pygame.draw.line(surf, lerp(_SKY[3], (255, 255, 255), 0.2), (x + 4, y + 1),
                         (x + length - 6, y + 1))

    # Two layers of hills; the near one carries olive groves and cypresses
    for color, base, amp, step in ((_HILLS_FAR, horizon - 8, 9, 9), (_HILLS_NEAR, horizon, 6, 6)):
        pts = [(0, h)]
        for x in range(0, w + step, step):
            pts.append((x, base - round(abs(math.sin(x * 0.03 + base)) * amp) - rng.randint(0, 2)))
        pts += [(w, h)]
        pygame.draw.polygon(surf, color, pts)
    for x in range(6, w, 11):
        if rng.random() < 0.7:
            _olive_silhouette(surf, x + rng.randint(-3, 3), horizon + rng.randint(1, 4),
                              rng.randint(6, 9), rng)
        else:
            top = horizon - rng.randint(10, 15)
            pygame.draw.polygon(surf, _CYPRESS, [(x, top), (x - 2, horizon + 2),
                                                 (x + 2, horizon + 2)])

    # Ground: olive grass with tufts, darker toward the viewer
    bands = [_GRASS_LIGHT, _GRASS, shade(_GRASS, -0.06), shade(_GRASS, -0.12)]
    top = horizon + 4
    for i, color in enumerate(bands):
        y0 = top + (h - top) * i // len(bands)
        y1 = top + (h - top) * (i + 1) // len(bands)
        pygame.draw.rect(surf, color, (0, y0, w, y1 - y0))
        if i:   # dithered seam instead of a hard line
            for x in range(y0 % 2, w, 2):
                surf.set_at((x, y0), bands[i - 1])
    for _ in range(220):
        x, y = rng.randrange(w), rng.randrange(horizon + 5, h)
        surf.set_at((x, y), rng.choice((_GRASS_DARK, _GRASS_LIGHT, _GRASS_DARK)))
    # The garden fence running behind the arena
    rail_y = horizon + 3
    pygame.draw.line(surf, _FENCE, (0, rail_y), (w, rail_y))
    pygame.draw.line(surf, _FENCE_DARK, (0, rail_y + 2), (w, rail_y + 2))
    for x in range(3, w, 12):
        pygame.draw.line(surf, _FENCE_DARK, (x + 1, rail_y - 3), (x + 1, rail_y + 4))
        pygame.draw.line(surf, _FENCE, (x, rail_y - 3), (x, rail_y + 4))

    # Bare earth under each combatant, ringed by grass
    for (fx, fy), pw in ((player_pos, 50), (enemy_pos, 44)):
        cx, cy = fx // _BACKDROP_SCALE, fy // _BACKDROP_SCALE
        rect = pygame.Rect(0, 0, pw, pw // 4)
        rect.center = (cx, cy)
        pygame.draw.ellipse(surf, _GRASS_DARK, rect.inflate(6, 3).move(0, 1))
        pygame.draw.ellipse(surf, _EARTH_DARK, rect.move(0, 1))
        pygame.draw.ellipse(surf, _EARTH, rect)
        pygame.draw.ellipse(surf, _EARTH_LIGHT, rect.inflate(-pw // 2, -pw // 10).move(-3, -1))
        for _ in range(pw // 3):
            x = rng.randrange(rect.left + 3, rect.right - 3)
            y = rng.randrange(rect.top + 1, rect.bottom - 1)
            surf.set_at((x, y), rng.choice((_EARTH_DARK, _EARTH_LIGHT)))
    return scale(surf, _BACKDROP_SCALE)
