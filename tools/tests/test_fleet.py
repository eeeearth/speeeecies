"""Tests for tools/agents/fleet.sh. Run with:
uv run --with pytest pytest tools/tests -q
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FLEET = REPO / "tools" / "agents" / "fleet.sh"
RECIPES = REPO / "tools" / "agents" / "recipes.md"

PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")


def render(tmp_path: Path, issue: str, slug: str, sci: str, regions: str) -> str:
    """Render a brief the way cmd_spawn does, without touching GitHub."""
    out = tmp_path / "brief.md"
    result = subprocess.run(
        [
            "bash", str(FLEET), "render-brief",
            "--issue", issue, "--slug", slug,
            "--scientific", sci, "--regions", regions,
            "--out", str(out),
        ],
        cwd=tmp_path,  # not the repo: config must resolve from the script dir
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(tmp_path),
            "GH_REPO": "jt55401/speeeecies",
            "BRANCH_PREFIX": "jt55401",
        },
    )
    assert result.returncode == 0, result.stderr
    return out.read_text(encoding="utf-8")


def test_templates_resolve_from_script_dir_not_cwd(tmp_path):
    """Regression: config resolved against the repo, so an unmerged harness
    invoked from the main checkout looked for tools/agents/ where it did not
    exist and refused to spawn."""
    brief = render(tmp_path, "9", "passer-montanus", "Passer montanus", "CN JP KR TW")
    assert "Brief: contribute one species record" in brief


def test_no_unsubstituted_placeholders(tmp_path):
    brief = render(tmp_path, "9", "passer-montanus", "Passer montanus", "CN JP KR TW")
    assert not PLACEHOLDER.search(brief), PLACEHOLDER.findall(brief)


def test_situation_fields_are_filled_in(tmp_path):
    brief = render(tmp_path, "9", "passer-montanus", "Passer montanus", "CN JP KR TW")
    assert "**#9**" in brief
    assert "passer-montanus" in brief
    assert "Passer montanus" in brief
    assert "`CN JP KR TW`" in brief
    assert "jt55401/species-9-passer-montanus" in brief


def test_recipe_is_injected(tmp_path):
    brief = render(tmp_path, "9", "passer-montanus", "Passer montanus", "CN JP KR TW")
    assert "## Your recipe for this issue" in brief
    assert "species/passer-domesticus/" in brief


def test_recipe_markers_do_not_prefix_match(tmp_path):
    """recipe:9 must not bleed into recipe:39."""
    brief9 = render(tmp_path, "9", "passer-montanus", "Passer montanus", "CN JP KR TW")
    assert "Weddell seal" not in brief9
    brief39 = render(tmp_path, "39", "leptonychotes-weddellii", "Leptonychotes weddellii", "AQ")
    assert "Weddell seal" in brief39
    assert "Eurasian tree sparrow" not in brief39


def test_unknown_issue_gets_explicit_no_recipe_note(tmp_path):
    brief = render(tmp_path, "9999", "unknown-thing", "Unknown thing", "GB")
    assert "No researched recipe for issue #9999" in brief


def test_recipes_file_covers_every_queued_issue():
    """Each recipe marker must name a species heading, so a stray marker with
    no body is caught rather than silently shipping an empty recipe."""
    text = RECIPES.read_text(encoding="utf-8")
    open_markers = re.findall(r"^<!-- recipe:(\d+) -->$", text, re.M)
    close_markers = re.findall(r"^<!-- /recipe:(\d+) -->$", text, re.M)
    assert open_markers, "no recipes found"
    assert sorted(open_markers) == sorted(close_markers), "unbalanced recipe markers"
    for issue in open_markers:
        body = text.split(f"<!-- recipe:{issue} -->")[1].split(f"<!-- /recipe:{issue} -->")[0]
        assert body.strip(), f"recipe:{issue} is empty"
        assert body.lstrip().startswith("###"), f"recipe:{issue} has no heading"


def test_recipe_bodies_are_unescaped(tmp_path):
    """Recipe text carries slashes and ampersands; a sed-based renderer would
    have corrupted them."""
    brief = render(tmp_path, "26", "salvator-merianae", "Salvator merianae", "AR BR")
    assert "Ectotherm" in brief
    assert "leg_length_ratio" in brief


def test_model_pool_excludes_proven_dead_model():
    """ling-3.0-flash-fin-free answers 'Cannot find any route matching'. It must
    not return to the pool, or the supervisor burns a slot on it every cycle."""
    text = FLEET.read_text(encoding="utf-8")
    pool = re.search(r"MODEL_POOL=\((.*?)\n\)", text, re.S)
    assert pool, "MODEL_POOL not found"
    assert "ling-3.0-flash-fin-free" not in pool.group(1)


def test_script_is_syntactically_valid():
    result = subprocess.run(["bash", "-n", str(FLEET)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
