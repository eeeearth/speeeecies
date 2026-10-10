"""Regression checks for Nairobi locale review corrections."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def behavior_for(slug: str) -> tuple[dict, dict]:
    species = load_json(f"species/{slug}/species.json")
    local_path = ROOT / "species" / slug / "behavior.json"
    if local_path.exists():
        program = json.loads(local_path.read_text(encoding="utf-8"))
    else:
        program = load_json(f"behaviors/{species['behavior']['program']}.json")
    return species, program


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def has_predicate(tree, key, value):
    return any(isinstance(node, dict) and node.get(key) == value for node in walk(tree))


def test_nairobi_songbirds_have_no_unsupported_nesting_month_gates_or_phases():
    for slug in (
        "turdus-abyssinicus", "ploceus-baglafecht", "cinnyris-venustus",
        "pycnonotus-barbatus", "motacilla-aguimp", "corvus-albus",
    ):
        species, program = behavior_for(slug)
        behavior_note = species["provenance"]["behavior"]["note"].lower()
        assert "shared perching-songbird" not in behavior_note
        assert "species-local" in behavior_note
        assert "wingspan_m" not in species["traits"]
        assert "traits.wingspan_m" not in species["provenance"]
        assert species["provenance"]["traits.lifespan_y"]["derived"] is True
        assert "not presented as a measured or typical lifespan" in species["provenance"]["traits.lifespan_y"]["note"]
        resolved_months = []
        for node in walk(program.get("root", program.get("states", {}))):
            condition = node.get("cond", node.get("when", {}))
            if "month_in" in condition:
                for month in condition["month_in"]:
                    if isinstance(month, str) and month.startswith("${"):
                        month = species["behavior"]["params"][month[2:-1]]
                    resolved_months.append(month)
            assert node.get("act", {}).get("do") != "build_nest"
            assert node.get("action", {}).get("do") != "build_nest"
        assert resolved_months == [], f"{slug} has hidden months {resolved_months}"
        assert all(p["name"] != "breeding" for p in species["seasonal"]["phases"])


def test_sunbird_never_uses_hop_to_feed_on_nectar():
    species, program = behavior_for("cinnyris-venustus")
    assert species["traits"]["diet"].get("nectar", 0) > 0
    feeding_branch = next(
        n for n in walk(program["root"])
        if isinstance(n.get("sequence"), list)
        and any(a.get("act", {}).get("do") == "eat_nearest" for a in n["sequence"])
    )
    actions = [a.get("act", {}) for a in feeding_branch["sequence"] if "act" in a]
    feed_index = next(i for i, action in enumerate(actions) if action.get("do") == "eat_nearest")
    assert actions[feed_index - 1] == {"do": "perch_nearest", "tag": "perch"}
    assert "gait" not in actions[feed_index]
    diet_provenance = species["provenance"]["traits.diet"]
    assert diet_provenance["confidence"] == "Low"
    assert diet_provenance["derived"] is True
    assert "70/30" in diet_provenance["note"] and "modeled" in diet_provenance["note"].lower()


def test_crow_and_wagtail_food_search_uses_walking():
    for slug in ("motacilla-aguimp", "corvus-albus"):
        _, program = behavior_for(slug)
        food_actions = [
            n["act"] for n in walk(program)
            if isinstance(n, dict) and n.get("act", {}).get("do") == "eat_nearest"
        ]
        assert food_actions and all(a.get("gait") == "walk" for a in food_actions)


def test_unresolved_black_kite_taxon_is_omitted_from_nairobi():
    locale = load_json("locales/nairobi-ke/locale.json")
    kite = load_json("species/milvus-migrans/species.json")
    assert len(locale["species"]) == 11
    assert "milvus-migrans" not in locale["species"]
    assert all(r["region"] != "KE-30" for r in kite["activity"]["regions"])
    assert kite["behavior"]["program"] == "fsm-seabird-predator-v1"
    assert not (ROOT / "species/milvus-migrans/behavior.json").exists()


def test_nairobi_weak_curves_are_disclosed_unusable():
    for slug in ("chlorocebus-pygerythrus", "sclerophrys-gutturalis"):
        species = load_json(f"species/{slug}/species.json")
        curve = next(r for r in species["activity"]["regions"] if r["region"] == "KE-30")
        assert curve["query"]["gbif"]["usable"] is False
        assert curve["query"]["gbif"]["total"] < curve["query"]["min_obs"]
        assert "low-count fallback" in curve["query"]["fallback_note"].lower()


def test_ke30_additions_preserve_existing_regional_curves():
    expected = {
        "columba-livia": ["GB", "GB-ENG", "US-LA", "US-PA", "US-NC", "US-IN", "US-AR", "US-NJ", "US-DE", "US-MO", "US-GA", "CA-ON", "IN-KA", "IE"],
        "passer-domesticus": ["GB", "GB-ENG", "US-LA", "US-PA", "US-NC", "US-IN", "US-AR", "US-NJ", "US-VT", "US-DE", "US-OK", "US-MO", "CL-RM", "FR-IDF", "US-ND", "CA-ON", "IN-KA", "MX-CMX", "ES-MD", "IE", "DE-BE"],
    }
    for slug, existing_regions in expected.items():
        species = load_json(f"species/{slug}/species.json")
        regions = species["activity"]["regions"]
        assert [r["region"] for r in regions if r["region"] != "KE-30"] == existing_regions
        assert sum(r["region"] == "KE-30" for r in regions) == 1
