"""Shared base for anything humanoid that stands on the map."""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites import WALK_FRAMES, Look, character, character_shadow


class Character:
    """Position, collision box, facing, and walk-cycle rendering.

    ``x``/``y`` is the center of the collision box, which covers only the
    feet so characters can walk close to (and behind) trees and fences. The
    sprite is drawn bottom-aligned on that box; ``depth`` (its bottom edge)
    orders characters against props. ``lift`` raises the sprite off the
    ground (jumps, falls) and ``alpha`` fades it, e.g. in cutscenes.
    """

    FOOT_WIDTH = s.SCALED_TILE // 2
    FOOT_HEIGHT = s.SCALED_TILE * 5 // 16
    FOOT_INSET = s.SCALED_TILE // 12   # gap between the feet and the tile's bottom edge

    def __init__(self, tile_x: int, tile_y: int, look: Look) -> None:
        self.width = self.FOOT_WIDTH
        self.height = self.FOOT_HEIGHT
        self.place(tile_x, tile_y)
        self.look = look
        self.facing = "down"
        self.moving = False
        self.lift = 0.0
        self.alpha = 255
        self._walk_timer = 0.0

    def tile_position(self, tile_x: int, tile_y: int) -> tuple[float, float]:
        """World position of the feet when standing on a tile, near its bottom edge."""
        return (tile_x * s.SCALED_TILE + s.SCALED_TILE // 2,
                (tile_y + 1) * s.SCALED_TILE - self.FOOT_INSET - self.height // 2)

    def place(self, tile_x: int, tile_y: int) -> None:
        """Stand on a tile."""
        self.x, self.y = self.tile_position(tile_x, tile_y)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - self.width / 2),
            round(self.y - self.height / 2),
            self.width,
            self.height,
        )

    @property
    def depth(self) -> int:
        return self.rect.bottom

    @property
    def sprite(self) -> pygame.Surface:
        return character(self.look, self.facing, self.frame)

    @property
    def sprite_rect(self) -> pygame.Rect:
        """Where the sprite is drawn, in world pixels."""
        r = self.rect
        return self.sprite.get_rect(midbottom=(r.centerx, r.bottom))

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
        if self.alpha <= 0:
            return
        r = self.rect.move(-cam_x, -cam_y)
        spr = self.sprite
        if self.alpha < 255:
            spr = spr.copy()
            spr.set_alpha(self.alpha)
        else:
            shadow = character_shadow()
            surface.blit(shadow, shadow.get_rect(center=(r.centerx, r.bottom - s.SCALE)))
        lift = round(self.lift / s.SCALE) * s.SCALE   # stay on the pixel grid
        surface.blit(spr, spr.get_rect(midbottom=(r.centerx, r.bottom - lift)))
