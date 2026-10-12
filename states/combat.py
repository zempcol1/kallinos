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
    ENEMY_IDLE_FRAMES, POSE_HANDS, battle_pose, combat_backdrop, enemy, item, laurel,
    portrait, silhouette,
)
from ui.widgets import draw_panel, draw_shadowed_text, font

if TYPE_CHECKING:
    from game.game import Game
    from entities.player import Player


def _ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class Combat(State):
    """Turn-based combat.

    Push with params:
        {
            "enemy": Enemy instance,
            "player": Player reference,
            "can_flee": bool (default True),
            "hint": str | None — shown until the first action,
        }

    Victory pops back and calls ``on_combat_victory()`` on the state below;
    defeat goes to the Game Over screen.
    """

    ACTIONS = ["Attack", "Defend", "Item", "Flee"]

    # Phases
    PHASE_INTRO = "intro"
    PHASE_PLAYER_CHOOSE = "player_choose"
    PHASE_ITEM_SELECT = "item_select"
    PHASE_PLAYER_ACT = "player_act"
    PHASE_ENEMY_ACT = "enemy_act"
    PHASE_VICTORY = "victory"
    PHASE_DEFEAT = "defeat"

    # Layout: screen-space feet positions of each combatant
    PLAYER_FEET = (190, 410)
    ENEMY_FEET = (566, 252)
    ENEMY_PANEL = pygame.Rect(36, 40, 280, 74)
    PLAYER_PANEL = pygame.Rect(20, s.SCREEN_HEIGHT - 112, 340, 92)
    MENU_PANEL = pygame.Rect(s.SCREEN_WIDTH - 250, s.SCREEN_HEIGHT - 196, 230, 176)
    MENU_ROWS = 4

    # Animation timings (ms), per design.md
    INTRO_MS = 700
    FLASH_MS = 220
    SLIDE_PX = 360
    LUNGE_MS = 240
    HIT_FLASH_MS = 320
    ENEMY_IDLE_MS = 600
    DEFEAT_FADE_MS = 700
    MESSAGE_MS = 1200
    POPUP_MS = 900
    SPARK_MS = 260
    HP_DRAIN_PER_MS = 0.02          # displayed HP catches up at this rate
    HP_LAG_DELAY_MS = 300           # the pale "damage" trail waits before shrinking

    HP_HIGH = (96, 172, 84)
    HP_MID = (222, 172, 62)
    HP_LOW = s.COLOR_HP_RED
    HP_TRAIL = (242, 224, 204)
    HEAL_COLOR = (130, 220, 120)

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._player: Player | None = None
        self._enemy: Enemy | None = None
        self._can_flee = True
        self._hint: str | None = None
        self._phase = self.PHASE_INTRO
        self._selected = 0
        self._item_options: list[tuple[dict, int]] = []  # (item, count)
        self._item_selected = 0
        self._defending = False
        self._message = ""
        self._message_timer = 0.0
        self._turn_count = 0
        self._victory_xp = 0
        self._attacker: str | None = None  # "player" / "enemy" during a hit animation
        self._anim_timer = 0.0
        self._idle_timer = 0.0
        self._time = 0.0
        self._shown_hp: dict[str, float] = {}
        self._trail_hp: dict[str, float] = {}
        self._hit_at: dict[str, float] = {}
        self._popups: list[list] = []   # [text, color, (x, y), born]
        self._sparks: list[list] = []   # [(x, y), born]

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        self._player = params["player"]
        self._enemy = params["enemy"]
        self._can_flee = params.get("can_flee", True)
        self._hint = params.get("hint")
        self._phase = self.PHASE_INTRO
        self._selected = 0
        self._item_options = []
        self._item_selected = 0
        self._defending = False
        self._message = ""
        self._message_timer = 0.0
        self._turn_count = 0
        self._victory_xp = 0
        self._attacker = None
        self._anim_timer = 0.0
        self._idle_timer = 0.0
        self._time = 0.0
        hp = {"player": self._player.hp, "enemy": self._enemy.hp}
        self._shown_hp = dict(hp)
        self._trail_hp = dict(hp)
        self._hit_at = {"player": -1e9, "enemy": -1e9}
        self._popups = []
        self._sparks = []

    # ── Input & actions ──────────────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if self._phase == self.PHASE_PLAYER_CHOOSE:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._selected = (self._selected - 1) % len(self.ACTIONS)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected = (self._selected + 1) % len(self.ACTIONS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                    self._execute_action()

            elif self._phase == self.PHASE_ITEM_SELECT:
                n_options = len(self._item_options) + 1  # + "Back"
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._item_selected = (self._item_selected - 1) % n_options
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._item_selected = (self._item_selected + 1) % n_options
                elif event.key == pygame.K_ESCAPE:
                    self._phase = self.PHASE_PLAYER_CHOOSE
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                    if self._item_selected == len(self._item_options):
                        self._phase = self.PHASE_PLAYER_CHOOSE
                    else:
                        self._use_item(self._item_options[self._item_selected][0])

            elif self._phase in (self.PHASE_VICTORY, self.PHASE_DEFEAT):
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
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
            self._item_options = self._player.inventory.consumable_stacks()
            if not self._item_options:
                self._set_message("No items to use!")
                return
            self._item_selected = 0
            self._phase = self.PHASE_ITEM_SELECT
            return
        elif action == "Flee":
            if not self._can_flee:
                self._set_message("Your legs won't move!")
                return
            # Non-tutorial flee: 50% chance
            if random.random() < 0.5:
                self._finish_combat()
                return
            self._set_message("Couldn't escape!")
            self._phase = self.PHASE_PLAYER_ACT

        self._hint = None

    def _use_item(self, used: dict) -> None:
        """Consume an item; using it takes the player's turn."""
        self._player.inventory.remove_item(used["id"])
        heal = min(used.get("heal", 0), self._player.max_hp - self._player.hp)
        self._player.hp += heal
        self._set_message(f"You use the {used['name']}. +{heal} HP")
        self._popup(f"+{heal}", self.HEAL_COLOR, "player")
        self._phase = self.PHASE_PLAYER_ACT
        self._hint = None

    def _do_player_attack(self) -> None:
        weapon = self._player.inventory.get_weapon()
        weapon_bonus = weapon.get("attack_bonus", 0) if weapon else 0
        raw = self._player.attack + weapon_bonus - self._enemy.defense
        damage = max(1, raw + random.randint(-1, 2))
        self._enemy.hp = max(0, self._enemy.hp - damage)

        weapon_name = weapon["name"] if weapon else "bare fists"
        self._set_message(f"You strike with {weapon_name}! {damage} damage!")
        self._phase = self.PHASE_PLAYER_ACT
        self._start_hit_anim("player", "enemy", damage)

    def _do_enemy_attack(self) -> None:
        raw = self._enemy.attack - self._player.defense
        if self._defending:
            raw = raw // 2
            self._defending = False
        damage = max(1, raw + random.randint(-1, 1))
        self._player.hp = max(0, self._player.hp - damage)

        self._set_message(f"{self._enemy.name} lunges! {damage} damage!")
        self._phase = self.PHASE_ENEMY_ACT
        self._start_hit_anim("enemy", "player", damage)

    def _start_hit_anim(self, attacker: str, target: str, damage: int) -> None:
        self._attacker = attacker
        self._anim_timer = 0.0
        # The number and spark appear when the lunge connects
        born = self._time + self.LUNGE_MS / 2
        self._hit_at[target] = born
        self._popup(f"-{damage}", s.COLOR_WHITE, target, born)
        self._sparks.append([self._body_center(target), born])

    def _popup(self, text: str, color: tuple, who: str, born: float | None = None) -> None:
        x, y = self._body_center(who)
        self._popups.append([text, color, (x, y - 30), self._time if born is None else born])

    def _body_center(self, who: str) -> tuple[int, int]:
        fx, fy = self.PLAYER_FEET if who == "player" else self.ENEMY_FEET
        return fx + (12 if who == "player" else 0), fy - (70 if who == "player" else 50)

    def _set_message(self, msg: str) -> None:
        self._message = msg
        self._message_timer = self.MESSAGE_MS

    def _finish_combat(self) -> None:
        machine = self.game.state_machine
        machine.pop()
        if self._phase == self.PHASE_DEFEAT:
            machine.change("game_over")
            return
        current = machine.current
        if self._phase == self.PHASE_VICTORY and hasattr(current, "on_combat_victory"):
            current.on_combat_victory()

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._time += dt
        self._anim_timer += dt
        self._idle_timer += dt
        if self._phase == self.PHASE_INTRO and self._time >= self.INTRO_MS:
            self._phase = self.PHASE_PLAYER_CHOOSE
        self._update_hp_bars(dt)
        self._popups = [p for p in self._popups if self._time - p[3] < self.POPUP_MS]
        self._sparks = [sp for sp in self._sparks if self._time - sp[1] < self.SPARK_MS]
        if self._message_timer > 0:
            self._message_timer -= dt
            # Only action phases auto-advance; victory/defeat wait for Enter
            if self._message_timer <= 0 and self._phase in (self.PHASE_PLAYER_ACT,
                                                            self.PHASE_ENEMY_ACT):
                self._advance_phase()

    def _update_hp_bars(self, dt: float) -> None:
        """Displayed HP drains toward the real value; a pale trail follows later."""
        for who, actual in (("player", self._player.hp), ("enemy", self._enemy.hp)):
            if self._time < self._hit_at[who]:
                continue
            step = self.HP_DRAIN_PER_MS * dt * max(1.0, abs(self._shown_hp[who] - actual))
            shown = self._shown_hp[who]
            self._shown_hp[who] = max(actual, shown - step) if shown > actual else \
                min(actual, shown + step)
            if self._time - self._hit_at[who] > self.HP_LAG_DELAY_MS:
                trail = self._trail_hp[who]
                self._trail_hp[who] = max(self._shown_hp[who], trail - step)
            if self._trail_hp[who] < self._shown_hp[who]:
                self._trail_hp[who] = self._shown_hp[who]

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
        slide = 1 - _ease_out(self._time / self.INTRO_MS)
        self._draw_enemy(surface, round(slide * self.SLIDE_PX))
        self._draw_player(surface, -round(slide * self.SLIDE_PX))
        self._draw_effects(surface)
        if self._phase != self.PHASE_INTRO:
            self._draw_panels(surface)
            self._draw_action_menu(surface)
            self._draw_message(surface)
            if self._hint and self._phase == self.PHASE_PLAYER_CHOOSE:
                hint = font(26)
                text_rect = hint.render(self._hint, True, s.COLOR_ACCENT_GOLD).get_rect(
                    midtop=(s.SCREEN_WIDTH // 2, 14))
                draw_shadowed_text(surface, self._hint, hint, text_rect.topleft,
                                   s.COLOR_TITLE_GOLD)
        if self._time < self.FLASH_MS:
            flash = pygame.Surface(surface.get_size())
            flash.fill(s.COLOR_WHITE)
            flash.set_alpha(int(255 * (1 - self._time / self.FLASH_MS)))
            surface.blit(flash, (0, 0))

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

    def _draw_enemy(self, surface: pygame.Surface, slide: int) -> None:
        frames = ENEMY_IDLE_FRAMES.get(self._enemy.id, 1)
        frame = int(self._idle_timer // self.ENEMY_IDLE_MS) % frames
        spr = enemy(self._enemy.id, frame, s.COMBAT_SCALE)
        dx, flash = self._anim_offsets("enemy")
        x, y = self.ENEMY_FEET[0] + dx + slide, self.ENEMY_FEET[1]

        if self._phase == self.PHASE_VICTORY:
            # Hops away to the right, fading
            t = min(1.0, self._anim_timer / self.DEFEAT_FADE_MS)
            x += round(t * 160)
            y -= round(abs(math.sin(t * math.pi * 2)) * 50)
            spr = spr.copy()
            spr.set_alpha(int(255 * (1 - t)))
        elif flash:
            spr = silhouette(spr, s.COLOR_WHITE)
        surface.blit(spr, spr.get_rect(midbottom=(x, y)))

    def _draw_player(self, surface: pygame.Surface, slide: int) -> None:
        dx, flash = self._anim_offsets("player")
        striking = self._attacker == "player" and self.LUNGE_MS / 2 <= self._anim_timer < \
            self.LUNGE_MS * 2
        pose = "strike" if striking else "ready"
        body = battle_pose(self._player.look, pose)
        rect = body.get_rect(midbottom=(self.PLAYER_FEET[0] + dx + slide, self.PLAYER_FEET[1]))
        if flash:
            surface.blit(silhouette(body, s.COLOR_WHITE), rect)
            return
        surface.blit(body, rect)

        weapon = self._player.inventory.get_weapon()
        weapon_spr = item(weapon["id"], s.COMBAT_SCALE) if weapon else None
        if weapon_spr:
            # The weapon's grip sits in the hand; striking swings it down 90°
            grip = (3, 14)
            if pose == "strike":
                weapon_spr = pygame.transform.rotate(weapon_spr, -90)
                grip = (s.TILE_SIZE - 1 - grip[1], grip[0])
            hand = POSE_HANDS[pose]
            surface.blit(weapon_spr, (rect.x + (hand[0] - grip[0]) * s.COMBAT_SCALE,
                                      rect.y + (hand[1] - grip[1]) * s.COMBAT_SCALE))

    def _draw_effects(self, surface: pygame.Surface) -> None:
        """Hit sparks and floating numbers."""
        for (x, y), born in self._sparks:
            t = (self._time - born) / self.SPARK_MS
            if t < 0:
                continue
            reach = 10 + round(t * 26)
            color = s.COLOR_WHITE if t < 0.5 else s.COLOR_TITLE_GOLD
            for i in range(8):
                a = i * math.tau / 8 + 0.3
                inner = (x + math.cos(a) * reach * 0.4, y + math.sin(a) * reach * 0.4)
                outer = (x + math.cos(a) * reach, y + math.sin(a) * reach)
                pygame.draw.line(surface, color, inner, outer, 4 if i % 2 else 2)
        number_font = font(40)
        for text, color, (x, y), born in self._popups:
            t = (self._time - born) / self.POPUP_MS
            if t < 0:
                continue
            rise = round(_ease_out(t * 2) * 34)
            alpha = int(255 * min(1.0, (1 - t) * 3))
            label = number_font.render(text, True, color)
            rect = label.get_rect(center=(x, y - rise))
            shadow = number_font.render(text, True, (40, 20, 24))
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
                shadow.set_alpha(alpha)
                surface.blit(shadow, rect.move(ox, oy))
            label.set_alpha(alpha)
            surface.blit(label, rect)

    def _hp_bar(self, surface: pygame.Surface, rect: pygame.Rect, who: str,
                max_hp: int) -> None:
        shown = self._shown_hp[who] / max_hp
        trail = self._trail_hp[who] / max_hp
        color = self.HP_HIGH if shown > 0.5 else self.HP_MID if shown > 0.25 else self.HP_LOW
        pygame.draw.rect(surface, (30, 24, 36), rect.inflate(4, 4))
        pygame.draw.rect(surface, (64, 58, 70), rect)
        pygame.draw.rect(surface, self.HP_TRAIL, (rect.x, rect.y, round(rect.w * trail), rect.h))
        fill = pygame.Rect(rect.x, rect.y, round(rect.w * shown), rect.h)
        pygame.draw.rect(surface, color, fill)
        pygame.draw.line(surface, tuple(min(255, c + 50) for c in color), fill.topleft,
                         (fill.right - 1, fill.top))

    def _draw_panels(self, surface: pygame.Surface) -> None:
        # Enemy: name plate with HP
        panel = self.ENEMY_PANEL
        draw_panel(surface, panel, fill=(22, 26, 48, 225), ornate=True)
        draw_shadowed_text(surface, self._enemy.name, font(30), (panel.x + 18, panel.y + 12),
                           s.COLOR_TITLE_GOLD)
        bar = pygame.Rect(panel.x + 56, panel.y + 46, panel.w - 80, 10)
        draw_shadowed_text(surface, "HP", font(22), (panel.x + 20, panel.y + 42), s.COLOR_SAND)
        self._hp_bar(surface, bar, "enemy", self._enemy.max_hp)

        # Player: portrait, name, HP with numbers
        panel = self.PLAYER_PANEL
        draw_panel(surface, panel, fill=(22, 26, 48, 225), ornate=True)
        face = portrait(self._player.look, factor=1)
        frame = face.get_rect(midleft=(panel.x + 16, panel.centery))
        pygame.draw.rect(surface, (44, 36, 54), frame)
        surface.blit(face, frame)
        pygame.draw.rect(surface, s.COLOR_ACCENT_GOLD, frame.inflate(4, 4), 2)
        text_x = frame.right + 18
        draw_shadowed_text(surface, self._player.name, font(30), (text_x, panel.y + 14),
                           s.COLOR_TITLE_GOLD)
        bar = pygame.Rect(text_x + 34, panel.y + 52, 150, 10)
        draw_shadowed_text(surface, "HP", font(22), (text_x, panel.y + 48), s.COLOR_SAND)
        self._hp_bar(surface, bar, "player", self._player.max_hp)
        draw_shadowed_text(surface, f"{round(self._shown_hp['player'])}/{self._player.max_hp}",
                           font(22), (bar.right + 10, panel.y + 48), s.COLOR_TEXT_LIGHT)

    def _draw_action_menu(self, surface: pygame.Surface) -> None:
        if self._phase == self.PHASE_PLAYER_CHOOSE:
            options, selected_i = self.ACTIONS, self._selected
        elif self._phase == self.PHASE_ITEM_SELECT:
            options = [f"{it['name']} x{count}" for it, count in self._item_options] + ["Back"]
            selected_i = self._item_selected
        else:
            return

        panel = self.MENU_PANEL
        draw_panel(surface, panel, fill=(22, 26, 48, 230), ornate=True)
        # Scroll so the selection is always one of the visible rows
        first = max(0, selected_i - self.MENU_ROWS + 1)
        cursor = laurel(flip=True)
        for row, action in enumerate(options[first:first + self.MENU_ROWS]):
            selected = first + row == selected_i
            y = panel.y + 22 + row * 36
            color = s.COLOR_TITLE_GOLD if selected else s.COLOR_SAND
            disabled = action == "Flee" and not self._can_flee
            if disabled:
                color = (128, 124, 140)
            draw_shadowed_text(surface, action, font(30), (panel.x + 64, y), color)
            if selected:
                sway = round(math.sin(self._time / 300) * 2)
                surface.blit(cursor, cursor.get_rect(midright=(panel.x + 56 + sway, y + 10)))

    def _draw_message(self, surface: pygame.Surface) -> None:
        # Victory/defeat messages stay up until the player presses Enter
        persistent = self._phase in (self.PHASE_VICTORY, self.PHASE_DEFEAT)
        if not self._message or (self._message_timer <= 0 and not persistent):
            return
        text_font = font(28)
        text = text_font.render(self._message, True, s.COLOR_WHITE)
        box = text.get_rect(center=(s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT - 150)).inflate(40, 24)
        box.right = min(box.right, self.MENU_PANEL.left - 10) if self._phase in (
            self.PHASE_PLAYER_CHOOSE, self.PHASE_ITEM_SELECT) else box.right
        draw_panel(surface, box, fill=(22, 26, 48, 230), ornate=True)
        draw_shadowed_text(surface, self._message, text_font, (box.x + 20, box.y + 12))
        if persistent:
            hint = font(20).render("[Enter] Continue", True, s.COLOR_TEXT_DIM)
            surface.blit(hint, hint.get_rect(midtop=(box.centerx, box.bottom + 6)))
