"""Turn-based combat screen — Harry Potter GBC/GBA style.

This state is the presentation: menus, messages, animation. The rules
(damage, fleeing, items, who has won) live in ``systems/battle.py``.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from systems import controls
from systems.battle import Battle
from systems.sprites import (
    ENEMY_IDLE_FRAMES, POSE_HANDS, battle_pose, combat_backdrop, enemy, item, laurel,
    portrait, silhouette,
)
from ui.effects import draw_veil, ease_out
from ui.menu import Menu
from ui.widgets import draw_bar, draw_panel, draw_shadowed_text, font

if TYPE_CHECKING:
    from entities.enemy import Enemy
    from entities.player import Player
    from game.game import Game

PLAYER = "player"
ENEMY = "enemy"


@dataclass
class _Side:
    """One combatant on screen: where it stands and its animated HP bar."""

    fighter: Player | Enemy
    feet: tuple[int, int]            # screen position of the feet
    body: tuple[int, int]            # offset from the feet to the body center
    shown_hp: float = 0.0            # HP the bar shows; drains toward the real value
    trail_hp: float = 0.0            # the pale "damage" trail, which follows later
    hit_at: float = -math.inf        # combat time of the last hit taken

    def __post_init__(self) -> None:
        self.shown_hp = self.trail_hp = float(self.fighter.hp)

    @property
    def body_center(self) -> tuple[int, int]:
        return self.feet[0] + self.body[0], self.feet[1] + self.body[1]


@dataclass
class _Popup:
    """A floating number ("-4", "+10") that rises and fades."""

    text: str
    color: tuple
    pos: tuple[int, int]
    born: float


@dataclass
class _Spark:
    """A burst of lines where a hit lands."""

    pos: tuple[int, int]
    born: float


class Combat(State):
    """Turn-based combat.

    Push with params:
        {
            "enemy": Enemy instance,
            "player": Player reference,
            "can_flee": bool (default True),
            "hint": str | None — shown until the first action,
            "on_victory": callable | None — called after a win, once this
                          state has popped,
        }

    Defeat goes to the Game Over screen; fleeing just pops.
    """

    ATTACK, DEFEND, ITEM, FLEE = "Attack", "Defend", "Item", "Flee"
    ACTIONS = (ATTACK, DEFEND, ITEM, FLEE)
    BACK = "Back"

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
    PLAYER_BODY = (12, -70)
    ENEMY_BODY = (0, -50)
    ENEMY_PANEL = pygame.Rect(36, 40, 280, 74)
    PLAYER_PANEL = pygame.Rect(20, s.SCREEN_HEIGHT - 112, 340, 92)
    MENU_PANEL = pygame.Rect(s.SCREEN_WIDTH - 250, s.SCREEN_HEIGHT - 196, 230, 176)
    MENU_ROWS = 4
    MENU_ROW_HEIGHT = 36
    MESSAGE_Y = s.SCREEN_HEIGHT - 150
    HINT_Y = 14
    BAR_HEIGHT = 10
    PLAYER_BAR_WIDTH = 150
    WEAPON_GRIP = (3, 14)           # where the hand holds a weapon sprite, logical px

    # Animation (ms and screen pixels), per design.md
    INTRO_MS = 700
    FLASH_MS = 220
    SLIDE_PX = 360
    LUNGE_MS = 240
    LUNGE_PX = 30
    HIT_FLASH_MS = 320
    SHAKE_PX = 4
    SHAKE_STEP_MS = 50
    BLINK_STEP_MS = 80
    ENEMY_IDLE_MS = 600
    DEFEAT_FADE_MS = 700
    DEFEAT_HOP = (160, 50)          # the beaten enemy hops this far right / this high
    MESSAGE_MS = 1200
    POPUP_MS = 900
    POPUP_LIFT = 30                 # numbers start this far above the body center
    POPUP_RISE = 34
    SPARK_MS = 260
    SPARK_RAYS = 8
    MUSIC_STOP_MS = 300
    CURSOR_SWAY_MS = 300
    HP_DRAIN_PER_MS = 0.02          # displayed HP catches up at this rate
    HP_LAG_DELAY_MS = 300           # the pale "damage" trail waits before shrinking

    HP_HIGH = (96, 172, 84)
    HP_MID = (222, 172, 62)
    HP_LOW = s.COLOR_HP_RED
    HEAL_COLOR = (130, 220, 120)
    POPUP_SHADOW = (40, 20, 24)
    PANEL_FILL = (22, 26, 48, 230)

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._battle: Battle | None = None
        self._sides: dict[str, _Side] = {}
        self._actions = Menu(game.audio, self.ACTIONS)
        self._items = Menu(game.audio)
        self._item_stacks: list[tuple[dict, int]] = []
        self._on_victory: Callable[[], None] | None = None
        self._hint: str | None = None
        self._phase = self.PHASE_INTRO
        self._message = ""
        self._message_timer = 0.0
        self._attacker: str | None = None   # PLAYER / ENEMY during a hit animation
        self._anim_timer = 0.0
        self._time = 0.0
        self._popups: list[_Popup] = []
        self._sparks: list[_Spark] = []
        self._sounds: list[tuple[float, str]] = []   # (when, name) to play later

    def enter(self, params: dict | None = None) -> None:
        params = params or {}
        self._battle = Battle(params["player"], params["enemy"], params.get("can_flee", True))
        self._sides = {
            PLAYER: _Side(self._battle.player, self.PLAYER_FEET, self.PLAYER_BODY),
            ENEMY: _Side(self._battle.enemy, self.ENEMY_FEET, self.ENEMY_BODY),
        }
        self._actions.reset()
        self._items.reset([])
        self._item_stacks = []
        self._on_victory = params.get("on_victory")
        self._hint = params.get("hint")
        self._phase = self.PHASE_INTRO
        self._message = ""
        self._message_timer = 0.0
        self._attacker = None
        self._anim_timer = 0.0
        self._time = 0.0
        self._popups = []
        self._sparks = []
        self._sounds = []
        self.game.audio.play_music("battle")
        self.game.audio.play("swoosh")

    @property
    def _player(self) -> Player:
        return self._battle.player

    @property
    def _enemy(self) -> Enemy:
        return self._battle.enemy

    # ── Input & actions ──────────────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for key in controls.pressed_keys(events):
            if self._phase == self.PHASE_PLAYER_CHOOSE:
                if self._actions.handle_key(key):
                    self._choose_action(self._actions.choice)
            elif self._phase == self.PHASE_ITEM_SELECT:
                if key in controls.CANCEL:
                    self._phase = self.PHASE_PLAYER_CHOOSE
                elif self._items.handle_key(key):
                    self._choose_item()
            elif self._phase in (self.PHASE_VICTORY, self.PHASE_DEFEAT):
                if key in controls.CONFIRM:
                    self._finish()

    def _choose_action(self, action: str) -> None:
        if action == self.ATTACK:
            self._player_attack()
        elif action == self.DEFEND:
            self._battle.defend()
            self._set_message("You brace yourself!")
            self._end_player_turn()
        elif action == self.ITEM:
            self._open_items()
        elif action == self.FLEE:
            self._flee()

    def _end_player_turn(self) -> None:
        """The player has acted: the enemy answers once the message has been read."""
        self._phase = self.PHASE_PLAYER_ACT
        self._hint = None

    def _player_attack(self) -> None:
        weapon = self._player.inventory.weapon
        damage = self._battle.player_attack()
        weapon_name = weapon["name"] if weapon else "bare fists"
        self._set_message(f"You strike with {weapon_name}! {damage} damage!")
        self._end_player_turn()
        self._start_hit_anim(PLAYER, ENEMY, damage)

    def _open_items(self) -> None:
        self._item_stacks = self._player.inventory.stacks("consumable")
        if not self._item_stacks:
            self._set_message("No items to use!")
            return
        labels = [f"{stack['name']} x{count}" for stack, count in self._item_stacks]
        self._items.reset([*labels, self.BACK])
        self._phase = self.PHASE_ITEM_SELECT

    def _choose_item(self) -> None:
        if self._items.choice == self.BACK:
            self._phase = self.PHASE_PLAYER_CHOOSE
            return
        used, _ = self._item_stacks[self._items.selected]
        healed = self._battle.use_item(used)
        self._set_message(f"You use the {used['name']}. +{healed} HP")
        self._popup(f"+{healed}", self.HEAL_COLOR, PLAYER)
        self.game.audio.play("heal")
        self._end_player_turn()

    def _flee(self) -> None:
        if not self._battle.can_flee:
            self._set_message("Your legs won't move!")
            self.game.audio.play("deny")
        elif self._battle.try_flee():
            self._finish()
        else:
            self._set_message("Couldn't escape!")
            self._end_player_turn()

    def _enemy_attack(self) -> None:
        damage = self._battle.enemy_attack()
        self._set_message(f"{self._enemy.attack_text} {damage} damage!")
        self._phase = self.PHASE_ENEMY_ACT
        if self._enemy.attack_sound:
            self.game.audio.play(self._enemy.attack_sound)
        self._start_hit_anim(ENEMY, PLAYER, damage)

    def _start_hit_anim(self, attacker: str, target: str, damage: int) -> None:
        self._attacker = attacker
        self._anim_timer = 0.0
        # The number and spark appear when the lunge connects
        born = self._time + self.LUNGE_MS / 2
        self._sides[target].hit_at = born
        self._sounds.append((born, "hit" if target == ENEMY else "hurt"))
        self._popup(f"-{damage}", s.COLOR_WHITE, target, born)
        self._sparks.append(_Spark(self._sides[target].body_center, born))

    def _popup(self, text: str, color: tuple, who: str, born: float | None = None) -> None:
        x, y = self._sides[who].body_center
        self._popups.append(_Popup(text, color, (x, y - self.POPUP_LIFT),
                                   self._time if born is None else born))

    def _set_message(self, msg: str) -> None:
        self._message = msg
        self._message_timer = self.MESSAGE_MS

    def _finish(self) -> None:
        """Leave combat: Game Over after a defeat, else back to the state below."""
        machine = self.game.state_machine
        machine.pop()
        if self._phase == self.PHASE_DEFEAT:
            machine.change("game_over")
        elif self._phase == self.PHASE_VICTORY and self._on_victory:
            self._on_victory()

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._time += dt
        self._anim_timer += dt
        if self._phase == self.PHASE_INTRO and self._time >= self.INTRO_MS:
            self._phase = self.PHASE_PLAYER_CHOOSE
        for side in self._sides.values():
            self._update_hp_bar(side, dt)
        for when, name in self._sounds:
            if when <= self._time:
                self.game.audio.play(name)
        self._sounds = [sound for sound in self._sounds if sound[0] > self._time]
        self._popups = [p for p in self._popups if self._time - p.born < self.POPUP_MS]
        self._sparks = [sp for sp in self._sparks if self._time - sp.born < self.SPARK_MS]
        if self._message_timer > 0:
            self._message_timer -= dt
            # Only action phases auto-advance; victory/defeat wait for Enter
            if self._message_timer <= 0 and self._phase in (self.PHASE_PLAYER_ACT,
                                                            self.PHASE_ENEMY_ACT):
                self._advance_phase()

    def _update_hp_bar(self, side: _Side, dt: float) -> None:
        """Displayed HP drains toward the real value; a pale trail follows later."""
        if self._time < side.hit_at:
            return
        actual = side.fighter.hp
        step = self.HP_DRAIN_PER_MS * dt * max(1.0, abs(side.shown_hp - actual))
        if side.shown_hp > actual:
            side.shown_hp = max(actual, side.shown_hp - step)
        else:
            side.shown_hp = min(actual, side.shown_hp + step)
        if self._time - side.hit_at > self.HP_LAG_DELAY_MS:
            side.trail_hp -= step
        side.trail_hp = max(side.trail_hp, side.shown_hp)

    def _advance_phase(self) -> None:
        if self._battle.won:
            xp = self._battle.claim_reward()
            self._phase = self.PHASE_VICTORY
            self._attacker = None
            self._anim_timer = 0.0
            self.game.audio.stop_music(self.MUSIC_STOP_MS)
            self.game.audio.play("victory")
            self._set_message(f"{self._enemy.defeat_text} +{xp} XP")
        elif self._battle.lost:
            self._phase = self.PHASE_DEFEAT
            self._set_message("You collapse... everything goes dark.")
            self.game.audio.stop_music(self.MUSIC_STOP_MS)
            self.game.audio.play("defeat")
        elif self._phase == self.PHASE_PLAYER_ACT:
            self._enemy_attack()
        else:
            # The enemy has acted: back to the player
            self._phase = self.PHASE_PLAYER_CHOOSE
            self._actions.reset()

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(combat_backdrop(self.PLAYER_FEET, self.ENEMY_FEET), (0, 0))
        slide = round((1 - ease_out(self._time / self.INTRO_MS)) * self.SLIDE_PX)
        self._draw_enemy(surface, slide)
        self._draw_player(surface, -slide)
        self._draw_effects(surface)
        if self._phase != self.PHASE_INTRO:
            self._draw_panels(surface)
            self._draw_menu(surface)
            self._draw_message(surface)
            if self._hint and self._phase == self.PHASE_PLAYER_CHOOSE:
                draw_shadowed_text(surface, self._hint, font(26),
                                   (s.SCREEN_WIDTH // 2, self.HINT_Y), s.COLOR_TITLE_GOLD,
                                   anchor="midtop")
        if self._time < self.FLASH_MS:
            draw_veil(surface, 255 * (1 - self._time / self.FLASH_MS), s.COLOR_WHITE)

    def _anim_offsets(self, who: str) -> tuple[int, bool]:
        """(x offset, flashing) for a combatant from the current hit animation."""
        if self._attacker is None:
            return 0, False
        t = self._anim_timer
        if self._attacker == who:
            if t < self.LUNGE_MS:
                direction = 1 if who == PLAYER else -1
                return int(math.sin(math.pi * t / self.LUNGE_MS) * self.LUNGE_PX) * direction, False
            return 0, False
        # Target: shake and flash once the lunge connects
        hit_t = t - self.LUNGE_MS / 2
        if 0 <= hit_t < self.HIT_FLASH_MS:
            shake = self.SHAKE_PX if int(hit_t // self.SHAKE_STEP_MS) % 2 else -self.SHAKE_PX
            return shake, int(hit_t // self.BLINK_STEP_MS) % 2 == 0
        return 0, False

    def _draw_enemy(self, surface: pygame.Surface, slide: int) -> None:
        frames = ENEMY_IDLE_FRAMES.get(self._enemy.id, 1)
        frame = int(self._time // self.ENEMY_IDLE_MS) % frames
        spr = enemy(self._enemy.id, frame, s.COMBAT_SCALE)
        dx, flash = self._anim_offsets(ENEMY)
        x, y = self.ENEMY_FEET[0] + dx + slide, self.ENEMY_FEET[1]

        if self._phase == self.PHASE_VICTORY:
            # Hops away to the right, fading
            t = min(1.0, self._anim_timer / self.DEFEAT_FADE_MS)
            x += round(t * self.DEFEAT_HOP[0])
            y -= round(abs(math.sin(t * math.pi * 2)) * self.DEFEAT_HOP[1])
            spr = spr.copy()
            spr.set_alpha(int(255 * (1 - t)))
        elif flash:
            spr = silhouette(spr, s.COLOR_WHITE)
        surface.blit(spr, spr.get_rect(midbottom=(x, y)))

    def _draw_player(self, surface: pygame.Surface, slide: int) -> None:
        dx, flash = self._anim_offsets(PLAYER)
        striking = self._attacker == PLAYER and self.LUNGE_MS / 2 <= self._anim_timer < \
            self.LUNGE_MS * 2
        pose = "strike" if striking else "ready"
        body = battle_pose(self._player.look, pose)
        rect = body.get_rect(midbottom=(self.PLAYER_FEET[0] + dx + slide, self.PLAYER_FEET[1]))
        if flash:
            surface.blit(silhouette(body, s.COLOR_WHITE), rect)
            return
        surface.blit(body, rect)

        weapon = self._player.inventory.weapon
        weapon_spr = item(weapon["id"], s.COMBAT_SCALE) if weapon else None
        if weapon_spr:
            # The weapon's grip sits in the hand; striking swings it down 90°
            grip = self.WEAPON_GRIP
            if pose == "strike":
                weapon_spr = pygame.transform.rotate(weapon_spr, -90)
                grip = (s.TILE_SIZE - 1 - grip[1], grip[0])
            hand = POSE_HANDS[pose]
            surface.blit(weapon_spr, (rect.x + (hand[0] - grip[0]) * s.COMBAT_SCALE,
                                      rect.y + (hand[1] - grip[1]) * s.COMBAT_SCALE))

    def _draw_effects(self, surface: pygame.Surface) -> None:
        """Hit sparks and floating numbers."""
        for spark in self._sparks:
            t = (self._time - spark.born) / self.SPARK_MS
            if t < 0:
                continue
            x, y = spark.pos
            reach = 10 + round(t * 26)
            color = s.COLOR_WHITE if t < 0.5 else s.COLOR_TITLE_GOLD
            for i in range(self.SPARK_RAYS):
                a = i * math.tau / self.SPARK_RAYS + 0.3
                inner = (x + math.cos(a) * reach * 0.4, y + math.sin(a) * reach * 0.4)
                outer = (x + math.cos(a) * reach, y + math.sin(a) * reach)
                pygame.draw.line(surface, color, inner, outer, 4 if i % 2 else 2)
        number_font = font(48)
        for popup in self._popups:
            t = (self._time - popup.born) / self.POPUP_MS
            if t < 0:
                continue
            x, y = popup.pos
            rise = round(ease_out(t * 2) * self.POPUP_RISE)
            alpha = int(255 * min(1.0, (1 - t) * 3))
            label = number_font.render(popup.text, True, popup.color)
            rect = label.get_rect(center=(x, y - rise))
            shadow = number_font.render(popup.text, True, self.POPUP_SHADOW)
            shadow.set_alpha(alpha)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
                surface.blit(shadow, rect.move(dx, dy))
            label.set_alpha(alpha)
            surface.blit(label, rect)

    def _draw_hp_bar(self, surface: pygame.Surface, rect: pygame.Rect, side: _Side) -> None:
        max_hp = side.fighter.max_hp
        shown = side.shown_hp / max_hp
        color = self.HP_HIGH if shown > 0.5 else self.HP_MID if shown > 0.25 else self.HP_LOW
        draw_bar(surface, rect, shown, color, trail=side.trail_hp / max_hp)

    def _draw_panels(self, surface: pygame.Surface) -> None:
        # Enemy: name plate with HP
        panel = self.ENEMY_PANEL
        draw_panel(surface, panel, fill=self.PANEL_FILL, ornate=True)
        draw_shadowed_text(surface, self._enemy.name, font(30), (panel.x + 18, panel.y + 12),
                           s.COLOR_TITLE_GOLD)
        bar = pygame.Rect(panel.x + 56, panel.y + 46, panel.w - 80, self.BAR_HEIGHT)
        draw_shadowed_text(surface, "HP", font(22), (panel.x + 20, panel.y + 42), s.COLOR_SAND)
        self._draw_hp_bar(surface, bar, self._sides[ENEMY])

        # Player: portrait, name, HP with numbers
        panel = self.PLAYER_PANEL
        side = self._sides[PLAYER]
        draw_panel(surface, panel, fill=self.PANEL_FILL, ornate=True)
        face = portrait(self._player.look, factor=1)
        frame = face.get_rect(midleft=(panel.x + 16, panel.centery))
        pygame.draw.rect(surface, s.COLOR_PORTRAIT_BG, frame)
        surface.blit(face, frame)
        pygame.draw.rect(surface, s.COLOR_ACCENT_GOLD, frame.inflate(4, 4), 2)
        text_x = frame.right + 18
        draw_shadowed_text(surface, self._player.name, font(30), (text_x, panel.y + 14),
                           s.COLOR_TITLE_GOLD)
        bar = pygame.Rect(text_x + 34, panel.y + 52, self.PLAYER_BAR_WIDTH, self.BAR_HEIGHT)
        draw_shadowed_text(surface, "HP", font(22), (text_x, panel.y + 48), s.COLOR_SAND)
        self._draw_hp_bar(surface, bar, side)
        draw_shadowed_text(surface, f"{round(side.shown_hp)}/{self._player.max_hp}",
                           font(22), (bar.right + 10, panel.y + 48), s.COLOR_TEXT_LIGHT)

    def _draw_menu(self, surface: pygame.Surface) -> None:
        """The action menu, or the item list while choosing an item."""
        if self._phase == self.PHASE_PLAYER_CHOOSE:
            menu = self._actions
        elif self._phase == self.PHASE_ITEM_SELECT:
            menu = self._items
        else:
            return

        panel = self.MENU_PANEL
        draw_panel(surface, panel, fill=self.PANEL_FILL, ornate=True)
        cursor = laurel(flip=True)
        for row, (index, option) in enumerate(menu.window(self.MENU_ROWS)):
            selected = index == menu.selected
            y = panel.y + 22 + row * self.MENU_ROW_HEIGHT
            color = s.COLOR_TITLE_GOLD if selected else s.COLOR_SAND
            if menu is self._actions and option == self.FLEE and not self._battle.can_flee:
                color = s.COLOR_TEXT_DISABLED
            draw_shadowed_text(surface, option, font(30), (panel.x + 64, y), color)
            if selected:
                sway = round(math.sin(self._time / self.CURSOR_SWAY_MS) * 2)
                surface.blit(cursor, cursor.get_rect(midright=(panel.x + 56 + sway, y + 10)))

    def _draw_message(self, surface: pygame.Surface) -> None:
        # Victory/defeat messages stay up until the player presses Enter
        persistent = self._phase in (self.PHASE_VICTORY, self.PHASE_DEFEAT)
        if not self._message or (self._message_timer <= 0 and not persistent):
            return
        text_font = font(24)
        box = pygame.Rect((0, 0), text_font.size(self._message))
        box.center = (s.SCREEN_WIDTH // 2, self.MESSAGE_Y)
        box = box.inflate(40, 24)
        if self._phase in (self.PHASE_PLAYER_CHOOSE, self.PHASE_ITEM_SELECT):
            box.right = min(box.right, self.MENU_PANEL.left - 10)   # keep clear of the menu
        draw_panel(surface, box, fill=self.PANEL_FILL, ornate=True)
        draw_shadowed_text(surface, self._message, text_font, (box.x + 20, box.y + 12))
        if persistent:
            hint = font(20).render("[Enter] Continue", True, s.COLOR_TEXT_DIM)
            surface.blit(hint, hint.get_rect(midtop=(box.centerx, box.bottom + 6)))
