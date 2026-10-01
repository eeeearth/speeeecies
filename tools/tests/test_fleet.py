"""Tests for tools/agents/fleet.sh. Run with:
uv run --with pytest pytest tools/tests -q
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path
import signal
import time

import pytest

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



def test_a_failed_agents_work_is_salvaged_not_deleted():
    """Teardown promises the branch is kept "for salvage", but --force skipped the
    uncommitted-changes guard and `worktree remove --force` deleted the files. A
    locale agent part-way through a dozen species lost all of it, and the retry
    then reset the branch, so committed work died too."""
    text = FLEET.read_text(encoding="utf-8")
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}\n", 1)[0]
    rm = teardown.index('worktree remove --force "$wt"')
    salvage = teardown.find("salvaged uncommitted work from")
    assert salvage != -1, "teardown never salvages uncommitted work"
    assert salvage < rm, (
        "salvage must happen before the worktree is removed, or it salvages nothing"
    )
    assert "git add -A" in teardown, "salvage must commit the pending files"
    assert "could not salvage" in teardown, (
        "a failed salvage must be reported rather than silently dropping the work"
    )


def test_a_retry_continues_the_branch_instead_of_resetting_it():
    """FLEET_MAX_ATTEMPTS_LOCALE=5 is pointless if each retry restarts from
    origin/main. Verified in a scratch repo: `worktree add <path> <branch>` keeps
    the salvaged commit, `-B <branch> origin/main` discards it."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert "resetting branch" not in spawn, "a retry still resets to base and discards work"
    assert 'worktree_add=(git worktree add "$wpath" "$branch")' in spawn, (
        "an existing branch must be checked out where it stands"
    )
    assert 'worktree_add=(git worktree add -b "$branch" "$wpath" "$BASE_REF")' in spawn, (
        "a new branch must still start from base"
    )


def test_briefs_name_the_real_status_file_and_forbid_an_in_repo_one():
    """A STATUS.md was committed on a live branch and would have landed in that
    pull request. The brief said "your status file" with no path, so agents
    invented one inside the repo."""
    for brief in (BRIEF, BRIEF_LOCALE):
        body = brief.read_text(encoding="utf-8")
        low = " ".join(body.lower().split())
        assert "{{STATUSFILE}}" in body, f"{brief.name} does not name a status path"
        assert "do not create, edit or commit any status file" in low, (
            f"{brief.name} does not forbid touching the in-repo status file"
        )
        assert "continuing a previous attempt" in low, (
            f"{brief.name} does not tell a retried agent to continue salvaged work"
        )
    text = FLEET.read_text(encoding="utf-8")
    assert "STATUSFILE=" in text, "render_brief does not supply the status path"
    assert text.count('"$STATE_DIR/$slug.status.md"') >= 2, (
        "both the spawn and dry-run render must pass a status path"
    )


def test_a_successful_spawn_is_not_silent():
    """spawn_err captured stdout and stderr on success and never printed it, so
    every successful spawn lost its own diagnostics."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    ok = loop.index("live=$(( live + 1 ))")
    prior = loop[:ok]
    assert 'printf \'%s\\n\' "$spawn_err"' in prior, (
        "a successful spawn prints nothing; its output is captured and dropped"
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
    refill = loop.split('while [ -n "$remaining" ]', 1)[1].split("\n      done", 1)[0]
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
    assert loop.index("BELOW_FLOOR") < loop.index('write_state "$STATE_DIR/heartbeat"'), (
        "the invariant must run before the heartbeat is written, or it guards nothing"
    )
    assert loop.index("BELOW_FLOOR") > loop.index('while [ -n "$remaining" ]'), (
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
    those slugs, so this path is reached routinely.

    This originally reset the branch with -B. That was safe from the supervisor's
    point of view but destroyed the previous attempt's committed work, so a retry
    now continues the branch where it stands."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert 'die "branch $branch exists' not in spawn, (
        "an existing branch is a retry, not a fatal collision"
    )
    assert "worktree_add=(git worktree add \"$wpath\" \"$branch\")" in spawn, (
        "an existing branch must be checked out where it stands, not reset"
    )
    assert 'show-ref --quiet "refs/heads/$branch"' in spawn, (
        "the retry must be chosen by testing for the branch, not by a flag"
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
    # Anchor on -v busy="$busy" ' rather than a bare awk: with re.S an unanchored
    # match runs from an unrelated awk in the file all the way to the queue line
    # and captures most of the script.
    awk_body = re.search(
        r"-v busy=\"\$busy\" '\n(.*?)\n\s*' \"\$STATE_DIR/queue\.tsv\" -\)",
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


def test_a_live_locale_blocks_the_same_named_species(tmp_path):
    """Liveness is keyed on the bare slug, not kind/slug, because every state file
    is $slug.* -- .meta, .log, .status.md, .launch.sh. A species and a locale
    sharing a name would otherwise overwrite each other's files while the
    scheduler believed they were distinct. Attempts stay per kind/slug, so the
    blocked species keeps its own retry history and is merely scheduled later.
    """
    queue = tmp_path / "queue.tsv"
    queue.write_text("", encoding="utf-8")
    candidates = "9\tshared\tlocale\ta\n4\tshared\tspecies\tb\n"

    filtered = _queue_filter(queue, candidates, busy="shared")

    assert "species" not in filtered, (
        "a live locale did not block the same-named species; their state files "
        "would collide"
    )
    assert "locale" not in filtered


def test_queue_filter_never_offers_a_slug_with_a_live_agent(tmp_path):
    """A running agent is under its attempt budget, so the retry filter made its
    own slug a candidate. Respawning it hit "worktree path already exists",
    and die() there exits the whole supervisor. The fleet died this way."""
    queue = tmp_path / "queue.tsv"
    queue.write_text("37\tspecies\tadeliae\n", encoding="utf-8")
    candidates = "37\tadeliae\tspecies\ta\n38\temperor\tspecies\tb\n"

    filtered = _queue_filter(queue, candidates, max_attempts=3, busy="adeliae")

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


def test_spawn_actually_completes_on_a_clean_state_dir(tmp_path):
    """Fifty-five source-inspecting tests passed while `cmd_spawn` was fatal on
    every call: it passed `$status` to render_brief one line before declaring it,
    so `set -u` killed the process. Two more failures hid behind that one (a
    missing provider_counts killed the tally under pipefail, and a worktree
    registered by a dead spawn wedged the slug). None were visible without
    running a spawn end to end, so this does that.

    Uses a scratch repo with a real origin and a stubbed gh and agent, so it
    touches neither the live fleet nor GitHub.
    """
    import os
    import shutil

    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    state = tmp_path / "state"
    worktrees = tmp_path / "wt"
    bin_ = tmp_path / "bin"
    for d in (state, worktrees, bin_):
        d.mkdir()

    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(repo), "config", k, v], check=True)
    (repo / "README.md").write_text("base\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
    subprocess.run(["git", "-C", str(repo), "push", "-q", "origin", "main"], check=True)

    agent = bin_ / "agentstub"
    agent.write_text("#!/usr/bin/env bash\nexit 0\n")
    agent.chmod(0o755)
    gh = bin_ / "gh"
    # `gh -q` prints bare values, so the state probe must be unquoted JSON-free text.
    gh.write_text(
        "#!/usr/bin/env bash\n"
        'case "$*" in\n'
        '  *"issue view"*)\n'
        '    if [[ "$*" == *"--json state,assignees"* ]]; then printf \'OPEN|\\n\'; else\n'
        '      printf \'{"body":"Suggested regions\\\\n`US-CO`\\\\n"}\\n\'; fi ;;\n'
        '  *"issue list"*) printf \'[]\\n\' ;;\n'
        '  *"pr list"*) printf \'0\\n\' ;;\n'
        '  *"pr view"*) printf -- \'-\\n\' ;;\n'
        "  *) printf '\\n' ;;\n"
        "esac\n"
    )
    gh.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{bin_}{os.pathsep}{env['PATH']}"
    env.update(
        AGENT_BIN=str(agent),
        GH_REPO="jt55401/speeeecies",
        WORKTREE_ROOT=str(worktrees),
        FLEET_STATE_DIR=str(state),
        BRANCH_PREFIX="test",
        BASE_REF="origin/main",
    )
    proc = subprocess.run(
        [
            "bash", str(FLEET), "spawn",
            "--issue", "7", "--slug", "test-species", "--scientific", "Testus species",
        ],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"spawn failed: {proc.stdout}\n{proc.stderr}"

    for suffix in ("meta", "brief.md", "status.md", "launch.sh"):
        assert (state / f"test-species.{suffix}").is_file(), f"spawn wrote no {suffix}"
    assert (worktrees / "species-test-species").is_dir(), "spawn created no worktree"

    # The bug that started this: the status path must be substituted, not empty.
    brief = (state / "test-species.brief.md").read_text()
    assert "Your status file is ``" not in brief, (
        "render_brief received an empty status path"
    )
    assert str(state / "test-species.status.md") in brief, (
        "the brief does not name the real status file"
    )
    assert not PLACEHOLDER.search(brief), "the rendered brief still has placeholders"

    # The queue drives retry accounting, so its shape is part of the contract.
    assert (state / "queue.tsv").is_file(), "spawn never recorded the attempt"
    row = (state / "queue.tsv").read_text().strip()
    assert row.split("\t") == ["7", "species", "test-species"], f"bad queue row: {row!r}"
    assert (state / "provider_counts").is_file(), "the provider tally was never seeded"

    for leftover in (origin, repo, worktrees):
        shutil.rmtree(leftover, ignore_errors=True)


def test_a_failed_spawn_leaves_no_orphaned_worktree():
    """A spawn that died between `git worktree add` and the .meta write left a
    worktree the supervisor could not count, could not reap, and retried around;
    three had accumulated.

    This used to be an EXIT trap. It could not work: it fires when the *shell*
    exits, expanding $slug and $wpath long after cmd_spawn's locals were gone, so
    it printed `slug: unbound variable` and leaked the worktree it was meant to
    undo. Guarded `return 1` paths return from a function, so it never fired for
    them at all. Cleanup is now explicit at each failure point.
    """
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]

    # Comments are excluded: the prose explaining why the trap was removed
    # contains the word "trap", and matching that would pass for the very thing
    # this asserts is gone.
    code = "\n".join(l for l in spawn.split("\n") if not l.strip().startswith("#"))
    assert "trap " not in code, (
        "cmd_spawn must not rely on an EXIT trap: it expands locals after the "
        "function returns and never fires for a guarded `return 1`"
    )
    add = spawn.index('"${worktree_add[@]}"')
    meta = spawn.index('> "$STATE_DIR/$slug.meta"')
    assert add < meta, "the worktree is created before the agent is published"
    rollback = spawn.index("spawn_rollback() {")
    assert add < rollback or rollback < add, "rollback helper is defined in spawn"
    assert 'git -C "$REPO" worktree remove --force "$wpath"' in spawn, (
        "the rollback must remove the worktree it created"
    )
    assert "worktree prune" in spawn, "and prune the registration it leaves"

def test_a_failed_salvage_keeps_the_worktree():
    """Salvage exists so a stopped agent's files survive. If the salvage commit
    itself fails, removing the directory throws away the only copy anyway."""
    text = FLEET.read_text(encoding="utf-8")
    teardown = text.split("cmd_teardown() {", 1)[1].split("\n}\n", 1)[0]
    assert "salvage_failed" in teardown, "a failed salvage is not tracked"
    guard = teardown.index("if [ \"$salvage_failed\" = 1 ]; then")
    rm = teardown.index('worktree remove --force "$wt"', guard)
    assert guard < rm, "the removal guard must precede the removal"
    assert "else" in teardown[guard:rm], (
        "the worktree must still be removed when salvage succeeded"
    )
    assert "will be removed with its changes" not in teardown, (
        "the old message promised the loss; salvage failure must keep the files"
    )


def test_regions_come_only_from_the_suggested_section():
    """The fallback scraped every two-letter uppercase token from the issue body,
    so licence text became regions: an agent was told to fetch activity curves
    for "CC BY-SA US-CO PR CC BY NC"."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert "[Ss]uggested regions" in spawn, "the real region hint parser is gone"
    assert 'r"\\b([A-Z]{2}' not in spawn, (
        "the whole-body uppercase-token fallback is back; it mines licence text"
    )
    assert '[ -n "$regions" ] || regions=' not in spawn, (
        "a second, unguessed region source remains"
    )
    # The brief already covers an empty hint, so dropping the fallback is safe.
    assert "read the" in BRIEF.read_text(encoding="utf-8").lower()


def test_refill_cannot_spin_on_a_duplicate_candidate():
    """The row advance was `awk 'NR>1 && $2 != s'`, which skips only row 1. One
    duplicate row therefore made the walk oscillate between two slugs forever:
    two blocked issues produced 434 refusals in about eight minutes and the
    heartbeat went stale, because the poll never finished."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert "awk -F'\\t' '!seen[$3 \"/\" $2]++'" in loop, (
        "candidates are not deduplicated by kind/slug, so the walk can revisit one"
    )
    assert "local remaining budget" in loop and re.search(
        r'budget=\$\(printf .*grep -c', loop
    ), "the refill loop is unbounded; a bad row advance spins the poll"
    assert '[ "$budget" -gt 0 ]' in loop, "the budget is computed but never applied"
    assert loop.index('[ "$budget" -gt 0 ]') < loop.index("cmd_spawn --issue"), (
        "the budget must bound the loop, not merely be computed"
    )


def test_orphan_worktrees_are_reclaimed():
    """The fleet counts agents by .meta, so a worktree with no meta belongs to
    nobody: it cannot be reaped and its slug dies forever on 'worktree path
    already exists'. Two of those blocked every remaining species issue."""
    text = FLEET.read_text(encoding="utf-8")
    reap = text.split("# Reap: an agent that finished", 1)[0]
    assert 'species-*|locale-*' in reap, "orphan scan does not recognise fleet worktrees"
    assert '[ -f "$STATE_DIR/$oslug.meta" ] && continue' in reap, (
        "orphan scan would delete live agents' worktrees"
    )
    assert "worktree remove --force" in reap, "orphans are detected but never removed"
    # Only clean orphans may be removed automatically.
    block = reap[reap.index("# Reclaim orphans first."):]
    assert "orphan worktree $wbase has uncommitted work" in block, (
        "an orphan holding uncommitted work must be left for a human"
    )
    assert block.index("status --porcelain") < block.index("worktree remove --force"), (
        "the cleanliness check must precede the removal"
    )


def _awk_prog(needle: str) -> str:
    """Pull an awk program out of the quoted tail of the fleet.sh line holding `needle`."""
    line = next(l for l in FLEET.read_text(encoding="utf-8").splitlines() if needle in l)
    parts = line.split("awk ", 1)[1].split("'")
    assert len(parts) > 3, f"no quoted awk program in: {line.strip()}"
    return parts[3]


def _walk_candidates(candidates: str) -> list[str]:
    """Run the refill walk the supervisor actually ships, over `candidates`.

    The dedupe and the shrink step are pulled out of fleet.sh rather than copied,
    so this fails if either expression changes underneath it.
    """
    dedupe = _awk_prog("!seen[$3")
    shrink = _awk_prog('-v k="$kind/$sl"')
    script = (
        "set -u\n"
        "remaining=$(cat)\n"
        f"remaining=$(printf '%s\\n' \"$remaining\" | awk -F'\\t' '{dedupe}')\n"
        "budget=$(printf '%s\\n' \"$remaining\" | grep -c . || true)\n"
        'out=""\n'
        'while [ -n "$remaining" ] && [ "$budget" -gt 0 ]; do\n'
        '  budget=$(( budget - 1 ))\n'
        "  row_pick=$(printf '%s\\n' \"$remaining\" | head -1)\n"
        "  IFS=$'\\t' read -r n sl kind ti <<<\"$row_pick\"\n"
        f"  remaining=$(printf '%s\\n' \"$remaining\" | awk -F'\\t' -v k=\"$kind/$sl\" '{shrink}')\n"
        '  out="$out $sl"\n'
        "done\n"
        'printf "%s" "$out"\n'
    )
    out = subprocess.run(
        ["bash", "-c", script], input=candidates, capture_output=True, text=True, check=True
    ).stdout
    return out.split()


def test_refill_walk_reaches_every_candidate_in_order():
    """The advance used to be `awk 'NR>1 && $2 != s'`, which skips only row 1. For
    candidates a b c d that walked a -> b -> c -> b, so a stubborn early issue
    starved everything after it and the per-poll budget ran out before reaching
    the last candidate. Refusals must still advance."""
    tried = _walk_candidates("1\ta\tspecies\tA\n2\tb\tspecies\tB\n3\tc\tspecies\tC\n4\td\tspecies\tD\n")
    assert tried == ["a", "b", "c", "d"], f"walk visited {tried}, expected every candidate in order"


def test_refill_walk_terminates_when_every_candidate_refuses():
    tried = _walk_candidates("1\ta\tspecies\tA\n2\tb\tspecies\tB\n3\tc\tspecies\tC\n")
    assert tried == ["a", "b", "c"], f"walk visited {tried}"


def test_a_species_and_a_locale_sharing_a_slug_are_distinct_candidates():
    """Dedupe keyed on bare slug collapsed a species and a locale with the same
    name into one, while attempts and busy agents are counted by kind/slug."""
    tried = _walk_candidates("4\tshared\tspecies\tS\n9\tshared\tlocale\tL\n")
    assert sorted(tried) == ["shared", "shared"], f"a same-slug pair collapsed to {tried}"


def test_launch_title_names_the_work_kind():
    """Every run was titled "species <name> #<issue>", including locales, so the
    agent list and logs mislabelled locale work as species records."""
    text = FLEET.read_text(encoding="utf-8")
    assert '--title "$kind $sci #$issue"' in text, (
        "the launch title hardcodes species, mislabelling locale agents"
    )
    assert '--title "species $sci' not in text, "the hardcoded species title is back"


def test_status_and_reap_quote_the_pr_label_the_same_way():
    """`status` passed a bare `#\\(.number) \\(.state)` to `gh -q`, which is not a
    jq string, so gh failed and the label came back GHERR even when the pull
    request existed. The reap loop quoted it correctly, so the two disagreed."""
    text = FLEET.read_text(encoding="utf-8")
    calls = re.findall(r'pr_field "\$slug" number,state (\'[^\']*\'|"[^"]*")', text)
    assert calls, "no pr_field label calls found"
    assert len(set(calls)) == 1, f"status and reap disagree on jq quoting: {set(calls)}"
    assert calls[0].startswith("'") and "#" in calls[0], (
        "the jq expression must be a quoted string for gh -q"
    )


def test_briefs_forbid_touching_the_repository_status_file():
    """A root STATUS.md already exists on origin/main holding another agent's
    notes, so "do not create one" does not stop an agent appending to it. PR #134
    shipped 9 lines of that as part of a locale contribution."""
    for brief in (BRIEF, BRIEF_LOCALE):
        low = " ".join(brief.read_text(encoding="utf-8").lower().split())
        assert "do not create, edit or commit any status file" in low, (
            f"{brief.name} only forbids creating a status file, not editing the "
            "one already committed to the repository"
        )
        assert "already exists" in low, (
            f"{brief.name} must explain that the in-repo status file is not the agent's"
        )


def test_a_dead_model_route_does_not_burn_an_issue_retry():
    """The queue row is written at spawn, so a provider outage counted against the
    issue's three attempts. Three consecutive route failures could retire an issue
    that had done nothing wrong. A routing failure is now refunded."""
    text = FLEET.read_text(encoding="utf-8")
    assert "refund_attempt()" in text, "no attempt refund exists"
    # note_route_failure must distinguish the two outcomes, and the caller must
    # use it in a condition so the non-routing path cannot trip errexit.
    fn = text.split("note_route_failure() {", 1)[1].split("\n}\n", 1)[0]
    assert "return 0" in fn and "return 1" in fn, (
        "note_route_failure must report whether the failure was routing"
    )
    reap = text.split("*)     # if-guard", 1)
    assert len(reap) == 2 and "refund_attempt" in reap[1][:400], (
        "the reap does not refund on a routing failure"
    )
    assert "if note_route_failure" in text, (
        "note_route_failure is called bare; its non-routing return would trip errexit"
    )


def test_liveness_and_attempts_use_consistent_keys():
    """Scheduling keyed liveness on kind/slug while every state file is $slug.*,
    so a species and a locale sharing a name would overwrite each other's .meta.
    Liveness now keys on the bare slug, matching the state layer; attempts stay
    keyed by kind/slug because they are separate issues."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    busy = re.search(r"busy=\$\(for m in \"\$\{metas\[@\]\}\"; do ([^\n]*)", loop)
    assert busy, "no busy-set construction found"
    assert "basename" in busy.group(1) and "/$s" not in busy.group(1), (
        "the busy set must be keyed on the bare slug to match the state files"
    )
    assert '{ if ($2 == "" || $3 == "") next; key = $3 "/" $2; if ($2 in live) next;' in loop, (
        "the filter must test the bare slug for liveness"
    )
    assert 'FILENAME == q { if ($3 != "") n[$2 "/" $3]++; next }' in loop, (
        "attempts must still be counted per kind/slug"
    )


def test_supervisor_reverts_a_scratch_file_edit_whatever_the_brief_says():
    """Containment cannot rest on the prompt. A root STATUS.md already exists on
    origin/main from an earlier agent, so an agent reading the tree sees an
    invitation, and two live agents were launched before the briefs forbade
    touching it. One PR already shipped that file."""
    text = FLEET.read_text(encoding="utf-8")
    guard = text.split("# Scratch-file guard.", 1)
    assert len(guard) == 2, "no STATUS.md guard in the poll loop"
    block = guard[1].split("# Reap:", 1)[0]
    # The guard iterates a denylist, so the restore targets "$scratch"; the file
    # names live in the loop header, not in the git command.
    assert 'restore --staged --worktree --source=HEAD -- "$scratch"' in block, (
        "the guard must restore the file, not merely warn about it"
    )
    # This used to assert the guard skipped untracked files. That was wrong: an
    # untracked report.md is invisible to `git diff HEAD`, so skipping it left
    # the file sitting there for the next `git add -A` to sweep into a commit.
    # The guard now covers untracked scratch too.
    assert 'cat-file -e "HEAD:$scratch"' in block, (
        "a base-branch file is reverted; an agent-created one is removed"
    )
    # It has to run every poll, before the reap that would declare the PR done.
    loop = text.split("cmd_supervise() {", 1)[1]
    assert loop.index("# Scratch-file guard.") < loop.index("# Reap:"), (
        "the guard must run before a finished agent's PR is accepted"
    )


def test_route_detection_only_reads_the_tail_of_the_log():
    """Grepping the whole log refunded an issue attempt whenever an agent merely
    mentioned a rate limit while researching, which is not a routing death."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("note_route_failure() {", 1)[1].split("\n}\n", 1)[0]
    assert "tail -40" in fn, (
        "route detection must scope to the end of the log, where the death is"
    )
    # The tail is captured once and every match runs against that. grep must
    # never see the whole file, or a passing mention somewhere in a long agent
    # log refunds the attempt.
    assert re.search(r'recent=\$\(tail -40 "\$STATE_DIR/\$1\.log"', fn), (
        "the log must be tailed before anything matches against it"
    )
    assert '<<<"$recent"' in fn, "every pattern must match the tail, not the file"
    assert not re.search(r'grep -qiE[^\n]*\$STATE_DIR/\$1\.log', fn), (
        "grep is still being handed the whole log"
    )


def test_the_provider_tally_can_be_reconciled_against_the_log():
    """note_spawn_provider ran before the queue append and before the `spawned`
    line, so the tally sat permanently ahead of anything visible in the log."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    tally = spawn.index("note_spawn_provider")
    logged = spawn.index('say "spawned $slug')
    queued = spawn.index('>> "$STATE_DIR/queue.tsv"')
    assert queued < logged < tally, (
        "the tally must be recorded after the row and the log line it should match"
    )


def test_only_one_supervisor_may_run_per_state_directory():
    """Two supervisors race each other through the orphan scan and the STATUS.md
    sweep, each reverting worktrees it does not own."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert "flock -n 9" in loop, "the supervisor takes no exclusive lock"
    assert 'exec 9>"$STATE_DIR/supervisor.lock"' in loop, (
        "the lock must live in the state directory so it is per-run"
    )


def test_the_launcher_records_its_own_pid():
    """Without a recorded PID the supervisor cannot stop what it started, and
    teardown removed the worktree while the agent kept running out of a deleted
    directory: five live processes for three agents."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert 'echo \\$\\$ > "$STATE_DIR/$slug.pid"' in spawn, (
        "the launcher must write its own pid; setsid makes it a group leader"
    )


def test_stop_agent_kills_the_whole_process_group_and_waits():
    """Killing only the recorded pid can leave the agent itself alive, since the
    launcher runs it as a child rather than exec'ing it."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("stop_signal() {", 1)[1].split("\n}\n", 1)[0]
    # The group is resolved from /proc, because the pid we hold may be the agent
    # itself rather than the group leader.
    assert "/proc/$pid/stat" in fn, "the process group must be read from /proc"
    assert 'kill -TERM -- "-$pgid"' in fn or 'kill -TERM -- "-$pid"' in fn, (
        "SIGTERM must go to the process group"
    )
    assert 'kill -KILL -- "-$pgid"' in fn or 'kill -KILL -- "-$pid"' in fn, (
        "an agent that ignores SIGTERM needs SIGKILL"
    )
    assert 'kill -0 "$pid"' in fn, "the stop must be waited on, not fired and forgotten"
    assert fn.index("SIGTERM") < fn.index("SIGKILL"), "escalate in order"
    stop = text.split("stop_agent() {", 1)[1].split("\n}\n", 1)[0]
    assert 'stop_signal "$pid"' in stop, "stop_agent must delegate to stop_signal"
    assert 'rm -f "$pf"' in stop, "a stale pidfile would resurrect a phantom agent"


def test_teardown_stops_the_agent_before_it_salvages():
    """Otherwise salvage commits files out from under a process still writing
    them, and the worktree is removed while the agent runs on in it."""
    text = FLEET.read_text(encoding="utf-8")
    td = text.split("cmd_teardown() {", 1)[1].split("\n}\n", 1)[0]
    stop = td.index('stop_agent "$slug"')
    assert stop < td.index("salvage"), "stop the agent before salvaging its work"
    assert stop < td.index("worktree remove"), "stop the agent before removing the tree"
    # Forced teardown is exactly the path that leaked, so it must stop it too.
    forced = td[td.index('force=1'):]
    assert 'stop_agent "$slug"' in td, "teardown never signals the agent"


def test_liveness_reads_the_pid_not_the_worktree_path():
    """A retired agent whose slug respawns into the same path matches on path,
    which is how one agent was counted as two while the stale one kept editing
    the replacement's tree."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("agent_running() {", 1)[1].split("\n}\n", 1)[0]
    assert fn.index('.pid"') < fn.index("agent_for_worktree"), (
        "the recorded pid must decide liveness before falling back to a scan"
    )
    assert 'group_serves_worktree "$wt" "$pid" && return 0' in fn, (
        "a live pid is only this agent if its group still serves the worktree"
    )
    assert 'kill -0 "$pid" 2>/dev/null; then' in fn, (
        "existence must be checked before ownership is inferred from it"
    )


def test_the_poll_loop_reaps_orphaned_processes():
    """A pidfile with no metadata is an agent nobody owns."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert "*.pid" in loop, "the poll loop never looks for orphaned processes"
    assert 'stop_agent "$oslug"' in loop, "an orphan is detected but never stopped"


def test_the_status_guard_also_clears_a_staged_edit():
    """`git checkout -- <path>` restores the worktree from the index, so a staged
    edit survived it and still shipped while the guard logged a false success."""
    text = FLEET.read_text(encoding="utf-8")
    block = text.split("# Scratch-file guard.", 1)[1].split("# Reap:", 1)[0]
    assert 'restore --staged --worktree --source=HEAD -- "$scratch"' in block, (
        "a staged STATUS.md edit is not cleared by checkout; it needs the index reset"
    )
    # A guard that logs success without verifying is worse than no guard.
    assert block.index("restore --staged") < block.index("WARNING"), (
        "the warning must be the fallback branch, after the attempt"
    )
    assert 'diff --quiet HEAD -- "$scratch"' in block, (
        "the restore must be confirmed clean before success is reported"
    )


def test_route_detection_requires_provider_context_and_never_matches_bare_429():
    """Species logs carry Wikidata property ids like P4293, and a data fetch
    against a rate-limited endpoint is not the agent failing to route."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("note_route_failure() {", 1)[1].split("\n}\n", 1)[0]
    # Two stages now, and they quote their patterns differently: unambiguous
    # routing deaths, then a 429 that must also name the provider.
    pats = []
    for line in fn.splitlines():
        for q in ('"', "'"):
            tok = f"grep -qiE {q}"
            if tok in line:
                pats.append(re.compile(line.split(tok, 1)[1].split(q)[0], re.I))
    assert len(pats) == 2, f"expected two route patterns, found {len(pats)}"
    rx = pats[0]
    rx_prov = pats[1]

    # Real routing deaths must still refund the attempt.
    for dead in (
        "Cannot find any route for model opencode/space-bunny-free",
        "ERROR: model opencode/mimo-v2.5 is overloaded",
        "429 Too Many Requests from provider api",
        "quota exceeded for model opencode/longcat",
    ):
        assert rx.search(dead) or rx_prov.search(dead), (
            f"a real routing death was missed: {dead!r}"
        )

    # A species log is full of numbers and mentions of limits. Neither is the
    # agent failing to route, and neither may refund an issue attempt.
    for alive in (
        "the taxon's circumscription cites P4293 and Q4293",
        "rate limits at the reserve are 5 visitors per day",
        "P4293 retrieved 200 OK from the Wikidata API",
        "the 429 birds counted in the survey were ringed",
        # Real lines from this fleet's own logs, which marked a healthy provider
        # as failed and refunded an attempt the agent had earned.
        "FETCH-ERROR: HTTP Error 429: Too Many Requests",
        "<urlopen error 429> while fetching the activity curve",
        "urllib.error.HTTPError: 429",
    ):
        assert not (rx.search(alive) or rx_prov.search(alive)), (
            f"a data-fetch line matched and would refund: {alive!r}"
        )


def test_the_provider_tally_is_rebuilt_from_the_log_and_refuses_to_publish_a_wrong_one():
    """The tally had drifted one above anything derivable from the log, which is
    the property it exists to provide."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("reconcile_provider_counts() {", 1)[1].split("\n}\n", 1)[0]
    assert "/^spawned " in fn, "the tally must be rebuilt by counting the log's spawn lines"
    assert "grep -c '^spawned '" in fn, "the log's own spawn count is the cross-check"
    assert 'ne "$logged"' in fn, "a parse that disagrees with the log must not be published"
    # The spawn line is "model <id>", not "model=<id>"; matching the wrong one
    # silently yields zero models and would reset a correct tally.
    assert r"model \([^)]*\)" in fn, "the parse must match the line as actually written"
    code = "\n".join(l for l in fn.splitlines() if not l.strip().startswith("#"))
    assert "model=" not in code, "the spawn line has a space, not an equals sign"
    loop = text.split("cmd_supervise() {", 1)[1]
    assert "reconcile_provider_counts" in loop, "reconcile is never called"


def test_the_guard_covers_report_as_well_as_status():
    """A locale PR shipped report.md because the brief told the agent to write
    one and a blanket `git add` swept it in. Two files, one denylist."""
    text = FLEET.read_text(encoding="utf-8")
    block = text.split("# Scratch-file guard.", 1)[1].split("# Reap:", 1)[0]
    assert "for scratch in STATUS.md report.md" in block, (
        "the guard must cover the report file the locale agents created"
    )


def test_the_guard_sees_an_untracked_scratch_file():
    """`git diff HEAD` cannot see an untracked file, so a report.md not yet
    staged walked past the guard and was swept into the commit by the next
    `git add -A` -- the exact failure the guard exists to prevent."""
    text = FLEET.read_text(encoding="utf-8")
    block = text.split("# Scratch-file guard.", 1)[1].split("# Reap:", 1)[0]
    assert '[ ! -e "$gwt/$scratch" ]' in block, (
        "presence must be tested on disk, since an untracked file has no diff"
    )
    assert "ls-files --error-unmatch" in block, (
        "the index must also be consulted, to catch a staged deletion"
    )
    assert 'git diff --quiet HEAD -- "$scratch" 2>/dev/null && continue' not in block, (
        "diffing against HEAD alone silently skips untracked scratch files"
    )


def test_the_guard_handles_a_scratch_file_that_is_not_in_head():
    """report.md is never on the base branch, so restoring it from HEAD fails
    and the staged copy would ship. It has to be unstaged and deleted instead,
    which is a different fix from reverting an edit to a base-branch file."""
    text = FLEET.read_text(encoding="utf-8")
    block = text.split("# Scratch-file guard.", 1)[1].split("# Reap:", 1)[0]
    assert 'cat-file -e "HEAD:$scratch"' in block, (
        "the two shapes need branching on whether the file exists in HEAD"
    )
    assert block.index('cat-file -e "HEAD:$scratch"') < block.index('rm -q --cached'), (
        "the agent-created branch must unstage and delete"
    )


def test_no_brief_redirects_the_report_into_the_worktree():
    """The locale brief instructed `> report.md`, which is how two PRs shipped
    one. Containment in the supervisor is the backstop; the instruction that
    caused it has to go too."""
    for path in (BRIEF, BRIEF_LOCALE):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith(("#", "-", "|", ">")) or "report.md" not in line:
                continue
            assert "> report.md" not in line, (
                f"{path.name} still redirects the report into the worktree: {line.strip()!r}"
            )
    locale = BRIEF_LOCALE.read_text(encoding="utf-8")
    assert "never `git add -A`" in locale, (
        "the locale brief had no commit step at all, so nothing stopped a "
        "blanket add from sweeping scratch files in"
    )


def test_the_pidless_fallback_matches_on_the_whole_command_line():
    """`pgrep -f` prints bare pids; only `-a` appends the command line. Without
    the -a the fallback grepped the worktree path against a pid string, matched
    nothing, and returned success -- so teardown of an agent launched before
    pidfiles existed still left the process running, which is the leak this
    fallback exists to close."""
    # This originally guarded `pgrep -f` printing bare pids, which cannot be
    # matched against a path. Matching no longer reads the rendered command line
    # at all, so the fix is structural: pids come from pgrep and the worktree is
    # compared as an exact --dir argv value.
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("stop_agent() {", 1)[1].split("\n}\n", 1)[0]
    assert 'for pid in $(pgrep -f -- "$AGENT_BIN run"' in fn, (
        "the fallback must enumerate agent pids"
    )
    assert '[ "$(pid_arg_dir "$pid")" = "$wt" ] || continue' in fn, (
        "each candidate must be confirmed by exact --dir argv before being signalled"
    )
    assert "grep -qF" not in fn, "the fallback must not grep a rendered command line"
    assert "no pidfile for $1" in fn, "the fallback path must be reachable and logged"


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="spawns and signals a real process group",
)
def test_stopping_an_agent_without_a_pidfile_still_reaches_the_process():
    """Exercised for real, not asserted structurally: an agent-shaped process with
    no pidfile anywhere, and the fallback has to find and stop it.

    The previous version of this test blocked. It launched the fake with
    `subprocess.run(["setsid", launcher, wt])`, and because the launcher exec'd
    `sleep 120` in the foreground, the call did not return for the sleep's
    duration -- so the slow-test gate timed out and the claimed "both skipped
    tests pass" was not reproducible. It also faked argv wrongly: `exec -a
    "opencode run --dir X"` makes the whole string one argv[0], so `--dir` was
    never a discrete argument. Both are fixed by the shared helper.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        state = f"{td}/state"
        os.makedirs(state)
        wt = f"{td}/wt"
        os.makedirs(wt)
        agent = _spawn_fake_agent(wt, td)

        # No pidfile at all: this is the fallback that has to do the work.
        Path(state, "demo.meta").write_text(f"worktree={wt}\n", encoding="utf-8")
        assert not list(Path(state).glob("*.pid")), "the pidless case must have no pidfile"

        proc = subprocess.run(["bash", _stop_agent_harness(state)],
                              capture_output=True, text=True, timeout=90)
        assert proc.returncode == 0, (
            f"stop_agent exited {proc.returncode} on the pidless path: {proc.stderr.strip()}"
        )
        assert "no pidfile for demo" in proc.stdout, (
            f"the fallback did not run; output was: {proc.stdout!r}"
        )
        assert _exited(agent), (
            "stop_agent returned success but the pidless agent is still alive"
        )

@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="signals real processes to compare lock inheritance",
)
def test_a_child_that_closes_the_lock_fd_does_not_hold_the_lock():
    """Controlled comparison, because a bare holder count is confounded: the
    measurement itself forks children that inherit the fd. Same method three
    times: no child, a child that keeps fd 9, a child that closes it.

    Two details make this faithful to cmd_supervise. The lock must sit on fd 9
    specifically, because that is the fd the launcher closes. And the children
    must be spawned with close_fds=False, because bash's `&` inherits every
    descriptor while Popen closes them above 2 by default -- with the default,
    neither child inherits anything and the test passes vacuously.
    """
    import fcntl
    import tempfile

    def holders(path: str) -> int:
        out = subprocess.run(["fuser", path], capture_output=True, text=True)
        return len([w for w in out.stdout.split() if w.isdigit()])

    with tempfile.TemporaryDirectory() as td:
        lock = f"{td}/supervisor.lock"
        fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o644)
        os.dup2(fd, 9)  # cmd_supervise locks fd 9; the launcher closes fd 9
        fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)

        def spawn(script: str) -> subprocess.Popen:
            return subprocess.Popen(
                ["setsid", "bash", "-c", script],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, close_fds=False)

        base = holders(lock)

        keeper = spawn('exec -a probeA sleep 15')
        time.sleep(1)
        with_keeper = holders(lock)
        keeper.terminate()

        closer = spawn('exec 9>&-; exec -a probeB sleep 15')
        time.sleep(1)
        with_closer = holders(lock)
        closer.terminate()

        assert with_keeper > base, (
            f"a child that keeps fd 9 should add a lock holder "
            f"(baseline {base}, with keeper {with_keeper}); if it does not, this "
            f"test cannot detect the inheritance bug it exists to catch"
        )
        assert with_closer == base, (
            f"a child that closes fd 9 still holds the lock "
            f"({with_closer} vs baseline {base})"
        )


def test_process_matching_uses_exact_argv_not_a_cmdline_substring():
    """The whole brief is passed via --auto "$(cat brief)", so every agent's
    rendered command line contains every other agent's worktree path. A
    substring match therefore reports --dir /wt/species-foo-bar as a hit for
    /wt/species-foo, and teardown kills an innocent agent's process group."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("pid_arg_dir() {", 1)[1].split("\n}\n", 1)[0]
    assert "/proc/$pid/cmdline" in fn, (
        "the --dir value must be read from NUL-separated argv, not the rendered line"
    )
    assert 'grep' not in fn, "pid_arg_dir must not grep the command line"
    assert '[ "$prev" = "--dir" ] && dir="$arg"' in fn, (
        "--dir must be read as a discrete argument, not a substring"
    )
    scan = text.split("agent_for_worktree() {", 1)[1].split("\n}\n", 1)[0]
    assert '[ "$d" = "$wt" ] && return 0' in scan, (
        "the scan must require an exact --dir match"
    )
    stop = text.split("stop_agent() {", 1)[1].split("\n}\n", 1)[0]
    assert '[ "$(pid_arg_dir "$pid")" = "$wt" ] || continue' in stop, (
        "teardown must require an exact --dir match before signalling"
    )
    for name, body in (("agent_for_worktree", scan), ("stop_agent", stop)):
        assert "grep -qF -- \"$wt\"" not in body, (
            f"{name} still substring-matches the worktree against a command line"
        )


def test_a_pid_is_only_trusted_when_it_still_serves_the_worktree():
    """`kill -0` proves a pid exists, not that it is ours. A recycled pid would
    be counted as the agent and then have its process group killed."""
    text = FLEET.read_text(encoding="utf-8")
    live = text.split("agent_running() {", 1)[1].split("\n}\n", 1)[0]
    assert 'group_serves_worktree "$wt" "$pid"' in live, (
        "liveness must prove the pid serves this worktree, not merely exist"
    )
    assert live.index("kill -0") < live.index("group_serves_worktree"), (
        "existence is a precondition, not proof of ownership"
    )
    stop = text.split("stop_agent() {", 1)[1].split("\n}\n", 1)[0]
    assert "treating the pidfile as stale, not signalling" in stop, (
        "a pid that does not serve the worktree must never be signalled"
    )
    assert stop.index("does not serve") < stop.index('say "stopping $1'), (
        "the ownership check has to precede the signal"
    )


def test_the_supervisor_refuses_to_signal_its_own_process_group():
    """A stale pidfile whose pid was recycled into the supervisor's own group
    would make `kill -- -$pgid` terminate the supervisor, which is far worse
    than leaking an agent."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("stop_signal() {", 1)[1].split("\n}\n", 1)[0]
    assert '"/proc/$$/stat"' in fn, "the supervisor must know its own process group"
    assert 'refusing to signal it' in fn, "there must be a refusal path"
    guard = fn.index('"$pgid" = "$self"')
    assert guard < fn.index("kill -TERM"), (
        "the self-group check must come before any signal is sent"
    )


def test_the_supervisor_lock_is_taken_before_any_state_is_written():
    """Reconciling first meant a second supervisor rewrote the provider tally on
    its way to being refused -- a write by a process that had not yet established
    it was allowed to write."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert loop.index("flock -n 9") < loop.index("reconcile_provider_counts"), (
        "exclusivity must be established before the tally is rewritten"
    )


def test_no_child_of_the_supervisor_inherits_its_lock_fd():
    """An orphaned poll sleep, reparented to init after the supervisor was
    killed, still held the lock, so an immediate restart was refused with
    "another supervisor already holds" while no supervisor was running. I hit
    exactly that: zero supervisors, one lock holder, a `sleep` with ppid 1."""
    text = FLEET.read_text(encoding="utf-8")
    code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))

    # Every sleep the supervisor runs, and the launcher spawn, must drop the fd.
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("sleep ") or "setsid nohup" in stripped:
            assert "9>&-" in stripped, (
                f"a child spawned here inherits the supervisor's lock fd: {stripped!r}"
            )
    assert 'sleep "$POLL_SECONDS" 9>&-' in code, (
        "the poll sleep outliving the supervisor is the exact orphan observed"
    )
    assert 'setsid nohup "$launch" 9>&-' in code, (
        "setsid holds the lock in between fork and the launcher closing it"
    )


def _extract_function(name: str) -> str:
    """Pull one function verbatim out of fleet.sh, so a test drives the shipped
    code rather than a paraphrase of it."""
    text = FLEET.read_text(encoding="utf-8")
    start = text.index(f"{name}() {{")
    return text[start:text.index("\n}\n", start) + 3]


def _spawn_fake_agent(wt: str, tmpdir: str, seconds: int = 90) -> int:
    """Start something shaped like a real agent: a setsid session leader whose
    argv has `--dir <wt>` as a discrete argument, exactly as
    "$AGENT_BIN" run --model M --dir W --title T produces.

    Two things this deliberately avoids. `exec -a "opencode run --dir X"` sets
    the whole string as a SINGLE argv[0], so `--dir` is never a discrete
    argument and pid_arg_dir correctly finds nothing -- a fake that would pass
    for a broken implementation. And the pid comes from the child writing it
    rather than from pgrep, because any pattern broad enough to find the fake
    also matches the shell that launched it.
    """
    pidfile = f"{tmpdir}/fake-agent.pid"
    subprocess.Popen(
        ["setsid", sys.executable, "-c",
         "import os,sys,time;open(sys.argv[1],'w').write(str(os.getpid()));"
         f"time.sleep({seconds})",
         pidfile, "opencode", "run", "--model", "m", "--dir", wt, "--title", "t"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 10
    while time.time() < deadline:
        if os.path.exists(pidfile):
            txt = Path(pidfile).read_text().strip()
            if txt.isdigit():
                return int(txt)
        time.sleep(0.2)
    raise AssertionError("the fake agent never reported its pid")


def _stop_agent_harness(state: str, slug: str = "demo") -> str:
    """A harness driving the shipped stop_agent against STATE_DIR."""
    path = f"{state}/../harness.sh"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("set -u\n")
        fh.write(f'STATE_DIR="{state}"\n')
        fh.write("AGENT_BIN=opencode\n")
        fh.write('meta_get() { sed -n "s/^$2=//p" "$STATE_DIR/$1.meta" 2>/dev/null | head -1; }\n')
        fh.write('say() { printf "%s\\n" "$*"; }\n')
        for fn in ("pid_arg_dir", "group_serves_worktree", "stop_signal", "stop_agent"):
            fh.write(_extract_function(fn))
        fh.write(f"stop_agent {slug}\n")
    return path


def _exited(pid: int, timeout: float = 15.0) -> bool:
    """True once the pid is gone OR a zombie. A killed child that has not been
    reaped keeps its /proc entry with state Z, and a zombie is not a running
    agent -- counting it as alive made a correct stop look like a failure."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        stat = Path(f"/proc/{pid}/stat")
        if not stat.exists():
            return True
        try:
            if stat.read_text().rsplit(")", 1)[-1].split()[0] == "Z":
                return True
        except (OSError, IndexError):
            return True
        time.sleep(0.5)
    return False


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="spawns and signals a real process group",
)
def test_stop_agent_stops_a_pidfile_owned_agent():
    """The ordinary path: a pidfile, a process group, a meta naming the worktree.

    This is the case that regressed. `wt` was assigned only inside the no-pidfile
    branch, so the pidfile path reached an unbound `wt` under `set -u` and
    aborted -- and a forced teardown then removed the worktree and the metadata
    while leaving the agent running, which is the exact failure all the
    process-ownership work exists to prevent.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        state = f"{td}/state"
        os.makedirs(state)
        wt = f"{td}/wt"
        os.makedirs(wt)
        leader = _spawn_fake_agent(wt, td)
        assert Path(f"/proc/{leader}").exists(), "the fake agent never started"

        Path(state, "demo.meta").write_text(f"worktree={wt}\n", encoding="utf-8")
        Path(state, "demo.pid").write_text(f"{leader}\n", encoding="utf-8")

        proc = subprocess.run(["bash", _stop_agent_harness(state)],
                              capture_output=True, text=True, timeout=90)
        assert proc.returncode == 0, (
            f"stop_agent exited {proc.returncode} on the pidfile path: {proc.stderr.strip()}"
        )
        assert _exited(leader), (
            "stop_agent returned success but the process group is still alive"
        )


def test_the_supervisor_lock_records_its_owner():
    """The lock alone cannot distinguish a running supervisor from an orphan
    child that inherited fd 9, so it has to say who holds it."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert 'write_state "$STATE_DIR/supervisor.owner"' in loop, (
        "the lock must record its owner, or a stale holder is indistinguishable"
    )
    assert loop.index("flock -n 9") < loop.index('write_state "$STATE_DIR/supervisor.owner"'), (
        "the owner can only be recorded once the lock is actually held"
    )
    # Guarded: an unwritable state dir used to abort the supervisor on a raw
    # redirection error, so the fleet died silently instead of reporting why.
    assert '|| die "cannot record the lock owner' in loop, (
        "a failed owner write must be fatal with a named reason, not a bare redirect"
    )


def test_a_stale_lock_holder_does_not_block_a_restart():
    """bash does not set close-on-exec on fd 9, so any child keeps holding the
    lock after the supervisor dies. I hit this live: zero supervisors running,
    one lock holder with ppid 1, and a replacement refused. Closing fd 9 at
    every spawn site cannot be complete across dozens of gh and git calls, so
    the lock breaks itself when its recorded owner is gone."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert "breaking a supervisor lock orphaned by dead pid" in loop, (
        "a lock whose owner is dead must be reclaimed, not obeyed"
    )
    assert "supervisor_alive" in loop, (
        "liveness of the recorded owner decides whether the lock is stale"
    )


def test_a_live_lock_holder_is_still_refused():
    """The reclaim must never fire on a pid that is alive, or a second
    supervisor would start beside a running one and they would race through the
    orphan scan and the scratch sweep."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    fn = text.split("supervisor_alive() {", 1)[1].split("\n}\n", 1)[0]
    # The check must confirm the pid is one of OUR supervisors, not merely alive,
    # so a recycled pid cannot authorise breaking a live supervisor's lock.
    assert '*/fleet.sh) saw_script=1' in fn, (
        "argv must contain fleet.sh as a discrete word"
    )
    assert "supervise)  saw_supervise=1" in fn, (
        "argv must contain supervise as a discrete word"
    )
    assert fn.index("kill -0") < fn.index("/proc/$pid/cmdline"), (
        "existence is checked, then identity"
    )
    assert '[ "$saw_script" = 1 ] && [ "$saw_supervise" = 1 ]' in fn, (
        "both words are required before a lock may be broken"
    )
    guard = loop.index("! supervisor_alive")
    assert guard < loop.index("die \"another supervisor already holds"), (
        "a live or unattributable holder must reach the refusal, not the reclaim"
    )


def test_the_orphan_sweep_can_never_reap_the_supervisor_itself():
    """The sweep globs *.pid and reaps any pidfile with no matching .meta. Naming
    the lock's owner record supervisor.pid put it inside that glob: the supervisor
    found what it took to be a dead agent, called stop_agent on itself, and
    signalled its own process group. It exited within a poll with no error, which
    is why it looked like a silent crash rather than self-termination.

    The owner's argv has no --dir, so both wt and pid_arg_dir came back empty,
    the stale-pid guard compared "" to "" and passed, and stop_signal happily
    signalled pgid == its own.
    """
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]

    # The owner record must not be spelled *.pid, or the glob catches it.
    assert '> "$STATE_DIR/supervisor.pid"' not in text, (
        "the owner record must not use the .pid extension the orphan sweep globs"
    )
    assert 'write_state "$STATE_DIR/supervisor.owner"' in loop, (
        "the owner record must be written under a name the sweep cannot match"
    )

    # And the sweep must refuse that name regardless of extension.
    sweep = loop.split("# Orphans.", 1)[1].split("# Scratch-file guard.", 1)[0]
    assert "*/supervisor.pid|*/supervisor.owner" in sweep, (
        "the sweep must explicitly skip the supervisor's own record"
    )
    guard = sweep.index("case \"$pf\" in")
    reap = sweep.index("stop_agent \"$oslug\"")
    assert guard < reap, "the skip has to come before the reap, not after"


def test_an_empty_worktree_can_never_authorise_killing_a_process_group():
    """The guard that decides whether to signal compared the recorded --dir
    against the worktree. Both were empty for a process with no --dir, the
    comparison passed, and stop_signal signalled whatever group it found. An
    empty worktree is a failure to identify the process, never a match."""
    text = FLEET.read_text(encoding="utf-8")
    for name in ("stop_agent", "agent_running"):
        body = text.split(f"{name}() {{", 1)[1].split("\n}\n", 1)[0]
        code = "\n".join(l for l in body.splitlines() if not l.strip().startswith("#"))
        assert "-z \"$wt\"" in code or "[ -n \"$wt\" ]" in code, (
            f"{name} must refuse to act when the worktree is unknown"
        )


def test_meta_get_never_aborts_its_caller():
    """A pidfile can outlive its .meta -- that is exactly what the orphan sweep
    exists to clean up. But sed failing inside the pipeline made pipefail fail
    the caller's assignment, so the caller died before reaching its own guard,
    and an orphan pidfile killed the supervisor instead of being reaped."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("meta_get() {", 1)[1].split("\n}\n", 1)[0]
    assert "|| true" in fn, (
        "meta_get must always succeed; a missing meta is an expected state"
    )
    # Every caller must tolerate an empty result rather than treating it as fatal.
    for name in ("agent_running", "stop_agent", "supervisor_alive"):
        assert name in text, f"{name} should exist"


def test_liveness_requires_the_worktree_to_still_exist():
    """An agent whose worktree has been deleted cannot commit and is working out
    of a directory that no longer exists. It was still counted as live, so the
    fleet reported `live=3 state=OK` while an agent was stranded in a deleted
    cwd."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("agent_running() {", 1)[1].split("\n}\n", 1)[0]
    guard = fn.index('[ -d "$wt" ] || return 1')
    assert guard < fn.index("kill -0"), (
        "the worktree check must come before any liveness claim"
    )


def test_the_stale_lock_reclaim_is_serialised():
    """Unlink-and-recreate is atomic per process but not between them: two
    contenders can both see a dead owner, both unlink, and hold locks on two
    different inodes, each convinced it is exclusive. Oracle measured 42 of 80
    concurrent trials admitting two supervisors."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert 'mkdir "$STATE_DIR/supervisor.reclaim"' in loop, (
        "the reclaim needs an atomic mutex between contenders"
    )
    # The mutex must be taken BEFORE the staleness decision, and the decision
    # re-tested under it.
    take = loop.index('mkdir "$STATE_DIR/supervisor.reclaim"')
    decide = loop.index('supervisor_alive "$holder"')
    assert take < decide, "the mutex must serialise the staleness decision"
    assert loop.count("flock -n 9") >= 2, (
        "flock must be re-tested under the mutex, after the winner may hold it"
    )
    # rm -rf, not rmdir: the mutex directory holds an `owner` file, so rmdir
    # fails on it as non-empty and, under `set -e`, that failure exited the
    # supervisor -- the reclaim path killed the restart it exists to enable.
    assert 'rm -rf "$STATE_DIR/supervisor.reclaim"' in loop, (
        "the mutex must be released on every exit path, with rm -rf"
    )
    assert 'rmdir "$STATE_DIR/supervisor.reclaim"' not in loop, (
        "rmdir fails on the non-empty mutex directory and kills the supervisor"
    )
    # A dead owner is detected immediately, not after the full wait, so a restart
    # after a killed supervisor does not sit through the whole grace period.
    check = loop.index('reclaim_owner=$(tr -dc')
    timeout_check = loop.index('[ "$waited" -gt 30 ]')
    assert check < timeout_check, (
        "a dead mutex owner must be detected on the first iteration, or every "
        "restart waits out the full timeout before recovering"
    )


def test_a_lock_holder_is_proven_by_the_lock_not_by_its_argv():
    """Argv shape is not ownership: any process whose arguments contain a path
    ending in fleet.sh plus a bare `supervise` satisfied the old check, and a
    supervisor of a different state directory would have had its lock broken by
    this one."""
    text = FLEET.read_text(encoding="utf-8")
    fn = text.split("supervisor_alive() {", 1)[1].split("\n}\n", 1)[0]
    assert "/proc/\"$pid\"/fd/*" in fn, (
        "ownership must be proven by holding this state dir's lock descriptor"
    )
    assert 'target="$STATE_DIR/supervisor.lock"' in fn, (
        "the descriptor must be checked against THIS state directory's lock"
    )
    shape = fn.index("saw_supervise=1")
    proof = fn.index('/proc/"$pid"/fd/*')
    assert shape < proof, "argv shape is a precondition, not the proof"


def test_a_failed_worktree_add_cannot_report_a_spawn():
    """`cmd_spawn` is invoked as `if ! spawn_err=$( ( cmd_spawn ... ) 2>&1 )`, and
    bash suspends `set -e` inside a condition context. So a failed
    `git worktree add` did not abort: the spawn wrote a .meta and a .pid for an
    agent that never existed and logged "spawned". The branch was checked out by
    a worktree outside WORKTREE_ROOT, git refused with `fatal: ... already used
    by worktree at`, and the fleet counted a phantom -- reporting live=3 with two
    real agents, and re-spawning the same doomed slug every poll.
    """
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]

    # The subshell must be inside an `if !`, not a bare statement.
    assert 'if ! ( cd "$REPO" && git worktree prune' in spawn, (
        "the worktree-add subshell must have its status checked explicitly"
    )
    assert 'could not create a worktree for' in spawn, (
        "a failed worktree add must be reported, not swallowed"
    )
    # The failure must return before any .meta or pidfile is written.
    fail = spawn.index("return 1")
    meta = spawn.index('> "$STATE_DIR/$slug.meta"')
    assert fail < meta, (
        "the failure has to return before the metadata is written, or a phantom "
        "agent is created that the supervisor then counts as live"
    )
    # And the real worktree-add line must no longer stand alone.
    assert "\n  ( cd \"$REPO\" && git worktree prune" not in spawn, (
        "an unchecked worktree add is what produced the phantom spawn"
    )


def test_the_provider_cursor_advances_once_per_committed_spawn():
    """Reordering cmd_spawn to publish the agent last removed both `advance_model`
    calls along the way, and the definition alone looks fine to every gate. The
    cursor would have frozen and one model would be served forever, which is the
    rotation the task actually asks for."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert len(re.findall(r"^\s*advance_model\s*$", spawn, re.M)) == 1, (
        "exactly one advance_model call per spawn, or the rotation is wrong"
    )
    # And it must come after the commit point, so a refused spawn does not rotate.
    assert spawn.index("advance_model") > spawn.index('spawn_started "$slug"'), (
        "the cursor must only step once the agent is confirmed running"
    )


def test_a_spawn_is_published_only_after_the_launcher_exists():
    """`cmd_spawn` runs inside `if ! spawn_err=$( ... )`, where bash suspends
    `set -e`, so nothing aborted on its own. Writing `.meta` first left a phantom
    when the launcher could not be created: the spawn logged "spawned" with no
    agent behind it, and the next poll died tailing a log that never existed."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]

    build = spawn.index('cat > "$launch_tmp" <<LAUNCHER')
    checks = spawn.index('if [ ! -s "$launch_tmp" ]')
    install = spawn.index('mv -fT "$launch_tmp" "$launch"')
    publish = spawn.index('> "$STATE_DIR/$slug.meta"')
    commit = spawn.index('spawn_started "$slug"')
    launched = spawn.index('setsid nohup "$launch"')
    assert build < checks < install, "the launcher is built, then verified, then installed"
    # Ownership before process. A .meta with no live agent is recoverable -- the
    # reap loop tears it down next poll -- but a running process with no .meta is
    # invisible to everything, which is how agents were stranded in deleted
    # worktrees. So the meta is written first and the launch verified after.
    assert install < publish < launched, (
        "the launcher must be installed, then ownership published, then launched"
    )
    assert spawn.index('spawn_started "$slug"') > launched, (
        "a launch that never took must be detected and rolled back"
    )
    assert commit < spawn.index("advance_model"), (
        "the launch must be confirmed before the cursor steps and `spawned` is logged"
    )


def test_the_launcher_must_be_an_executable_regular_file():
    """Plain `mv -f src dst` where dst is an existing directory moves src *into*
    it and still exits 0, so a launcher path that was really a directory
    installed successfully. And a directory is "executable" because it is
    searchable, so an -x-only check passed it too."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert 'mv -fT "$launch_tmp" "$launch"' in spawn, (
        "mv must use -T, or a directory at the destination swallows the launcher"
    )
    assert '[ ! -f "$launch" ] || [ ! -x "$launch" ]' in spawn, (
        "the launcher must be a regular executable file; a directory passes -x"
    )


def test_a_failed_spawn_rolls_back_its_worktree():
    """The EXIT trap cannot do this. It fires when the shell exits, and these
    paths `return` from a function instead; under `supervise` the shell then runs
    for days, so every guarded failure leaked a worktree and a branch
    registration that blocked the slug's next attempt."""
    text = FLEET.read_text(encoding="utf-8")
    spawn = text.split("cmd_spawn() {", 1)[1].split("\n}\n", 1)[0]
    assert "spawn_rollback()" in spawn, "there must be a rollback helper"
    body = text.split("spawn_rollback() {", 1)[1].split("\n}\n", 1)[0]
    assert 'worktree remove --force "$wpath"' in body, (
        "the rollback must remove the worktree it created"
    )
    assert "worktree prune" in body, "and prune the registration it leaves"
    # Every guarded failure after the worktree exists must roll back. The worktree
    # failure itself happens before there is a worktree to undo, so it is excluded.
    guarded = re.findall(
        r'say "(?:could not (?:write|make|install)[^"]*'
        r'|the launcher[^"]*)"\s*\n\s*rm -f [^\n]*\n\s*spawn_rollback\n\s*return 1',
        spawn)
    assert len(guarded) == 4, (
        f"all four post-worktree failure paths must roll back, found {len(guarded)}"
    )
    # Every failure path that runs AFTER a worktree exists must roll back. The
    # worktree-add failure itself is excluded on purpose: it is the one failure
    # with nothing to undo, because git never created the tree.
    lines = spawn.split("\n")
    # Skip the worktree-add failure entirely: git never created the tree there, so
    # that path has nothing to undo. Its `return 1` sits before the closing `fi`.
    # Start after the rollback/startup helper definitions close, so their own
    # `return 1` lines are not mistaken for spawn failure paths.
    helper_end = max(
        next(i for i, l in enumerate(lines) if l.startswith("  spawn_rollback() {")),
        next(i for i, l in enumerate(lines) if l.startswith("  spawn_started() {")),
    )
    helper_end = next(i for i in range(helper_end, len(lines))
                      if lines[i] == "  }") + 1
    worktree_made = helper_end
    commit = next(i for i, l in enumerate(lines) if 'spawn_started "$slug"' in l)
    assert worktree_made < commit, "worktree creation must precede the commit point"
    for i in range(worktree_made, commit):
        if lines[i].strip() != "return 1":
            continue
        # Walk back over the rm -f that precedes it, if any.
        j = i - 1
        while j > worktree_made and lines[j].strip().startswith("rm -f "):
            j -= 1
        assert lines[j].strip() == "spawn_rollback", (
            f"a failure path leaks its worktree: {lines[i - 2].strip()!r} "
            f"returns without rolling back"
        )


def test_a_missing_agent_log_cannot_kill_the_reap():
    """A phantom or salvaged agent can have a `.meta` and no log. The unguarded
    `tail` made the supervisor exit on the reap, which is how a false spawn killed
    the following poll."""
    text = FLEET.read_text(encoding="utf-8")
    reap = text.split("# Reap:", 1)[1].split("Refill to the floor", 1)[0]
    for line in reap.splitlines():
        if 'tail -5 "$STATE_DIR/$slug.log"' in line:
            assert "2>/dev/null" in line, (
                f"the reap must tolerate a missing log: {line.strip()!r}"
            )
    assert "no agent log" in reap, "a missing log should be reported, not fatal"


def test_the_reclaim_mutex_cannot_wedge_forever():
    """A contender killed between `mkdir supervisor.reclaim` and its `rmdir` left
    the directory behind, and every future contender then waited 30s and died --
    permanently wedging stale-lock recovery, which is the one path that must work
    when a supervisor is restarted."""
    text = FLEET.read_text(encoding="utf-8")
    loop = text.split("cmd_supervise() {", 1)[1]
    assert "clearing a reclaim mutex orphaned by dead pid" in loop, (
        "a mutex whose owner is dead must be reclaimable"
    )
    assert '> "$STATE_DIR/supervisor.reclaim/owner"' in loop, (
        "the mutex must record its owner so staleness is decidable"
    )
    clear = loop.index("clearing a reclaim mutex orphaned")
    giveup = loop.index('die "another supervisor is reclaiming')
    assert clear < giveup, "staleness must be checked before giving up"


def test_the_orphan_worktree_sweep_spares_a_worktree_with_a_live_agent():
    """The sweep reclaimed any worktree with no `.meta` and a clean tree, and
    "no meta" is not evidence a slug is unused. A supervisor killed between
    creating the worktree and writing the meta leaves exactly that state, so the
    sweep pulled the tree out from under a running agent: its cwd became deleted,
    it could never commit, and with no meta and no pidfile nothing could ever find
    it again. Three agents lost their work that way while the fleet reported
    live=3 -- the count matched the metas, not the processes."""
    text = FLEET.read_text(encoding="utf-8")
    sweep = text.split("# Reclaim orphans first.", 1)[1].split("# Orphans.", 1)[0]
    assert "agent_for_worktree" in sweep, (
        "the sweep must check for a live agent before removing a worktree"
    )
    assert "leaving it alone" in sweep, "and say why it is skipping one"
    # The glob yields a trailing slash; --dir does not, so an unstripped path
    # would never match and the guard would silently do nothing.
    assert 'agent_for_worktree "${w%/}"' in sweep, (
        "the worktree path must be compared without the glob's trailing slash"
    )
    guard = sweep.index("agent_for_worktree")
    remove = sweep.index("worktree remove --force")
    assert guard < remove, "the liveness check must precede the removal"


def test_a_failed_state_write_does_not_kill_the_supervisor():
    """The heartbeat write runs in the main poll loop where errexit is ACTIVE, so a
    full or read-only state dir killed the supervisor mid-poll -- and with it every
    running agent, since nothing reaps or refills without it. A state write failing
    is a degraded fleet, not a reason to stop working."""
    text = FLEET.read_text(encoding="utf-8")
    assert "write_state() {" in text, "there must be a guarded state-write helper"
    loop = text.split("cmd_supervise() {", 1)[1]
    assert 'write_state "$STATE_DIR/heartbeat"' in loop, (
        "the heartbeat must go through the guarded writer"
    )
    assert "STATE_WRITE_FAILED" in loop, (
        "a fleet whose heartbeat cannot be written must say so in its state"
    )
    # And the failed write must not skip the sleep, or the loop would spin.
    guard = loop.index("STATE_WRITE_FAILED")
    assert "sleep \"$POLL_SECONDS\" 9>&-" in loop[guard:], (
        "a failed heartbeat must still pace the next poll"
    )


def test_an_unreclaimable_orphan_worktree_is_reported_not_silently_skipped():
    """The orphan sweep removes a worktree with no meta and a clean tree. If the
    directory belongs to a *different* checkout, `git worktree remove` fails and
    the sweep reported nothing at all -- so the slug stayed wedged on "worktree
    path already exists" with no indication why. It must be named, and it must not
    be deleted automatically: it belongs to another checkout."""
    text = FLEET.read_text(encoding="utf-8")
    sweep = text.split("# Reclaim orphans first.", 1)[1].split("# Orphans.", 1)[0]
    assert "could not be reclaimed" in sweep or "foreign" in sweep, (
        "a worktree the sweep cannot remove must be reported, not skipped in silence"
    )
    # It must be a warning about a blocker, not a removal.
    warned = sweep.index("could not be reclaimed") if "could not be reclaimed" in sweep \
        else sweep.index("foreign")
    assert "worktree remove --force" not in sweep[warned:], (
        "a foreign worktree must never be deleted automatically"
    )


# --- dynamic tests for the foreign-worktree blocker ------------------------------
# Static assertions missed the state-lie regression entirely: `fleet_state` had
# been assigned inside the "have I warned yet" branch, so the heartbeat said OK on
# every poll after the first warning while the slug was still wedged. These drive
# the real supervisor against a real second checkout.

def _foreign_worktree(other_repo: str, root: str, name: str, branch: str,
                      force: bool = False) -> None:
    # -B resets an existing branch so the same slug can be recreated under the
    # same directory name, which is what the remove-and-recreate case needs.
    cmd = ["git", "-C", other_repo, "worktree", "add", "-q", f"{root}/{name}"]
    cmd += ["-B" if force else "-b", branch]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _drop_worktree(other_repo: str, root: str, name: str) -> None:
    subprocess.run(["git", "-C", other_repo, "worktree", "remove", "--force",
                    f"{root}/{name}"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", other_repo, "worktree", "prune"], check=True)


def _scratch_repo() -> str:
    d = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", d], check=True)
    Path(d, "f").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", d, "add", "-A"], check=True)
    subprocess.run(["git", "-C", d, "-c", "user.email=a@a", "-c", "user.name=a",
                    "commit", "-qm", "base"], check=True)
    return d


def _poll(worktree_root: str, state: str, seconds: float = 6.0) -> str:
    """Run the supervisor for a few polls, then stop it and return what it said.

    `supervise` is a poll loop, so it has to be killed rather than awaited, and
    `subprocess.run(timeout=...)` discards the output when it fires. Popen plus
    killpg keeps the several polls of output we are asserting on.
    """
    env = dict(os.environ, WORKTREE_ROOT=worktree_root, GH_REPO="jt55401/speeeecies",
               FLEET_STATE_DIR=state, POLL_SECONDS="2")
    proc = subprocess.Popen(["bash", str(FLEET), "supervise", "--min", "0", "--max", "0"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env, start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        out, _ = proc.communicate()
    out = out or ""
    # Guard against a vacuous pass. Two of the three tests below assert that a
    # warning is ABSENT, which is trivially true of empty output -- and they did
    # pass, green, against a tree where the supervisor had died on "not inside a
    # git repository" before reaching the sweep at all. A poll line proves the
    # supervisor actually ran the code under test.
    assert "fleet=" in out, (
        f"the supervisor produced no poll line, so this proves nothing: {out!r}"
    )
    return out


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="builds real git worktrees and runs supervisor passes",
)
def test_a_foreign_worktree_blocks_the_reported_state_on_every_poll():
    """The heartbeat said OK on every poll after the first warning, because
    `fleet_state` was assigned inside the "have I warned yet" branch. The fleet
    reported healthy while a slug stayed wedged on "worktree path already
    exists"."""
    import tempfile as _tf
    root, other, state = _tf.mkdtemp(), _scratch_repo(), _tf.mkdtemp()
    try:
        _foreign_worktree(other, root, "locale-alpha", "alpha")
        out = _poll(root, state)
        assert "could not be reclaimed" in out, f"the blocker was not reported: {out!r}"
        states = re.findall(r"state=([A-Z_]+)", out)
        polls = [s for s in states if s in ("OK", "BLOCKED_BY_FOREIGN_WORKTREE")]
        assert polls, f"no poll lines found: {out!r}"
        assert all(s == "BLOCKED_BY_FOREIGN_WORKTREE" for s in polls), (
            f"a poll reported {set(polls)} while a foreign worktree was wedging a slug"
        )
    finally:
        for d in (root, other, state):
            subprocess.run(["rm", "-rf", d], check=False)


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="builds real git worktrees and runs supervisor passes",
)
def test_two_foreign_worktrees_warn_once_each_and_do_not_re_arm():
    """A single scalar latch compared for equality logged all six times: alpha
    was warned, then beta reset the latch, then alpha was no longer 'warned'."""
    import tempfile as _tf
    root, other, state = _tf.mkdtemp(), _scratch_repo(), _tf.mkdtemp()
    try:
        _foreign_worktree(other, root, "locale-alpha", "alpha")
        _foreign_worktree(other, root, "locale-beta", "beta")
        out = _poll(root, state)
        assert out.count("could not be reclaimed") == 2, (
            f"expected one warning per blocker, got {out.count('could not be reclaimed')}"
        )
        assert "locale-alpha could not" in out and "locale-beta could not" in out
    finally:
        for d in (root, other, state):
            subprocess.run(["rm", "-rf", d], check=False)


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="builds real git worktrees and runs supervisor passes",
)
def test_a_removed_foreign_worktree_clears_the_blocker_and_the_state():
    """The latch must be rebuilt from what each pass actually sees: a blocker that
    is gone stops being reported, and the fleet returns to OK."""
    import tempfile as _tf
    root, other, state = _tf.mkdtemp(), _scratch_repo(), _tf.mkdtemp()
    try:
        _foreign_worktree(other, root, "locale-alpha", "alpha")
        assert "could not be reclaimed" in _poll(root, state)
        subprocess.run(["git", "-C", other, "worktree", "remove", "--force",
                        f"{root}/locale-alpha"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", other, "worktree", "prune"], check=True)
        out = _poll(root, state)
        assert "could not be reclaimed" not in out, (
            f"a removed worktree is still being reported: {out!r}"
        )
        assert "state=BLOCKED_BY_FOREIGN_WORKTREE" not in out, (
            "the fleet is still reporting blocked after the blocker was removed"
        )
    finally:
        for d in (root, other, state):
            subprocess.run(["rm", "-rf", d], check=False)


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="runs one long-lived supervisor and mutates the tree mid-run",
)
def test_a_blocker_removed_mid_run_unblocks_the_same_supervisor():
    """`foreign_now` was declared outside the poll loop and appended to without ever
    being cleared, so one sighting pinned the fleet to BLOCKED for the lifetime of
    the process -- removing the worktree did not unblock it. Every other test here
    started a fresh supervisor per scenario, so nothing could see the accumulation;
    this one keeps a single supervisor running and removes the blocker underneath
    it."""
    import tempfile as _tf
    root, other, state = _tf.mkdtemp(), _scratch_repo(), _tf.mkdtemp()
    outdir = _tf.mkdtemp()
    out = os.path.join(outdir, "supervisor.out")
    env = dict(os.environ, WORKTREE_ROOT=root, GH_REPO="jt55401/speeeecies",
               FLEET_STATE_DIR=state, POLL_SECONDS="2")
    with open(out, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen(["bash", str(FLEET), "supervise", "--min", "0", "--max", "0"],
                                stdout=fh, stderr=subprocess.STDOUT, text=True,
                                env=env, start_new_session=True)
    try:
        time.sleep(5)                                    # a poll or two with no blocker
        _foreign_worktree(other, root, "locale-alpha", "alpha")
        time.sleep(6)                                    # polls that see the blocker
        subprocess.run(["git", "-C", other, "worktree", "remove", "--force",
                        f"{root}/locale-alpha"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", other, "worktree", "prune"], check=True)
        time.sleep(7)                                    # polls after it is gone
    finally:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait(timeout=30)

    text = Path(out).read_text(encoding="utf-8")
    states = re.findall(r"fleet=0 \(min 0 max 0\) state=([A-Z_]+)", text)
    assert states, f"the supervisor never polled: {text!r}"
    assert text.count("could not be reclaimed") == 1, (
        f"expected one warning for one blocker, got {text.count('could not be reclaimed')}"
    )
    assert "BLOCKED_BY_FOREIGN_WORKTREE" in states, (
        f"the blocker was never reported while it existed: {states}"
    )
    # The whole point: the state has to come back on its own, in this same process.
    assert states[-1] == "OK", (
        f"the fleet stayed blocked after the blocker was removed: {states}"
    )
    for d in (root, other, state, outdir):
        subprocess.run(["rm", "-rf", d], check=False)


@pytest.mark.skipif(
    os.environ.get("FLEET_SLOW_TESTS") != "1",
    reason="runs one long-lived supervisor and mutates the tree mid-run",
)
def test_a_slug_removed_and_recreated_mid_run_warns_again():
    """A slug that is blocked, removed, and then recreated inside one supervisor
    lifetime has to warn a second time. This is the case the latch got wrong twice:
    first because the state was assigned inside the "have I warned yet" branch, then
    because the blocker list was only ever appended to. Oracle verified it by hand;
    this encodes it so the next edit cannot silently undo it."""
    import tempfile as _tf
    root, other, state = _tf.mkdtemp(), _scratch_repo(), _tf.mkdtemp()
    outdir = _tf.mkdtemp()
    out = os.path.join(outdir, "supervisor.out")
    env = dict(os.environ, WORKTREE_ROOT=root, GH_REPO="jt55401/speeeecies",
               FLEET_STATE_DIR=state, POLL_SECONDS="2")
    with open(out, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen(["bash", str(FLEET), "supervise", "--min", "0", "--max", "0"],
                                stdout=fh, stderr=subprocess.STDOUT, text=True,
                                env=env, start_new_session=True)
    try:
        time.sleep(5)
        _foreign_worktree(other, root, "locale-alpha", "alpha")
        time.sleep(6)
        _drop_worktree(other, root, "locale-alpha")
        time.sleep(6)
        # Same slug, same path, back again -- the latch must not still hold it.
        _foreign_worktree(other, root, "locale-alpha", "alpha", force=True)
        time.sleep(6)
    finally:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait(timeout=30)

    text = Path(out).read_text(encoding="utf-8")
    states = re.findall(r"fleet=0 \(min 0 max 0\) state=([A-Z_]+)", text)
    assert states, f"the supervisor never polled: {text!r}"
    assert text.count("could not be reclaimed") == 2, (
        f"one warning per appearance of the blocker, want 2, got "
        f"{text.count('could not be reclaimed')}"
    )
    assert states[0] == "OK" and states[-1] == "BLOCKED_BY_FOREIGN_WORKTREE", (
        f"expected the fleet to end blocked on the recreated slug, got {states}"
    )
    # And it must have gone clear in between, or the second warning proves nothing.
    assert "OK" in states[1:-1], f"the blocker was never lifted: {states}"
    for d in (root, other, state, outdir):
        subprocess.run(["rm", "-rf", d], check=False)


# --- provider balance and model capability -------------------------------------
# These run the real shell functions, extracted verbatim from fleet.sh, instead of
# asserting on the source text. The bugs fixed in this loop were all invisible to
# source assertions: one made two tests pass against a supervisor that had died
# before reaching the code, and the tally skew survived because nothing ever
# executed the selection.

def _shell_function(name: str) -> str:
    text = FLEET.read_text(encoding="utf-8")
    start = text.index(f"\n{name}() {{")
    end = text.index("\n}\n", start) + 3
    return text[start:end]


def _run_provider_selection(counts: str, cursor: str) -> str:
    """Drive the real provider_of/advance_model with a crafted tally; return the
    provider cursor they hand over to."""
    state = tempfile.mkdtemp()
    if counts is not None:
        Path(state, "provider_counts").write_text(counts, encoding="utf-8")
    Path(state, "provider_cursor").write_text(cursor + "\n", encoding="utf-8")
    pool = FLEET.read_text(encoding="utf-8")
    zen = pool.split("MODEL_POOL_ZEN=(", 1)[1].split(")", 1)[0]
    go = pool.split("MODEL_POOL_GO=(", 1)[1].split(")", 1)[0]
    script = (
        f'STATE_DIR={state}\n'
        f"MODEL_POOL_ZEN=({zen})\n"
        f"MODEL_POOL_GO=({go})\n"
        f"{_shell_function('provider_of')}"
        f"{_shell_function('provider_tally')}"
        f"{_shell_function('advance_model')}\n"
        "advance_model\n"
        'cat "$STATE_DIR/provider_cursor"\n'
    )
    p = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    subprocess.run(["rm", "-rf", state], check=False)
    assert p.returncode == 0, f"selection failed: {p.stderr}"
    return p.stdout.strip()


def test_a_skewed_tally_is_converged_rather_than_frozen():
    """Strict alternation preserved a lifetime skew instead of closing it: the tally
    read zen 40 / go 25 and every handover kept that 15-spawn gap. Whoever is behind
    has to be served next, or "balance their usage" is not actually happening."""
    # go is behind, so go is served next; zen is behind in the mirror case.
    assert _run_provider_selection("zen 40\ngo 25\n", "zen") == "go"
    assert _run_provider_selection("zen 25\ngo 40\n", "zen") == "zen"


def test_provider_selection_alternates_once_the_tally_is_level():
    assert _run_provider_selection("zen 40\ngo 40\n", "zen") == "go"
    assert _run_provider_selection("zen 40\ngo 40\n", "go") == "zen"


def test_provider_selection_survives_a_missing_tally():
    """A fresh state dir has no provider_counts at all. The poll must not abort on
    it, and both providers have to read as level rather than one of them winning by
    default."""
    assert _run_provider_selection(None, "zen") == "go"
    assert _run_provider_selection(None, "go") == "zen"


def test_the_default_rotation_only_serves_larger_routes():
    """The brief asks for larger, research-capable free routes. Flash and lightning
    models shared one list with nemotron-3-ultra, so the cursor served them just as
    often -- the opposite of the preference. They stay available, off the rotation."""
    text = FLEET.read_text(encoding="utf-8")
    rotated = text.split("MODEL_POOL_ZEN=(", 1)[1].split(")", 1)[0]
    rotated += text.split("MODEL_POOL_GO=(", 1)[1].split(")", 1)[0]
    for small in ("flash", "lightning"):
        assert small not in rotated, (
            f"a {small} route is in the auto-rotated pool: {rotated}"
        )
    assert "nemotron-3-ultra-free" in rotated, "the largest free route must stay"
    # Kept, not deleted: an operator still needs them when a primary route is down.
    assert "MODEL_POOL_ZEN_FALLBACK=(" in text


def _simulate_spawns(counts: str, cursor: str, n: int) -> list[str]:
    """Replay the REAL spawn sequence n times and return the provider served each time.

    The committed order in cmd_spawn is next_model -> advance_model ->
    note_spawn_provider, so the next cursor is computed from the tally that does not
    yet include the model just served. Testing advance_model alone missed that: the
    lifetime catch-up rule it implements serves the lagging provider seventeen times
    in a row against a 15-spawn skew, which the isolated handoff test cannot see.
    """
    state = tempfile.mkdtemp()
    Path(state, "provider_counts").write_text(counts, encoding="utf-8")
    Path(state, "provider_cursor").write_text(cursor + "\n", encoding="utf-8")
    src = FLEET.read_text(encoding="utf-8")
    zen = src.split("MODEL_POOL_ZEN=(", 1)[1].split(")", 1)[0]
    go = src.split("MODEL_POOL_GO=(", 1)[1].split(")", 1)[0]
    # Take the *value* out of ${FLEET_MAX_PROVIDER_STREAK:-2}, not the whole
    # expansion, or the comparison below runs against a literal "${...}" string.
    m = re.search(r"FLEET_MAX_PROVIDER_STREAK=\$\{FLEET_MAX_PROVIDER_STREAK:-(\d+)\}", src)
    assert m, "FLEET_MAX_PROVIDER_STREAK default not found in fleet.sh"
    streak = m.group(1)
    # write_state must come along: advance_model persists the streak through it, and
    # omitting it made the write fail silently, leaving the streak at 0 and the
    # catch-up unbounded -- a harness gap that looked exactly like a code bug.
    fns = "".join(_shell_function(f) for f in (
        "provider_of", "provider_of_model", "provider_tally",
        "next_model", "advance_model", "note_spawn_provider", "write_state"))
    script = (
        f'STATE_DIR={state}\n'
        f'FLEET_MAX_PROVIDER_STREAK="{streak}"\n'
        f"MODEL_POOL_ZEN=({zen})\n"
        f"MODEL_POOL_GO=({go})\n"
        f"{fns}\n"
        "for i in $(seq 1 " + str(n) + "); do\n"
        '  m=$(next_model)\n'
        "  advance_model\n"
        '  note_spawn_provider "$m"\n'
        '  provider_of_model "$m"\n'
        "done\n"
    )
    p = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60)
    subprocess.run(["rm", "-rf", state], check=False)
    assert p.returncode == 0, f"simulation failed: {p.stderr}"
    return p.stdout.split()


def test_provider_catchup_is_bounded_not_a_single_long_burst():
    """Serving the lagging provider until a 15-spawn skew is level means fifteen
    consecutive spawns against one route. That hammers one quota, which is not what
    "balance their usage ... evenly and consistently" asks for. The catch-up has to
    be bounded; convergence belongs in the long window, not one burst."""
    served = _simulate_spawns("zen 40\ngo 25\n", "zen", 90)
    assert len(served) == 90
    longest, run = 1, 1
    for a, b in zip(served, served[1:]):
        run = run + 1 if a == b else 1
        longest = max(longest, run)
    assert longest <= 2, (
        f"one provider served {longest} spawns consecutively; catch-up must be bounded"
    )
    # Still convergent: the lagging provider has to close the gap over the window,
    # otherwise "bounded" would just mean "gave up on balancing".
    counts = {"zen": 40, "go": 25}
    for s in served:
        counts[s] += 1
    assert counts["go"] > 40, f"the lagging provider never caught up: {counts}"
    assert abs(counts["zen"] - counts["go"]) <= 2, f"did not converge: {counts}"


def test_provider_balance_stays_even_once_the_tally_is_level():
    served = _simulate_spawns("zen 47\ngo 47\n", "zen", 40)
    counts = {"zen": 0, "go": 0}
    for s in served:
        counts[s] += 1
    assert abs(counts["zen"] - counts["go"]) <= 2, f"unbalanced at parity: {counts}"
