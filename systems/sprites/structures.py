"""Built things: houses, the terrace stone wall, fences, the temple, props.

Houses and walls are baked into the ground layer. Fences are drawn per tile
(``fence_piece``) and connect to neighbouring fence tiles, so corners, ends
and junctions get proper posts.
"""

from __future__ import annotations

import math

import pygame

import settings as s
from systems.sprites.pixel_art import (
    cached, lerp, outline, scale, seeded, shade, stamp,
)

T = s.TILE_SIZE
OUTLINE = (45, 34, 28)

# ── Palette ──────────────────────────────────────────────────────────────────
PLASTER = (238, 230, 210)
PLASTER_LIGHT = (250, 246, 234)
PLASTER_SHADE = (214, 202, 178)
PLASTER_DEEP = (186, 172, 148)
TERRACOTTA = (190, 106, 78)
TERRACOTTA_DARK = (146, 72, 56)
TERRACOTTA_DEEP = (108, 52, 44)
TERRACOTTA_LIGHT = (218, 140, 104)
TERRACOTTA_GLOW = (238, 172, 128)
WOOD = (110, 74, 52)
WOOD_DARK = (74, 48, 36)
WOOD_LIGHT = (146, 104, 72)
SHUTTER = (74, 116, 146)
SHUTTER_DARK = (50, 82, 110)
WINDOW = (46, 38, 46)
BRONZE = (200, 156, 72)
MARBLE = (240, 234, 220)
MARBLE_LIGHT = (252, 250, 242)
MARBLE_SHADE = (200, 192, 178)
MARBLE_DEEP = (150, 142, 134)
PAINT_BLUE = (62, 98, 150)
PAINT_BLUE_DARK = (40, 66, 110)
PAINT_RED = (176, 84, 62)
GOLD = (212, 168, 68)
CELLA = (52, 44, 52)
WATER = (40, 62, 84)
WALL_WASHES = (  # variant → (wash, light, shade, deep)
    ((238, 230, 210), (250, 246, 234), (214, 202, 178), (186, 172, 148)),
    ((228, 204, 160), (242, 222, 184), (204, 178, 134), (172, 146, 106)),
    ((234, 212, 196), (246, 230, 218), (210, 186, 170), (178, 152, 138)),
)
STONE = (170, 156, 128)
STONE_DARK = (122, 110, 90)
STONE_DEEP = (84, 74, 62)
STONE_LIGHT = (200, 188, 160)
TERRACE_GRASS_DARK = (80, 114, 60)
TERRACE_GRASS_LIGHT = (124, 158, 88)
FENCE = (186, 160, 118)
FENCE_DARK = (132, 108, 76)
FENCE_LIGHT = (218, 198, 156)
GERANIUM = (214, 64, 60)
LEAF = (76, 120, 56)
MOSS = (96, 124, 64)

Shapes = list[tuple[str, tuple[int, int, int, int]]]


def _canvas(w: int, h: int) -> pygame.Surface:
    return pygame.Surface((w * T, h * T), pygame.SRCALPHA)


# ── House ────────────────────────────────────────────────────────────────────

def _masked(dest: pygame.Surface, pattern: pygame.Surface, points: list) -> None:
    """Blit ``pattern`` onto ``dest`` only inside the polygon ``points``."""
    layer = pattern.copy()
    mask = pygame.Surface(pattern.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), points)
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    dest.blit(layer, (0, 0))


def _roof_tiles(size: tuple[int, int], tint: float, seed: object) -> pygame.Surface:
    """Rows of curved cover tiles over flat pans, tinted for one roof face."""
    rng = seeded("roof_tiles", size, tint, seed)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    period, course = 6, 5
    surf.fill(shade(TERRACOTTA_DARK, tint))
    for y in range(-1, size[1], course):
        for x in range(0, size[0], period):
            t = tint + rng.uniform(-0.06, 0.06)
            pan, cover = shade(TERRACOTTA_DARK, t), shade(TERRACOTTA, t)
            pygame.draw.rect(surf, pan, (x + 3, y, 3, course))
            pygame.draw.line(surf, shade(pan, 0.12), (x + 3, y), (x + 5, y))
            pygame.draw.rect(surf, cover, (x, y, 3, course))
            pygame.draw.line(surf, shade(cover, 0.3), (x, y), (x, y + course - 1))
            pygame.draw.line(surf, shade(cover, -0.22), (x + 2, y), (x + 2, y + course - 1))
            pygame.draw.line(surf, shade(cover, -0.15), (x, y + course - 1),
                             (x + 2, y + course - 1))
    return surf


def _window(surf: pygame.Surface, x: int, y: int, flowers: bool) -> None:
    """A small window with open blue shutters, wooden lintel and stone sill.

    ``(x, y)`` is the top-left of the 5×6 opening.
    """
    pygame.draw.rect(surf, WINDOW, (x, y, 5, 6))
    pygame.draw.line(surf, shade(WINDOW, 0.25), (x, y + 5), (x + 4, y + 5))
    surf.set_at((x + 1, y + 1), shade(WINDOW, 0.35))  # glint of the dark room
    for sx in (x - 3, x + 6):
        pygame.draw.rect(surf, SHUTTER, (sx, y, 2, 6))
        pygame.draw.line(surf, SHUTTER_DARK, (sx + 1, y), (sx + 1, y + 5))
        for sy in (y + 1, y + 3):
            surf.set_at((sx, sy), SHUTTER_DARK)
    pygame.draw.line(surf, WOOD, (x - 1, y - 1), (x + 5, y - 1))
    pygame.draw.line(surf, STONE_LIGHT, (x - 1, y + 6), (x + 5, y + 6))
    if flowers:
        # A terracotta pot of geraniums on the sill
        pygame.draw.rect(surf, TERRACOTTA, (x + 1, y + 4, 3, 2))
        surf.set_at((x + 3, y + 5), TERRACOTTA_DARK)
        for fx, fy, color in ((x + 1, y + 3, LEAF), (x + 3, y + 3, LEAF),
                              (x + 1, y + 2, GERANIUM), (x + 2, y + 3, GERANIUM),
                              (x + 3, y + 2, shade(GERANIUM, 0.3))):
            surf.set_at((fx, fy), color)


_AMPHORA = [  # a clay storage jar with a painted black band
    "..LLl..",
    "...d...",
    ".dlLld.",
    "dlLlllD",
    "dkkkkkD",
    ".lllld.",
    ".dllDD.",
    "..dDD..",
    "...D...",
]
_AMPHORA_PALETTE = {"L": TERRACOTTA_GLOW, "l": TERRACOTTA, "d": TERRACOTTA_DARK,
                    "D": TERRACOTTA_DEEP, "k": (60, 40, 36)}


def _amphora(surf: pygame.Surface, x: int, y: int, tall: bool) -> None:
    """A clay jar standing with its foot centered at (x, y); short jars lose the neck."""
    rows = _AMPHORA if tall else _AMPHORA[2:]
    stamp(surf, rows, _AMPHORA_PALETTE, (x - 3, y - len(rows) + 1))


@cached
def house(w: int = 6, h: int = 4, variant: int = 0, door: int | None = None) -> pygame.Surface:
    """Village house in 3/4 view: hipped terracotta roof over a washed wall.

    ``door`` is the door's tile column (default: the middle); ``variant``
    picks the wall wash and the small details (flowers, jars, a vine).
    """
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("house", w, h, variant)
    wash, wash_light, wash_shade, wash_deep = WALL_WASHES[variant % len(WALL_WASHES)]
    roof_h = round(ph * 0.55)
    wall = pygame.Rect(2, roof_h - 2, pw - 4, ph - roof_h + 2)

    # Wall: uneven wash, lit left corner, shaded right corner, stone plinth
    pygame.draw.rect(surf, wash, wall)
    for _ in range(wall.w * wall.h // 24):
        x, y = rng.randrange(wall.left, wall.right), rng.randrange(wall.top, wall.bottom)
        surf.set_at((x, y), rng.choice((wash_light, lerp(wash, wash_shade, 0.5))))
    pygame.draw.line(surf, wash_light, (wall.left, wall.top), (wall.left, wall.bottom))
    pygame.draw.rect(surf, wash_shade, (wall.right - 3, wall.top, 2, wall.h))
    pygame.draw.line(surf, wash_deep, (wall.right - 1, wall.top), (wall.right - 1, wall.bottom))
    pygame.draw.rect(surf, wash_deep, (wall.left, roof_h, wall.w, 3))         # eave shadow
    for x in range(wall.left, wall.right, 2):
        surf.set_at((x, roof_h + 3), wash_shade)
    for x in range(wall.left + 3, wall.right - 3, 6):                          # rafter ends
        pygame.draw.rect(surf, WOOD, (x, roof_h, 2, 2))
        surf.set_at((x, roof_h), WOOD_LIGHT)
    plinth = pygame.Rect(wall.left, ph - 4, wall.w, 4)
    pygame.draw.rect(surf, STONE, plinth)
    pygame.draw.line(surf, STONE_LIGHT, plinth.topleft, (plinth.right - 1, plinth.top))
    pygame.draw.line(surf, STONE_DARK, (plinth.left, ph - 1), (plinth.right - 1, ph - 1))
    for x in range(plinth.left + rng.randint(2, 5), plinth.right, 6):
        surf.set_at((x, ph - 3), STONE_DARK)

    # Door: plank door in a stone frame, with a lintel and a worn step
    door_col = w // 2 if door is None else max(0, min(w - 1, door))
    frame = pygame.Rect(door_col * T + 2, roof_h + 4, 12, ph - roof_h - 5)
    pygame.draw.rect(surf, STONE, frame)
    pygame.draw.line(surf, STONE_LIGHT, frame.topleft, (frame.left, frame.bottom - 1))
    pygame.draw.rect(surf, STONE_LIGHT, (frame.left - 1, frame.top - 1, frame.w + 2, 3))
    leaf = frame.inflate(-4, -2).move(0, 1)
    pygame.draw.rect(surf, WOOD, leaf)
    for x in range(leaf.left + 2, leaf.right - 1, 2):
        pygame.draw.line(surf, WOOD_DARK, (x, leaf.top + 1), (x, leaf.bottom - 1))
    pygame.draw.line(surf, WOOD_LIGHT, (leaf.left, leaf.top), (leaf.left, leaf.bottom - 1))
    pygame.draw.line(surf, shade(WOOD_DARK, -0.3), leaf.topleft, (leaf.right - 1, leaf.top))
    for y in (leaf.top + 4, leaf.bottom - 5):
        pygame.draw.line(surf, WOOD_DARK, (leaf.left, y), (leaf.right - 1, y))
    surf.set_at((leaf.right - 3, leaf.centery), BRONZE)
    pygame.draw.rect(surf, STONE_LIGHT, (frame.left - 2, ph - 3, frame.w + 4, 2))

    # Windows on the tiles left and right of the door
    for col in (door_col - 2, door_col + 2) if w >= 5 else (door_col - 1, door_col + 1):
        if 0 <= col < w:
            _window(surf, col * T + 5, roof_h + 6, flowers=(col + variant) % 2 == 0)
    if variant % 2 == 0:                       # storage jars by the door
        _amphora(surf, frame.right + 4, ph - 2, tall=True)
    if variant % 3 == 1:                       # a vine climbing the left corner
        for y in range(roof_h + 2, ph - 3):
            x = wall.left + 2 + round(math.sin(y * 0.7) * 1.5)
            surf.set_at((x, y), LEAF if y % 3 else shade(LEAF, 0.25))
        for gy in (roof_h + 6, roof_h + 12):
            surf.set_at((wall.left + 4, gy), (96, 60, 110))

    # Hipped roof: back slope, two hips and the big front slope, each its own shade
    # (1px margin all round so the outline is never clipped)
    ridge_y = round(roof_h * 0.3)
    inset = round(roof_h * 0.62)
    l, t, r, b = 1, 1, pw - 2, roof_h - 1
    faces = [
        (-0.28, [(l, t), (r, t), (r - inset, ridge_y), (inset, ridge_y)]),        # back
        (0.14, [(l, t), (inset, ridge_y), (l, b)]),                              # left hip
        (-0.2, [(r, t), (r - inset, ridge_y), (r, b)]),                          # right hip
        (0.0, [(inset, ridge_y), (r - inset, ridge_y), (r, b), (l, b)]),         # front
    ]
    for tint, points in faces:
        _masked(surf, _roof_tiles((pw, roof_h), tint, (w, h, variant)), points)
    # Ridge and hip caps
    for start, stop in (((inset, ridge_y), (l, b)), ((r - inset, ridge_y), (r, b))):
        pygame.draw.line(surf, TERRACOTTA_LIGHT, start, stop, 2)
        pygame.draw.line(surf, TERRACOTTA_DEEP, (start[0], start[1] + 2), (stop[0], stop[1] + 1))
    pygame.draw.line(surf, TERRACOTTA_DEEP, (inset, ridge_y + 1), (r - inset, ridge_y + 1))
    for x in range(inset, r - inset + 1, 3):
        pygame.draw.line(surf, TERRACOTTA_GLOW, (x, ridge_y - 1), (x + 1, ridge_y - 1))
        surf.set_at((x, ridge_y), TERRACOTTA_LIGHT)
    # Front eave with antefixes
    pygame.draw.line(surf, TERRACOTTA_DEEP, (l, b), (r, b))
    for x in range(3, r - 2, 6):
        pygame.draw.rect(surf, TERRACOTTA_LIGHT, (x, b - 2, 3, 2))
        surf.set_at((x + 1, b - 2), TERRACOTTA_GLOW)
    return scale(outline(surf, OUTLINE))


def house_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(2, 8, pw - 4, ph - 9)]


def building_shadow(w: int, h: int, variant: int = 0) -> Shapes:
    pw, ph = w * T, h * T
    return [("rect", (3, ph, pw - 2, 3)), ("rect", (pw - 1, 8, 3, ph - 6))]


# ── Terrace stone wall ───────────────────────────────────────────────────────

@cached
def stone_wall(w: int, h: int, variant: int = 0) -> pygame.Surface:
    """Dry-stone terrace wall: capstones and a face of rough fieldstones.

    On walls taller than the face, the top stays transparent so the map's
    grass reads as the raised bank behind the wall.
    """
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("stone_wall", w, h, variant)
    face_h = min(ph - 4, 28)
    cap_y = ph - face_h - 4

    # Capstones: flat slabs seen from above, with weeds poking up behind
    x = -rng.randint(0, 4)
    while x < pw:
        slab = rng.randint(6, 11)
        tone = shade(STONE_LIGHT, rng.uniform(-0.08, 0.08))
        pygame.draw.rect(surf, tone, (x, cap_y, slab - 1, 4), border_radius=1)
        pygame.draw.line(surf, shade(tone, 0.25), (x + 1, cap_y), (x + slab - 3, cap_y))
        pygame.draw.line(surf, STONE_DARK, (x + slab - 1, cap_y + 1), (x + slab - 1, cap_y + 3))
        x += slab
    if cap_y > 1:
        for _ in range(w * 2):
            gx = rng.randrange(1, pw - 1)
            surf.set_at((gx, cap_y - 1), TERRACE_GRASS_DARK)
            surf.set_at((gx + 1, cap_y - 2), TERRACE_GRASS_LIGHT)
    pygame.draw.line(surf, STONE_DEEP, (0, cap_y + 4), (pw, cap_y + 4))  # overhang shadow

    # Face: rough stones of mixed size, packed with dark mortarless joints
    face = pygame.Rect(0, cap_y + 5, pw, ph - cap_y - 5)
    pygame.draw.rect(surf, STONE_DEEP, face)
    taken = pygame.mask.Mask((pw, ph))
    for attempt in range(pw * face.h // 2):
        big = attempt < pw * face.h // 6       # big stones first, then fill the gaps
        rect = pygame.Rect(rng.randrange(-3, pw - 2), rng.randrange(face.top - 2, ph - 2),
                           rng.randint(6, 11) if big else rng.randint(3, 6),
                           rng.randint(4, 7) if big else rng.randint(3, 4)).clip(face)
        if rect.w < 3 or rect.h < 3:
            continue
        probe = pygame.mask.Mask((rect.w + 1, rect.h + 1), fill=True)
        if taken.overlap(probe, (rect.x - 1, rect.y - 1)):
            continue
        taken.draw(pygame.mask.Mask(rect.size, fill=True), rect.topleft)
        depth = (rect.centery - face.top) / max(1, face.h)
        tone = shade(STONE, rng.uniform(-0.12, 0.12) - depth * 0.15)
        pygame.draw.rect(surf, tone, rect, border_radius=2)
        pygame.draw.line(surf, shade(tone, 0.28), (rect.left + 1, rect.top),
                         (rect.right - 2, rect.top))
        pygame.draw.line(surf, shade(tone, 0.12), (rect.left, rect.top + 1),
                         (rect.left, rect.bottom - 2))
        pygame.draw.line(surf, shade(tone, -0.22), (rect.left + 1, rect.bottom - 1),
                         (rect.right - 2, rect.bottom - 1))
        if depth > 0.55 and rng.random() < 0.35:     # moss on damp lower stones
            surf.set_at((rect.left + 1, rect.top), MOSS)
            surf.set_at((rect.left + 2, rect.top), lerp(MOSS, tone, 0.4))
    # Small chinking stones wedged into the larger gaps
    for _ in range(pw * face.h // 10):
        x, y = rng.randrange(1, pw - 2), rng.randrange(face.top + 1, ph - 1)
        if not taken.get_at((x, y)) and not taken.get_at((x + 1, y)):
            surf.set_at((x, y), STONE_DARK)
            surf.set_at((x + 1, y), shade(STONE_DARK, 0.15))

    # A caper bush rooted in a joint, very Greek
    if w >= 4:
        cx = rng.randrange(8, pw - 8)
        cy = face.top + 3 + rng.randrange(0, max(1, face.h - 12))
        for dx, dy in ((0, 0), (-1, 1), (1, 1), (-2, 2), (2, 2), (0, 2), (-1, 3), (1, 3)):
            surf.set_at((cx + dx, cy + dy), LEAF if (dx + dy) % 2 else shade(LEAF, 0.2))
        surf.set_at((cx, cy - 1), (240, 220, 236))
        surf.set_at((cx + 1, cy - 1), (210, 150, 200))
    return scale(surf)


def stone_wall_shadow(w: int, h: int, variant: int = 0) -> Shapes:
    pw, ph = w * T, h * T
    return [("rect", (2, ph, pw - 1, 3))]


# ── Fences (connected per tile) ──────────────────────────────────────────────

Links = tuple[bool, bool, bool, bool]   # (north, east, south, west) neighbours


def _post(surf: pygame.Surface, heavy: bool) -> None:
    if heavy:
        # Corner and end posts: stout, with a pointed cap
        pygame.draw.rect(surf, FENCE, (6, 3, 5, 11))
        pygame.draw.line(surf, FENCE_LIGHT, (6, 3), (6, 13))
        pygame.draw.rect(surf, FENCE_DARK, (9, 3, 2, 11))
        pygame.draw.line(surf, FENCE_LIGHT, (7, 2), (9, 2))
        surf.set_at((8, 1), FENCE_LIGHT)
        pygame.draw.line(surf, FENCE_DARK, (6, 6), (10, 6))   # lashing
    else:
        pygame.draw.rect(surf, FENCE, (7, 3, 3, 11))
        pygame.draw.line(surf, FENCE_LIGHT, (7, 3), (7, 13))
        pygame.draw.line(surf, FENCE_DARK, (9, 3), (9, 13))
        pygame.draw.line(surf, FENCE_LIGHT, (7, 3), (9, 3))
    left, right = (6, 10) if heavy else (7, 9)
    pygame.draw.line(surf, shade(FENCE_DARK, -0.2), (left, 13), (right, 13))


@cached
def fence_piece(links: Links, variant: int = 0) -> pygame.Surface:
    """One fence tile: a post with rails toward each linked neighbour."""
    surf = pygame.Surface((T, T), pygame.SRCALPHA)
    north, east, south, west = links
    horizontal, vertical = east or west, north or south

    if vertical:
        y0, y1 = (0 if north else 6), (T if south else 12)
        pygame.draw.rect(surf, FENCE, (7, y0, 3, y1 - y0))
        pygame.draw.line(surf, FENCE_LIGHT, (7, y0), (7, y1 - 1))
        pygame.draw.line(surf, FENCE_DARK, (9, y0), (9, y1 - 1))
    if horizontal:
        x0, x1 = (0 if west else 8), (T if east else 9)
        for rail_y in (5, 9):
            pygame.draw.line(surf, FENCE_LIGHT, (x0, rail_y), (x1 - 1, rail_y))
            pygame.draw.line(surf, FENCE_DARK, (x0, rail_y + 1), (x1 - 1, rail_y + 1))
    straight = (horizontal and not vertical and east and west) or \
        (vertical and not horizontal and north and south)
    _post(surf, heavy=not straight)
    return scale(outline(surf, OUTLINE))


def fence_footprint(links: Links) -> list[tuple[int, int, int, int]]:
    north, east, south, west = links
    rects = [(6, 9, 5, 5)]
    if east or west:
        x0, x1 = (0 if west else 6), (T if east else 11)
        rects.append((x0, 9, x1 - x0, 5))
    if north or south:
        y0, y1 = (0 if north else 9), (T if south else 14)
        rects.append((6, y0, 5, y1 - y0))
    return rects


def fence_shadow(links: Links, variant: int = 0) -> Shapes:
    north, east, south, west = links
    shapes: Shapes = [("ellipse", (7, 12, 6, 3))]
    if east or west:
        x0, x1 = (1 if west else 9), (T + 1 if east else 10)
        shapes.append(("rect", (x0, 13, x1 - x0, 2)))
    if north or south:
        y0, y1 = (1 if north else 9), (T + 1 if south else 14)
        shapes.append(("rect", (10, y0, 2, y1 - y0)))
    return shapes


# ── Temple ───────────────────────────────────────────────────────────────────

_OWL = [  # Athena's owl, painted in the pediment
    "g.g",
    "ggg",
    "gwg",
    ".g.",
]


@cached
def temple(w: int = 7, h: int = 6, variant: int = 0) -> pygame.Surface:
    """Doric temple from the front and above: steps, columns, painted frieze,
    a pediment with Athena's owl and the long tiled roof behind it."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    cx = pw // 2
    steps_h = 9
    col_bottom = ph - steps_h
    col_top = col_bottom - round(ph * 0.32)
    entab_top = col_top - 8
    ped_h = round(pw * 0.16)
    apex = entab_top - ped_h
    depth = round(ph * 0.28)                  # how far the roof recedes on screen

    # Roof: two long slopes running back from the pediment, ridge in the middle
    left_slope = [(1, entab_top), (cx, apex), (cx, apex - depth), (1, entab_top - depth)]
    right_slope = [(pw - 2, entab_top), (cx, apex), (cx, apex - depth),
                   (pw - 2, entab_top - depth)]
    _masked(surf, _roof_tiles((pw, ph), 0.1, ("temple", w, h)), left_slope)
    _masked(surf, _roof_tiles((pw, ph), -0.22, ("temple", w, h)), right_slope)
    pygame.draw.line(surf, TERRACOTTA_LIGHT, (cx, apex - depth), (cx, apex), 2)
    for y in range(apex - depth, apex, 3):
        surf.set_at((cx - 1, y), TERRACOTTA_GLOW)
    pygame.draw.line(surf, TERRACOTTA_DEEP, (1, entab_top - depth), (1, entab_top))
    pygame.draw.line(surf, TERRACOTTA_DEEP, (pw - 2, entab_top - depth), (pw - 2, entab_top))
    for x, y in ((cx, apex - depth - 2), (2, entab_top - depth - 1),
                 (pw - 3, entab_top - depth - 1)):
        pygame.draw.rect(surf, GOLD, (x - 1, y, 3, 2))                     # acroteria

    # Pediment: marble cornice framing a blue tympanum with the owl
    pygame.draw.polygon(surf, MARBLE, [(0, entab_top), (cx, apex - 1), (pw - 1, entab_top)])
    inner = [(5, entab_top - 1), (cx, apex + 3), (pw - 6, entab_top - 1)]
    pygame.draw.polygon(surf, PAINT_BLUE, inner)
    pygame.draw.line(surf, PAINT_BLUE_DARK, inner[0], inner[2])
    stamp(surf, _OWL, {"g": GOLD, "w": MARBLE_LIGHT}, (cx - 1, entab_top - 6))
    pygame.draw.line(surf, MARBLE_LIGHT, (0, entab_top), (cx, apex - 1))
    pygame.draw.line(surf, MARBLE_SHADE, (cx, apex - 1), (pw - 1, entab_top))

    # Entablature: cornice, frieze of triglyphs and metopes, architrave
    pygame.draw.rect(surf, MARBLE_LIGHT, (0, entab_top, pw, 2))
    pygame.draw.line(surf, MARBLE_DEEP, (0, entab_top + 2), (pw - 1, entab_top + 2))
    pygame.draw.rect(surf, MARBLE, (1, entab_top + 3, pw - 2, 5))
    for x in range(3, pw - 4, 6):
        pygame.draw.rect(surf, PAINT_BLUE, (x, entab_top + 3, 2, 3))
        pygame.draw.line(surf, PAINT_BLUE_DARK, (x + 1, entab_top + 3), (x + 1, entab_top + 5))
        surf.set_at((x + 4, entab_top + 4), PAINT_RED)
    pygame.draw.line(surf, MARBLE_SHADE, (1, entab_top + 6), (pw - 2, entab_top + 6))
    pygame.draw.line(surf, MARBLE_DEEP, (1, col_top - 1), (pw - 2, col_top - 1))

    # Dark porch behind the columns, bronze doors with a warm glow inside
    pygame.draw.rect(surf, CELLA, (3, col_top, pw - 6, col_bottom - col_top))
    door = pygame.Rect(cx - 6, col_top + 6, 12, col_bottom - col_top - 6)
    pygame.draw.rect(surf, (120, 82, 44), door)
    pygame.draw.line(surf, (82, 54, 30), door.midtop, (door.centerx, door.bottom - 1))
    pygame.draw.line(surf, (236, 196, 110), (door.centerx, door.top + 2),
                     (door.centerx, door.bottom - 2))
    for y in range(door.top + 2, door.bottom - 1, 4):
        surf.set_at((door.left + 2, y), GOLD)
        surf.set_at((door.right - 3, y), GOLD)

    # Fluted columns with capitals, lit from the left
    n_cols = max(2, w - 1)
    spacing = (pw - 14) / (n_cols - 1)
    for i in range(n_cols):
        x = round(4 + i * spacing)
        pygame.draw.rect(surf, MARBLE, (x, col_top, 6, col_bottom - col_top))
        pygame.draw.line(surf, MARBLE_LIGHT, (x, col_top), (x, col_bottom - 1))
        pygame.draw.line(surf, MARBLE_LIGHT, (x + 2, col_top + 2), (x + 2, col_bottom - 1))
        pygame.draw.line(surf, MARBLE_SHADE, (x + 4, col_top), (x + 4, col_bottom - 1))
        pygame.draw.line(surf, MARBLE_DEEP, (x + 5, col_top), (x + 5, col_bottom - 1))
        pygame.draw.rect(surf, MARBLE_LIGHT, (x - 1, col_top, 8, 2))          # abacus
        pygame.draw.line(surf, MARBLE_SHADE, (x - 1, col_top + 2), (x + 6, col_top + 2))

    # Three steps: lit treads, shaded risers
    for i in range(3):
        y = col_bottom + i * 3
        inset = 2 - i
        pygame.draw.rect(surf, MARBLE_LIGHT, (inset, y, pw - inset * 2, 1))
        pygame.draw.rect(surf, MARBLE_SHADE, (inset, y + 1, pw - inset * 2, 2))
        pygame.draw.line(surf, MARBLE_DEEP, (inset, y + 2), (pw - inset - 1, y + 2))
    return scale(outline(surf, OUTLINE))


def temple_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(1, round(ph * 0.35), pw - 2, ph - round(ph * 0.35) - 1)]


# ── Village props ────────────────────────────────────────────────────────────

@cached
def well(w: int = 2, h: int = 2, variant: int = 0) -> pygame.Surface:
    """Stone well with a wooden frame, rope and bucket."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("well", w, h, variant)
    ring = pygame.Rect(3, ph - 18, pw - 6, 10)
    # Cylinder front: coursed stones below the rim
    pygame.draw.rect(surf, STONE_DARK, (ring.left, ring.centery, ring.w, 8))
    pygame.draw.ellipse(surf, STONE_DARK, (ring.left, ring.centery + 3, ring.w, 9))
    for y in range(ring.centery + 1, ring.centery + 10, 3):
        x = ring.left + 1 + rng.randint(0, 2)
        while x < ring.right - 2:
            pygame.draw.line(surf, STONE, (x, y), (x + 3, y))
            surf.set_at((x, y - 1), STONE_LIGHT)
            x += 5
    # Rim and dark water
    pygame.draw.ellipse(surf, STONE_LIGHT, ring)
    pygame.draw.ellipse(surf, STONE, ring.inflate(-2, -2).move(0, 1))
    pygame.draw.ellipse(surf, WATER, ring.inflate(-6, -4).move(0, 1))
    surf.set_at((ring.centerx - 3, ring.centery), (120, 150, 170))
    # Frame, crossbar, rope and bucket
    for x in (ring.left + 1, ring.right - 3):
        pygame.draw.rect(surf, WOOD, (x, 3, 2, ring.centery - 3))
        pygame.draw.line(surf, WOOD_LIGHT, (x, 3), (x, ring.centery - 1))
    pygame.draw.rect(surf, WOOD_DARK, (ring.left, 3, ring.w, 2))
    pygame.draw.line(surf, WOOD_LIGHT, (ring.left, 3), (ring.right - 1, 3))
    pygame.draw.line(surf, (180, 160, 120), (pw // 2, 5), (pw // 2, 11))
    pygame.draw.rect(surf, WOOD, (pw // 2 - 2, 11, 5, 4))
    pygame.draw.line(surf, WOOD_DARK, (pw // 2 - 2, 12), (pw // 2 + 2, 12))
    return scale(outline(surf, OUTLINE))


def well_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(3, ph - 14, pw - 6, 12)]


@cached
def amphorae(w: int = 1, h: int = 1, variant: int = 0) -> pygame.Surface:
    """A few clay storage jars."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    for i in range(w * 2):
        x = 4 + i * 7 + (variant % 2)
        _amphora(surf, x, ph - 2, tall=(i + variant) % 2 == 0)
    return scale(outline(surf, OUTLINE))


def amphorae_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(1, ph - 6, pw - 2, 5)]


def small_shadow(w: int, h: int, variant: int = 0) -> Shapes:
    pw, ph = w * T, h * T
    return [("ellipse", (2, ph - 5, pw, 5))]
