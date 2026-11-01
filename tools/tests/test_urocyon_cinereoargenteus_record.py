"""Regression checks for gray fox climbing and source-backed feeding actions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = ROOT / "species" / "urocyon-cinereoargenteus"


def load_species() -> dict:
    return json.loads((SPECIES_DIR / "species.json").read_text(encoding="utf-8"))


def load_behavior() -> dict:
    return json.loads((SPECIES_DIR / "behavior.json").read_text(encoding="utf-8"))


def test_gray_fox_flees_by_climbing_and_can_feed_on_each_modeled_diet_category() -> None:
    species = load_species()
    program = load_behavior()
    states = program["states"]
    transitions = program["transitions"]

    assert species["behavior"]["program"] == program["id"]
    assert "Climb" in species["traits"]["locomotion_modes"]
    assert states["flee"]["action"] == {"do": "flee", "gait": "climb"}

    food_states = {
        "forage_vertebrate": "small_vertebrate",
        "forage_invertebrate": "invertebrate",
        "forage_fruit": "fruit",
        "forage_carrion": "carrion",
    }
    for state, tag in food_states.items():
        assert states[state]["action"]["do"] == "eat_nearest"
        assert states[state]["action"]["tag"] == tag
        assert any(t["from"] == "idle" and t["to"] == state for t in transitions)
        assert any(t["from"] == state and t["to"] == "idle" for t in transitions)
        assert any(t["from"] == state and t["to"] == "rest" for t in transitions)

    assert not any("month_in" in t["when"] for t in transitions)
    assert "gallop" not in program["params"].values()
