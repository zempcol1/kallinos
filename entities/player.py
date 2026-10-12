"""Player entity with movement and collision."""

from __future__ import annotations

import pygame

import settings as s
from entities.character import Character
from systems.inventory_system import Inventory
from systems.sprites import PLAYER_LOOK


class Player(Character):
    """The player character on the exploration map."""

    REACH = s.SCALED_TILE // 2   # how far in front of the feet interactions reach
    DIAGONAL_GRACE_MS = 90       # keep a diagonal facing while one key is let go first
    _FACING_STEP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0),
                    "up_left": (-0.7, -0.7), "up_right": (0.7, -0.7),
                    "down_left": (-0.7, 0.7), "down_right": (0.7, 0.7)}

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
        self._diagonal_grace = 0.0

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
        if self.moving:
            facing = self.facing_for(dx, dy)
            if "_" in facing:
                self._diagonal_grace = self.DIAGONAL_GRACE_MS
            elif self._diagonal_grace > 0 and facing in self.facing.split("_"):
                facing = self.facing          # releasing a diagonal: hold the pose
            self.facing = facing
        self._diagonal_grace = max(0.0, self._diagonal_grace - dt)

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

    def reach_rect(self) -> pygame.Rect:
        """The area in front of the player that interactions can reach."""
        dx, dy = self._FACING_STEP[self.facing]
        return self.rect.move(round(dx * self.REACH), round(dy * self.REACH)).inflate(
            self.REACH // 2,
                                                                        self.REACH // 2)

    def stop(self) -> None:
        """Halt the walk cycle (e.g. when a cutscene takes control)."""
        self.moving = False
        self.update_animation(0)

    def _collides(self, collisions: list[pygame.Rect]) -> bool:
        return self.rect.collidelist(collisions) != -1
