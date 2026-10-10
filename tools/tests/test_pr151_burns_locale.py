"""Regression coverage for PR151's corrected Burns claims."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCALE = ROOT / "locales/or-highdesert/locale.json"


def record(slug):
    return json.loads((ROOT / "species" / slug / "species.json").read_text())


def test_burns_curves_use_sufficient_gbif_samples_and_keep_main_regions():
    locale = json.loads(LOCALE.read_text())
    assert len(locale["species"]) == 12
    for slug in locale["species"]:
        species = record(slug)
        region = next(r for r in species["activity"]["regions"] if r["region"] == "US-OR")
        assert region["query"]["used"] == ["gbif"]
        assert region["query"]["gbif"]["total"] >= region["query"]["min_obs"] == 300
        assert "CC0_1_0" in region["query"]["gbif"]["url"]
        assert region["sources"] == ["gbif-activity-us-or"]

    # These current-main records gained a regional curve without losing earlier ones.
    expected = {
        "haemorhous-mexicanus": {"US-NM", "US-CO", "MX-CMX"},
        "pica-hudsonia": {"US-CO"},
        "spinus-tristis": {"US-ND"},
    }
    for slug, old_regions in expected.items():
        assert old_regions <= {r["region"] for r in record(slug)["activity"]["regions"]}


def test_columbia_spotted_frog_claims_match_local_fsm_and_primary_source():
    frog = record("rana-luteiventris")
    diet = frog["traits"]["diet"]
    assert diet.get("fish", 0) == 0
    assert diet["invertebrate"] == 0.95
    assert sum(diet.values()) == 1
    assert frog["traits"]["activity_pattern"] == "Cathemeral"
    assert frog["provenance"]["traits.diet"]["confidence"] == "Low"
    assert "no fish diet evidence" in frog["provenance"]["traits.diet"]["note"].lower()
    assert "usfs-bull-2005" in frog["provenance"]["traits.diet"]["sources"]

    behavior = json.loads((ROOT / "species/rana-luteiventris/behavior.json").read_text())
    assert frog["behavior"]["program"] == behavior["id"] == "fsm-columbia-spotted-frog-v1"
    call_gate = next(
        t["when"]["all"][0]["month_in"]
        for t in behavior["transitions"]
        if t["from"] == "rest" and t["to"] == "call"
    )
    assert call_gate == [3, 4, 5, 6]
    assert all(
        "is_day" not in json.dumps(t.get("when", {}))
        for t in behavior["transitions"]
    )


def test_belding_squirrel_length_includes_tail_and_thrasher_span_is_omitted():
    squirrel = record("urocitellus-beldingi")
    assert squirrel["traits"]["length_m"] == 0.325
    assert "body length" in squirrel["provenance"]["traits.length_m"]["note"]
    assert "tail length" in squirrel["provenance"]["traits.length_m"]["note"]

    thrasher = record("oreoscoptes-montanus")
    assert "wingspan_m" not in thrasher["traits"]
    assert "traits.wingspan_m" not in thrasher["provenance"]


def test_burns_flora_catalog_uses_drawable_taxa_and_marks_range_gap():
    catalog = json.loads((ROOT / "locales/or-highdesert/flora-catalog.json").read_text())
    assert len(catalog["entries"]) == 8
    assert sum(entry["evergreen"] for entry in catalog["entries"]) >= 2
    ash = next(entry for entry in catalog["entries"] if entry.get("stand_in_for") == "Fraxinus latifolia")
    assert ash["native_status"]["or-highdesert"] == "Unknown"
    assert "does not establish a natural Burns-area population" in ash["provenance"]["note"]


def _resolved_actions(program, overrides=None):
    """Return actions with ${param} references resolved as the importer does."""
    params = {**program.get("params", {}), **(overrides or {})}

    def resolve(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            return params[value[2:-1]]
        if isinstance(value, list):
            return [resolve(item) for item in value]
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        return value

    found = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("act"), dict):
                found.append(resolve(node["act"]))
            if isinstance(node.get("action"), dict):
                found.append(resolve(node["action"]))
            for key, value in node.items():
                if key not in {"act", "action"}:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(program)
    return found


def test_frog_call_gate_includes_march_through_june_but_not_february_or_july():
    frog = record("rana-luteiventris")
    behavior = json.loads((ROOT / "species/rana-luteiventris/behavior.json").read_text())
    call_gate = next(
        t["when"]["all"][0]["month_in"]
        for t in behavior["transitions"]
        if t["from"] == "rest" and t["to"] == "call"
    )
    assert call_gate == [3, 4, 5, 6]
    assert {month for month in range(1, 13) if month in call_gate} == {3, 4, 5, 6}
    assert 2 not in call_gate and 7 not in call_gate
    assert frog["behavior"]["program"] == behavior["id"]


def test_burns_species_actions_use_only_declared_gaits_and_poses():
    birds = [
        "corvus-corax",
        "oreoscoptes-montanus",
        "sialia-currucoides",
        "sturnella-neglecta",
        "tyrannus-verticalis",
    ]
    for slug in birds:
        species = record(slug)
        program = json.loads((ROOT / "species" / slug / "behavior.json").read_text())
        assert species["behavior"]["program"] == program["id"]
        actions = _resolved_actions(program, species["behavior"].get("params"))
        assert all(action.get("do") != "build_nest" for action in actions)
        modes = {mode.lower() for mode in species["traits"]["locomotion_modes"]}
        poses = set(species["look"]["poses"])
        for action in actions:
            assert "${" not in json.dumps(action), (slug, action)
            gait = action.get("gait")
            if gait:
                assert gait in modes, (slug, action, modes)
                assert gait in poses, (slug, action, poses)
        if slug in {"corvus-corax", "tyrannus-verticalis"}:
            feeding = next(action for action in actions if action.get("do") == "eat_nearest")
            assert feeding["gait"] == "walk"

    for slug in ("rana-luteiventris", "urocitellus-beldingi", "lepus-californicus"):
        species = record(slug)
        local_program = ROOT / "species" / slug / "behavior.json"
        program_path = local_program if local_program.is_file() else ROOT / "behaviors" / f"{species['behavior']['program']}.json"
        program = json.loads(program_path.read_text())
        modes = {mode.lower() for mode in species["traits"]["locomotion_modes"]}
        poses = set(species["look"]["poses"])
        actions = _resolved_actions(program, species["behavior"].get("params"))
        for action in actions:
            assert "${" not in json.dumps(action), (slug, action)
            gait = action.get("gait")
            if gait:
                assert gait in modes, (slug, action, modes)
                assert gait in poses, (slug, action, poses)
        if slug in {"urocitellus-beldingi", "lepus-californicus"}:
            fleeing = next(action for action in actions if action.get("do") == "flee")
            assert fleeing["gait"] == "hop"
