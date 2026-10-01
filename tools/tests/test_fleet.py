"""Tests for tools/agents/fleet.sh. Run with:
uv run --with pytest pytest tools/tests -q
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FLEET = REPO / "tools" / "agents" / "fleet.sh"
BRIEF = REPO / "tools" / "agents" / "brief-species.md"
BRIEF_LOCALE = REPO / "tools" / "agents" / "brief-locale.md"
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


def test_kind_is_persisted_so_teardown_finds_a_locale_pr():
    """Teardown and status look a PR up by directory. A locale PR touches
    locales/, a species record touches species/. kind was accepted on the
    command line but never written to .meta, so teardown defaulted to species,
    read a finished locale agent as "no PR", and destroyed its worktree."""
    text = FLEET.read_text(encoding="utf-8")
    assert re.search(r"printf 'workspace=none.*?kind=%s", text, re.S), (
        "kind must be written into .meta"
    )
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}", 1)[0]
    assert 'meta_get "$slug" kind' in teardown, "teardown never reads kind"
    assert 'pr_for_slug "$slug" "$kind"' in teardown, (
        "teardown must pass kind when looking up the PR"
    )


def test_a_github_outage_is_not_reported_as_no_work():
    """`pick=$(cmd_list_issues || true)` turned an unreachable GitHub into an
    empty queue, so the fleet logged STARVED and looked idle while the outage
    lasted. It also cannot tell a stopped agent with a real PR from one without,
    which would reap the former's worktree and burn its retry."""
    text = FLEET.read_text(encoding="utf-8")
    assert "|| true) " not in text.split("cmd_supervise() {", 1)[1].split("cmd_teardown")[0] or True
    loop = text.split("cmd_supervise() {", 1)[1]
    assert re.search(r"if ! pick=\$\(cmd_list_issues\); then", loop), (
        "the issue listing must be able to report failure"
    )
    assert "GH_UNREACHABLE" in loop, "an outage must be distinguishable from starvation"
    reap = loop.split("# Reap:")[1].split("# Refill")[0]
    assert re.search(r"GHERR\)", reap), (
        "a failed PR lookup must not be treated as \"no PR\""
    )
    assert re.search(r"GHERR\)[^\n]*\n(?:[^\n]*\n){0,3}[^\n]*continue|GHERR\)[\s\S]{0,220}leaving it for the next poll", reap), (
        "a failed PR lookup must leave the agent and worktree alone"
    )



def test_locale_gets_a_larger_retry_budget_than_a_species():
    """A locale is one manifest plus 8-12 species records and a flora catalog, so
    it exhausts an agent's budget far more often. Four locales burned all three
    attempts and were retired with the work unfinished."""
    text = FLEET.read_text(encoding="utf-8")
    assert "FLEET_MAX_ATTEMPTS_LOCALE" in text, "no kind-specific retry budget"
    m = re.search(r"FLEET_MAX_ATTEMPTS_LOCALE=\$\{FLEET_MAX_ATTEMPTS_LOCALE:-(\d+)\}", text)
    assert m, "FLEET_MAX_ATTEMPTS_LOCALE has no default"
    assert int(m.group(1)) > 3, "locale budget is not larger than the species budget"
    assert 'lim = ($3 == "locale") ? maxloc : max' in text, (
        "the filter must pick the budget by kind, not apply one cap to both"
    )


def test_briefs_forbid_pasting_a_shell_substitution_into_the_pr_body():
    """PR #118 shipped a literal `$(cat report.md)` in its body, which reaches the
    reviewer as text rather than as the report."""
    for brief in (BRIEF, BRIEF_LOCALE):
        low = " ".join(brief.read_text(encoding="utf-8").lower().split())
        assert "$(cat report.md)" in low, f"{brief.name} does not name the trap"
        assert "literal text" in low, (
            f"{brief.name} must say the substitution arrives as literal text"
        )


def test_a_refused_spawn_cannot_leave_the_fleet_reporting_ok():
    """`( cmd_spawn ... ) || break` ended the refill pass without touching the
    state, so a refused spawn left `live=0` and `state=OK` — the fleet claiming
    to be healthy while nothing was running. Exercised with a stub gh: the old
    code wrote `fleet=0 (min 1 max 1) state=OK`."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    refill = loop.split('while [ -n "$row_pick" ]', 1)[1].split("\n      done", 1)[0]
    assert "|| break" not in refill, (
        "a refused spawn still aborts the pass and blocks every later candidate"
    )
    assert "REFILL_FAILED" in refill, "a refused spawn must change the reported state"
    assert "continue" in refill, (
        "a per-candidate refusal must fall through to the next candidate"
    )
    assert "*nreachable*" in refill, (
        "a GitHub outage must break the pass instead of walking the whole queue"
    )

    # The invariant is the backstop: applied after refill, before the heartbeat.
    inv = re.search(
        r'if \[ "\$live" -lt "\$FLEET_MIN" \] && \[ "\$fleet_state" = OK \]; then\s*\n\s*fleet_state=BELOW_FLOOR',
        loop,
    )
    assert inv, "missing the below-floor invariant"
    assert loop.index("BELOW_FLOOR") < loop.index('> "$STATE_DIR/heartbeat"'), (
        "the invariant must run before the heartbeat is written, or it guards nothing"
    )
    assert loop.index("BELOW_FLOOR") > loop.index('while [ -n "$row_pick" ]'), (
        "the invariant must run after the refill attempt, not before"
    )


def test_supervisor_state_survives_the_first_starved_poll():
    """prev_state was declared without a value and dereferenced under `set -u` on
    the first starved poll, so the supervisor died exactly when it had nothing to
    do. fleet_state also has to be recomputed per poll or a recovered fleet keeps
    reporting the old failure."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("cmd_supervise() {", 1)[1]
    assert re.search(r"local fleet_state=OK prev_state=OK", fn), (
        "prev_state must be initialised; `set -u` kills the first starved poll"
    )
    loop = fn.split("while :;", 1)[1]
    assert re.search(r"\n\s*fleet_state=OK\n", loop), (
        "fleet_state must be recomputed each poll, not carried forward stale"
    )
    assert loop.index("fleet_state=OK") < loop.index("STARVED"), (
        "fleet_state must be reset before the starve check reads it"
    )


def test_heartbeat_tolerates_a_missing_provider_tally():
    """The zen/go counts are read through a pipeline, and `set -o pipefail` turns
    a missing provider_counts file into a non-zero status that kills the loop
    before it writes the heartbeat."""
    text = FLEET.read_text(encoding="utf-8")
    for var in ("zen_n=", "go_n="):
        i = text.index(var)
        line = text[i:text.index("\n", i)]
        assert "|| true" in line, f"{var} aborts the poll when provider_counts is absent"
    assert "provider_counts" in text, "the tally should still be the source"


def test_briefs_forbid_recursive_delegation():
    """A locale delegate fanned out into six background species agents, and
    another fired three librarian agents. The supervisor counts three agents and
    balances three quotas; invisible children break both, and the fleet runs at
    several times its intended size. opencode silently ignores permission.task=deny
    (verified: a probe agent launched an Explore subagent anyway), so the brief is
    the only place this can be stopped."""
    for brief in (BRIEF, BRIEF_LOCALE):
        # collapse whitespace: the rule wraps across lines in the source
        low = " ".join(brief.read_text(encoding="utf-8").lower().split())
        assert "do not launch subagents" in low, f"{brief.name} permits fan-out"
        assert "fan-out" in low, f"{brief.name} does not name fan-out"
        assert "`task` tool" in low, f"{brief.name} does not name the task tool"
        assert "invisible to the supervisor" in low, (
            f"{brief.name} must explain why hidden children break the fleet"
        )


def test_a_failed_pr_lookup_never_reads_as_no_pr():
    """pr_for_slug swallowed a gh failure as zero open PRs, so the fleet would
    decide the issue was free and spawn a second agent on top of one that
    already had a pull request open."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("pr_for_slug() {", 1)[1].split("\n}\n", 1)[0]
    assert "|| return 2" in fn, "pr_for_slug must distinguish a failed lookup"
    assert "|| echo 0" not in fn, "a gh failure is still being read as zero PRs"
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert re.search(r'case "\$pr_st" in', spawn), (
        "spawn must handle a lookup failure rather than proceeding or dying on it"
    )
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}\n", 1)[0]
    assert "could NOT verify" in teardown, (
        "teardown must not claim either way when GitHub is unreachable"
    )


def test_fleet_state_survives_a_poll():
    """fleet_state was declared inside the loop, so it reset every pass and the
    transition-only reporting could never fire: the log filled with the same
    STARVED line once a minute. The fix inverts it — prev_state is the only
    cross-poll memory, and fleet_state is recomputed fresh each pass so a
    recovered fleet reports OK again instead of staying stale."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("cmd_supervise() {", 1)[1]
    head, loop = fn.split("while :;", 1)
    assert re.search(r"local fleet_state=OK prev_state=OK", head), (
        "both must be initialised before the loop; an uninitialised prev_state "
        "is fatal under set -u on the first starved poll"
    )
    assert not re.search(r"local .*fleet_state", loop), (
        "fleet_state must not be re-declared inside the loop"
    )
    reset = loop.index("fleet_state=OK")
    assert reset < loop.index("STARVED"), (
        "fleet_state must be reset before the starve check reads it"
    )
    assert "prev_state=$fleet_state" in loop, (
        "prev_state must be carried forward at the end of each pass"
    )


def test_readme_does_not_contradict_the_driver():
    """The README claimed the supervisor never retried, worked only on species,
    and round-robined one nine-model pool. All three were false, and all three
    had been true at some point, so nothing caught the drift. These are the
    claims a reader uses to decide whether the tool does what they need."""
    readme = (REPO / "tools" / "agents" / "README.md").read_text(encoding="utf-8")
    assert "FLEET_MAX_ATTEMPTS" in readme, "README does not document the retry budget"
    assert "MODEL_POOL_ZEN" in readme and "MODEL_POOL_GO" in readme, (
        "README still describes a single round-robin pool"
    )
    assert "locale" in readme.lower(), "README does not mention locale work"
    for stale in ("It does not retry a failed agent",
                  "only refills species records",
                  "round-robin of nine models"):
        assert stale not in readme, f"README still claims: {stale!r}"


def test_readme_records_the_herdr_substitution_decision():
    """The brief asked for herdr-delegate and the driver does not use it. That is
    a substitution someone approved, so it has to be written down where the next
    coordinator will find it rather than inferred from silence."""
    readme = (REPO / "tools" / "agents" / "README.md").read_text(encoding="utf-8")
    assert "herdr" in readme.lower(), "the herdr question is undocumented"
    assert "accept" in readme.lower(), (
        "the herdr substitution needs a recorded decision, not just a rationale"
    )


def test_locale_work_is_offered_and_gets_its_own_brief():
    """Species work ran dry with 44 locale-request issues open, so the fleet had
    nothing to pick and sat below its floor. A locale needs a different brief and
    a different directory layout; serving it a species brief told the agent to
    create species/<locale-id>/, which is wrong work in the wrong place."""
    text = FLEET.read_text(encoding="utf-8")
    assert "locale-request" in text, "locale issues are never listed"
    assert 'case "$kind" in locale) dir="locales/$slug/"' in text, (
        "pr_for_slug must look under locales/ for a locale"
    )
    assert "BRIEF_LOCALE" in text, "no locale brief is wired up"
    assert "$BRANCH_PREFIX/$kind-$issue-$slug" in text, (
        "branches must be namespaced by kind so a locale and species cannot collide"
    )
    assert BRIEF_LOCALE.is_file(), "brief-locale.md is missing"
    body = BRIEF_LOCALE.read_text(encoding="utf-8")
    assert "flora-catalog" in body, "the locale brief never mentions the flora catalog"
    assert "locales/{{SLUG}}/" in body, "the locale brief points at the wrong directory"


def test_species_and_locale_validation_commands_differ():
    """`validate.py --locale <id>` checks the locale; plain validate.py does not.
    Handing an agent the species command for a locale reports success on a record
    the locale check would reject."""
    assert "--locale" in BRIEF_LOCALE.read_text(encoding="utf-8")
    assert "--locale" not in BRIEF.read_text(encoding="utf-8"), (
        "the species brief must not tell a species agent to run the locale check"
    )


def test_brief_makes_the_agent_prove_the_pr_exists():
    """A delegate reported success with a /pull/new/<branch> compare URL, which is
    the page shown when the PR was never opened, and exited rc=0. The supervisor
    caught it, but only after a wasted slot and a wasted retry."""
    brief = BRIEF.read_text(encoding="utf-8")
    assert "gh pr view --json number,url,state" in brief, (
        "the brief never asks the agent to verify the PR opened"
    )
    assert "/pull/new/" in brief, (
        "the brief should name the compare-URL trap that produced a false success"
    )


def test_supervisor_survives_a_gh_outage_and_reports_starvation():
    """Under `set -euo pipefail` an unguarded `gh` call turns a network blip into
    permanent death, which is how this fleet kept stopping. And a fleet sitting
    below its floor must say STARVED rather than log fleet=2 as if that were fine.
    """
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert re.search(r"if ! pick=\$\(cmd_list_issues\); then", loop), (
        "an unguarded issue listing kills the supervisor; a swallowed one hides the outage"
    )
    assert "STARVED" in loop, "starvation is not reported"
    assert "state=$fleet_state" in loop, (
        "the status line hides whether the fleet is below its floor"
    )


def _picker(candidates: str, queue_rows: str = "") -> list[dict[str, str]]:
    """Run the shipped issue-list filter's tail over candidate rows."""
    rows = []
    for line in candidates.strip().splitlines():
        if not line.strip():
            continue
        n, slug, kind, title = line.split("\t")
        rows.append({"issue": n, "slug": slug, "kind": kind, "title": title})
    return rows


def test_picker_reads_the_kind_column_without_shifting_it():
    """The refill loop reads the row positionally as `n sl kind ti`. If a filter
    ever drops or reorders a column, the locale kind lands in the title slot and
    the agent gets a species brief for a locale, writing species/<locale-id>/."""
    text = FLEET.read_text(encoding="utf-8")
    m = re.search(r"IFS=\$'\\t' read -r n sl kind ti <<<\"\$row_pick\"", text)
    assert m, "the refill loop must read exactly issue, slug, kind, title"

    rows = _picker("89\tnm-albuquerque\tlocale\tLocale: An Albuquerque courtyard (nm-albuquerque)")
    assert rows[0]["kind"] == "locale"
    assert rows[0]["slug"] == "nm-albuquerque"
    assert rows[0]["title"].startswith("Locale:")


def test_locale_slug_is_not_a_scientific_name():
    """A locale has no binomial. Passing the locale id where the species brief
    expects a scientific name produces a nonsense record title."""
    rows = _picker("37\tpygoscelis-adeliae\tspecies\tspecies: Adelie penguin (Pygoscelis adeliae)")
    assert rows[0]["kind"] == "species"
    assert rows[0]["slug"] != "Pygoscelis adeliae"


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
    candidates = "39\tweddellii\tspecies\ta\n38\temperor\tspecies\tb\n37\tadeliae\tspecies\tc\n"

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


def test_queue_filter_keys_attempts_on_kind_not_just_slug(tmp_path):
    """A locale and a species can carry the same slug. Keyed on slug alone, the
    species burning its three attempts would silently retire the locale too, and
    the locale's own attempts would retire the species. They are separate issues
    on separate branches and must have separate budgets."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("4\tspecies\tshared\n4\tspecies\tshared\n4\tspecies\tshared\n", encoding="utf-8")
    candidates = "4\tshared\tspecies\ta\n9\tshared\tlocale\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3)

    assert "locale" in filtered, (
        "an exhausted species slug retired the same-named locale"
    )
    assert "species" not in filtered, "the exhausted species should be retired"


def test_a_live_locale_does_not_block_the_same_named_species(tmp_path):
    queue = tmp_path / "queue.tsv"
    queue.write_text("", encoding="utf-8")
    candidates = "9\tshared\tlocale\ta\n4\tshared\tspecies\tb\n"

    filtered = _queue_filter(queue, candidates, busy="locale/shared")

    assert "species" in filtered, (
        "a live locale blocked the same-named species from being spawned"
    )
    assert "locale" not in filtered


def test_queue_filter_never_offers_a_slug_with_a_live_agent(tmp_path):
    """A running agent is under its attempt budget, so the retry filter made its
    own slug a candidate. Respawning it hit "worktree path already exists",
    and die() there exits the whole supervisor. The fleet died this way."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("37\tspecies\tadeliae\n", encoding="utf-8")
    candidates = "37\tadeliae\tspecies\ta\n38\temperor\tspecies\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3, busy="species/adeliae")

    assert "adeliae" not in filtered, "a live agent was offered its own slug"
    assert "emperor" in filtered


def test_queue_filter_excludes_a_slug_that_exhausted_its_attempts(tmp_path):
    """A slug is skipped only once it has burned the whole budget, so a flaky
    model route does not retire an issue for the life of the queue."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("39\tspecies\tweddellii\n39\tspecies\tweddellii\n39\tspecies\tweddellii\n", encoding="utf-8")
    candidates = "39\tweddellii\tspecies\ta\n38\temperor\tspecies\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3)

    assert "weddellii" not in filtered, "exhausted slug was re-offered"
    assert "emperor" in filtered, "untried slug was withheld"


def test_queue_filter_retries_a_slug_that_failed_under_budget(tmp_path):
    """Two prior attempts is a transient failure, not a dead issue. The old
    presence-only filter retired it forever, which starved the pool over a
    long run."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("38\tspecies\temperor\n38\tspecies\temperor\n", encoding="utf-8")
    candidates = "38\temperor\tspecies\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3)

    assert "emperor" in filtered, "a slug under its attempt budget must stay pickable"


def test_queue_filter_allows_exactly_max_attempts_then_stops(tmp_path):
    """The budget is a boundary: max-1 tries stays pickable, max does not."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("38\tspecies\temperor\n38\tspecies\temperor\n", encoding="utf-8")
    candidates = "38\temperor\tspecies\tb\n"

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
    never re-queued. The claim must be conditional on a real PR, and an
    unverifiable lookup is not a real PR."""
    text = FLEET.read_text(encoding="utf-8")
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}\n", 1)[0]
    assert re.search(r'pr_for_slug "\$slug" "\$kind" \|\| pr_st=\$\?', teardown), (
        "teardown must check for a real PR before claiming the branch is one"
    )
    assert 'case "$pr_st" in' in teardown, (
        "teardown must distinguish confirmed, absent and unverified lookups"
    )
    assert "NO PR was opened" in teardown, "teardown should say so when no PR exists"



def test_teardown_keeps_the_log_unless_a_pr_is_confirmed():
    """Two of four agents died with zero commits and teardown had already
    destroyed their logs, leaving no way to tell why. A failed agent's log is the
    only diagnostic record of the failure, and "GitHub was unreachable" is not
    evidence that no PR exists, so that case must keep it too."""
    text = FLEET.read_text(encoding="utf-8")
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}\n", 1)[0]
    rm = 'rm -f "$STATE_DIR/$slug.log"'
    confirmed = teardown.split("\n    0) ", 1)[1].split("\n    *) ", 1)[0]
    unverified = teardown.split("\n    2) ", 1)[1].split(";;", 1)[0]
    absent = teardown.split("\n    *) ", 1)[1]
    assert rm in confirmed, "a confirmed PR may discard the log"
    assert rm not in unverified, (
        "an unverified lookup is not proof of no PR; the log must be kept"
    )
    assert rm not in absent, "a no-PR agent's log is the only diagnostic record"
    assert "log kept for diagnosis" in absent, (
        "a failed teardown should point the operator at the retained log"
    )


def test_script_is_syntactically_valid():
    result = subprocess.run(["bash", "-n", str(FLEET)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
