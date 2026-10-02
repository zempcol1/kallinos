"""Procedural pixel-art sprites for Kallinos.

Everything is generated in code at logical resolution (16px tiles) and
scaled by ``settings.SCALE``. Generators are cached, so calling them every
frame is cheap.
"""

from systems.sprites.backdrops import combat_backdrop
from systems.sprites.characters import DIRECTIONS, PLAYER_LOOK, WALK_FRAMES, Look, character
from systems.sprites.creatures import ENEMY_IDLE_FRAMES, enemy
from systems.sprites.items import item
from systems.sprites.pixel_art import clear_cache, silhouette
from systems.sprites.tiles import (
    OBJECT_GENERATORS, OVERHEAD_OBJECTS, dirt_path, grass, missing_tile,
)

__all__ = [
    "DIRECTIONS", "ENEMY_IDLE_FRAMES", "OBJECT_GENERATORS", "OVERHEAD_OBJECTS",
    "PLAYER_LOOK", "WALK_FRAMES", "Look", "character", "clear_cache",
    "combat_backdrop", "dirt_path", "enemy", "grass", "item", "missing_tile",
    "silhouette",
]
