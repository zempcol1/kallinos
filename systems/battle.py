"""Combat rules, free of pygame: who hits whom for how much, and who has won.

``states/combat.py`` is the screen (menus, animation, messages); it asks a
``Battle`` what each action does. Skills, status effects and enemy move
lists belong here.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.enemy import Enemy
    from entities.player import Player


class Battle:
    """One fight between the player and an enemy.

    Every action applies its effect right away and returns what happened, so
    the screen can show it. ``rng`` can be a seeded ``random.Random`` (tests).
    """

    MIN_DAMAGE = 1
    PLAYER_VARIANCE = (-1, 2)   # random spread added to the player's hits
    ENEMY_VARIANCE = (-1, 1)
    GUARD_DIVISOR = 2           # defending halves the next hit taken
    FLEE_CHANCE = 0.5

    def __init__(self, player: Player, enemy: Enemy, can_flee: bool = True,
                 rng: random.Random | None = None) -> None:
        self.player = player
        self.enemy = enemy
        self.can_flee = can_flee
        self._rng = rng or random
        self._guarding = False

    @property
    def won(self) -> bool:
        return self.enemy.hp <= 0

    @property
    def lost(self) -> bool:
        return self.player.hp <= 0

    def player_attack(self) -> int:
        """Strike with the equipped weapon (or bare fists); returns the damage."""
        weapon = self.player.inventory.weapon
        bonus = weapon.get("attack_bonus", 0) if weapon else 0
        return self._strike(self.player.attack + bonus, self.enemy, self.PLAYER_VARIANCE)

    def enemy_attack(self) -> int:
        """The enemy's turn; a guard raised by ``defend`` is used up. Returns the damage."""
        guarded, self._guarding = self._guarding, False
        return self._strike(self.enemy.attack, self.player, self.ENEMY_VARIANCE, guarded)

    def defend(self) -> None:
        """Brace: the enemy's next hit does half damage."""
        self._guarding = True

    def use_item(self, item: dict) -> int:
        """Consume one of ``item`` from the player's inventory; returns the HP healed."""
        self.player.inventory.remove_item(item["id"])
        healed = min(item.get("heal", 0), self.player.max_hp - self.player.hp)
        self.player.hp += healed
        return healed

    def try_flee(self) -> bool:
        """Whether the player gets away."""
        return self.can_flee and self._rng.random() < self.FLEE_CHANCE

    def claim_reward(self) -> int:
        """Give the player the XP for winning; returns the amount."""
        self.player.xp += self.enemy.xp_reward
        return self.enemy.xp_reward

    def _strike(self, power: int, target: Player | Enemy, variance: tuple[int, int],
                guarded: bool = False) -> int:
        raw = power - target.defense
        if guarded:
            raw //= self.GUARD_DIVISOR
        damage = max(self.MIN_DAMAGE, raw + self._rng.randint(*variance))
        target.hp = max(0, target.hp - damage)
        return damage
