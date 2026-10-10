"""Regression checks for the EltonTraits-backed thrush record."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rufous_bellied_thrush_matches_eltontraits_row_and_license():
    record = json.loads(
        (ROOT / "species/turdus-rufiventris/species.json").read_text()
    )
    eltontraits = next(source for source in record["sources"] if source["id"] == "eltontraits")

    assert eltontraits["license"] == "CC-BY-4.0"
    assert eltontraits["license_url"] == "https://creativecommons.org/licenses/by/4.0/"
    assert record["traits"]["mass_kg"] == 0.06944
    assert record["traits"]["size_class"] == "Small"
    assert record["traits"]["diet"] == {"fruit": 0.5, "invertebrate": 0.5}
    assert record["habitat"]["use"] == {"ground": 1.0}
    assert [resource["tag"] for resource in record["habitat"]["resources"]] == [
        "invertebrate",
        "fruit",
        "nest_cup",
        "perch",
        "shrub_thicket",
    ]

    for path in ("traits.mass_kg", "traits.diet", "habitat.use"):
        note = record["provenance"][path]["note"].lower()
        assert "expected" not in note


def test_rufous_bellied_thrush_nesting_months_are_explicit():
    program_id = "bt-turdus-rufiventris-v1"
    program = json.loads(
        (ROOT / "species/turdus-rufiventris/behavior.json").read_text()
    )
    assert program["id"] == program_id
    months = [
        node["cond"]["month_in"]
        for node in _walk(program["root"])
        if "cond" in node and "month_in" in node["cond"]
    ]
    assert months == [[8, 9, 10, 11, 12, 1, 2, 3]]


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)
