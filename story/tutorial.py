"""The garden tutorial: Niko vanishes, the branch, the frog, the shimmer."""

from __future__ import annotations

import json
import math
import os
from typing import TYPE_CHECKING

import pygame

import settings as s
from story.map_script import MapScript
from systems.sprites import silhouette

if TYPE_CHECKING:
    from entities.npc import NPC
    from states.exploration import Exploration


def _lines(raw: list[list[str]]) -> list[tuple[str, str]]:
    return [(speaker, text) for speaker, text in raw]


class TutorialScript(MapScript):
    """Linear tutorial flow. Text, ids and positions come from tutorial.json.

    Phases: intro → npc_leaves → explore → reveal → combat → npc_drops →
    victory → shimmer → done.
    """

    DATA_FILE = os.path.join(s.DATA_DIR, "scripts", "tutorial.json")
    VANISH_MS = 400                       # Niko fades out behind the boulder
    DROP_HEIGHT = s.SCALED_TILE * 2       # Niko falls out of the olive crown
    GRAVITY = 0.004                       # px per ms², for the fall
    MOTES = 14                            # golden motes rising from the shimmering tree
    MOTE_RISE_MS = 1600

    def __init__(self, scene: Exploration) -> None:
        super().__init__(scene)
        with open(self.DATA_FILE, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._phase = "intro"
        self._timer = 0.0
        self._fall_speed = 0.0
        self._safe_pos = (scene.player.x, scene.player.y)

    def _missing_npc(self) -> NPC | None:
        return self.scene.get_npc(self._data["missing_npc"])

    def on_start(self) -> None:
        self.scene.push_dialogue(_lines(self._data["intro"]), on_complete="intro_done")

    def allows_control(self) -> bool:
        return self._phase in ("explore", "victory")

    def update(self, dt: float) -> None:
        self._timer += dt
        if self._phase == "npc_leaves":
            self._update_npc_leaving()
        elif self._phase == "explore":
            self._check_trigger()
        elif self._phase == "npc_drops":
            self._update_npc_drop(dt)
        elif self._phase == "shimmer" and self._timer > self._data["shimmer_ms"]:
            self._phase = "done"
            self.scene.fade_out(self._show_title_card)

    def _update_npc_leaving(self) -> None:
        """Niko walks behind the boulder, then fades away: *croak*."""
        npc = self._missing_npc()
        if npc and npc.walking:
            self._timer = 0.0
            return
        if npc and self._timer < self.VANISH_MS:
            npc.alpha = int(255 * (1 - self._timer / self.VANISH_MS))
            return
        if npc:
            npc.visible = False
            npc.alpha = 255
        self._phase = "explore"
        self.scene.show_toast(self._data["intro_toast"])

    def _update_npc_drop(self, dt: float) -> None:
        npc = self._missing_npc()
        self._fall_speed += self.GRAVITY * dt
        npc.lift = max(0.0, npc.lift - self._fall_speed * dt)
        if npc.lift <= 0:
            npc.face_towards(self.scene.player.x, self.scene.player.y)
            self._phase = "victory"
            self.scene.push_dialogue(_lines(self._data["victory"]), on_complete="victory_done")

    def _check_trigger(self) -> None:
        zone = self.scene.tile_map.get_trigger(self._data["trigger"])
        player = self.scene.player
        if zone is None:
            return
        if not player.rect.colliderect(zone):
            # Remember a spot comfortably outside the zone to send the player back to
            margin = s.SCALED_TILE * self._data["pushback_tiles"]
            if not player.rect.colliderect(zone.inflate(margin * 2, margin * 2)):
                self._safe_pos = (player.x, player.y)
            return

        if not player.inventory.has_item(self._data["required_item"]):
            # Soft block: warn and step the player back out of the zone
            self.scene.push_dialogue(_lines(self._data["missing_item"]))
            player.x, player.y = self._safe_pos
            return

        self._phase = "reveal"
        self.scene.push_dialogue(_lines(self._data["reveal"]), on_complete="reveal_done")

    def on_dialogue_complete(self, event_id: str) -> None:
        if event_id == "intro_done":
            npc = self._missing_npc()
            if npc:
                npc.walk(self._data["missing_npc_path"])
            self._phase = "npc_leaves"
        elif event_id == "reveal_done":
            self._phase = "combat"
            self.scene.start_combat(self._data["enemy"], can_flee=False,
                                    hint=self._data["combat_hint"])
        elif event_id == "victory_done":
            self._phase = "shimmer"
            self._timer = 0.0

    def on_combat_victory(self) -> None:
        npc = self._missing_npc()
        if npc is None:
            self._phase = "victory"
            self.scene.push_dialogue(_lines(self._data["victory"]), on_complete="victory_done")
            return
        npc.visible = True
        npc.place(*self._data["missing_npc_return"])
        npc.facing = "down"
        npc.lift = self.DROP_HEIGHT
        self._fall_speed = 0.0
        self._phase = "npc_drops"

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
        prop = self.scene.tile_map.get_prop(self._data["shimmer_object"])
        if prop is None:
            return
        # Athena's olive pulses gold (foreshadowing) while motes drift up from it
        rect = prop.rect.move(-cam_x, -cam_y)
        glow = silhouette(prop.sprite, s.COLOR_TITLE_GOLD)
        glow.set_alpha(int(abs(math.sin(self._timer / 300.0)) * 160))
        surface.blit(glow, rect)

        mote = pygame.Surface((s.SCALE, s.SCALE))
        for i in range(self.MOTES):
            t = (self._timer / self.MOTE_RISE_MS + i / self.MOTES) % 1.0
            x = rect.left + rect.w * ((i * 0.618) % 1.0)
            x += math.sin(t * math.tau + i) * s.SCALE * 2
            y = rect.bottom - s.SCALED_TILE - t * rect.h
            mote.fill(s.COLOR_TITLE_GOLD if i % 3 else s.COLOR_WHITE)
            mote.set_alpha(int(math.sin(t * math.pi) * 255))
            surface.blit(mote, (round(x / s.SCALE) * s.SCALE, round(y / s.SCALE) * s.SCALE))
