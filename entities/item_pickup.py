"""Item pickup entity on the exploration map."""

from __future__ import annotations

import math

import pygame

import settings as s
from systems.sprites import character_shadow, item


class ItemPickup:
    """A world object that the player can pick up."""

    def __init__(self, item_id: str, tile_x: int, tile_y: int,
                 color: tuple[int, int, int]) -> None:
        self.item_id = item_id
        self.x = tile_x * s.SCALED_TILE + s.SCALED_TILE // 2
        self.y = tile_y * s.SCALED_TILE + s.SCALED_TILE // 2
        self.color = color  # Fallback when the item has no sprite
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

    @property
    def depth(self) -> int:
        return self.rect.bottom

    def interaction_rect(self) -> pygame.Rect:
        return self.rect.inflate(s.SCALED_TILE // 2, s.SCALED_TILE // 2)

    def update(self, dt: float) -> None:
        self._bob_timer += dt

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self.collected:
            return
        bob = round(math.sin(self._bob_timer / 400.0)) * s.SCALE   # stay on the pixel grid
        r = self.rect.move(-cam_x, -cam_y)
        spr = item(self.item_id)
        if spr is None:
            pygame.draw.rect(surface, self.color, r.move(0, bob))
            pygame.draw.rect(surface, s.COLOR_WHITE, r.move(0, bob), 1)
            return

        # Shadow stays on the ground while the item bobs above it
        shadow = character_shadow()
        surface.blit(shadow, shadow.get_rect(center=(r.centerx, r.bottom + s.SCALE)))
        surface.blit(spr, spr.get_rect(center=(r.centerx, r.centery + bob)))
