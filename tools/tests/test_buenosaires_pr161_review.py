"""Regression checks for Buenos Aires PR #161 review corrections."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCALE = json.loads((ROOT / "locales/buenosaires-ar/locale.json").read_text())
MAIN_RECORD_HASHES = {
    "furnarius-rufus": "4dc787d91a6f749090bb2a9368e938864b81718ea215d360fe381bea60ba41ab",
    "myiopsitta-monachus": "77257cd2066f63bd7799a2dc17dea83466fe999a8ac4ff2a4cfa553807b839ca",
    "passer-domesticus": "d9d7f501ca6f9ec8412afb02c4f3490beab9441d5fda559aa16386f5d65121b5",
    "rattus-norvegicus": "073b874fddbab3388f7950c32b1c2b4b01850fa6fb5651da0819c0a2d2201bc0",
    "salvator-merianae": "f0b017a370a2901b8d59731b65dd10e2b4c0855611ba9255d67f1b3658c7569a",
    "turdus-rufiventris": "de202332f97cfeae8bf4e5bcd6a329e1a6baf8080712d598f30f4744817d4f01",
    "zenaida-auriculata": "54603477f1239c56d4c02412bb619491559461dd786a11cae7560f8ef67b838d",
    "zonotrichia-capensis": "6038e2313f815fb9e900188dc26b053b466001ce4694769c1fc6bf0154438e3e",
}


def record(slug):
    return json.loads((ROOT / "species" / slug / "species.json").read_text())


def behavior(slug):
    data = record(slug)
    local = ROOT / "species" / slug / "behavior.json"
    if local.exists():
        program = json.loads(local.read_text())
    else:
        program_id = data["behavior"]["program"]
        program = json.loads((ROOT / "behaviors" / f"{program_id}.json").read_text())
    program["params"] = {**program.get("params", {}), **data["behavior"].get("params", {})}
    return program


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def resolved_month_gates(program):
    params = program["params"]
    gates = []
    for node in walk(program):
        cond = node.get("cond")
        if isinstance(cond, dict) and "month_in" in cond:
            gates.append([params.get(v[2:-1], v) if isinstance(v, str) and v.startswith("${") else v for v in cond["month_in"]])
    return gates


def test_existing_main_species_are_unchanged_outside_ar_c():
    for slug, expected in MAIN_RECORD_HASHES.items():
        data = record(slug)
        data["activity"]["regions"] = [r for r in data["activity"]["regions"] if r["region"] != "AR-C"]
        data["sources"] = [s for s in data["sources"] if "ar-c" not in s["id"]]
        data["provenance"] = {k: v for k, v in data["provenance"].items() if k != "activity.AR-C"}
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(encoded).hexdigest() == expected


def test_mockingbird_gate_resolves_to_supported_september_january_window():
    slug = "mimus-saturninus"
    assert resolved_month_gates(behavior(slug)) == [[9, 10, 11, 12, 1]]
    phase = record(slug)["seasonal"]["phases"]
    assert [(p["start"], p["end"]) for p in phase] == [("09-01", "01-31")]


def test_unsupported_nesting_calendars_are_not_executed():
    for slug in ("pitangus-sulphuratus", "patagioenas-picazuro", "didelphis-albiventris"):
        assert resolved_month_gates(behavior(slug)) == []
        assert len(record(slug)["seasonal"]["phases"]) == 1
    assert not {"nest_m1", "nest_m2"} & set(behavior("pitangus-sulphuratus")["params"])


def test_picazuro_uses_night_rest_and_flight_escape():
    data = record("patagioenas-picazuro")
    params = data["behavior"]["params"]
    assert params["forage_gait"] == "walk"
    assert params["flee_gait"] == "fly"
    assert (params["rest_sun_lo_deg"], params["rest_sun_hi_deg"]) == (-90, -6)
    assert "fly" in data["look"]["poses"]


def test_opossum_has_no_egg_stage_or_unsupported_calls_or_measurements():
    data = record("didelphis-albiventris")
    assert all(stage["stage"] != "Egg" for stage in data["seasonal"]["life_stages"])
    assert data["vocalizations"] == []
    assert data["traits"]["length_m"] == 1.08
    length_note = data["provenance"]["traits.length_m"]["note"]
    assert "45–70 cm for males" in length_note and "41–60 cm for females" in length_note
    assert "((41+40)+(70+65))/2 = 1.08 m" in length_note
    assert "shoulder_height_m" not in data["traits"]
    assert "wingspan_m" not in data["traits"]
    assert "lifespan_y" in data["traits"]


def test_guessed_optional_wingspans_are_omitted():
    for slug in ("pitangus-sulphuratus", "mimus-saturninus", "patagioenas-picazuro"):
        traits = record(slug)["traits"]
        assert "wingspan_m" not in traits
        assert "lifespan_y" in traits
    assert record("patagioenas-picazuro")["traits"]["length_m"] == 0.32
    assert record("patagioenas-picazuro")["provenance"]["traits.lifespan_y"]["confidence"] == "Low"


def test_kiskadee_lifespan_is_labeled_as_usgs_maximum_record():
    data = record("pitangus-sulphuratus")
    assert data["traits"]["lifespan_y"] == 83 / 12
    source = next(s for s in data["sources"] if s["id"] == "usgs-bbl-longevity")
    assert source["license"] == "US-Gov-PD"
    note = data["provenance"]["traits.lifespan_y"]["note"]
    assert "6 years 11 months" in note
    assert "not a typical or average lifespan" in note
    assert "no more permissively licensed" not in note


def test_opossum_mixed_license_and_low_count_curves_are_explicit():
    data = record("didelphis-albiventris")
    source = next(s for s in data["sources"] if s["id"] == "inat-activity-ar-c")
    assert source["license"] == "CC-BY-NC-SA-4.0"
    assert "cc0,cc-by,cc-by-sa,cc-by-nc,cc-by-nc-sa" in source["url"]
    row = next(r for r in data["activity"]["regions"] if r["region"] == "AR-C")
    assert row["observations"] == 235
    assert row["query"]["inat"]["usable"] is False
    assert row["query"]["gbif"]["total"] == 230 and row["query"]["gbif"]["usable"] is False

    rat = next(r for r in record("rattus-norvegicus")["activity"]["regions"] if r["region"] == "AR-C")
    assert rat["observations"] == 43
    assert rat["query"]["inat"]["total"] == 40 and rat["query"]["inat"]["usable"] is False
    assert rat["query"]["gbif"]["usable"] is False


def test_buenos_aires_mesquite_is_native_algarrobo_stand_in():
    catalog = json.loads((ROOT / "locales/buenosaires-ar/flora-catalog.json").read_text())
    entry = next(p for p in catalog["entries"] if p["taxon"] == "Prosopis glandulosa")
    assert entry["stand_in_for"] == "Prosopis alba"
    assert entry["native_status"]["buenosaires-ar"] == "Native"
    assert any("prosopis_alba" in s["url"].lower() and s["license"] == "CC-BY-SA-4.0" for s in entry["provenance"]["sources"])
    source = next(s for s in entry["provenance"]["sources"] if "argentina.gob.ar" in s["url"])
    assert source["license"] == "CC-BY-4.0"
    assert "San Isidro" in entry["provenance"]["note"]


def test_every_locale_species_has_one_ar_c_curve():
    for slug in LOCALE["species"]:
        rows = [r for r in record(slug)["activity"]["regions"] if r["region"] == "AR-C"]
        assert len(rows) == 1
