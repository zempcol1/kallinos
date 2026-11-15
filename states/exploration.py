"""Exploration state — the overworld: map, player, NPCs, pickups, map scripts."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

import settings as s
from entities.enemy import Enemy
from entities.interactable import Interactable
from entities.item_pickup import ItemPickup
from entities.npc import NPC
from entities.player import Player
from game.state_machine import State
from story import MAP_SCRIPTS, MapScript
from systems import content, controls
from systems.ambience import Ambience
from systems.camera import Camera
from systems.map_system import TILE_EARTH, TILE_PATH, TileMap
from systems.sprites import Look, interact_bubble
from ui.effects import ScreenFade
from ui.widgets import draw_fade_strip, draw_shadowed_text, draw_text_box, font

if TYPE_CHECKING:
    from game.game import Game


class Exploration(State):
    """Generic map mode. Story logic lives in the map's ``MapScript``.

    Enter with params: ``{"map": "<map name>"}`` (default: the session's
    current map). The player comes from ``game.session`` so stats and
    inventory persist across maps.
    """

    TOAST_MS = 2500
    TOAST_Y = 60
    PROMPT_BOB_MS = 300   # interaction bubble bob period
    HUD_STRIP = 36        # height of the soft dark bands behind HUD text
    HUD_MARGIN = (14, 8)  # location text offset from the top-left corner
    HUD_DIAMOND = 5       # half-size of the gold diamond before the location
    STEP_FRAMES = (1, 3)  # walk-cycle frames where a foot touches down
    GRASS_STEP_VOLUME = 0.5
    CONTROLS_HINT = "WASD / Arrows  move     E / Enter  interact     M  sound     Esc  menu"

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.tile_map: TileMap | None = None
        self._camera: Camera | None = None
        self._npcs: list[NPC] = []
        self._pickups: list[ItemPickup] = []
        self._script: MapScript | None = None
        self._ambience: Ambience | None = None
        self._target: Interactable | None = None   # what the interact key would use now
        self._prompt_timer = 0.0
        self._step_frame = 0
        self._toast_text = ""
        self._toast_expires = 0  # pygame ticks; wall-clock so it also expires under overlays
        self._fade = ScreenFade()

    @property
    def player(self) -> Player:
        return self.game.session.player

    def enter(self, params: dict | None = None) -> None:
        map_name = (params or {}).get("map", self.game.session.current_map)

        self.tile_map = TileMap.load(map_name)
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
        self._ambience = Ambience(self.tile_map.ambience, self.tile_map.props, map_name)
        self.game.audio.play_music(self.tile_map.music)

        self._target = None
        self._step_frame = 0
        self._toast_text = ""
        self._toast_expires = 0
        self._fade.fade_in(self._on_faded_in)

    def resume(self) -> None:
        """Back from an overlay (combat changes the music): the map's track again."""
        self.game.audio.play_music(self.tile_map.music)

    def _on_faded_in(self) -> None:
        if self.tile_map.intro_toast:
            self.show_toast(self.tile_map.intro_toast)
        self._script.on_start()

    # ── Helpers for map scripts and interactables ────────────────────────────

    def get_npc(self, npc_id: str) -> NPC | None:
        for npc in self._npcs:
            if npc.id == npc_id:
                return npc
        return None

    def show_toast(self, text: str) -> None:
        self._toast_text = text
        self._toast_expires = pygame.time.get_ticks() + self.TOAST_MS

    def give_item(self, item_id: str | None) -> dict | None:
        """Put an item in the player's inventory (weapons are equipped at once).

        Returns the item's data, or None for an unknown id.
        """
        item_data = content.items().get(item_id)
        if item_data:
            self.player.inventory.add_item(item_id)
            if item_data.get("type") == "weapon":
                self.player.inventory.equip_weapon(item_id)
        return item_data

    def push_dialogue(self, lines: list[tuple[str, str]],
                      on_complete: Callable[[], None] | None = None) -> None:
        """Show dialogue; ``on_complete`` is called once the last line is dismissed."""
        self._push("dialogue", {"lines": lines, "on_complete": on_complete,
                                "looks": self._speaker_looks()})

    def _speaker_looks(self) -> dict[str, Look]:
        """Speaker name -> Look, so the dialogue box can show their portraits."""
        looks = {npc.name: npc.look for npc in self._npcs}
        looks[self.player.name] = self.player.look
        return looks

    def start_combat(self, enemy_id: str, can_flee: bool = True, hint: str | None = None,
                     on_victory: Callable[[], None] | None = None) -> None:
        """Fight an enemy from enemies.json; ``on_victory`` is called after a win."""
        self._push("combat", {
            "player": self.player,
            "enemy": Enemy(content.enemies()[enemy_id]),
            "can_flee": can_flee,
            "hint": hint,
            "on_victory": on_victory,
        })

    def fade_out(self, callback: Callable[[], None]) -> None:
        """Fade to black, then call ``callback``."""
        self._fade.fade_out(callback)

    def _push(self, state_name: str, params: dict) -> None:
        """Push an overlay state (dialogue/combat), freezing the player in place."""
        self.player.stop()
        self.game.state_machine.push(state_name, params)

    # ── Input & update ───────────────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._fade.active:
            return  # No input during fades

        for key in controls.pressed_keys(events):
            if key in controls.CANCEL:
                self.game.state_machine.change("main_menu")
                return
            if key in controls.INTERACT and self._script.allows_control():
                target = self._find_target()
                if target is not None:
                    target.interact(self)

    def _find_target(self) -> Interactable | None:
        """The pickup under the player, or the fig tree / person they face."""
        candidates: list[Interactable] = [*self._pickups, *self.tile_map.props, *self._npcs]
        return next((thing for thing in candidates if thing.in_reach(self.player)), None)

    def update(self, dt: float) -> None:
        if self._fade.active:
            self._fade.update(dt)
            return

        if self._script.allows_control():
            # NPCs block, except one already overlapping the player (no getting stuck)
            feet = self.player.rect
            blockers = [npc.rect for npc in self._npcs
                        if npc.visible and not npc.rect.colliderect(feet)]
            self.player.handle_input(pygame.key.get_pressed(), dt,
                                     self.tile_map.collisions + blockers)
            self._target = self._find_target()
        else:
            self.player.stop()
            self._target = None
        self._prompt_timer += dt

        sprite_rect, feet_y = self.player.sprite_rect, self.player.depth
        for prop in self.tile_map.props:
            prop.update_fade(sprite_rect, feet_y)
        self._camera.follow(self.player.x, self.player.y)
        self._update_footsteps()
        view = pygame.Rect(self._camera.x, self._camera.y, s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        self._ambience.update(dt, view)
        for pickup in self._pickups:
            pickup.update(dt)
        for npc in self._npcs:
            npc.update(dt)
        self._script.update(dt)

    def _update_footsteps(self) -> None:
        """Each time a foot lands, kick up dust on bare ground."""
        frame = self.player.frame if self.player.moving else 0
        if frame != self._step_frame and frame in self.STEP_FRAMES:
            feet = self.player.rect
            bare = self.tile_map.tile_at(feet.centerx, feet.bottom) in (TILE_PATH, TILE_EARTH)
            if bare:
                self._ambience.dust(feet.centerx, feet.bottom - s.SCALE)
            # Steps sound firmer on bare ground than on grass
            self.game.audio.play("step" if frame == self.STEP_FRAMES[0] else "step_alt",
                                 1.0 if bare else self.GRASS_STEP_VOLUME)
        self._step_frame = frame

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        cam_x, cam_y = self._camera.x, self._camera.y

        # Clear first: maps smaller than the screen don't cover it
        surface.fill(s.COLOR_BLACK)
        self.tile_map.render(surface, cam_x, cam_y)

        # Props and characters back-to-front, so lower ones overlap higher ones
        entities = [*self.tile_map.props, *self._pickups, *self._npcs, self.player]
        for entity in sorted(entities, key=lambda e: e.depth):
            entity.render(surface, cam_x, cam_y)

        self.tile_map.render_overhead(surface, cam_x, cam_y)
        self._ambience.render(surface, cam_x, cam_y)
        self._ambience.render_light(surface)
        self._script.render(surface, cam_x, cam_y)
        on_top = self.game.state_machine.current is self
        if self._target is not None and on_top:
            self._render_prompt(surface, cam_x, cam_y)
        self._render_hud(surface, show_controls=on_top and self._script.allows_control())

        if self._toast_text and pygame.time.get_ticks() < self._toast_expires:
            draw_text_box(surface, self._toast_text, font(30),
                          center=(s.SCREEN_WIDTH // 2, self.TOAST_Y), fill=s.COLOR_TOAST_BG)
        self._fade.render(surface)

    def _render_prompt(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """A bobbing speech bubble over whatever the interact key would use."""
        x, y = self._target.prompt_anchor
        bubble = interact_bubble()
        bob = round(math.sin(self._prompt_timer / self.PROMPT_BOB_MS)) * s.SCALE
        surface.blit(bubble, bubble.get_rect(midbottom=(x - cam_x, y - cam_y + bob)))

    def _render_hud(self, surface: pygame.Surface, show_controls: bool) -> None:
        # Location, top-left, with a gold diamond
        draw_fade_strip(surface, pygame.Rect(0, 0, s.SCREEN_WIDTH, self.HUD_STRIP))
        x, y = self.HUD_MARGIN
        r = self.HUD_DIAMOND
        cy = y + 8
        pygame.draw.polygon(surface, s.COLOR_ACCENT_GOLD,
                            [(x, cy - r), (x + r, cy), (x, cy + r), (x - r, cy)])
        draw_shadowed_text(surface, self.tile_map.display_name, font(24), (x + 12, y))

        # Controls hint, only while the player is in control (not under dialogue)
        if not show_controls:
            return
        draw_fade_strip(surface, pygame.Rect(0, s.SCREEN_HEIGHT - self.HUD_STRIP,
                                             s.SCREEN_WIDTH, self.HUD_STRIP), fade_down=False)
        draw_shadowed_text(surface, self.CONTROLS_HINT, font(22), (x, s.SCREEN_HEIGHT - 22),
                           s.COLOR_TEXT_DIM)
