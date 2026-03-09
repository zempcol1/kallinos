"""Player entity with movement and collision."""

from __future__ import annotations

import pygame

import settings as s
from systems.inventory_system import Inventory
from systems.sprite_factory import sprite_player


class Player:
    """The player character on the exploration map."""

    def __init__(self, tile_x: int, tile_y: int) -> None:
        self.x = tile_x * s.SCALED_TILE + s.SCALED_TILE // 2
        self.y = tile_y * s.SCALED_TILE + s.SCALED_TILE // 2
        self.width = int(s.SCALED_TILE * 0.6)
        self.height = int(s.SCALED_TILE * 0.85)
        self.speed = s.PLAYER_SPEED
        self.color = (220, 195, 150)  # Skin/tunic placeholder

        # Stats
        self.name = "Kallinos"
        self.max_hp = 35
        self.hp = 35
        self.attack = 3
        self.defense = 1
        self.level = 1
        self.xp = 0
        self.xp_to_next = 30

        self.inventory = Inventory()

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height,
        )

    def handle_input(self, keys: pygame.key.ScancodeWrapper, dt: float,
                     collisions: list[pygame.Rect]) -> None:
        """Move the player based on held keys, respecting collisions."""
        dx, dy = 0.0, 0.0
        dist = self.speed * (dt / 1000.0)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= dist
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += dist
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= dist
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += dist

        # Normalize diagonal
        if dx and dy:
            factor = 0.7071  # 1/sqrt(2)
            dx *= factor
            dy *= factor

        # Move X then Y separately for sliding along walls
        self.x += dx
        if self._collides(collisions):
            self.x -= dx

        self.y += dy
        if self._collides(collisions):
            self.y -= dy

    def _collides(self, collisions: list[pygame.Rect]) -> bool:
        r = self.rect
        for wall in collisions:
            if r.colliderect(wall):
                return True
        return False

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        spr = sprite_player()
        # Center the sprite on the player's collision rect
        r = self.rect.move(-cam_x, -cam_y)
        sx = r.centerx - spr.get_width() // 2
        sy = r.bottom - spr.get_height()
        surface.blit(spr, (sx, sy))
