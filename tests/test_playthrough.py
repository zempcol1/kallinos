"""End-to-end: the game played headlessly through real key presses.

The fight needs no seeded dice: Kallinos (35 HP, 3–6 damage a hit with the
branch) always outlasts the Vátrachos (18 HP, at most 4 a hit), and at 1 HP
he always falls to its first lunge.
"""

from __future__ import annotations

import pygame

ROUND_FRAMES = 160      # both combatants' messages have played out


def reach_free_roam(play) -> None:
    """New game, through the intro, until Niko has vanished and the player may walk."""
    play.start_new_game()
    play.wait_for("Dialogue")
    play.advance_dialogue()
    play.step(300)


def pick_up_branch(play) -> None:
    play.player.place(12, 10)
    play.press(pygame.K_e, settle=2)


def walk_into_boulder_zone(play) -> None:
    zone = play.scene.tile_map.get_trigger("boulder_zone")
    play.player.x, play.player.y = zone.left + 10, zone.bottom - 14
    play.step(2)


def fight_until_over(play, key: int = pygame.K_RETURN, limit: int = 12) -> None:
    """Attack every round (and confirm the result screen) until combat closes."""
    for _ in range(limit):
        if play.state != "Combat":
            return
        play.press(key, settle=ROUND_FRAMES)
    raise AssertionError("combat never ended")


def test_title_menu(play):
    assert play.state == "MainMenu"
    play.press(pygame.K_SPACE)                  # skips the intro, selects nothing
    play.press(pygame.K_DOWN)
    play.press(pygame.K_RETURN)                 # Continue: nothing to load yet
    assert play.state == "MainMenu"
    play.press(pygame.K_DOWN)
    play.press(pygame.K_RETURN)                 # Quit
    assert not play.game.running


def test_tutorial_from_title_to_village(play):
    reach_free_roam(play)
    scene, player = play.scene, play.player
    assert play.state == "Exploration"
    assert play.game.session.current_map == "tutorial"
    assert not scene.get_npc("niko").visible

    # Walking: held keys move the player, walls stop them
    start = (player.x, player.y)
    play.hold((pygame.K_LEFT,), 30)
    assert player.x < start[0] and player.y == start[1] and player.facing == "left"
    play.hold((pygame.K_UP, pygame.K_d), 20)
    assert player.facing == "up_right"

    # The boulder without a weapon: a warning, and a step back out of the zone
    walk_into_boulder_zone(play)
    assert play.state == "Dialogue"
    play.advance_dialogue()
    zone = scene.tile_map.get_trigger("boulder_zone")
    assert not player.rect.colliderect(zone)

    # The branch is picked up and equipped; a fig tree gives figs once
    pick_up_branch(play)
    assert player.inventory.weapon["id"] == "olive_branch"
    player.place(6, 8)
    player.facing = "up"
    play.step(2)
    play.press(pygame.K_e, settle=2)
    play.press(pygame.K_e, settle=2)
    assert player.inventory.count("figs") == 1

    # Doros has something to say, and stays where he is
    player.place(9, 7)
    player.facing = "up"
    play.step(2)
    play.press(pygame.K_RETURN, settle=2)
    assert play.state == "Dialogue"
    play.advance_dialogue()

    # Back to the boulder, armed: reveal, then the fight
    walk_into_boulder_zone(play)
    play.advance_dialogue()
    assert play.state == "Combat"
    play.step(60)                                   # battle intro

    for _ in range(3):
        play.press(pygame.K_DOWN)
    play.press(pygame.K_RETURN)                     # Flee: not from the tutorial fight
    assert play.state == "Combat"

    play.press(pygame.K_UP)
    play.press(pygame.K_UP)
    play.press(pygame.K_RETURN, settle=ROUND_FRAMES)    # Defend, then the frog's lunge
    hurt = player.hp
    assert 0 < hurt < player.max_hp

    play.press(pygame.K_DOWN)
    play.press(pygame.K_DOWN)
    play.press(pygame.K_RETURN)                     # Item
    play.press(pygame.K_RETURN, settle=ROUND_FRAMES)    # Figs
    assert not player.inventory.has_item("figs")
    assert player.hp > hurt - 5                     # healed, minus one more lunge

    fight_until_over(play)
    assert player.hp > 0 and player.xp == 10

    # Niko drops out of the tree, the olive shimmers, the chapter card appears
    play.wait_for("Dialogue")
    assert scene.get_npc("niko").visible
    play.advance_dialogue()
    play.wait_for("TitleCard")
    play.step(80)
    play.press(pygame.K_RETURN)

    # The village: everything Kallinos earned came along
    assert play.state == "Exploration"
    assert play.game.session.current_map == "village"
    assert player.xp == 10 and player.inventory.has_item("olive_branch")
    play.step(60)
    player.place(16, 7)
    player.facing = "up"
    play.step(2)
    play.press(pygame.K_e, settle=2)
    assert play.state == "Dialogue"                 # Elder Theron
    play.advance_dialogue()

    play.press(pygame.K_ESCAPE)
    assert play.state == "MainMenu"


def test_defeat_then_retry_restores_the_checkpoint(play):
    reach_free_roam(play)
    pick_up_branch(play)
    play.player.hp = 1
    walk_into_boulder_zone(play)
    play.advance_dialogue()
    play.step(60)
    fight_until_over(play)
    assert play.state == "GameOver"

    play.step(60)                                   # the screen ignores keys at first
    play.press(pygame.K_e)                          # Retry
    assert play.state == "Exploration"
    assert play.game.session.current_map == "tutorial"
    assert play.player.hp == play.player.max_hp
    assert not play.player.inventory.has_item("olive_branch")


def test_defeat_then_back_to_the_title(play):
    reach_free_roam(play)
    pick_up_branch(play)
    play.player.hp = 1
    walk_into_boulder_zone(play)
    play.advance_dialogue()
    play.step(60)
    fight_until_over(play, key=pygame.K_SPACE)
    play.step(60)
    play.press(pygame.K_s)
    play.press(pygame.K_SPACE)                      # Main Menu
    assert play.state == "MainMenu"
