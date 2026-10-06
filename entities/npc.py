"""NPC entity for the exploration map."""

from __future__ import annotations

import math

import pygame

import settings as s
from entities.character import Character
from systems.sprites import Look


class NPC(Character):
    """A non-player character that stands on the map and can be talked to.

    Cutscenes can make an NPC ``walk`` along tile waypoints.
    """

    WALK_SPEED = s.PLAYER_SPEED * 0.8   # pixels per second

    def __init__(self, npc_id: str, name: str, tile_x: int, tile_y: int,
                 look: Look, dialogue_idle: list[str] | None = None) -> None:
        super().__init__(tile_x, tile_y, look)
        self.id = npc_id
        self.name = name
        self.visible = True
        self.dialogue_idle = dialogue_idle or []
        self._path: list[tuple[float, float]] = []

    @classmethod
    def from_data(cls, data: dict) -> NPC:
        """Build an NPC from a map JSON entry."""
        look = Look(
            tunic=tuple(data["color"]),
            hair=tuple(data.get("hair", (70, 48, 30))),
            trim=tuple(data["trim"]) if "trim" in data else None,
            hair_style=data.get("hair_style", "short"),
            bearded=data.get("bearded", False),
        )
        return cls(data["id"], data["name"], data["x"], data["y"], look,
                   data.get("dialogue_idle", []))

    @property
    def walking(self) -> bool:
        return bool(self._path)

    def walk(self, path: list[list[int]]) -> None:
        """Walk through tile waypoints (cutscenes), ignoring collisions."""
        self._path = [self.tile_position(tx, ty) for tx, ty in path]

    def update(self, dt: float) -> None:
        self.moving = bool(self._path)
        if self._path:
            tx, ty = self._path[0]
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            step = self.WALK_SPEED * dt / 1000
            if dist <= step:
                self.x, self.y = tx, ty
                self._path.pop(0)
            else:
                self.face_towards(tx, ty)
                self.x += dx / dist * step
                self.y += dy / dist * step
        self.update_animation(dt)

    def interaction_rect(self) -> pygame.Rect:
        """The feet box grown by half a tile: talk from any side."""
        return self.rect.inflate(s.SCALED_TILE // 2, s.SCALED_TILE // 2)

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self.visible:
            super().render(surface, cam_x, cam_y)
