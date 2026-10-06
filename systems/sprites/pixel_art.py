"""Low-level helpers for building pixel art at logical (unscaled) resolution.

Sprites are authored either as text grids (one character per pixel, mapped
through a palette) or procedurally with a seeded RNG, then scaled up by
``settings.SCALE`` for rendering.
"""

from __future__ import annotations

import functools
import random
from collections.abc import Callable, Sequence

import pygame

import settings as s

Color = tuple[int, int, int] | tuple[int, int, int, int]
Palette = dict[str, Color]

TRANSPARENT = "."

_cached_functions: list[functools._lru_cache_wrapper] = []


def cached(func: Callable) -> Callable:
    """Memoize a sprite generator so each sprite is only drawn once."""
    wrapper = functools.cache(func)
    _cached_functions.append(wrapper)
    return wrapper


def clear_cache() -> None:
    """Drop every cached sprite (e.g. after changing SCALE)."""
    for func in _cached_functions:
        func.cache_clear()


def from_grid(rows: Sequence[str], palette: Palette) -> pygame.Surface:
    """Build a surface from text rows; '.' is transparent."""
    width = len(rows[0])
    surf = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"Grid row {y} is {len(row)} wide, expected {width}: {row!r}")
        for x, ch in enumerate(row):
            if ch != TRANSPARENT:
                surf.set_at((x, y), palette[ch])
    return surf


def mirrored(half_rows: Sequence[str]) -> list[str]:
    """Complete a left-right symmetric grid from its left half."""
    return [row + row[::-1] for row in half_rows]


def scale(surf: pygame.Surface, factor: int = s.SCALE) -> pygame.Surface:
    """Scale a logical surface up by an integer factor (nearest neighbour)."""
    w, h = surf.get_size()
    result = pygame.transform.scale(surf, (w * factor, h * factor))
    if pygame.display.get_surface() is not None:
        result = result.convert_alpha()
    return result


def shade(color: Color, amount: float) -> tuple[int, int, int]:
    """Lighten (amount > 0) or darken (amount < 0) a color by a 0–1 fraction."""
    target = 255 if amount > 0 else 0
    t = abs(amount)
    return tuple(int(c + (target - c) * t) for c in color[:3])


def lerp(a: Color, b: Color, t: float) -> tuple[int, int, int]:
    """Blend two colors; ``t`` = 0 gives ``a``, 1 gives ``b``."""
    return tuple(int(x + (y - x) * t) for x, y in zip(a[:3], b[:3]))


def stamp(surf: pygame.Surface, rows: Sequence[str], palette: Palette,
          pos: tuple[int, int]) -> None:
    """Draw a small text grid (a leaf, a flower...) onto a surface at ``pos``."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != TRANSPARENT:
                px, py = pos[0] + x, pos[1] + y
                if 0 <= px < surf.get_width() and 0 <= py < surf.get_height():
                    surf.set_at((px, py), palette[ch])


def silhouette(surf: pygame.Surface, color: Color) -> pygame.Surface:
    """A same-size surface with every opaque pixel filled with one color."""
    mask = pygame.mask.from_surface(surf)
    return mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))


def outline(surf: pygame.Surface, color: Color) -> pygame.Surface:
    """Draw a 1px outline around opaque pixels, inside the surface bounds."""
    sil = silhouette(surf, color)
    result = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        result.blit(sil, (dx, dy))
    result.blit(surf, (0, 0))
    return result


def speckle(surf: pygame.Surface, rng: random.Random, color: Color, count: int,
            area: pygame.Rect | None = None) -> None:
    """Scatter single pixels of one color at random positions."""
    area = area or surf.get_rect()
    for _ in range(count):
        surf.set_at((rng.randrange(area.left, area.right),
                     rng.randrange(area.top, area.bottom)), color)


def seeded(*parts: object) -> random.Random:
    """A deterministic RNG so procedural sprites look the same every run."""
    return random.Random("|".join(str(p) for p in parts))
