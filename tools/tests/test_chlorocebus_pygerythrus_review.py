import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = ROOT / "species" / "chlorocebus-pygerythrus"


def load_json(name):
    return json.loads((SPECIES_DIR / name).read_text())


def test_eltontraits_diet_retains_values_but_marks_genus_imputation():
    record = load_json("species.json")
    provenance = record["provenance"]["traits.diet"]

    assert record["traits"]["diet"] == {
        "fruit": 0.4,
        "invertebrate": 0.2,
        "browse": 0.2,
        "vertebrate": 0.2,
    }
    assert record["sources"][[s["id"] for s in record["sources"]].index("eltontraits")]["license"] == "CC0-1.0"
    assert provenance["confidence"] != "High"
    assert provenance["derived"] is True
    assert "D1" in provenance["note"] and "genus" in provenance["note"].lower()


def test_maximum_lifespan_and_home_range_are_not_typical_scalars():
    record = load_json("species.json")

    assert record["traits"]["lifespan_y"] == 11
    lifespan = record["provenance"]["traits.lifespan_y"]
    assert lifespan["derived"] is True
    assert "10-12" in lifespan["note"]
    assert "(10 + 12) / 2" in lifespan["note"]
    assert "home_range_ha" not in record["traits"]
    assert "traits.home_range_ha" not in record["provenance"]


def test_mating_window_is_derived_from_birth_window_and_gestation():
    record = load_json("species.json")
    phases = {phase["name"]: phase for phase in record["seasonal"]["phases"]}

    assert phases["mating"]["start"] == "03-20"
    assert phases["mating"]["end"] == "09-16"
    assert "165" in phases["mating"]["note"]
    assert record["provenance"]["seasonal.phases"]["derived"] is True


def test_species_behavior_describes_only_implemented_actions():
    record = load_json("species.json")
    behavior = load_json("behavior.json")
    params = behavior["params"]
    states = behavior["states"]
    transitions = behavior["transitions"]

    assert "sentinel_interval_s" not in params
    assert params["alert_min_dwell_s"] == 300
    assert behavior["id"] == record["behavior"]["program"] == "fsm-vervet-forager-v1"
    assert record["behavior"]["params"]["alert_min_dwell_s"] == 300
    assert "sentinel_interval_s" not in record["behavior"]["params"]
    assert "sentinel" not in states
    assert states["alert"]["action"] == {"do": "emote", "kind": "alert"}
    assert states["flee"]["action"]["gait"] == "walk"
    assert any(t["from"] == "forage" and t["to"] == "alert" for t in transitions)
    description = behavior["description"].lower()
    assert "flees to the trees" not in description
    assert "posts a sentinel" not in description
    assert "coordinates troop feeding" not in description
    assert "no sentinel role" in record["provenance"]["behavior"]["note"].lower()
    assert record["provenance"]["behavior"]["derived"] is True
    alarm_source = next(s for s in record["sources"] if s["id"] == "vervet-alarm-context")
    assert alarm_source["license"] == "CC-BY-4.0"
    assert "intergroup aggression" in record["provenance"]["behavior"]["note"]
