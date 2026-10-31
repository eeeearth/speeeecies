"""Regression checks for the Sedge Warbler's seasonal behaviour gates."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_sedge_warbler_behavior_matches_breeding_calendar_and_feeding_mode():
    program = json.loads(
        (ROOT / "species/acrocephalus-schoenobaenus/behavior.json").read_text()
    )
    branches = program["root"]["selector"]

    song = branches[5]["sequence"]
    assert next(node["cond"]["month_in"] for node in song if "month_in" in node.get("cond", {})) == [4, 5, 6, 7]
    assert any(node.get("child", {}).get("act", {}).get("do") == "sing" for node in song)

    nesting = branches[6]["sequence"]
    assert nesting[1]["cond"]["month_in"] == ["${nest_m1}", 6, "${nest_m2}"]
    assert program["params"]["nest_m1"] == 5
    assert program["params"]["nest_m2"] == 7

    feeding = branches[7]["sequence"][-1]["act"]
    assert feeding == {"do": "eat_nearest", "tag": "${food_tag}", "gait": "hop"}
    night_roost = branches[4]["sequence"]
    assert night_roost[0]["cond"] == {"is_day": False}
    assert night_roost[-1]["act"]["do"] == "rest"
