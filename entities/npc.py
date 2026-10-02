"""NPC entity for the exploration map."""

from __future__ import annotations

import pygame

import settings as s
from entities.character import Character
from systems.sprites import Look


class NPC(Character):
    """A non-player character that stands on the map and can be talked to."""

    def __init__(self, npc_id: str, name: str, tile_x: int, tile_y: int,
                 look: Look, dialogue_idle: list[str] | None = None) -> None:
        super().__init__(tile_x, tile_y, look)
        self.id = npc_id
        self.name = name
        self.visible = True
        self.dialogue_idle = dialogue_idle or []

    @classmethod
    def from_data(cls, data: dict) -> NPC:
        """Build an NPC from a map JSON entry."""
        look = Look(
            tunic=tuple(data["color"]),
            hair=tuple(data.get("hair", (70, 48, 30))),
            bearded=data.get("bearded", False),
        )
        return cls(data["id"], data["name"], data["x"], data["y"], look,
                   data.get("dialogue_idle", []))

    def interaction_rect(self) -> pygame.Rect:
        """A slightly larger rect used for interaction checks."""
        return self.rect.inflate(s.SCALED_TILE, s.SCALED_TILE)

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self.visible:
            super().render(surface, cam_x, cam_y)
