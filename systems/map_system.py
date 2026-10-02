"""Tile map loader and renderer."""

from __future__ import annotations

import json

import pygame

import settings as s
from systems.sprites import OBJECT_GENERATORS, OVERHEAD_OBJECTS, dirt_path, grass, missing_tile

TILE_GRASS = 0
TILE_PATH = 1


class TileMap:
    """Loads a JSON map and pre-renders it into ground and overhead layers.

    The ground layer holds tiles plus objects the player walks in front of;
    the overhead layer (tree canopies) is drawn after characters.
    """

    def __init__(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.name: str = data["name"]
        self.display_name: str = data.get("display_name", self.name)
        self.width: int = data["width"]
        self.height: int = data["height"]
        self.player_start: tuple[int, int] = tuple(data["player_start"])

        self.ground: list[list[int]] = data["ground"]
        self.objects: list[dict] = data.get("objects", [])
        self.collisions: list[pygame.Rect] = [self._tile_rect(r)
                                              for r in data.get("collisions", [])]
        self.triggers: list[dict] = data.get("triggers", [])
        self.npc_data: list[dict] = data.get("npcs", [])
        self.item_pickup_data: list[dict] = data.get("item_pickups", [])

        # Pixel dimensions at scale
        self.pixel_width = self.width * s.SCALED_TILE
        self.pixel_height = self.height * s.SCALED_TILE

        self._ground_layer = self._bake(overhead=False)
        self._overhead_layer = self._bake(overhead=True)

    @staticmethod
    def _tile_rect(r: dict) -> pygame.Rect:
        """Convert a {x, y, w, h} tile-unit dict into a scaled pixel rect."""
        return pygame.Rect(
            r["x"] * s.SCALED_TILE, r["y"] * s.SCALED_TILE,
            r["w"] * s.SCALED_TILE, r["h"] * s.SCALED_TILE,
        )

    def get_trigger(self, trigger_id: str) -> pygame.Rect | None:
        for t in self.triggers:
            if t["id"] == trigger_id:
                return self._tile_rect(t)
        return None

    def find_object(self, obj_type: str) -> pygame.Rect | None:
        """Pixel rect of the first object of a given type, if any."""
        for obj in self.objects:
            if obj["type"] == obj_type:
                return self._tile_rect(obj)
        return None

    # ── Pre-rendering ────────────────────────────────────────────────────────

    def _tile_id(self, col: int, row: int) -> int | None:
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.ground[row][col]
        return None

    def _ground_sprite(self, col: int, row: int) -> pygame.Surface:
        tile_id = self.ground[row][col]
        if tile_id == TILE_GRASS:
            # Deterministic per-position variety; flowers are rarer
            h = (col * 73856093) ^ (row * 19349663)
            variant = 3 if h % 11 == 0 else h % 3
            return grass(variant)
        if tile_id == TILE_PATH:
            # Grass fringe on sides bordering grass (map edges count as path)
            edges = tuple(
                self._tile_id(col + dc, row + dr) == TILE_GRASS
                for dc, dr in ((0, -1), (1, 0), (0, 1), (-1, 0))
            )
            return dirt_path(edges)
        return missing_tile()

    def _bake(self, overhead: bool) -> pygame.Surface:
        layer = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        if not overhead:
            for row in range(self.height):
                for col in range(self.width):
                    layer.blit(self._ground_sprite(col, row),
                               (col * s.SCALED_TILE, row * s.SCALED_TILE))

        for obj in self.objects:
            if (obj["type"] in OVERHEAD_OBJECTS) != overhead:
                continue
            gen = OBJECT_GENERATORS.get(obj["type"])
            dest = self._tile_rect(obj)
            if gen:
                layer.blit(gen(obj["w"], obj["h"]), dest)
            else:
                pygame.draw.rect(layer, (255, 0, 255), dest)
        return layer.convert_alpha() if pygame.display.get_surface() else layer

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, camera_x: int, camera_y: int) -> None:
        """Draw the ground layer (tiles + ground-level objects)."""
        surface.blit(self._ground_layer, (-camera_x, -camera_y))

    def render_overhead(self, surface: pygame.Surface, camera_x: int, camera_y: int) -> None:
        """Draw objects that should appear above characters."""
        surface.blit(self._overhead_layer, (-camera_x, -camera_y))
