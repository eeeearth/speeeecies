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


def test_black_kite_behavior_matches_daylight_call_and_diet_tags():
    species, program = behavior_for("milvus-migrans")
    assert program["id"] == species["behavior"]["program"]
    assert program["id"] == "fsm-black-kite-forager-v1"
    states = program["states"]
    assert states["call"]["action"]["do"] == "sing"
    call = states["call"]["action"]["call"]
    assert program["params"][call[2:-1]] == species["vocalizations"][0]["call_id"]
    tags = {n["tag"] for n in walk(program) if isinstance(n.get("tag"), str)}
    diet = species["traits"]["diet"]
    assert diet["carrion"] > 0 and "carrion" in tags
    assert diet["vertebrate"] > 0 and "small_vertebrate" in tags
    assert "fish" in diet and "fish" not in tags
    assert "fish" in species["provenance"]["behavior"]["note"].lower()
    for state in ("patrol", "hunt", "scavenge", "call"):
        assert any(
            t.get("to") == state and has_predicate(t.get("when", {}), "is_day", True)
            for t in program["transitions"]
        ), f"{state} lacks a daytime gate"
    assert any(t.get("to") == "rest" and has_predicate(t.get("when", {}), "is_day", False) for t in program["transitions"])


def test_nairobi_weak_curves_are_disclosed_unusable_and_kite_is_gbif_only():
    for slug in ("chlorocebus-pygerythrus", "sclerophrys-gutturalis"):
        species = load_json(f"species/{slug}/species.json")
        curve = next(r for r in species["activity"]["regions"] if r["region"] == "KE-30")
        assert curve["query"]["gbif"]["usable"] is False
        assert curve["query"]["gbif"]["total"] < curve["query"]["min_obs"]
        assert "low-count fallback" in curve["query"]["fallback_note"].lower()
    kite = load_json("species/milvus-migrans/species.json")
    curve = next(r for r in kite["activity"]["regions"] if r["region"] == "KE-30")
    assert curve["method"] == "gbif_share"
    assert curve["query"]["gbif"]["tier"] == "A"
    source = next(s for s in kite["sources"] if s["id"] == "gbif-activity-ke-30")
    assert source["license"] == "CC-BY-4.0"
    assert curve["query"]["used"] == ["gbif"]
    assert curve["sources"] == ["gbif-activity-ke-30"]
    assert all(s["id"] != "inat-activity-ke-30" for s in kite["sources"])


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
