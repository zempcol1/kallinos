"""Plants and rocks: olive, cypress, plane and fig trees, bushes, boulders.

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
OLIVE_LEAF = (118, 140, 92)
OLIVE_LEAF_DARK = (76, 98, 64)
OLIVE_LEAF_DEEP = (58, 76, 52)
OLIVE_LEAF_LIGHT = (164, 182, 136)
OLIVE_SILVER = (198, 208, 178)
OLIVE_FRUIT = (66, 52, 74)
OLIVE_BARK = (128, 112, 94)
OLIVE_BARK_DARK = (86, 72, 60)
OLIVE_BARK_LIGHT = (164, 150, 126)

CYPRESS = (52, 86, 58)
CYPRESS_DARK = (34, 60, 44)
CYPRESS_LIGHT = (84, 122, 74)

PLANE_LEAF = (104, 150, 70)
PLANE_LEAF_DARK = (66, 108, 52)
PLANE_LEAF_DEEP = (48, 82, 44)
PLANE_LEAF_LIGHT = (150, 188, 96)
PLANE_BARK = (150, 142, 118)
PLANE_BARK_DARK = (102, 96, 78)
PLANE_BARK_PATCH = (204, 198, 166)
PLANE_BARK_OLIVE = (124, 124, 84)

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


# ── Olive tree ───────────────────────────────────────────────────────────────

_OLIVE_TONES = (OLIVE_LEAF_DEEP, OLIVE_LEAF_DARK, OLIVE_LEAF, OLIVE_LEAF_LIGHT)
_OLIVE_STROKES = [
    (OLIVE_SILVER, OLIVE_LEAF_LIGHT, ((0, 0), (1, 0))),
    (OLIVE_LEAF_LIGHT, OLIVE_LEAF, ((0, 0), (1, 0))),
    (OLIVE_LEAF_LIGHT, OLIVE_LEAF, ((0, 0),)),
    (OLIVE_LEAF_DARK, OLIVE_LEAF, ((0, 0), (1, 0))),
    (OLIVE_LEAF_DEEP, OLIVE_LEAF_DARK, ((0, 0),)),
]


@cached
def olive_tree(w: int = 3, h: int = 3, variant: int = 0) -> pygame.Surface:
    """Gnarled olive: a twisted grey trunk forking into silvery leaf clumps."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("olive", w, h, variant)
    bark = (OLIVE_BARK, OLIVE_BARK_DARK, OLIVE_BARK_LIGHT)

    base = (pw // 2 + rng.randint(-2, 2), ph - 3)
    trunk_h = int(ph * 0.4)
    lean = rng.choice((-1, 1)) * rng.uniform(1.5, 3.5)
    top = _trunk(surf, rng, base, trunk_h, (6 + w, 5), lean, 1.5, bark)

    # Olive trunks twist and split: a hollow and a few spiralling fissures
    hollow = pygame.Rect(0, 0, 3, 5)
    hollow.center = (base[0] + int(lean / 3), base[1] - trunk_h // 3)
    pygame.draw.ellipse(surf, shade(OLIVE_BARK_DARK, -0.25), hollow)
    for i in range(3):
        x = base[0] - 2 + i * 2
        y0 = base[1] - rng.randint(1, 3)
        pygame.draw.line(surf, OLIVE_BARK_DARK, (x, y0), (x + int(lean / 2), y0 - trunk_h // 2))

    crown = pygame.Rect(3, 3, pw - 6, int(ph * 0.6))
    clumps = _limb_clumps(rng, top, crown, 2 + w // 3, (9, 12 + w))
    for end, _ in clumps:
        mid = ((top[0] + end[0]) // 2 + rng.randint(-1, 1), (top[1] + end[1]) // 2)
        _limb(surf, top, mid, 3, OLIVE_BARK, OLIVE_BARK_DARK)
        _limb(surf, mid, end, 2, OLIVE_BARK, OLIVE_BARK_DARK)
    for _, rect in clumps:
        _clump(surf, rect, _OLIVE_TONES)
    _texture(surf, rng, crown.inflate(4, 4), pw * ph // 6, _OLIVE_STROKES)

    for _ in range(2 + w):
        _, rect = rng.choice(clumps)
        surf.set_at((rect.centerx + rng.randint(-2, 2), rect.bottom - 2), OLIVE_FRUIT)
    return scale(outline(surf, OUTLINE))


def olive_tree_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(pw // 2 - 5, ph - 7, 10, 5)]


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
    max_half = pw // 2 - 3 + rng.randint(0, 1)

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
            if surf.get_at((x + dx, y)).a:
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


# ── Plane tree (platanos) ────────────────────────────────────────────────────

_PLANE_TONES = (PLANE_LEAF_DEEP, PLANE_LEAF_DARK, PLANE_LEAF, PLANE_LEAF_LIGHT)
_PLANE_STROKES = [
    (PLANE_LEAF_LIGHT, PLANE_LEAF, ((0, 0), (1, 0), (0, -1))),
    (shade(PLANE_LEAF_LIGHT, 0.3), PLANE_LEAF_LIGHT, ((0, 0), (1, 0))),
    (PLANE_LEAF_DARK, PLANE_LEAF, ((0, 0), (1, 1))),
    (PLANE_LEAF_DEEP, PLANE_LEAF_DARK, ((0, 0), (1, 0))),
]


@cached
def plane_tree(w: int = 5, h: int = 5, variant: int = 0) -> pygame.Surface:
    """The great village plane tree: mottled bark under a vast green crown."""
    surf = _canvas(w, h)
    pw, ph = surf.get_size()
    rng = seeded("plane", w, h, variant)
    bark = (PLANE_BARK, PLANE_BARK_DARK, shade(PLANE_BARK, 0.2))

    base = (pw // 2, ph - 3)
    trunk_h = int(ph * 0.45)
    top = _trunk(surf, rng, base, trunk_h, (w * 2 + 4, 8), rng.uniform(-2, 2), 1.0, bark)

    # Plane bark peels in pale cream and olive patches
    for _ in range(trunk_h * 2):
        x = base[0] + rng.randint(-w - 1, w)
        y = base[1] - rng.randint(1, trunk_h - 1)
        if surf.get_at((x, y))[:3] == PLANE_BARK[:3]:
            color = rng.choice((PLANE_BARK_PATCH, PLANE_BARK_OLIVE, PLANE_BARK_OLIVE))
            pygame.draw.rect(surf, color, (x, y, rng.randint(1, 3), rng.randint(1, 2)))

    crown = pygame.Rect(3, 3, pw - 6, int(ph * 0.7))
    clumps = _limb_clumps(rng, top, crown, w - 1, (16, 22), filler=w * 2)
    for end, _ in clumps:
        if end != top:
            _limb(surf, top, end, 3, PLANE_BARK, PLANE_BARK_DARK)
    for _, rect in clumps:
        _clump(surf, rect, _PLANE_TONES)
    _texture(surf, rng, crown.inflate(4, 4), pw * ph // 5, _PLANE_STROKES)
    return scale(outline(surf, OUTLINE))


def plane_tree_footprint(w: int, h: int) -> list[tuple[int, int, int, int]]:
    pw, ph = w * T, h * T
    return [(pw // 2 - w - 3, ph - 9, w * 2 + 6, 7)]


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
