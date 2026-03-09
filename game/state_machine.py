"""State Machine and base State class for Kallinos."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.game import Game


class State:
    """Base class that all game states inherit from.

    Subclasses must override handle_events, update, and render.
    enter() and exit() are optional hooks.
    """

    def __init__(self, game: Game) -> None:
        self.game = game

    def enter(self, params: dict | None = None) -> None:
        """Called when this state becomes the active state."""

    def exit(self) -> None:
        """Called when this state is removed from the stack."""

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        raise NotImplementedError

    def render(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


class StateMachine:
    """A stack-based finite state machine.

    States are registered by name and instantiated once. The machine
    maintains a stack so states can be pushed (pausing the previous)
    and popped (resuming it).
    """

    def __init__(self) -> None:
        self._states: dict[str, State] = {}
        self._stack: list[State] = []

    def register(self, name: str, state: State) -> None:
        """Register a state instance under a name."""
        self._states[name] = state

    @property
    def current(self) -> State | None:
        """The state on top of the stack, or None if empty."""
        return self._stack[-1] if self._stack else None

    def push(self, name: str, params: dict | None = None) -> None:
        """Push a new state onto the stack, calling its enter()."""
        state = self._states[name]
        self._stack.append(state)
        state.enter(params)

    def pop(self) -> None:
        """Pop the current state, calling its exit(), and resume the one below."""
        if self._stack:
            self._stack[-1].exit()
            self._stack.pop()
            # Re-enter the state that is now on top
            if self._stack:
                self._stack[-1].enter()

    def change(self, name: str, params: dict | None = None) -> None:
        """Replace the current state: pop, then push the new one."""
        if self._stack:
            self._stack[-1].exit()
            self._stack.pop()
        state = self._states[name]
        self._stack.append(state)
        state.enter(params)
