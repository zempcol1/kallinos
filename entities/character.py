"""Shared base for anything humanoid that stands on the map."""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites import WALK_FRAMES, Look, character


class Character:
    """Position, collision box, facing, and walk-cycle rendering.

    ``x``/``y`` is the center of the collision box (the character's feet
    area); the sprite is drawn bottom-aligned on that box.
    """

    def __init__(self, tile_x: int, tile_y: int, look: Look) -> None:
        self.place(tile_x, tile_y)
        self.width = int(s.SCALED_TILE * 0.6)
        self.height = int(s.SCALED_TILE * 0.85)
        self.look = look
        self.facing = "down"
        self.moving = False
        self._walk_timer = 0.0

    def place(self, tile_x: int, tile_y: int) -> None:
        """Move to the center of a tile."""
        self.x = tile_x * s.SCALED_TILE + s.SCALED_TILE // 2
        self.y = tile_y * s.SCALED_TILE + s.SCALED_TILE // 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height,
        )

    def face_towards(self, other_x: float, other_y: float) -> None:
        """Turn to look at a point (e.g. the player who started talking)."""
        dx, dy = other_x - self.x, other_y - self.y
        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"

    def update_animation(self, dt: float) -> None:
        if self.moving:
            self._walk_timer += dt
        else:
            self._walk_timer = 0.0

    @property
    def frame(self) -> int:
        if not self.moving:
            return 0
        return int(self._walk_timer // s.WALK_FRAME_MS) % WALK_FRAMES

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        spr = character(self.look, self.facing, self.frame)
        r = self.rect.move(-cam_x, -cam_y)

        shadow = pygame.Rect(0, 0, int(s.SCALED_TILE * 0.6), s.SCALE * 3)
        shadow.midbottom = (r.centerx, r.bottom + s.SCALE)
        shadow_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (20, 25, 10, 70), shadow_surf.get_rect())
        surface.blit(shadow_surf, shadow)

        surface.blit(spr, (r.centerx - spr.get_width() // 2, r.bottom - spr.get_height()))
