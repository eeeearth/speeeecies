"""Focused regression checks for Albuquerque PR #118 review repairs."""
import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "fdd777ed1ccb82dbc857210adf432e7d6da96dfc"
ROSTER = [
    "geococcyx-californianus", "haemorhous-mexicanus", "columba-livia",
    "zenaida-asiatica", "toxostoma-curvirostre", "spinus-psaltria",
    "archilochus-alexandri", "astur-cooperii", "sylvilagus-audubonii",
    "otospermophilus-variegatus", "tadarida-brasiliensis",
]
EXISTING = [s for s in ROSTER if s not in {"spinus-psaltria", "astur-cooperii"}]


def read(path):
    return json.loads((ROOT / path).read_text())


def test_albuquerque_uses_verified_public_site_and_flora():
    locale = read("locales/nm-albuquerque/locale.json")
    assert (locale["public_lat"], locale["public_lon"], locale["elevation_m"]) == (35.08, -106.60, 1590)
    assert locale["place_source"]["url"].endswith("Q7045560")
    assert locale["species"] == ROSTER
    assert len(locale["species"]) >= 8
    assert "sceloporus-cowlesi" not in locale["species"]
    catalog = read("locales/nm-albuquerque/flora-catalog.json")
    assert len(catalog["entries"]) == 8
    assert sum(e["evergreen"] for e in catalog["entries"]) >= 2
    for entry in catalog["entries"]:
        schema_sources = [s for s in entry["provenance"]["sources"] if "flora-taxa.json" in s["url"]]
        assert len(schema_sources) == 1
        assert schema_sources[0]["license"] == "CC-BY-SA-4.0"
    taxa = {x["taxon"]: x for x in read("schema/v0.1/flora-taxa.json")["taxa"]}
    for entry in catalog["entries"]:
        model = taxa[entry["taxon"]]
        assert (entry["archetype"], entry["height_m"], entry["crown_width_m"], entry["evergreen"]) == (model["archetype"], model["height_m"], model["crown_width_m"], model["evergreen"])


def test_us_nm_curves_are_tier_a_and_old_records_are_otherwise_unchanged():
    for slug in ROSTER:
        species = read(f"species/{slug}/species.json")
        region = next(r for r in species["activity"]["regions"] if r["region"] == "US-NM")
        assert region["query"]["gbif"]["tier"] == "A"
        assert region["query"]["gbif"]["usable"] is True
        assert region["query"]["gbif"]["total"] >= 300
        assert region["query"]["used"] == ["gbif"]
        assert region["sources"] == ["gbif-activity-us-nm"]
        src = next(s for s in species["sources"] if s["id"] == "gbif-activity-us-nm")
        assert src["license"] == "CC-BY-4.0"
    for slug in EXISTING:
        base = json.loads(subprocess.check_output(["git", "show", f"{BASE}:species/{slug}/species.json"], cwd=ROOT))
        current = read(f"species/{slug}/species.json")
        base["activity"]["regions"] = [r for r in base["activity"]["regions"] if r["region"] != "US-NM"]
        base["sources"] = [s for s in base["sources"] if s["id"] not in {"gbif-activity-us-nm", "inat-activity-us-nm"}]
        base["provenance"].pop("activity.US-NM", None)
        current["activity"]["regions"] = [r for r in current["activity"]["regions"] if r["region"] != "US-NM"]
        current["sources"] = [s for s in current["sources"] if s["id"] not in {"gbif-activity-us-nm", "inat-activity-us-nm"}]
        current["provenance"].pop("activity.US-NM", None)
        assert current == base, slug


def test_goldfinch_nesting_months_resolve_to_supported_window():
    species = read("species/spinus-psaltria/species.json")
    behavior = read("species/spinus-psaltria/behavior.json")
    assert species["behavior"]["program"] == behavior["id"] == "bt-lesser-goldfinch-v1"
    months = []
    def visit(node):
        if isinstance(node, dict):
            if "month_in" in node:
                months.extend(node["month_in"])
            for value in node.values(): visit(value)
        elif isinstance(node, list):
            for value in node: visit(value)
    visit(behavior["root"])
    assert months == [4, 5, 6, 7, 8, 9]
    assert species["seasonal"]["phases"][0]["start"] == "04-01"
    assert species["seasonal"]["phases"][0]["end"] == "09-30"


def test_hawk_is_species_local_and_does_not_claim_a_breeding_calendar():
    species = read("species/astur-cooperii/species.json")
    behavior = read("species/astur-cooperii/behavior.json")
    assert species["behavior"]["program"] == behavior["id"] == "fsm-coopers-hawk-v1"
    assert behavior["kind"] == "fsm"
    assert "aerial pursuit" in behavior["description"]
    assert species["traits"]["lifespan_y"] == 1.3
    assert "average wild lifespan 1.3 years in one study" in species["provenance"]["traits"]["note"]
    assert species["seasonal"]["phases"][0]["name"] == "territorial"
    assert "does not establish territorial timing" in species["seasonal"]["phases"][0]["note"]
    assert all(v["season_months"] == [] for v in species["vocalizations"])
