"""Shared UI logic: menus, key groups, fades, the state stack."""

from __future__ import annotations

import pygame

from game.state_machine import State, StateMachine
from systems import controls
from ui.effects import ScreenFade, ease_out
from ui.menu import Menu


def test_menu_moves_wraps_and_confirms(audio):
    menu = Menu(audio, ["Attack", "Defend", "Item"])

    assert not menu.handle_key(pygame.K_DOWN)
    assert not menu.handle_key(pygame.K_s)
    assert menu.choice == "Item"
    assert not menu.handle_key(pygame.K_DOWN)       # wraps to the top
    assert menu.selected == 0
    assert not menu.handle_key(pygame.K_w)          # and back to the bottom
    assert menu.choice == "Item"
    assert audio.played == ["menu_move"] * 4

    for key in controls.CONFIRM:
        assert menu.handle_key(key)
    assert not menu.handle_key(pygame.K_x)
    assert menu.choice == "Item"                    # confirming doesn't move


def test_menu_reset_and_scrolling_window(audio):
    menu = Menu(audio, ["old"])
    menu.reset([f"Item {i}" for i in range(6)])
    assert menu.window(4) == [(0, "Item 0"), (1, "Item 1"), (2, "Item 2"), (3, "Item 3")]

    for _ in range(5):
        menu.handle_key(pygame.K_DOWN)
    assert [index for index, _ in menu.window(4)] == [2, 3, 4, 5]
    assert menu.window(10)[-1] == (5, "Item 5")

    menu.reset()
    assert menu.selected == 0 and len(menu.options) == 6


def test_movement_combines_keys_and_cancels_opposites():
    def keys(*held):
        return {key: key in held for group in (controls.UP, controls.DOWN, controls.LEFT,
                                               controls.RIGHT) for key in group}

    assert controls.movement(keys()) == (0, 0)
    assert controls.movement(keys(pygame.K_w, pygame.K_RIGHT)) == (1, -1)
    assert controls.movement(keys(pygame.K_a, pygame.K_d, pygame.K_DOWN)) == (0, 1)


def test_pressed_keys_ignores_other_events():
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e),
              pygame.event.Event(pygame.KEYUP, key=pygame.K_e),
              pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)]
    assert controls.pressed_keys(events) == [pygame.K_e, pygame.K_m]


def test_screen_fade_runs_once_then_calls_back():
    fade = ScreenFade(speed=0.5)
    done = []
    assert not fade.active

    fade.fade_out(lambda: done.append("out"))
    frames = 0
    while fade.active:
        fade.update(16)
        frames += 1
    assert done == ["out"]
    assert 500 <= frames * 16 <= 540        # about half a second

    fade.update(16)                          # idle: nothing more happens
    assert done == ["out"]

    fade.fade_in(lambda: done.append("in"))
    while fade.active:
        fade.update(16)
    assert done == ["out", "in"]


def test_ease_out_is_clamped_and_front_loaded():
    assert ease_out(-1) == 0 and ease_out(0) == 0
    assert ease_out(1) == 1 and ease_out(5) == 1
    assert ease_out(0.5) > 0.5


class _Recorder(State):
    def __init__(self, name: str, log: list[str]) -> None:
        super().__init__(game=None)
        self.name, self.log = name, log

    def enter(self, params=None) -> None:
        self.log.append(f"{self.name} enter {params}")

    def exit(self) -> None:
        self.log.append(f"{self.name} exit")

    def resume(self) -> None:
        self.log.append(f"{self.name} resume")


def test_state_stack_push_pop_change():
    log: list[str] = []
    machine = StateMachine()
    for name in ("map", "talk", "menu"):
        machine.register(name, _Recorder(name, log))
    assert machine.current is None

    machine.push("map", {"map": "village"})
    machine.push("talk")
    assert [state.name for state in machine.stack] == ["map", "talk"]
    machine.pop()
    machine.change("menu")
    assert [state.name for state in machine.stack] == ["menu"]
    assert log == ["map enter {'map': 'village'}", "talk enter None", "talk exit",
                   "map resume", "map exit", "menu enter None"]
