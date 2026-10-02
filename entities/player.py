"""Player entity with movement and collision."""

from __future__ import annotations

import pygame

import settings as s
from entities.character import Character
from systems.inventory_system import Inventory
from systems.sprites import PLAYER_LOOK


class Player(Character):
    """The player character on the exploration map."""

    def __init__(self, tile_x: int, tile_y: int) -> None:
        super().__init__(tile_x, tile_y, PLAYER_LOOK)
        self.speed = s.PLAYER_SPEED

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

        self.moving = bool(dx or dy)
        if dx:
            self.facing = "right" if dx > 0 else "left"
        elif dy:
            self.facing = "down" if dy > 0 else "up"

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

        self.update_animation(dt)

    def stop(self) -> None:
        """Halt the walk cycle (e.g. when a cutscene takes control)."""
        self.moving = False
        self.update_animation(0)

    def _collides(self, collisions: list[pygame.Rect]) -> bool:
        return self.rect.collidelist(collisions) != -1
