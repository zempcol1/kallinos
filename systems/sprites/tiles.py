"""Ground tiles and multi-tile map objects (houses, trees, walls...)."""

from __future__ import annotations

from collections.abc import Callable

import pygame

import settings as s
from systems.sprites.pixel_art import (
    cached, ellipse_shadow, outline, scale, seeded, shade, speckle,
)

T = s.TILE_SIZE

# ── Palette ──────────────────────────────────────────────────────────────────
GRASS = (107, 142, 78)
GRASS_DARK = (86, 121, 62)
GRASS_LIGHT = (128, 162, 92)
DIRT = (214, 190, 142)
DIRT_DARK = (189, 164, 117)
DIRT_LIGHT = (231, 211, 168)
PEBBLE = (160, 142, 108)
OUTLINE = (45, 34, 28)

PLASTER = (236, 226, 204)
PLASTER_SHADE = (212, 198, 172)
TERRACOTTA = (192, 114, 94)
TERRACOTTA_DARK = (150, 80, 64)
TERRACOTTA_LIGHT = (216, 146, 120)
WOOD = (93, 64, 55)
WOOD_DARK = (64, 43, 37)
WOOD_LIGHT = (128, 92, 72)
MARBLE = (242, 239, 234)
MARBLE_SHADE = (205, 200, 192)
STONE = (168, 152, 124)
STONE_DARK = (132, 118, 94)
STONE_LIGHT = (192, 178, 150)

OLIVE_LEAF = (112, 138, 84)
OLIVE_LEAF_DARK = (74, 98, 58)
OLIVE_LEAF_LIGHT = (156, 176, 122)
OLIVE_BARK = (104, 86, 66)
OLIVE_BARK_DARK = (74, 60, 46)


# ── Ground tiles (16×16) ─────────────────────────────────────────────────────

def _grass_base(variant: int) -> pygame.Surface:
    surf = pygame.Surface((T, T))
    surf.fill(GRASS)
    rng = seeded("grass", variant)
    # Small "v" shaped blades
    for _ in range(6):
        x, y = rng.randrange(1, T - 1), rng.randrange(1, T - 1)
        surf.set_at((x - 1, y), GRASS_DARK)
        surf.set_at((x + 1, y), GRASS_DARK)
        surf.set_at((x, y + 1), GRASS_DARK)
    speckle(surf, rng, GRASS_LIGHT, 5)
    return surf


@cached
def grass(variant: int = 0) -> pygame.Surface:
    """Grass with a few texture variants; variant 3 has wildflowers."""
    surf = _grass_base(variant)
    if variant == 3:
        rng = seeded("flowers", variant)
        for color in ((242, 236, 220), (240, 200, 70), (200, 110, 150)):
            x, y = rng.randrange(2, T - 2), rng.randrange(2, T - 2)
            surf.set_at((x, y), color)
            surf.set_at((x, y + 1), GRASS_DARK)
    return scale(surf)


@cached
def dirt_path(edges: tuple[bool, bool, bool, bool] = (False,) * 4) -> pygame.Surface:
    """Packed-earth path. ``edges`` = (top, right, bottom, left) grass borders."""
    surf = pygame.Surface((T, T))
    surf.fill(DIRT)
    rng = seeded("dirt", edges)
    speckle(surf, rng, DIRT_DARK, 10)
    speckle(surf, rng, DIRT_LIGHT, 8)
    for _ in range(2):
        x, y = rng.randrange(2, T - 3), rng.randrange(2, T - 3)
        pygame.draw.rect(surf, PEBBLE, (x, y, 2, 1))
        surf.set_at((x, y + 1), DIRT_DARK)

    # Ragged grass fringe along edges that border grass
    top, right, bottom, left = edges
    for i in range(T):
        depth = 1 + (rng.random() < 0.45)
        if top:
            pygame.draw.line(surf, GRASS, (i, 0), (i, depth - 1))
            surf.set_at((i, depth), DIRT_DARK)
        if bottom:
            pygame.draw.line(surf, GRASS, (i, T - depth), (i, T - 1))
        if left:
            pygame.draw.line(surf, GRASS, (0, i), (depth - 1, i))
            surf.set_at((depth, i), DIRT_DARK)
        if right:
            pygame.draw.line(surf, GRASS, (T - depth, i), (T - 1, i))
    return scale(surf)


@cached
def missing_tile() -> pygame.Surface:
    """Loud magenta checkerboard for unknown tile IDs."""
    surf = pygame.Surface((T, T))
    surf.fill((255, 0, 255))
    pygame.draw.rect(surf, (0, 0, 0), (0, 0, T // 2, T // 2))
    pygame.draw.rect(surf, (0, 0, 0), (T // 2, T // 2, T // 2, T // 2))
    return scale(surf)


# ── Map objects (sized in tiles) ─────────────────────────────────────────────

def _canvas(w: int, h: int) -> pygame.Surface:
    return pygame.Surface((w * T, h * T), pygame.SRCALPHA)


@cached
def stone_wall(w: int, h: int) -> pygame.Surface:
    """Dry-stone wall: a light cap on top, coursed stone face below."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    cap_h = 6
    rng = seeded("stone_wall", w, h)
    surf.fill(STONE_DARK)

    # Face: irregular courses of stones
    y = cap_h
    row = 0
    while y < ph:
        course_h = rng.choice((4, 5))
        x = -rng.randrange(0, 6) if row % 2 else 0
        while x < pw:
            stone_w = rng.randrange(5, 9)
            rect = pygame.Rect(x + 1, y + 1, stone_w - 1, course_h - 1)
            pygame.draw.rect(surf, STONE, rect)
            pygame.draw.line(surf, STONE_LIGHT, rect.topleft, (rect.right - 1, rect.top))
            x += stone_w
        y += course_h
        row += 1

    # Cap
    pygame.draw.rect(surf, STONE_LIGHT, (0, 0, pw, cap_h))
    speckle(surf, rng, STONE, pw // 2, pygame.Rect(0, 0, pw, cap_h - 1))
    pygame.draw.line(surf, STONE_DARK, (0, cap_h - 1), (pw, cap_h - 1))
    pygame.draw.line(surf, shade(STONE_DARK, -0.3), (0, ph - 1), (pw, ph - 1))
    return scale(surf)


@cached
def house_wall(w: int, h: int) -> pygame.Surface:
    """Whitewashed plaster wall with shuttered windows at each end."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("house_wall", w, h)
    surf.fill(PLASTER)
    speckle(surf, rng, PLASTER_SHADE, pw * ph // 40)
    # Stone plinth along the bottom
    pygame.draw.rect(surf, STONE, (0, ph - 3, pw, 3))
    pygame.draw.line(surf, STONE_DARK, (0, ph - 3), (pw, ph - 3))
    # Corner shading
    pygame.draw.line(surf, PLASTER_SHADE, (0, 0), (0, ph))
    pygame.draw.line(surf, PLASTER_SHADE, (pw - 1, 0), (pw - 1, ph))

    if w >= 3:
        win_y = ph - T + 3
        for tile_x in (0, w - 1):
            wx = tile_x * T + 5
            pygame.draw.rect(surf, (52, 44, 50), (wx, win_y, 6, 6))
            pygame.draw.line(surf, WOOD_LIGHT, (wx - 2, win_y), (wx - 2, win_y + 5))
            pygame.draw.line(surf, WOOD_LIGHT, (wx + 7, win_y), (wx + 7, win_y + 5))
            pygame.draw.line(surf, STONE_LIGHT, (wx - 1, win_y + 6), (wx + 6, win_y + 6))
    return scale(surf)


@cached
def house_roof(w: int, h: int) -> pygame.Surface:
    """Terracotta tiled roof seen from above, with ridge and eave shadow."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    surf.fill(TERRACOTTA)
    course_h = 4
    for row, y in enumerate(range(2, ph, course_h)):
        offset = 0 if row % 2 == 0 else 3
        pygame.draw.line(surf, TERRACOTTA_LIGHT, (0, y), (pw, y))
        pygame.draw.line(surf, TERRACOTTA_DARK, (0, y + course_h - 1), (pw, y + course_h - 1))
        for x in range(offset, pw, 6):
            pygame.draw.line(surf, TERRACOTTA_DARK, (x, y + 1), (x, y + course_h - 2))
    # Ridge cap
    pygame.draw.rect(surf, TERRACOTTA_DARK, (0, 0, pw, 2))
    pygame.draw.line(surf, TERRACOTTA_LIGHT, (0, 0), (pw, 0))
    # Eaves: dark underside
    pygame.draw.rect(surf, shade(TERRACOTTA_DARK, -0.35), (0, ph - 2, pw, 2))
    pygame.draw.line(surf, TERRACOTTA_DARK, (0, 0), (0, ph))
    pygame.draw.line(surf, TERRACOTTA_DARK, (pw - 1, 0), (pw - 1, ph))
    return scale(surf)


@cached
def house_door(w: int = 1, h: int = 1) -> pygame.Surface:
    """Wooden plank door in a stone frame, with a threshold step."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    door = pygame.Rect(3, 1, pw - 6, ph - 3)
    pygame.draw.rect(surf, STONE_LIGHT, door.inflate(2, 0).move(0, -1))
    pygame.draw.rect(surf, WOOD, door.inflate(-2, 0).move(0, 1))
    for x in range(door.left + 3, door.right - 1, 3):
        pygame.draw.line(surf, WOOD_DARK, (x, door.top + 2), (x, door.bottom))
    pygame.draw.line(surf, WOOD_LIGHT, (door.left + 1, door.top + 1),
                     (door.right - 2, door.top + 1))
    surf.set_at((door.right - 4, door.centery + 1), (212, 168, 68))  # brass handle
    pygame.draw.rect(surf, STONE, (1, ph - 2, pw - 2, 2))
    return scale(surf)


@cached
def temple(w: int, h: int) -> pygame.Surface:
    """Small marble shrine: pediment, painted frieze, columns, steps."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    pediment_h = 10
    frieze_h = 4
    steps_h = 6
    col_top = pediment_h + frieze_h
    col_bottom = ph - steps_h

    # Dark cella interior behind the columns
    pygame.draw.rect(surf, (58, 50, 56), (2, col_top, pw - 4, col_bottom - col_top))

    # Pediment (triangle) + painted frieze (Greeks painted their marble)
    pygame.draw.polygon(surf, MARBLE, [(0, pediment_h), (pw // 2, 0), (pw - 1, pediment_h)])
    pygame.draw.polygon(surf, MARBLE_SHADE,
                        [(6, pediment_h - 1), (pw // 2, 3), (pw - 7, pediment_h - 1)])
    pygame.draw.lines(surf, OUTLINE, False,
                      [(0, pediment_h), (pw // 2, 0), (pw - 1, pediment_h)])
    pygame.draw.rect(surf, MARBLE, (0, pediment_h, pw, frieze_h))
    for x in range(2, pw - 2, 4):
        color = (52, 100, 150) if (x // 4) % 2 else (212, 168, 68)
        pygame.draw.rect(surf, color, (x, pediment_h + 1, 2, 2))
    pygame.draw.line(surf, MARBLE_SHADE, (0, col_top - 1), (pw, col_top - 1))

    # Columns, evenly spaced, leaving a doorway in the middle
    n_cols = 4 if w >= 4 else 2
    spacing = (pw - 8) / (n_cols - 1)
    for i in range(n_cols):
        cx = int(4 + i * spacing)
        pygame.draw.rect(surf, MARBLE, (cx - 3, col_top, 6, col_bottom - col_top))
        pygame.draw.line(surf, MARBLE_SHADE, (cx + 2, col_top), (cx + 2, col_bottom))
        pygame.draw.line(surf, MARBLE_SHADE, (cx - 1, col_top + 2), (cx - 1, col_bottom - 2))
        pygame.draw.rect(surf, MARBLE, (cx - 4, col_top, 8, 2))
        pygame.draw.rect(surf, MARBLE, (cx - 4, col_bottom - 2, 8, 2))

    # Bronze doors
    door = pygame.Rect(pw // 2 - 5, col_bottom - 14, 10, 14)
    pygame.draw.rect(surf, (120, 82, 44), door)
    pygame.draw.line(surf, (82, 54, 30), door.midtop, door.midbottom)

    # Steps
    for i in range(3):
        y = col_bottom + i * 2
        pygame.draw.rect(surf, MARBLE if i % 2 == 0 else MARBLE_SHADE, (i, y, pw - 2 * i, 2))
    return scale(outline(surf, OUTLINE))


@cached
def fence(w: int, h: int) -> pygame.Surface:
    """Wooden post-and-rail fence; runs vertically when taller than wide."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    wood = (196, 172, 130)
    dark = (140, 116, 82)
    vertical = h > w

    if vertical:
        cx = pw // 2
        pygame.draw.rect(surf, wood, (cx - 3, 0, 2, ph))
        pygame.draw.rect(surf, wood, (cx + 1, 0, 2, ph))
        pygame.draw.line(surf, dark, (cx - 2, 0), (cx - 2, ph))
        pygame.draw.line(surf, dark, (cx + 2, 0), (cx + 2, ph))
        posts = [(cx, ty * T + 4) for ty in range(h)]
    else:
        for rail_y in (5, 10):
            pygame.draw.rect(surf, wood, (0, rail_y, pw, 2))
            pygame.draw.line(surf, dark, (0, rail_y + 1), (pw, rail_y + 1))
        posts = [(tx * T + 8, 2) for tx in range(w)]

    for px, py in posts:
        pygame.draw.rect(surf, wood, (px - 2, py, 4, 12))
        pygame.draw.line(surf, dark, (px + 1, py), (px + 1, py + 11))
        pygame.draw.rect(surf, shade(wood, 0.25), (px - 2, py, 4, 1))
        ellipse_shadow(surf, (px - 3, py + 10, 7, 3), alpha=50)
    return scale(outline(surf, OUTLINE))


@cached
def boulder(w: int, h: int) -> pygame.Surface:
    """One big mossy boulder filling the object's footprint."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("boulder", w, h)
    gray, dark, light = (128, 126, 116), (92, 90, 84), (166, 164, 152)
    moss = (96, 126, 64)

    ellipse_shadow(surf, (1, ph - 8, pw - 2, 7), alpha=80)
    body = pygame.Rect(2, 3, pw - 4, ph - 6)
    pygame.draw.ellipse(surf, dark, body)
    pygame.draw.ellipse(surf, gray, body.inflate(-2, -4).move(-1, -2))
    pygame.draw.ellipse(surf, light, (body.x + 5, body.y + 3, body.w // 3, body.h // 4))
    # Cracks
    cx = body.centerx + rng.randrange(-3, 4)
    pygame.draw.lines(surf, dark, False,
                      [(cx, body.top + 4), (cx - 2, body.centery), (cx + 1, body.bottom - 6)])
    pygame.draw.line(surf, dark, (cx - 2, body.centery), (cx - 7, body.centery + 3))
    # Moss on the shaded side
    for _ in range(14):
        mx = rng.randrange(body.left + 3, body.centerx)
        my = rng.randrange(body.centery, body.bottom - 3)
        if surf.get_at((mx, my)).a:
            surf.set_at((mx, my), moss)
    return scale(outline(surf, OUTLINE))


@cached
def bush(w: int = 1, h: int = 1) -> pygame.Surface:
    """Round shrub with leafy highlights and a few red berries."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("bush", w, h)
    green, dark, light = (82, 116, 56), (58, 88, 40), (118, 152, 80)

    ellipse_shadow(surf, (1, ph - 5, pw - 2, 4), alpha=80)
    for cx, cy, r in ((5, 9, 4), (11, 9, 4), (8, 6, 5)):
        pygame.draw.circle(surf, dark, (cx, cy + 1), r)
    for cx, cy, r in ((5, 8, 3), (11, 8, 3), (8, 5, 4)):
        pygame.draw.circle(surf, green, (cx, cy), r)
    for _ in range(6):
        x, y = rng.randrange(4, 12), rng.randrange(2, 9)
        surf.set_at((x, y), light)
    for x, y in ((6, 8), (10, 6), (9, 10)):
        surf.set_at((x, y), (196, 58, 52))
    return scale(outline(surf, OUTLINE))


@cached
def tree_trunk(w: int = 1, h: int = 1) -> pygame.Surface:
    """Gnarled olive trunk with spreading roots."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    ellipse_shadow(surf, (0, ph - 6, pw, 6), alpha=90)
    trunk = [(5, 0), (11, 0), (10, 5), (11, 10), (13, 14), (3, 14), (5, 10), (6, 5)]
    pygame.draw.polygon(surf, OLIVE_BARK, trunk)
    pygame.draw.line(surf, OLIVE_BARK_DARK, (9, 0), (8, 6))
    pygame.draw.line(surf, OLIVE_BARK_DARK, (8, 6), (9, 12))
    pygame.draw.line(surf, OLIVE_BARK_DARK, (6, 2), (7, 4))
    pygame.draw.line(surf, shade(OLIVE_BARK, 0.2), (6, 1), (6, 3))
    pygame.draw.line(surf, OLIVE_BARK_DARK, (4, 13), (12, 13))
    return scale(outline(surf, OUTLINE))


@cached
def tree_canopy(w: int, h: int) -> pygame.Surface:
    """Silvery-green olive crown built from overlapping leaf clumps."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("canopy", w, h)
    crown_rect = pygame.Rect(2, 2, pw - 4, ph - 4)
    pygame.draw.ellipse(surf, OLIVE_LEAF_DARK, crown_rect)
    # Clumps scattered over the crown ellipse, larger toward the middle
    clumps = []
    while len(clumps) < w * h * 5:
        r = rng.randrange(4, 7)
        cx = rng.randrange(r, pw - r)
        cy = rng.randrange(r, ph - r)
        nx = (cx - crown_rect.centerx) / (crown_rect.w / 2)
        ny = (cy - crown_rect.centery) / (crown_rect.h / 2)
        if nx * nx + ny * ny <= 0.75:
            clumps.append((cx, cy, r))
    clumps.sort(key=lambda c: c[1])  # paint back-to-front
    # Dark underside, mid body, then light tops: gives each clump volume
    for cx, cy, r in clumps:
        pygame.draw.circle(surf, OLIVE_LEAF_DARK, (cx, cy + 1), r)
    for cx, cy, r in clumps:
        pygame.draw.circle(surf, OLIVE_LEAF, (cx, cy - 1), r - 1)
    for cx, cy, r in clumps:
        pygame.draw.circle(surf, OLIVE_LEAF_LIGHT, (cx - 1, cy - r // 2 - 1), max(1, r // 3))
    # Leaf texture and a few olives, only on the crown itself
    crown = pygame.mask.from_surface(surf, 1)
    for count, color in ((pw * ph // 25, OLIVE_LEAF_DARK), (w * 2, (70, 62, 80))):
        for _ in range(count):
            x, y = rng.randrange(pw), rng.randrange(ph)
            if crown.get_at((x, y)):
                surf.set_at((x, y), color)
    return scale(outline(surf, OUTLINE))


OBJECT_GENERATORS: dict[str, Callable[[int, int], pygame.Surface]] = {
    "stone_wall": stone_wall,
    "house_wall": house_wall,
    "house_roof": house_roof,
    "house_door": house_door,
    "temple": temple,
    "fence": fence,
    "boulder": boulder,
    "bush": bush,
    "tree_trunk": tree_trunk,
    "tree_canopy": tree_canopy,
}

# Objects drawn above characters (the player can walk "under" them)
OVERHEAD_OBJECTS = {"tree_canopy"}
