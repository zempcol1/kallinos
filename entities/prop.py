"""Map objects drawn depth-sorted with characters: trees, bushes, fences."""

from __future__ import annotations

import pygame

import settings as s
from systems.sprites import ObjectType, silhouette


class Prop:
    """One sorted map object, built by ``TileMap`` from the map JSON.

    ``depth`` is the world y of the object's base line: characters whose feet
    are below it are drawn in front of it, others behind. Trees fade while
    the player stands behind them. Harvestable props (``"harvest": item_id``
    in the map JSON) yield that item once, then switch to their picked look.
    """

    SEE_THROUGH_ALPHA = 140
    GLOW_ALPHA = 160              # strongest golden glow (scripts set ``glow`` 0–1)
    REACH = (int(s.SCALED_TILE * 1.4), s.SCALED_TILE)   # interaction margin (x, y)

    def __init__(self, data: dict, kind: ObjectType, rect: pygame.Rect,
                 footprints: list[pygame.Rect], links: tuple[bool, ...] | None = None) -> None:
        self.id: str | None = data.get("id")
        self.type: str = data["type"]
        self.rect = rect
        self.footprints = footprints
        self.depth = max((f.bottom for f in footprints), default=rect.bottom)
        self.harvest: str | None = data.get("harvest") if kind.harvestable else None
        self.harvest_text: str | None = data.get("harvest_text")
        self.harvested = False
        self.faded = False
        self.glow = 0.0
        self.glow_color: tuple = s.COLOR_TITLE_GOLD

        self._kind = kind
        self._args = (links,) if kind.tiled else (data["w"], data["h"])
        self._variant: int = data.get("variant", 0)
        self._options = {key: data[key] for key in kind.options if key in data}
        self._sprite = kind.draw(*self._args, self._variant, **self._options)
        self._faded_sprite: pygame.Surface | None = None

    @property
    def sprite(self) -> pygame.Surface:
        return self._sprite

    @property
    def can_harvest(self) -> bool:
        return self.harvest is not None and not self.harvested

    def pick(self) -> str | None:
        """Harvest the prop: returns the item id, or None if nothing is left."""
        if not self.can_harvest:
            return None
        self.harvested = True
        self._sprite = self._kind.draw(*self._args, self._variant, ripe=False, **self._options)
        self._faded_sprite = None
        return self.harvest

    def interaction_rect(self) -> pygame.Rect:
        base = self.footprints[0].unionall(self.footprints[1:]) if self.footprints else self.rect
        return base.inflate(*self.REACH)

    def update_fade(self, sprite_rect: pygame.Rect, feet_y: int) -> None:
        """Fade if the given character stands behind this prop and is hidden by it."""
        self.faded = (self._kind.see_through and feet_y < self.depth
                      and self.rect.colliderect(sprite_rect))

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        sprite = self._sprite
        if self.faded:
            if self._faded_sprite is None:
                self._faded_sprite = sprite.copy()
                self._faded_sprite.set_alpha(self.SEE_THROUGH_ALPHA)
            sprite = self._faded_sprite
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        surface.blit(sprite, pos)
        if self.glow > 0:
            # Drawn with the prop, so characters in front of it stay in front
            light = silhouette(self._sprite, self.glow_color)
            alpha = self.GLOW_ALPHA * self.glow
            light.set_alpha(int(alpha * (self.SEE_THROUGH_ALPHA / 255 if self.faded else 1)))
            surface.blit(light, pos)
