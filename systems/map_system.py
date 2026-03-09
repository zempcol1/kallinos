"""Tile map loader and renderer."""

from __future__ import annotations

import json

import pygame

import settings as s
from systems.sprite_factory import get_tile_sprite


class TileMap:
    """Loads a JSON map and renders tile layers."""

    def __init__(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.name: str = data["name"]
        self.width: int = data["width"]
        self.height: int = data["height"]
        self.player_start: tuple[int, int] = tuple(data["player_start"])

        self.ground: list[list[int]] = data["ground"]
        self.objects: list[dict] = data.get("objects", [])
        self.collisions: list[pygame.Rect] = self._load_rects(data.get("collisions", []))
        self.triggers: list[dict] = data.get("triggers", [])
        self.npc_data: list[dict] = data.get("npcs", [])
        self.item_pickup_data: list[dict] = data.get("item_pickups", [])

        # Pixel dimensions at scale
        self.pixel_width = self.width * s.SCALED_TILE
        self.pixel_height = self.height * s.SCALED_TILE

    def _load_rects(self, rects: list[dict]) -> list[pygame.Rect]:
        result = []
        for r in rects:
            result.append(pygame.Rect(
                r["x"] * s.SCALED_TILE, r["y"] * s.SCALED_TILE,
                r["w"] * s.SCALED_TILE, r["h"] * s.SCALED_TILE,
            ))
        return result

    def get_trigger(self, trigger_id: str) -> pygame.Rect | None:
        for t in self.triggers:
            if t["id"] == trigger_id:
                return pygame.Rect(
                    t["x"] * s.SCALED_TILE, t["y"] * s.SCALED_TILE,
                    t["w"] * s.SCALED_TILE, t["h"] * s.SCALED_TILE,
                )
        return None

    def render(self, surface: pygame.Surface, camera_x: int, camera_y: int) -> None:
        """Draw the ground layer and object layer."""
        # Ground
        for row_i, row in enumerate(self.ground):
            for col_i, tile_id in enumerate(row):
                dest_x = col_i * s.SCALED_TILE - camera_x
                dest_y = row_i * s.SCALED_TILE - camera_y
                sprite = get_tile_sprite(tile_id)
                if sprite:
                    surface.blit(sprite, (dest_x, dest_y))
                else:
                    color = s.TILE_COLORS.get(tile_id, s.COLOR_OLIVE_GREEN)
                    rect = pygame.Rect(dest_x, dest_y, s.SCALED_TILE, s.SCALED_TILE)
                    pygame.draw.rect(surface, color, rect)

        # Objects
        for obj in self.objects:
            tile_id = obj["tile"]
            ox = obj["x"] * s.SCALED_TILE - camera_x
            oy = obj["y"] * s.SCALED_TILE - camera_y
            ow = obj["w"]
            oh = obj["h"]
            sprite = get_tile_sprite(tile_id)
            if sprite:
                for ty in range(oh):
                    for tx in range(ow):
                        surface.blit(sprite, (ox + tx * s.SCALED_TILE, oy + ty * s.SCALED_TILE))
            else:
                color = s.TILE_COLORS.get(tile_id, (200, 200, 200))
                rect = pygame.Rect(ox, oy, ow * s.SCALED_TILE, oh * s.SCALED_TILE)
                pygame.draw.rect(surface, color, rect)
