"""Regression checks for the Hermit Thrush record's executable behaviour.

Asserts the nest-month set and the reachable food actions, which the shared
perching-songbird program gets wrong for this species (April nesting and no
berry action). Reads the committed JSON only; no network.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECIES = ROOT / "species" / "catharus-guttatus"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _actions(node, out):
    if isinstance(node, dict):
        if "act" in node:
            out.append(node["act"])
        for value in node.values():
            _actions(value, out)
    elif isinstance(node, list):
        for item in node:
            _actions(item, out)
    return out


def _month_sets(node, out):
    if isinstance(node, dict):
        if "month_in" in node:
            out.append(node["month_in"])
        for value in node.values():
            _month_sets(value, out)
    elif isinstance(node, list):
        for item in node:
            _month_sets(item, out)
    return out


def test_nest_months_are_may_to_july_only():
    record = _load(SPECIES / "species.json")
    program = _load(SPECIES / "behavior.json")
    params = {**program.get("params", {}), **record["behavior"].get("params", {})}
    sets = _month_sets(program["root"], [])
    assert len(sets) == 1
    months = set()
    for entry in sets[0]:
        months.add(params[entry[2:-1]] if isinstance(entry, str) and entry.startswith("${") else entry)
    assert months == {5, 6, 7}
    assert 4 not in months


def test_berry_and_invertebrate_food_actions_are_reachable():
    record = _load(SPECIES / "species.json")
    program = _load(SPECIES / "behavior.json")
    params = {**program.get("params", {}), **record["behavior"].get("params", {})}
    tags = set()
    for act in _actions(program["root"], []):
        if act.get("do") == "eat_nearest":
            tag = act["tag"]
            tags.add(params[tag[2:-1]] if tag.startswith("${") else tag)
    assert tags == {"invertebrate", "berry"}
    food_tags = {r["tag"] for r in record["habitat"]["resources"] if r["kind"] == "Herbivory" or r["kind"] == "Predation"}
    assert tags <= food_tags
