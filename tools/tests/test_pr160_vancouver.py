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


def test_pacific_chorus_frog_call_gate_includes_march_through_may_only():
    species = load_species("pseudacris-regilla")
    program = json.loads((ROOT / "species/pseudacris-regilla/behavior.json").read_text())
    call_gate = next(
        condition["month_in"]
        for transition in program["transitions"]
        if transition["to"] == "call"
        for condition in transition["when"]["all"]
        if "month_in" in condition
    )

    assert call_gate == [3, 4, 5]
    assert {month: month in call_gate for month in (2, 3, 4, 5, 6)} == {
        2: False,
        3: True,
        4: True,
        5: True,
        6: False,
    }
    assert species["behavior"]["program"] == program["id"]
    shared = json.loads((ROOT / "behaviors/fsm-anuran-nocturnal-v1.json").read_text())
    shared_gate = next(
        condition["month_in"]
        for transition in shared["transitions"]
        if transition["to"] == "call"
        for condition in transition["when"]["all"]
        if "month_in" in condition
    )
    assert shared_gate == ["${call_m1}", "${call_m2}"]
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
