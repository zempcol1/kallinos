"""Enemy sprites. Each enemy id in enemies.json maps to a generator here."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from systems.sprites.pixel_art import cached, from_grid, mirrored, scale

# ── Vátrachos (24×18, front-facing) ──────────────────────────────────────────

_VATRACHOS_PALETTE = {
    "o": (24, 38, 20),
    "g": (72, 118, 50),
    "G": (48, 86, 36),
    "L": (112, 158, 72),
    "w": (92, 134, 58),
    "m": (30, 50, 26),
    "b": (196, 196, 128),
    "B": (160, 160, 98),
    "y": (232, 176, 48),
    "Y": (255, 228, 140),
    "p": (20, 14, 10),
}

_VATRACHOS = [
    [  # resting
        "............",
        "...oooo.....",
        "..oYyyyo....",
        "..oyypyo....",
        "..oyypyooooo",
        ".oLoyyoLLLLL",
        ".oLgooggggLL",
        "oLgggggggwgg",
        "oggwgggggggg",
        "oggggmmmmmmm",
        "oGgggggbbbbb",
        "oGggggbbbbbb",
        ".oGgbbbbBbbb",
        "oLooGbbbbBbb",
        "ogLgoGbbbBBB",
        "ogggoGGBBBBB",
        "oGGGGoGGGGGG",
        ".ooooooooooo",
    ],
    [  # throat puffed
        "............",
        "...oooo.....",
        "..oYyyyo....",
        "..oyypyo....",
        "..oyypyooooo",
        ".oLoyyoLLLLL",
        ".oLgooggggLL",
        "oLgggggggwgg",
        "oggwgmmmmmmm",
        "ogggmbbbbbbb",
        "oGggbbbbbbbb",
        "oGgbbbbbbbbb",
        ".oGbbbbbbBbb",
        "oLoGbbbbbbBb",
        "ogLgoGbbbBBB",
        "ogggoGGBBBBB",
        "oGGGGoGGGGGG",
        ".ooooooooooo",
    ],
]


@cached
def vatrachos(frame: int = 0) -> pygame.Surface:
    """Logical-size Vátrachos frame (callers scale for their view)."""
    return from_grid(mirrored(_VATRACHOS[frame % len(_VATRACHOS)]), _VATRACHOS_PALETTE)


ENEMY_GENERATORS: dict[str, Callable[[int], pygame.Surface]] = {
    "vatrachos": vatrachos,
}
ENEMY_IDLE_FRAMES: dict[str, int] = {
    "vatrachos": len(_VATRACHOS),
}


@cached
def enemy(enemy_id: str, frame: int = 0, factor: int = 1) -> pygame.Surface:
    """An enemy frame scaled by ``factor`` (falls back to a placeholder blob)."""
    gen = ENEMY_GENERATORS.get(enemy_id)
    if gen is None:
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(surf, (150, 40, 60), (8, 8), 7)
    else:
        surf = gen(frame)
    return scale(surf, factor)
