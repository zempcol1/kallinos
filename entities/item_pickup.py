"""Item pickup entity on the exploration map."""

from __future__ import annotations

import math

import pygame

import settings as s
from systems.sprite_factory import sprite_item_branch


class ItemPickup:
    """A world object that the player can pick up."""

    def __init__(self, item_id: str, tile_x: int, tile_y: int,
                 color: tuple[int, int, int]) -> None:
        self.item_id = item_id
        self.x = tile_x * s.SCALED_TILE + s.SCALED_TILE // 2
        self.y = tile_y * s.SCALED_TILE + s.SCALED_TILE // 2
        self.color = color
        self.collected = False
        self._bob_timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        size = int(s.SCALED_TILE * 0.5)
        return pygame.Rect(
            self.x - size // 2,
            self.y - size // 2,
            size, size,
        )

    def update(self, dt: float) -> None:
        self._bob_timer += dt

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self.collected:
            return
        bob = int(math.sin(self._bob_timer / 400.0) * 3)
        r = self.rect.move(-cam_x, -cam_y + bob)
        # Use sprite if available
        if self.item_id == "olive_branch":
            spr = sprite_item_branch()
            surface.blit(spr, (r.x, r.y))
        else:
            pygame.draw.rect(surface, self.color, r)
            pygame.draw.rect(surface, s.COLOR_WHITE, r, 1)
