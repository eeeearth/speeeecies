import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = ROOT / "species" / "emberiza-schoeniclus"


def load_json(path):
    return json.loads(path.read_text())


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def action_branches(program, action):
    return [
        node["sequence"]
        for node in walk(program["root"])
        if "sequence" in node
        and any(
            child.get("act", {}).get("do") == action
            for child in walk(node["sequence"])
        )
    ]


def month_sets(branch):
    return [
        node["cond"]["month_in"]
        for node in walk(branch)
        if "cond" in node and "month_in" in node["cond"]
    ]


def test_reed_bunting_behavior_matches_its_seasonal_diet_and_roosting():
    species = load_json(SPECIES_DIR / "species.json")
    program = load_json(SPECIES_DIR / "behavior.json")
    roots = program["root"]["selector"]

    nest = action_branches(program, "build_nest")
    song = action_branches(program, "sing")
    insects = action_branches(program, "eat_nearest")

    assert month_sets(nest) == [[4, 5, 6, 7, 8]]
    assert month_sets(song) == [[4, 5, 6, 7, 8]]
    assert any(
        node.get("cond", {}).get("is_day") is True
        for node in walk(song)
    )
    food_branches = [
        branch
        for branch in insects
        if any(
            node.get("act", {}).get("tag") in {"seed", "invertebrate"}
            for node in walk(branch)
        )
    ]
    assert month_sets(food_branches) == [[4, 5, 6, 7, 8], [1, 2, 3, 9, 10, 11, 12]]
    assert [
        next(
            node["act"]["tag"]
            for node in walk(branch)
            if node.get("act", {}).get("do") == "eat_nearest"
        )
        for branch in food_branches
    ] == ["invertebrate", "seed"]

    night_branch = next(
        index
        for index, branch in enumerate(roots)
        if any(
            node.get("cond", {}).get("is_day") is False
            for node in walk(branch)
        )
    )
    assert night_branch < min(
        index
        for index, branch in enumerate(roots)
        if any(
            node.get("act", {}).get("do") == "eat_nearest"
            for node in walk(branch)
        )
    )
    assert any(
        node.get("act", {}).get("do") == "rest"
        for node in walk(roots[night_branch])
    )

    used_gaits = {
        node["act"]["gait"]
        for node in walk(program["root"])
        if node.get("act", {}).get("gait")
    }
    assert used_gaits == {"hop", "fly"}
    assert used_gaits <= {mode.lower() for mode in species["traits"]["locomotion_modes"]}
    assert {"idle", "hop", "fly", "perched"} <= set(species["look"]["poses"])
