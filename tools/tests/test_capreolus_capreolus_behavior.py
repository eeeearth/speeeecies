import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_roe_deer_behavior_reaches_browse_graze_and_day_rest():
    program = json.loads((ROOT / "species/capreolus-capreolus/behavior.json").read_text())
    record = json.loads((ROOT / "species/capreolus-capreolus/species.json").read_text())
    states = program["states"]
    transitions = program["transitions"]

    for tag in ("browse", "graze"):
        forage_state = states[tag]
        assert forage_state["action"] == {"do": "eat_nearest", "tag": tag, "gait": "${forage_gait}"}
        assert any(
            transition["to"] == tag
            and transition["when"].get("all", [{}])[1] == {"food_within_m": "${food_m}", "tag": tag}
            for transition in transitions
        )
        assert any(transition["from"] == tag and transition["to"] == "idle" for transition in transitions)

    assert any(
        transition["from"] == "*"
        and transition["to"] == "rest"
        and transition.get("priority") == 10
        and transition["when"] == {"sun_elevation_between_deg": ["${rest_sun_lo_deg}", "${rest_sun_hi_deg}"]}
        for transition in transitions
    )
    assert program["params"]["rest_sun_lo_deg"] == 10
    assert program["params"]["rest_sun_hi_deg"] == 90
    assert program["states"]["flee"]["action"]["gait"] == "${flee_gait}"
    assert program["params"]["flee_gait"] == "gallop"
    assert record["seasonal"]["phases"][0]["start"] == "07-01"
    assert record["seasonal"]["phases"][0]["end"] == "08-31"
