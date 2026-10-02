"""Full-screen backdrops, drawn at low resolution for a chunky pixel look."""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites.pixel_art import cached, scale, seeded, shade

_BACKDROP_SCALE = 4


@cached
def combat_backdrop(player_pos: tuple[int, int], enemy_pos: tuple[int, int]) -> pygame.Surface:
    """Dusk sky, distant hills and grass platforms under each combatant.

    Positions are the screen-space feet of each combatant.
    """
    w, h = s.SCREEN_WIDTH // _BACKDROP_SCALE, s.SCREEN_HEIGHT // _BACKDROP_SCALE
    surf = pygame.Surface((w, h))
    horizon = int(h * 0.42)
    rng = seeded("combat_backdrop")

    # Banded dusk sky (bands instead of a smooth gradient = pixel-art look)
    top, bottom = s.COLOR_COMBAT_BG, (150, 92, 98)
    bands = 8
    for i in range(bands):
        t = i / (bands - 1)
        color = tuple(int(a + (b - a) * t) for a, b in zip(top, bottom))
        y0 = horizon * i // bands
        pygame.draw.rect(surf, color, (0, y0, w, horizon // bands + 1))
    for _ in range(18):
        surf.set_at((rng.randrange(w), rng.randrange(horizon // 2)), (200, 196, 210))

    # Two layers of hills
    for layer, (color, base, amp) in enumerate((((62, 66, 84), horizon - 6, 8),
                                                ((48, 62, 52), horizon, 5))):
        pts = [(0, h)]
        x = 0
        while x <= w:
            pts.append((x, base - rng.randrange(amp)))
            x += rng.randrange(6, 14)
        pts += [(w, base), (w, h)]
        pygame.draw.polygon(surf, color, pts)

    # Ground
    ground = (74, 96, 56)
    pygame.draw.rect(surf, ground, (0, horizon, w, h - horizon))
    for _ in range(140):
        x, y = rng.randrange(w), rng.randrange(horizon + 1, h)
        surf.set_at((x, y), shade(ground, rng.choice((-0.15, 0.12))))

    # Platforms
    for (fx, fy), pw in ((player_pos, 46), (enemy_pos, 40)):
        cx, cy = fx // _BACKDROP_SCALE, fy // _BACKDROP_SCALE
        rect = pygame.Rect(0, 0, pw, pw // 4)
        rect.center = (cx, cy)
        pygame.draw.ellipse(surf, (52, 70, 40), rect.move(0, 1))
        pygame.draw.ellipse(surf, (108, 142, 78), rect)
        pygame.draw.ellipse(surf, (128, 162, 92), rect.inflate(-pw // 3, -pw // 10).move(0, -1))
    return scale(surf, _BACKDROP_SCALE)
