"""
Element data access.
Loads data/elements.json once and exposes simple lookup helpers.
No game logic lives here.
"""

import json
import os
import random

_ELEMENTS = None
DATA_PATH = os.path.join("data", "elements.json")


def load_elements() -> list:
    """Return the full element list. Cached after first call."""
    global _ELEMENTS
    if _ELEMENTS is None:
        with open(DATA_PATH) as f:
            _ELEMENTS = json.load(f)
    return _ELEMENTS


def get_by_name(name: str) -> dict | None:
    """Return element dict by name (case-insensitive)."""
    name = name.lower()
    return next((e for e in load_elements() if e["name"].lower() == name), None)


def get_by_number(number: int) -> dict | None:
    return next((e for e in load_elements() if e["number"] == number), None)


def random_element(exclude: list[str] | None = None) -> dict:
    """Return a random element, optionally excluding a list of names."""
    pool = load_elements()
    if exclude:
        excl = {n.lower() for n in exclude}
        pool = [e for e in pool if e["name"].lower() not in excl]
    return random.choice(pool)


def wrong_choices(correct: dict, count: int = 3) -> list:
    """Return `count` elements that are NOT the correct one (for quiz distractors)."""
    pool = [e for e in load_elements() if e["name"] != correct["name"]]
    return random.sample(pool, min(count, len(pool)))
