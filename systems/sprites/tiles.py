"""Ground tiles (16×16). Map objects live in structures.py and nature.py."""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites.pixel_art import cached, scale, seeded, speckle

T = s.TILE_SIZE

# ── Palette ──────────────────────────────────────────────────────────────────
GRASS = (107, 142, 78)
GRASS_DARK = (86, 121, 62)
GRASS_LIGHT = (128, 162, 92)
DIRT = (214, 190, 142)
DIRT_DARK = (189, 164, 117)
DIRT_LIGHT = (231, 211, 168)
PEBBLE = (160, 142, 108)


# ── Ground tiles (16×16) ─────────────────────────────────────────────────────

def _grass_base(variant: int) -> pygame.Surface:
    surf = pygame.Surface((T, T))
    surf.fill(GRASS)
    rng = seeded("grass", variant)
    # Small "v" shaped blades
    for _ in range(6):
        x, y = rng.randrange(1, T - 1), rng.randrange(1, T - 1)
        surf.set_at((x - 1, y), GRASS_DARK)
        surf.set_at((x + 1, y), GRASS_DARK)
        surf.set_at((x, y + 1), GRASS_DARK)
    speckle(surf, rng, GRASS_LIGHT, 5)
    return surf


@cached
def grass(variant: int = 0) -> pygame.Surface:
    """Grass with a few texture variants; variant 3 has wildflowers."""
    surf = _grass_base(variant)
    if variant == 3:
        rng = seeded("flowers", variant)
        for color in ((242, 236, 220), (240, 200, 70), (200, 110, 150)):
            x, y = rng.randrange(2, T - 2), rng.randrange(2, T - 2)
            surf.set_at((x, y), color)
            surf.set_at((x, y + 1), GRASS_DARK)
    return scale(surf)


@cached
def dirt_path(edges: tuple[bool, bool, bool, bool] = (False,) * 4) -> pygame.Surface:
    """Packed-earth path. ``edges`` = (top, right, bottom, left) grass borders."""
    surf = pygame.Surface((T, T))
    surf.fill(DIRT)
    rng = seeded("dirt", edges)
    speckle(surf, rng, DIRT_DARK, 10)
    speckle(surf, rng, DIRT_LIGHT, 8)
    for _ in range(2):
        x, y = rng.randrange(2, T - 3), rng.randrange(2, T - 3)
        pygame.draw.rect(surf, PEBBLE, (x, y, 2, 1))
        surf.set_at((x, y + 1), DIRT_DARK)

    # Ragged grass fringe along edges that border grass
    top, right, bottom, left = edges
    for i in range(T):
        depth = 1 + (rng.random() < 0.45)
        if top:
            pygame.draw.line(surf, GRASS, (i, 0), (i, depth - 1))
            surf.set_at((i, depth), DIRT_DARK)
        if bottom:
            pygame.draw.line(surf, GRASS, (i, T - depth), (i, T - 1))
        if left:
            pygame.draw.line(surf, GRASS, (0, i), (depth - 1, i))
            surf.set_at((depth, i), DIRT_DARK)
        if right:
            pygame.draw.line(surf, GRASS, (T - depth, i), (T - 1, i))
    return scale(surf)


@cached
def missing_tile() -> pygame.Surface:
    """Loud magenta checkerboard for unknown tile IDs."""
    surf = pygame.Surface((T, T))
    surf.fill((255, 0, 255))
    pygame.draw.rect(surf, (0, 0, 0), (0, 0, T // 2, T // 2))
    pygame.draw.rect(surf, (0, 0, 0), (T // 2, T // 2, T // 2, T // 2))
    return scale(surf)
