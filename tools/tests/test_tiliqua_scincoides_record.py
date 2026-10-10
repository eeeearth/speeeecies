"""Data contracts for the blue-tongue repair; independent of Git history."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "species" / "tiliqua-scincoides" / "species.json"


def load_record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_national_curve_is_additive_and_uses_tier_a_sources():
    record = load_record()
    regions = {entry["region"]: entry for entry in record["activity"]["regions"]}
    assert set(regions) == {"AU-NSW", "AU"}
    assert regions["AU-NSW"]["monthly"] == [
        0.91, 0.69, 0.52, 0.42, 0.24, 0.14, 0.21, 0.42, 0.95, 1.0, 0.7, 0.94
    ]

    national = regions["AU"]
    assert len(national["monthly"]) == 12
    assert max(national["monthly"]) == 1.0
    assert national["method"] == "mean(inat_raw, gbif_raw)"
    assert national["observations"] == sum(
        national["query"][provider]["total"] for provider in national["query"]["used"]
    )
    assert national["query"]["min_obs"] == 300
    assert national["sources"] == ["inat-activity-au", "gbif-activity-au"]

    sources = {source["id"]: source for source in record["sources"]}
    expected_licenses = {
        "inat": {"cc0", "cc-by"},
        "gbif": {"CC0_1_0", "CC_BY_4_0"},
    }
    for provider, allowed in expected_licenses.items():
        query = national["query"][provider]
        source = sources[f"{provider}-activity-au"]
        assert query["tier"] == "A"
        assert query["usable"] and query["total"] >= national["query"]["min_obs"]
        assert query["url"] == source["url"]
        license_params = parse_qs(urlsplit(source["url"]).query)["license"]
        actual_licenses = set(license_params[0].split(",")) if provider == "inat" else set(license_params)
        assert actual_licenses == allowed
        assert source["license"] == "CC-BY-4.0"
        assert source["attribution"]


def test_wild_lifespan_proxy_is_explicit_and_other_main_traits_remain():
    record = load_record()
    traits = record["traits"]
    assert traits["lifespan_y"] == 13.5
    provenance = record["provenance"]["traits.lifespan_y"]
    assert provenance["sources"] == ["victoria-wildlife-guidelines"]
    assert provenance["derived"] is True
    assert provenance["confidence"] == "Low"
    assert "12–15" in provenance["note"] and "wild cohort" in provenance["note"]
    source = next(s for s in record["sources"] if s["id"] == provenance["sources"][0])
    assert source["license"] == "CC-BY-4.0" and source["attribution"]
    wikipedia = next(s for s in record["sources"] if s["id"] == "wikipedia")
    assert urlsplit(wikipedia["url"]).path == "/wiki/Tiliqua_scincoides"
    assert wikipedia["license"] == "CC-BY-SA-4.0" and wikipedia["attribution"]

    assert traits["diet"] == {
        "invertebrate": 0.4, "fruit": 0.3, "vertebrate": 0.2, "browse": 0.1
    }
    assert record["behavior"]["program"] == "fsm-ground-forager-v1"
    assert record["behavior"]["params"]["rest_sun_hi_deg"] == -6
    assert record["look"]["poses"] == {"idle": {}, "walk": {}, "rest": {}}
