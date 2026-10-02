"""The garden tutorial: Niko vanishes, the branch, the frog, the shimmer."""

from __future__ import annotations

import json
import math
import os
from typing import TYPE_CHECKING

import pygame

import settings as s
from story.map_script import MapScript
from systems.sprites import OBJECT_GENERATORS, silhouette

if TYPE_CHECKING:
    from states.exploration import Exploration


def _lines(raw: list[list[str]]) -> list[tuple[str, str]]:
    return [(speaker, text) for speaker, text in raw]


class TutorialScript(MapScript):
    """Linear tutorial flow. Text, ids and positions come from tutorial.json.

    Phases: intro → explore → reveal → combat → victory → shimmer → done.
    """

    DATA_FILE = os.path.join(s.DATA_DIR, "scripts", "tutorial.json")

    def __init__(self, scene: Exploration) -> None:
        super().__init__(scene)
        with open(self.DATA_FILE, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._phase = "intro"
        self._shimmer_timer = 0.0

    def on_start(self) -> None:
        self.scene.push_dialogue(_lines(self._data["intro"]), on_complete="intro_done")

    def allows_control(self) -> bool:
        return self._phase in ("explore", "victory")

    def update(self, dt: float) -> None:
        if self._phase == "explore":
            self._check_trigger()
        elif self._phase == "shimmer":
            self._shimmer_timer += dt
            if self._shimmer_timer > self._data["shimmer_ms"]:
                self._phase = "done"
                self.scene.fade_out(self._show_title_card)

    def _check_trigger(self) -> None:
        zone = self.scene.tile_map.get_trigger(self._data["trigger"])
        player = self.scene.player
        if zone is None or not player.rect.colliderect(zone):
            return

        if not player.inventory.has_item(self._data["required_item"]):
            # Soft block: warn and step the player back out of the zone
            self.scene.push_dialogue(_lines(self._data["missing_item"]))
            player.x -= s.SCALED_TILE * self._data["pushback_tiles"]
            return

        self._phase = "reveal"
        self.scene.push_dialogue(_lines(self._data["reveal"]), on_complete="reveal_done")

    def on_dialogue_complete(self, event_id: str) -> None:
        if event_id == "intro_done":
            npc = self.scene.get_npc(self._data["missing_npc"])
            if npc:
                npc.visible = False
            self._phase = "explore"
            self.scene.show_toast(self._data["intro_toast"])
        elif event_id == "reveal_done":
            self._phase = "combat"
            self.scene.start_combat(self._data["enemy"], can_flee=False,
                                    hint=self._data["combat_hint"])
        elif event_id == "victory_done":
            self._phase = "shimmer"
            self._shimmer_timer = 0.0

    def on_combat_victory(self) -> None:
        self._phase = "victory"
        npc = self.scene.get_npc(self._data["missing_npc"])
        if npc:
            npc.visible = True
            npc.place(*self._data["missing_npc_return"])
        self.scene.push_dialogue(_lines(self._data["victory"]), on_complete="victory_done")

    def _show_title_card(self) -> None:
        card = self._data["title_card"]
        self.scene.game.state_machine.change("title_card", {
            "title": card["title"],
            "subtitle": card["subtitle"],
            "next_state": "exploration",
            "next_params": {"map": card["next_map"]},
        })

    def render(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self._phase != "shimmer":
            return
        # Pulse a golden glow over the olive tree's crown (foreshadowing)
        obj_type = self._data["shimmer_object"]
        rect = self.scene.tile_map.find_object(obj_type)
        if rect is None:
            return
        glow = silhouette(OBJECT_GENERATORS[obj_type](rect.w // s.SCALED_TILE,
                                                      rect.h // s.SCALED_TILE),
                          s.COLOR_TITLE_GOLD)
        glow.set_alpha(int(abs(math.sin(self._shimmer_timer / 300.0)) * 180))
        surface.blit(glow, rect.move(-cam_x, -cam_y))
