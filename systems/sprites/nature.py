"""Plants and rocks: olive, cypress, plane, pine and fig trees, bushes, boulders.

Trees are one sprite each (trunk and crown together) and are drawn
depth-sorted with characters, so the player can walk behind them. Each
generator takes ``(w, h, variant)``: the size in tiles fills the canvas and
``variant`` reseeds the shape, so neighbouring trees don't look identical.
"""

from __future__ import annotations

import math
import random

import pygame

import settings as s
from systems.sprites.pixel_art import (
    Color, cached, lerp, outline, scale, seeded, shade, stamp,
)

T = s.TILE_SIZE
OUTLINE = (45, 34, 28)

# ── Palette ──────────────────────────────────────────────────────────────────
OLIVE_LEAVES = (  # deep shade → silver tips
    (44, 60, 44), (70, 92, 58), (104, 126, 78), (146, 164, 104), (192, 202, 150),
)
OLIVE_FRUIT = (60, 40, 64)
OLIVE_FRUIT_GREEN = (150, 158, 78)
OLIVE_BARK = (160, 132, 96)
OLIVE_BARK_DARK = (106, 84, 60)
OLIVE_BARK_DEEP = (66, 50, 38)
OLIVE_BARK_LIGHT = (206, 180, 134)

CYPRESS = (52, 86, 58)
CYPRESS_DARK = (34, 60, 44)
CYPRESS_LIGHT = (84, 122, 74)

PLANE_LEAVES = ((36, 62, 38), (58, 94, 48), (90, 132, 62), (136, 172, 84), (184, 206, 120))
PLANE_BARK = ((196, 190, 158), (148, 144, 116), (100, 98, 78), (62, 60, 48))
PLANE_PATCHES = ((224, 216, 180), (110, 118, 90), (156, 126, 84), (128, 132, 100))

PINE_NEEDLES = ((38, 62, 40), (62, 96, 50), (104, 138, 64), (150, 178, 88), (198, 212, 130))
PINE_BARK = ((196, 150, 112), (150, 104, 80), (98, 66, 54), (62, 42, 36))

FIG_LEAF = (96, 146, 64)
FIG_LEAF_DARK = (62, 104, 50)
FIG_LEAF_LIGHT = (142, 184, 88)
FIG_BARK = (150, 146, 136)
FIG_BARK_DARK = (102, 98, 92)
FIG_FRUIT = (104, 54, 92)
FIG_FRUIT_LIGHT = (156, 98, 136)

ROCK = (132, 128, 116)
ROCK_DARK = (94, 90, 84)
ROCK_LIGHT = (170, 166, 152)
MOSS = (100, 128, 66)


def _canvas(w: int, h: int) -> pygame.Surface:
    return pygame.Surface((w * T, h * T), pygame.SRCALPHA)


# ── Shared building blocks ───────────────────────────────────────────────────

def _trunk(surf: pygame.Surface, rng: random.Random, base: tuple[int, int], height: int,
           widths: tuple[float, float], lean: float, wobble: float,
           bark: tuple[Color, Color, Color]) -> tuple[int, int]:
    """Draw a tapering, slightly sinuous trunk; returns its top center.

    ``widths`` is (base, top) in px. Bark is (mid, dark, light); the left side
    catches the light and the right side is in shade.
    """
    mid, dark, light = bark
    base_x, base_y = base
    phase = rng.random() * math.tau
    top = (base_x, base_y)
    for i in range(height):
        t = i / max(1, height - 1)
        flare = max(0.0, 1 - t * 6) * 3       # roots spread at the very bottom
        w = widths[0] + (widths[1] - widths[0]) * t + flare
        cx = base_x + lean * t + math.sin(t * math.pi * 1.6 + phase) * wobble
        left, right = round(cx - w / 2), round(cx + w / 2)
        y = base_y - i
        pygame.draw.line(surf, mid, (left, y), (right, y))
        surf.set_at((left, y), light)
        if right - left > 4:
            surf.set_at((left + 1, y), light)
        pygame.draw.line(surf, dark, (right - max(1, (right - left) // 3), y), (right, y))
        top = (round(cx), y)
    return top


def _limb(surf: pygame.Surface, start: tuple[int, int], end: tuple[int, int],
          width: int, color: Color, shadow: Color) -> None:
    """A branch from ``start`` to ``end`` with a shaded underside."""
    pygame.draw.line(surf, shadow, (start[0] + 1, start[1] + 1), (end[0] + 1, end[1] + 1), width)
    pygame.draw.line(surf, color, start, end, width)


def _clump(surf: pygame.Surface, rect: pygame.Rect,
           tones: tuple[Color, Color, Color, Color]) -> None:
    """An oval leaf clump lit from the top-left: deep rim, body, highlight."""
    deep, dark, mid, light = tones
    pygame.draw.ellipse(surf, deep, rect.move(1, 1))
    pygame.draw.ellipse(surf, dark, rect)
    body = rect.inflate(-2, -2).move(-1, -1)
    pygame.draw.ellipse(surf, mid, body)
    if rect.w >= 8 and rect.h >= 6:
        glow = pygame.Rect(0, 0, rect.w // 2, max(2, rect.h // 3))
        glow.topleft = (rect.x + 2, rect.y + 1)
        pygame.draw.ellipse(surf, light, glow)


def _texture(surf: pygame.Surface, rng: random.Random, area: pygame.Rect, count: int,
             strokes: list[tuple[Color, Color, tuple[tuple[int, int], ...]]]) -> None:
    """Scatter small leaf strokes over painted pixels of a matching tone.

    Each stroke is (color, required tone, pixel offsets): a stroke only lands
    where its first pixel already has the required tone, so light leaves stay
    on lit areas and dark ones in shade, keeping the volume readable.
    """
    area = area.clip(surf.get_rect())
    for _ in range(count):
        x = rng.randrange(area.left, area.right)
        y = rng.randrange(area.top, area.bottom)
        color, tone, offsets = rng.choice(strokes)
        if surf.get_at((x, y))[:3] != tone[:3]:
            continue
        for dx, dy in offsets:
            px, py = x + dx, y + dy
            if area.collidepoint(px, py) and surf.get_at((px, py)).a:
                surf.set_at((px, py), color)


def _limb_clumps(rng: random.Random, top: tuple[int, int], crown: pygame.Rect, limbs: int,
                 size: tuple[int, int],
                 filler: int = 0) -> list[tuple[tuple[int, int], pygame.Rect]]:
    """Spread limb ends over the crown and hang 2–3 oval clumps on each.

    ``filler`` adds clumps anywhere inside the crown oval to fill big crowns.
    Returns (limb end, clump rect) pairs; clumps are sorted back to front.
    """
    result = []
    for i in range(limbs):
        t = (i + 0.5) / limbs
        end = (int(crown.left + crown.w * (0.15 + 0.7 * t) + rng.randint(-2, 2)),
               int(crown.top + crown.h * rng.uniform(0.3, 0.55)))
        for _ in range(rng.randint(2, 3)):
            w = rng.randint(*size)
            h = max(4, int(w * rng.uniform(0.6, 0.75)))
            rect = pygame.Rect(0, 0, w, h)
            rect.center = (end[0] + rng.randint(-w // 3, w // 3),
                           end[1] + rng.randint(-h // 2, h // 3))
            rect.clamp_ip(crown)
            result.append((end, rect))
    while filler > 0:
        w = rng.randint(*size)
        rect = pygame.Rect(0, 0, w, int(w * 0.7))
        rect.center = (rng.randint(crown.left, crown.right), rng.randint(crown.top, crown.bottom))
        nx = (rect.centerx - crown.centerx) / (crown.w / 2)
        ny = (rect.centery - crown.centery) / (crown.h / 2)
        if nx * nx + ny * ny <= 0.45:
            rect.clamp_ip(crown)
            result.append((top, rect))
            filler -= 1
    # A crowning clump on top so the silhouette is a dome, not a row
    w = size[1] + 2
    rect = pygame.Rect(0, 0, w, int(w * 0.7))
    rect.midtop = (crown.centerx + rng.randint(-3, 3), crown.top)
    result.append((top, rect))
    result.sort(key=lambda pair: pair[1].centery)
    return result


# ── Twisting trunks and leaf tufts (olive, pine) ─────────────────────────────

Strand = list[tuple[float, float, float]]   # (x, y, width) from the base up


def _strand(surf: pygame.Surface, points: Strand,
            bark: tuple[Color, Color, Color, Color]) -> None:
    """One twisting trunk strand, lit on its left edge and shaded on its right.

    Several overlapping strands drawn back to front read as a braided,
    gnarled olive trunk. Bark is (light, mid, dark, deep).
    """
    light, mid, dark, deep = bark
    for (x0, y0, w0), (x1, y1, w1) in zip(points, points[1:]):
        rows = max(1, round(abs(y1 - y0)))
        for i in range(rows + 1):
            t = i / rows
            x, y, w = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w0 + (w1 - w0) * t
            left, right = round(x - w / 2), round(x + w / 2)
            row = round(y)
            pygame.draw.line(surf, mid, (left, row), (right, row))
            pygame.draw.line(surf, dark, (right - max(1, round(w / 3)), row), (right, row))
            surf.set_at((right, row), deep)
            surf.set_at((left, row), light)
            if w > 4:
                surf.set_at((left + 1, row), light)


def _leafy_clump(surf: pygame.Surface, rng: random.Random, center: tuple[float, float],
                 radii: tuple[float, float], tones: tuple[Color, ...],
                 leaf: list[str] | None = None) -> None:
    """A rounded mass of small leaves: serrated edge, shadow below, lit top-left.

    ``tones`` runs from deep shade to the brightest leaf tips (5 colors).
    ``leaf`` (a small grid, ``l`` leaf / ``v`` vein) stamps whole leaves on the
    lit side, for big-leaved trees like the plane.
    """
    deep, dark, mid, light, tip = tones
    cx, cy = center
    rx, ry = radii
    # Serrated silhouette: leaf points sticking out all around the edge
    steps = int((rx + ry) * 1.6)
    for i in range(steps):
        a = math.tau * i / steps + rng.uniform(-0.1, 0.1)
        ex, ey = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        length = rng.uniform(1, 2.4)
        color = dark if math.sin(a) > 0.2 else (mid if math.sin(a) > -0.6 else light)
        pygame.draw.line(surf, color, (round(ex), round(ey)),
                         (round(ex + math.cos(a) * length), round(ey + math.sin(a) * length)))
    body = pygame.Rect(0, 0, round(rx * 2), round(ry * 2))
    body.center = (round(cx), round(cy))
    pygame.draw.ellipse(surf, dark, body)
    pygame.draw.ellipse(surf, deep, (body.x + 1, body.centery, body.w - 1, body.h // 2 + 1))
    pygame.draw.ellipse(surf, dark, body.inflate(-2, -3).move(0, -1))
    pygame.draw.ellipse(surf, mid, body.inflate(-round(rx * 0.5), -round(ry * 0.6)).move(-1, -2))
    glow = pygame.Rect(0, 0, round(rx * 0.9), round(ry * 0.7))
    glow.center = (round(cx - rx * 0.3), round(cy - ry * 0.4))
    pygame.draw.ellipse(surf, light, glow)
    # Individual leaves: light flecks up top, dark separations below
    for _ in range(int(rx * ry * 0.9)):
        x = cx + rng.uniform(-rx, rx) * 0.9
        y = cy + rng.uniform(-ry, ry) * 0.9
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > 0.8:
            continue
        upper = (x - cx) / rx * 0.4 + (y - cy) / ry < -0.1
        if upper:
            color, dx = (tip if rng.random() < 0.5 else light), 1
        else:
            color, dx = (deep if (y - cy) > ry * 0.3 else dark), -1
        surf.set_at((round(x), round(y)), color)
        surf.set_at((round(x) + dx, round(y) - 1), color)
    if leaf:
        for _ in range(int(rx * ry * 0.06) + 1):
            x = cx + rng.uniform(-rx * 0.7, rx * 0.3)
            y = cy + rng.uniform(-ry * 0.8, 0)
            stamp(surf, leaf, {"l": rng.choice((light, tip)), "v": mid},
                  (round(x) - len(leaf[0]) // 2, round(y) - len(leaf) // 2))


# ── Olive tree ───────────────────────────────────────────────────────────────

@cached
def olive_tree(w: int = 3, h: int = 3, variant: int = 0) -> pygame.Surface:
    """Old olive: a braided, hollow trunk under a silvery crown of leaf clumps."""
    return scale(olive_tree_logical(w, h, variant))


@cached
def olive_tree_logical(w: int = 3, h: int = 3, variant: int = 0) -> pygame.Surface:
    """The olive at logical size, outlined (the title screen reuses it)."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("olive", w, h, variant)
    k = pw / (3 * T)                      # proportions are designed for a 3×3 tree
    bark = (OLIVE_BARK_LIGHT, OLIVE_BARK, OLIVE_BARK_DARK, OLIVE_BARK_DEEP)
    bx, by = pw / 2 + rng.uniform(-2, 2), ph - 3
    lean = rng.choice((-1, 1))
    spread = rng.uniform(0.85, 1.15)

    # Flared roots gripping the ground
    for dx in (-9, -6, 6, 9):
        pygame.draw.line(surf, OLIVE_BARK_DARK, (bx, by - 2), (bx + dx * k, by + 1), 2)
        pygame.draw.line(surf, OLIVE_BARK, (bx, by - 3), (bx + dx * k, by), 1)

    # Two or three strands twist around each other and fork into limbs
    left_end = (bx - 13 * k * spread, by - 25 * k)
    right_end = (bx + 12 * k * spread, by - 27 * k)
    strands = [
        [(bx + 3 * k, by, 8 * k), (bx + 1 * k, by - 7 * k, 6 * k),
         (bx + 4 * k * lean, by - 15 * k, 5 * k), (*right_end, 3)],
        [(bx - 3 * k, by, 8 * k), (bx - 2 * k, by - 8 * k, 6 * k),
         (bx - 6 * k * lean, by - 16 * k, 4 * k), (*left_end, 3)],
    ]
    if variant % 2 == 0:
        strands.insert(1, [(bx, by - 1, 6 * k), (bx - 1 * k * lean, by - 11 * k, 4 * k),
                           (bx + 2 * k, by - 21 * k, 3 * k), (bx + rng.uniform(-3, 3),
                                                             by - 30 * k, 2)])
    for strand in strands:
        _strand(surf, strand, bark)
    # The hollow where the strands part, and spiral fissures
    hollow = pygame.Rect(0, 0, round(4 * k), round(6 * k))
    hollow.center = (round(bx), round(by - 12 * k))
    pygame.draw.ellipse(surf, OLIVE_BARK_DEEP, hollow)
    pygame.draw.line(surf, OLIVE_BARK_DARK, hollow.topright, hollow.bottomright)
    for i in range(3):
        y0 = by - rng.uniform(1, 6) * k
        x0 = bx + (i - 1) * 3 * k
        pygame.draw.line(surf, OLIVE_BARK_DARK, (x0, y0), (x0 - 2 * lean, y0 - 5 * k))

    # Crown: small leaf clumps on branch tips around a loose dome, with gaps
    # where the twisting limbs show through. Anchors are (dx, dy, radius)
    # relative to the trunk base, designed for a 3×3 tree.
    anchors = [(-15, -24, 5.5), (-10, -33, 6), (-1, -38, 6), (9, -34, 6), (15, -25, 5.5),
               (3, -27, 4.5)]
    if w >= 4:
        anchors += [(-21, -29, 4.5), (20, -31, 4.5), (-5, -44, 5)]
    clumps = []
    for dx, dy, r in anchors:
        jx, jy = rng.uniform(-2, 2), rng.uniform(-1.5, 1.5)
        rx, ry = r * k, r * k * 0.8
        x = max(rx + 3, min(pw - rx - 3, bx + (dx + jx) * k * spread))
        y = max(ry + 3, by + (dy + jy) * k)
        clumps.append((x, y, rx, ry))
    fork = (bx, by - 16 * k)
    for x, y, _, _ in clumps:
        limb = left_end if x < bx else right_end
        mid = ((limb[0] + x) / 2, (limb[1] + y) / 2 + 2)
        pygame.draw.lines(surf, OLIVE_BARK_DARK, False, [fork, limb, mid, (x, y + 2)], 2)
        pygame.draw.lines(surf, OLIVE_BARK, False, [limb, mid, (x - 1, y + 1)], 1)
    for x, y, rx, ry in sorted(clumps, key=lambda c: c[1]):
        _leafy_clump(surf, rng, (x, y), (rx, ry), OLIVE_LEAVES)

    # Olives hang on the undersides of the clumps
    for cx, cy, rx, ry in clumps:
        for _ in range(2):
            x = round(cx + rng.uniform(-rx, rx) * 0.6)
            y = round(cy + ry * rng.uniform(0.3, 0.7))
            surf.set_at((x, y), OLIVE_FRUIT if rng.random() < 0.7 else OLIVE_FRUIT_GREEN)
    return outline(surf, OUTLINE)


def olive_tree_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(pw // 2 - 6, ph - 7, 12, 5)]


def tree_shadow(w: int, h: int, variant: int = 0) -> list[tuple[str, tuple[int, int, int, int]]]:
    """Crown shadow on the ground, cast slightly toward the bottom-right."""
    pw, ph = w * T, h * T
    sw = int(pw * 0.8)
    return [("ellipse", (pw // 2 - sw // 2 + 3, ph - 9, sw, 9))]


# ── Cypress ──────────────────────────────────────────────────────────────────

@cached
def cypress(w: int = 2, h: int = 4, variant: int = 0) -> pygame.Surface:
    """Mediterranean cypress: a tall, dark green flame."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("cypress", w, h, variant)
    cx = pw // 2
    base_y = ph - 3
    top_y = 1
    max_half = min(pw // 2 - 3, round(ph * 0.14)) + rng.randint(0, 1)

    # Stubby trunk under the foliage
    pygame.draw.rect(surf, OLIVE_BARK_DARK, (cx - 1, base_y - 4, 3, 5))
    surf.set_at((cx - 1, base_y), OLIVE_BARK)

    # Flame silhouette: widest about two thirds of the way down
    height = base_y - 3 - top_y
    for i in range(height):
        t = i / height                      # 0 at the tip, 1 at the base
        profile = math.sin(min(1.0, t / 0.72) * math.pi / 2) ** 0.8
        if t > 0.85:
            profile *= 1 - (t - 0.85) * 1.6
        half = max(1, round(max_half * profile + math.sin(i * 0.9 + variant) * 0.6))
        y = top_y + i
        pygame.draw.line(surf, CYPRESS, (cx - half, y), (cx + half - 1, y))
        surf.set_at((cx - half, y), CYPRESS_LIGHT)
        pygame.draw.line(surf, CYPRESS_DARK, (cx + half // 3, y), (cx + half - 1, y))

    # Scale-leaf tufts: light on the lit left side, dark on the right
    for _ in range(pw * ph // 8):
        x = rng.randrange(1, pw - 1)
        y = rng.randrange(top_y, base_y - 3)
        if not surf.get_at((x, y)).a:
            continue
        lit = x < cx + rng.randint(-2, 1)
        color = CYPRESS_LIGHT if lit else CYPRESS_DARK
        for dx in range(rng.randint(1, 3)):
            if x + dx < pw and surf.get_at((x + dx, y)).a:
                surf.set_at((x + dx, y), color)
        if lit and surf.get_at((x, y + 1)).a:
            surf.set_at((x, y + 1), CYPRESS)
    return scale(outline(surf, OUTLINE))


def cypress_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(pw // 2 - 4, ph - 6, 8, 4)]


def cypress_shadow(w: int, h: int, variant: int = 0) -> list[tuple[str, tuple[int, int, int, int]]]:
    pw, ph = w * T, h * T
    return [("ellipse", (pw // 2 - 5, ph - 7, 14, 6))]


# ── Oriental plane (platanos) ────────────────────────────────────────────────

_PLANE_LEAF = [  # a palmate plane leaf
    "l.l.l",
    "lllll",
    ".lvl.",
    "..v..",
]


@cached
def plane_tree(w: int = 6, h: int = 6, variant: int = 0) -> pygame.Surface:
    """Oriental plane: a massive mottled trunk under a vast, broad crown."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("plane", w, h, variant)
    k = pw / (6 * T)                      # designed for a 6×6 tree
    bx, by = pw / 2 + rng.uniform(-3, 3), ph - 4

    # Buttressed base, then a short massive trunk splitting into great limbs
    for dx in (-18, -12, 12, 18):
        pygame.draw.line(surf, PLANE_BARK[2], (bx, by - 4), (bx + dx * k, by + 1), 3)
    fork_y = by - 30 * k
    limbs = [(-30, -52), (-12, -66), (10, -64), (30, -50)]
    for i, (dx, dy) in enumerate(limbs):
        side = -1 if dx < 0 else 1
        _strand(surf, [(bx + side * 5 * k, by, 12 * k), (bx + side * 4 * k, fork_y, 9 * k),
                       (bx + dx * 0.5 * k, by + dy * 0.75 * k, 6 * k),
                       (bx + dx * k, by + dy * k, 3 * k)], PLANE_BARK)
    _strand(surf, [(bx, by, 18 * k), (bx - 1, by - 14 * k, 14 * k), (bx, fork_y + 2, 11 * k)],
            PLANE_BARK)
    # Plane bark sheds in pale and olive patches: a camouflage mosaic
    mask = pygame.mask.from_surface(surf)
    for _ in range(int(260 * k * k)):
        x = round(bx + rng.uniform(-22, 22) * k)
        y = rng.randrange(int(by - 60 * k), ph)
        if not mask.get_at((x, y)) or surf.get_at((x, y))[:3] == PLANE_BARK[3][:3]:
            continue
        color = rng.choice(PLANE_PATCHES)
        for _ in range(rng.randint(3, 7)):   # an irregular blotch of a few pixels
            px, py = x + rng.randint(-2, 2), y + rng.randint(-1, 1)
            if 0 <= px < pw and 0 <= py < ph and mask.get_at((px, py)):
                surf.set_at((px, py), color)

    # Broad dome of big leaf clumps
    anchors = [(-36, -46, 12), (-24, -62, 14), (-4, -72, 15), (16, -66, 14), (34, -50, 12),
               (-12, -50, 11), (18, -48, 11), (2, -56, 12), (-40, -34, 8), (40, -36, 8)]
    clumps = []
    for dx, dy, r in anchors:
        rx, ry = r * k, r * k * 0.78
        x = max(rx + 3, min(pw - rx - 3, bx + (dx + rng.uniform(-3, 3)) * k))
        y = max(ry + 3, by + (dy + rng.uniform(-2, 2)) * k)
        clumps.append((x, y, rx, ry))
    for x, y, rx, ry in sorted(clumps, key=lambda c: c[1]):
        _leafy_clump(surf, rng, (x, y), (rx, ry), PLANE_LEAVES, _PLANE_LEAF)
    return scale(outline(surf, OUTLINE))


def plane_tree_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(pw // 2 - w * 2 - 2, ph - 10, w * 4 + 4, 8)]


# ── Aleppo pine ──────────────────────────────────────────────────────────────

@cached
def aleppo_pine(w: int = 4, h: int = 5, variant: int = 0) -> pygame.Surface:
    """Aleppo pine: a leaning reddish trunk carrying flat clouds of needles."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("pine", w, h, variant)
    k = pw / (4 * T)                      # designed for a 4×5 tree
    lean = rng.choice((-1, 1)) * rng.uniform(0.6, 1.0)
    bx, by = pw / 2 - lean * 8 * k, ph - 3

    bend = rng.uniform(-4, 4)
    trunk = [(bx, by, 6 * k), (bx + (lean * 3 + bend) * k, by - 20 * k, 5 * k),
             (bx + lean * 12 * k, by - 42 * k, 4 * k), (bx + lean * 16 * k, by - 60 * k, 2)]
    _strand(surf, trunk, PINE_BARK)
    for _ in range(int(24 * k)):   # flaky, plated bark
        i = rng.randrange(len(trunk) - 1)
        (x0, y0, _), (x1, y1, _) = trunk[i], trunk[i + 1]
        t = rng.random()
        x = x0 + (x1 - x0) * t + rng.uniform(-1.5, 1.5)
        surf.set_at((round(x), round(y0 + (y1 - y0) * t)), PINE_BARK[2])

    def trunk_at(y: float) -> tuple[float, float]:
        for (x0, y0, _), (x1, y1, _) in zip(trunk, trunk[1:]):
            if y1 <= y <= y0:
                return x0 + (x1 - x0) * (y0 - y) / (y0 - y1), y
        return trunk[-1][0], trunk[-1][1]

    # An open, irregular crown of needle clouds on upward-angled branches
    top_x = bx + lean * 16 * k
    anchors = [(0, -64, 10), (-14, -56, 9), (13, -54, 9), (-22, -44, 8), (20, -42, 8),
               (-6, -48, 8), (6, -40, 7), (-12, -34, 6)]
    clouds = []
    for dx, dy, r in anchors:
        rx, ry = r * k, r * k * 0.7
        x = max(rx + 3, min(pw - rx - 3, top_x + (dx + rng.uniform(-2, 2)) * k))
        y = max(ry + 3, by + (dy + rng.uniform(-2, 2)) * k)
        clouds.append((x, y, rx, ry))
    for x, y, _, _ in clouds:
        root = trunk_at(min(by - 8 * k, y + 10 * k))
        pygame.draw.line(surf, PINE_BARK[2], root, (x, y + 2), 2)
        pygame.draw.line(surf, PINE_BARK[1], (root[0], root[1] - 1), (x, y + 1), 1)
    for x, y, rx, ry in sorted(clouds, key=lambda c: c[1]):
        _leafy_clump(surf, rng, (x, y), (rx, ry), PINE_NEEDLES)
    return scale(outline(surf, OUTLINE))


def aleppo_pine_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    k = pw / (4 * T)
    return [(round(pw / 2 - 5 * k), ph - 7, round(10 * k), 5)]


def pine_shadow(w: int, h: int, variant: int = 0) -> list[tuple[str, tuple[int, int, int, int]]]:
    """Open crown: a lighter, irregular pair of shadow blobs."""
    pw, ph = w * T, h * T
    return [("ellipse", (pw // 2 - pw // 3, ph - 8, pw // 2, 7)),
            ("ellipse", (pw // 2, ph - 10, pw // 3, 6))]


# ── Fig tree ─────────────────────────────────────────────────────────────────

_FIG_TONES = (shade(FIG_LEAF_DARK, -0.2), FIG_LEAF_DARK, FIG_LEAF, FIG_LEAF_LIGHT)
_FIG_STROKES = [  # broad leaves: chunky light blots and dark veins
    (FIG_LEAF_LIGHT, FIG_LEAF, ((0, 0), (1, 0), (0, 1), (-1, 0))),
    (shade(FIG_LEAF_LIGHT, 0.25), FIG_LEAF_LIGHT, ((0, 0), (1, 0))),
    (FIG_LEAF_DARK, FIG_LEAF, ((0, 0), (0, 1))),
    (FIG_LEAF_DARK, FIG_LEAF, ((0, 0), (1, 1))),
]
_FIG = [
    ".g.",
    "pPp",
    "ppp",
    ".p.",
]


@cached
def fig_tree(w: int = 3, h: int = 3, variant: int = 0, ripe: bool = True) -> pygame.Surface:
    """Many-stemmed fig with broad leaves; ``ripe`` hangs purple figs in it.

    At 2×2 tiles or smaller it grows as a low fig bush.
    """
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("fig", w, h, variant)
    bushy = w <= 2
    base = (pw // 2, ph - 3)

    # Smooth grey stems fanning out low from the base
    bark = (FIG_BARK, FIG_BARK_DARK, shade(FIG_BARK, 0.25))
    top = base if bushy else _trunk(surf, rng, base, int(ph * 0.25), (6, 4),
                                     rng.uniform(-1, 1), 0.6, bark)
    if bushy:
        # Low and wide: lobes sit right above short stems
        crown = pygame.Rect(1, 2, pw - 2, ph - 4)
        lobes = [(1, ph - 19, 14, 11), (pw - 15, ph - 19, 14, 11),
                 (pw // 2 - 8, ph - 27, 16, 12), (pw // 2 - 6, ph - 16, 12, 9)]
        clumps = [((x + lw // 2, y + lh // 2), pygame.Rect(x, y, lw, lh))
                  for x, y, lw, lh in lobes]
        clumps.sort(key=lambda pair: pair[1].centery)
    else:
        crown = pygame.Rect(2, 3, pw - 4, int(ph * 0.66))
        clumps = _limb_clumps(rng, top, crown, 2 + w // 2, (8 + w, 11 + w * 2))
    for end, _ in clumps:
        if end != top:
            _limb(surf, top, end, 2, FIG_BARK, FIG_BARK_DARK)
    for _, rect in clumps:
        _clump(surf, rect, _FIG_TONES)
    _texture(surf, rng, crown.inflate(4, 4), pw * ph // 8, _FIG_STROKES)

    if ripe:
        fig_palette = {"p": FIG_FRUIT, "P": FIG_FRUIT_LIGHT, "g": FIG_LEAF_DARK}
        hanging = sorted((rect for _, rect in clumps), key=lambda r: -r.bottom)
        for i in range(2 + w):
            rect = hanging[i % len(hanging)]
            stamp(surf, _FIG, fig_palette,
                  (rect.x + 2 + (i * 5 + rng.randint(0, 3)) % max(1, rect.w - 5),
                   rect.bottom - 5 + rng.randint(-2, 1)))
    return scale(outline(surf, OUTLINE))


def fig_tree_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    if w <= 2:
        return [(pw // 2 - 6, ph - 7, 12, 5)]
    return [(pw // 2 - 5, ph - 7, 10, 5)]


# ── Bushes ───────────────────────────────────────────────────────────────────

# variant → (leaf tones, flower colors): myrtle, oleander, lavender
_BUSHES = [
    (((36, 64, 38), (54, 88, 48), (76, 116, 58), (112, 150, 78)),
     ((244, 240, 226), (214, 206, 176))),
    (((46, 74, 42), (66, 100, 54), (92, 132, 68), (128, 164, 90)),
     ((226, 112, 146), (250, 170, 190))),
    (((66, 84, 72), (92, 112, 94), (124, 144, 116), (160, 178, 146)),
     ((132, 100, 176), (174, 146, 210))),
]


@cached
def bush(w: int = 1, h: int = 1, variant: int = 0) -> pygame.Surface:
    """A garden shrub. Variants: 0 myrtle, 1 oleander, 2 lavender."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("bush", w, h, variant)
    tones, flowers = _BUSHES[variant % len(_BUSHES)]
    light = tones[3]

    # Three overlapping lobes: two at the base, one on top
    lobes = [pygame.Rect(1, ph - 11, 9, 9), pygame.Rect(pw - 10, ph - 11, 9, 9),
             pygame.Rect(pw // 2 - 5, ph - 15, 10, 10)]
    for extra in range(w - 1):
        lobes.append(pygame.Rect(6 + extra * 10, ph - 16, 10, 10))
    lobes.sort(key=lambda r: r.centery)
    for rect in lobes:
        _clump(surf, rect, tones)
    body = pygame.Rect(0, 0, pw, ph)
    _texture(surf, rng, body, pw * ph // 6,
             [(light, tones[2], ((0, 0),)), (tones[1], tones[2], ((0, 0), (1, 0))),
              (tones[0], tones[1], ((0, 0),))])

    # Flowers in small clusters, never a lone pair (reads as eyes)
    for _ in range(2 + w):
        x = rng.randrange(3, pw - 4)
        y = rng.randrange(ph - 14, ph - 6)
        if surf.get_at((x, y)).a and surf.get_at((x + 1, y + 1)).a:
            surf.set_at((x, y), flowers[0])
            surf.set_at((x + 1, y + 1), flowers[0])
            surf.set_at((x + 1, y), flowers[1])
    return scale(outline(surf, OUTLINE))


def bush_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(2, ph - 9, pw - 4, 8)]


def bush_shadow(w: int, h: int, variant: int = 0) -> list[tuple[str, tuple[int, int, int, int]]]:
    pw, ph = w * T, h * T
    return [("ellipse", (2, ph - 5, pw - 1, 5))]


# ── Boulder ──────────────────────────────────────────────────────────────────

@cached
def boulder(w: int, h: int, variant: int = 0) -> pygame.Surface:
    """One big mossy boulder filling the object's footprint."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("boulder", w, h, variant)

    body = pygame.Rect(2, 3, pw - 4, ph - 6)
    pygame.draw.ellipse(surf, ROCK_DARK, body)
    pygame.draw.ellipse(surf, ROCK, body.inflate(-2, -4).move(-1, -2))
    pygame.draw.ellipse(surf, ROCK_LIGHT, (body.x + 5, body.y + 3, body.w // 3, body.h // 4))
    pygame.draw.ellipse(surf, shade(ROCK_LIGHT, 0.3),
                        (body.x + 7, body.y + 4, body.w // 6, body.h // 8))
    # Cracks
    cx = body.centerx + rng.randrange(-3, 4)
    pygame.draw.lines(surf, ROCK_DARK, False,
                      [(cx, body.top + 4), (cx - 2, body.centery), (cx + 1, body.bottom - 6)])
    pygame.draw.line(surf, ROCK_DARK, (cx - 2, body.centery), (cx - 7, body.centery + 3))
    pygame.draw.line(surf, ROCK_LIGHT, (cx - 1, body.top + 4), (cx - 3, body.centery - 1))
    # Moss creeping up from the damp, shaded base
    for _ in range(pw * 2):
        mx = rng.randrange(body.left + 2, body.right - 2)
        my = rng.randrange(body.centery + 2, body.bottom - 1)
        if surf.get_at((mx, my)).a:
            surf.set_at((mx, my), lerp(MOSS, ROCK_DARK, rng.random() * 0.4))
    return scale(outline(surf, OUTLINE))


def boulder_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(3, ph // 3, pw - 6, ph - ph // 3 - 3)]


def boulder_shadow(w: int, h: int, variant: int = 0) -> list[tuple[str, tuple[int, int, int, int]]]:
    pw, ph = w * T, h * T
    return [("ellipse", (2, ph - 9, pw, 8))]
