"""Ground tiles (16×16): grass, footpath, dry earth.

Map objects live in structures.py and nature.py.
"""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites.pixel_art import cached, scale, seeded, speckle

T = s.TILE_SIZE

# ── Palette ──────────────────────────────────────────────────────────────────
# Late-summer Greece: olive-tinted grass, sun-dried straw, ochre earth
GRASS = (118, 134, 70)
GRASS_DARK = (96, 112, 58)
GRASS_LIGHT = (142, 154, 86)
STRAW = (176, 164, 100)
DIRT = (208, 184, 136)
DIRT_DARK = (184, 158, 112)
DIRT_LIGHT = (226, 206, 160)
EARTH = (176, 150, 106)
EARTH_DARK = (150, 124, 86)
EARTH_LIGHT = (196, 172, 126)
PEBBLE = (160, 142, 108)
PEBBLE_LIGHT = (204, 192, 166)
FLOWERS = ((242, 236, 220), (240, 200, 70), (200, 110, 150), (170, 140, 210))

Edges = tuple[bool, bool, bool, bool]   # (top, right, bottom, left) borders grass


# ── Ground tiles (16×16) ─────────────────────────────────────────────────────

@cached
def grass(variant: int = 0) -> pygame.Surface:
    """Olive-tinted grass. Variants: 0–2 plain, 3 wildflowers, 4 dry with a bare spot."""
    surf = pygame.Surface((T, T))
    surf.fill(GRASS)
    rng = seeded("grass", variant)
    if variant == 4:
        spot = pygame.Rect(rng.randrange(2, 7), rng.randrange(3, 8), rng.randint(5, 8), 4)
        pygame.draw.ellipse(surf, EARTH, spot)
        speckle(surf, rng, EARTH_DARK, 4, spot.inflate(-2, -1))
    # Small "v" shaped blades, a few straw-dry ones
    for _ in range(6):
        x, y = rng.randrange(1, T - 1), rng.randrange(1, T - 1)
        color = STRAW if rng.random() < 0.2 else GRASS_DARK
        surf.set_at((x - 1, y), color)
        surf.set_at((x + 1, y), color)
        surf.set_at((x, y + 1), GRASS_DARK)
    speckle(surf, rng, GRASS_LIGHT, 5)
    if variant == 3:
        for color in rng.sample(FLOWERS, 3):
            x, y = rng.randrange(2, T - 2), rng.randrange(2, T - 2)
            surf.set_at((x, y), color)
            surf.set_at((x, y + 1), GRASS_DARK)
    return scale(surf)


def _fringe(surf: pygame.Surface, rng, edges: Edges, shadow: tuple) -> None:
    """Ragged grass along the sides that border grass, with a darker lip."""
    top, right, bottom, left = edges
    for i in range(T):
        depth = 1 + (rng.random() < 0.45) + (rng.random() < 0.15)
        if top:
            pygame.draw.line(surf, GRASS, (i, 0), (i, depth - 1))
            surf.set_at((i, depth), shadow)
        if bottom:
            pygame.draw.line(surf, GRASS, (i, T - depth), (i, T - 1))
        if left:
            pygame.draw.line(surf, GRASS, (0, i), (depth - 1, i))
            surf.set_at((depth, i), shadow)
        if right:
            pygame.draw.line(surf, GRASS, (T - depth, i), (T - 1, i))


@cached
def dirt_path(edges: Edges = (False,) * 4) -> pygame.Surface:
    """Packed, sun-bleached footpath."""
    surf = pygame.Surface((T, T))
    surf.fill(DIRT)
    rng = seeded("dirt", edges)
    speckle(surf, rng, DIRT_DARK, 10)
    speckle(surf, rng, DIRT_LIGHT, 8)
    for _ in range(2):
        x, y = rng.randrange(2, T - 3), rng.randrange(2, T - 3)
        pygame.draw.rect(surf, PEBBLE, (x, y, 2, 1))
        surf.set_at((x, y + 1), DIRT_DARK)
    _fringe(surf, rng, edges, DIRT_DARK)
    return scale(surf)


@cached
def earth(edges: Edges = (False,) * 4, variant: int = 0) -> pygame.Surface:
    """Dry ochre earth with pebbles and a few stubborn grass tufts."""
    surf = pygame.Surface((T, T))
    surf.fill(EARTH)
    rng = seeded("earth", edges, variant)
    speckle(surf, rng, EARTH_DARK, 14)
    speckle(surf, rng, EARTH_LIGHT, 10)
    for _ in range(rng.randint(1, 3)):
        x, y = rng.randrange(1, T - 2), rng.randrange(1, T - 2)
        surf.set_at((x, y), PEBBLE_LIGHT)
        surf.set_at((x + 1, y), PEBBLE)
        surf.set_at((x, y + 1), EARTH_DARK)
    for _ in range(rng.randint(0, 2)):   # sparse tufts
        x, y = rng.randrange(2, T - 2), rng.randrange(2, T - 2)
        surf.set_at((x - 1, y), GRASS)
        surf.set_at((x + 1, y), STRAW)
        surf.set_at((x, y + 1), GRASS_DARK)
    _fringe(surf, rng, edges, EARTH_DARK)
    return scale(surf)


@cached
def missing_tile() -> pygame.Surface:
    """Loud magenta checkerboard for unknown tile IDs."""
    surf = pygame.Surface((T, T))
    surf.fill((255, 0, 255))
    pygame.draw.rect(surf, (0, 0, 0), (0, 0, T // 2, T // 2))
    pygame.draw.rect(surf, (0, 0, 0), (T // 2, T // 2, T // 2, T // 2))
    return scale(surf)
