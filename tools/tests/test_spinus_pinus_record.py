"""Focused checks for Pine Siskin behavior and its regional nest window."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPECIES = ROOT / "species/spinus-pinus"


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_pine_siskin_behavior_matches_supported_actions_and_nest_months():
    program = json.loads((SPECIES / "behavior.json").read_text())
    nodes = list(_walk(program["root"]))
    months = [
        node["cond"]["month_in"]
        for node in nodes
        if "cond" in node and "month_in" in node["cond"]
    ]
    assert months == [[4, 5, 6, 7]]

    eating = [node["act"] for node in nodes if node.get("act", {}).get("do") == "eat_nearest"]
    assert eating == [{"do": "eat_nearest", "tag": "${food_tag}", "gait": "hop"}]
    assert {"do": "fly_to_nearest", "tag": "perch"} in [
        node["act"] for node in nodes if "act" in node
    ]
    assert any(node.get("act", {}).get("do") == "build_nest" for node in nodes)
    assert not any(node.get("act", {}).get("do") in {"sing", "alarm"} for node in nodes)


def test_pine_siskin_activity_curve_uses_both_usable_us_sources():
    record = json.loads((SPECIES / "species.json").read_text())
    activity = record["activity"]["regions"][0]
    assert activity["region"] == "US"
    assert len(activity["monthly"]) == 12
    assert activity["observations"] == 2_463_175
    assert activity["query"]["inat"]["tier"] == "A"
    assert activity["query"]["inat"]["usable"] is True
    assert activity["query"]["gbif"]["tier"] == "A"
    assert activity["query"]["gbif"]["usable"] is True
