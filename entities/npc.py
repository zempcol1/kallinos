"""NPC entity for the exploration map."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

import settings as s
from entities.character import Character
from systems.sprites import Look

if TYPE_CHECKING:
    from entities.player import Player
    from states.exploration import Exploration


class NPC(Character):
    """A non-player character that stands on the map and can be talked to.

    Cutscenes can make an NPC ``walk`` along tile waypoints.
    """

    WALK_SPEED = s.PLAYER_SPEED * 0.8   # pixels per second
    _LOOK_COLORS = ("hair", "skin", "trim")               # map JSON keys copied into the Look
    _LOOK_STYLES = ("hair_style", "bearded", "face")

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
        """Build an NPC from a map JSON entry; keys it leaves out use ``Look``'s defaults."""
        colors = {key: tuple(data[key]) for key in cls._LOOK_COLORS if key in data}
        styles = {key: data[key] for key in cls._LOOK_STYLES if key in data}
        look = Look(tunic=tuple(data["color"]), **colors, **styles)
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

    # ── Interactable (people with something to say) ──────────────────────────

    def in_reach(self, player: Player) -> bool:
        return (self.visible and bool(self.dialogue_idle)
                and player.reach_rect().colliderect(self.interaction_rect()))

    @property
    def prompt_anchor(self) -> tuple[int, int]:
        return self.sprite_rect.midtop

    def interact(self, scene: Exploration) -> None:
        self.face_towards(scene.player.x, scene.player.y)
        scene.push_dialogue([(self.name, line) for line in self.dialogue_idle])

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self.visible:
            super().render(surface, cam_x, cam_y)
