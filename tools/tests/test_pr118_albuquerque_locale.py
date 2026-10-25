"""Focused regression checks for Albuquerque PR #118 review repairs."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FIXTURE = "tools/tests/fixtures/pr118_albuquerque_existing_species.json"
BASELINE_COMMIT = "fdd777ed1ccb82dbc857210adf432e7d6da96dfc"
ROSTER = [
    "geococcyx-californianus", "haemorhous-mexicanus", "columba-livia",
    "zenaida-asiatica", "toxostoma-curvirostre", "spinus-psaltria",
    "archilochus-alexandri", "astur-cooperii", "sylvilagus-audubonii",
    "otospermophilus-variegatus", "tadarida-brasiliensis",
]
EXISTING = (
    "geococcyx-californianus",
    "haemorhous-mexicanus",
    "columba-livia",
    "zenaida-asiatica",
    "toxostoma-curvirostre",
    "archilochus-alexandri",
    "sylvilagus-audubonii",
    "otospermophilus-variegatus",
    "tadarida-brasiliensis",
)


def read(path):
    return json.loads((ROOT / path).read_text())


def without_new_mexico_activity(species):
    normalized = copy.deepcopy(species)
    normalized["activity"]["regions"] = [
        region for region in normalized["activity"]["regions"]
        if region["region"] != "US-NM"
    ]
    normalized["sources"] = [
        source for source in normalized["sources"]
        if source["id"] not in {"gbif-activity-us-nm", "inat-activity-us-nm"}
    ]
    normalized["provenance"].pop("activity.US-NM", None)
    return normalized


def species_fingerprint(species):
    canonical = json.dumps(species, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    baseline = read(BASELINE_FIXTURE)
    assert baseline["base_commit"] == BASELINE_COMMIT
    assert set(baseline["species_sha256"]) == set(EXISTING)
    for slug in EXISTING:
        current = without_new_mexico_activity(read(f"species/{slug}/species.json"))
        assert species_fingerprint(current) == baseline["species_sha256"][slug], slug


def test_goldfinch_mass_range_and_habitat_sources_match_provenance():
    species = read("species/spinus-psaltria/species.json")
    assert species["traits"]["mass_kg"] == 0.0088
    assert species["traits"]["mass_range_kg"] == [0.006, 0.0115]
    assert species["provenance"]["traits"]["sources"] == ["avonet", "adw"]
    assert "AVONET species-average mass is 8.77 g" in species["provenance"]["traits"]["note"]
    assert species["provenance"]["habitat"]["sources"] == ["wikipedia", "adw"]


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
