"""PR109 keeps current main data and adds only reusable LK/MY activity."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECIES_PATH = ROOT / "species/duttaphrynus-melanostictus/species.json"


def _record():
    return json.loads(SPECIES_PATH.read_text())


def _fingerprint(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def test_pr109_preserves_main_record_and_in_ka_curve_exactly():
    record = _record()
    core = {key: value for key, value in record.items() if key not in {"sources", "activity", "provenance"}}
    assert _fingerprint(core) == "7be1db2f9d9d5d80243a2c1725ff1206b45777071bd6f74f96005011556a3e8a"
    in_ka = next(row for row in record["activity"]["regions"] if row["region"] == "IN-KA")
    assert _fingerprint(in_ka) == "af44342658997001ca794e5c3ccbc23183e582345b9616143803d7ff4d17df1e"
    in_ka_sources = [source for source in record["sources"] if "in-ka" in source["id"]]
    assert _fingerprint(in_ka_sources) == "0f778b40c7f6c3f268a5f92e6b8cc65031715b19192426534ee1fcb228e376a7"
    original_sources = [source for source in record["sources"] if source["id"] not in {"gbif-activity-lk", "gbif-activity-my"}]
    assert _fingerprint(original_sources) == "3aca1220b5f588ab4b35a3e037e168292f6dd1c5860a103d12cf17e79c7ce2ce"
    original_provenance = {key: value for key, value in record["provenance"].items() if key not in {"activity.LK", "activity.MY"}}
    assert _fingerprint(original_provenance) == "46dc8237fed43543cb9332f608ce8d10cc542e6a6f0221b55d0c5108e6dd9f31"
    assert record["external"] == {
        "gbif_usage_key": 2422538,
        "inat_taxon_id": 62345,
        "ncbi_taxon_id": 30335,
        "wikidata": "Q28031739",
    }


def test_pr109_adds_only_supported_gbif_lk_and_my_curves():
    record = _record()
    regions = {row["region"]: row for row in record["activity"]["regions"]}
    assert set(regions) == {"IN-KA", "LK", "MY"}
    assert regions["LK"]["monthly"] == [0.5, 0.19, 0.26, 0.62, 1.0, 0.36, 0.27, 0.62, 0.11, 0.3, 0.19, 0.3]
    assert regions["MY"]["monthly"] == [0.13, 0.21, 0.23, 0.35, 0.08, 1.0, 0.26, 0.33, 0.19, 0.33, 0.18, 0.31]

    source_ids = {source["id"]: source for source in record["sources"]}
    for region, count in (("LK", 486), ("MY", 396)):
        row = regions[region]
        source_id = f"gbif-activity-{region.lower()}"
        assert row["method"] == "gbif_raw"
        assert row["observations"] == count
        assert row["sources"] == [source_id]
        assert row["query"]["used"] == ["gbif"]
        assert row["query"]["gbif"]["tier"] == "A"
        assert row["query"]["gbif"]["total"] == count
        assert row["query"]["gbif"]["url"].endswith("license=CC0_1_0&license=CC_BY_4_0")
        assert row["query"]["min_obs"] == 300
        assert source_ids[source_id]["license"] == "CC-BY-4.0"
        assert source_ids[source_id]["id"] == source_id
        assert source_id in record["provenance"][f"activity.{region}"]["sources"]

    assert "inat-activity-lk" not in source_ids
    assert "inat-activity-my" not in source_ids
