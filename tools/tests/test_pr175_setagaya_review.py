"""Regression checks for the Setagaya locale review corrections."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def behavior_for(slug: str) -> tuple[dict, dict]:
    species = load_json(f"species/{slug}/species.json")
    program = load_json(f"species/{slug}/behavior.json")
    return species, program


def test_eltontraits_diet_categories_are_mapped_to_the_matching_resources():
    expected = {
        "spodiopsar-cineraceus": {
            "invertebrate": 0.6,
            "vertebrate": 0.1,
            "fruit": 0.3,
        },
        "corvus-macrorhynchos": {
            "invertebrate": 0.2,
            "vertebrate": 0.2,
            "carrion": 0.3,
            "fruit": 0.2,
            "seed": 0.1,
        },
    }
    for slug, diet in expected.items():
        species = load_json(f"species/{slug}/species.json")
        assert species["traits"]["diet"] == diet
        assert "eltontraits" in species["provenance"]["traits.diet"]["sources"]
    dataset = next(
        source
        for source in load_json("species/spodiopsar-cineraceus/species.json")["sources"]
        if source["id"] == "eltontraits"
    )
    assert dataset["license"] == "CC0-1.0"


def test_seasonally_ungrounded_nesting_actions_are_absent_from_local_programs():
    for slug in (
        "parus-minor",
        "corvus-macrorhynchos",
        "spodiopsar-cineraceus",
        "streptopelia-orientalis",
    ):
        species, program = behavior_for(slug)
        assert species["behavior"]["program"] == program["id"]
        assert program["id"].startswith("bt-setagaya-")
        assert all(node.get("act", {}).get("do") != "build_nest" for node in walk(program))
        assert all("month_in" not in node.get("cond", {}) for node in walk(program))


def test_ground_foragers_walk_and_white_eye_feeds_from_a_perch():
    for slug in ("corvus-macrorhynchos", "spodiopsar-cineraceus", "streptopelia-orientalis"):
        _, program = behavior_for(slug)
        food_actions = [
            node["act"] for node in walk(program)
            if node.get("act", {}).get("do") == "eat_nearest"
        ]
        assert food_actions and all(action.get("gait") == "walk" for action in food_actions)

    _, white_eye = behavior_for("zosterops-japonicus")
    feed_branches = [
        node["sequence"] for node in walk(white_eye)
        if isinstance(node.get("sequence"), list)
        and any(child.get("act", {}).get("do") == "eat_nearest" for child in node["sequence"])
    ]
    assert feed_branches
    assert all(
        any(child.get("act", {}).get("do") == "perch_nearest" for child in branch[:feed])
        for branch in feed_branches
        for feed, child in enumerate(branch)
        if child.get("act", {}).get("do") == "eat_nearest"
    )


def test_unmeasured_starling_span_is_omitted_and_required_lifespan_is_low_confidence():
    traits = load_json("species/spodiopsar-cineraceus/species.json")["traits"]
    assert "wingspan_m" not in traits
    assert traits["lifespan_y"] == 4
    provenance = load_json("species/spodiopsar-cineraceus/species.json")["provenance"]["traits.lifespan_y"]
    assert provenance["confidence"] == "Low" and provenance["derived"] is True
    assert "not a measured" in provenance["note"]


def test_raccoon_dog_diet_discloses_the_congener_proxy():
    species = load_json("species/nyctereutes-viverrinus/species.json")
    provenance = species["provenance"]["traits.diet"]
    assert provenance["confidence"] == "Low"
    assert provenance["derived"] is True
    note = provenance["note"].lower()
    assert "nyctereutes procyonoides" in note
    assert "proxy" in note and "not a measured" in note


def test_jp13_curves_preserve_other_regions_and_low_count_fox_is_unusable():
    expected = {
        "hypsipetes-amaurotis": ["KR-11"],
        "streptopelia-orientalis": ["KR-11"],
        "corvus-macrorhynchos": ["KR-11"],
        "parus-minor": ["KR-11"],
        "passer-montanus": ["CN", "JP", "KR", "TW", "KR-11"],
        "columba-livia": ["GB", "GB-ENG", "US-LA", "US-PA", "US-NC", "US-IN", "US-AR", "US-NJ", "US-DE", "US-MO", "US-GA", "CA-ON", "IN-KA", "IE"],
        "troglodytes-troglodytes": ["GB", "GB-ENG", "IE", "DE-BE"],
        "vulpes-vulpes": ["GB", "DE", "GB-ENG", "US-LA", "US-NC", "US-MA", "US-NJ", "US-DE", "CA-ON", "IE", "DE-BE"],
    }
    for slug, existing in expected.items():
        species = load_json(f"species/{slug}/species.json")
        regions = [entry["region"] for entry in species["activity"]["regions"]]
        assert [region for region in regions if region != "JP-13"] == existing
        assert regions.count("JP-13") == 1

    fox = load_json("species/vulpes-vulpes/species.json")
    curve = next(row for row in fox["activity"]["regions"] if row["region"] == "JP-13")
    assert curve["query"]["inat"]["total"] < curve["query"]["min_obs"]
    assert curve["query"]["gbif"]["total"] < curve["query"]["min_obs"]
    assert curve["query"]["gbif"]["usable"] is False
    assert curve["query"]["inat"]["usable"] is False
    note = fox["provenance"]["activity.JP-13"]["note"].lower()
    assert "exploratory" in note and "below min_obs=300" in note
    inat_source = next(source for source in fox["sources"] if source["id"] == "inat-activity-jp-13")
    assert inat_source["license"] == "CC-BY-NC-SA-4.0"


def test_chord_scaled_or_judged_wingspans_are_omitted():
    for slug in ("hypsipetes-amaurotis", "streptopelia-orientalis", "corvus-macrorhynchos", "parus-minor", "spodiopsar-cineraceus"):
        species = load_json(f"species/{slug}/species.json")
        assert "wingspan_m" not in species["traits"]
        assert "traits.wingspan_m" not in species["provenance"]
