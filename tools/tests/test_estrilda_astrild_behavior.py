"""Keep the Common Waxbill program aligned with its seed diet and calendar."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPECIES_DIR = REPO_ROOT / "species" / "estrilda-astrild"


def test_seed_foraging_and_southern_african_nesting_window() -> None:
    species = json.loads((SPECIES_DIR / "species.json").read_text(encoding="utf-8"))
    program = json.loads((SPECIES_DIR / "behavior.json").read_text(encoding="utf-8"))

    assert species["behavior"]["program"] == program["id"]
    assert species["behavior"]["params"]["food_tag"] == "seed"

    nodes = program["root"]["selector"]
    forage = next(
        node["sequence"]
        for node in nodes
        if "sequence" in node
        and any(child.get("act", {}).get("do") == "eat_nearest" for child in node["sequence"])
    )
    eat = next(child["act"] for child in forage if child.get("act", {}).get("do") == "eat_nearest")
    assert eat["tag"] == "${food_tag}"
    assert eat["gait"] == "hop"

    nesting = next(
        node["sequence"]
        for node in nodes
        if "sequence" in node
        and any(child.get("act", {}).get("do") == "build_nest" for child in node["sequence"])
    )
    month_check = next(child["cond"]["month_in"] for child in nesting if child.get("cond", {}).get("month_in"))
    assert month_check == [9, 10, 11, 12, 1]

    night = next(
        node["sequence"]
        for node in nodes
        if "sequence" in node and any(child.get("cond", {}).get("is_day") is False for child in node["sequence"])
    )
    assert any(child.get("act", {}).get("do") == "rest" for child in night)
