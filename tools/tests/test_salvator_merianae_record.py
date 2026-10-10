"""Regression checks for evidence-backed Salvator merianae record corrections."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORD_PATH = ROOT / "species" / "salvator-merianae" / "species.json"


def test_tegu_range_home_range_and_diet_match_provenance():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))

    assert set(record["range"]["native"]) == {"AR", "BO", "BR", "PY", "UY"}
    sources = {source["id"]: source for source in record["sources"]}
    assert record["provenance"]["range"]["sources"] == ["zenodo-range-2016"]
    assert sources["zenodo-range-2016"]["license"] == "CC0-1.0"
    assert "home_range_ha" not in record["traits"]

    diet = record["traits"]["diet"]
    assert diet["fruit"] > 0
    assert record["provenance"]["traits.diet"]["sources"] == ["campagnoli-christianini-2024"]
    assert sources["campagnoli-christianini-2024"]["license"] == "CC-BY-4.0"
    assert abs(sum(diet.values()) - 1) <= 0.05

    fruit_resources = [
        use for use in record["habitat"]["resources"]
        if use["tag"] == "fruit" and use["kind"] == "Herbivory"
    ]
    assert len(fruit_resources) == 1
    assert fruit_resources[0]["weight"] > 0
