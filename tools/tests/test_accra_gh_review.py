"""Regression checks for the reviewed Accra locale and its source-backed activity."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NEW_SLUGS = {
    "ploceus-cucullatus", "corvus-albus", "centropus-senegalensis",
    "lophoceros-nasutus", "corvinella-corvina", "crinifer-piscator",
    "bubulcus-ibis",
}

EXPECTED_GH_COUNTS = {
    "ploceus-cucullatus": 670,
    "corvus-albus": 2464,
    "spilopelia-senegalensis": 2348,
    "centropus-senegalensis": 1462,
    "lophoceros-nasutus": 1635,
    "corvinella-corvina": 1220,
    "crinifer-piscator": 2001,
    "bubulcus-ibis": 1791,
    "columba-livia": 787,
    "psittacula-krameri": 486,
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_gaits(node):
    if isinstance(node, dict):
        if "gait" in node:
            yield node["gait"]
        for value in node.values():
            yield from find_gaits(value)
    elif isinstance(node, list):
        for value in node:
            yield from find_gaits(value)


def find_month_gates(node):
    if isinstance(node, dict):
        if "month_in" in node:
            yield node["month_in"]
        for value in node.values():
            yield from find_month_gates(value)
    elif isinstance(node, list):
        for value in node:
            yield from find_month_gates(value)


def test_accra_locale_contains_only_the_ten_supported_records():
    locale = load(ROOT / "locales/accra-gh/locale.json")
    assert len(locale["species"]) == 10
    assert set(locale["species"]) == set(EXPECTED_GH_COUNTS)
    assert "eidolon-helvum" not in locale["species"]
    assert "sclerophrys-regularis" not in locale["species"]


def test_accra_and_nairobi_activity_rows_use_verified_permissive_gbif_tiers():
    for slug, expected_count in EXPECTED_GH_COUNTS.items():
        record = load(ROOT / "species" / slug / "species.json")
        row = next(r for r in record["activity"]["regions"] if r["region"] == "GH-AA")
        gbif = row["query"]["gbif"]
        source = next(s for s in record["sources"] if s["id"] == "gbif-activity-gh-aa")
        assert row["method"] == "gbif_share"
        assert row["observations"] == expected_count >= row["query"]["min_obs"] == 300
        assert gbif["tier"] == "A" and gbif["usable"] is True
        assert gbif["area"] == ["gadmGid", "GHA7_2"]
        assert "license=CC0_1_0&license=CC_BY_4_0" in gbif["url"]
        assert source["license"] == "CC-BY-4.0"

    crow = load(ROOT / "species/corvus-albus/species.json")
    nairobi = next(r for r in crow["activity"]["regions"] if r["region"] == "KE-30")
    gbif = nairobi["query"]["gbif"]
    source = next(s for s in crow["sources"] if s["id"] == "gbif-activity-ke-30")
    assert nairobi["observations"] == 9384 >= 300
    assert gbif["tier"] == "A" and gbif["area"] == ["gadmGid", "KEN.30_1"]
    assert source["license"] == "CC-BY-4.0"
    assert "license=CC0_1_0&license=CC_BY_4_0" in source["url"]


def test_new_bird_programs_do_not_run_unsupported_month_gates_or_undeclared_gaits():
    for slug in NEW_SLUGS:
        record = load(ROOT / "species" / slug / "species.json")
        assert record["seasonal"]["phases"] == []
        program_path = ROOT / "species" / slug / "behavior.json"
        if not program_path.exists():
            continue
        program = load(program_path)
        assert list(find_month_gates(program)) == []
        assert "build_nest" not in json.dumps(program)
        modes = {mode.lower() for mode in record["traits"]["locomotion_modes"]}
        params = dict(program.get("params", {}))
        params.update(record.get("behavior", {}).get("params", {}))
        gaits = {
            params[gait[2:-1]] if gait.startswith("${") and gait.endswith("}") else gait
            for gait in find_gaits(program)
        }
        assert gaits <= modes

    egret = load(ROOT / "species/bubulcus-ibis/behavior.json")
    assert "gallop" not in json.dumps(egret)
    assert "sun_elevation_between_deg" not in json.dumps(egret)


def test_corrected_eltontraits_diets_match_primary_rows_and_resources():
    expected = {
        "ploceus-cucullatus": {"invertebrate": 0.3, "seed": 0.5, "fruit": 0.1, "nectar": 0.1},
        "corvus-albus": {"invertebrate": 0.4, "vertebrate": 0.4, "fish": 0.1, "carrion": 0.1},
        "centropus-senegalensis": {"invertebrate": 0.4, "vertebrate": 0.6},
        "corvinella-corvina": {"invertebrate": 0.8, "vertebrate": 0.2},
        "crinifer-piscator": {"fruit": 1.0},
        "bubulcus-ibis": {"invertebrate": 0.6, "vertebrate": 0.2, "fish": 0.1, "carrion": 0.1},
    }
    for slug, diet in expected.items():
        record = load(ROOT / "species" / slug / "species.json")
        assert record["traits"]["diet"] == diet
        assert record["provenance"]["traits.diet"]["sources"] == ["eltontraits"]
    plantain = load(ROOT / "species/crinifer-piscator/species.json")
    fruit_resource = next(r for r in plantain["habitat"]["resources"] if r["tag"] == "fruit")
    assert fruit_resource["weight"] == 1.0
    hornbill = load(ROOT / "species/lophoceros-nasutus/species.json")
    assert hornbill["provenance"]["traits.diet"]["confidence"] == "Low"
    assert hornbill["provenance"]["traits.diet"]["derived"] is True
    assert "not measured" in hornbill["provenance"]["traits.diet"]["note"]


def test_unsupported_wingspan_heuristics_are_omitted():
    for slug in {"ploceus-cucullatus", "centropus-senegalensis", "lophoceros-nasutus", "corvinella-corvina", "crinifer-piscator"}:
        record = load(ROOT / "species" / slug / "species.json")
        assert "wingspan_m" not in record["traits"]
    for slug in {"corvus-albus", "bubulcus-ibis"}:
        record = load(ROOT / "species" / slug / "species.json")
        assert record["traits"]["wingspan_m"] > 0
        assert record["provenance"]["traits.wingspan_m"]["derived"] is True


def test_gbif_taxon_authorship_is_current_for_new_records():
    expected = {
        "ploceus-cucullatus": "(Statius Muller, 1776)",
        "corvus-albus": "Statius Muller, 1776",
        "centropus-senegalensis": "(Linnaeus, 1766)",
        "lophoceros-nasutus": "(Linnaeus, 1766)",
        "corvinella-corvina": "(Shaw, 1809)",
        "crinifer-piscator": "(Boddaert, 1783)",
        "bubulcus-ibis": "(Linnaeus, 1758)",
    }
    for slug, authority in expected.items():
        record = load(ROOT / "species" / slug / "species.json")
        assert record["taxonomy"]["authority"] == authority
        assert any(source["id"] == "gbif-backbone" for source in record["sources"])


def test_unknown_seasonality_can_remain_empty_instead_of_inventing_months():
    schema = load(ROOT / "schema/v0.1/species.schema.json")
    assert "minItems" not in schema["$defs"]["Seasonal"]["properties"]["phases"]
    for slug in NEW_SLUGS:
        record = load(ROOT / "species" / slug / "species.json")
        assert record["seasonal"]["phases"] == []
        assert record["provenance"]["seasonal.phases"]["derived"] is True
        assert "no locally supported" in record["provenance"]["seasonal.phases"]["note"].lower()
