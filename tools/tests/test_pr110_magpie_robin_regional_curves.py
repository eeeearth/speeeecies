"""Preservation and source-license regressions for PR #110's regional rows."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGIONS = {"IN", "TH", "MY", "SG"}


def read(path):
    return json.loads((ROOT / path).read_text())


def test_current_record_and_existing_in_ka_are_preserved():
    snapshot = read("tools/tests/fixtures/pr110-current-main-record.json")
    assert snapshot["source_commit"] == "fdd777ed1ccb82dbc857210adf432e7d6da96dfc"
    base = snapshot["record"]
    current = read("species/copsychus-saularis/species.json")
    old_in_ka = next(r for r in base["activity"]["regions"] if r["region"] == "IN-KA")
    new_in_ka = next(r for r in current["activity"]["regions"] if r["region"] == "IN-KA")
    assert new_in_ka == old_in_ka

    # Remove only the four intended GBIF rows/sources and supported ITIS identifier.
    current["activity"]["regions"] = [r for r in current["activity"]["regions"] if r["region"] not in REGIONS]
    added_ids = {f"gbif-activity-{region.lower()}" for region in REGIONS}
    current["sources"] = [s for s in current["sources"] if s["id"] not in added_ids | {"itis"}]
    current["external"].pop("itis_tsn")
    for key in ("taxonomy", "external"):
        if "itis" in current["provenance"][key].get("sources", []):
            current["provenance"][key]["sources"].remove("itis")
        if key == "taxonomy":
            current["provenance"][key].pop("note", None)
    assert current == base


def test_added_national_curves_meet_threshold_with_permissive_gbif_only():
    species = read("species/copsychus-saularis/species.json")
    for region in REGIONS:
        row = next(r for r in species["activity"]["regions"] if r["region"] == region)
        assert row["query"]["gbif"]["tier"] == "A"
        assert row["query"]["gbif"]["usable"] is True
        assert row["query"]["gbif"]["total"] >= 300
        assert row["method"] == "gbif_share"
        assert row["query"]["used"] == ["gbif"]
        assert row["sources"] == [f"gbif-activity-{region.lower()}"]
        assert "Not queried" in row["query"]["inat"]["skipped"]
        source = next(s for s in species["sources"] if s["id"] == f"gbif-activity-{region.lower()}")
        assert source["license"] == "CC-BY-4.0"
        assert "CC-BY-NC" not in source["license"]
    assert not any(s["id"] == "inat-activity-sg" for s in species["sources"])


def test_itis_identifier_is_verified_and_old_review_fixes_remain():
    species = read("species/copsychus-saularis/species.json")
    assert species["external"]["itis_tsn"] == 559432
    assert any(s["id"] == "itis" and s["license"] == "public-domain" for s in species["sources"])
    assert "BT" in species["range"]["native"] and "BH" not in species["range"]["native"]
    assert species["provenance"]["traits.diet"]["note"].find("Diet-Vunk 10") >= 0
    assert species["traits"]["diet"]["vertebrate"] == 0.1
