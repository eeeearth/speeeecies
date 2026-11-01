"""Regression coverage for the black rat's climb-gait omnivory."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_every_recorded_food_resource_has_a_reachable_climb_feeding_action() -> None:
    record = json.loads((ROOT / "species/rattus-rattus/species.json").read_text())
    program = json.loads((ROOT / "species/rattus-rattus/behavior.json").read_text())
    resources = {
        resource["tag"]
        for resource in record["habitat"]["resources"]
        if resource["kind"] != "Shelter"
    }
    feeding_states = {
        state
        for state, action in program["states"].items()
        if action["action"]["do"] == "eat_nearest"
    }
    reachable = {
        transition["to"]
        for transition in program["transitions"]
        if transition["from"] == "idle"
        and transition["to"] in feeding_states
    }

    assert {program["states"][state]["action"]["tag"] for state in reachable} == resources
    gait_by_tag = {
        program["states"][state]["action"]["tag"]: program["states"][state]["action"]["gait"]
        for state in reachable
    }
    assert gait_by_tag["fruit"] == "climb"
    assert gait_by_tag["seed"] == "climb"
    assert gait_by_tag["invertebrate"] == "walk"
    assert gait_by_tag["carrion"] == "walk"


def test_local_program_keeps_nocturnal_rest_and_declared_escape_gaits() -> None:
    record = json.loads((ROOT / "species/rattus-rattus/species.json").read_text())
    program = json.loads((ROOT / "species/rattus-rattus/behavior.json").read_text())
    actions = [state["action"] for state in program["states"].values()]
    declared = {gait.lower() for gait in record["traits"]["locomotion_modes"]}
    used = {action["gait"] for action in actions if "gait" in action}

    assert used <= declared
    assert program["states"]["rest"]["action"] == {"do": "rest", "at": "shelter"}
    assert program["params"]["rest_sun_lo_deg"] == 10
    assert program["params"]["rest_sun_hi_deg"] == 90
