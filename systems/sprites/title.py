"""Title screen art: an Aegean sunset with a temple headland and Athena's olive.

The scene is painted at logical resolution in layers (sky, sea, headland,
foreground) that the main menu composes every frame together with the
animated bits (stars, clouds, gulls, sea glitter, motes), then scales up.
"""

from __future__ import annotations

import math

import pygame

import settings as s
from systems.sprites.nature import olive_tree_logical
from systems.sprites.pixel_art import cached, lerp, outline, scale, seeded, shade

# Logical canvas: the screen at the world's pixel size, rounded up
WIDTH = -(-s.SCREEN_WIDTH // s.SCALE)
HEIGHT = -(-s.SCREEN_HEIGHT // s.SCALE)
HORIZON = 118
SUN = (150, HORIZON)
SUN_RADIUS = 21

SKY_BANDS = [
    (16, 14, 40), (26, 20, 58), (44, 28, 78), (72, 38, 96), (108, 50, 106),
    (148, 66, 108), (188, 88, 100), (222, 116, 92), (242, 152, 96), (250, 192, 122),
]
SEA_BANDS = [(132, 96, 124), (88, 74, 120), (58, 60, 110), (40, 48, 96), (28, 38, 80),
             (20, 28, 64), (14, 20, 50)]
SUN_CORE = (255, 240, 196)
SUN_RIM = (255, 214, 142)
GLINT = (255, 226, 160)
ISLAND = (92, 56, 100)
ISLAND_LIT = (140, 74, 104)
ROCK = (46, 28, 52)
ROCK_LIT = (132, 70, 82)
ROCK_DARK = (28, 16, 34)
MARBLE_LIT = (252, 210, 164)
MARBLE_MID = (212, 160, 140)
MARBLE_SHADE = (150, 96, 116)
ROOF_LIT = (176, 92, 78)
ROOF_SHADE = (110, 56, 68)
FRIEZE = (76, 70, 122)
CELLA = (54, 30, 52)
GOLD = (236, 190, 96)
LEAF_RIM = (196, 132, 78)
SILHOUETTE_DARK = (20, 16, 30)
SILHOUETTE_LIGHT = (74, 58, 78)
OLIVE_BASE = (40, 150)            # where the title olive's trunk meets the rock
CLOUD = (120, 62, 108)
CLOUD_LIT = (238, 146, 108)
CLOUD_GLOW = (252, 190, 130)
BIRD = (36, 22, 46)

LOGO_SCALE = 5
LOGO_TOP = (255, 244, 190)
LOGO_MID = (240, 180, 60)
LOGO_LOW = (176, 100, 30)
LOGO_OUTLINE = (40, 18, 22)
LOGO_SHADOW = (30, 10, 40)


def _dithered_bands(surf: pygame.Surface, bands: list, top: int, bottom: int) -> None:
    """Horizontal color bands with a checkerboard dither row between neighbours."""
    height = bottom - top
    for i, color in enumerate(bands):
        y0 = top + height * i // len(bands)
        y1 = top + height * (i + 1) // len(bands)
        pygame.draw.rect(surf, color, (0, y0, WIDTH, y1 - y0))
        if i:
            for x in range(y0 % 2, WIDTH, 2):
                surf.set_at((x, y0), bands[i - 1])


@cached
def sky() -> pygame.Surface:
    """Banded dusk sky with the setting sun and its halo."""
    surf = pygame.Surface((WIDTH, HORIZON + 1))
    _dithered_bands(surf, SKY_BANDS, 0, HORIZON + 1)
    # Halo: dithered rings that warm the sky around the sun
    for ring, color in ((52, SKY_BANDS[-3]), (40, SKY_BANDS[-2]), (30, SKY_BANDS[-1])):
        for y in range(SUN[1] - ring, SUN[1] + 1):
            for x in range(SUN[0] - ring, SUN[0] + ring + 1):
                d = math.hypot(x - SUN[0], (y - SUN[1]) * 1.15)
                if d <= ring and (d <= ring - 3 or (x + y) % 2 == 0):
                    if 0 <= x < WIDTH and 0 <= y <= HORIZON:
                        current = surf.get_at((x, y))
                        surf.set_at((x, y), lerp(current, color, 0.55))
    pygame.draw.circle(surf, SUN_RIM, SUN, SUN_RADIUS)
    pygame.draw.circle(surf, SUN_CORE, (SUN[0] - 1, SUN[1] - 1), SUN_RADIUS - 3)
    # The sea cuts the sun's lower half in streaks, as at real sunsets
    for i, y in enumerate(range(SUN[1] - 5, SUN[1] + 1, 2)):
        pygame.draw.line(surf, SKY_BANDS[-1], (SUN[0] - SUN_RADIUS, y),
                         (SUN[0] + SUN_RADIUS, y))
    return surf


@cached
def stars() -> list[tuple[int, int, float]]:
    """(x, y, twinkle phase) for the stars in the high, dark part of the sky."""
    rng = seeded("title_stars")
    return [(rng.randrange(WIDTH), rng.randrange(HORIZON // 2), rng.random() * math.tau)
            for _ in range(42)]


@cached
def islands() -> pygame.Surface:
    """Distant island silhouettes on the horizon, lit on the sun-facing side."""
    surf = pygame.Surface((WIDTH, HORIZON + 1), pygame.SRCALPHA)
    rng = seeded("title_islands")
    for left, right, peak in ((4, 112, 11), (186, 214, 5), (226, WIDTH, 7)):
        pts = [(left, HORIZON)]
        for x in range(left, right + 1, 3):
            t = (x - left) / max(1, right - left)
            h = math.sin(t * math.pi) ** 0.7 * peak + rng.uniform(-1, 1)
            pts.append((x, HORIZON - max(0, round(h))))
        pts.append((right, HORIZON))
        pygame.draw.polygon(surf, ISLAND, pts)
        # Rim light along the ridge, strongest toward the sun
        for x, y in pts[1:-1]:
            if abs(x - SUN[0]) < 90:
                surf.set_at((x, y), lerp(ISLAND_LIT, SUN_RIM, 0.3))
    return surf


@cached
def sea() -> pygame.Surface:
    """The sea with the sun's path baked in: still dashes that widen and fade
    toward the viewer (the menu only lets a few of them sparkle, slowly)."""
    surf = pygame.Surface((WIDTH, HEIGHT - HORIZON))
    _dithered_bands(surf, SEA_BANDS, 0, HEIGHT - HORIZON)
    for y in range(0, 14):
        half = int(SUN_RADIUS * 1.6 * (1 - y / 16))
        for x in range(SUN[0] - half, SUN[0] + half):
            if (x + y) % 2 == 0 or y < 3:
                surf.set_at((x, y), lerp(surf.get_at((x, y)), SKY_BANDS[-2], 0.5))
    rng = seeded("sun_path")
    height = HEIGHT - HORIZON
    for y in range(1, height, 2):
        depth = y / height
        half = SUN_RADIUS * (0.7 + depth * 1.6)
        color = lerp(GLINT, SEA_BANDS[3], depth * 0.9)
        for _ in range(2):
            x = SUN[0] + rng.uniform(-half, half) * (0.5 + 0.5 * rng.random())
            w = rng.randint(1, 4)
            pygame.draw.line(surf, SUN_CORE if depth < 0.1 else color,
                             (round(x - w / 2), y), (round(x + w / 2), y))
    return surf


@cached
def sparkles() -> list[tuple[int, int, int, float]]:
    """(x, y, width, phase) of the few spots on the sun path that slowly glint."""
    rng = seeded("sparkles")
    height = HEIGHT - HORIZON
    spots = []
    for _ in range(7):
        y = rng.randrange(2, height // 2)
        half = SUN_RADIUS * (0.7 + y / height * 1.6)
        spots.append((round(SUN[0] + rng.uniform(-half, half) * 0.7), HORIZON + y,
                      rng.randint(2, 4), rng.random() * math.tau))
    return spots


def _temple(surf: pygame.Surface, x: int, base: int, width: int = 48) -> None:
    """A Doric temple in the last light: the sun side glows, the rest is dusk."""
    cx = x + width // 2
    col_bottom = base - 6
    col_top = col_bottom - 17
    ent_top = col_top - 5
    apex = ent_top - 9
    depth = 6
    # Roof slopes receding behind the pediment
    pygame.draw.polygon(surf, ROOF_LIT, [(x - 1, ent_top), (cx, apex), (cx, apex - depth),
                                         (x - 1, ent_top - depth)])
    pygame.draw.polygon(surf, ROOF_SHADE, [(x + width, ent_top), (cx, apex), (cx, apex - depth),
                                           (x + width, ent_top - depth)])
    pygame.draw.line(surf, MARBLE_LIT, (cx, apex - depth), (cx, apex))
    # Pediment with a dusk-blue tympanum
    pygame.draw.polygon(surf, MARBLE_LIT, [(x - 2, ent_top), (cx, apex), (x + width + 1, ent_top)])
    pygame.draw.polygon(surf, MARBLE_SHADE, [(cx, apex), (x + width + 1, ent_top), (cx, ent_top)])
    pygame.draw.polygon(surf, FRIEZE, [(x + 4, ent_top - 1), (cx, apex + 3),
                                       (x + width - 5, ent_top - 1)])
    for px, py in ((cx, apex - depth - 1), (x - 1, ent_top - depth - 1),
                   (x + width, ent_top - depth - 1)):
        surf.set_at((px, py), GOLD)
    # Entablature: architrave and a frieze of triglyphs
    pygame.draw.rect(surf, MARBLE_LIT, (x - 1, ent_top, width + 2, 2))
    pygame.draw.rect(surf, FRIEZE, (x, ent_top + 2, width, 3))
    for i in range(x + 1, x + width - 1, 4):
        pygame.draw.line(surf, MARBLE_MID, (i, ent_top + 2), (i, ent_top + 4))
    pygame.draw.rect(surf, MARBLE_SHADE, (cx, ent_top, x + width + 1 - cx, 2))
    # Dark porch, a warm glow through the doors, six fluted columns
    pygame.draw.rect(surf, CELLA, (x + 2, col_top, width - 4, col_bottom - col_top))
    pygame.draw.rect(surf, (156, 92, 76), (cx - 3, col_top + 5, 6, col_bottom - col_top - 5))
    pygame.draw.line(surf, (236, 170, 104), (cx, col_top + 6), (cx, col_bottom - 1))
    for i in range(6):
        col_x = x + 1 + round(i * (width - 5) / 5)
        lit = col_x < cx
        pygame.draw.rect(surf, MARBLE_MID, (col_x, col_top, 4, col_bottom - col_top))
        pygame.draw.line(surf, MARBLE_LIT if lit else MARBLE_MID, (col_x, col_top),
                         (col_x, col_bottom - 1))
        pygame.draw.line(surf, MARBLE_SHADE, (col_x + 3, col_top), (col_x + 3, col_bottom - 1))
        pygame.draw.rect(surf, MARBLE_LIT if lit else MARBLE_MID, (col_x - 1, col_top, 6, 1))
    # Three steps
    for i in range(3):
        y = col_bottom + i * 2
        pygame.draw.line(surf, MARBLE_LIT, (x - i, y), (x + width - 1 + i, y))
        pygame.draw.line(surf, MARBLE_SHADE, (x - i, y + 1), (x + width - 1 + i, y + 1))


@cached
def headland() -> pygame.Surface:
    """Cliff on the right with a small temple, catching the last light."""
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    rng = seeded("title_headland")
    top = 96
    pts = [(176, HEIGHT), (184, 160), (190, 132), (198, 112), (206, top + 2), (212, top),
           (WIDTH, top - 2), (WIDTH, HEIGHT)]
    pygame.draw.polygon(surf, ROCK, pts)
    # Lit cliff face (facing the sun) and rock strata
    for x0, y0 in ((184, 160), (190, 132), (198, 112), (206, top + 2)):
        pygame.draw.line(surf, ROCK_LIT, (x0, y0), (x0 + 6, y0 + 10))
    for _ in range(60):
        x, y = rng.randrange(190, WIDTH), rng.randrange(top + 4, HEIGHT)
        if surf.get_at((x, y)).a:
            pygame.draw.line(surf, ROCK_DARK if rng.random() < 0.7 else ROCK_LIT,
                             (x, y), (x + rng.randint(2, 6), y))
    pygame.draw.line(surf, ROCK_LIT, (206, top + 2), (WIDTH, top - 2))
    # Breakers at the foot of the cliff
    for x in range(176, 200, 3):
        surf.set_at((x, HEIGHT - 26 + (x % 2)), (220, 200, 210))

    _temple(surf, 212, top - 1)
    return outline(surf, ROCK_DARK)


@cached
def foreground() -> pygame.Surface:
    """Rocky outcrop with a gnarled olive, dark against the sunset."""
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    rng = seeded("title_olive")
    ground = [(0, 148), (22, 145), (50, 149), (72, 158), (94, 174), (110, HEIGHT),
              (0, HEIGHT)]
    pygame.draw.polygon(surf, ROCK_DARK, ground)
    for (x0, y0), (x1, y1) in zip(ground, ground[1:5]):
        pygame.draw.line(surf, ROCK_LIT, (x0, y0), (x1, y1))
    for _ in range(9):   # dry grass tufts along the edge, leaning in the breeze
        x = rng.randrange(4, 96)
        top = next(y for y in range(HEIGHT) if surf.get_at((x, y)).a)
        for dx in range(rng.randint(2, 4)):
            h = rng.randint(2, 5)
            pygame.draw.line(surf, ROCK_DARK, (x + dx, top), (x + dx + 1, top - h))

    # The olive: the map's olive drawn large, turned into a dusk silhouette
    # with a warm rim where it faces the sun
    olive = olive_tree_logical(6, 6, 2)
    tree = pygame.Surface(olive.get_size(), pygame.SRCALPHA)
    w, h = olive.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = olive.get_at((x, y))
            if a:
                lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
                tree.set_at((x, y), lerp(SILHOUETTE_DARK, SILHOUETTE_LIGHT, lum ** 1.4))
    mask = pygame.mask.from_surface(tree)
    for y in range(h):
        for x in range(w):
            if not mask.get_at((x, y)):
                continue
            open_up = y == 0 or not mask.get_at((x, y - 1))
            open_right = x + 1 >= w or not mask.get_at((x + 1, y))
            if open_up or open_right:
                warmth = 0.45 + 0.55 * x / w
                tree.set_at((x, y), lerp(tree.get_at((x, y)), LEAF_RIM, warmth))
    surf.blit(tree, (OLIVE_BASE[0] - w // 2, OLIVE_BASE[1] - h + 3))
    return surf


@cached
def cloud(length: int, variant: int) -> pygame.Surface:
    """A thin sunset cloud: violet on top, glowing underneath."""
    rng = seeded("title_cloud", length, variant)
    surf = pygame.Surface((length, 8), pygame.SRCALPHA)
    for _ in range(length // 5):
        w = rng.randint(length // 4, length // 2)
        x = rng.randint(0, length - w)
        y = rng.randint(1, 3)
        pygame.draw.ellipse(surf, CLOUD, (x, y, w, 4))
    for x in range(length):
        for y in range(7, 0, -1):
            if surf.get_at((x, y)).a and not surf.get_at((x, y + 1)).a:
                surf.set_at((x, y), CLOUD_LIT)
                if surf.get_at((x, y - 1)).a and x % 3:
                    surf.set_at((x, y - 1), lerp(CLOUD, CLOUD_LIT, 0.5))
                break
    return surf


@cached
def gull(frame: int) -> pygame.Surface:
    """A tiny gull silhouette; frame 0 wings up, frame 1 wings level."""
    rows = ["o...o", ".o.o.", "..o.."] if frame == 0 else [".....", "oo.oo", "..o.."]
    surf = pygame.Surface((5, 3), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "o":
                surf.set_at((x, y), BIRD)
    return surf


# ── Logo ─────────────────────────────────────────────────────────────────────

_LETTERS = {
    "K": ["XXXX...XXXX",
          ".XX.....XX.",
          ".XX....XX..",
          ".XX...XX...",
          ".XX..XX....",
          ".XXXXX.....",
          ".XXXXXX....",
          ".XX..XXX...",
          ".XX...XXX..",
          ".XX....XXX.",
          ".XX.....XX.",
          "XXXX...XXXX"],
    "A": ["....XX.....",
          "....XX.....",
          "...XXXX....",
          "...X.XX....",
          "..XX.XXX...",
          "..X...XX...",
          ".XXXXXXXX..",
          ".X.....XX..",
          "XX.....XXX.",
          "X.......XX.",
          "X.......XX.",
          "XXX...XXXXX"],
    "L": ["XXXX.....",
          ".XX......",
          ".XX......",
          ".XX......",
          ".XX......",
          ".XX......",
          ".XX......",
          ".XX......",
          ".XX......",
          ".XX.....X",
          ".XX....XX",
          "XXXXXXXXX"],
    "I": ["XXXX",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          ".XX.",
          "XXXX"],
    "N": ["XXX....XXXX",
          ".XX.....X..",
          ".XXX....X..",
          ".X.XX...X..",
          ".X.XX...X..",
          ".X..XX..X..",
          ".X..XX..X..",
          ".X...XX.X..",
          ".X...XX.X..",
          ".X....XXX..",
          ".X.....XX..",
          "XXXX....X.."],
    "O": ["...XXXXX...",
          "..XX...XX..",
          ".XX.....XX.",
          "XX.......XX",
          "XX.......XX",
          "XX.......XX",
          "XX.......XX",
          "XX.......XX",
          "XX.......XX",
          ".XX.....XX.",
          "..XX...XX..",
          "...XXXXX..."],
    "S": ["..XXXXX.X",
          ".XX....XX",
          "XX......X",
          "XX.......",
          ".XXX.....",
          "..XXXXX..",
          ".....XXX.",
          ".......XX",
          "X......XX",
          "XX.....XX",
          "XXX...XX.",
          "X.XXXXX.."],
}
_LETTER_GAP = 2


def _logo_mask(text: str) -> pygame.Surface:
    widths = [len(_LETTERS[ch][0]) for ch in text]
    rows = len(_LETTERS["K"])
    surf = pygame.Surface((sum(widths) + _LETTER_GAP * (len(text) - 1), rows), pygame.SRCALPHA)
    x = 0
    for ch, w in zip(text, widths):
        for y, row in enumerate(_LETTERS[ch]):
            for dx, cell in enumerate(row):
                if cell == "X":
                    surf.set_at((x + dx, y), (255, 255, 255))
        x += w + _LETTER_GAP
    return surf


@cached
def logo(text: str = "KALLINOS") -> pygame.Surface:
    """The title in gilded, inscription-style capitals with outline and shadow."""
    mask = _logo_mask(text)
    w, h = mask.get_size()
    letters = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / (h - 1)
        color = lerp(LOGO_TOP, LOGO_MID, t * 2) if t < 0.5 else lerp(LOGO_MID, LOGO_LOW,
                                                                      (t - 0.5) * 2)
        for x in range(w):
            if mask.get_at((x, y)).a:
                above = y > 0 and mask.get_at((x, y - 1)).a
                letters.set_at((x, y), color if above else shade(color, 0.35))
    surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    shadow = pygame.mask.from_surface(mask).to_surface(setcolor=LOGO_SHADOW,
                                                       unsetcolor=(0, 0, 0, 0))
    surf.blit(outline_wide(shadow, LOGO_SHADOW), (2, 2))
    surf.blit(outline_wide(letters, LOGO_OUTLINE), (1, 1))
    return scale(surf, LOGO_SCALE)


def outline_wide(surf: pygame.Surface, color: tuple) -> pygame.Surface:
    """Pad by 1px and outline, so the outline is never clipped at the edges."""
    padded = pygame.Surface((surf.get_width() + 2, surf.get_height() + 2), pygame.SRCALPHA)
    padded.blit(surf, (1, 1))
    return outline(padded, color)


@cached
def logo_silhouette(text: str = "KALLINOS") -> pygame.Surface:
    """White mask of just the letters, aligned with ``logo`` (for the shine sweep)."""
    mask = _logo_mask(text)
    w, h = mask.get_size()
    surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    surf.fill((255, 255, 255, 0))
    surf.blit(mask, (2, 2))
    return scale(surf, LOGO_SCALE)
