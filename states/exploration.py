"""Exploration state — the main overworld / map mode with tutorial scripting."""

from __future__ import annotations

import math
import os
from typing import TYPE_CHECKING

import pygame

import settings as s
from entities.enemy import Enemy, load_enemy_db
from entities.item_pickup import ItemPickup
from entities.npc import NPC
from entities.player import Player
from game.state_machine import State
from systems.camera import Camera
from systems.inventory_system import load_item_db
from systems.map_system import TileMap
from systems.sprites import OBJECT_GENERATORS, silhouette
from ui.widgets import draw_panel, draw_text_box, font

if TYPE_CHECKING:
    from game.game import Game


class Exploration(State):
    """Full exploration state with map, player, NPCs, items, and triggers."""

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._tile_map: TileMap | None = None
        self._camera: Camera | None = None
        self._player: Player | None = None
        self._npcs: list[NPC] = []
        self._pickups: list[ItemPickup] = []
        self._item_db: dict = {}
        self._enemy_db: dict = {}

        # Tutorial script state
        self._script_phase = "init"  # init -> intro_dialogue -> explore -> boulder_cutscene -> combat -> post_combat -> done
        self._triggered_events: set[str] = set()
        self._toast_text = ""
        self._toast_timer = 0.0
        self._fade_alpha = 255
        self._fading_in = True
        self._fading_out = False
        self._fade_callback: str | None = None
        self._shimmer_timer = 0.0
        self._show_shimmer = False
        self._tutorial_complete = False
        self._tutorial_complete_timer = 0.0
        self._is_tutorial = True
        self._current_map = "tutorial"


    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        map_name = params.get("map", "tutorial")

        # Load data
        map_path = os.path.join(s.MAPS_DIR, f"{map_name}.json")
        self._tile_map = TileMap(map_path)
        self._item_db = load_item_db()
        self._enemy_db = load_enemy_db()

        # Camera
        self._camera = Camera(self._tile_map.pixel_width, self._tile_map.pixel_height)

        # Player
        sx, sy = self._tile_map.player_start
        self._player = Player(sx, sy)

        # NPCs
        self._npcs = [NPC.from_data(nd) for nd in self._tile_map.npc_data]

        # Item pickups
        self._pickups = []
        for pd in self._tile_map.item_pickup_data:
            pickup = ItemPickup(pd["item_id"], pd["x"], pd["y"], tuple(pd["color"]))
            self._pickups.append(pickup)

        # Determine if this is the tutorial or a free-roam map
        self._is_tutorial = (map_name == "tutorial")
        self._current_map = map_name

        # Reset script
        self._script_phase = "init" if self._is_tutorial else "explore"
        self._triggered_events.clear()
        self._toast_text = ""
        self._toast_timer = 0.0
        self._fade_alpha = 255
        self._fading_in = True
        self._fading_out = False
        self._fade_callback = None
        self._shimmer_timer = 0.0
        self._show_shimmer = False
        self._tutorial_complete = False
        self._tutorial_complete_timer = 0.0

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._tutorial_complete:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # Progress to the village — Act I begins
                    self.game.state_machine.change("exploration", {"map": "village"})
            return

        if self._fading_in or self._fading_out:
            return  # No input during fades

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                self.game.state_machine.change("main_menu")
                return

            if event.key in (pygame.K_e, pygame.K_RETURN):
                self._try_interact()

    def _try_interact(self) -> None:
        """Check for NPC interaction or item pickup."""
        if self._script_phase not in ("explore", "post_combat"):
            return

        pr = self._player.rect

        # Item pickups
        for pickup in self._pickups:
            if not pickup.collected and pr.colliderect(pickup.rect.inflate(20, 20)):
                item_data = self._item_db.get(pickup.item_id)
                if item_data:
                    self._player.inventory.add_item(dict(item_data))
                    # Auto-equip weapons
                    if item_data.get("type") == "weapon":
                        self._player.inventory.equip_weapon(item_data["id"])
                    pickup.collected = True
                    self._show_toast(f"Picked up {item_data['name']}")
                return

        # NPC interaction
        for npc in self._npcs:
            if npc.visible and npc.dialogue_idle and pr.colliderect(npc.interaction_rect()):
                npc.face_towards(self._player.x, self._player.y)
                lines = [(npc.name, line) for line in npc.dialogue_idle]
                self._push("dialogue", {"lines": lines})
                return

    def update(self, dt: float) -> None:
        # Fade in
        if self._fading_in:
            self._fade_alpha = max(0, self._fade_alpha - int(dt * 0.5))
            if self._fade_alpha <= 0:
                self._fading_in = False
                if self._script_phase == "init" and self._is_tutorial:
                    self._start_intro()
                elif not self._is_tutorial:
                    self._show_toast("The next morning...")
            return

        # Fade out
        if self._fading_out:
            self._fade_alpha = min(255, self._fade_alpha + int(dt * 0.5))
            if self._fade_alpha >= 255:
                self._fading_out = False
                if self._fade_callback == "tutorial_complete":
                    self._tutorial_complete = True
                    self._tutorial_complete_timer = 0.0
            return

        # Tutorial complete screen
        if self._tutorial_complete:
            self._tutorial_complete_timer += dt
            return

        # Player movement (only during explore phase)
        if self._script_phase in ("explore", "post_combat"):
            keys = pygame.key.get_pressed()
            self._player.handle_input(keys, dt, self._tile_map.collisions)
        else:
            self._player.stop()

        # Camera
        self._camera.follow(self._player.x, self._player.y)

        # Pickups bobbing
        for pickup in self._pickups:
            pickup.update(dt)

        # Toast timer
        if self._toast_timer > 0:
            self._toast_timer -= dt

        # Shimmer effect
        if self._show_shimmer:
            self._shimmer_timer += dt
            if self._shimmer_timer > 2000:
                self._show_shimmer = False
                self._start_fade_out("tutorial_complete")

        # Trigger checks
        if self._script_phase == "explore":
            self._check_triggers()

    def _start_intro(self) -> None:
        """Kick off the intro dialogue sequence."""
        self._script_phase = "intro_dialogue"

        # Make Niko visible for the intro
        niko = self._get_npc("niko")
        if niko:
            niko.visible = True

        lines = [
            ("Niko", "I'm telling you, something lives behind that boulder."),
            ("Niko", "I heard it last night... a wet, slapping sound."),
            ("Doros", "You heard a fish flopping in the creek. Sit down."),
            ("Niko", "Watch. I'll prove it."),
            ("Doros", "Niko, wait--"),
        ]
        self._push("dialogue", {
            "lines": lines,
            "on_complete": "intro_done",
        })

    def on_dialogue_complete(self, event_id: str) -> None:
        """Called by Dialogue state when it finishes."""
        if event_id == "intro_done":
            # Niko disappears
            niko = self._get_npc("niko")
            if niko:
                niko.visible = False
            self._script_phase = "explore"
            # Show a brief croak message
            self._show_toast("*CROAK!*  ...silence.")

        elif event_id == "boulder_cutscene_done":
            self._start_combat()

        elif event_id == "post_combat_done":
            self._start_shimmer()

        elif event_id == "branch_warning":
            pass  # Just returns to explore

    def _check_triggers(self) -> None:
        """Check if player stepped on a trigger zone."""
        boulder_zone = self._tile_map.get_trigger("boulder_zone")
        if boulder_zone and self._player.rect.colliderect(boulder_zone):
            if "boulder" not in self._triggered_events:
                # Check if player has the branch
                if not self._player.inventory.has_item("olive_branch"):
                    self._push("dialogue", {
                        "lines": [("Doros", "Grab that branch, at least! Are you crazy?!")],
                        "on_complete": "branch_warning",
                    })
                    # Push player back
                    self._player.x -= s.SCALED_TILE * 2
                    return

                self._triggered_events.add("boulder")
                self._script_phase = "boulder_cutscene"
                lines = [
                    ("", "Niko is nowhere to be seen."),
                    ("", "Instead, crouched in the shadows..."),
                    ("", "A fat, hissing frog the size of a cat stares back at you."),
                    ("", "Its amber eyes catch the fading sunlight."),
                    ("Kallinos", "What-- what IS that?!"),
                    ("", "The Vatrachos puffs up and lunges!"),
                ]
                self._push("dialogue", {
                    "lines": lines,
                    "on_complete": "boulder_cutscene_done",
                })

    def _start_combat(self) -> None:
        """Transition to the combat state."""
        enemy_data = self._enemy_db.get("vatrachos")
        if not enemy_data:
            return
        enemy = Enemy(enemy_data)
        self._push("combat", {
            "player": self._player,
            "enemy": enemy,
            "is_tutorial": True,
        })

    def on_combat_victory(self) -> None:
        """Called when combat ends in victory."""
        self._script_phase = "post_combat"
        # Niko reappears
        niko = self._get_npc("niko")
        if niko:
            niko.visible = True
            # Move Niko near the tree
            niko.x = 12 * s.SCALED_TILE + s.SCALED_TILE // 2
            npc_y = 7 * s.SCALED_TILE + s.SCALED_TILE // 2
            niko.y = npc_y

        lines = [
            ("Niko", "You... you actually hit it?!"),
            ("Kallinos", "You were IN the tree?!"),
            ("Niko", "It JUMPED at me! What was I supposed to do?!"),
            ("Doros", "Is it gone? I heard croaking-- are you both alive?"),
            ("Niko", "Kallinos chased it off. With a stick."),
            ("Doros", "...A stick."),
            ("", "..."),
            ("Doros", "Brave. Stupid, but brave."),
        ]
        self._push("dialogue", {
            "lines": lines,
            "on_complete": "post_combat_done",
        })

    def _start_shimmer(self) -> None:
        """Start the olive tree shimmer foreshadowing."""
        self._show_shimmer = True
        self._shimmer_timer = 0.0

    def _start_fade_out(self, callback: str) -> None:
        self._fading_out = True
        self._fade_alpha = 0
        self._fade_callback = callback

    def _show_toast(self, text: str) -> None:
        self._toast_text = text
        self._toast_timer = 2500.0

    def _push(self, state_name: str, params: dict) -> None:
        """Push an overlay state (dialogue/combat), freezing the player in place."""
        self._player.stop()
        self.game.state_machine.push(state_name, params)

    def _get_npc(self, npc_id: str) -> NPC | None:
        for npc in self._npcs:
            if npc.id == npc_id:
                return npc
        return None

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if self._tutorial_complete:
            self._render_tutorial_complete(surface)
            return

        cam_x = self._camera.x if self._camera else 0
        cam_y = self._camera.y if self._camera else 0

        # Clear first: maps smaller than the screen don't cover it
        surface.fill(s.COLOR_BLACK)
        self._tile_map.render(surface, cam_x, cam_y)

        # Entities, back-to-front so lower ones overlap higher ones
        entities = [*self._pickups, *self._npcs, self._player]
        for entity in sorted(entities, key=lambda e: e.rect.bottom):
            entity.render(surface, cam_x, cam_y)

        self._tile_map.render_overhead(surface, cam_x, cam_y)

        if self._show_shimmer:
            self._render_shimmer(surface, cam_x, cam_y)

        self._render_hud(surface)

        if self._toast_timer > 0 and self._toast_text:
            draw_text_box(surface, self._toast_text, font(26),
                          center=(s.SCREEN_WIDTH // 2, 60), fill=s.COLOR_TOAST_BG)

        if self._fade_alpha > 0:
            fade_surf = pygame.Surface((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
            fade_surf.fill(s.COLOR_BLACK)
            fade_surf.set_alpha(self._fade_alpha)
            surface.blit(fade_surf, (0, 0))

    def _render_hud(self, surface: pygame.Surface) -> None:
        # Location bar at top
        draw_panel(surface, pygame.Rect(0, 0, s.SCREEN_WIDTH, 24), fill=(0, 0, 0, 120),
                   border=None)
        loc_surf = font(22).render(self._tile_map.display_name, True, s.COLOR_WHITE)
        surface.blit(loc_surf, (10, 4))

        # Controls hint
        draw_panel(surface, pygame.Rect(0, s.SCREEN_HEIGHT - 20, s.SCREEN_WIDTH, 20),
                   fill=(0, 0, 0, 100), border=None)
        hint = "[WASD/Arrows] Move  [E/Enter] Interact  [ESC] Menu"
        hint_surf = font(22).render(hint, True, s.COLOR_TEXT_DIM)
        surface.blit(hint_surf, (10, s.SCREEN_HEIGHT - 18))

    def _render_shimmer(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Pulse a golden glow over the olive tree's crown (foreshadowing)."""
        canopy = self._tile_map.find_object("tree_canopy")
        if canopy is None:
            return
        tiles_w, tiles_h = canopy.w // s.SCALED_TILE, canopy.h // s.SCALED_TILE
        glow = silhouette(OBJECT_GENERATORS["tree_canopy"](tiles_w, tiles_h),
                          s.COLOR_TITLE_GOLD)
        glow.set_alpha(int(abs(math.sin(self._shimmer_timer / 300.0)) * 180))
        surface.blit(glow, canopy.move(-cam_x, -cam_y))

    def _render_tutorial_complete(self, surface: pygame.Surface) -> None:
        surface.fill(s.COLOR_BLACK)
        cx, cy = s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT // 2
        lines = [
            ("Tutorial Complete", font(48), s.COLOR_TITLE_GOLD, -40),
            ("Chapter 1 — The Village", font(26), s.COLOR_ACCENT_GOLD, 0),
        ]
        if self._tutorial_complete_timer > 1000:
            lines.append(("Press Enter to continue", font(26), s.COLOR_TEXT_DIM, 40))
        for text, text_font, color, dy in lines:
            text_surf = text_font.render(text, True, color)
            surface.blit(text_surf, text_surf.get_rect(center=(cx, cy + dy)))
