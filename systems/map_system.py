"""Tile map loader and renderer."""

from __future__ import annotations

import json

import pygame

import settings as s
from entities.prop import Prop
from systems.sprites import (
    OBJECT_TYPES, OVERHEAD, SORTED, dirt_path, grass, missing_tile, scale,
)

TILE_GRASS = 0
TILE_PATH = 1


class TileMap:
    """Loads a JSON map and pre-renders it into layers.

    - Ground layer: tiles, ground objects (houses, walls) and every shadow.
    - Props: sorted objects (trees, bushes, fences), drawn depth-sorted with
      characters by the exploration state.
    - Overhead layer: objects drawn above characters.

    Object footprints (trunks, fence rails...) are added to ``collisions``.
    """

    SHADOW_COLOR = (36, 30, 52, 72)   # cool, translucent: reads as late-afternoon shade

    def __init__(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.name: str = data["name"]
        self.display_name: str = data.get("display_name", self.name)
        self.script: str | None = data.get("script")
        self.intro_toast: str | None = data.get("intro_toast")
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

        self.props: list[Prop] = []
        self._ground_layer = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        self._overhead_layer: pygame.Surface | None = None
        self._build()

    @staticmethod
    def _tile_rect(r: dict) -> pygame.Rect:
        """Convert a {x, y, w, h} tile-unit dict (fractions allowed) into a pixel rect."""
        return pygame.Rect(
            round(r["x"] * s.SCALED_TILE), round(r["y"] * s.SCALED_TILE),
            round(r["w"] * s.SCALED_TILE), round(r["h"] * s.SCALED_TILE),
        )

    def get_trigger(self, trigger_id: str) -> pygame.Rect | None:
        for t in self.triggers:
            if t["id"] == trigger_id:
                return self._tile_rect(t)
        return None

    def get_prop(self, prop_id: str) -> Prop | None:
        """The sorted object with this ``"id"`` in the map JSON, if any."""
        for prop in self.props:
            if prop.id == prop_id:
                return prop
        return None

    # ── Building ─────────────────────────────────────────────────────────────

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

    def _placements(self) -> list[tuple[dict, tuple[bool, ...] | None]]:
        """Every object to draw, with tiled objects split into linked tiles.

        Returns (object data, links) pairs in map order; ``links`` is only set
        for tiled types and says which neighbours share the type.
        """
        tiled_cells: dict[str, dict[tuple[int, int], dict]] = {}
        for obj in self.objects:
            kind = OBJECT_TYPES.get(obj["type"])
            if kind and kind.tiled:
                cells = tiled_cells.setdefault(obj["type"], {})
                for ty in range(obj["y"], obj["y"] + obj["h"]):
                    for tx in range(obj["x"], obj["x"] + obj["w"]):
                        cells[(tx, ty)] = {**obj, "x": tx, "y": ty, "w": 1, "h": 1}

        placements: list[tuple[dict, tuple[bool, ...] | None]] = []
        for obj in self.objects:
            kind = OBJECT_TYPES.get(obj["type"])
            if not (kind and kind.tiled):
                placements.append((obj, None))
        for cells in tiled_cells.values():
            for (tx, ty), cell in sorted(cells.items(), key=lambda c: (c[0][1], c[0][0])):
                links = tuple((tx + dx, ty + dy) in cells
                              for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
                placements.append((cell, links))
        return placements

    def _build(self) -> None:
        ground = self._ground_layer
        for row in range(self.height):
            for col in range(self.width):
                ground.blit(self._ground_sprite(col, row),
                            (col * s.SCALED_TILE, row * s.SCALED_TILE))

        # Shadows are drawn at logical size into one mask, so overlapping
        # shadows don't stack up darker and stay on the pixel grid.
        t = s.TILE_SIZE
        shadows = pygame.Surface((self.width * t, self.height * t), pygame.SRCALPHA)
        overhead: list[tuple[pygame.Surface, pygame.Rect]] = []

        for obj, links in self._placements():
            kind = OBJECT_TYPES.get(obj["type"])
            dest = self._tile_rect(obj)
            if kind is None:
                pygame.draw.rect(ground, (255, 0, 255), dest)
                continue
            geometry = (links,) if kind.tiled else (obj["w"], obj["h"])
            variant = obj.get("variant", 0)
            origin = (obj["x"] * t, obj["y"] * t)

            for shape, (x, y, w, h) in kind.shadow(*geometry, variant) if kind.shadow else ():
                draw = pygame.draw.ellipse if shape == "ellipse" else pygame.draw.rect
                draw(shadows, self.SHADOW_COLOR, (origin[0] + x, origin[1] + y, w, h))

            footprints = [pygame.Rect((origin[0] + x) * s.SCALE, (origin[1] + y) * s.SCALE,
                                      w * s.SCALE, h * s.SCALE)
                          for x, y, w, h in (kind.footprint(*geometry) if kind.footprint else ())]
            if obj.get("solid", True):
                self.collisions.extend(footprints)

            if kind.layer == SORTED:
                self.props.append(Prop(obj, kind, dest, footprints, links))
            elif kind.layer == OVERHEAD:
                overhead.append((kind.draw(*geometry, variant), dest))
            else:
                ground.blit(kind.draw(*geometry, variant), dest)

        ground.blit(scale(shadows), (0, 0))
        if overhead:
            self._overhead_layer = pygame.Surface((self.pixel_width, self.pixel_height),
                                                  pygame.SRCALPHA)
            for sprite, dest in overhead:
                self._overhead_layer.blit(sprite, dest)

        if pygame.display.get_surface():
            self._ground_layer = ground.convert_alpha()
            if self._overhead_layer:
                self._overhead_layer = self._overhead_layer.convert_alpha()

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, camera_x: int, camera_y: int) -> None:
        """Draw the ground layer (tiles, ground-level objects and shadows)."""
        surface.blit(self._ground_layer, (-camera_x, -camera_y))

    def render_overhead(self, surface: pygame.Surface, camera_x: int, camera_y: int) -> None:
        """Draw objects that should appear above characters."""
        if self._overhead_layer:
            surface.blit(self._overhead_layer, (-camera_x, -camera_y))
