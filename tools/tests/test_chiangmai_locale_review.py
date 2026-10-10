"""Regression checks for the Chiang Mai locale audit corrections."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCALE = json.loads((ROOT / "locales/chiangmai-th/locale.json").read_text())
BIRDS = (
    "pycnonotus-jocosus",
    "pycnonotus-aurigaster",
    "spilopelia-chinensis",
    "acridotheres-tristis",
    "copsychus-saularis",
    "passer-montanus",
    "orthotomus-sutorius",
)


def load_species(slug: str) -> dict:
    return json.loads((ROOT / "species" / slug / "species.json").read_text())


def load_local_behavior(slug: str) -> dict:
    return json.loads((ROOT / "species" / slug / "behavior.json").read_text())


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def actions(program: dict, action_name: str) -> list[dict]:
    return [
        node["act"]
        for node in walk(program)
        if isinstance(node, dict)
        and "act" in node
        and node["act"].get("do") == action_name
    ]


def fsm_actions(program: dict, action_name: str) -> list[dict]:
    """Resolve concrete actions from FSM states (not BT ``act`` nodes)."""
    return [
        state["action"]
        for state in program.get("states", {}).values()
        if state.get("action", {}).get("do") == action_name
    ]


def resolved_gait(action: dict, record: dict, program: dict) -> str | None:
    gait = action.get("gait")
    if not isinstance(gait, str) or not gait.startswith("${"):
        return gait
    name = gait[2:-1]
    params = {**program.get("params", {}), **record["behavior"].get("params", {})}
    return params.get(name)


def test_calotes_is_omitted_until_chiang_mai_taxon_identity_is_supported():
    assert "calotes-versicolor" not in LOCALE["species"]
    assert not (ROOT / "species/calotes-versicolor").exists()
    assert len(LOCALE["species"]) == 11


def test_spotted_dove_and_myna_th50_curves_use_only_permissive_gbif_tier_a():
    for slug in ("spilopelia-chinensis", "acridotheres-tristis"):
        record = load_species(slug)
        region = next(r for r in record["activity"]["regions"] if r["region"] == "TH-50")
        assert region["method"] == "gbif_share"
        assert region["query"]["used"] == ["gbif"]
        assert region["query"]["gbif"]["tier"] == "A"
        assert region["query"]["gbif"]["total"] >= 300
        assert region["query"]["gbif"]["usable"] is True
        assert region["sources"] == ["gbif-activity-th-50"]
        source = next(s for s in record["sources"] if s["id"] == "gbif-activity-th-50")
        assert source["license"] == "CC-BY-4.0"
        assert "license=CC0_1_0&license=CC_BY_4_0" in source["url"]
        assert "inat-activity-th-50" not in {s["id"] for s in record["sources"]}


def test_rare_species_curves_disclose_below_minimum_fallbacks():
    expected = {
        "callosciurus-finlaysonii": (134, 103),
        "tamiops-mcclellandii": (187, 181),
        "duttaphrynus-melanostictus": (177, 153),
    }
    for slug, (inat_count, gbif_count) in expected.items():
        record = load_species(slug)
        region = next(r for r in record["activity"]["regions"] if r["region"] == "TH-50")
        assert region["query"]["min_obs"] == 300
        assert region["query"]["inat"]["total"] == inat_count
        assert region["query"]["gbif"]["total"] == gbif_count
        assert region["query"]["inat"]["usable"] is False
        assert region["query"]["gbif"]["usable"] is False
        assert region["observations"] < 300
        note = record["provenance"]["activity.TH-50"]["note"].lower()
        assert "below the 300-record minimum" in note
        assert "provisional" in note


def test_bird_behaviors_have_no_hidden_nesting_calendar_and_species_supported_gait():
    shared = json.loads(
        (ROOT / "behaviors/bt-perching-songbird-v1.json").read_text()
    )
    assert shared["id"] == "bt-perching-songbird-v1"
    assert {"nest_m1", "nest_m2"} <= shared["params"].keys()
    assert any(
        "month_in" in node.get("cond", {})
        and node["cond"]["month_in"] == ["${nest_m1}", 4, 5, "${nest_m2}"]
        for node in walk(shared)
    )
    expected_gait = {
        "pycnonotus-jocosus": "hop",
        "pycnonotus-aurigaster": "hop",
        "spilopelia-chinensis": "walk",
        "acridotheres-tristis": "walk",
        "copsychus-saularis": "hop",
        "passer-montanus": "hop",
        "orthotomus-sutorius": "hop",
    }
    gait_pose = {"walk": "walk", "hop": "hop"}
    for slug in BIRDS:
        record = load_species(slug)
        program = load_local_behavior(slug)
        assert record["behavior"]["program"] == program["id"]
        assert not any("month_in" in node.get("cond", {}) for node in walk(program))
        assert not actions(program, "build_nest")
        forage = actions(program, "eat_nearest")
        gait = expected_gait[slug]
        assert forage and all(resolved_gait(action, record, program) == gait for action in forage)
        assert gait_pose[gait] in record["look"]["poses"]
        assert "nest_m1" not in program["params"]
        assert "nest_m2" not in program["params"]


def test_toad_call_month_gate_resolves_to_may_through_september():
    record = load_species("duttaphrynus-melanostictus")
    program = load_local_behavior("duttaphrynus-melanostictus")
    assert record["behavior"]["program"] == program["id"]
    call_transition = next(
        t for t in program["transitions"]
        if t["from"] == "rest" and t["to"] == "call"
    )
    resolved_months = call_transition["when"]["all"][0]["month_in"]
    assert resolved_months == [5, 6, 7, 8, 9]
    assert set(range(5, 10)) <= set(resolved_months)
    assert not {"call_m1", "call_m2"} & program["params"].keys()
    assert "not a sourced Thai calendar" in program["description"]
    behavior_note = record["provenance"]["behavior"]["note"]
    assert "global May–September call gate" in behavior_note
    assert "does not establish Thai calling months" in behavior_note
    india_phase = next(
        phase for phase in record["seasonal"]["phases"]
        if phase["name"] == "breeding"
    )
    assert india_phase["region"] == "IN"
    assert (india_phase["start"], india_phase["end"]) == ("06-01", "09-30")
    life = record["provenance"]["traits.lifespan_y"]
    assert life["confidence"] == "Low" and life["derived"] is True
    assert "not a measured typical lifespan" in life["note"]
    age_source = next(s for s in record["sources"] if s["id"] == "toad-age-study")
    assert age_source["url"] == "https://doi.org/10.3390/ani13132099"
    assert age_source["license"] == "CC-BY-4.0"


def test_squirrel_fsm_actions_use_declared_poses_and_do_not_claim_climbing():
    shared = json.loads((ROOT / "behaviors/fsm-ground-forager-v1.json").read_text())
    assert shared["params"]["forage_gait"] == "walk"
    assert shared["params"]["flee_gait"] == "gallop"
    gait_pose = {"walk": "walk", "gallop": "gallop"}
    for slug in ("callosciurus-finlaysonii", "tamiops-mcclellandii"):
        record = load_species(slug)
        program = load_local_behavior(slug)
        assert record["behavior"]["program"] == program["id"]
        assert "climb" not in program["params"].values()
        assert "climb" not in record["behavior"]["params"].values()
        assert all(
            action.get("gait") != "climb"
            for state in program["states"].values()
            for action in [state.get("action", {})]
        )
        for action_name, expected in (
            ("wander", "walk"),
            ("eat_nearest", "walk"),
            ("drink_nearest", "walk"),
            ("flee", "gallop"),
        ):
            resolved = fsm_actions(program, action_name)
            assert resolved, f"{slug}: missing FSM action {action_name}"
            assert all(resolved_gait(action, record, program) == expected for action in resolved)
            assert gait_pose[expected] in record["look"]["poses"]
        assert "no climb pose" in program["description"].lower()


def test_uncalibrated_chord_wingspans_are_omitted_and_gecko_length_is_total():
    for slug in (
        "pycnonotus-jocosus",
        "pycnonotus-aurigaster",
        "spilopelia-chinensis",
        "copsychus-saularis",
        "orthotomus-sutorius",
    ):
        record = load_species(slug)
        assert "wingspan_m" not in record["traits"]
        assert "traits.wingspan_m" not in record["provenance"]
    gecko = load_species("hemidactylus-platyurus")
    wiki = next(s for s in gecko["sources"] if s["id"] == "wikipedia")
    assert "secondary overview" in wiki["title"].lower()
    assert gecko["traits"]["length_m"] == 0.127
    assert "61 mm" in gecko["provenance"]["traits"]["note"]
    assert "66 mm" in gecko["provenance"]["traits"]["note"]
    assert "sum" in gecko["provenance"]["traits"]["note"]


def test_prior_monthly_curves_remain_and_each_protected_species_gains_th50():
    expected_existing = {
        "pycnonotus-jocosus": "9f9cd06a268074b65c3805c95821f648ac23e16c0542223b7bd523969a52efe2",
        "spilopelia-chinensis": "d19d0f700becb81b19891711167d84eb4da566378ef6751711af21b05333378f",
        "acridotheres-tristis": "2b6edfe51b5e95c67d1f6af20343a0a9eae4396e1370155959f8e7ab38f47241",
        "copsychus-saularis": "d746ec28b37d0753cec133539c049cf6f33b3d75126ad75621eb31aecb496401",
        "passer-montanus": "e12faef337ffa2facd924ac3e12dabfe1c01238125e4e4a78bad35e03f053dc2",
        "duttaphrynus-melanostictus": "5ba16647013d594984494e29247ddbd1cd96260940f544bed06fb40056da9ed7",
    }
    for slug, expected_digest in expected_existing.items():
        record = load_species(slug)
        rows = [
            {"region": r["region"], "monthly": r["monthly"]}
            for r in record["activity"]["regions"]
            if r["region"] != "TH-50"
        ]
        digest = hashlib.sha256(
            json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
        assert digest == expected_digest
        assert "TH-50" in {r["region"] for r in record["activity"]["regions"]}


def test_tree_sparrow_thailand_range_is_separate_from_occurrence_evidence():
    record = load_species("passer-montanus")
    assert "TH" in record["range"]["native"]
    note = record["provenance"]["range"]["note"]
    assert "Thailand is included" in note
    assert "occurrence data provides regional activity, not the basis for nativeness" in note
