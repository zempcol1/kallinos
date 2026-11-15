"""Combat rules (systems/battle.py), without the combat screen."""

from __future__ import annotations

import pytest

from entities.enemy import Enemy
from entities.player import Player
from systems.battle import Battle


class FixedRng:
    """Always rolls the same: ``roll`` for damage spread, ``chance`` for 0–1 rolls."""

    def __init__(self, roll: int = 0, chance: float = 0.0) -> None:
        self.roll = roll
        self.chance = chance

    def randint(self, low: int, high: int) -> int:
        return max(low, min(high, self.roll))

    def random(self) -> float:
        return self.chance


def make_battle(roll: int = 0, chance: float = 0.0, can_flee: bool = True, **enemy) -> Battle:
    stats = {"id": "dummy", "name": "Dummy", "hp": 20, "attack": 5, "defense": 1,
             "xp_reward": 7, **enemy}
    return Battle(Player(0, 0), Enemy(stats), can_flee, FixedRng(roll, chance))


def test_bare_fists_hit_for_attack_minus_defense():
    battle = make_battle()
    assert battle.player_attack() == battle.player.attack - battle.enemy.defense
    assert battle.enemy.hp == 20 - 2


def test_weapon_adds_its_attack_bonus():
    battle = make_battle()
    battle.player.inventory.add_item("olive_branch")
    battle.player.inventory.equip_weapon("olive_branch")
    assert battle.player_attack() == 3 + 2 - 1


def test_damage_spread_stays_in_range():
    assert make_battle(roll=99).player_attack() == 2 + Battle.PLAYER_VARIANCE[1]
    assert make_battle(roll=-99).player_attack() == 2 + Battle.PLAYER_VARIANCE[0]
    assert make_battle(roll=99).enemy_attack() == 4 + Battle.ENEMY_VARIANCE[1]


def test_a_hit_always_does_at_least_one_damage():
    battle = make_battle(roll=-99, defense=50, attack=0)
    assert battle.player_attack() == Battle.MIN_DAMAGE
    assert battle.enemy_attack() == Battle.MIN_DAMAGE


def test_hp_never_drops_below_zero():
    battle = make_battle(hp=1)
    battle.player_attack()
    assert battle.enemy.hp == 0
    assert battle.won and not battle.lost


def test_defending_halves_only_the_next_hit():
    battle = make_battle()          # enemy hits for 5 - 1 = 4
    battle.defend()
    assert battle.enemy_attack() == 2
    assert battle.enemy_attack() == 4


def test_item_heals_up_to_max_hp_and_is_consumed():
    battle = make_battle()
    player = battle.player
    player.inventory.add_item("figs", 2)
    figs = player.inventory.stacks("consumable")[0][0]

    player.hp = player.max_hp - 3
    assert battle.use_item(figs) == 3
    assert player.hp == player.max_hp
    assert player.inventory.count("figs") == 1

    player.hp = 1
    assert battle.use_item(figs) == figs["heal"]
    assert not player.inventory.has_item("figs")


@pytest.mark.parametrize("chance, escaped", [(0.0, True), (0.49, True), (0.5, False)])
def test_flee_is_a_coin_toss(chance, escaped):
    assert make_battle(chance=chance).try_flee() is escaped


def test_cannot_flee_when_the_fight_forbids_it():
    assert not make_battle(chance=0.0, can_flee=False).try_flee()


def test_losing_and_reward():
    battle = make_battle()
    battle.player.hp = 1
    battle.enemy_attack()
    assert battle.lost and not battle.won

    assert battle.claim_reward() == 7
    assert battle.player.xp == 7
