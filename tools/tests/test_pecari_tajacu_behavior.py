"""Focused regression checks for the collared peccary's local foraging FSM."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = REPO_ROOT / "species" / "pecari-tajacu"


def load_record_and_program() -> tuple[dict, dict]:
    record = json.loads((SPECIES_DIR / "species.json").read_text(encoding="utf-8"))
    program = json.loads((SPECIES_DIR / "behavior.json").read_text(encoding="utf-8"))
    return record, program


def leaves(predicate: dict):
    if "all" in predicate or "any" in predicate:
        for child in predicate.get("all", predicate.get("any", [])):
            yield from leaves(child)
    elif "not" in predicate:
        yield from leaves(predicate["not"])
    else:
        yield predicate


def test_each_modeled_food_has_a_reachable_eat_action() -> None:
    record, program = load_record_and_program()
    diet_tags = set(record["traits"]["diet"])
    landscape_tags = {resource["tag"] for resource in record["habitat"]["resources"]}
    routes = {}
    for transition in program["transitions"]:
        if transition["from"] != "idle":
            continue
        predicates = list(leaves(transition["when"]))
        for predicate in predicates:
            if "food_within_m" in predicate:
                routes[predicate["tag"]] = transition["to"]

    assert diet_tags <= landscape_tags
    assert diet_tags <= routes.keys()
    for tag in diet_tags:
        action = program["states"][routes[tag]]["action"]
        assert action["do"] == "eat_nearest"
        assert action["tag"] == tag


def test_local_daylight_rest_and_trot_flee_match_the_regional_program() -> None:
    _, program = load_record_and_program()
    rest_entry = next(t for t in program["transitions"] if t["to"] == "rest" and t["from"] == "idle")
    rest_conditions = list(leaves(rest_entry["when"]))
    sun_condition = next(p for p in rest_conditions if "sun_elevation_between_deg" in p)
    lower, upper = sun_condition["sun_elevation_between_deg"]

    assert lower == "${rest_sun_lo_deg}"
    assert upper == "${rest_sun_hi_deg}"
    assert program["params"]["rest_sun_lo_deg"] == 55
    assert program["params"]["rest_sun_hi_deg"] == 90
    assert program["states"]["flee"]["action"]["gait"] == "trot"
    assert any(t["from"] == "rest" and t["to"] == "idle" for t in program["transitions"])
