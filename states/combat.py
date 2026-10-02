"""Turn-based combat state — Harry Potter GBC/GBA style."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

import settings as s
from entities.enemy import Enemy
from game.state_machine import State
from systems.sprites import (
    ENEMY_IDLE_FRAMES, PLAYER_LOOK, character, combat_backdrop, enemy, item, silhouette,
)
from ui.widgets import draw_bar, draw_panel, draw_text_box, font

if TYPE_CHECKING:
    from game.game import Game
    from entities.player import Player


class Combat(State):
    """Turn-based combat.

    Push with params:
        {
            "enemy": Enemy instance,
            "player": Player reference,
            "is_tutorial": bool,
        }
    """

    ACTIONS = ["Attack", "Defend", "Item", "Flee"]

    # Phases
    PHASE_PLAYER_CHOOSE = "player_choose"
    PHASE_PLAYER_ACT = "player_act"
    PHASE_ENEMY_ACT = "enemy_act"
    PHASE_VICTORY = "victory"
    PHASE_DEFEAT = "defeat"

    # Layout: screen-space feet positions of each combatant
    PLAYER_FEET = (160, 400)
    ENEMY_FEET = (560, 236)

    # Animation timings (ms), per design.md
    LUNGE_MS = 240
    HIT_FLASH_MS = 320
    ENEMY_IDLE_MS = 600
    DEFEAT_FADE_MS = 700

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._player: Player | None = None
        self._enemy: Enemy | None = None
        self._is_tutorial = False
        self._phase = self.PHASE_PLAYER_CHOOSE
        self._selected = 0
        self._defending = False
        self._message = ""
        self._message_timer = 0.0
        self._turn_count = 0
        self._show_tutorial_hint = False
        self._victory_xp = 0
        self._attacker: str | None = None  # "player" / "enemy" during a hit animation
        self._anim_timer = 0.0
        self._idle_timer = 0.0

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        self._player = params["player"]
        self._enemy = params["enemy"]
        self._is_tutorial = params.get("is_tutorial", False)
        self._phase = self.PHASE_PLAYER_CHOOSE
        self._selected = 0
        self._defending = False
        self._message = ""
        self._message_timer = 0.0
        self._turn_count = 0
        self._show_tutorial_hint = self._is_tutorial
        self._victory_xp = 0
        self._attacker = None
        self._anim_timer = 0.0
        self._idle_timer = 0.0

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if self._phase == self.PHASE_PLAYER_CHOOSE:
                if event.key == pygame.K_UP:
                    self._selected = (self._selected - 1) % len(self.ACTIONS)
                elif event.key == pygame.K_DOWN:
                    self._selected = (self._selected + 1) % len(self.ACTIONS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._execute_action()

            elif self._phase in (self.PHASE_VICTORY, self.PHASE_DEFEAT):
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._finish_combat()

    def _execute_action(self) -> None:
        action = self.ACTIONS[self._selected]

        if action == "Attack":
            self._do_player_attack()
        elif action == "Defend":
            self._defending = True
            self._set_message("You brace yourself!")
            self._phase = self.PHASE_PLAYER_ACT
        elif action == "Item":
            consumables = self._player.inventory.get_consumables()
            if not consumables:
                self._set_message("No items to use!")
                return
        elif action == "Flee":
            if self._is_tutorial:
                self._set_message("Your legs won't move!")
                return
            # Non-tutorial flee: 50% chance
            if random.random() < 0.5:
                self._finish_combat()
                return
            self._set_message("Couldn't escape!")
            self._phase = self.PHASE_PLAYER_ACT

        self._show_tutorial_hint = False

    def _do_player_attack(self) -> None:
        weapon = self._player.inventory.get_weapon()
        weapon_bonus = weapon.get("attack_bonus", 0) if weapon else 0
        raw = self._player.attack + weapon_bonus - self._enemy.defense
        damage = max(1, raw + random.randint(-1, 2))
        self._enemy.hp = max(0, self._enemy.hp - damage)

        weapon_name = weapon["name"] if weapon else "bare fists"
        self._set_message(f"You strike with {weapon_name}! {damage} damage!")
        self._phase = self.PHASE_PLAYER_ACT
        self._start_hit_anim("player")

    def _do_enemy_attack(self) -> None:
        raw = self._enemy.attack - self._player.defense
        if self._defending:
            raw = raw // 2
            self._defending = False
        damage = max(1, raw + random.randint(-1, 1))
        self._player.hp = max(0, self._player.hp - damage)

        self._set_message(f"{self._enemy.name} lunges! {damage} damage!")
        self._phase = self.PHASE_ENEMY_ACT
        self._start_hit_anim("enemy")

    def _start_hit_anim(self, attacker: str) -> None:
        self._attacker = attacker
        self._anim_timer = 0.0

    def _set_message(self, msg: str) -> None:
        self._message = msg
        self._message_timer = 1200.0  # ms to show

    def _finish_combat(self) -> None:
        self.game.state_machine.pop()
        current = self.game.state_machine.current
        if self._phase == self.PHASE_VICTORY and hasattr(current, "on_combat_victory"):
            current.on_combat_victory()

    def update(self, dt: float) -> None:
        self._anim_timer += dt
        self._idle_timer += dt
        if self._message_timer > 0:
            self._message_timer -= dt
            # Only action phases auto-advance; victory/defeat wait for Enter
            if self._message_timer <= 0 and self._phase in (self.PHASE_PLAYER_ACT,
                                                            self.PHASE_ENEMY_ACT):
                self._advance_phase()

    def _advance_phase(self) -> None:
        if self._enemy.hp <= 0:
            self._victory_xp = self._enemy.xp_reward
            self._player.xp += self._victory_xp
            self._phase = self.PHASE_VICTORY
            self._attacker = None
            self._anim_timer = 0.0
            self._set_message(
                f"The {self._enemy.name} croaks weakly and hops away! +{self._victory_xp} XP"
            )
            return

        if self._player.hp <= 0:
            self._phase = self.PHASE_DEFEAT
            self._set_message("You collapse... everything goes dark.")
            return

        if self._phase == self.PHASE_PLAYER_ACT:
            # Enemy's turn
            self._do_enemy_attack()
        elif self._phase == self.PHASE_ENEMY_ACT:
            # Back to player
            self._turn_count += 1
            self._phase = self.PHASE_PLAYER_CHOOSE
            self._selected = 0

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(combat_backdrop(self.PLAYER_FEET, self.ENEMY_FEET), (0, 0))
        self._draw_enemy(surface)
        self._draw_player(surface)
        self._draw_hud(surface)
        self._draw_action_menu(surface)
        self._draw_message(surface)
        if self._show_tutorial_hint and self._phase == self.PHASE_PLAYER_CHOOSE:
            hint_surf = font(22).render("Choose ATTACK to strike with your weapon.",
                                        True, s.COLOR_ACCENT_GOLD)
            surface.blit(hint_surf, hint_surf.get_rect(midtop=(s.SCREEN_WIDTH // 2, 30)))

    def _anim_offsets(self, who: str) -> tuple[int, bool]:
        """(x offset, flashing) for a combatant from the current hit animation."""
        if self._attacker is None:
            return 0, False
        t = self._anim_timer
        if self._attacker == who:
            if t < self.LUNGE_MS:
                direction = 1 if who == "player" else -1
                return int(math.sin(math.pi * t / self.LUNGE_MS) * 30) * direction, False
            return 0, False
        # Target: shake and flash once the lunge connects
        hit_t = t - self.LUNGE_MS / 2
        if 0 <= hit_t < self.HIT_FLASH_MS:
            shake = 4 if int(hit_t // 50) % 2 else -4
            return shake, int(hit_t // 80) % 2 == 0
        return 0, False

    def _blit_combatant(self, surface: pygame.Surface, spr: pygame.Surface,
                        feet: tuple[int, int], dx: int, flash: bool,
                        alpha: int = 255) -> pygame.Rect:
        rect = spr.get_rect(midbottom=(feet[0] + dx, feet[1]))
        if flash:
            spr = silhouette(spr, s.COLOR_WHITE)
        elif alpha < 255:
            spr = spr.copy()
            spr.set_alpha(alpha)
        surface.blit(spr, rect)
        return rect

    def _draw_enemy(self, surface: pygame.Surface) -> None:
        frames = ENEMY_IDLE_FRAMES.get(self._enemy.id, 1)
        frame = int(self._idle_timer // self.ENEMY_IDLE_MS) % frames
        spr = enemy(self._enemy.id, frame, s.COMBAT_SCALE)

        alpha = 255
        if self._phase == self.PHASE_VICTORY:
            alpha = max(0, 255 - int(255 * self._anim_timer / self.DEFEAT_FADE_MS))
        dx, flash = self._anim_offsets("enemy")
        rect = self._blit_combatant(surface, spr, self.ENEMY_FEET, dx, flash, alpha)

        # Name + HP bar above the enemy (anchored to its feet so the shake doesn't move it)
        top_left = (self.ENEMY_FEET[0] - rect.w // 2, rect.y)
        name_surf = font(28).render(self._enemy.name, True, s.COLOR_WHITE)
        surface.blit(name_surf, (top_left[0], top_left[1] - 48))
        bar = pygame.Rect(top_left[0], top_left[1] - 24, 100, 8)
        draw_bar(surface, bar, self._enemy.hp / self._enemy.max_hp, s.COLOR_HP_RED)
        hp_text = font(22).render(f"{self._enemy.hp}/{self._enemy.max_hp}",
                                  True, s.COLOR_TEXT_LIGHT)
        surface.blit(hp_text, (bar.right + 8, bar.y - 4))

    def _draw_player(self, surface: pygame.Surface) -> None:
        spr = character(PLAYER_LOOK, "right", 0, s.COMBAT_SCALE)
        dx, flash = self._anim_offsets("player")
        rect = self._blit_combatant(surface, spr, self.PLAYER_FEET, dx, flash)

        weapon = self._player.inventory.get_weapon()
        weapon_spr = item(weapon["id"], s.COMBAT_SCALE) if weapon else None
        if weapon_spr and not flash:
            # Weapon grip (bottom-left of its sprite) sits in the hand
            hand_x = rect.x + 8 * s.COMBAT_SCALE
            hand_y = rect.y + 16 * s.COMBAT_SCALE
            surface.blit(weapon_spr, (hand_x - 1 * s.COMBAT_SCALE,
                                      hand_y - 13 * s.COMBAT_SCALE))

    def _draw_hud(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(20, s.SCREEN_HEIGHT - 90, 290, 70)
        draw_panel(surface, panel, fill=(22, 33, 62, 220))
        name_surf = font(28).render(self._player.name, True, s.COLOR_WHITE)
        surface.blit(name_surf, (panel.x + 12, panel.y + 10))

        bar = pygame.Rect(panel.x + 12, panel.y + 40, 160, 12)
        draw_bar(surface, bar, self._player.hp / self._player.max_hp, s.COLOR_HP_RED)
        hp_text = font(22).render(f"HP {self._player.hp}/{self._player.max_hp}",
                                  True, s.COLOR_TEXT_LIGHT)
        surface.blit(hp_text, (bar.right + 8, bar.y - 2))

    def _draw_action_menu(self, surface: pygame.Surface) -> None:
        if self._phase != self.PHASE_PLAYER_CHOOSE:
            return

        panel = pygame.Rect(s.SCREEN_WIDTH - 250, s.SCREEN_HEIGHT - 180, 220, 160)
        draw_panel(surface, panel, fill=(22, 33, 62, 230))

        for i, action in enumerate(self.ACTIONS):
            selected = i == self._selected
            color = s.COLOR_ACCENT_GOLD if selected else s.COLOR_WHITE
            prefix = "> " if selected else "  "
            text_surf = font(28).render(prefix + action, True, color)
            surface.blit(text_surf, (panel.x + 15, panel.y + 15 + i * 34))

    def _draw_message(self, surface: pygame.Surface) -> None:
        # Victory/defeat messages stay up until the player presses Enter
        persistent = self._phase in (self.PHASE_VICTORY, self.PHASE_DEFEAT)
        if not self._message or (self._message_timer <= 0 and not persistent):
            return
        draw_text_box(surface, self._message, font(28),
                      center=(s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT - 135),
                      padding=(20, 12))
        if persistent:
            hint = font(20).render("[Enter] Continue", True, s.COLOR_TEXT_DIM)
            surface.blit(hint, hint.get_rect(center=(s.SCREEN_WIDTH // 2,
                                                     s.SCREEN_HEIGHT - 105)))
