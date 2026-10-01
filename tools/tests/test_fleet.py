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


def model_pool(provider: str | None = None) -> list[str]:
    """The model ids in one provider pool, in rotation order."""
    text = FLEET.read_text(encoding="utf-8")
    if provider is not None:
        pool = re.search(rf"MODEL_POOL_{provider.upper()}=\((.*?)\n\)", text, re.S)
    else:
        pools = re.findall(r"MODEL_POOL_(?:ZEN|GO)=\((.*?)\n\)", text, re.S)
        assert pools, "no provider pools found"
        return [m for p in pools for m in re.findall(r'"([^"]+)"', p)]
    assert pool is not None, f"MODEL_POOL_{provider.upper()} not found"
    return re.findall(r'"([^"]+)"', pool.group(1))


def test_provider_pool_ratio_is_usable():
    """Zen holds six routes and Go only two, so the pool cannot be even. Rotation
    has to alternate providers rather than walk one list, or the fleet serves
    three zen spawns per go one and exhausts the zen quota first."""
    zen, go = model_pool("zen"), model_pool("go")
    assert zen and go, "one provider pool is empty"
    assert len(go) >= 2, "go pool too small to alternate against a large zen pool"


def _rotation(tmp_path, body: str) -> str:
    """Run the real provider rotation against a throwaway state dir."""
    text = FLEET.read_text(encoding="utf-8")
    pools = re.findall(r"MODEL_POOL_(?:ZEN|GO)=\((.*?)\n\)", text, re.S)
    assert len(pools) == 2, "expected exactly one pool per provider"
    funcs = re.search(
        r"provider_of\(\) \{.*?\n\}\n.*?advance_model\(\) \{.*?\n\}\n", text, re.S
    )
    assert funcs, "could not find the provider rotation functions"
    script = (
        "set -euo pipefail\n"
        f'STATE_DIR="{tmp_path}"\n'
        + "MODEL_POOL_ZEN=(\n" + pools[0] + "\n)\n"
        + "MODEL_POOL_GO=(\n" + pools[1] + "\n)\n"
        + funcs.group(0)
        + body
    )
    out = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, check=True
    ).stdout
    return out


def test_rotation_alternates_providers_across_spawns(tmp_path):
    """One zen and one go spawn per cycle, whatever the pool sizes."""
    picks = _rotation(tmp_path, "for i in 1 2 3 4 5 6; do next_model; echo; advance_model; done")
    providers = ["go" if m.startswith("opencode-go/") else "zen" for m in picks.split()]
    assert providers == ["zen", "go", "zen", "go", "zen", "go"], providers


def test_next_model_does_not_consume_a_turn(tmp_path):
    """The status line calls next_model every poll to show the next model. If
    that advanced the rotation, merely looking at the fleet would skew it."""
    picks = _rotation(tmp_path, "next_model; echo; next_model; echo")
    first, second = picks.split()
    assert first == second, f"peek consumed a turn: {first} then {second}"


def test_a_failing_provider_is_skipped_for_one_turn(tmp_path):
    """A rate-limited provider must not stall the fleet; the other one takes the
    slot and the rotation resumes on the original provider afterwards."""
    out = _rotation(
        tmp_path,
        'touch "$STATE_DIR/provider_fail_zen"\n'
        'next_model; echo\nadvance_model\nnext_model; echo',
    )
    skipped, resumed = out.split()
    assert skipped.startswith("opencode-go/"), f"did not back off: {skipped}"
    assert resumed.startswith("opencode/") and not resumed.startswith("opencode-go/"), (
        f"did not resume zen: {resumed}"
    )


def test_route_failure_backs_off_the_provider_that_hit_it(tmp_path):
    """A delegate that dies on routing must not cost the next slot the same dead
    route. The reap marks the provider from the model that failed."""
    text = FLEET.read_text(encoding="utf-8")
    funcs = re.search(
        r"provider_note_failure\(\) \{.*?\n\}\n.*?note_route_failure\(\) \{.*?\n\}\n", text, re.S
    )
    assert funcs, "could not find the route-failure helpers"
    state = tmp_path / "state"
    state.mkdir()
    (state / "leptonychotes-weddellii.meta").write_text("model=opencode-go/space-bunny-free\n")
    (state / "leptonychotes-weddellii.log").write_text(
        "Error: Cannot find any route matching opencode-go/space-bunny-free\n"
    )
    meta_get = 'meta_get() { sed -n "s/^$2=//p" "$STATE_DIR/$1.meta" 2>/dev/null | head -1; }\n'
    script = (
        "set -euo pipefail\n"
        f'STATE_DIR="{state}"\n'
        + meta_get
        + funcs.group(0)
        + 'note_route_failure leptonychotes-weddellii\n'
        + 'ls "$STATE_DIR" | grep provider_fail | sed "s/provider_fail_//"\n'
    )
    out = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "go", f"backed off the wrong provider: {out.strip()!r}"


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


def test_spawn_retries_a_leftover_branch_instead_of_dying():
    """cmd_spawn is called directly from the refill loop and die() calls exit, so
    dying on a leftover branch ends the whole supervisor. Teardown keeps the
    branch of a no-PR failure on purpose, and the retry filter re-picks exactly
    those slugs, so this path is reached routinely."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}", 1)[0]
    assert 'die "branch $branch exists' not in spawn, (
        "an existing branch is a retry, not a fatal collision"
    )
    assert "branch_flag=-B" in spawn, "a retry must reset the leftover branch"
    assert 'worktree add "$branch_flag"' in spawn, (
        "worktree add must use the chosen flag rather than a hardcoded -b"
    )


def test_spawn_failure_cannot_exit_the_supervisor():
    """cmd_spawn dies on several conditions and die() calls exit. Run bare from
    the refill loop, any of them ends the whole fleet; this actually happened
    when a respawn hit an existing worktree path."""
    text = FLEET.read_text(encoding="utf-8")
    refill = text.split("# Refill to the floor", 1)[1]
    assert "( cmd_spawn --issue" in refill, (
        "cmd_spawn must run in a subshell so a die() cannot exit the supervisor"
    )


def _queue_filter(
    queue: Path, candidates: str, max_attempts: int = 3, busy: str = ""
) -> str:
    """Run the awk the refill loop actually ships, extracted from fleet.sh so a
    test cannot pass while the real filter does something else."""
    text = FLEET.read_text(encoding="utf-8")
    # Capture the whole program between the opening quote after the -v options
    # and the closing quote before the input files. Anchoring on a rule body
    # instead would silently drop a leading BEGIN block.
    awk_body = re.search(
        r"awk -F'\\t'.*?'\n(.*?)\n\s*' \"\$STATE_DIR/queue\.tsv\" -\)",
        text,
        re.S,
    )
    assert awk_body, "could not find the queue filter in fleet.sh"
    program = awk_body.group(1)
    assert "BEGIN" in program, "extracted awk program is missing its BEGIN block"
    return subprocess.run(
        [
            "awk", "-F\t", "-v", f"q={queue}", "-v", f"max={max_attempts}",
            "-v", f"busy={busy}", program, str(queue), "-",
        ],
        input=candidates,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_queue_filter_never_offers_a_slug_with_a_live_agent(tmp_path):
    """A running agent is under its attempt budget, so the retry filter made its
    own slug a candidate. Respawning it hit "worktree path already exists",
    and die() there exits the whole supervisor. The fleet died this way."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("37\tadeliae\n", encoding="utf-8")
    candidates = "37\tadeliae\ta\n38\temperor\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3, busy="adeliae")

    assert "adeliae" not in filtered, "a live agent was offered its own slug"
    assert "emperor" in filtered


def test_queue_filter_excludes_a_slug_that_exhausted_its_attempts(tmp_path):
    """A slug is skipped only once it has burned the whole budget, so a flaky
    model route does not retire an issue for the life of the queue."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("39\tweddellii\n39\tweddellii\n39\tweddellii\n", encoding="utf-8")
    candidates = "39\tweddellii\ta\n38\temperor\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3)

    assert "weddellii" not in filtered, "exhausted slug was re-offered"
    assert "emperor" in filtered, "untried slug was withheld"


def test_queue_filter_retries_a_slug_that_failed_under_budget(tmp_path):
    """Two prior attempts is a transient failure, not a dead issue. The old
    presence-only filter retired it forever, which starved the pool over a
    long run."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("38\temperor\n38\temperor\n", encoding="utf-8")
    candidates = "38\temperor\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3)

    assert "emperor" in filtered, "a slug under its attempt budget must stay pickable"


def test_queue_filter_allows_exactly_max_attempts_then_stops(tmp_path):
    """The budget is a boundary: max-1 tries stays pickable, max does not."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("38\temperor\n38\temperor\n", encoding="utf-8")
    candidates = "38\temperor\tb\n"

    assert "emperor" in _queue_filter(queue, candidates, max_attempts=3)
    assert "emperor" not in _queue_filter(queue, candidates, max_attempts=2)


def test_pr_field_never_dereferences_bare_third_argument():
    """The reap loop calls pr_field with a jq expression, but a bare $3 is fatal
    under `set -u` and that killed the supervisor the first time an agent
    finished, which is precisely when the reap loop has to work."""
    text = FLEET.read_text(encoding="utf-8")
    body = text.split("pr_field() {", 1)[1].split("\n}", 1)[0]
    assert '-q "$3"' not in body, "pr_field still dereferences a bare $3"
    assert '${3:-' in body, "pr_field should default its jq expression"


def test_reap_loop_requests_a_hash_prefixed_pr_label():
    """Reap matches \\#* to tell "finished with a PR" from "died with none". A bare
    number would fall into the NO PR branch and tear down a healthy agent."""
    text = FLEET.read_text(encoding="utf-8")
    reap = text.split("# Reap:", 1)[1].split("done", 1)[0]
    assert re.search(r'pr_field\s+"\$slug"\s+number(?:,\w+)*\s+\S', reap), (
        "reap must pass a jq expression that yields a #-prefixed label"
    )


def test_pr_field_jq_only_touches_requested_fields():
    """`gh pr view --json <fields>` only returns the fields it was asked for, so
    a jq expression that interpolates anything else silently renders `null`.
    Every reap logged "finished: #99 null" because it read .state from a
    response that only carried number.

    Only the root of a chain counts: `.statusCheckRollup[]?.conclusion` needs
    `statusCheckRollup` requested, not `conclusion`."""
    text = FLEET.read_text(encoding="utf-8")
    calls = re.findall(r'pr_field\s+"[^"]+"\s+([\w,]+)\s+(\'[^\']*\'|"[^"]*")', text)
    assert calls, "found no pr_field call sites to check"
    for fields, jq_expr in calls:
        requested = {f.strip() for f in fields.split(",")}
        chains = re.findall(r"((?:\??\.[A-Za-z_]\w*(?:\[\])?)+)", jq_expr)
        assert chains, f"no field access found in jq expression {jq_expr}"
        for chain in chains:
            root = re.findall(r"[A-Za-z_]\w*", chain)[0]
            assert root in requested, (
                f"jq reads {chain} rooted at .{root} but pr_field only "
                f"requested {sorted(requested)}"
            )


def test_teardown_reports_whether_a_pr_actually_exists():
    """Teardown used to say "branch kept because it is the PR" unconditionally, so
    an agent that died without opening one looked delivered and its issue was
    never re-queued. The claim must be conditional on a real PR."""
    text = FLEET.read_text(encoding="utf-8")
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}", 1)[0]
    assert 'if pr_for_slug "$slug"; then' in teardown, (
        "teardown must check for a real PR before claiming the branch is one"
    )
    assert "NO PR was opened" in teardown, "teardown should say so when no PR exists"


def test_teardown_keeps_the_log_when_no_pr_was_opened():
    """Two of four agents died with zero commits and teardown had already
    destroyed their logs, leaving no way to tell why. A failed agent's log is
    the only diagnostic record of the failure."""
    text = FLEET.read_text(encoding="utf-8")
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}", 1)[0]
    bulk_rm, _, branches = teardown.partition("if pr_for_slug")
    assert "$slug.log" not in bulk_rm, (
        "the unconditional rm must not delete the agent log"
    )
    assert 'rm -f "$STATE_DIR/$slug.log"' in branches, (
        "a successful agent's log may be discarded, but only on the PR branch"
    )
    assert "log kept for diagnosis" in teardown, (
        "a failed teardown should point the operator at the retained log"
    )


def test_script_is_syntactically_valid():
    result = subprocess.run(["bash", "-n", str(FLEET)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
