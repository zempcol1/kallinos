"""Inventory: counts by item id and the equipped weapon."""

from __future__ import annotations

import pytest

from systems.inventory_system import Inventory


def test_items_stack_and_keep_pickup_order():
    inventory = Inventory()
    inventory.add_item("figs")
    inventory.add_item("olive_branch")
    inventory.add_item("figs", 2)

    assert inventory.count("figs") == 3
    assert [(item["id"], count) for item, count in inventory.stacks()] == [
        ("figs", 3), ("olive_branch", 1)]
    assert [item["id"] for item, _ in inventory.stacks("consumable")] == ["figs"]


def test_remove_takes_one_at_a_time():
    inventory = Inventory()
    inventory.add_item("figs", 2)

    assert inventory.remove_item("figs")
    assert inventory.has_item("figs")
    assert inventory.remove_item("figs")
    assert not inventory.has_item("figs")
    assert not inventory.remove_item("figs")


def test_unknown_items_are_rejected():
    with pytest.raises(KeyError):
        Inventory().add_item("excalibur")


def test_only_carried_weapons_can_be_equipped():
    inventory = Inventory()
    assert inventory.weapon is None
    assert not inventory.equip_weapon("olive_branch")      # not carried

    inventory.add_item("figs")
    assert not inventory.equip_weapon("figs")              # not a weapon

    inventory.add_item("olive_branch")
    assert inventory.equip_weapon("olive_branch")
    assert inventory.weapon["name"] == "Olive-Wood Branch"


def test_losing_the_last_copy_unequips_the_weapon():
    inventory = Inventory()
    inventory.add_item("olive_branch", 2)
    inventory.equip_weapon("olive_branch")

    inventory.remove_item("olive_branch")
    assert inventory.weapon is not None
    inventory.remove_item("olive_branch")
    assert inventory.weapon is None
