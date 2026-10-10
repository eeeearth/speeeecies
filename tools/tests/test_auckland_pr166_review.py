"""Regression checks for the Auckland locale corrections in PR #166."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCALE = json.loads((ROOT / "locales/auckland-nz/locale.json").read_text())
MAIN_CURVE_HASHES = {
    "acridotheres-tristis": "4e7685f8aaf55689d68c4ef97f397118d148188d259f69ae566b85d7aa061503",
    "passer-domesticus": "0c9a18f96e8b99c13995a3d0456cb04689d49abf17726d917b3d1b31567aa50c",
    "turdus-merula": "f5d13fc2a1b8fe9ab54c7c2e70d2c93edf3c8cdc6b6c5501b14200f4e96ea732",
    "trichosurus-vulpecula": "764fa593da08b4e3f0ada0475ad93fd7eb41c77676114d5c7e16f3413bc04496",
    "erinaceus-europaeus": "9ab99c0f24cdd5227968f231cae5e1499e10dc51a3a6a6a6d2f78ff3062fdab8",
}

def record(slug):
    return json.loads((ROOT / "species" / slug / "species.json").read_text())

def program(slug):
    return json.loads((ROOT / "species" / slug / "behavior.json").read_text())

def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)

def test_existing_main_species_curves_are_unchanged():
    for slug, expected in MAIN_CURVE_HASHES.items():
        regions = [r for r in record(slug)["activity"]["regions"] if r["region"] != "NZ-AUK"]
        encoded = json.dumps(regions, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(encoded).hexdigest() == expected

def test_auckland_elevation_uses_centroid_dem_sample():
    assert LOCALE["elevation_m"] == 40
    fact = next(f for f in LOCALE["facts"] if "public Auckland centroid" in f["text"])
    assert "39.81 m" in fact["text"]
    assert "locations=-36.85,174.77" in fact["source"]["url"]
    assert fact["source"]["license"] == "CC-BY-4.0"
    assert fact["source"]["attribution"]
    assert "highest point" not in fact["text"]

def test_resolved_species_local_month_gates_match_local_claims():
    expected = {
        "prosthemadera-novaeseelandiae": [9, 10],
        "hemiphaga-novaeseelandiae": [9, 10, 11, 12, 1, 2, 3, 4],
        "rhipidura-fuliginosa": [8, 9, 10, 11, 12, 1, 2, 3],
        "todiramphus-sanctus": [8, 9, 10, 11, 12, 1, 2, 3],
        "zosterops-lateralis": [9, 10, 11, 12],
        "ranoidea-aurea": [10, 11, 12, 1, 2, 3],
    }
    for slug, months in expected.items():
        gates = [n["month_in"] for n in walk(program(slug)) if "month_in" in n]
        assert gates == [months]
        assert months[0] in gates[0] and months[-1] in gates[0]
        assert len(gates[0]) == len(set(gates[0]))

    tui_behavior_note = record("prosthemadera-novaeseelandiae")["provenance"]["behavior"]["note"]
    assert "September and October" in tui_behavior_note
    assert "September-January" not in tui_behavior_note

def test_silent_species_have_no_unresolved_songbird_call_actions():
    for slug in ("todiramphus-sanctus", "zosterops-lateralis"):
        d = record(slug); b = program(slug)
        assert d["vocalizations"] == []
        assert not [n for n in walk(b) if n.get("do") in ("sing", "alarm")]
        assert not {"song", "alarm"} & set(b["params"])

def test_feeding_does_not_use_inappropriate_shared_ground_hop():
    tui = [n for n in walk(program("prosthemadera-novaeseelandiae")) if n.get("do") == "eat_nearest"]
    kingfisher = [n for n in walk(program("todiramphus-sanctus")) if n.get("do") == "eat_nearest"]
    kereru = [n for n in walk(program("hemiphaga-novaeseelandiae")) if n.get("do") == "eat_nearest"]
    assert tui and all("gait" not in a for a in tui)
    assert kingfisher and all("gait" not in a for a in kingfisher)
    assert kereru and all(a.get("gait") == "walk" for a in kereru)

def test_uncertain_measurements_and_low_sample_curves_are_explicit():
    for slug in ("prosthemadera-novaeseelandiae", "rhipidura-fuliginosa", "todiramphus-sanctus"):
        assert "wingspan_m" not in record(slug)["traits"]
    skink = record("lampropholis-delicata")
    assert skink["traits"]["length_m"] == 0.096
    assert "snout-vent length 40.57 mm and tail length 55.29 mm" in skink["provenance"]["traits.length_m"]["note"]
    row = next(r for r in skink["activity"]["regions"] if r["region"] == "NZ-AUK")
    assert row["observations"] == 332 and row["query"]["used"] == ["gbif"]
    assert row["query"]["gbif"]["tier"] == "A" and row["query"]["gbif"]["usable"] is True
    for slug, count in (("ranoidea-aurea", 284), ("erinaceus-europaeus", 255)):
        row = next(r for r in record(slug)["activity"]["regions"] if r["region"] == "NZ-AUK")
        assert row["observations"] == count
        assert not any(q.get("usable") for q in row["query"].values() if isinstance(q, dict))

def test_nz_hedgehog_seasons_are_scoped_away_from_european_months():
    d = record("erinaceus-europaeus"); phases = d["seasonal"]["phases"]
    nz = [p for p in phases if p.get("region") == "NZ-AUK"]
    assert nz == []
    assert {p.get("region") for p in phases} == {"GB-ENG", "FR-IDF", "ES-MD", "IE", "DE-BE"}
    evidence = d["provenance"]["seasonal.phases"]
    assert evidence["sources"] == ["wikipedia"]
    assert "No Auckland phase dates are included" in evidence["note"]
    assert "does not model hibernation" in evidence["note"]
    assert not any(s["id"] == "parkes-thesis" for s in d["sources"])

def test_permissive_gbif_alternative_replaces_tier_c_inat_for_myna_and_silvereye():
    for slug in ("acridotheres-tristis", "zosterops-lateralis"):
        row = next(r for r in record(slug)["activity"]["regions"] if r["region"] == "NZ-AUK")
        assert row["query"]["used"] == ["gbif"]
        assert row["query"]["gbif"]["tier"] == "A" and row["query"]["gbif"]["usable"] is True

def test_auckland_tier_c_inat_sources_keep_sharealike_license():
    for slug in LOCALE["species"]:
        for source in record(slug)["sources"]:
            if source["id"].endswith("nz-auk") and "license=cc0,cc-by,cc-by-sa,cc-by-nc,cc-by-nc-sa" in source.get("url", ""):
                assert source["license"] == "CC-BY-NC-SA-4.0"
