import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_species(slug):
    return json.loads((ROOT / "species" / slug / "species.json").read_text())


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def test_annas_hummingbird_uses_flight_feeding_without_nest_gate():
    species = load_species("calypte-anna")
    assert species["traits"]["diet"] == {"nectar": 0.9, "invertebrate": 0.1}
    assert species["traits"]["locomotion_modes"] == ["Fly"]
    assert "fly" in species["look"]["poses"]
    program = json.loads((ROOT / "species/calypte-anna/behavior.json").read_text())
    assert species["behavior"]["program"] == program["id"]
    nodes = list(walk(program["root"]))
    feeding = [n for n in nodes if n.get("do") == "eat_nearest"]
    assert feeding and all(n.get("gait") == "fly" for n in feeding)
    assert not any("month_in" in n for n in nodes)


def test_pacific_chorus_frog_call_gate_resolves_to_local_peak_survey_months():
    species = load_species("pseudacris-regilla")
    params = species["behavior"]["params"]
    program = json.loads((ROOT / "behaviors/fsm-anuran-nocturnal-v1.json").read_text())
    call_gate = next(
        condition["month_in"]
        for transition in program["transitions"]
        if transition["to"] == "call"
        for condition in transition["when"]["all"]
        if "month_in" in condition
    )
    resolved = [params[value[2:-1]] if isinstance(value, str) and value.startswith("${") else value for value in call_gate]
    assert resolved == [3, 5]
    assert not species["seasonal"].get("triggers")
    assert species["seasonal"]["strategy"] == "ActiveYearRound"


def test_douglas_squirrel_eltontraits_diet_and_behavior_scope_are_explicit():
    species = load_species("tamiasciurus-douglasii")
    assert species["traits"]["diet"] == {
        "vertebrate": 0.3,
        "fruit": 0.2,
        "nectar": 0.1,
        "seed": 0.2,
        "browse": 0.2,
    }
    note = species["provenance"]["behavior"]["note"].lower()
    assert "tree climbing" in note and "cone caching" in note
