"""Regression coverage for the Adélie penguin's prey-specific dive FSM."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = REPO_ROOT / "species" / "pygoscelis-adeliae"


def load_program() -> dict:
    return json.loads((SPECIES_DIR / "behavior.json").read_text(encoding="utf-8"))


def resolve(value: str, params: dict) -> str:
    return params[value[2:-1]] if value.startswith("${") and value.endswith("}") else value


def matches(predicate: dict, *, food_tags: set[str], hunger: float, params: dict) -> bool:
    if "all" in predicate:
        return all(matches(child, food_tags=food_tags, hunger=hunger, params=params) for child in predicate["all"])
    if "any" in predicate:
        return any(matches(child, food_tags=food_tags, hunger=hunger, params=params) for child in predicate["any"])
    if "not" in predicate:
        return not matches(predicate["not"], food_tags=food_tags, hunger=hunger, params=params)
    if "threat_within_m" in predicate:
        return False
    if "conspecifics_within_m" in predicate:
        return False
    if "food_within_m" in predicate:
        return resolve(predicate["tag"], params) in food_tags
    if predicate.get("need") == "hunger":
        operator = "gt" if "gt" in predicate else "lt"
        return hunger > predicate[operator] if operator == "gt" else hunger < predicate[operator]
    raise AssertionError(f"Unhandled predicate in regression fixture: {predicate}")


def transition(program: dict, source: str, *, food_tags: set[str], hunger: float) -> str | None:
    candidates = [t for t in program["transitions"] if t["from"] in (source, "*")]
    candidates.sort(key=lambda t: t.get("priority", 0), reverse=True)
    for candidate in candidates:
        if matches(candidate["when"], food_tags=food_tags, hunger=hunger, params=program["params"]):
            return candidate["to"]
    return None


def test_krill_only_food_reaches_an_action_that_eats_krill() -> None:
    program = load_program()
    food_tags = {"invertebrate"}

    state = transition(program, "commute", food_tags=food_tags, hunger=0.8)

    assert state == "dive_forage_krill"
    action = program["states"][state]["action"]
    assert action["do"] == "eat_nearest"
    assert resolve(action["tag"], program["params"]) in food_tags


def test_fish_and_krill_routes_preserve_colony_and_commute_entries_and_exit_on_hunger() -> None:
    program = load_program()
    cases = [
        ("commute", {"small_vertebrate"}, "dive_forage_fish"),
        ("commute", {"invertebrate"}, "dive_forage_krill"),
        ("colony", {"small_vertebrate"}, "dive_forage_fish"),
        ("colony", {"invertebrate"}, "dive_forage_krill"),
    ]

    for source, food_tags, expected in cases:
        assert transition(program, source, food_tags=food_tags, hunger=0.8) == expected
        assert resolve(program["states"][expected]["action"]["tag"], program["params"]) in food_tags
        assert transition(program, source, food_tags=set(), hunger=0.8) is None

    for state in ("dive_forage_fish", "dive_forage_krill"):
        assert transition(program, state, food_tags=set(), hunger=0.1) == "haul_out"
        assert transition(program, state, food_tags=set(), hunger=0.5) is None
