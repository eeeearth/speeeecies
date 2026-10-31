import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_garden_warbler_behavior_selects_seasonal_foods_and_supported_gait():
    species = json.loads((ROOT / "species/sylvia-borin/species.json").read_text())
    behavior = json.loads((ROOT / "species/sylvia-borin/behavior.json").read_text())

    assert species["behavior"]["program"] == behavior["id"]
    nest = next(node["sequence"] for node in behavior["root"]["selector"] if "sequence" in node and node["sequence"][0].get("cond", {}).get("need") == "nest")
    assert nest[1]["cond"]["month_in"] == [4, 5, 6, 7]
    song = next(node["sequence"] for node in behavior["root"]["selector"] if "sequence" in node and node["sequence"] and node["sequence"][0].get("cond", {}).get("sun_elevation_between_deg") == [-6, 12])
    assert song[1]["cond"]["month_in"] == [4, 5, 6, 7]
    assert species["traits"]["locomotion_modes"] == ["Walk", "Hop", "Fly"]
    assert "walk" in species["look"]["poses"]

    hunger = behavior["root"]["selector"][7]["sequence"]
    feeding_selector = hunger[2]["selector"]
    fruit_branch, insect_branch = feeding_selector
    assert fruit_branch["sequence"][0]["cond"]["month_in"] == [7, 8, 9]
    assert fruit_branch["sequence"][1]["act"] == {
        "do": "eat_nearest",
        "tag": "fruit",
        "gait": "walk",
    }
    assert insect_branch["act"] == {
        "do": "eat_nearest",
        "tag": "invertebrate",
        "gait": "walk",
    }
