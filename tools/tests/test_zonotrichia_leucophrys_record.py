"""Regression checks for the White-crowned Sparrow species-local behaviour."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / "species/zonotrichia-leucophrys/behavior.json"
RECORD = ROOT / "species/zonotrichia-leucophrys/species.json"


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def test_nesting_months_are_an_explicit_april_to_july_set():
    program = json.loads(PROGRAM.read_text())
    assert program["id"] == "bt-zonotrichia-leucophrys-v1"
    months = [
        node["cond"]["month_in"]
        for node in _walk(program["root"])
        if "cond" in node and isinstance(node["cond"], dict) and "month_in" in node["cond"]
    ]
    assert months == [[4, 5, 6, 7]]


def test_seed_and_invertebrate_feeding_are_both_reachable():
    program = json.loads(PROGRAM.read_text())
    eat_tags = [
        node["act"]["tag"]
        for node in _walk(program["root"])
        if "act" in node and node["act"].get("do") == "eat_nearest"
    ]
    assert eat_tags == ["${food_tag}", "seed"]


def test_ground_fallback_does_not_fly_to_a_perch_when_not_hungry():
    program = json.loads(PROGRAM.read_text())
    children = program["root"]["selector"]
    assert children[-1] == {"act": {"do": "wander", "gait": "hop"}}
    assert not any("cooldown_s" in node and "child" in node for node in children)


def test_record_uses_species_local_program_and_derived_lifespan():
    record = json.loads(RECORD.read_text())
    assert record["behavior"] == {"program": "bt-zonotrichia-leucophrys-v1"}
    assert record["external"]["gbif_usage_key"] == 5231132
    assert record["external"]["inat_taxon_id"] == 9176
    lifespan = record["provenance"]["traits.lifespan_y"]
    assert lifespan["derived"] is True
    assert lifespan["confidence"] == "Low"
    assert abs(record["traits"]["lifespan_y"] - 1.77) < 0.01
    assert record["traits"]["diet"]["seed"] == 0.7
