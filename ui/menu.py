"""Menu — the cursor logic every list of options shares."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from systems import controls

if TYPE_CHECKING:
    from systems.audio import Audio


class Menu:
    """A vertical list with one selected row: keys, wrap-around, move sound.

    Only the logic lives here. Drawing stays with the owner, because the
    title, combat and game-over menus each look different; ``window`` helps
    with lists longer than the space they have.
    """

    def __init__(self, audio: Audio, options: Sequence[str] = ()) -> None:
        self._audio = audio
        self.options = list(options)
        self.selected = 0

    def reset(self, options: Sequence[str] | None = None) -> None:
        """Back to the first row, optionally with a new list of options."""
        if options is not None:
            self.options = list(options)
        self.selected = 0

    @property
    def choice(self) -> str:
        """The selected option's text."""
        return self.options[self.selected]

    def handle_key(self, key: int) -> bool:
        """Move the cursor on up/down; True when the selection was confirmed."""
        if key in controls.UP:
            self._move(-1)
        elif key in controls.DOWN:
            self._move(1)
        else:
            return key in controls.CONFIRM
        return False

    def _move(self, step: int) -> None:
        self.selected = (self.selected + step) % len(self.options)
        self._audio.play("menu_move")

    def window(self, rows: int) -> list[tuple[int, str]]:
        """Up to ``rows`` (index, option) pairs, scrolled to keep the selection in view."""
        first = max(0, self.selected - rows + 1)
        return list(enumerate(self.options))[first:first + rows]
