"""Registry of map object types: how each is drawn, layered and collided with."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from systems.sprites import nature, structures

# Layers, bottom to top
GROUND = "ground"      # baked under characters (walls, houses, doors)
SORTED = "sorted"      # depth-sorted with characters (trees, bushes, fences)
OVERHEAD = "overhead"  # baked above characters

Rect = tuple[int, int, int, int]
Shapes = list[tuple[str, Rect]]


@dataclass(frozen=True)
class ObjectType:
    """How one map object type looks and behaves.

    All geometry is in logical pixels relative to the object's top-left.

    Attributes:
        draw: ``(w, h, variant) -> scaled sprite``. Tiled types get ``(links, variant)``.
        layer: ``GROUND``, ``SORTED`` or ``OVERHEAD``.
        footprint: ``(w, h) -> rects`` that block movement, added to the map's
            collisions automatically. For sorted objects the lowest footprint
            edge is the depth line: characters below it are drawn in front.
        shadow: ``(w, h, variant) -> [(kind, rect)]`` ground shadow shapes,
            kind ``"ellipse"`` or ``"rect"``. May reach outside the object.
        tiled: drawn tile by tile, each tile linking to same-type neighbours
            as ``links = (north, east, south, west)`` (fences).
        see_through: fades while the player stands behind it (tree crowns).
        harvestable: ``draw`` accepts ``ripe=False`` for the picked look.
    """

    draw: Callable[..., pygame.Surface]
    layer: str = GROUND
    footprint: Callable[..., list[Rect]] | None = None
    shadow: Callable[..., Shapes] | None = None
    tiled: bool = False
    see_through: bool = False
    harvestable: bool = False


OBJECT_TYPES: dict[str, ObjectType] = {
    # Buildings
    "house_wall": ObjectType(structures.house_wall, shadow=structures.house_wall_shadow),
    "house_roof": ObjectType(structures.house_roof),
    "house_door": ObjectType(structures.house_door),
    "temple": ObjectType(structures.temple, shadow=structures.temple_shadow),
    "stone_wall": ObjectType(structures.stone_wall, shadow=structures.stone_wall_shadow),
    "fence": ObjectType(structures.fence_piece, SORTED, structures.fence_footprint,
                        structures.fence_shadow, tiled=True),
    # Nature
    "olive_tree": ObjectType(nature.olive_tree, SORTED, nature.olive_tree_footprint,
                             nature.tree_shadow, see_through=True),
    "cypress": ObjectType(nature.cypress, SORTED, nature.cypress_footprint,
                          nature.cypress_shadow, see_through=True),
    "plane_tree": ObjectType(nature.plane_tree, SORTED, nature.plane_tree_footprint,
                             nature.tree_shadow, see_through=True),
    "fig_tree": ObjectType(nature.fig_tree, SORTED, nature.fig_tree_footprint,
                           nature.tree_shadow, see_through=True, harvestable=True),
    "bush": ObjectType(nature.bush, SORTED, nature.bush_footprint, nature.bush_shadow),
    "boulder": ObjectType(nature.boulder, SORTED, nature.boulder_footprint,
                          nature.boulder_shadow),
}
