"""NPC entity for the exploration map."""

from __future__ import annotations

import pygame

import settings as s
from systems.sprite_factory import sprite_npc


class NPC:
    """A non-player character that stands on the map and can be talked to."""

    def __init__(self, npc_id: str, name: str, tile_x: int, tile_y: int,
                 color: tuple[int, int, int],
                 dialogue_idle: list[str] | None = None) -> None:
        self.id = npc_id
        self.name = name
        self.x = tile_x * s.SCALED_TILE + s.SCALED_TILE // 2
        self.y = tile_y * s.SCALED_TILE + s.SCALED_TILE // 2
        self.width = int(s.SCALED_TILE * 0.6)
        self.height = int(s.SCALED_TILE * 0.85)
        self.color = color
        self.visible = True
        self.dialogue_idle = dialogue_idle or []

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width, self.height,
        )

    def interaction_rect(self) -> pygame.Rect:
        """A slightly larger rect used for interaction checks."""
        r = self.rect
        return r.inflate(s.SCALED_TILE, s.SCALED_TILE)

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if not self.visible:
            return
        spr = sprite_npc(self.color, self.name)
        r = self.rect.move(-cam_x, -cam_y)
        sx = r.centerx - spr.get_width() // 2
        sy = r.bottom - spr.get_height()
        surface.blit(spr, (sx, sy))
