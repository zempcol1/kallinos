"""Key bindings in one place, so every screen answers to the same keys.

States compare ``event.key`` against these groups instead of naming pygame
keys themselves; key rebinding (settings menu) only has to change this module.
"""

from __future__ import annotations

from collections.abc import Iterable

import pygame

UP = (pygame.K_UP, pygame.K_w)
DOWN = (pygame.K_DOWN, pygame.K_s)
LEFT = (pygame.K_LEFT, pygame.K_a)
RIGHT = (pygame.K_RIGHT, pygame.K_d)
CONFIRM = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e)   # menus, dialogue, cards
INTERACT = (pygame.K_e, pygame.K_RETURN)                  # on the map (Space stays free)
CANCEL = (pygame.K_ESCAPE,)
MUTE = (pygame.K_m,)


def pressed_keys(events: Iterable[pygame.event.Event]) -> list[int]:
    """The keys that went down in this frame's events, in order."""
    return [event.key for event in events if event.type == pygame.KEYDOWN]


def movement(keys: pygame.key.ScancodeWrapper) -> tuple[int, int]:
    """Held direction as (dx, dy), each -1, 0 or 1; opposite keys cancel out."""
    def held(group: tuple[int, ...]) -> bool:
        return any(keys[key] for key in group)

    return held(RIGHT) - held(LEFT), held(DOWN) - held(UP)
