"""Title screen art: an Aegean sunset with a temple headland and Athena's olive.

The scene is painted at logical resolution in layers (sky, sea, headland,
foreground) that the main menu composes every frame together with the
animated bits (stars, clouds, gulls, sea glitter, motes), then scales up.
"""

from __future__ import annotations

import math

import pygame

import settings as s
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
MARBLE_SHADE = (150, 96, 116)
LEAF_DARK = (26, 26, 38)
LEAF = (40, 40, 52)
LEAF_RIM = (196, 132, 78)
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
    """Static sea: dithered bands darkening toward the viewer, a glow under the sun."""
    surf = pygame.Surface((WIDTH, HEIGHT - HORIZON))
    _dithered_bands(surf, SEA_BANDS, 0, HEIGHT - HORIZON)
    for y in range(0, 14):
        half = int(SUN_RADIUS * 1.6 * (1 - y / 16))
        for x in range(SUN[0] - half, SUN[0] + half):
            if (x + y) % 2 == 0 or y < 3:
                surf.set_at((x, y), lerp(surf.get_at((x, y)), SKY_BANDS[-2], 0.5))
    return surf


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

    # The temple: steps, six columns, entablature, pediment
    tx, base = 214, top - 1
    width = 42
    for i in range(3):
        pygame.draw.rect(surf, MARBLE_LIT if i == 0 else MARBLE_SHADE,
                         (tx - i, base - 2 - i * 2, width + i * 2, 2))
    col_top = base - 22
    pygame.draw.rect(surf, (54, 30, 52), (tx + 2, col_top, width - 4, 16))
    for i in range(6):
        cx = tx + 3 + i * 7
        pygame.draw.rect(surf, MARBLE_SHADE, (cx, col_top, 3, 16))
        pygame.draw.line(surf, MARBLE_LIT, (cx, col_top), (cx, col_top + 15))
    pygame.draw.rect(surf, MARBLE_LIT, (tx - 1, col_top - 4, width + 2, 4))
    pygame.draw.line(surf, MARBLE_SHADE, (tx - 1, col_top - 1), (tx + width, col_top - 1))
    pygame.draw.polygon(surf, MARBLE_LIT, [(tx - 2, col_top - 4), (tx + width // 2, col_top - 12),
                                           (tx + width + 1, col_top - 4)])
    pygame.draw.polygon(surf, MARBLE_SHADE, [(tx + 4, col_top - 5), (tx + width // 2, col_top - 9),
                                             (tx + width - 4, col_top - 5)])
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

    # Thick, twisting trunk that splits into three limbs
    base_x, base_y, fork_y = 36, 150, 108
    for y in range(fork_y, base_y + 1):
        t = (base_y - y) / (base_y - fork_y)
        cx = base_x + math.sin(t * 3.0) * 4 + t * 7
        w = 13 - t * 6 + (3 if t < 0.12 else 0)
        pygame.draw.line(surf, ROCK_DARK, (round(cx - w / 2), y), (round(cx + w / 2), y))
        surf.set_at((round(cx + w / 2), y), ROCK_LIT)
        if int(y * 0.7) % 4 == 0:
            surf.set_at((round(cx), y), ROCK)
    fork = (44, fork_y)
    ends = [(12, 90), (40, 78), (66, 84), (88, 98)]
    for end in ends:
        mid = ((fork[0] + end[0]) // 2 + 2, (fork[1] + end[1]) // 2 + 3)
        pygame.draw.lines(surf, ROCK_DARK, False, [fork, mid, end], 4)
        pygame.draw.lines(surf, ROCK_LIT, False, [(fork[0] + 2, fork[1]), (mid[0] + 2, mid[1]),
                                                  (end[0] + 1, end[1])], 1)

    # Crown: overlapping oval clumps hung on the limb ends, with sky showing through
    clumps = []
    for ex, ey in ends:
        for _ in range(4):
            w, h = rng.randint(16, 26), rng.randint(8, 12)
            clumps.append((ex + rng.randint(-10, 10) - w // 2, ey + rng.randint(-6, 4) - h // 2,
                           w, h))
    clumps.sort(key=lambda c: c[1])
    for x, y, w, h in clumps:
        pygame.draw.ellipse(surf, LEAF_DARK, (x, y + 1, w, h))
        pygame.draw.ellipse(surf, LEAF, (x + 1, y, w - 4, h - 3))
    crown = pygame.Rect(0, 60, 104, 50)
    for _ in range(260):   # silvery leaf specks
        px, py = rng.randrange(crown.left, crown.right), rng.randrange(crown.top, crown.bottom)
        if surf.get_at((px, py))[:3] == LEAF[:3]:
            surf.set_at((px, py), (62, 58, 76))
    # Warm rim where the crown faces the sun (up and right)
    mask = pygame.mask.from_surface(surf)
    for py in range(crown.top, crown.bottom):
        for px in range(crown.left, crown.right):
            if not mask.get_at((px, py)):
                continue
            open_up = py > 0 and not mask.get_at((px, py - 1))
            open_right = px + 1 < WIDTH and not mask.get_at((px + 1, py))
            if open_up or (open_right and py < crown.centery):
                warmth = min(1.0, px / 90)
                surf.set_at((px, py), lerp(LEAF, LEAF_RIM, 0.35 + 0.65 * warmth))
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
