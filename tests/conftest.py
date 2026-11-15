"""Shared fixtures: a headless game and a driver that plays it frame by frame."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # before pygame is imported
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from game.game import Game

FRAME_MS = 16


class FakeAudio:
    """Records the effects a test triggers instead of playing them."""

    def __init__(self) -> None:
        self.played: list[str] = []

    def play(self, name: str, volume: float = 1.0) -> None:
        self.played.append(name)


class _HeldKeys:
    """Stands in for ``pygame.key.get_pressed()``."""

    def __init__(self, held: set[int]) -> None:
        self._held = held

    def __getitem__(self, key: int) -> bool:
        return key in self._held


class Driver:
    """Plays the game without a window: steps frames, presses and holds keys.

    Time is simulated (``FRAME_MS`` per frame), so tests run as fast as the
    machine allows and always behave the same.
    """

    def __init__(self, game: Game, monkeypatch: pytest.MonkeyPatch) -> None:
        self.game = game
        self.held: set[int] = set()
        self.ticks = 0
        monkeypatch.setattr(pygame.time, "get_ticks", lambda: self.ticks)
        monkeypatch.setattr(pygame.key, "get_pressed", lambda: _HeldKeys(self.held))

    @property
    def state(self) -> str:
        """Class name of the top state, e.g. ``"Exploration"``."""
        return type(self.game.state_machine.current).__name__

    @property
    def scene(self):
        """The exploration state, wherever it is in the stack."""
        return next(state for state in self.game.state_machine.stack
                    if type(state).__name__ == "Exploration")

    @property
    def player(self):
        return self.game.session.player

    def step(self, frames: int = 1) -> None:
        for _ in range(frames):
            self.game.step([], FRAME_MS)
            self.ticks += FRAME_MS

    def press(self, key: int, settle: int = 1) -> None:
        """One key press, then ``settle`` quiet frames."""
        self.game.step([pygame.event.Event(pygame.KEYDOWN, key=key)], FRAME_MS)
        self.ticks += FRAME_MS
        self.step(settle)

    def hold(self, keys: tuple[int, ...], frames: int) -> None:
        self.held.update(keys)
        self.step(frames)
        self.held.clear()

    def wait_for(self, state: str, limit: int = 1500) -> None:
        """Step until the top state is ``state``."""
        for _ in range(limit):
            if self.state == state:
                return
            self.step()
        raise AssertionError(f"never reached {state}; stuck in {self.state}")

    def advance_dialogue(self, limit: int = 60) -> None:
        """Press through the open dialogue until it closes."""
        for _ in range(limit):
            if self.state != "Dialogue":
                return
            self.press(pygame.K_e, settle=2)
        raise AssertionError("dialogue never ended")

    def start_new_game(self) -> None:
        """Title screen → New Game → the first map has faded in."""
        self.press(pygame.K_SPACE)       # skip the title intro
        self.press(pygame.K_RETURN)      # New Game
        self.wait_for("Exploration")


@pytest.fixture(scope="session", autouse=True)
def _display():
    """A display for the whole run: sprite generators convert to its format."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game() -> Game:
    return Game(audio=False)


@pytest.fixture
def play(game: Game, monkeypatch: pytest.MonkeyPatch) -> Driver:
    return Driver(game, monkeypatch)


@pytest.fixture
def audio() -> FakeAudio:
    return FakeAudio()
