#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.18"]
# ///
"""speeeecies validator.

Checks a species record (`species/<slug>/species.json`) and behaviour
programs (`species/<slug>/behavior.json`, `behaviors/*.json`) against the
v0.1 schemas, then runs the cross-reference, look, behaviour-lint and
licence/provenance checks described in `PLAN.md`.

Pipeline (see `run()`): load -> schema check -> cross-refs/bounds ->
behaviour lint -> licence/provenance -> report.

Usage:
    uv run tools/validate.py [PATH ...]
    uv run tools/validate.py --report
    uv run tools/validate.py species/vulpes-vulpes --write-attribution

With no PATH, every `species/*/` and `behaviors/*.json` is checked.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Iterator

import jsonschema

FORMAT_VERSION = "0.1"

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

LEVELS = ("error", "warning", "info")


@dataclass
class Finding:
    level: str  # error | warning | info
    code: str
    path: str
    message: str

    def line(self) -> str:
        return f"{self.level.upper()} {self.path}: {self.message}"


def has_blocking_errors(findings: Iterable[Finding], strict: bool) -> bool:
    for f in findings:
        if f.level == "error":
            return True
        if strict and f.level == "warning":
            return True
    return False


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ---------------------------------------------------------------------------
# Repo layout / loading
# ---------------------------------------------------------------------------


def default_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path, findings: list[Finding]) -> Any | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        findings.append(Finding("error", "IoError", str(path), f"cannot read file: {exc}"))
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        findings.append(Finding("error", "JsonError", str(path), f"invalid JSON: {exc}"))
        return None


class Schemas:
    """Loads and caches the v0.1 schema/policy files from `<root>/schema/v0.1`."""

    def __init__(self, root: Path):
        schema_dir = root / "schema" / "v0.1"
        self.species_schema = json.loads((schema_dir / "species.schema.json").read_text())
        self.behavior_schema = json.loads(
            (schema_dir / "behavior-program.schema.json").read_text()
        )
        self.body_plans = json.loads((schema_dir / "body-plans.json").read_text())
        self.licenses = json.loads((schema_dir / "licenses.json").read_text())
        self._validators: dict[int, jsonschema.protocols.Validator] = {}

    def validator_for(self, schema: dict) -> jsonschema.protocols.Validator:
        key = id(schema)
        v = self._validators.get(key)
        if v is None:
            v = jsonschema.Draft202012Validator(
                schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
            )
            self._validators[key] = v
        return v


def schema_findings(instance: Any, schema: dict, schemas: Schemas, prefix: str) -> list[Finding]:
    validator = schemas.validator_for(schema)
    findings = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(map(str, e.path))):
        path = prefix
        for seg in err.path:
            path += f"[{seg}]" if isinstance(seg, int) else f".{seg}"
        findings.append(Finding("error", "Schema", path, err.message))
    return findings


# ---------------------------------------------------------------------------
# Species cross-refs and bounds
# ---------------------------------------------------------------------------

SIZE_CLASS_BOUNDS = [("Tiny", 0.05), ("Small", 1), ("Medium", 50)]
GAIT_TO_LOCOMOTION = {
    "walk": "Walk",
    "trot": "Trot",
    "gallop": "Gallop",
    "hop": "Hop",
    "climb": "Climb",
    "slither": "Slither",
    "swim": "Swim",
    "fly": "Fly",
    "glide": "Glide",
    "hover": "Hover",
    "burrow": "Burrow",
}
DORMANCY_STRATEGIES = {"Hibernation", "Brumation", "Torpor", "Diapause", "Aestivation"}


def expected_size_class(mass_kg: float) -> str:
    for name, bound in SIZE_CLASS_BOUNDS:
        if mass_kg < bound:
            return name
    return "Large"


def region_country(code: str) -> str:
    return code.split("-", 1)[0]


def check_range_pair(pair: Any, path: str, findings: list[Finding], code: str = "RangeOrder") -> None:
    if isinstance(pair, list) and len(pair) == 2 and is_number(pair[0]) and is_number(pair[1]):
        if pair[0] > pair[1]:
            findings.append(Finding("error", code, path, f"low {pair[0]} > high {pair[1]}"))


def check_identity(species: dict, slug_from_dir: str | None, findings: list[Finding]) -> None:
    taxon_id = species.get("id", "")
    derived_slug = taxon_id.lower().replace(" ", "-")
    slug = species.get("slug")
    if slug != derived_slug:
        findings.append(
            Finding("error", "SlugMismatch", "slug", f"slug '{slug}' != derived from id '{derived_slug}'")
        )
    if slug_from_dir is not None and slug != slug_from_dir:
        findings.append(
            Finding(
                "error",
                "SlugDirMismatch",
                "slug",
                f"slug '{slug}' != directory name '{slug_from_dir}'",
            )
        )
    genus = species.get("taxonomy", {}).get("genus")
    first_word = taxon_id.split(" ")[0] if taxon_id else ""
    if genus and genus != first_word:
        findings.append(
            Finding(
                "error",
                "GenusMismatch",
                "taxonomy.genus",
                f"genus '{genus}' != first word of id '{first_word}'",
            )
        )
    taxonomy = species.get("taxonomy", {})
    if taxonomy.get("status") == "Synonym" and not taxonomy.get("accepted_id"):
        findings.append(
            Finding(
                "error",
                "SynonymNeedsAcceptedId",
                "taxonomy.accepted_id",
                "status is Synonym but accepted_id is missing",
            )
        )


def check_traits(species: dict, findings: list[Finding]) -> None:
    traits = species.get("traits", {})

    diet = traits.get("diet", {})
    if diet:
        total = sum(v for v in diet.values() if is_number(v))
        if abs(total - 1.0) > 0.05:
            findings.append(
                Finding("error", "DietSum", "traits.diet", f"diet shares sum to {total:.3f}, expected 1 +/- 0.05")
            )

    mass_kg = traits.get("mass_kg")
    mass_range = traits.get("mass_range_kg")
    check_range_pair(mass_range, "traits.mass_range_kg", findings)
    if is_number(mass_kg) and isinstance(mass_range, list) and len(mass_range) == 2:
        lo, hi = mass_range
        if is_number(lo) and is_number(hi) and not (lo <= mass_kg <= hi):
            findings.append(
                Finding(
                    "error",
                    "MassOutOfRange",
                    "traits.mass_kg",
                    f"mass_kg {mass_kg} outside mass_range_kg {mass_range}",
                )
            )

    size_class = traits.get("size_class")
    if size_class and is_number(mass_kg):
        expected = expected_size_class(mass_kg)
        if size_class != expected:
            findings.append(
                Finding(
                    "error",
                    "SizeClassMismatch",
                    "traits.size_class",
                    f"size_class '{size_class}' inconsistent with mass_kg {mass_kg} (expected '{expected}')",
                )
            )

    check_range_pair(traits.get("social", {}).get("group_size"), "traits.social.group_size", findings)

    locomotion_modes = set(traits.get("locomotion_modes", []))
    for gait, speed in traits.get("speed_ms", {}).items():
        mode = GAIT_TO_LOCOMOTION.get(gait)
        if mode and mode not in locomotion_modes:
            findings.append(
                Finding(
                    "error",
                    "MissingLocomotionForGait",
                    f"traits.speed_ms.{gait}",
                    f"speed_ms has '{gait}' but locomotion_modes lacks '{mode}'",
                )
            )

    if "Fly" in locomotion_modes:
        if not is_number(traits.get("wingspan_m")):
            findings.append(
                Finding("error", "FlyNeedsWingspan", "traits.wingspan_m", "Fly locomotion needs wingspan_m")
            )
        if traits.get("flight") == "None":
            findings.append(
                Finding("error", "FlyNeedsFlight", "traits.flight", "Fly locomotion needs flight != None")
            )



def check_habitat(species: dict, findings: list[Finding]) -> None:
    habitat = species.get("habitat", {})
    use = habitat.get("use", {})
    if use:
        total = sum(v for v in use.values() if is_number(v))
        if abs(total - 1.0) > 0.05:
            findings.append(
                Finding("error", "HabitatUseSum", "habitat.use", f"use shares sum to {total:.3f}, expected 1 +/- 0.05")
            )

    density = habitat.get("density_per_ha", {})
    lo, typ, hi = density.get("min"), density.get("typical"), density.get("max")
    if all(is_number(x) for x in (lo, typ, hi)):
        if not (lo <= typ <= hi):
            findings.append(
                Finding(
                    "error",
                    "DensityOrder",
                    "habitat.density_per_ha",
                    f"expected min <= typical <= max, got {lo} <= {typ} <= {hi}",
                )
            )

    life_stages = {ls.get("stage") for ls in species.get("seasonal", {}).get("life_stages", [])}
    for i, res in enumerate(habitat.get("resources", [])):
        stage = res.get("life_stage")
        if stage and stage not in life_stages:
            findings.append(
                Finding(
                    "error",
                    "UnknownLifeStage",
                    f"habitat.resources[{i}].life_stage",
                    f"life_stage '{stage}' not in seasonal.life_stages",
                )
            )


def check_seasonal(species: dict, findings: list[Finding]) -> None:
    seasonal = species.get("seasonal", {})
    strategy = seasonal.get("strategy")
    phases = seasonal.get("phases", [])
    phase_names = {p.get("name") for p in phases}

    if strategy in DORMANCY_STRATEGIES:
        if not seasonal.get("triggers"):
            findings.append(
                Finding(
                    "error",
                    "MissingTriggers",
                    "seasonal.triggers",
                    f"strategy '{strategy}' requires seasonal.triggers",
                )
            )
        if "dormancy" not in phase_names:
            findings.append(
                Finding(
                    "warning",
                    "DormancyPhaseMissing",
                    "seasonal.phases",
                    f"strategy '{strategy}' usually has a phase named 'dormancy'",
                )
            )

    if strategy == "Migration" and "absent" not in phase_names:
        findings.append(
            Finding("error", "MissingAbsentPhase", "seasonal.phases", "Migration requires a phase named 'absent'")
        )

    if strategy == "PartialMigration" and not is_number(seasonal.get("winter_fraction")):
        findings.append(
            Finding(
                "error",
                "MissingWinterFraction",
                "seasonal.winter_fraction",
                "PartialMigration requires winter_fraction",
            )
        )

    native = species.get("range", {}).get("native", [])
    introduced = species.get("range", {}).get("introduced", [])
    range_countries = {region_country(c) for c in native + introduced}
    for i, phase in enumerate(phases):
        region = phase.get("region")
        if region and region_country(region) not in range_countries:
            findings.append(
                Finding(
                    "warning",
                    "PhaseRegionNotInRange",
                    f"seasonal.phases[{i}].region",
                    f"region '{region}' not in range.native or range.introduced",
                )
            )


def check_vocalizations(species: dict, findings: list[Finding]) -> None:
    seen = set()
    source_ids = {s.get("id") for s in species.get("sources", [])}
    for i, voc in enumerate(species.get("vocalizations", [])):
        path = f"vocalizations[{i}]"
        call_id = voc.get("call_id")
        if call_id in seen:
            findings.append(Finding("error", "DuplicateCallId", f"{path}.call_id", f"duplicate call_id '{call_id}'"))
        seen.add(call_id)
        check_range_pair(voc.get("freq_hz"), f"{path}.freq_hz", findings)
        check_range_pair(voc.get("duration_s"), f"{path}.duration_s", findings)
        for rec in voc.get("recordings", []):
            if rec not in source_ids:
                findings.append(
                    Finding("error", "RecordingSourceMissing", f"{path}.recordings", f"source id '{rec}' not in sources")
                )


def check_activity(species: dict, findings: list[Finding]) -> None:
    native = species.get("range", {}).get("native", [])
    introduced = species.get("range", {}).get("introduced", [])
    range_countries = {region_country(c) for c in native + introduced}
    source_ids = {s.get("id") for s in species.get("sources", [])}
    seen_regions = set()
    for i, region in enumerate(species.get("activity", {}).get("regions", [])):
        path = f"activity.regions[{i}]"
        code = region.get("region")
        if code in seen_regions:
            findings.append(Finding("error", "DuplicateActivityRegion", path, f"duplicate region '{code}'"))
        seen_regions.add(code)
        monthly = region.get("monthly", [])
        if monthly:
            peak = max(monthly)
            if abs(peak - 1.0) > 0.01:
                findings.append(
                    Finding("error", "ActivityPeakNotOne", f"{path}.monthly", f"peak month is {peak}, expected 1 +/- 0.01")
                )
        if code and region_country(code) not in range_countries:
            findings.append(
                Finding("warning", "ActivityRegionNotInRange", f"{path}.region", f"region '{code}' not in range.native or range.introduced")
            )
        for sid in region.get("sources", []):
            if sid not in source_ids:
                findings.append(
                    Finding("error", "ActivitySourceMissing", f"{path}.sources", f"source id '{sid}' not in sources")
                )


def check_species_crossrefs(species: dict, slug_from_dir: str | None, findings: list[Finding]) -> None:
    check_identity(species, slug_from_dir, findings)
    check_traits(species, findings)
    check_habitat(species, findings)
    check_seasonal(species, findings)
    check_vocalizations(species, findings)
    check_activity(species, findings)


# ---------------------------------------------------------------------------
# Look / body-plan cross-refs
# ---------------------------------------------------------------------------


def generated_part_names(look: dict, body_plans: dict) -> list[str] | None:
    plan_name = look.get("body_plan")
    plan = body_plans.get("plans", {}).get(plan_name)
    if plan is None:
        return None
    if plan_name == "serpentine":
        segments = look.get("proportions", {}).get("segments", plan["defaults"].get("segments", 10))
        return ["head"] + [f"segment{i}" for i in range(segments)]
    return list(plan["parts"])


def extra_part_result_names(ep: dict) -> list[str]:
    name = ep.get("name", "")
    if ep.get("mirror"):
        return [f"{name}_left", f"{name}_right"]
    return [name]


def check_look(species: dict, body_plans: dict, findings: list[Finding]) -> None:
    look = species.get("look")
    if not look:
        return
    plan_name = look.get("body_plan")
    plan = body_plans.get("plans", {}).get(plan_name)
    if plan is None:
        findings.append(Finding("error", "UnknownBodyPlan", "look.body_plan", f"unknown body plan '{plan_name}'"))
        return

    if plan_name in ("quadruped", "hopper") and not is_number(species.get("traits", {}).get("shoulder_height_m")):
        findings.append(
            Finding(
                "warning",
                "MissingShoulderHeight",
                "traits.shoulder_height_m",
                f"look.body_plan '{plan_name}' usually gives traits.shoulder_height_m",
            )
        )

    generated = generated_part_names(look, body_plans) or []
    all_parts = set(generated)
    # Bare names of earlier extra parts that exist as-is (non-mirrored) and so
    # are valid parents / names for later extra parts.
    prior_extra_bare = set()
    # Bare names of earlier *mirrored* extra parts. buildModel() in
    # site/js/blockmesh.js only ever registers "<name>_left"/"<name>_right"
    # for a mirrored extra part -- the bare name is never a real part -- so
    # this is tracked separately and must never be treated as eligible.
    mirrored_bare_names = set()

    for i, ep in enumerate(look.get("extra_parts", [])):
        path = f"look.extra_parts[{i}]"
        name = ep.get("name")
        parent = ep.get("parent")
        eligible_parents = all_parts | prior_extra_bare
        if parent not in eligible_parents:
            findings.append(
                Finding("error", "UnknownParentPart", f"{path}.parent", f"parent '{parent}' is not a generated part or an earlier extra part")
            )
        result_names = extra_part_result_names(ep)
        if any(n in all_parts for n in result_names) or name in prior_extra_bare or name in mirrored_bare_names:
            findings.append(Finding("error", "DuplicateExtraPartName", f"{path}.name", f"part name '{name}' clashes with an existing part"))
        all_parts.update(result_names)
        if ep.get("mirror"):
            mirrored_bare_names.add(name)
        else:
            prior_extra_bare.add(name)

    poses = look.get("poses", {})
    for pose_name, pose in poses.items():
        for k, kf in enumerate(pose.get("keyframes", []) if pose else []):
            for part_name in kf.get("parts", {}):
                if part_name not in all_parts:
                    findings.append(
                        Finding(
                            "error",
                            "UnknownPosePart",
                            f"look.poses.{pose_name}.keyframes[{k}].parts.{part_name}",
                            f"part '{part_name}' does not exist on body plan '{plan_name}'",
                        )
                    )

    for key in look.get("part_colors", {}):
        if key in mirrored_bare_names:
            findings.append(
                Finding(
                    "error",
                    "PartColorsMirroredBareName",
                    f"look.part_colors.{key}",
                    f"'{key}' is a mirrored extra part; only '{key}_left'/'{key}_right' exist, not the bare name",
                )
            )
            continue
        if not any(fnmatch.fnmatch(part, key) for part in all_parts):
            findings.append(
                Finding("warning", "UnmatchedPartColorGlob", f"look.part_colors.{key}", f"'{key}' matches no part of body plan '{plan_name}'")
            )

    locomotion_to_pose = body_plans.get("locomotion_to_pose", {})
    for mode in species.get("traits", {}).get("locomotion_modes", []):
        pose_name = locomotion_to_pose.get(mode)
        if pose_name and pose_name not in poses:
            findings.append(
                Finding("warning", "MissingLocomotionPose", "look.poses", f"locomotion mode '{mode}' usually needs a '{pose_name}' pose")
            )

    if species.get("traits", {}).get("perching") and "perched" not in poses:
        findings.append(Finding("warning", "MissingPerchedPose", "look.poses", "traits.perching is true but no 'perched' pose"))

    builtin_poses = set(plan.get("poses", []))
    for pose_name, pose in poses.items():
        has_keyframes = bool(pose and pose.get("keyframes"))
        if pose_name not in builtin_poses and not has_keyframes:
            findings.append(
                Finding("warning", "NoBuiltInAnimation", f"look.poses.{pose_name}", f"'{pose_name}' has no built-in animation for '{plan_name}' and no keyframes")
            )


# ---------------------------------------------------------------------------
# Behaviour program loading / resolution
# ---------------------------------------------------------------------------

PARAM_REF_RE = re.compile(r"^\$\{([a-z_][a-z0-9_]*)\}$")

DURATIVE_ACTS = {
    "idle",
    "wander",
    "rest",
    "incubate",
    "build_nest",
    "eat_nearest",
    "drink_nearest",
    "hide_nearest",
    "flee",
}


def shared_program_path(root: Path, program_id: str) -> Path:
    return root / "behaviors" / f"{program_id}.json"


def load_shared_program(root: Path, program_id: str, cache: dict[str, Any | None]) -> Any | None:
    if program_id in cache:
        return cache[program_id]
    path = shared_program_path(root, program_id)
    program = None
    if path.is_file():
        try:
            program = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            program = None
    cache[program_id] = program
    return program


def bt_children(node: dict) -> list[dict]:
    for key in ("selector", "sequence", "parallel"):
        if key in node:
            return node[key]
    for key in ("inverter", "succeeder"):
        if key in node:
            return [node[key]]
    if "repeat" in node or "cooldown_s" in node or "timeout_s" in node:
        return [node["child"]]
    return []


def iter_bt_nodes(node: dict) -> Iterator[dict]:
    yield node
    for child in bt_children(node):
        yield from iter_bt_nodes(child)


def collect_declared_params(
    program: dict, root: Path, cache: dict[str, Any | None], visited: set[str] | None = None
) -> dict[str, str]:
    """Param name -> 'number'|'string', merged from this program and every bt subtree it reaches."""
    visited = visited if visited is not None else set()
    pid = program.get("id")
    if pid in visited:
        return {}
    visited.add(pid)
    declared = {
        name: ("number" if is_number(value) else "string") for name, value in program.get("params", {}).items()
    }
    if program.get("kind") == "bt":
        for node in iter_bt_nodes(program.get("root", {})):
            if "subtree" in node:
                sub = load_shared_program(root, node["subtree"], cache)
                if sub:
                    declared.update(collect_declared_params(sub, root, cache, visited))
    return declared


def collect_declared_param_values(
    program: dict, root: Path, cache: dict[str, Any | None], visited: set[str] | None = None
) -> dict[str, Any]:
    visited = visited if visited is not None else set()
    pid = program.get("id")
    if pid in visited:
        return {}
    visited.add(pid)
    values: dict[str, Any] = {}
    if program.get("kind") == "bt":
        for node in iter_bt_nodes(program.get("root", {})):
            if "subtree" in node:
                sub = load_shared_program(root, node["subtree"], cache)
                if sub:
                    values.update(collect_declared_param_values(sub, root, cache, visited))
    values.update(program.get("params", {}))
    return values


def check_param_overrides(
    overrides: dict, declared: dict[str, str], path_prefix: str, findings: list[Finding]
) -> None:
    for name, value in overrides.items():
        path = f"{path_prefix}.{name}"
        if name not in declared:
            findings.append(Finding("error", "UnknownParamOverride", path, f"program does not declare param '{name}'"))
            continue
        expected = declared[name]
        actual = "number" if is_number(value) else "string"
        if actual != expected:
            findings.append(
                Finding("error", "ParamTypeMismatch", path, f"param '{name}' is {expected} in the program, got {actual}")
            )


# ---------------------------------------------------------------------------
# Param substitution
# ---------------------------------------------------------------------------


def collect_referenced_param_names(value: Any, names: set[str]) -> None:
    """Collect every `${name}` reference in `value` (a program's own raw body,
    pre-substitution) into `names`. Does not descend into subtree bodies --
    a `{"subtree": "some-id"}` node's string value never matches
    PARAM_REF_RE, so subtrees are never accidentally credited with using a
    param they don't declare themselves."""
    if isinstance(value, str):
        m = PARAM_REF_RE.match(value)
        if m:
            names.add(m.group(1))
        return
    if isinstance(value, list):
        for v in value:
            collect_referenced_param_names(v, names)
        return
    if isinstance(value, dict):
        for v in value.values():
            collect_referenced_param_names(v, names)


def check_unused_params(program: dict, prefix: str, findings: list[Finding]) -> None:
    """Warn about params a program declares in its own `params` block but
    never references anywhere in its own body (subtrees it reaches don't
    count as using them)."""
    declared = program.get("params", {})
    if not declared:
        return
    referenced: set[str] = set()
    if program.get("kind") == "fsm":
        collect_referenced_param_names(program.get("states", {}), referenced)
        collect_referenced_param_names(program.get("transitions", []), referenced)
    elif program.get("kind") == "bt":
        collect_referenced_param_names(program.get("root", {}), referenced)
    else:
        return
    for name in declared:
        if name not in referenced:
            findings.append(
                Finding("warning", "UnusedParam", f"{prefix}.params.{name}", f"param '{name}' is declared but never referenced in this program's own body")
            )


def substitute(value: Any, params: dict[str, Any], path: str, findings: list[Finding]) -> Any:
    if isinstance(value, str):
        m = PARAM_REF_RE.match(value)
        if m:
            name = m.group(1)
            if name not in params:
                findings.append(Finding("error", "UndeclaredParamRef", path, f"unknown param ref '${{{name}}}'"))
                return value
            return params[name]
        if "${" in value:
            findings.append(Finding("error", "BadParamRef", path, f"malformed param reference: {value!r}"))
            return value
        return value
    if isinstance(value, list):
        return [substitute(v, params, f"{path}[{i}]", findings) for i, v in enumerate(value)]
    if isinstance(value, dict):
        return {k: substitute(v, params, f"{path}.{k}", findings) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# Static value-range lint (post substitution)
# ---------------------------------------------------------------------------

WITHIN_M_KEYS = (
    "threat_within_m",
    "food_within_m",
    "water_within_m",
    "shelter_within_m",
    "perch_within_m",
    "nest_site_within_m",
    "player_within_m",
    "conspecifics_within_m",
)


def check_predicate_ranges(pred: dict, path: str, findings: list[Finding]) -> None:
    if "chance" in pred and is_number(pred["chance"]) and not (0 <= pred["chance"] <= 1):
        findings.append(Finding("error", "ChanceOutOfRange", path, f"chance {pred['chance']} outside [0,1]"))

    if "need" in pred:
        for bound in ("gt", "lt"):
            if bound in pred and is_number(pred[bound]) and not (0 <= pred[bound] <= 1):
                findings.append(Finding("error", "NeedBoundOutOfRange", f"{path}.{bound}", f"{bound} {pred[bound]} outside [0,1]"))

    for key in WITHIN_M_KEYS:
        if key in pred and is_number(pred[key]) and not (0 < pred[key] <= 1000):
            findings.append(Finding("error", "WithinMOutOfRange", f"{path}.{key}", f"{key} {pred[key]} outside (0,1000]"))

    if "conspecifics_within_m" in pred and "gte" in pred and is_number(pred["gte"]) and pred["gte"] < 1:
        findings.append(Finding("error", "ConspecificsGteInvalid", f"{path}.gte", f"gte {pred['gte']} must be >= 1"))

    if "sun_elevation_between_deg" in pred:
        lo, hi = pred["sun_elevation_between_deg"]
        if is_number(lo) and is_number(hi):
            if not (-90 <= lo <= 90) or not (-90 <= hi <= 90):
                findings.append(Finding("error", "SunElevationOutOfRange", f"{path}.sun_elevation_between_deg", f"{[lo, hi]} outside [-90,90]"))
            elif lo > hi:
                findings.append(Finding("error", "SunElevationOrder", f"{path}.sun_elevation_between_deg", f"low {lo} > high {hi}"))

    if "month_in" in pred:
        for m in pred["month_in"]:
            if is_number(m) and not (1 <= m <= 12):
                findings.append(Finding("error", "MonthInOutOfRange", f"{path}.month_in", f"month {m} outside 1..12"))

    if "temperature_between_c" in pred:
        lo, hi = pred["temperature_between_c"]
        if is_number(lo) and is_number(hi):
            if not (-60 <= lo <= 60) or not (-60 <= hi <= 60):
                findings.append(Finding("error", "TemperatureOutOfRange", f"{path}.temperature_between_c", f"{[lo, hi]} outside [-60,60]"))
            elif lo > hi:
                findings.append(Finding("error", "TemperatureOrder", f"{path}.temperature_between_c", f"low {lo} > high {hi}"))


def check_action(action: dict, path: str, findings: list[Finding]) -> None:
    if action.get("do") == "emote" and "kind" not in action:
        findings.append(Finding("error", "EmoteMissingKind", path, "emote action requires 'kind'"))


def check_duration(value: Any, path: str, findings: list[Finding], name: str) -> None:
    if is_number(value) and not (0 < value <= 86400):
        findings.append(Finding("error", "DurationOutOfRange", path, f"{name} {value} outside (0,86400]"))


def check_repeat(value: Any, path: str, findings: list[Finding]) -> None:
    if is_number(value) and (value != int(value) or value < 1):
        findings.append(Finding("error", "RepeatInvalid", path, f"repeat {value} must be an integer >= 1"))


def check_parallel(node: dict, path: str, findings: list[Finding]) -> None:
    n = len(node.get("parallel", []))
    succeed_on = node.get("succeed_on")
    if is_number(succeed_on) and not (1 <= succeed_on <= n):
        findings.append(Finding("error", "ParallelSucceedOnInvalid", f"{path}.succeed_on", f"succeed_on {succeed_on} outside 1..{n}"))


def iter_predicates(pred: dict, path: str) -> Iterator[tuple[dict, str]]:
    yield pred, path
    if "all" in pred:
        for i, p in enumerate(pred["all"]):
            yield from iter_predicates(p, f"{path}.all[{i}]")
    elif "any" in pred:
        for i, p in enumerate(pred["any"]):
            yield from iter_predicates(p, f"{path}.any[{i}]")
    elif "not" in pred:
        yield from iter_predicates(pred["not"], f"{path}.not")


def check_call_and_food(action: dict, path: str, species: dict, findings: list[Finding]) -> None:
    do = action.get("do")
    if do in ("sing", "alarm"):
        call = action.get("call", "song" if do == "sing" else "alarm")
        call_ids = {v.get("call_id") for v in species.get("vocalizations", [])}
        if call not in call_ids:
            findings.append(Finding("warning", "UnknownCallId", f"{path}.call", f"call '{call}' not found in vocalizations"))
    elif do == "eat_nearest" and action.get("tag"):
        check_food_tag(action["tag"], path, species, findings)


def check_food_tag(tag: str, path: str, species: dict, findings: list[Finding]) -> None:
    tags = {r.get("tag") for r in species.get("habitat", {}).get("resources", [])}
    if tag not in tags:
        findings.append(Finding("warning", "UnknownFoodTag", path, f"food tag '{tag}' not in habitat.resources"))


def check_food_tag_predicate(pred: dict, path: str, species: dict, findings: list[Finding]) -> None:
    if "food_within_m" in pred and "tag" in pred:
        check_food_tag(pred["tag"], f"{path}.tag", species, findings)


# ---------------------------------------------------------------------------
# FSM structural lint
# ---------------------------------------------------------------------------


def bfs(graph: dict[str, set[str]], start: str) -> set[str]:
    seen = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def lint_fsm_structure(program: dict, prefix: str, findings: list[Finding]) -> None:
    states = program.get("states", {})
    transitions = program.get("transitions", [])
    initial = program.get("initial")
    state_names = set(states.keys())

    if initial not in state_names:
        findings.append(Finding("error", "FsmInitialMissing", f"{prefix}.initial", f"initial state '{initial}' is not defined"))

    for i, t in enumerate(transitions):
        tp = f"{prefix}.transitions[{i}]"
        frm, to = t.get("from"), t.get("to")
        if frm != "*" and frm not in state_names:
            findings.append(Finding("error", "FsmUnknownState", f"{tp}.from", f"unknown state '{frm}'"))
        if to not in state_names:
            findings.append(Finding("error", "FsmUnknownState", f"{tp}.to", f"unknown state '{to}'"))
        if frm == to:
            findings.append(Finding("warning", "FsmNoOpTransition", tp, f"transition {frm} -> {to} never changes state"))

    wildcard_targets = {t["to"] for t in transitions if t.get("from") == "*" and t.get("to") in state_names}
    graph: dict[str, set[str]] = {s: set(wildcard_targets) - {s} for s in state_names}
    explicit_out = {s: False for s in state_names}
    for t in transitions:
        frm, to = t.get("from"), t.get("to")
        if frm != "*" and frm in state_names and to in state_names:
            graph[frm].add(to)
            explicit_out[frm] = True

    if initial in state_names:
        reached = bfs(graph, initial)
        for s in sorted(state_names - reached):
            findings.append(Finding("error", "FsmUnreachableState", f"{prefix}.states.{s}", f"state '{s}' is not reachable from initial '{initial}'"))

    for s in sorted(state_names):
        can_return = bfs(graph, s)
        if s != initial and initial not in can_return:
            findings.append(Finding("error", "FsmDeadEnd", f"{prefix}.states.{s}", f"state '{s}' has no path back to initial '{initial}'"))
        if not explicit_out[s]:
            findings.append(Finding("warning", "FsmNoExplicitExit", f"{prefix}.states.{s}", f"state '{s}' has no outgoing transitions other than wildcard '*' ones"))


# ---------------------------------------------------------------------------
# BT structural lint
# ---------------------------------------------------------------------------


def is_bare_durative_act(node: dict) -> bool:
    return "act" in node and node["act"].get("do") in DURATIVE_ACTS


def check_bt_value_ranges(node: dict, path: str, findings: list[Finding]) -> None:
    """Re-check the numeric-range findings embedded in the BT tree shape
    (`repeat`, `cooldown_s`, `timeout_s`, a `parallel`'s `succeed_on`) against
    substituted values, without re-emitting the structural findings from
    `lint_bt_node` (those don't depend on param values, so are only linted
    once per program file -- see `lint_program`). Does not descend into
    `subtree` nodes: a subtree's own value ranges are checked when that
    program is linted in its own right."""
    if "selector" in node or "sequence" in node:
        key = "selector" if "selector" in node else "sequence"
        for i, c in enumerate(node[key]):
            check_bt_value_ranges(c, f"{path}.{key}[{i}]", findings)
        return
    if "parallel" in node:
        check_parallel(node, path, findings)
        for i, c in enumerate(node["parallel"]):
            check_bt_value_ranges(c, f"{path}.parallel[{i}]", findings)
        return
    if "inverter" in node:
        check_bt_value_ranges(node["inverter"], f"{path}.inverter", findings)
        return
    if "succeeder" in node:
        check_bt_value_ranges(node["succeeder"], f"{path}.succeeder", findings)
        return
    if "repeat" in node:
        check_repeat(node.get("repeat"), f"{path}.repeat", findings)
        check_bt_value_ranges(node["child"], f"{path}.child", findings)
        return
    if "cooldown_s" in node:
        check_duration(node.get("cooldown_s"), f"{path}.cooldown_s", findings, "cooldown_s")
        check_bt_value_ranges(node["child"], f"{path}.child", findings)
        return
    if "timeout_s" in node:
        check_duration(node.get("timeout_s"), f"{path}.timeout_s", findings, "timeout_s")
        check_bt_value_ranges(node["child"], f"{path}.child", findings)
        return
    # subtree / cond / act: leaves for this purpose.


def lint_bt_structure(
    program: dict,
    prefix: str,
    findings: list[Finding],
    root: Path,
    cache: dict[str, Any | None],
) -> None:
    lint_bt_node(program.get("root", {}), f"{prefix}.root", findings, root, cache, [program.get("id")], is_root=True)


def lint_bt_node(
    node: dict,
    path: str,
    findings: list[Finding],
    root: Path,
    cache: dict[str, Any | None],
    ancestry: list[str],
    is_root: bool = False,
) -> None:
    if "selector" in node:
        children = node["selector"]
        for i, c in enumerate(children[:-1]):
            if is_bare_durative_act(c):
                findings.append(
                    Finding("warning", "BtUnreachableAfterDurative", f"{path}.selector[{i}]", f"selector children after this unconditional durative act '{c['act']['do']}' are unreachable")
                )
        if is_root and children and not is_bare_durative_act(children[-1]):
            findings.append(Finding("warning", "BtMissingFallback", path, "root selector has no always-running fallback (e.g. idle) as its last child"))
        for i, c in enumerate(children):
            lint_bt_node(c, f"{path}.selector[{i}]", findings, root, cache, ancestry)
        return

    if "sequence" in node:
        children = node["sequence"]
        for i, c in enumerate(children[:-1]):
            if is_bare_durative_act(c):
                findings.append(
                    Finding("warning", "BtDurativeNotLast", f"{path}.sequence[{i}]", f"durative act '{c['act']['do']}' is not the last child of this sequence; later children never run")
                )
        for i, c in enumerate(children):
            lint_bt_node(c, f"{path}.sequence[{i}]", findings, root, cache, ancestry)
        return

    if "parallel" in node:
        check_parallel(node, path, findings)
        for i, c in enumerate(node["parallel"]):
            lint_bt_node(c, f"{path}.parallel[{i}]", findings, root, cache, ancestry)
        return

    if "inverter" in node:
        lint_bt_node(node["inverter"], f"{path}.inverter", findings, root, cache, ancestry)
        return
    if "succeeder" in node:
        lint_bt_node(node["succeeder"], f"{path}.succeeder", findings, root, cache, ancestry)
        return
    if "repeat" in node:
        check_repeat(node.get("repeat"), f"{path}.repeat", findings)
        lint_bt_node(node["child"], f"{path}.child", findings, root, cache, ancestry)
        return
    if "cooldown_s" in node:
        check_duration(node.get("cooldown_s"), f"{path}.cooldown_s", findings, "cooldown_s")
        lint_bt_node(node["child"], f"{path}.child", findings, root, cache, ancestry)
        return
    if "timeout_s" in node:
        check_duration(node.get("timeout_s"), f"{path}.timeout_s", findings, "timeout_s")
        lint_bt_node(node["child"], f"{path}.child", findings, root, cache, ancestry)
        return
    if "subtree" in node:
        sub_id = node["subtree"]
        if sub_id in ancestry:
            findings.append(Finding("error", "BtSubtreeCycle", path, f"subtree cycle: {' -> '.join(ancestry + [sub_id])}"))
            return
        sub = load_shared_program(root, sub_id, cache)
        if sub is None:
            findings.append(Finding("error", "BtUnresolvedSubtree", path, f"subtree '{sub_id}' does not resolve to behaviors/{sub_id}.json"))
        elif sub.get("kind") != "bt":
            findings.append(Finding("error", "BtSubtreeNotBt", path, f"subtree '{sub_id}' is not a bt program"))
        else:
            lint_bt_node(sub.get("root", {}), f"{path}(subtree:{sub_id}).root", findings, root, cache, ancestry + [sub_id], is_root=True)
        return
    # cond / act: leaves, nothing further to descend into.


def iter_fsm_actions_and_predicates(program: dict, prefix: str) -> tuple[list[tuple[dict, str]], list[tuple[dict, str]]]:
    actions = []
    predicates: list[tuple[dict, str]] = []
    for name, st in program.get("states", {}).items():
        actions.append((st.get("action", {}), f"{prefix}.states.{name}.action"))
    for i, t in enumerate(program.get("transitions", [])):
        predicates.extend(iter_predicates(t.get("when", {}), f"{prefix}.transitions[{i}].when"))
    return actions, predicates


def iter_bt_actions_and_predicates(program: dict, prefix: str) -> tuple[list[tuple[dict, str]], list[tuple[dict, str]]]:
    actions: list[tuple[dict, str]] = []
    predicates: list[tuple[dict, str]] = []

    def walk(node: dict, path: str) -> None:
        if "act" in node:
            actions.append((node["act"], f"{path}.act"))
            return
        if "cond" in node:
            predicates.extend(iter_predicates(node["cond"], f"{path}.cond"))
            return
        if "subtree" in node:
            return  # subtrees are linted (and their own actions checked) when validated as their own program
        for key in ("selector", "sequence", "parallel"):
            if key in node:
                for i, c in enumerate(node[key]):
                    walk(c, f"{path}.{key}[{i}]")
                return
        for key in ("inverter", "succeeder"):
            if key in node:
                walk(node[key], f"{path}.{key}")
                return
        if "repeat" in node or "cooldown_s" in node or "timeout_s" in node:
            walk(node["child"], f"{path}.child")

    walk(program.get("root", {}), f"{prefix}.root")
    return actions, predicates


# ---------------------------------------------------------------------------
# Program lint driver
# ---------------------------------------------------------------------------


def lint_program(
    program: dict,
    prefix: str,
    params: dict[str, Any],
    findings: list[Finding],
    root: Path,
    cache: dict[str, Any | None],
    species: dict | None = None,
    *,
    structural: bool = True,
) -> None:
    """Static lint of one program instantiated with `params`.

    Called once per program *file*, with its own declared defaults
    (`species=None`, `structural=True`) -- this is the only pass that emits
    the structural findings (FSM reachability/dead-end/no-explicit-exit, BT
    selector/sequence/subtree shape, unused params, param-ref shape, the
    `emote` action check): none of those depend on param *values*, so
    running them again per species would just duplicate the same findings.

    Called again per species instantiation, with that species' effective
    params (its overrides applied) and `species` given (`structural=False`):
    this pass only re-checks what genuinely depends on the instantiation --
    numeric ranges after substitution, call ids, and food tags.
    """
    sub_findings: list[Finding] = []
    program = copy.deepcopy(program)

    if program.get("kind") == "fsm":
        if structural:
            check_unused_params(program, prefix, findings)
        program["states"] = substitute(program.get("states", {}), params, f"{prefix}.states", sub_findings)
        program["transitions"] = substitute(program.get("transitions", []), params, f"{prefix}.transitions", sub_findings)
        if structural:
            findings.extend(sub_findings)
            lint_fsm_structure(program, prefix, findings)
        for name, st in program.get("states", {}).items():
            if "min_dwell_s" in st:
                check_duration(st["min_dwell_s"], f"{prefix}.states.{name}.min_dwell_s", findings, "min_dwell_s")
        actions, predicates = iter_fsm_actions_and_predicates(program, prefix)
    elif program.get("kind") == "bt":
        if structural:
            check_unused_params(program, prefix, findings)
        program["root"] = substitute(program.get("root", {}), params, f"{prefix}.root", sub_findings)
        if structural:
            findings.extend(sub_findings)
            lint_bt_structure(program, prefix, findings, root, cache)
        else:
            check_bt_value_ranges(program.get("root", {}), f"{prefix}.root", findings)
        actions, predicates = iter_bt_actions_and_predicates(program, prefix)
    else:
        return

    for action, apath in actions:
        if structural:
            check_action(action, apath, findings)
        if species is not None:
            check_call_and_food(action, apath, species, findings)
    for pred, ppath in predicates:
        check_predicate_ranges(pred, ppath, findings)
        if species is not None:
            check_food_tag_predicate(pred, ppath, species, findings)


# ---------------------------------------------------------------------------
# Licence policy
# ---------------------------------------------------------------------------


def license_tier(license_id: str | None, policy: dict) -> dict | None:
    if not license_id:
        return None
    for pattern in policy.get("rejected_patterns", []):
        if pattern in license_id:
            return None
    for tier in policy.get("tiers", []):
        if license_id in tier.get("licenses", []):
            return tier
    return None


def check_sources(species: dict, policy: dict, findings: list[Finding]) -> dict[str, dict]:
    source_map: dict[str, dict] = {}
    seen_ids: set[str] = set()
    attribution_not_required = set(policy.get("attribution_not_required", []))
    for i, src in enumerate(species.get("sources", [])):
        path = f"sources[{i}]"
        sid = src.get("id")
        if sid in seen_ids:
            findings.append(Finding("error", "DuplicateSourceId", f"{path}.id", f"duplicate source id '{sid}'"))
        seen_ids.add(sid)
        source_map[sid] = src
        lic = src.get("license")
        tier = license_tier(lic, policy)
        if tier is None:
            findings.append(Finding("error", "RejectedLicense", f"{path}.license", f"license '{lic}' is rejected or unknown"))
        elif lic not in attribution_not_required and not src.get("attribution"):
            findings.append(Finding("error", "MissingAttribution", f"{path}.attribution", f"license '{lic}' requires an attribution line"))
    return source_map


# ---------------------------------------------------------------------------
# Provenance / coverage / cleanliness
# ---------------------------------------------------------------------------

_MISSING = object()

BLOCK_PATHS = {
    "taxonomy",
    "external",
    "range",
    "conservation",
    "traits",
    "habitat",
    "seasonal",
    "vocalizations",
    "look",
    "behavior",
}

LIST_MATCH_KEYS = ("call_id", "region", "name", "stage", "tag")


def _match_in_list(items: list, seg: str) -> Any:
    if seg.isdigit():
        idx = int(seg)
        if 0 <= idx < len(items):
            return items[idx]
    for item in items:
        if isinstance(item, dict):
            for key in LIST_MATCH_KEYS:
                if key in item and str(item[key]) == seg:
                    return item
    return _MISSING


def _descend(node: Any, seg: str) -> Any:
    if isinstance(node, dict):
        if seg in node:
            return node[seg]
        for v in node.values():
            if isinstance(v, list):
                found = _match_in_list(v, seg)
                if found is not _MISSING:
                    return found
        return _MISSING
    if isinstance(node, list):
        return _match_in_list(node, seg)
    return _MISSING


def resolve_path_exists(species: dict, path: str) -> bool:
    node: Any = species
    for seg in path.split("."):
        node = _descend(node, seg)
        if node is _MISSING:
            return False
    return True


def compute_required_datums(species: dict) -> set[str]:
    datums = {"taxonomy", "external", "range"}
    if "conservation" in species:
        datums.add("conservation")
    for k in species.get("traits", {}):
        datums.add(f"traits.{k}")
    for k in species.get("habitat", {}):
        datums.add(f"habitat.{k}")
    datums.add("seasonal.strategy")
    datums.add("seasonal.phases")
    datums.add("seasonal.life_stages")
    if "triggers" in species.get("seasonal", {}):
        datums.add("seasonal.triggers")
    for voc in species.get("vocalizations", []):
        cid = voc.get("call_id")
        if cid:
            datums.add(f"vocalizations.{cid}")
    datums.add("look")
    datums.add("behavior")
    return datums


@dataclass
class ProvenanceResult:
    covered: int
    total: int
    cleanliness: float | None
    license_mix: Counter
    source_license_counts: Counter


def check_provenance(species: dict, source_map: dict[str, dict], policy: dict, findings: list[Finding]) -> ProvenanceResult:
    provenance: dict = species.get("provenance", {})

    for path, entry in provenance.items():
        ppath = f"provenance.{path}"
        if not resolve_path_exists(species, path):
            findings.append(Finding("error", "BadProvenancePath", ppath, f"path '{path}' does not resolve into the record"))
        for sid in entry.get("sources", []):
            if sid not in source_map:
                findings.append(Finding("error", "UnknownSourceId", f"{ppath}.sources", f"source id '{sid}' not in sources"))
        if not entry.get("sources") and not (entry.get("derived") and entry.get("note")):
            findings.append(Finding("error", "EmptySourcesNeedsDerivedNote", ppath, "empty sources needs derived=true and a note"))

    required = compute_required_datums(species)
    effective_sources: dict[str, list[str]] = {}
    missing: list[str] = []
    for datum in required:
        candidates = [p for p in provenance if datum == p or datum.startswith(p + ".")]
        if not candidates:
            missing.append(datum)
            continue
        nearest = max(candidates, key=len)
        effective_sources[datum] = provenance[nearest].get("sources", [])

    if missing:
        findings.append(Finding("error", "UncoveredDatum", "provenance", "not covered by provenance: " + ", ".join(sorted(missing))))

    for path in provenance:
        if path in BLOCK_PATHS:
            count = sum(1 for d in required if d == path or d.startswith(path + "."))
            if count > 1:
                findings.append(Finding("info", "CoarseProvenance", f"provenance.{path}", f"covers {count} datums at once"))

    activity_regions = species.get("activity", {}).get("regions", [])
    for region in activity_regions:
        code = region.get("region")
        if code:
            effective_sources[f"activity.{code}"] = region.get("sources", [])

    scores: list[float] = []
    tier4_backed: dict[str, list[str]] = {}
    mix: Counter = Counter()
    for datum, sids in effective_sources.items():
        if not sids:
            scores.append(1.0)
            mix["authored"] += 1
            continue
        best_score = None
        for sid in sids:
            src = source_map.get(sid)
            tier = license_tier(src.get("license"), policy) if src else None
            score = tier["score"] if tier else 0.0
            if tier and tier.get("warning"):
                tier4_backed.setdefault(sid, []).append(datum)
            if best_score is None or score < best_score[0]:
                best_score = (score, tier)
        scores.append(best_score[0])
        if best_score[1] is None:
            mix["rejected"] += 1
        else:
            mix[f"tier{best_score[1]['tier']}"] += 1

    for sid, src in source_map.items():
        tier = license_tier(src.get("license"), policy)
        if tier and tier.get("warning"):
            datums = sorted(tier4_backed.get(sid, []))
            suffix = f"; backs: {', '.join(datums)}" if datums else "; backs no covered datum"
            findings.append(Finding("warning", "NonCommercialLicense", f"sources.{sid}", f"license '{src.get('license')}' is tier 4 (non-commercial){suffix}"))

    cleanliness = round(100 * mean(scores)) if scores else None
    source_license_counts: Counter = Counter(s.get("license") for s in species.get("sources", []))
    total = len(required) + len(activity_regions)
    covered = total - len(missing)
    return ProvenanceResult(covered, total, cleanliness, mix, source_license_counts)


def datum_sources_for_attribution(species: dict) -> dict[str, list[str]]:
    """Source id -> sorted datum paths it backs, for ATTRIBUTION.md."""
    provenance: dict = species.get("provenance", {})
    required = compute_required_datums(species)
    backing: dict[str, set[str]] = {}
    for datum in required:
        candidates = [p for p in provenance if datum == p or datum.startswith(p + ".")]
        if not candidates:
            continue
        nearest = max(candidates, key=len)
        for sid in provenance[nearest].get("sources", []):
            backing.setdefault(sid, set()).add(datum)
    for region in species.get("activity", {}).get("regions", []):
        code = region.get("region")
        for sid in region.get("sources", []):
            backing.setdefault(sid, set()).add(f"activity.{code}")
    return {sid: sorted(datums) for sid, datums in backing.items()}


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


def write_attribution(species: dict, species_dir: Path, policy: dict) -> Path:
    common_name = species.get("common_names", {}).get("en", "?")
    scientific_name = species.get("id", "?")
    backing = datum_sources_for_attribution(species)
    sources_by_id = {s.get("id"): s for s in species.get("sources", [])}

    tier_order = sorted(policy.get("tiers", []), key=lambda t: t["tier"])
    lines = [f"# {common_name} ({scientific_name})", "", "Generated by tools/validate.py; do not edit.", ""]

    for tier in tier_order:
        tier_ids = sorted(
            sid for sid, src in sources_by_id.items() if src.get("license") in tier.get("licenses", [])
        )
        if not tier_ids:
            continue
        lines.append(f"## Tier {tier['tier']}: {tier['name']}")
        if tier.get("warning"):
            lines.append("")
            lines.append("**Non-commercial licence: do not use this data in a commercial context.**")
        lines.append("")
        for sid in tier_ids:
            src = sources_by_id[sid]
            lines.append(f"- **{src.get('title')}**")
            lines.append(f"  - URL: {src.get('url')}")
            lines.append(f"  - Licence: {src.get('license')}")
            attribution = src.get("attribution")
            if attribution:
                lines.append(f"  - Attribution: {attribution}")
            lines.append(f"  - Accessed: {src.get('accessed')}")
            datums = backing.get(sid, [])
            if datums:
                lines.append(f"  - Covers: {', '.join(datums)}")
        lines.append("")

    out_path = species_dir / "ATTRIBUTION.md"
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Per-target results
# ---------------------------------------------------------------------------


@dataclass
class ProgramReport:
    program_id: str
    kind: str
    source: str  # "shared" | "species"
    node_count: int
    findings: list[Finding] = field(default_factory=list)


def count_program_nodes(program: dict) -> int:
    if program.get("kind") == "fsm":
        return len(program.get("states", {}))
    if program.get("kind") == "bt":
        return sum(1 for _ in iter_bt_nodes(program.get("root", {})))
    return 0


@dataclass
class SpeciesReport:
    slug: str
    path: Path
    species: dict | None
    findings: list[Finding] = field(default_factory=list)
    program_reports: list[ProgramReport] = field(default_factory=list)
    cleanliness: float | None = None
    coverage: tuple[int, int] | None = None
    license_mix: Counter = field(default_factory=Counter)
    source_license_counts: Counter = field(default_factory=Counter)
    visual_check: dict | None = None

    def all_findings(self) -> list[Finding]:
        out = list(self.findings)
        for pr in self.program_reports:
            out.extend(pr.findings)
        return out


@dataclass
class StandaloneProgramReport:
    path: Path
    program_id: str | None
    findings: list[Finding] = field(default_factory=list)


@dataclass
class Result:
    species_reports: list[SpeciesReport] = field(default_factory=list)
    program_reports: list[StandaloneProgramReport] = field(default_factory=list)

    def has_errors(self, strict: bool) -> bool:
        for sr in self.species_reports:
            if has_blocking_errors(sr.all_findings(), strict):
                return True
        for pr in self.program_reports:
            if has_blocking_errors(pr.findings, strict):
                return True
        return False


# ---------------------------------------------------------------------------
# Validating one species / one standalone program
# ---------------------------------------------------------------------------


def resolve_species_program(
    species: dict, species_dir: Path, root: Path, cache: dict[str, Any | None], findings: list[Finding]
) -> tuple[dict | None, str]:
    program_id = species.get("behavior", {}).get("program")
    own_path = species_dir / "behavior.json"
    if own_path.is_file():
        own = load_json(own_path, findings)
        if isinstance(own, dict) and own.get("id") == program_id:
            return own, "species"
        if isinstance(own, dict):
            findings.append(
                Finding("error", "ProgramIdMismatch", "behavior.program", f"species/{species_dir.name}/behavior.json id '{own.get('id')}' != '{program_id}'")
            )
    shared = load_shared_program(root, program_id, cache)
    if shared is not None:
        if shared.get("id") != program_id:
            findings.append(Finding("error", "ProgramFileIdMismatch", "behavior.program", f"behaviors/{program_id}.json id '{shared.get('id')}' != filename '{program_id}'"))
        return shared, "shared"
    findings.append(Finding("error", "ProgramNotFound", "behavior.program", f"program '{program_id}' resolves to neither species/{species_dir.name}/behavior.json nor behaviors/{program_id}.json"))
    return None, "missing"


def validate_species(
    species_dir: Path,
    root: Path,
    schemas: Schemas,
    cache: dict[str, Any | None],
    structural_done: set[str] | None = None,
) -> SpeciesReport:
    if structural_done is None:
        structural_done = set()
    slug = species_dir.name
    species_path = species_dir / "species.json"
    findings: list[Finding] = []
    species = load_json(species_path, findings)
    report = SpeciesReport(slug=slug, path=species_dir, species=species, findings=findings)
    if not isinstance(species, dict):
        return report

    findings.extend(schema_findings(species, schemas.species_schema, schemas, "species"))
    if species.get("format_version") != FORMAT_VERSION:
        findings.append(Finding("error", "FormatVersion", "format_version", f"unsupported format_version '{species.get('format_version')}'"))

    check_species_crossrefs(species, slug, findings)
    check_look(species, schemas.body_plans, findings)

    program, source = resolve_species_program(species, species_dir, root, cache, findings)
    if program is not None:
        prog_prefix = "behavior.program" if source == "shared" else "species.behavior.json"
        prog_findings: list[Finding] = []
        prog_findings.extend(schema_findings(program, schemas.behavior_schema, schemas, prog_prefix))
        declared_types = collect_declared_params(program, root, cache)
        overrides = species.get("behavior", {}).get("params", {})
        check_param_overrides(overrides, declared_types, "behavior.params", prog_findings)
        for i, phase in enumerate(species.get("seasonal", {}).get("phases", [])):
            phase_overrides = phase.get("behavior_params", {})
            if phase_overrides:
                check_param_overrides(phase_overrides, declared_types, f"seasonal.phases[{i}].behavior_params", prog_findings)

        # Full (structural) lint, program's own declared defaults -- run at
        # most once per program id across the whole `run()`, however many
        # species/standalone passes reference it (see `structural_done`).
        program_id = program.get("id", "?")
        own_defaults = collect_declared_param_values(program, root, cache)
        if program_id not in structural_done:
            lint_program(program, prog_prefix, own_defaults, prog_findings, root, cache, species=None, structural=True)
            structural_done.add(program_id)

        # Species instantiation lint, with overrides applied: only the
        # species-dependent checks (ranges after substitution, call ids,
        # food tags) -- never the structural findings again.
        effective_params = dict(own_defaults)
        effective_params.update(overrides)
        lint_program(
            program,
            f"{prog_prefix} (instantiated)",
            effective_params,
            prog_findings,
            root,
            cache,
            species=species,
            structural=False,
        )

        report.program_reports.append(
            ProgramReport(program_id=program.get("id", "?"), kind=program.get("kind", "?"), source=source, node_count=count_program_nodes(program), findings=prog_findings)
        )

    source_map = check_sources(species, schemas.licenses, findings)
    prov = check_provenance(species, source_map, schemas.licenses, findings)
    report.cleanliness = prov.cleanliness
    report.coverage = (prov.covered, prov.total)
    report.license_mix = prov.license_mix
    report.source_license_counts = prov.source_license_counts

    visual_check_path = species_dir / "visual-check.json"
    if visual_check_path.is_file():
        report.visual_check = load_json(visual_check_path, findings)

    return report


def validate_standalone_program(
    path: Path,
    root: Path,
    schemas: Schemas,
    cache: dict[str, Any | None],
    structural_done: set[str] | None = None,
) -> StandaloneProgramReport:
    if structural_done is None:
        structural_done = set()
    findings: list[Finding] = []
    program = load_json(path, findings)
    report = StandaloneProgramReport(path=path, program_id=None, findings=findings)
    if not isinstance(program, dict):
        return report
    report.program_id = program.get("id")
    findings.extend(schema_findings(program, schemas.behavior_schema, schemas, str(path)))
    if path.stem != program.get("id"):
        findings.append(Finding("error", "ProgramFileIdMismatch", str(path), f"file name '{path.stem}' != id '{program.get('id')}'"))
    cache.setdefault(program.get("id"), program)
    program_id = program.get("id")
    if program_id not in structural_done:
        own_defaults = collect_declared_param_values(program, root, cache)
        lint_program(program, str(path), own_defaults, findings, root, cache, species=None, structural=True)
        structural_done.add(program_id)
    return report


# ---------------------------------------------------------------------------
# Target discovery
# ---------------------------------------------------------------------------


def discover_targets(paths: list[str], root: Path) -> tuple[list[Path], list[Path], list[Finding]]:
    """Returns (species_dirs, standalone_program_files, usage_findings)."""
    findings: list[Finding] = []
    if not paths:
        species_dirs = sorted((root / "species").glob("*")) if (root / "species").is_dir() else []
        species_dirs = [p for p in species_dirs if p.is_dir()]
        programs = sorted((root / "behaviors").glob("*.json")) if (root / "behaviors").is_dir() else []
        return species_dirs, programs, findings

    species_dirs = []
    programs = []
    for raw in paths:
        p = Path(raw)
        candidates = [p]
        if not p.exists() and any(ch in raw for ch in "*?[]"):
            from glob import glob

            candidates = [Path(g) for g in glob(raw)]
        for candidate in candidates:
            if candidate.is_dir():
                species_dirs.append(candidate)
            elif candidate.name == "species.json":
                species_dirs.append(candidate.parent)
            elif candidate.name == "behavior.json" and (candidate.parent / "species.json").is_file():
                # A species' own behavior.json (species/<slug>/behavior.json)
                # is validated as part of that species, never as a standalone
                # shared program -- otherwise its id (which need not be
                # "behavior") gets compared against the filename "behavior"
                # and falsely flagged as ProgramFileIdMismatch.
                species_dirs.append(candidate.parent)
            elif candidate.suffix == ".json":
                programs.append(candidate)
            else:
                findings.append(Finding("error", "UsageError", raw, f"don't know how to validate '{raw}'"))

    # De-duplicate while preserving order, in case a species dir and its own
    # species.json/behavior.json were both named explicitly.
    species_dirs = list(dict.fromkeys(species_dirs))
    programs = list(dict.fromkeys(programs))
    return species_dirs, programs, findings


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def status_icon(findings: list[Finding]) -> str:
    if any(f.level == "error" for f in findings):
        return "❌"
    if any(f.level == "warning" for f in findings):
        return "⚠️"
    return "✅"


def render_plain(result: Result, strict: bool) -> str:
    lines: list[str] = []
    total_errors = 0
    total_warnings = 0
    for sr in result.species_reports:
        for f in sr.all_findings():
            lines.append(f.line())
            if f.level == "error":
                total_errors += 1
            elif f.level == "warning":
                total_warnings += 1
    for pr in result.program_reports:
        for f in pr.findings:
            lines.append(f.line())
            if f.level == "error":
                total_errors += 1
            elif f.level == "warning":
                total_warnings += 1
    n_targets = len(result.species_reports) + len(result.program_reports)
    lines.append(f"--- {n_targets} target(s): {total_errors} error(s), {total_warnings} warning(s) ---")
    return "\n".join(lines)


def render_visual_check_table(images: list[dict], target_label: str) -> list[str]:
    """Render the `images` array of a `visual-check.json` report (the exact
    shape `tools/visual_check.py`'s `build_report()` produces) as Markdown
    table lines: pose, yaw, top label, top score, target probability."""
    lines = ["| pose | yaw | top label | top score | target probability |", "|---|---|---|---|---|"]
    for img in images:
        probs = img.get("probabilities", {})
        target_prob = probs.get(target_label, 0.0)
        lines.append(
            f"| {img.get('pose', '?')} | {img.get('yaw', '?')} | {img.get('top_label', '?')} | "
            f"{img.get('top_score', 0.0):.3f} | {target_prob:.3f} |"
        )
    return lines


def render_markdown(result: Result) -> str:
    lines = ["# speeeecies validation report", ""]
    lines.append("| species | status | errors | warnings | cleanliness | provenance |")
    lines.append("|---|---|---|---|---|---|")
    for sr in result.species_reports:
        f = sr.all_findings()
        errs = sum(1 for x in f if x.level == "error")
        warns = sum(1 for x in f if x.level == "warning")
        cov = f"{sr.coverage[0]}/{sr.coverage[1]}" if sr.coverage else "-"
        clean = sr.cleanliness if sr.cleanliness is not None else "-"
        lines.append(f"| {sr.slug} | {status_icon(f)} | {errs} | {warns} | {clean} | {cov} |")
    lines.append("")

    for sr in result.species_reports:
        lines.append(f"## {sr.slug}")
        f = sr.all_findings()
        errors = [x for x in f if x.level == "error"]
        warnings_ = [x for x in f if x.level == "warning"]
        infos = [x for x in f if x.level == "info"]
        if errors:
            lines.append("### Errors")
            for e in errors:
                lines.append(f"- `{e.code}` {e.path}: {e.message}")
        if warnings_:
            lines.append("### Warnings")
            for w in warnings_:
                lines.append(f"- `{w.code}` {w.path}: {w.message}")
        if infos:
            lines.append("### Notes")
            for i in infos:
                lines.append(f"- `{i.code}` {i.path}: {i.message}")
        if sr.license_mix:
            lines.append("### Licence mix")
            lines.append("| tier | datums |")
            lines.append("|---|---|")
            for tier, count in sorted(sr.license_mix.items()):
                lines.append(f"| {tier} | {count} |")
        if sr.program_reports:
            lines.append("### Behaviour")
            lines.append("| program | kind | states/nodes |")
            lines.append("|---|---|---|")
            for pr in sr.program_reports:
                lines.append(f"| {pr.program_id} | {pr.kind} | {pr.node_count} |")
        if sr.visual_check:
            vc = sr.visual_check
            lines.append("### Visual check (advisory)")
            summary = vc.get("summary", {})
            target_label = vc.get("target_label", "?")
            lines.append(f"model: {vc.get('model', '?')} ({vc.get('model_license', '?')})")
            lines.append(
                f"target: {target_label}, mean target probability: {summary.get('mean_target_probability', '?')}, "
                f"rank-1 rate: {summary.get('rank1_rate', '?')} (n={summary.get('n_images', '?')})"
            )
            lines.extend(render_visual_check_table(vc.get("images", []), target_label))
        lines.append("")

    if result.program_reports:
        lines.append("## behaviors/*.json")
        lines.append("| program | errors | warnings |")
        lines.append("|---|---|---|")
        for pr in result.program_reports:
            errs = sum(1 for x in pr.findings if x.level == "error")
            warns = sum(1 for x in pr.findings if x.level == "warning")
            lines.append(f"| {pr.program_id or pr.path.name} | {errs} | {warns} |")
        for pr in result.program_reports:
            for x in pr.findings:
                lines.append(f"- `{x.code}` {x.path}: {x.message}")
        lines.append("")

    return "\n".join(lines)


def render_json(result: Result) -> dict:
    def finding_dict(f: Finding) -> dict:
        return {"level": f.level, "code": f.code, "path": f.path, "message": f.message}

    return {
        "species": [
            {
                "slug": sr.slug,
                "findings": [finding_dict(f) for f in sr.all_findings()],
                "cleanliness": sr.cleanliness,
                "coverage": list(sr.coverage) if sr.coverage else None,
                "license_mix": dict(sr.license_mix),
                "source_license_counts": dict(sr.source_license_counts),
                "programs": [
                    {"id": pr.program_id, "kind": pr.kind, "source": pr.source, "node_count": pr.node_count}
                    for pr in sr.program_reports
                ],
            }
            for sr in result.species_reports
        ],
        "programs": [
            {
                "path": str(pr.path),
                "id": pr.program_id,
                "findings": [finding_dict(f) for f in pr.findings],
            }
            for pr in result.program_reports
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def run(paths: list[str], root: Path) -> tuple[Result, list[Finding]]:
    schemas = Schemas(root)
    cache: dict[str, Any | None] = {}
    structural_done: set[str] = set()
    species_dirs, programs, usage_findings = discover_targets(paths, root)

    result = Result()
    for sd in species_dirs:
        result.species_reports.append(validate_species(sd, root, schemas, cache, structural_done))
    for p in programs:
        result.program_reports.append(validate_standalone_program(p, root, schemas, cache, structural_done))
    return result, usage_findings


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="speeeecies validator")
    parser.add_argument("paths", nargs="*", help="species dir(s), species.json, or behaviors/*.json")
    parser.add_argument("--report", action="store_true", help="print a Markdown report")
    parser.add_argument("--report-file", help="write the Markdown report to a file")
    parser.add_argument("--write-attribution", action="store_true", help="write species/<slug>/ATTRIBUTION.md")
    parser.add_argument("--json", action="store_true", help="print a machine-readable JSON result")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors for the exit code")
    parser.add_argument("--root", help="repository root override (for tests)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else default_root()

    try:
        result, usage_findings = run(args.paths, root)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if usage_findings:
        for f in usage_findings:
            print(f.line(), file=sys.stderr)
        return 2

    if args.write_attribution:
        for sr in result.species_reports:
            if isinstance(sr.species, dict):
                write_attribution(sr.species, sr.path, Schemas(root).licenses)

    if args.report_file:
        Path(args.report_file).write_text(render_markdown(result), encoding="utf-8")

    if args.json:
        print(json.dumps(render_json(result), indent=2))
    elif args.report:
        print(render_markdown(result))
    else:
        print(render_plain(result, args.strict))

    return 1 if result.has_errors(args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
