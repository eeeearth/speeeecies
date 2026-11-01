"""Regression checks for adding Australia's national lorikeet curve."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPECIES_PATH = REPO_ROOT / "species" / "trichoglossus-moluccanus" / "species.json"
MAIN_RECORD_SHA256 = "a3dff44bb7ed327609fc9d0cf8363afe43738a1ad36182b9bb7df5110b234cb2"
MAIN_NSW_REGION_SHA256 = "fec53bf7fb52855929212cf873060d7c2bc8ce630f32339d964981b3d958132c"
ADDED_SOURCE_IDS = {"inat-activity-au", "gbif-activity-au", "gbif-usage", "itis"}


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_species() -> dict:
    return json.loads(SPECIES_PATH.read_text(encoding="utf-8"))


def test_national_curve_addition_preserves_main_record_and_au_nsw() -> None:
    species = load_species()
    nsw = next((region for region in species["activity"]["regions"] if region["region"] == "AU-NSW"), None)
    assert nsw is not None
    assert canonical_hash(nsw) == MAIN_NSW_REGION_SHA256

    preserved = copy.deepcopy(species)
    preserved["activity"]["regions"] = [r for r in preserved["activity"]["regions"] if r["region"] != "AU"]
    preserved["sources"] = [s for s in preserved["sources"] if s["id"] not in ADDED_SOURCE_IDS]
    wikidata_source = next(s for s in preserved["sources"] if s["id"] == "wikidata")
    wikidata_source["url"] = "https://www.wikidata.org/wiki/Q1220037"
    wikidata_source["title"] = "Wikidata: Trichoglossus moluccanus (Q1220037)"
    wikidata_source["accessed"] = "2026-10-01"
    preserved["external"]["wikidata"] = "Q1220037"
    preserved["external"].pop("itis_tsn", None)
    preserved["external"].pop("ncbi_taxon_id", None)
    preserved["taxonomy"]["accepted_id"] = "Trichoglossus haematodus"
    preserved["provenance"]["taxonomy"] = {
        "sources": ["gbif-backbone"],
        "confidence": "High",
        "note": "GBIF files T. moluccanus as a synonym of T. haematodus; accepted usage key 6170530.",
    }
    preserved["provenance"]["external"] = {
        "sources": ["gbif-backbone", "wikidata"],
        "confidence": "High",
    }
    preserved["provenance"].pop("activity.AU", None)
    assert canonical_hash(preserved) == MAIN_RECORD_SHA256


def test_national_au_curve_has_twelve_months_and_licensed_adequate_sources() -> None:
    species = load_species()
    region = next((r for r in species["activity"]["regions"] if r["region"] == "AU"), None)
    assert region is not None
    assert len(region["monthly"]) == 12
    assert all(0.0 <= month <= 1.0 for month in region["monthly"])
    assert max(region["monthly"]) == 1.0
    assert region["method"] == "mean(inat_share, gbif_share)"

    query = region["query"]
    assert query["min_obs"] == 300
    assert query["inat"]["tier"] == query["gbif"]["tier"] == "A"
    assert query["inat"]["usable"] and query["gbif"]["usable"]
    assert query["inat"]["total"] >= query["min_obs"]
    assert query["gbif"]["total"] >= query["min_obs"]
    assert region["observations"] == query["inat"]["total"] + query["gbif"]["total"]
    assert query["inat"]["total"] == 5797
    assert query["gbif"]["total"] == 1214092

    sources = {source["id"]: source for source in species["sources"]}
    for source_id in region["sources"]:
        source = sources[source_id]
        assert source["license"] == "CC-BY-4.0"
        assert source.get("attribution")
    assert "license=cc0,cc-by" in sources["inat-activity-au"]["url"]
    assert "license=CC0_1_0&license=CC_BY_4_0" in sources["gbif-activity-au"]["url"]


def test_existing_lorikeet_behavior_and_poses_remain_compatible() -> None:
    species = load_species()
    assert species["behavior"]["program"] == "bt-perching-songbird-v1"
    assert species["behavior"]["params"]["food_tag"] in {
        resource["tag"] for resource in species["habitat"]["resources"]
    }
    poses = species["look"]["poses"]
    assert {"idle", "walk", "fly", "perched"} <= set(poses)
    assert {"Walk", "Fly"} <= set(species["traits"]["locomotion_modes"])

    body_plans = json.loads((REPO_ROOT / "schema" / "v0.1" / "body-plans.json").read_text(encoding="utf-8"))
    behavior = json.loads((REPO_ROOT / "behaviors" / "bt-perching-songbird-v1.json").read_text(encoding="utf-8"))
    plan = body_plans["plans"][species["look"]["body_plan"]]
    assert all(body_plans["locomotion_to_pose"][mode] in poses for mode in species["traits"]["locomotion_modes"])

    def actions(node):
        if isinstance(node, dict):
            if isinstance(node.get("act"), dict):
                yield node["act"]
            for value in node.values():
                yield from actions(value)
        elif isinstance(node, list):
            for value in node:
                yield from actions(value)

    feeding = next(action for action in actions(behavior["root"]) if action.get("do") == "eat_nearest")
    food_tag = species["behavior"]["params"][feeding["tag"][2:-1]]
    assert food_tag in {resource["tag"] for resource in species["habitat"]["resources"]}
    assert feeding["gait"] in plan["poses"]


def test_taxonomy_and_external_ids_use_the_verified_taxon_records() -> None:
    species = load_species()
    assert species["taxonomy"]["accepted_id"] == "Trichoglossus haematodus moluccanus"
    assert species["external"]["wikidata"] == "Q1809222"
    assert species["external"]["itis_tsn"] == 714103
    assert species["external"]["ncbi_taxon_id"] == 1549204

    sources = {source["id"]: source for source in species["sources"]}
    assert sources["gbif-usage"]["url"] == "https://api.gbif.org/v1/species/2479694"
    assert sources["gbif-usage"]["license"] == "CC-BY-4.0"
    assert sources["itis"]["license"] == "public-domain"
    assert species["provenance"]["taxonomy"]["sources"] == ["gbif-backbone", "gbif-usage", "itis", "wikipedia"]
