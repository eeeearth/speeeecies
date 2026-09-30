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


def model_pool() -> list[str]:
    """The model ids in MODEL_POOL, in rotation order."""
    pool = re.search(r"MODEL_POOL=\((.*?)\n\)", FLEET.read_text(encoding="utf-8"), re.S)
    assert pool is not None, "MODEL_POOL not found"
    return re.findall(r'"([^"]+)"', pool.group(1))


def test_model_pool_excludes_proven_dead_model():
    """ling-3.0-flash-fin-free answers 'Cannot find any route matching'. It must
    not return to the pool, or the supervisor burns a slot on it every cycle."""
    assert "ling-3.0-flash-fin-free" not in model_pool()


def test_model_pool_is_free_tier_only():
    """The pool exists to spread load across free quotas. One paid model in it
    quietly spends the account's money, which is the opposite of the point."""
    models = model_pool()
    assert len(models) >= 4, "pool too small to spread quota"
    for m in models:
        assert m.startswith(("opencode/", "opencode-go/")), f"{m} is not an opencode provider"
        assert m.endswith("-free"), f"{m} is not a free-tier model"


def test_model_pool_interleaves_both_providers():
    """The same weights under opencode/ and opencode-go/ are separate quota
    buckets, so both must appear or one aggregate limit absorbs all the load."""
    models = model_pool()
    assert any(m.startswith("opencode/") for m in models), "no zen models"
    assert any(m.startswith("opencode-go/") for m in models), "no opencode-go models"


def test_worktree_root_defaults_beside_the_checkout():
    """Worktrees must land in a worktrees/ sibling of the repo, not under $HOME,
    or a run scatters checkouts across the home directory."""
    text = FLEET.read_text(encoding="utf-8")
    assert 'WORKTREE_ROOT=${WORKTREE_ROOT:-$(dirname "$REPO")/worktrees}' in text, (
        "WORKTREE_ROOT default regressed away from the project directory"
    )


def test_live_count_does_not_use_bare_ls_glob():
    """nullglob is set in the reap loop, so an unmatched "$STATE_DIR"/*.meta glob
    expands to zero words and bare `ls` lists the cwd instead. The repo root has
    14 entries, which read as fleet=14 >= FLEET_MIN and suppressed every refill."""
    text = FLEET.read_text(encoding="utf-8")
    assert 'live=$(ls "$STATE_DIR"/*.meta' not in text, (
        "live-count regressed to a nullglob-unsafe ls glob"
    )
    assert 'local metas=("$STATE_DIR"/*.meta)' in text, (
        "live-count should use an array glob"
    )
    assert "live=${#metas[@]}" in text, "live-count should use the array length"


def test_queue_filter_keeps_candidates_when_queue_file_is_empty(tmp_path):
    """A first run has an empty queue.tsv. With an empty first file, NR and FNR
    advance in lockstep, so an NR==FNR guard stays true for every row and the
    whole queue is swallowed as already-tried: the fleet never spawns anything."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("", encoding="utf-8")
    candidates = "39\tweddellii\ta\n38\temperor\tb\n37\tadeliae\tc\n"

    filtered = subprocess.run(
        [
            "awk", "-F\t", "-v", f"q={queue}",
            'FILENAME == q { if ($2 != "") seen[$2] = 1; next } !($2 in seen)',
            str(queue), "-",
        ],
        input=candidates,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert len(filtered.strip().splitlines()) == 3, "empty queue swallowed every candidate"
    assert "weddellii" in filtered


def test_queue_filter_still_excludes_already_attempted(tmp_path):
    """The filter must keep its original job: never re-pick a slug already tried."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("39\tweddellii\n", encoding="utf-8")
    candidates = "39\tweddellii\ta\n38\temperor\tb\n"

    filtered = subprocess.run(
        [
            "awk", "-F\t", "-v", f"q={queue}",
            'FILENAME == q { if ($2 != "") seen[$2] = 1; next } !($2 in seen)',
            str(queue), "-",
        ],
        input=candidates,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert "weddellii" not in filtered, "already-attempted slug was re-offered"
    assert "emperor" in filtered


def test_script_is_syntactically_valid():
    result = subprocess.run(["bash", "-n", str(FLEET)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
