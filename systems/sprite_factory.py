"""Procedural pixel-art sprite generator for Kallinos.

Generates 16×16 tile sprites, 16×24 character sprites, and
other game art using pygame.Surface drawing at the logical scale,
then scaled up for rendering.
"""

from __future__ import annotations

import pygame

import settings as s

# Cache generated surfaces so we only draw once
_cache: dict[str, pygame.Surface] = {}


def _px(surf: pygame.Surface, x: int, y: int, color: tuple) -> None:
    """Draw a single pixel."""
    surf.set_at((x, y), color)


def _rect(surf: pygame.Surface, x: int, y: int, w: int, h: int, color: tuple) -> None:
    """Draw a filled rectangle on a logical-scale surface."""
    pygame.draw.rect(surf, color, (x, y, w, h))


def _scale(surf: pygame.Surface) -> pygame.Surface:
    """Scale a logical-size surface up to render size."""
    w, h = surf.get_size()
    return pygame.transform.scale(surf, (w * s.SCALE, h * s.SCALE))


# ── Tile sprites (16×16 logical) ────────────────────────────────────────────

def tile_grass() -> pygame.Surface:
    if "tile_grass" in _cache:
        return _cache["tile_grass"]
    surf = pygame.Surface((16, 16))
    surf.fill((107, 142, 78))
    # Grass blades — darker tufts
    dark = (85, 120, 60)
    light = (125, 160, 90)
    for pos in [(3, 4), (7, 2), (12, 6), (2, 10), (9, 11), (14, 3), (5, 13), (11, 14)]:
        _px(surf, pos[0], pos[1], dark)
        _px(surf, pos[0], pos[1] + 1, dark)
    for pos in [(1, 7), (6, 9), (13, 12), (10, 1), (4, 14)]:
        _px(surf, pos[0], pos[1], light)
    result = _scale(surf)
    _cache["tile_grass"] = result
    return result


def tile_dirt() -> pygame.Surface:
    if "tile_dirt" in _cache:
        return _cache["tile_dirt"]
    surf = pygame.Surface((16, 16))
    surf.fill((193, 178, 140))
    dark = (170, 155, 120)
    light = (210, 195, 160)
    for pos in [(2, 3), (8, 7), (12, 2), (5, 11), (14, 13), (1, 9)]:
        _px(surf, pos[0], pos[1], dark)
    for pos in [(4, 1), (10, 5), (7, 13), (13, 9), (0, 6)]:
        _px(surf, pos[0], pos[1], light)
    # Small pebbles
    for pos in [(6, 4), (11, 10)]:
        _px(surf, pos[0], pos[1], (140, 130, 110))
    result = _scale(surf)
    _cache["tile_dirt"] = result
    return result


def tile_stone_wall() -> pygame.Surface:
    if "tile_stone_wall" in _cache:
        return _cache["tile_stone_wall"]
    surf = pygame.Surface((16, 16))
    surf.fill((160, 140, 110))
    # Brick pattern
    mortar = (130, 115, 90)
    highlight = (180, 160, 130)
    # Horizontal mortar lines
    _rect(surf, 0, 4, 16, 1, mortar)
    _rect(surf, 0, 8, 16, 1, mortar)
    _rect(surf, 0, 12, 16, 1, mortar)
    # Vertical mortar (offset per row)
    _rect(surf, 5, 0, 1, 4, mortar)
    _rect(surf, 11, 0, 1, 4, mortar)
    _rect(surf, 2, 5, 1, 3, mortar)
    _rect(surf, 8, 5, 1, 3, mortar)
    _rect(surf, 14, 5, 1, 3, mortar)
    _rect(surf, 5, 9, 1, 3, mortar)
    _rect(surf, 11, 9, 1, 3, mortar)
    _rect(surf, 2, 13, 1, 3, mortar)
    _rect(surf, 8, 13, 1, 3, mortar)
    # Highlight
    for pos in [(1, 1), (7, 1), (13, 1), (4, 6), (10, 6), (1, 10), (7, 10)]:
        _px(surf, pos[0], pos[1], highlight)
    result = _scale(surf)
    _cache["tile_stone_wall"] = result
    return result


def tile_house_wall() -> pygame.Surface:
    if "tile_house_wall" in _cache:
        return _cache["tile_house_wall"]
    surf = pygame.Surface((16, 16))
    surf.fill((180, 120, 90))
    # Plaster/stucco texture
    dark = (160, 105, 75)
    light = (200, 140, 110)
    for pos in [(3, 2), (10, 5), (6, 10), (13, 14), (1, 7)]:
        _px(surf, pos[0], pos[1], dark)
    for pos in [(5, 4), (12, 8), (2, 12), (8, 1), (14, 11)]:
        _px(surf, pos[0], pos[1], light)
    # Border lines
    _rect(surf, 0, 0, 16, 1, dark)
    _rect(surf, 0, 15, 16, 1, dark)
    result = _scale(surf)
    _cache["tile_house_wall"] = result
    return result


def tile_house_roof() -> pygame.Surface:
    if "tile_house_roof" in _cache:
        return _cache["tile_house_roof"]
    surf = pygame.Surface((16, 16))
    surf.fill((170, 90, 60))
    # Terracotta tile pattern
    dark = (140, 70, 45)
    light = (190, 110, 80)
    for y in range(0, 16, 4):
        _rect(surf, 0, y, 16, 1, dark)
        offset = 0 if (y // 4) % 2 == 0 else 4
        for x in range(offset, 16, 8):
            _rect(surf, x, y + 1, 1, 3, dark)
    for pos in [(2, 2), (10, 2), (6, 6), (14, 6), (2, 10), (10, 10)]:
        _px(surf, pos[0], pos[1], light)
    result = _scale(surf)
    _cache["tile_house_roof"] = result
    return result


def tile_tree_canopy() -> pygame.Surface:
    if "tile_tree_canopy" in _cache:
        return _cache["tile_tree_canopy"]
    surf = pygame.Surface((16, 16))
    surf.fill((80, 110, 55))
    dark = (60, 90, 40)
    light = (100, 135, 70)
    bright = (120, 150, 85)
    # Leaf clusters
    for pos in [(2, 3), (5, 1), (8, 4), (12, 2), (3, 8), (7, 7), (11, 9),
                (1, 12), (6, 13), (10, 11), (14, 7), (4, 5), (9, 14), (13, 13)]:
        _px(surf, pos[0], pos[1], dark)
    for pos in [(3, 2), (7, 5), (11, 3), (1, 9), (5, 11), (9, 8), (13, 12),
                (4, 14), (8, 10), (14, 5)]:
        _px(surf, pos[0], pos[1], light)
    for pos in [(6, 3), (10, 6), (2, 7), (14, 10)]:
        _px(surf, pos[0], pos[1], bright)
    result = _scale(surf)
    _cache["tile_tree_canopy"] = result
    return result


def tile_tree_trunk() -> pygame.Surface:
    if "tile_tree_trunk" in _cache:
        return _cache["tile_tree_trunk"]
    surf = pygame.Surface((16, 16))
    surf.fill((107, 142, 78))  # grass background
    brown = (90, 70, 50)
    dark = (70, 50, 35)
    light = (110, 90, 65)
    # Trunk in center
    _rect(surf, 5, 0, 6, 16, brown)
    _rect(surf, 5, 0, 1, 16, dark)
    _rect(surf, 10, 0, 1, 16, dark)
    # Bark texture
    for pos in [(7, 3), (8, 7), (6, 11), (9, 14)]:
        _px(surf, pos[0], pos[1], dark)
    for pos in [(8, 2), (7, 9), (9, 5), (8, 13)]:
        _px(surf, pos[0], pos[1], light)
    # Roots at bottom
    _px(surf, 4, 14, brown)
    _px(surf, 4, 15, brown)
    _px(surf, 11, 14, brown)
    _px(surf, 11, 15, brown)
    result = _scale(surf)
    _cache["tile_tree_trunk"] = result
    return result


def tile_boulder() -> pygame.Surface:
    if "tile_boulder" in _cache:
        return _cache["tile_boulder"]
    surf = pygame.Surface((16, 16))
    surf.fill((107, 142, 78))  # grass background
    gray = (120, 120, 110)
    dark = (90, 90, 80)
    light = (150, 150, 140)
    # Boulder shape (rounded)
    _rect(surf, 3, 4, 10, 10, gray)
    _rect(surf, 2, 5, 12, 8, gray)
    _rect(surf, 4, 3, 8, 12, gray)
    # Shading
    _rect(surf, 2, 11, 12, 2, dark)
    _rect(surf, 4, 13, 8, 1, dark)
    # Highlights
    _rect(surf, 4, 4, 4, 2, light)
    _px(surf, 5, 3, light)
    # Moss
    _px(surf, 3, 6, (80, 110, 55))
    _px(surf, 4, 7, (80, 110, 55))
    _px(surf, 12, 10, (80, 110, 55))
    result = _scale(surf)
    _cache["tile_boulder"] = result
    return result


def tile_fence() -> pygame.Surface:
    if "tile_fence" in _cache:
        return _cache["tile_fence"]
    surf = pygame.Surface((16, 16))
    surf.fill((107, 142, 78))  # grass behind
    wood = (200, 185, 155)
    dark = (170, 155, 125)
    # Horizontal rails
    _rect(surf, 0, 4, 16, 2, wood)
    _rect(surf, 0, 10, 16, 2, wood)
    _rect(surf, 0, 4, 16, 1, dark)
    _rect(surf, 0, 10, 16, 1, dark)
    # Vertical posts
    _rect(surf, 2, 2, 2, 12, wood)
    _rect(surf, 12, 2, 2, 12, wood)
    _rect(surf, 2, 2, 1, 12, dark)
    _rect(surf, 12, 2, 1, 12, dark)
    # Post caps
    _rect(surf, 1, 1, 4, 2, wood)
    _rect(surf, 11, 1, 4, 2, wood)
    result = _scale(surf)
    _cache["tile_fence"] = result
    return result


def tile_bush() -> pygame.Surface:
    if "tile_bush" in _cache:
        return _cache["tile_bush"]
    surf = pygame.Surface((16, 16))
    surf.fill((107, 142, 78))  # grass background
    green = (75, 100, 50)
    dark = (55, 80, 35)
    light = (95, 120, 65)
    # Bush shape
    _rect(surf, 3, 6, 10, 8, green)
    _rect(surf, 2, 7, 12, 6, green)
    _rect(surf, 4, 5, 8, 10, green)
    # Shading
    _rect(surf, 2, 12, 12, 2, dark)
    _rect(surf, 3, 5, 2, 2, dark)
    # Highlights / leaf detail
    for pos in [(5, 6), (8, 7), (6, 9), (10, 8), (4, 11)]:
        _px(surf, pos[0], pos[1], light)
    # Small berries
    _px(surf, 7, 8, (180, 60, 60))
    _px(surf, 10, 10, (180, 60, 60))
    result = _scale(surf)
    _cache["tile_bush"] = result
    return result


# Map from tile IDs to generator functions
TILE_GENERATORS: dict[int, callable] = {
    0: tile_grass,
    1: tile_dirt,
    2: tile_stone_wall,
    3: tile_house_wall,
    4: tile_house_roof,
    5: tile_tree_canopy,
    6: tile_boulder,
    7: tile_tree_trunk,
    8: tile_fence,
    9: tile_bush,
}


def get_tile_sprite(tile_id: int) -> pygame.Surface | None:
    """Get a pre-scaled tile sprite by tile ID."""
    gen = TILE_GENERATORS.get(tile_id)
    if gen:
        return gen()
    return None


# ── Character sprites (16×24 logical → scaled) ─────────────────────────────

def sprite_player() -> pygame.Surface:
    """16×24 player character — Greek teenager in a tunic."""
    if "sprite_player" in _cache:
        return _cache["sprite_player"]
    surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    skin = (220, 195, 150)
    skin_shadow = (190, 165, 120)
    tunic = (230, 220, 200)
    tunic_dark = (200, 190, 170)
    belt = (140, 110, 60)
    hair = (80, 55, 30)
    sandal = (160, 120, 70)
    eye = (40, 35, 25)

    # Hair (top)
    _rect(surf, 5, 0, 6, 3, hair)
    _rect(surf, 4, 1, 8, 2, hair)

    # Head
    _rect(surf, 5, 3, 6, 6, skin)
    _rect(surf, 4, 4, 8, 4, skin)
    # Shadow on face
    _rect(surf, 4, 7, 8, 1, skin_shadow)
    # Eyes
    _px(surf, 6, 5, eye)
    _px(surf, 9, 5, eye)
    # Mouth
    _px(surf, 7, 7, skin_shadow)
    _px(surf, 8, 7, skin_shadow)

    # Neck
    _rect(surf, 7, 9, 2, 1, skin)

    # Tunic body
    _rect(surf, 4, 10, 8, 8, tunic)
    _rect(surf, 3, 11, 10, 6, tunic)
    _rect(surf, 3, 11, 1, 6, tunic_dark)
    _rect(surf, 12, 11, 1, 6, tunic_dark)
    # Tunic bottom hem
    _rect(surf, 3, 17, 10, 1, tunic_dark)
    # Belt
    _rect(surf, 4, 13, 8, 1, belt)

    # Arms (skin)
    _rect(surf, 2, 11, 1, 5, skin)
    _rect(surf, 13, 11, 1, 5, skin)
    _rect(surf, 2, 15, 1, 1, skin_shadow)
    _rect(surf, 13, 15, 1, 1, skin_shadow)

    # Legs
    _rect(surf, 5, 18, 3, 4, skin)
    _rect(surf, 9, 18, 3, 4, skin)
    # Sandals
    _rect(surf, 4, 22, 4, 2, sandal)
    _rect(surf, 9, 22, 4, 2, sandal)
    _px(surf, 4, 22, (130, 95, 55))
    _px(surf, 12, 22, (130, 95, 55))

    result = _scale(surf)
    _cache["sprite_player"] = result
    return result


def sprite_npc(color: tuple[int, int, int], name: str = "") -> pygame.Surface:
    """16×24 NPC character with a colored tunic."""
    key = f"sprite_npc_{color}_{name}"
    if key in _cache:
        return _cache[key]
    surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    skin = (200, 175, 130)
    skin_shadow = (175, 150, 110)
    tunic_dark = (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30))
    hair = (60, 45, 25)
    eye = (30, 25, 20)
    sandal = (140, 105, 60)

    # Hair
    _rect(surf, 5, 0, 6, 3, hair)
    _rect(surf, 4, 1, 8, 2, hair)

    # Head
    _rect(surf, 5, 3, 6, 6, skin)
    _rect(surf, 4, 4, 8, 4, skin)
    _rect(surf, 4, 7, 8, 1, skin_shadow)
    _px(surf, 6, 5, eye)
    _px(surf, 9, 5, eye)

    # Neck
    _rect(surf, 7, 9, 2, 1, skin)

    # Tunic
    _rect(surf, 4, 10, 8, 8, color)
    _rect(surf, 3, 11, 10, 6, color)
    _rect(surf, 3, 11, 1, 6, tunic_dark)
    _rect(surf, 12, 11, 1, 6, tunic_dark)
    _rect(surf, 3, 17, 10, 1, tunic_dark)

    # Arms
    _rect(surf, 2, 11, 1, 5, skin)
    _rect(surf, 13, 11, 1, 5, skin)

    # Legs
    _rect(surf, 5, 18, 3, 4, skin)
    _rect(surf, 9, 18, 3, 4, skin)
    _rect(surf, 4, 22, 4, 2, sandal)
    _rect(surf, 9, 22, 4, 2, sandal)

    result = _scale(surf)
    _cache[key] = result
    return result


def sprite_enemy_vatrachos() -> pygame.Surface:
    """Vátrachos — a cat-sized marsh frog, ~20×16 logical."""
    if "sprite_vatrachos" in _cache:
        return _cache["sprite_vatrachos"]
    surf = pygame.Surface((20, 16), pygame.SRCALPHA)
    body = (40, 80, 30)
    belly = (70, 110, 55)
    dark = (30, 60, 20)
    eye_amber = (220, 180, 50)
    pupil = (20, 20, 10)

    # Body (elliptical)
    _rect(surf, 4, 5, 12, 8, body)
    _rect(surf, 3, 6, 14, 6, body)
    _rect(surf, 5, 4, 10, 10, body)
    # Belly
    _rect(surf, 6, 9, 8, 4, belly)
    _rect(surf, 5, 10, 10, 2, belly)
    # Dark shading
    _rect(surf, 3, 11, 14, 2, dark)
    _rect(surf, 5, 13, 10, 1, dark)

    # Eyes (big and prominent)
    _rect(surf, 4, 3, 4, 4, eye_amber)
    _rect(surf, 12, 3, 4, 4, eye_amber)
    _rect(surf, 5, 4, 2, 2, pupil)
    _rect(surf, 13, 4, 2, 2, pupil)

    # Front legs
    _rect(surf, 1, 11, 3, 2, body)
    _rect(surf, 16, 11, 3, 2, body)
    _rect(surf, 0, 12, 2, 2, body)
    _rect(surf, 18, 12, 2, 2, body)
    # Toes
    _px(surf, 0, 14, dark)
    _px(surf, 1, 14, dark)
    _px(surf, 18, 14, dark)
    _px(surf, 19, 14, dark)

    # Back legs (powerful)
    _rect(surf, 2, 7, 2, 3, body)
    _rect(surf, 16, 7, 2, 3, body)

    # Nostrils
    _px(surf, 8, 5, dark)
    _px(surf, 11, 5, dark)

    # Mouth line
    _rect(surf, 6, 8, 8, 1, dark)

    result = _scale(surf)
    _cache["sprite_vatrachos"] = result
    return result


def sprite_item_branch() -> pygame.Surface:
    """Olive-wood branch pickup sprite, 16×16."""
    if "sprite_branch" in _cache:
        return _cache["sprite_branch"]
    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    wood = (140, 110, 60)
    wood_dark = (110, 85, 40)
    leaf = (100, 135, 70)

    # Branch diagonal
    for i in range(12):
        x = 2 + i
        y = 13 - i
        _px(surf, x, y, wood)
        _px(surf, x, y + 1, wood)
    # Thicker middle
    for i in range(4, 9):
        x = 2 + i
        y = 13 - i
        _px(surf, x - 1, y, wood_dark)
    # Small side branches
    _px(surf, 8, 4, wood)
    _px(surf, 9, 3, wood)
    _px(surf, 5, 10, wood)
    _px(surf, 4, 11, wood)
    # Leaves
    _px(surf, 10, 2, leaf)
    _px(surf, 9, 2, leaf)
    _px(surf, 3, 11, leaf)
    _px(surf, 3, 12, leaf)

    result = _scale(surf)
    _cache["sprite_branch"] = result
    return result


def clear_cache() -> None:
    """Clear all cached sprites."""
    _cache.clear()
