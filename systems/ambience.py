"""Map atmosphere: light, drifting leaves, butterflies and walking dust.

Configured by the map JSON's optional ``"ambience"`` block::

    {"tint": [255, 232, 196], "glow": true, "vignette": true,
     "leaves": true, "butterflies": 3}

``tint`` multiplies the world's colors (time of day), ``glow`` adds warm
sunlight from the top-left, ``vignette`` darkens the corners a little.
Particles live in world space; the light is applied in screen space after
the world is drawn and before the HUD.
"""

from __future__ import annotations

import math
import random

import pygame

import settings as s
from entities.prop import Prop

# Light is built at low resolution, then smoothly scaled to the screen
_LIGHT_RES = (s.SCREEN_WIDTH // 8, s.SCREEN_HEIGHT // 8)
_GLOW = (44, 30, 10)                  # strongest added light, at the top-left corner
_VIGNETTE = 0.82                      # brightness left in the far corners

_LEAF_COLORS = ((156, 170, 112), (192, 202, 150), (118, 140, 88))
_LEAF_EVERY_MS = (900, 2600)          # per tree on screen
_LEAF_FALL = 0.035                    # px per ms
_LEAF_REST_MS = 2200                  # lying on the ground before fading out
_BUTTERFLY_COLORS = ((248, 244, 228), (246, 210, 90), (232, 140, 72), (150, 170, 230))
_BUTTERFLY_SPEED = 0.06               # px per ms
_BUTTERFLY_RANGE = s.SCALED_TILE * 2
_FLAP_MS = 110
_DUST_MS = 420
_DUST_COLOR = (214, 196, 152)

_LEAF_TREES = {"olive_tree", "fig_tree", "plane_tree"}


class Ambience:
    """Light and small life for one map; owned by the exploration state."""

    def __init__(self, config: dict, props: list[Prop], seed: str) -> None:
        self._rng = random.Random(seed)
        self._light_mult = self._build_mult(config)
        self._light_add = self._build_glow() if config.get("glow") else None
        self._trees = [p for p in props if p.type in _LEAF_TREES] if config.get("leaves") \
            else []
        self._leaf_timers = [self._rng.uniform(*_LEAF_EVERY_MS) for _ in self._trees]
        self._leaves: list[dict] = []
        self._dust: list[list] = []          # [x, y, age, dx]
        self._time = 0.0
        homes = [p.rect.center for p in props if p.type in ("bush", "fig_tree")]
        self._butterflies = []
        for i in range(config.get("butterflies", 0) if homes else 0):
            home = homes[i * 3 % len(homes)]
            self._butterflies.append({
                "home": home, "pos": [home[0], home[1] - s.SCALED_TILE],
                "target": home, "color": _BUTTERFLY_COLORS[i % len(_BUTTERFLY_COLORS)],
                "phase": self._rng.random() * 1000,
            })

    # ── Light ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_mult(config: dict) -> pygame.Surface | None:
        tint = config.get("tint")
        if not tint and not config.get("vignette"):
            return None
        tint = tint or (255, 255, 255)
        small = pygame.Surface(_LIGHT_RES)
        w, h = _LIGHT_RES
        for y in range(h):
            for x in range(w):
                k = 1.0
                if config.get("vignette"):
                    d = math.hypot((x / w - 0.5) * 2, (y / h - 0.5) * 2) / math.sqrt(2)
                    k = 1 - (1 - _VIGNETTE) * d ** 2
                small.set_at((x, y), tuple(min(255, int(c * k)) for c in tint))
        return pygame.transform.smoothscale(small, (s.SCREEN_WIDTH, s.SCREEN_HEIGHT))

    @staticmethod
    def _build_glow() -> pygame.Surface:
        small = pygame.Surface(_LIGHT_RES)
        w, h = _LIGHT_RES
        for y in range(h):
            for x in range(w):
                k = max(0.0, 1 - math.hypot(x / w, y / h) / 1.1) ** 2
                small.set_at((x, y), tuple(int(c * k) for c in _GLOW))
        return pygame.transform.smoothscale(small, (s.SCREEN_WIDTH, s.SCREEN_HEIGHT))

    def render_light(self, surface: pygame.Surface) -> None:
        """Time-of-day light over the world (call before drawing the HUD)."""
        if self._light_mult is not None:
            surface.blit(self._light_mult, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if self._light_add is not None:
            surface.blit(self._light_add, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    # ── Particles ────────────────────────────────────────────────────────────

    def dust(self, x: float, y: float) -> None:
        """A small puff kicked up by a footstep at world position (x, y)."""
        for side in (-1, 1):
            self._dust.append([x + side * s.SCALE * 2, y, 0.0, side * 0.012])

    def update(self, dt: float, view: pygame.Rect) -> None:
        """Advance particles; ``view`` is the visible world rect (spawns only there)."""
        self._time += dt
        for i, tree in enumerate(self._trees):
            if not view.colliderect(tree.rect):
                continue
            self._leaf_timers[i] -= dt
            if self._leaf_timers[i] <= 0:
                self._leaf_timers[i] = self._rng.uniform(*_LEAF_EVERY_MS)
                self._spawn_leaf(tree)
        for leaf in self._leaves:
            if leaf["y"] < leaf["ground"]:
                leaf["y"] = min(leaf["ground"], leaf["y"] + _LEAF_FALL * dt)
                leaf["x"] += math.sin(self._time / 380 + leaf["phase"]) * 0.03 * dt
            else:
                leaf["rest"] += dt
        self._leaves = [leaf for leaf in self._leaves if leaf["rest"] < _LEAF_REST_MS]
        for puff in self._dust:
            puff[2] += dt
            puff[0] += puff[3] * dt
            puff[1] -= 0.01 * dt
        self._dust = [p for p in self._dust if p[2] < _DUST_MS]
        for fly in self._butterflies:
            self._move_butterfly(fly, dt)

    def _spawn_leaf(self, tree: Prop) -> None:
        crown = tree.rect.inflate(-tree.rect.w // 4, -tree.rect.h // 2)
        crown.top = tree.rect.top + tree.rect.h // 6
        self._leaves.append({
            "x": self._rng.uniform(crown.left, crown.right),
            "y": self._rng.uniform(crown.top, crown.bottom),
            "ground": tree.depth + self._rng.uniform(-s.SCALED_TILE, s.SCALED_TILE * 0.5),
            "color": self._rng.choice(_LEAF_COLORS),
            "phase": self._rng.random() * math.tau,
            "rest": 0.0,
        })

    def _move_butterfly(self, fly: dict, dt: float) -> None:
        x, y = fly["pos"]
        tx, ty = fly["target"]
        dist = math.hypot(tx - x, ty - y)
        if dist < s.SCALE * 4:
            hx, hy = fly["home"]
            fly["target"] = (hx + self._rng.uniform(-_BUTTERFLY_RANGE, _BUTTERFLY_RANGE),
                             hy - s.SCALED_TILE + self._rng.uniform(-_BUTTERFLY_RANGE / 2,
                                                                     _BUTTERFLY_RANGE / 2))
            return
        step = _BUTTERFLY_SPEED * dt
        wobble = math.sin((self._time + fly["phase"]) / 90) * 0.6
        fly["pos"][0] += (tx - x) / dist * step
        fly["pos"][1] += (ty - y) / dist * step + wobble * step

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Leaves, dust and butterflies, in world space."""
        px = s.SCALE
        for leaf in self._leaves:
            alpha = 1 - leaf["rest"] / _LEAF_REST_MS
            x, y = round(leaf["x"] - cam_x), round(leaf["y"] - cam_y)
            spin = int((self._time / 260 + leaf["phase"]) % 2) if leaf["rest"] == 0 else 0
            size = (px * 2, px) if spin == 0 else (px, px * 2)
            color = tuple(int(c * (0.6 + 0.4 * alpha)) for c in leaf["color"])
            if alpha > 0.15:
                surface.fill(color, (x, y, *size))
        for x, y, age, _ in self._dust:
            t = age / _DUST_MS
            puff = pygame.Surface((px * 2, px * 2), pygame.SRCALPHA)
            puff.fill((*_DUST_COLOR, int(150 * (1 - t))))
            grow = round(t * 2) * px
            surface.blit(pygame.transform.scale(puff, (px * 2 + grow, px * 2 + grow)),
                         (round(x - cam_x) - grow // 2, round(y - cam_y) - grow // 2))
        for fly in self._butterflies:
            x, y = round(fly["pos"][0] - cam_x), round(fly["pos"][1] - cam_y)
            open_wings = int((self._time + fly["phase"]) // _FLAP_MS) % 2 == 0
            color = fly["color"]
            body = (60, 44, 36)
            if open_wings:
                surface.fill(color, (x - px * 2, y - px, px * 2, px * 2))
                surface.fill(color, (x + px, y - px, px * 2, px * 2))
            else:
                surface.fill(color, (x - px, y - px * 2, px, px * 2))
                surface.fill(color, (x + px, y - px * 2, px, px * 2))
            surface.fill(body, (x, y - px, px, px * 2))
