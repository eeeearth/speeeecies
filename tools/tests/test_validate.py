"""Tests for tools/validate.py.

Fixtures are built programmatically (see conftest.py): `fake_root` is a
tmp_path with the repo's real schema/ and behaviors/ copied in, and
`make_species` builds a minimal valid species record to mutate per test.
No network access; nothing here depends on the real `species/` directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from conftest import write_species

TOOLS_DIR = Path(__file__).resolve().parents[1]


def codes(findings):
    return {f.code for f in findings}


def run_one(validate_module, fake_root, species, slug="vulpes-vulpes"):
    write_species(fake_root, slug, species)
    result, usage = validate_module.run([], fake_root)
    assert usage == []
    assert len(result.species_reports) == 1
    return result.species_reports[0]


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


def test_minimal_valid_species_passes(validate_module, fake_root, make_species):
    sr = run_one(validate_module, fake_root, make_species())
    errors = [f for f in sr.all_findings() if f.level == "error"]
    assert errors == [], errors
    assert sr.coverage[0] == sr.coverage[1]
    assert sr.cleanliness == 100


def test_repo_behaviors_have_zero_errors(validate_module):
    root = validate_module.default_root()
    result, usage = validate_module.run(
        [str(p) for p in sorted((root / "behaviors").glob("*.json"))], root
    )
    assert usage == []
    all_errors = [f for pr in result.program_reports for f in pr.findings if f.level == "error"]
    assert all_errors == [], all_errors


def test_default_discovery_finds_behaviors_dir(validate_module):
    root = validate_module.default_root()
    result, usage = validate_module.run([], root)
    assert usage == []
    assert len(result.program_reports) == len(list((root / "behaviors").glob("*.json")))


def test_hadada_nesting_schedule_matches_breeding_months():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    behavior = json.loads((root / "behaviors/bt-ground-probing-bird-v1.json").read_text())
    species = json.loads((root / "species/bostrychia-hagedash/species.json").read_text())
    months = []

    def find_months(node):
        if isinstance(node, dict):
            if "month_in" in node:
                months.extend(node["month_in"])
            for value in node.values():
                find_months(value)
        elif isinstance(node, list):
            for value in node:
                find_months(value)

    find_months(behavior["root"])
    resolved = [
        species["behavior"]["params"][month[2:-1]] if isinstance(month, str) and month.startswith("${") else month
        for month in months
    ]
    assert resolved == [10, 11]


# ---------------------------------------------------------------------------
# Cross-ref / bounds checks
# ---------------------------------------------------------------------------


def test_diet_sum_out_of_range(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["diet"] = {"invertebrate": 0.1, "vertebrate": 0.1}
    sr = run_one(validate_module, fake_root, species)
    assert "DietSum" in codes(sr.findings)


def test_slug_mismatch(validate_module, fake_root, make_species):
    species = make_species()
    species["slug"] = "not-the-right-slug"
    sr = run_one(validate_module, fake_root, species)
    assert "SlugMismatch" in codes(sr.findings)
    assert "SlugDirMismatch" in codes(sr.findings)


def test_genus_mismatch(validate_module, fake_root, make_species):
    species = make_species()
    species["taxonomy"]["genus"] = "Canis"
    sr = run_one(validate_module, fake_root, species)
    assert "GenusMismatch" in codes(sr.findings)


def test_synonym_requires_accepted_id(validate_module, fake_root, make_species):
    species = make_species()
    species["taxonomy"]["status"] = "Synonym"
    sr = run_one(validate_module, fake_root, species)
    assert "SynonymNeedsAcceptedId" in codes(sr.findings)


def test_mass_out_of_mass_range(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["mass_kg"] = 100.0
    sr = run_one(validate_module, fake_root, species)
    assert "MassOutOfRange" in codes(sr.findings)


def test_size_class_mismatch(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["size_class"] = "Large"
    sr = run_one(validate_module, fake_root, species)
    assert "SizeClassMismatch" in codes(sr.findings)


def test_habitat_use_sum_out_of_range(validate_module, fake_root, make_species):
    species = make_species()
    species["habitat"]["use"] = {"ground": 0.2}
    sr = run_one(validate_module, fake_root, species)
    assert "HabitatUseSum" in codes(sr.findings)


def test_density_order(validate_module, fake_root, make_species):
    species = make_species()
    species["habitat"]["density_per_ha"] = {"min": 5, "typical": 1, "max": 2}
    sr = run_one(validate_module, fake_root, species)
    assert "DensityOrder" in codes(sr.findings)


def test_fly_requires_wingspan_and_flight(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["locomotion_modes"] = ["Walk", "Fly"]
    sr = run_one(validate_module, fake_root, species)
    assert "FlyNeedsWingspan" in codes(sr.findings)
    assert "FlyNeedsFlight" in codes(sr.findings)


def test_speed_ms_needs_locomotion_mode(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["speed_ms"] = {"walk": 1.0, "swim": 0.5}
    sr = run_one(validate_module, fake_root, species)
    assert "MissingLocomotionForGait" in codes(sr.findings)


def test_dormancy_needs_triggers_and_phase(validate_module, fake_root, make_species):
    species = make_species()
    species["seasonal"]["strategy"] = "Hibernation"
    sr = run_one(validate_module, fake_root, species)
    assert "MissingTriggers" in codes(sr.findings)
    assert "DormancyPhaseMissing" in codes(sr.findings)


def test_migration_needs_absent_phase(validate_module, fake_root, make_species):
    species = make_species()
    species["seasonal"]["strategy"] = "Migration"
    sr = run_one(validate_module, fake_root, species)
    assert "MissingAbsentPhase" in codes(sr.findings)


def test_activity_peak_not_one(validate_module, fake_root, make_species):
    species = make_species()
    species["activity"]["regions"][0]["monthly"] = [0.1] * 12
    sr = run_one(validate_module, fake_root, species)
    assert "ActivityPeakNotOne" in codes(sr.findings)


def test_activity_region_not_in_range_warns(validate_module, fake_root, make_species):
    species = make_species()
    species["activity"]["regions"][0]["region"] = "FR"
    sr = run_one(validate_module, fake_root, species)
    warnings = [f for f in sr.findings if f.code == "ActivityRegionNotInRange"]
    assert warnings


def test_duplicate_call_id(validate_module, fake_root, make_species):
    species = make_species()
    species["vocalizations"].append(dict(species["vocalizations"][0]))
    sr = run_one(validate_module, fake_root, species)
    assert "DuplicateCallId" in codes(sr.findings)


# ---------------------------------------------------------------------------
# Look cross-refs
# ---------------------------------------------------------------------------


def test_unknown_part_in_keyframes(validate_module, fake_root, make_species):
    species = make_species()
    species["look"]["poses"]["idle"] = {"keyframes": [{"t": 0.5, "parts": {"wing_left": {"rot_deg": [0, 0, 0]}}}]}
    sr = run_one(validate_module, fake_root, species)
    assert "UnknownPosePart" in codes(sr.findings)


def test_missing_idle_pose_rejected_by_schema(validate_module, fake_root, make_species):
    species = make_species()
    del species["look"]["poses"]["idle"]
    sr = run_one(validate_module, fake_root, species)
    assert "Schema" in codes(sr.findings)


def test_missing_shoulder_height_warns_for_quadruped(validate_module, fake_root, make_species):
    species = make_species()
    del species["traits"]["shoulder_height_m"]
    sr = run_one(validate_module, fake_root, species)
    assert "MissingShoulderHeight" in codes(sr.findings)


def test_perching_needs_perched_pose(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["perching"] = True
    sr = run_one(validate_module, fake_root, species)
    assert "MissingPerchedPose" in codes(sr.findings)


def test_extra_part_unknown_parent(validate_module, fake_root, make_species):
    species = make_species()
    species["look"]["extra_parts"] = [
        {"name": "crest", "parent": "nonexistent", "offset": [0, 0, 0], "size": [0.1, 0.1, 0.1], "color": "accent"}
    ]
    sr = run_one(validate_module, fake_root, species)
    assert "UnknownParentPart" in codes(sr.findings)


def test_part_colors_unmatched_glob_warns(validate_module, fake_root, make_species):
    species = make_species()
    species["look"]["part_colors"] = {"wing_*": "accent"}
    sr = run_one(validate_module, fake_root, species)
    assert "UnmatchedPartColorGlob" in codes(sr.findings)


# ---------------------------------------------------------------------------
# Behaviour resolution / params
# ---------------------------------------------------------------------------


def test_unknown_param_override(validate_module, fake_root, make_species):
    species = make_species()
    species["behavior"]["params"] = {"not_a_real_param": 1}
    sr = run_one(validate_module, fake_root, species)
    all_findings = sr.all_findings()
    assert "UnknownParamOverride" in codes(all_findings)


def test_param_type_mismatch(validate_module, fake_root, make_species):
    species = make_species()
    species["behavior"]["params"] = {"flee_m": "far"}
    sr = run_one(validate_module, fake_root, species)
    assert "ParamTypeMismatch" in codes(sr.all_findings())


def test_program_not_found(validate_module, fake_root, make_species):
    species = make_species()
    species["behavior"]["program"] = "fsm-does-not-exist-v1"
    sr = run_one(validate_module, fake_root, species)
    assert "ProgramNotFound" in codes(sr.findings)


def test_species_own_behavior_json_used(validate_module, fake_root, make_species):
    species = make_species()
    species["behavior"] = {"program": "fsm-only-mine-v1"}
    species_dir = write_species(fake_root, "vulpes-vulpes", species)
    own_program = {
        "schema_version": 1,
        "id": "fsm-only-mine-v1",
        "kind": "fsm",
        "initial": "idle",
        "states": {"idle": {"action": {"do": "idle"}}},
        "transitions": [{"from": "idle", "to": "idle", "when": {"chance": 0.1}}],
    }
    (species_dir / "behavior.json").write_text(json.dumps(own_program), encoding="utf-8")
    result, usage = validate_module.run([], fake_root)
    sr = result.species_reports[0]
    assert sr.program_reports and sr.program_reports[0].source == "species"


# ---------------------------------------------------------------------------
# Behaviour static lint: FSM
# ---------------------------------------------------------------------------


def make_fsm(**overrides):
    program = {
        "schema_version": 1,
        "id": "fsm-test-v1",
        "kind": "fsm",
        "params": {"p": 5},
        "initial": "a",
        "states": {
            "a": {"action": {"do": "idle"}},
            "b": {"action": {"do": "wander"}},
        },
        "transitions": [
            {"from": "a", "to": "b", "when": {"chance": 0.5}},
            {"from": "b", "to": "a", "when": {"chance": 0.5}},
        ],
    }
    program.update(overrides)
    return program


def test_bad_param_ref(validate_module, fake_root):
    program = make_fsm()
    program["transitions"][0]["when"] = {"chance": "not-a-ref-${p}-extra"}
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "BadParamRef" in codes(findings)


def test_undeclared_param_ref(validate_module, fake_root):
    program = make_fsm()
    program["transitions"][0]["when"] = {"chance": "${nope}"}
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "UndeclaredParamRef" in codes(findings)


def test_fsm_unreachable_state(validate_module, fake_root):
    program = make_fsm()
    program["states"]["c"] = {"action": {"do": "rest"}}
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "FsmUnreachableState" in codes(findings)


def test_fsm_dead_end_state(validate_module, fake_root):
    program = make_fsm()
    program["states"]["c"] = {"action": {"do": "rest"}}
    program["transitions"].append({"from": "a", "to": "c", "when": {"chance": 0.1}})
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "FsmDeadEnd" in codes(findings)


def test_fsm_initial_missing(validate_module, fake_root):
    program = make_fsm(initial="nope")
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "FsmInitialMissing" in codes(findings)


def test_fsm_noop_transition_warns(validate_module, fake_root):
    program = make_fsm()
    program["transitions"][0]["to"] = "a"
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "FsmNoOpTransition" in codes(findings)


# ---------------------------------------------------------------------------
# Behaviour static lint: BT
# ---------------------------------------------------------------------------


def make_bt(root_node):
    return {
        "schema_version": 1,
        "id": "bt-test-v1",
        "kind": "bt",
        "params": {},
        "root": root_node,
    }


def test_bt_unreachable_selector_child(validate_module, fake_root):
    program = make_bt(
        {
            "selector": [
                {"act": {"do": "idle"}},
                {"act": {"do": "wander"}},
            ]
        }
    )
    findings = []
    validate_module.lint_program(program, "test", {}, findings, fake_root, {})
    assert "BtUnreachableAfterDurative" in codes(findings)


def test_bt_durative_not_last_in_sequence(validate_module, fake_root):
    program = make_bt(
        {
            "selector": [
                {
                    "sequence": [
                        {"act": {"do": "rest"}},
                        {"act": {"do": "land"}},
                    ]
                },
                {"act": {"do": "idle"}},
            ]
        }
    )
    findings = []
    validate_module.lint_program(program, "test", {}, findings, fake_root, {})
    assert "BtDurativeNotLast" in codes(findings)


def test_bt_missing_fallback_warns(validate_module, fake_root):
    program = make_bt(
        {
            "selector": [
                {"cond": {"chance": 0.5}},
                {"act": {"do": "land"}},
            ]
        }
    )
    findings = []
    validate_module.lint_program(program, "test", {}, findings, fake_root, {})
    assert "BtMissingFallback" in codes(findings)


def test_bt_subtree_cycle(validate_module, fake_root):
    (fake_root / "behaviors" / "bt-cycle-a-v1.json").write_text(
        json.dumps(make_bt({"subtree": "bt-cycle-b-v1"})), encoding="utf-8"
    )
    (fake_root / "behaviors" / "bt-cycle-b-v1.json").write_text(
        json.dumps({**make_bt({"subtree": "bt-cycle-a-v1"}), "id": "bt-cycle-b-v1"}), encoding="utf-8"
    )
    cache = {}
    program = validate_module.load_shared_program(fake_root, "bt-cycle-a-v1", cache)
    findings = []
    validate_module.lint_program(program, "test", {}, findings, fake_root, cache)
    assert "BtSubtreeCycle" in codes(findings)


def test_emote_requires_kind(validate_module, fake_root):
    program = make_bt({"act": {"do": "emote"}})
    findings = []
    validate_module.lint_program(program, "test", {}, findings, fake_root, {})
    assert "EmoteMissingKind" in codes(findings)


def test_chance_out_of_range(validate_module, fake_root):
    program = make_bt({"selector": [{"cond": {"chance": 5}}, {"act": {"do": "idle"}}]})
    findings = []
    validate_module.lint_program(program, "test", {}, findings, fake_root, {})
    assert "ChanceOutOfRange" in codes(findings)


# ---------------------------------------------------------------------------
# Licence policy
# ---------------------------------------------------------------------------


def test_nd_license_rejected(validate_module, fake_root, make_species):
    species = make_species()
    species["sources"][0]["license"] = "CC-BY-ND-4.0"
    sr = run_one(validate_module, fake_root, species)
    assert "RejectedLicense" in codes(sr.findings)


def test_nc_license_warns(validate_module, fake_root, make_species):
    species = make_species()
    species["sources"][0]["license"] = "CC-BY-NC-4.0"
    species["sources"][0]["attribution"] = "Some Author, CC BY-NC 4.0"
    sr = run_one(validate_module, fake_root, species)
    assert "NonCommercialLicense" in codes(sr.findings)
    assert not any(f.level == "error" and f.code == "RejectedLicense" for f in sr.findings)


def test_missing_attribution_error(validate_module, fake_root, make_species):
    species = make_species()
    species["sources"][0]["license"] = "CC-BY-4.0"
    species["sources"][0].pop("attribution", None)
    sr = run_one(validate_module, fake_root, species)
    assert "MissingAttribution" in codes(sr.findings)


def test_duplicate_source_id(validate_module, fake_root, make_species):
    species = make_species()
    species["sources"].append(dict(species["sources"][0]))
    sr = run_one(validate_module, fake_root, species)
    assert "DuplicateSourceId" in codes(sr.findings)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_uncovered_datum(validate_module, fake_root, make_species):
    species = make_species()
    del species["provenance"]["habitat"]
    sr = run_one(validate_module, fake_root, species)
    uncovered = [f for f in sr.findings if f.code == "UncoveredDatum"]
    assert uncovered
    assert "habitat" in uncovered[0].message


def test_bad_provenance_path(validate_module, fake_root, make_species):
    species = make_species()
    species["provenance"]["traits.not_a_real_field"] = {"sources": ["src-main"], "confidence": "Low"}
    sr = run_one(validate_module, fake_root, species)
    assert "BadProvenancePath" in codes(sr.findings)


def test_unknown_source_id_in_provenance(validate_module, fake_root, make_species):
    species = make_species()
    species["provenance"]["traits"]["sources"] = ["does-not-exist"]
    sr = run_one(validate_module, fake_root, species)
    assert "UnknownSourceId" in codes(sr.findings)


def test_empty_sources_needs_derived_note(validate_module, fake_root, make_species):
    species = make_species()
    species["provenance"]["traits"] = {"sources": [], "confidence": "Low"}
    sr = run_one(validate_module, fake_root, species)
    assert "EmptySourcesNeedsDerivedNote" in codes(sr.findings)


def test_cleanliness_reflects_licence_tiers(validate_module, fake_root, make_species):
    species = make_species()
    species["sources"].append(
        {
            "id": "src-nc",
            "url": "https://example.org/nc",
            "title": "NC source",
            "license": "CC-BY-NC-4.0",
            "attribution": "Some Author",
            "accessed": "2026-01-01",
        }
    )
    species["provenance"]["habitat"] = {"sources": ["src-nc"], "confidence": "Low"}
    sr = run_one(validate_module, fake_root, species)
    assert sr.cleanliness is not None and sr.cleanliness < 100


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


def test_attribution_is_deterministic(validate_module, fake_root, make_species):
    species = make_species()
    species_dir = write_species(fake_root, "vulpes-vulpes", species)
    schemas = validate_module.Schemas(fake_root)
    validate_module.write_attribution(species, species_dir, schemas.licenses)
    first = (species_dir / "ATTRIBUTION.md").read_text(encoding="utf-8")
    validate_module.write_attribution(species, species_dir, schemas.licenses)
    second = (species_dir / "ATTRIBUTION.md").read_text(encoding="utf-8")
    assert first == second
    assert "Red fox" in first
    assert "do not edit" in first.lower()


def test_write_attribution_cli_flag(validate_module, fake_root, make_species):
    species = make_species()
    species_dir = write_species(fake_root, "vulpes-vulpes", species)
    rc = validate_module.main(["--root", str(fake_root), "--write-attribution"])
    assert rc == 0
    assert (species_dir / "ATTRIBUTION.md").exists()


# ---------------------------------------------------------------------------
# CLI / exit codes
# ---------------------------------------------------------------------------


def test_main_exit_code_zero_on_clean_species(validate_module, fake_root, make_species):
    write_species(fake_root, "vulpes-vulpes", make_species())
    rc = validate_module.main(["--root", str(fake_root)])
    assert rc == 0


def test_main_exit_code_one_on_error(validate_module, fake_root, make_species):
    species = make_species()
    species["slug"] = "wrong"
    write_species(fake_root, "vulpes-vulpes", species)
    rc = validate_module.main(["--root", str(fake_root)])
    assert rc == 1


def test_strict_promotes_warning_to_error_exit_code(validate_module, fake_root, make_species):
    species = make_species()
    species["traits"]["perching"] = True  # triggers only a warning (MissingPerchedPose)
    write_species(fake_root, "vulpes-vulpes", species)
    rc_normal = validate_module.main(["--root", str(fake_root)])
    rc_strict = validate_module.main(["--root", str(fake_root), "--strict"])
    assert rc_normal == 0
    assert rc_strict == 1


# ---------------------------------------------------------------------------
# Mirrored extra parts (only <name>_left/<name>_right exist, never the bare
# name -- see site/js/blockmesh.js buildModel())
# ---------------------------------------------------------------------------


def test_later_extra_part_parenting_mirrored_bare_name_is_error(validate_module, fake_root, make_species):
    species = make_species()
    species["look"]["extra_parts"] = [
        {"name": "wing", "parent": "body", "mirror": True, "offset": [0, 0, 0], "size": [0.2, 0.1, 0.4], "color": "accent"},
        {"name": "feather", "parent": "wing", "offset": [0, 0, 0], "size": [0.05, 0.05, 0.05], "color": "accent"},
    ]
    sr = run_one(validate_module, fake_root, species)
    findings = [f for f in sr.findings if f.code == "UnknownParentPart"]
    assert findings, sr.findings
    assert "extra_parts[1]" in findings[0].path
    assert "wing" in findings[0].message


def test_part_colors_naming_mirrored_bare_name_is_error(validate_module, fake_root, make_species):
    species = make_species()
    species["look"]["extra_parts"] = [
        {"name": "wing", "parent": "body", "mirror": True, "offset": [0, 0, 0], "size": [0.2, 0.1, 0.4], "color": "accent"},
    ]
    species["look"]["part_colors"] = {"wing": "accent"}
    sr = run_one(validate_module, fake_root, species)
    assert "PartColorsMirroredBareName" in codes(sr.findings)
    assert not any(f.code == "UnmatchedPartColorGlob" for f in sr.findings)


def test_non_mirrored_extra_part_bare_name_still_usable_as_parent(validate_module, fake_root, make_species):
    # Sanity check the fix doesn't over-tighten: a non-mirrored extra part's
    # bare name is a real part and remains a valid parent for a later one.
    species = make_species()
    species["look"]["extra_parts"] = [
        {"name": "crest", "parent": "body", "offset": [0, 0, 0], "size": [0.2, 0.1, 0.1], "color": "accent"},
        {"name": "crest_tip", "parent": "crest", "offset": [0, 0, 0], "size": [0.05, 0.05, 0.05], "color": "accent"},
    ]
    sr = run_one(validate_module, fake_root, species)
    assert "UnknownParentPart" not in codes(sr.findings)


# ---------------------------------------------------------------------------
# Visual-check Markdown rendering (matches the shape build_report() writes)
# ---------------------------------------------------------------------------


def _visual_check_module():
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    import visual_check as vc

    return vc


def test_render_markdown_renders_real_visual_check_shape(validate_module, fake_root, make_species):
    vc = _visual_check_module()
    species = make_species()
    species_dir = write_species(fake_root, "vulpes-vulpes", species)
    target = "Vulpes vulpes (red fox)"
    report = vc.build_report(
        slug="vulpes-vulpes",
        model="hf-hub:imageomics/bioclip",
        target_label=target,
        labels=[target, "Canis lupus familiaris (domestic dog)"],
        images=[
            {
                "image": "idle-35.png",
                "pose": "idle",
                "yaw": 35,
                "top_label": target,
                "top_score": 0.6,
                "probabilities": {target: 0.6, "Canis lupus familiaris (domestic dog)": 0.4},
            }
        ],
        date="2026-09-25",
    )
    (species_dir / "visual-check.json").write_text(json.dumps(report), encoding="utf-8")

    result, usage = validate_module.run([], fake_root)
    assert usage == []
    md = validate_module.render_markdown(result)

    assert "Visual check (advisory)" in md
    assert target in md
    assert "| idle | 35 |" in md
    assert "0.600" in md  # target probability in the per-image table row
    assert "mean target probability: 0.6" in md
    assert "rank-1 rate: 1.0" in md


# ---------------------------------------------------------------------------
# UnusedParam
# ---------------------------------------------------------------------------


def test_unused_param_warns(validate_module, fake_root):
    program = make_fsm(params={"p": 0.5, "unused_one": 3})
    program["transitions"][0]["when"] = {"chance": "${p}"}
    findings = []
    validate_module.lint_program(program, "test", {"p": 0.5, "unused_one": 3}, findings, fake_root, {})
    unused = [f for f in findings if f.code == "UnusedParam"]
    assert len(unused) == 1
    assert "unused_one" in unused[0].path


def test_unused_param_not_triggered_by_own_body_reference(validate_module, fake_root):
    program = make_fsm()
    program["transitions"][0]["when"] = {"chance": "${p}"}
    findings = []
    validate_module.lint_program(program, "test", {"p": 5}, findings, fake_root, {})
    assert "UnusedParam" not in codes(findings)


def test_repo_shared_programs_have_no_unused_params(validate_module):
    root = validate_module.default_root()
    result, usage = validate_module.run(
        [str(p) for p in sorted((root / "behaviors").glob("*.json"))], root
    )
    assert usage == []
    unused = [
        f for pr in result.program_reports for f in pr.findings if f.code == "UnusedParam"
    ]
    assert unused == [], unused


def test_unused_param_not_double_reported_across_species_and_standalone_pass(validate_module, fake_root, make_species):
    # A shared program used by a species must not have its structural
    # (once-per-program-file) findings duplicated between the species'
    # program report and the standalone behaviors/*.json report.
    shared = make_fsm(id="fsm-shared-unused-v1", params={"p": 0.5, "spare": 1})
    shared["transitions"][0]["when"] = {"chance": "${p}"}
    (fake_root / "behaviors" / "fsm-shared-unused-v1.json").write_text(
        json.dumps(shared),
        encoding="utf-8",
    )
    species = make_species()
    species["behavior"] = {"program": "fsm-shared-unused-v1", "params": {}}
    write_species(fake_root, "vulpes-vulpes", species)

    result, usage = validate_module.run([], fake_root)
    assert usage == []
    species_unused = [f for f in result.species_reports[0].all_findings() if f.code == "UnusedParam"]
    standalone_unused = [f for pr in result.program_reports for f in pr.findings if f.code == "UnusedParam"]
    total_unused = species_unused + standalone_unused
    assert len(total_unused) == 1, total_unused


# ---------------------------------------------------------------------------
# Structural lint runs once per program file; species/<slug>/behavior.json is
# routed through species validation, not treated as a shared program.
# ---------------------------------------------------------------------------


def test_structural_lint_not_duplicated_when_program_has_no_overrides(validate_module, fake_root, make_species):
    # fsm-ground-forager-v1 (a real shared program) has an unreachable state
    # bug injected so it produces a structural finding; two species sharing
    # it, with no overrides, must not each carry a duplicate copy of it.
    shared_path = fake_root / "behaviors" / "fsm-ground-forager-v1.json"
    program = json.loads(shared_path.read_text(encoding="utf-8"))
    program["states"]["orphan"] = {"action": {"do": "rest"}}
    shared_path.write_text(json.dumps(program), encoding="utf-8")

    species_a = make_species("vulpes-vulpes")
    species_b = make_species("erithacus-rubecula")
    species_b["id"] = "Erithacus rubecula"
    species_b["taxonomy"]["genus"] = "Erithacus"
    write_species(fake_root, "vulpes-vulpes", species_a)
    write_species(fake_root, "erithacus-rubecula", species_b)

    result, usage = validate_module.run([], fake_root)
    assert usage == []
    all_unreachable = [
        f
        for sr in result.species_reports
        for f in sr.all_findings()
        if f.code == "FsmUnreachableState"
    ]
    all_unreachable += [
        f for pr in result.program_reports for f in pr.findings if f.code == "FsmUnreachableState"
    ]
    assert len(all_unreachable) == 1, all_unreachable


def test_species_own_behavior_json_with_nonstandard_id_passes_and_is_not_duplicated(
    validate_module, fake_root, make_species
):
    species = make_species()
    species["behavior"] = {"program": "fsm-only-mine-v1"}
    species_dir = write_species(fake_root, "vulpes-vulpes", species)
    own_program = make_fsm(id="fsm-only-mine-v1")
    (species_dir / "behavior.json").write_text(json.dumps(own_program), encoding="utf-8")

    result, usage = validate_module.run([str(species_dir / "behavior.json")], fake_root)
    assert usage == []
    assert len(result.species_reports) == 1
    assert result.program_reports == []
    sr = result.species_reports[0]
    errors = [f for f in sr.all_findings() if f.level == "error"]
    assert errors == [], errors
    assert sr.program_reports and sr.program_reports[0].source == "species"
