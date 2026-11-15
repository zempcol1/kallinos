"""The garden tutorial: Niko vanishes, the branch, the frog, the shimmer."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

import settings as s
from story.map_script import MapScript
from systems import content
from ui.effects import draw_motes

if TYPE_CHECKING:
    from entities.npc import NPC
    from states.exploration import Exploration


class TutorialScript(MapScript):
    """Linear tutorial flow. Text, ids and positions come from tutorial.json.

    Phases: intro → npc_leaves → explore → reveal → combat → npc_drops →
    victory → shimmer → done.
    """

    VANISH_MS = 400                       # Niko fades out behind the boulder
    DROP_HEIGHT = s.SCALED_TILE * 2       # Niko falls out of the olive crown
    GRAVITY = 0.004                       # px per ms², for the fall
    GLOW_PULSE_MS = 300.0                 # the shimmering tree's glow period
    MOTES = 14                            # golden motes rising from the shimmering tree
    MOTE_RISE_MS = 1600
    MOTE_START = 0.55                     # motes rise from this height of the tree sprite
    MOTE_SWAY = s.SCALE * 2

    def __init__(self, scene: Exploration) -> None:
        super().__init__(scene)
        self._data = content.load_script("tutorial")
        self._phase = "intro"
        self._timer = 0.0
        self._fall_speed = 0.0
        self._safe_pos = (scene.player.x, scene.player.y)

    def _lines(self, key: str) -> list[tuple[str, str]]:
        """A dialogue from the script data as (speaker, text) pairs."""
        return [(speaker, text) for speaker, text in self._data[key]]

    def _missing_npc(self) -> NPC | None:
        return self.scene.get_npc(self._data["missing_npc"])

    def on_start(self) -> None:
        self.scene.push_dialogue(self._lines("intro"), self._npc_leaves)

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
        elif self._phase == "shimmer":
            prop = self.scene.tile_map.get_prop(self._data["shimmer_object"])
            if prop:
                prop.glow = abs(math.sin(self._timer / self.GLOW_PULSE_MS))
            if self._timer > self._data["shimmer_ms"]:
                self._phase = "done"
                self.scene.fade_out(self._show_title_card)

    # ── Beats, in story order ────────────────────────────────────────────────

    def _npc_leaves(self) -> None:
        """After the intro: Niko walks off to prove his point."""
        npc = self._missing_npc()
        if npc:
            npc.walk(self._data["missing_npc_path"])
        self._phase = "npc_leaves"

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
        self.scene.game.audio.play("croak")

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
            self.scene.push_dialogue(self._lines("missing_item"))
            player.x, player.y = self._safe_pos
            return

        self._phase = "reveal"
        self.scene.push_dialogue(self._lines("reveal"), self._start_fight)

    def _start_fight(self) -> None:
        self._phase = "combat"
        self.scene.start_combat(self._data["enemy"], can_flee=False,
                                hint=self._data["combat_hint"], on_victory=self._npc_returns)

    def _npc_returns(self) -> None:
        """After the fight: Niko drops out of the olive tree he hid in."""
        npc = self._missing_npc()
        if npc is None:
            self._celebrate()
            return
        npc.visible = True
        npc.place(*self._data["missing_npc_return"])
        npc.facing = "down"
        npc.lift = self.DROP_HEIGHT
        self._fall_speed = 0.0
        self._phase = "npc_drops"

    def _update_npc_drop(self, dt: float) -> None:
        npc = self._missing_npc()
        self._fall_speed += self.GRAVITY * dt
        npc.lift = max(0.0, npc.lift - self._fall_speed * dt)
        if npc.lift <= 0:
            self.scene.game.audio.play("thud")
            npc.face_towards(self.scene.player.x, self.scene.player.y)
            self._celebrate()

    def _celebrate(self) -> None:
        self._phase = "victory"
        self.scene.push_dialogue(self._lines("victory"), self._start_shimmer)

    def _start_shimmer(self) -> None:
        self._phase = "shimmer"
        self._timer = 0.0
        self.scene.game.audio.play("chime")

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
        # Athena's olive pulses gold (its prop draws the glow, see ``update``);
        # motes drift up out of its crown
        rect = prop.rect.move(-cam_x, -cam_y)
        rise = rect.h * self.MOTE_START
        draw_motes(surface, (rect.left, rect.top + rise), (rect.w, rise), self._timer,
                   count=self.MOTES, rise_ms=self.MOTE_RISE_MS, sway=self.MOTE_SWAY,
                   glints=True, snap=True)
