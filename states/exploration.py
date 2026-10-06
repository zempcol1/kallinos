"""Exploration state — the overworld: map, player, NPCs, pickups, map scripts."""

from __future__ import annotations

import math
import os
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

import settings as s
from entities.enemy import Enemy, load_enemy_db
from entities.item_pickup import ItemPickup
from entities.npc import NPC
from entities.player import Player
from entities.prop import Prop
from game.state_machine import State
from story import MAP_SCRIPTS, MapScript
from systems.camera import Camera
from systems.inventory_system import load_item_db
from systems.map_system import TileMap
from systems.sprites import Look, interact_bubble
from ui.widgets import draw_fade_strip, draw_shadowed_text, draw_text_box, font

if TYPE_CHECKING:
    from game.game import Game


class Exploration(State):
    """Generic map mode. Story logic lives in the map's ``MapScript``.

    Enter with params: ``{"map": "<map name>"}``. The player comes from
    ``game.session`` so stats and inventory persist across maps.
    """

    FADE_SPEED = 0.5      # Alpha per ms
    TOAST_MS = 2500
    PROMPT_BOB_MS = 300   # interaction bubble bob period
    PROMPT_LIFT = s.SCALED_TILE * 5 // 4   # bubble height above a prop's base
    HUD_STRIP = 36        # height of the soft dark bands behind HUD text

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.tile_map: TileMap | None = None
        self._camera: Camera | None = None
        self._npcs: list[NPC] = []
        self._pickups: list[ItemPickup] = []
        self._item_db: dict = {}
        self._enemy_db: dict = {}
        self._script: MapScript | None = None
        self._target: ItemPickup | Prop | NPC | None = None   # what E would use now
        self._prompt_timer = 0.0

        self._toast_text = ""
        self._toast_expires = 0  # pygame ticks; wall-clock so it also expires under overlays
        self._fade_alpha = 255
        self._fading_in = True
        self._fading_out = False
        self._fade_callback: Callable[[], None] | None = None

    @property
    def player(self) -> Player:
        return self.game.session.player

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        map_name = params.get("map", "tutorial")

        self.tile_map = TileMap(os.path.join(s.MAPS_DIR, f"{map_name}.json"))
        self._item_db = load_item_db()
        self._enemy_db = load_enemy_db()
        self._camera = Camera(self.tile_map.pixel_width, self.tile_map.pixel_height)

        self.player.place(*self.tile_map.player_start)
        self.player.facing = "down"
        self.player.stop()
        self.game.session.checkpoint(map_name)

        self._npcs = [NPC.from_data(nd) for nd in self.tile_map.npc_data]
        self._pickups = [ItemPickup(pd["item_id"], pd["x"], pd["y"], tuple(pd["color"]))
                         for pd in self.tile_map.item_pickup_data]

        script_cls = MAP_SCRIPTS.get(self.tile_map.script, MapScript)
        self._script = script_cls(self)

        self._target = None
        self._toast_text = ""
        self._toast_expires = 0
        self._fade_alpha = 255
        self._fading_in = True
        self._fading_out = False
        self._fade_callback = None

    # ── Helpers for map scripts ──────────────────────────────────────────────

    def get_npc(self, npc_id: str) -> NPC | None:
        for npc in self._npcs:
            if npc.id == npc_id:
                return npc
        return None

    def show_toast(self, text: str) -> None:
        self._toast_text = text
        self._toast_expires = pygame.time.get_ticks() + self.TOAST_MS

    def push_dialogue(self, lines: list[tuple[str, str]], on_complete: str | None = None) -> None:
        """Show dialogue; ``on_complete`` is passed back to the script when it ends."""
        self._push("dialogue", {"lines": lines, "on_complete": on_complete,
                                "looks": self._speaker_looks()})

    def _speaker_looks(self) -> dict[str, Look]:
        """Speaker name -> Look, so the dialogue box can show their portraits."""
        looks = {npc.name: npc.look for npc in self._npcs}
        looks[self.player.name] = self.player.look
        return looks

    def start_combat(self, enemy_id: str, can_flee: bool = True, hint: str | None = None) -> None:
        self._push("combat", {
            "player": self.player,
            "enemy": Enemy(self._enemy_db[enemy_id]),
            "can_flee": can_flee,
            "hint": hint,
        })

    def fade_out(self, callback: Callable[[], None]) -> None:
        """Fade to black, then call ``callback``."""
        self._fading_out = True
        self._fade_alpha = 0
        self._fade_callback = callback

    def _push(self, state_name: str, params: dict) -> None:
        """Push an overlay state (dialogue/combat), freezing the player in place."""
        self.player.stop()
        self.game.state_machine.push(state_name, params)

    # ── Callbacks from overlay states ────────────────────────────────────────

    def on_dialogue_complete(self, event_id: str) -> None:
        self._script.on_dialogue_complete(event_id)

    def on_combat_victory(self) -> None:
        self._script.on_combat_victory()

    # ── Input & update ───────────────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._fading_in or self._fading_out:
            return  # No input during fades

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                self.game.state_machine.change("main_menu")
                return
            if event.key in (pygame.K_e, pygame.K_RETURN) and self._script.allows_control():
                self._try_interact()

    def _find_target(self) -> ItemPickup | Prop | NPC | None:
        """The pickup under the player, or the fig tree / person they face."""
        feet, reach = self.player.rect, self.player.reach_rect()
        for pickup in self._pickups:
            if not pickup.collected and pickup.interaction_rect().colliderect(feet):
                return pickup
        for prop in self.tile_map.props:
            if prop.can_harvest and reach.colliderect(prop.interaction_rect()):
                return prop
        for npc in self._npcs:
            if npc.visible and npc.dialogue_idle and reach.colliderect(npc.interaction_rect()):
                return npc
        return None

    def _try_interact(self) -> None:
        """Pick up, harvest or talk to whatever is in reach."""
        target = self._find_target()
        if isinstance(target, ItemPickup):
            item_data = self._give_item(target.item_id)
            if item_data:
                target.collected = True
                self.show_toast(f"Picked up {item_data['name']}")
        elif isinstance(target, Prop):
            item_data = self._give_item(target.pick())
            if item_data:
                self.show_toast(target.harvest_text or f"Picked {item_data['name']}")
        elif isinstance(target, NPC):
            target.face_towards(self.player.x, self.player.y)
            self.push_dialogue([(target.name, line) for line in target.dialogue_idle])

    def _give_item(self, item_id: str | None) -> dict | None:
        """Add an item to the inventory (equipping weapons); returns its data."""
        item_data = self._item_db.get(item_id)
        if item_data:
            self.player.inventory.add_item(dict(item_data))
            if item_data.get("type") == "weapon":
                self.player.inventory.equip_weapon(item_data["id"])
        return item_data

    def update(self, dt: float) -> None:
        if self._fading_in:
            self._fade_alpha = max(0, self._fade_alpha - int(dt * self.FADE_SPEED))
            if self._fade_alpha <= 0:
                self._fading_in = False
                if self.tile_map.intro_toast:
                    self.show_toast(self.tile_map.intro_toast)
                self._script.on_start()
            return

        if self._fading_out:
            self._fade_alpha = min(255, self._fade_alpha + int(dt * self.FADE_SPEED))
            if self._fade_alpha >= 255:
                self._fading_out = False
                callback, self._fade_callback = self._fade_callback, None
                if callback:
                    callback()
            return

        if self._script.allows_control():
            keys = pygame.key.get_pressed()
            # NPCs block, except one already overlapping the player (no getting stuck)
            feet = self.player.rect
            blockers = [npc.rect for npc in self._npcs
                        if npc.visible and not npc.rect.colliderect(feet)]
            self.player.handle_input(keys, dt, self.tile_map.collisions + blockers)
            self._target = self._find_target()
        else:
            self.player.stop()
            self._target = None
        self._prompt_timer += dt

        sprite_rect, feet_y = self.player.sprite_rect, self.player.depth
        for prop in self.tile_map.props:
            prop.update_fade(sprite_rect, feet_y)
        self._camera.follow(self.player.x, self.player.y)
        for pickup in self._pickups:
            pickup.update(dt)
        for npc in self._npcs:
            npc.update(dt)
        self._script.update(dt)

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        cam_x = self._camera.x if self._camera else 0
        cam_y = self._camera.y if self._camera else 0

        # Clear first: maps smaller than the screen don't cover it
        surface.fill(s.COLOR_BLACK)
        self.tile_map.render(surface, cam_x, cam_y)

        # Props and characters back-to-front, so lower ones overlap higher ones
        entities = [*self.tile_map.props, *self._pickups, *self._npcs, self.player]
        for entity in sorted(entities, key=lambda e: e.depth):
            entity.render(surface, cam_x, cam_y)

        self.tile_map.render_overhead(surface, cam_x, cam_y)
        self._script.render(surface, cam_x, cam_y)
        if self._target is not None and self.game.state_machine.current is self:
            self._render_prompt(surface, cam_x, cam_y)
        self._render_hud(surface)

        if self._toast_text and pygame.time.get_ticks() < self._toast_expires:
            draw_text_box(surface, self._toast_text, font(26),
                          center=(s.SCREEN_WIDTH // 2, 60), fill=s.COLOR_TOAST_BG)

        if self._fade_alpha > 0:
            fade_surf = pygame.Surface((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
            fade_surf.fill(s.COLOR_BLACK)
            fade_surf.set_alpha(self._fade_alpha)
            surface.blit(fade_surf, (0, 0))

    def _render_prompt(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """A bobbing speech bubble over whatever E would interact with."""
        target = self._target
        if isinstance(target, NPC):
            anchor = target.sprite_rect.midtop
        elif isinstance(target, Prop):
            anchor = (target.interaction_rect().centerx, target.depth - self.PROMPT_LIFT)
        else:
            anchor = target.rect.midtop
        bubble = interact_bubble()
        bob = round(math.sin(self._prompt_timer / self.PROMPT_BOB_MS)) * s.SCALE
        surface.blit(bubble, bubble.get_rect(midbottom=(anchor[0] - cam_x,
                                                        anchor[1] - cam_y + bob)))

    def _render_hud(self, surface: pygame.Surface) -> None:
        # Location, top-left, with a gold diamond
        draw_fade_strip(surface, pygame.Rect(0, 0, s.SCREEN_WIDTH, self.HUD_STRIP))
        x, y = 14, 8
        cy = y + 8
        pygame.draw.polygon(surface, s.COLOR_ACCENT_GOLD,
                            [(x, cy - 5), (x + 5, cy), (x, cy + 5), (x - 5, cy)])
        draw_shadowed_text(surface, self.tile_map.display_name, font(24), (x + 12, y))

        # Controls hint, only while the player is in control (not under dialogue)
        if self.game.state_machine.current is not self or not self._script.allows_control():
            return
        draw_fade_strip(surface, pygame.Rect(0, s.SCREEN_HEIGHT - self.HUD_STRIP,
                                             s.SCREEN_WIDTH, self.HUD_STRIP), fade_down=False)
        hint = "WASD / Arrows  move      E / Enter  interact      Esc  menu"
        draw_shadowed_text(surface, hint, font(22), (14, s.SCREEN_HEIGHT - 22),
                           s.COLOR_TEXT_DIM)
