"""Procedural pixel-art sprites for Kallinos.

Everything is generated in code at logical resolution (16px tiles) and
scaled by ``settings.SCALE``. Generators are cached, so calling them every
frame is cheap.
"""

from systems.sprites.backdrops import combat_backdrop
from systems.sprites.characters import (
    DIRECTIONS, PLAYER_LOOK, WALK_FRAMES, Look, character, character_shadow,
)
from systems.sprites.creatures import ENEMY_IDLE_FRAMES, enemy
from systems.sprites.icons import app_icon, continue_arrow, interact_bubble, laurel
from systems.sprites.items import item
from systems.sprites.objects import GROUND, OBJECT_TYPES, OVERHEAD, SORTED, ObjectType
from systems.sprites.pixel_art import clear_cache, scale, silhouette
from systems.sprites.portraits import PORTRAIT_SIZE, portrait
from systems.sprites.tiles import dirt_path, grass, missing_tile

__all__ = [
    "DIRECTIONS", "ENEMY_IDLE_FRAMES", "app_icon", "GROUND", "OBJECT_TYPES", "OVERHEAD", "PLAYER_LOOK",
    "PORTRAIT_SIZE", "SORTED", "WALK_FRAMES", "Look", "ObjectType", "character",
    "character_shadow", "clear_cache", "combat_backdrop", "continue_arrow", "dirt_path",
    "enemy", "grass", "interact_bubble", "item", "laurel", "missing_tile", "portrait", "scale",
    "silhouette",
]
