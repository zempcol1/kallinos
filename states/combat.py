"""Turn-based combat state — Harry Potter GBC/GBA style."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

import settings as s
from entities.enemy import Enemy
from game.state_machine import State
from systems.sprite_factory import sprite_enemy_vatrachos, sprite_player

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

        # Fonts
        self._font: pygame.font.Font | None = None
        self._big_font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._dmg_font: pygame.font.Font | None = None

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

        self._font = pygame.font.Font(None, 28)
        self._big_font = pygame.font.Font(None, 40)
        self._small_font = pygame.font.Font(None, 22)
        self._dmg_font = pygame.font.Font(None, 36)

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

    def _do_enemy_attack(self) -> None:
        raw = self._enemy.attack - self._player.defense
        if self._defending:
            raw = raw // 2
            self._defending = False
        damage = max(1, raw + random.randint(-1, 1))
        self._player.hp = max(0, self._player.hp - damage)

        self._set_message(f"{self._enemy.name} lunges! {damage} damage!")
        self._phase = self.PHASE_ENEMY_ACT

    def _set_message(self, msg: str) -> None:
        self._message = msg
        self._message_timer = 1200.0  # ms to show

    def _finish_combat(self) -> None:
        self.game.state_machine.pop()
        current = self.game.state_machine.current
        if self._phase == self.PHASE_VICTORY and hasattr(current, "on_combat_victory"):
            current.on_combat_victory()

    def update(self, dt: float) -> None:
        if self._message_timer > 0:
            self._message_timer -= dt
            if self._message_timer <= 0:
                self._advance_phase()

    def _advance_phase(self) -> None:
        if self._enemy.hp <= 0:
            self._victory_xp = self._enemy.xp_reward
            self._player.xp += self._victory_xp
            self._phase = self.PHASE_VICTORY
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
        surface.fill(s.COLOR_COMBAT_BG)
        self._draw_enemy(surface)
        self._draw_player_sprite(surface)
        self._draw_hud(surface)
        self._draw_action_menu(surface)
        self._draw_message(surface)
        if self._show_tutorial_hint and self._phase == self.PHASE_PLAYER_CHOOSE:
            self._draw_tutorial_hint(surface)

    def _draw_enemy(self, surface: pygame.Surface) -> None:
        # Enemy sprite area (right side)
        ex, ey = 520, 120

        # Use generated sprite
        spr = sprite_enemy_vatrachos()
        # Scale up 2× more for combat view
        big = pygame.transform.scale(spr, (spr.get_width() * 2, spr.get_height() * 2))
        surface.blit(big, (ex - big.get_width() // 2 + 40, ey))

        ew = big.get_width()
        eh = big.get_height()

        # Name
        name_surf = self._font.render(self._enemy.name, True, s.COLOR_WHITE)
        surface.blit(name_surf, (ex, ey - 28))

        # HP bar
        bar_w = 80
        bar_h = 8
        bar_x, bar_y = ex, ey + eh + 8
        ratio = self._enemy.hp / self._enemy.max_hp
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, s.COLOR_HP_RED, (bar_x, bar_y, int(bar_w * ratio), bar_h))

        hp_text = self._small_font.render(
            f"{self._enemy.hp}/{self._enemy.max_hp}", True, s.COLOR_TEXT_LIGHT
        )
        surface.blit(hp_text, (bar_x, bar_y + 10))

    def _draw_player_sprite(self, surface: pygame.Surface) -> None:
        px, py = 140, 260

        # Use generated sprite, scaled up for combat view
        spr = sprite_player()
        big = pygame.transform.scale(spr, (spr.get_width() * 2, spr.get_height() * 2))
        surface.blit(big, (px - big.get_width() // 2, py))

        # Weapon indicator
        weapon = self._player.inventory.get_weapon()
        if weapon:
            # Brown line for the stick, next to the player
            wx = px + big.get_width() // 2 + 4
            wy = py + 20
            pygame.draw.line(surface, (140, 110, 60),
                             (wx, wy), (wx + 24, wy - 30), 4)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        # Player stats at bottom-left
        y = s.SCREEN_HEIGHT - 80
        name_surf = self._font.render(self._player.name, True, s.COLOR_WHITE)
        surface.blit(name_surf, (30, y))

        # HP bar
        bar_w, bar_h = 160, 12
        bar_x = 30
        hp_ratio = self._player.hp / self._player.max_hp
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, y + 28, bar_w, bar_h))
        pygame.draw.rect(surface, s.COLOR_HP_RED,
                         (bar_x, y + 28, int(bar_w * hp_ratio), bar_h))

        hp_text = self._small_font.render(
            f"HP {self._player.hp}/{self._player.max_hp}", True, s.COLOR_TEXT_LIGHT
        )
        surface.blit(hp_text, (bar_x + bar_w + 8, y + 26))

    def _draw_action_menu(self, surface: pygame.Surface) -> None:
        if self._phase != self.PHASE_PLAYER_CHOOSE:
            return

        menu_x = s.SCREEN_WIDTH - 250
        menu_y = s.SCREEN_HEIGHT - 180
        panel = pygame.Rect(menu_x, menu_y, 220, 160)

        # Panel bg
        panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        panel_surf.fill((22, 33, 62, 230))
        surface.blit(panel_surf, panel)
        pygame.draw.rect(surface, s.COLOR_ACCENT_GOLD, panel, 2)

        for i, action in enumerate(self.ACTIONS):
            if i == self._selected:
                color = s.COLOR_ACCENT_GOLD
                prefix = "> "
            else:
                color = s.COLOR_WHITE
                prefix = "  "
            text_surf = self._font.render(prefix + action, True, color)
            surface.blit(text_surf, (menu_x + 15, menu_y + 15 + i * 34))

    def _draw_message(self, surface: pygame.Surface) -> None:
        if not self._message or self._message_timer <= 0:
            return

        msg_surf = self._font.render(self._message, True, s.COLOR_WHITE)
        msg_rect = msg_surf.get_rect(center=(s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT // 2 + 40))

        # Background
        bg = msg_rect.inflate(20, 12)
        bg_surf = pygame.Surface((bg.width, bg.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        surface.blit(bg_surf, bg)
        surface.blit(msg_surf, msg_rect)

    def _draw_tutorial_hint(self, surface: pygame.Surface) -> None:
        hint = "Choose ATTACK to strike with your weapon."
        hint_surf = self._small_font.render(hint, True, s.COLOR_ACCENT_GOLD)
        surface.blit(hint_surf, (s.SCREEN_WIDTH // 2 - hint_surf.get_width() // 2, 30))
