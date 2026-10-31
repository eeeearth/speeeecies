"""Regression checks for the São Paulo locale evidence corrections."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def record(slug):
    return json.loads((ROOT / "species" / slug / "species.json").read_text())

def test_plain_parakeet_is_not_misidentified_or_given_invented_nest_claims():
    bird = record("brotogeris-tirica")
    assert bird["id"] == "Brotogeris tirica"
    assert bird["taxonomy"]["genus"] == "Brotogeris"
    assert bird["traits"]["diet"] == {"fruit": 0.3, "seed": 0.3, "browse": 0.3, "invertebrate": 0.1}
    assert "wingspan_m" not in bird["traits"]
    assert bird["traits"]["lifespan_y"] == 12.0
    assert bird["provenance"]["traits.lifespan_y"]["derived"] is True
    assert not bird["provenance"]["traits.lifespan_y"]["sources"]
    assert bird["look"]["part_colors"]["head"] == "body"
    assert bird["look"]["part_colors"]["beak"] == "accent"
    assert all(part["name"] != "forehead_band" for part in bird["look"]["extra_parts"])
    text = json.dumps({"habitat": bird["habitat"], "seasonal": bird["seasonal"], "provenance": bird["provenance"]}).lower()
    assert "11 eggs" not in text
    assert "no communal or termite-nest claim is made" in text
    assert all(phase["name"] != "breeding" for phase in bird["seasonal"]["phases"])


def test_ornate_toad_diet_behavior_and_breeding_months_are_consistent():
    toad = record("rhinella-ornata")
    assert toad["traits"]["diet"] == {"invertebrate": 0.93, "browse": 0.07}
    assert toad["behavior"]["params"]["food_tag"] == "invertebrate"
    resources = {r["tag"]: r for r in toad["habitat"]["resources"]}
    assert resources["invertebrate"]["weight"] == 0.93
    assert resources["browse"]["weight"] == 0.07
    assert resources["pond"]["months"] == [8, 9, 10, 11]
    breeding = next(p for p in toad["seasonal"]["phases"] if p["name"] == "breeding")
    assert (breeding["start"], breeding["end"], breeding["region"]) == ("08-01", "11-30", "BR-SP")
    assert toad["vocalizations"][0]["season_months"] == [8, 9, 10, 11]
    season_source = next(s for s in toad["sources"] if s["id"] == "rhinella-seasonality-sp")
    assert season_source["license"] == "CC-BY-NC-4.0"
    assert toad["provenance"]["traits.lifespan_y"]["derived"] is True
    assert "model parameter" in toad["provenance"]["traits.lifespan_y"]["note"]
    source = next(s for s in toad["sources"] if s["id"] == "rhinella-juvenile-diet")
    assert source["license"] == "CC-BY-4.0"
    assert source["url"] == "https://doi.org/10.1590/1519-6984.236597"


def test_house_gecko_brazil_range_is_introduced():
    gecko = record("hemidactylus-mabouia")
    assert "BR" not in gecko["range"]["native"]
    assert "BR" in gecko["range"]["introduced"]
    assert "BR" in gecko["range"]["invasive_in"]
    source = next(s for s in gecko["sources"] if s["id"] == "mabouia-biogeography")
    assert source["license"] == "CC-BY-4.0"
    reproduction = next(s for s in gecko["sources"] if s["id"] == "mabouia-reproduction-sp")
    assert reproduction["url"] == "https://www.scielo.br/j/isz/a/HSrqsKVMKNfCqxrjwrYgSsS/?lang=en"
    assert "10.1590/S0073-47212008000200006" in reproduction["attribution"]
    assert reproduction["license"] == "CC-BY-NC-4.0"


def test_six_local_curves_use_verified_gbif_tier_a_only():
    for slug in ("callithrix-penicillata", "columbina-talpacoti", "didelphis-aurita", "furnarius-rufus", "hemidactylus-mabouia", "rhinella-ornata"):
        species = record(slug)
        region = next(r for r in species["activity"]["regions"] if r["region"] == "BR-SP")
        assert region["sources"] == ["gbif-activity-br-sp"]
        assert region["query"]["gbif"]["tier"] == "A"
        assert region["query"]["gbif"]["usable"] is True
        assert "CC_BY_NC" not in region["query"]["gbif"]["url"]
        assert not any(s["id"] == "inat-activity-br-sp" for s in species["sources"])


def test_remaining_inat_query_keeps_nc_sharealike_license():
    species = record("callithrix-jacchus")
    source = next(s for s in species["sources"] if s["id"] == "inat-activity-br-sp")
    assert "cc-by-nc-sa" in source["url"]
    assert source["license"] == "CC-BY-NC-SA-4.0"


def test_unsupported_breeding_calendars_are_omitted():
    for slug in ("pitangus-sulphuratus", "thraupis-sayaca", "columbina-talpacoti", "didelphis-aurita"):
        species = record(slug)
        assert len(species["seasonal"]["phases"]) == 1
        assert species["seasonal"]["phases"][0]["start"] == "01-01"
        assert species["seasonal"]["phases"][0]["end"] == "12-31"
        assert "not a claim about breeding months" in species["seasonal"]["phases"][0]["note"] or "not a claim about seasonal birth months" in species["seasonal"]["phases"][0]["note"]
        assert species["provenance"]["seasonal.phases"]["sources"] == []
        assert "neutral schema-required placeholder" in species["provenance"]["seasonal.phases"]["note"]


def test_ground_gaits_use_species_local_programs_without_shared_changes():
    parakeet = record("brotogeris-tirica")
    dove = record("columbina-talpacoti")
    hornero = record("furnarius-rufus")
    local_dir = ROOT / "species"
    assert parakeet["behavior"]["program"] == "bt-brotogeris-season-neutral-v1"
    assert dove["behavior"]["program"] == "bt-columbina-season-neutral-v1"
    assert hornero["behavior"]["program"] == "bt-furnarius-ground-forager-v1"
    assert "hop" not in hornero["look"]["poses"]
    assert "Walk" in hornero["traits"]["locomotion_modes"]
    for slug, gait in (("brotogeris-tirica", "climb"), ("columbina-talpacoti", "walk"), ("furnarius-rufus", "walk")):
        local = json.loads((local_dir / slug / "behavior.json").read_text())
        gaits = [node["act"].get("gait") for node in _walk_nodes(local.get("root", {})) if "act" in node]
        assert gait in gaits
        assert "hop" not in gaits

def _walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_nodes(value)


def _nodes(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from _nodes(value)


def _resolved_month_gates(program, overrides):
    params = dict(program.get("params", {}))
    params.update(overrides)
    gates = []
    for node in _nodes(program):
        if "month_in" not in node:
            continue
        resolved = []
        for month in node["month_in"]:
            if isinstance(month, str) and month.startswith("${") and month.endswith("}"):
                resolved.append(params[month[2:-1]])
            else:
                resolved.append(month)
        gates.append(resolved)
    return gates


def test_rhinella_executed_call_gate_covers_supported_months_only():
    species = record("rhinella-ornata")
    program = json.loads((ROOT / "species/rhinella-ornata/behavior.json").read_text())
    gates = _resolved_month_gates(program, species["behavior"]["params"])
    assert gates == [[8, 9, 10, 11]]
    assert gates[0] == species["vocalizations"][0]["season_months"]
    assert {month: month in gates[0] for month in (7, 8, 9, 10, 11, 12)} == {
        7: False, 8: True, 9: True, 10: True, 11: True, 12: False
    }


def test_birds_with_no_supported_breeding_calendar_have_no_hidden_nest_gate():
    for slug in ("brotogeris-tirica", "columbina-talpacoti", "furnarius-rufus", "pitangus-sulphuratus", "thraupis-sayaca"):
        species = record(slug)
        program = json.loads((ROOT / "species" / slug / "behavior.json").read_text())
        assert species["behavior"]["program"] == program["id"]
        assert _resolved_month_gates(program, species["behavior"]["params"]) == []
        serialized = json.dumps(program)
        assert '"do": "build_nest"' not in serialized
        assert "nest_m1" not in program.get("params", {})
        assert "nest_m2" not in program.get("params", {})


def test_toad_collection_note_does_not_claim_the_whole_breeding_window():
    species = record("rhinella-ornata")
    phase = next(p for p in species["seasonal"]["phases"] if p["name"] == "breeding")
    assert "overlaps only the early part" in phase["note"]
    assert "does not establish the full window" in phase["note"]
