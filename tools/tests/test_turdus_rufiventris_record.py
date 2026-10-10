"""Regression checks for the EltonTraits-backed thrush record."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rufous_bellied_thrush_matches_eltontraits_row_and_license():
    record = json.loads(
        (ROOT / "species/turdus-rufiventris/species.json").read_text()
    )
    eltontraits = next(source for source in record["sources"] if source["id"] == "eltontraits")

    assert eltontraits["license"] == "CC0-1.0"
    assert eltontraits["url"] == "https://doi.org/10.6084/m9.figshare.3559887.v1"
    assert eltontraits["license_url"] == "https://creativecommons.org/publicdomain/zero/1.0/"
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
    assert months == [[10, 11, 12, 1, 2, 3]]

    record = json.loads(
        (ROOT / "species/turdus-rufiventris/species.json").read_text()
    )
    breeding = [phase for phase in record["seasonal"]["phases"] if phase["name"] == "breeding"]
    assert len(breeding) == 1
    assert breeding[0]["region"] == "AR"
    assert breeding[0]["start"] == "10-01"
    assert breeding[0]["end"] == "03-31"
    assert "Brazil song activity" in record["provenance"]["seasonal.phases"]["note"]
    assert "not establish nesting months" in record["provenance"]["seasonal.phases"]["note"]


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)
