"""Game content read from ``assets/data``: items, enemies, maps and scripts.

This is the one place that touches the data files. Items and enemies are
loaded once and shared, so treat the returned dicts as read-only.
"""

from __future__ import annotations

import functools
import json
import os

import settings as s


class ContentError(Exception):
    """A data file is missing or is not valid JSON."""


def load_json(*parts: str) -> dict:
    """Read a JSON file below ``assets/data``, e.g. ``load_json("maps", "village.json")``."""
    path = os.path.join(s.DATA_DIR, *parts)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as error:
        raise ContentError(f"Missing data file: {path}") from error
    except json.JSONDecodeError as error:
        raise ContentError(f"Invalid JSON in {path}: {error}") from error


@functools.cache
def items() -> dict[str, dict]:
    """Every item from items.json, keyed by id."""
    return {entry["id"]: entry for entry in load_json("items.json")["items"]}


@functools.cache
def enemies() -> dict[str, dict]:
    """Every enemy from enemies.json, keyed by id."""
    return {entry["id"]: entry for entry in load_json("enemies.json")["enemies"]}


def load_map(name: str) -> dict:
    """The raw map JSON for ``assets/data/maps/<name>.json``."""
    return load_json("maps", f"{name}.json")


def load_script(script_id: str) -> dict:
    """The data (text, ids, positions) for a map script."""
    return load_json("scripts", f"{script_id}.json")
