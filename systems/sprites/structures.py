"""Built things: houses, the terrace stone wall, fences and the temple.

Houses and walls are baked into the ground layer. Fences are drawn per tile
(``fence_piece``) and connect to neighbouring fence tiles, so corners, ends
and junctions get proper posts.
"""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites.pixel_art import (
    cached, lerp, outline, scale, seeded, shade,
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
MARBLE = (242, 239, 234)
MARBLE_SHADE = (205, 200, 192)
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
    pygame.draw.line(surf, PLASTER_SHADE, (x - 1, y + 7), (x + 5, y + 7))
    if flowers:
        # A terracotta pot of geraniums on the sill
        pygame.draw.rect(surf, TERRACOTTA, (x + 1, y + 4, 3, 2))
        surf.set_at((x + 3, y + 5), TERRACOTTA_DARK)
        for fx, fy, color in ((x + 1, y + 3, LEAF), (x + 3, y + 3, LEAF),
                              (x + 1, y + 2, GERANIUM), (x + 2, y + 3, GERANIUM),
                              (x + 3, y + 2, shade(GERANIUM, 0.3))):
            surf.set_at((fx, fy), color)


@cached
def house_wall(w: int, h: int, variant: int = 0) -> pygame.Surface:
    """Whitewashed wall: eave shadow, plaster texture, windows, stone plinth."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("house_wall", w, h, variant)
    surf.fill(PLASTER)

    # Soft, uneven whitewash: faint blotches and a few worn patches
    for _ in range(pw * ph // 28):
        x, y = rng.randrange(pw), rng.randrange(ph)
        color = rng.choice((PLASTER_LIGHT, lerp(PLASTER, PLASTER_SHADE, 0.4)))
        surf.set_at((x, y), color)
    for _ in range(w // 3):
        x, y = rng.randrange(4, pw - 6), rng.randrange(5, ph - 5)
        pygame.draw.line(surf, lerp(PLASTER, PLASTER_SHADE, 0.6), (x, y), (x + 2, y))
        surf.set_at((x + 1, y + 1), lerp(PLASTER, STONE, 0.5))

    # Shadow under the roof overhang, dithered at its lower edge
    pygame.draw.rect(surf, PLASTER_DEEP, (0, 0, pw, 2))
    pygame.draw.line(surf, PLASTER_SHADE, (0, 2), (pw, 2))
    for x in range(0, pw, 2):
        surf.set_at((x, 3), PLASTER_SHADE)

    # Corners: lit on the left, shaded on the right
    pygame.draw.line(surf, PLASTER_LIGHT, (0, 3), (0, ph))
    pygame.draw.line(surf, PLASTER_SHADE, (pw - 2, 2), (pw - 2, ph))
    pygame.draw.line(surf, PLASTER_DEEP, (pw - 1, 0), (pw - 1, ph))

    # Stone plinth
    pygame.draw.rect(surf, STONE, (0, ph - 3, pw, 3))
    pygame.draw.line(surf, STONE_LIGHT, (0, ph - 3), (pw, ph - 3))
    pygame.draw.line(surf, STONE_DARK, (0, ph - 1), (pw, ph - 1))
    for x in range(rng.randint(2, 5), pw, 7):
        surf.set_at((x, ph - 2), STONE_DARK)

    if w >= 3:
        win_y = ph - 12
        for i, tile_x in enumerate((0, w - 1)):
            _window(surf, tile_x * T + 6, win_y, flowers=(i + variant) % 2 == 0)
    return scale(surf)


def house_wall_shadow(w: int, h: int, variant: int = 0) -> Shapes:
    pw, ph = w * T, h * T
    return [("rect", (2, ph, pw, 3)), ("rect", (pw, 3, 3, ph))]


@cached
def house_roof(w: int, h: int, variant: int = 0) -> pygame.Surface:
    """Greek terracotta roof: rows of curved cover tiles, ridge and antefixes."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("house_roof", w, h, variant)
    period, course = 6, 5
    ridge_h, eave_h = 4, 4
    surf.fill(TERRACOTTA_DARK)

    # Courses of flat pan tiles (tegulae) with curved cover tiles (imbrices)
    # over the joints; every tile is a little different in hue.
    for y in range(ridge_h, ph - eave_h, course):
        light_bias = 0.1 * (1 - y / ph)          # tiles near the ridge catch more sun
        for x in range(0, pw, period):
            tint = rng.uniform(-0.07, 0.07) + light_bias
            pan = shade(TERRACOTTA_DARK, tint)
            pygame.draw.rect(surf, pan, (x + 3, y, 3, course))
            pygame.draw.line(surf, shade(pan, 0.1), (x + 3, y), (x + 5, y))      # overlap lip
            surf.set_at((x + 3, y + 1), shade(pan, -0.25))                       # cover's shadow
            cover = shade(TERRACOTTA, tint)
            pygame.draw.rect(surf, cover, (x, y, 3, course))
            pygame.draw.line(surf, shade(cover, 0.3), (x, y), (x, y + course - 1))
            pygame.draw.line(surf, shade(cover, -0.22), (x + 2, y), (x + 2, y + course - 1))
            surf.set_at((x + 1, y), shade(cover, 0.15))                          # rounded end
            pygame.draw.line(surf, shade(cover, -0.18), (x, y + course - 1),
                             (x + 2, y + course - 1))

    # Ridge: a row of rounded ridge tiles
    pygame.draw.rect(surf, TERRACOTTA_DEEP, (0, 0, pw, ridge_h))
    for x in range(0, pw, 4):
        pygame.draw.rect(surf, TERRACOTTA, (x, 0, 3, ridge_h - 1))
        pygame.draw.line(surf, TERRACOTTA_GLOW, (x, 0), (x + 1, 0))
        surf.set_at((x + 2, ridge_h - 2), TERRACOTTA_DARK)

    # Eave: antefixes (little palmette end tiles) over a dark overhang
    eave_y = ph - eave_h
    pygame.draw.rect(surf, TERRACOTTA_DARK, (0, eave_y, pw, eave_h))
    pygame.draw.line(surf, TERRACOTTA_DEEP, (0, ph - 1), (pw, ph - 1))
    for x in range(0, pw, period):
        pygame.draw.rect(surf, TERRACOTTA_LIGHT, (x, eave_y, 3, 2))
        surf.set_at((x + 1, eave_y + 2), TERRACOTTA_LIGHT)
        surf.set_at((x + 1, eave_y), TERRACOTTA_GLOW)

    # Gable ends: lit barge board on the left, shaded on the right
    pygame.draw.rect(surf, TERRACOTTA_LIGHT, (0, 0, 2, ph - 1))
    pygame.draw.line(surf, TERRACOTTA_GLOW, (0, 0), (0, ph - 2))
    pygame.draw.rect(surf, TERRACOTTA_DEEP, (pw - 2, 0, 2, ph))
    return scale(outline(surf, OUTLINE))


@cached
def house_door(w: int = 1, h: int = 1, variant: int = 0) -> pygame.Surface:
    """Plank door with a bronze ring, set in a stone frame above a step."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    frame = pygame.Rect(pw // 2 - 6, 1, 12, ph - 3)
    door = pygame.Rect(frame.x + 2, frame.y + 3, frame.w - 4, frame.h - 3)

    pygame.draw.rect(surf, STONE, frame)
    pygame.draw.line(surf, STONE_LIGHT, frame.topleft, (frame.left, frame.bottom - 1))
    pygame.draw.line(surf, STONE_DARK, (frame.right - 1, frame.top),
                     (frame.right - 1, frame.bottom))
    pygame.draw.rect(surf, STONE_LIGHT, (frame.left - 1, frame.top, frame.w + 2, 2))  # lintel
    pygame.draw.line(surf, STONE_DARK, (frame.left - 1, frame.top + 2),
                     (frame.right, frame.top + 2))

    pygame.draw.rect(surf, WOOD, door)
    for x in range(door.left + 2, door.right - 1, 2):
        pygame.draw.line(surf, WOOD_DARK, (x, door.top + 1), (x, door.bottom - 1))
    pygame.draw.line(surf, WOOD_LIGHT, (door.left, door.top + 1), (door.left, door.bottom - 1))
    pygame.draw.line(surf, shade(WOOD_DARK, -0.3), door.topleft, (door.right - 1, door.top))
    for y in (door.top + 3, door.bottom - 3):   # cross battens
        pygame.draw.line(surf, WOOD_DARK, (door.left, y), (door.right - 1, y))
    ring = (door.right - 3, door.centery)
    surf.set_at(ring, BRONZE)
    surf.set_at((ring[0], ring[1] + 1), shade(BRONZE, -0.35))

    # Threshold step
    pygame.draw.rect(surf, STONE_LIGHT, (frame.left - 1, ph - 3, frame.w + 2, 2))
    pygame.draw.line(surf, STONE_DARK, (frame.left - 1, ph - 1), (frame.right, ph - 1))
    return scale(surf)


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

@cached
def temple(w: int, h: int, variant: int = 0) -> pygame.Surface:
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


def temple_shadow(w: int, h: int, variant: int = 0) -> Shapes:
    pw, ph = w * T, h * T
    return [("rect", (3, ph, pw - 2, 3)), ("rect", (pw, 12, 3, ph - 12))]
