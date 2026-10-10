"""Regression checks for the Laughing dove's evidence and species-only model."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = ROOT / "species" / "spilopelia-senegalensis"


def load_species() -> dict:
    return json.loads((SPECIES_DIR / "species.json").read_text(encoding="utf-8"))


def load_behavior() -> dict:
    return json.loads((SPECIES_DIR / "behavior.json").read_text(encoding="utf-8"))


def actions(node: dict):
    if "act" in node:
        yield node["act"]
    for key in ("selector", "sequence"):
        for child in node.get(key, []):
            yield from actions(child)
    if "child" in node:
        yield from actions(node["child"])


def test_uncalibrated_wingspan_and_conflated_columba_sources_are_omitted() -> None:
    species = load_species()

    assert "wingspan_m" not in species["traits"]
    assert "traits.wingspan_m" not in species["provenance"]
    source_ids = {source["id"] for source in species["sources"]}
    assert not {"wikipedia-rock-dove", "wikipedia-stock-dove"} & source_ids


def test_mass_note_does_not_claim_the_measured_value_fits_the_conflicting_range() -> None:
    note = load_species()["provenance"]["traits.mass_kg"]["note"]

    assert "94-124" not in note
    assert "sits inside both" not in note


def test_side_neck_checker_is_drawn_on_both_sides_of_the_head() -> None:
    look = load_species()["look"]

    assert look["proportions"]["neck_angle_deg"] >= 20
    checkers = [part for part in look["extra_parts"] if part["name"].startswith("neck_checker")]
    assert len(checkers) >= 2
    assert all(part["parent"] == "head" and part.get("mirror") is True for part in checkers)
    assert all(0.5 <= part["offset"][2] <= 0.7 for part in checkers)
    assert all(part["size"][2] <= 0.2 for part in checkers)
    assert all(part["color"] == "accent" for part in checkers)


def test_species_behavior_walks_to_food_and_does_not_use_coo_as_alarm() -> None:
    species = load_species()
    program = load_behavior()
    program_actions = list(actions(program["root"]))

    assert species["behavior"]["program"] == program["id"]
    forage = [action for action in program_actions if action["do"] == "eat_nearest"]
    assert forage and all(action.get("gait") == "walk" for action in forage)
    assert all(action["do"] != "alarm" for action in program_actions)
    assert species["behavior"]["params"]["song"] == "coo"
    assert "alarm" not in species["behavior"]["params"]
