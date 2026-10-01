# Running a fleet of agents on species records

One agent contributes one species record and ends in one pull request. This
directory coordinates several of those at once, each in its own git worktree and
branch. A human still merges.

It exists because the species flow in [`AGENTS.md`](../../AGENTS.md) is written for
one agent at a time, and it is a lot of waiting: fetching activity curves,
validating, previewing and waiting for CI is mostly spent not thinking. Running
three to five at once turns that waiting into throughput.

Nothing here changes the species format or the validator. It is only a driver.

## Requirements

- `git`, and `gh` authenticated with write access to the repository.
- An agent CLI that can run headless. The default is `opencode run`; override
  with `AGENT_BIN`. See `MODEL_POOL` in `fleet.sh` for what it expects the
  binary to accept (`--model`, `--variant`, `--dir`, `--auto`).
- The tools this repository already needs: `uv`, `python3`.

## Use

```bash
# What is open, unassigned, and not already covered by an open PR.
tools/agents/fleet.sh list-issues

# Confirm every model in the pool still answers before you trust the rotation.
tools/agents/fleet.sh probe-models

# What an agent will be told, without spawning one or touching GitHub.
tools/agents/fleet.sh render-brief --issue 33 --slug tiliqua-scincoides \
  --scientific "Tiliqua scincoides" --regions AU

# One agent.
tools/agents/fleet.sh spawn --issue 33 \
  --slug tiliqua-scincoides --scientific "Tiliqua scincoides"

# What is happening.
tools/agents/fleet.sh status

# Keep between three and five running, forever. --once reconciles a single pass.
tools/agents/fleet.sh supervise --min 3 --max 5

# Close one out once its PR is open. --force when it stopped without one.
tools/agents/fleet.sh teardown tiliqua-scincoides
```

State lives in `~/.local/state/speeeecies-fleet/`: one `.meta` per agent, its
log, its filled brief, and the cursor into the model pool. Worktrees go to
`$WORKTREE_ROOT`, default `$(dirname "$REPO")/worktrees` — a sibling of the
checkout, not under `$HOME`. Nothing is written
inside the repository, so no state file can end up in a pull request.

Two things resolve against the **script's own directory**, not the repository:
`BRIEF_TEMPLATE` and `PERMISSIONS`. That is deliberate. A harness under
development is usually run from a checkout that does not have `tools/agents/`
committed yet, and resolving against the repo made it refuse to spawn with a
missing-template error while the template sat next to it. Override
`WORKTREE_ROOT` to put a run's worktrees somewhere specific:

```bash
WORKTREE_ROOT="$PWD/../worktrees" tools/agents/fleet.sh supervise --min 3 --max 5
```

## How an agent is spawned

`spawn` creates a worktree from `origin/main` on
`<branch-prefix>/species-<issue>-<slug>`, fills `brief-species.md` with the
issue number, slug, scientific name and the regions that issue suggests, and
launches the agent headless with its output to a log file. The brief is the
whole job: the agent is told the flow, the rules, which existing record to copy,
and what a rejected pull request looks like.

## Recipes

`brief-species.md` tells an agent the general method. `recipes.md` tells it the
answer for the specific issue it was handed, delimited by `<!-- recipe:N -->`
markers that `spawn` splices into the brief.

The reason is that the hard part of a species record is not the flow, which is
documented, it is picking the template and knowing which fields cannot be
carried across. Getting that wrong is expensive in a way that is invisible
until review: a seal built as a `serpentine`, a bat built as a `quadruped`, a
`call_m1`/`call_m2` copied unchanged from a European toad onto an Asian one
puts the record six months out of season. A recipe names the one record to copy
and lists the fields that must change, so the agent is correcting a known
template rather than discovering the trap.

Each recipe also says whether the issue is stale. Some request issues outlive
the work that satisfied them, and for those the recipe is "this record already
exists, fetch the missing regions" rather than "create this".

To add one, copy an existing block, change the marker to the new issue number,
and keep the `##` heading style. `tools/tests/test_fleet.py` fails if a marker
is unbalanced or its body is empty, so a half-finished recipe cannot ship
silently. An issue with no recipe is not an error: the brief says so explicitly
and tells the agent to use the general table and mention it in the pull request.

Recipes are advice, not contract. When one contradicts the repository, the
agent is told to trust the repository and say so in the pull request, because
the schema is the authority and a recipe is a human's reading of it.

## Balancing model usage

`MODEL_POOL_ZEN` and `MODEL_POOL_GO` are cycled **independently**, and the two
providers alternate: every spawn serves one provider then hands over to the
other, stepping only that provider's own cursor.

The point is not the list, it is the shape. The same model published under the
`opencode/` and `opencode-go/` provider ids is **two separate quota buckets**.
A single round-robin over one combined list cannot balance them — with six zen
routes and two go routes it serves three zen spawns per go one, which is exactly
what it did here (17 zen, 6 go over 23 spawns) until the pools were split.

Balance is observable rather than assumed: `provider_counts` in the state
directory tallied what was actually served, and the `heartbeat` file carries
`zen=` and `go=`. Check it instead of parsing the log.

Two operational notes. Probe before trusting the pool: a free model can lose its
route, and `probe-models` is how you find out before five agents stall on it.
And cold starts on the largest models are slow — a first call can take minutes,
which is normal and not a hang.

## Safety rails

`agent-permissions.json` is loaded as the agent's config. It denies
`gh pr merge`, force-push, amending, and pushing to `main`, and everything else is
allowed. This matters when the account running the fleet has maintainer rights:
without the rails a confused agent can merge its own work. The rails are what
makes "a human merges" true rather than aspirational.

The agent is also told, in the brief, never to merge, never to push to `main`,
and never to add itself as a reviewer. The permission file is the enforcement;
the brief is the explanation.

## Why this does not drive herdr

The brief for this fleet asked for `herdr-delegate`. This driver does not invoke
herdr, and that substitution was reviewed and accepted rather than assumed.

herdr is a terminal workspace manager with a socket API, and it does expose
`worktree create`, `agent start --kind opencode --pane <id>` and `agent prompt`,
so a model choice would be expressible. The blocker is lifetime, not capability:
`agent start` requires an **existing pane at an interactive shell prompt inside a
live herdr session**, and waits for the agent to reach interactive readiness.

That makes a herdr-driven fleet a guest of an interactive session — the same one
a person uses for other work, which on this machine already hosts a
`speeeecies-maintainer` agent. Closing that session stops the fleet. Running
agents detached, the way `spawn` does, survives the session and the terminal and
only depends on the machine. For a driver whose whole purpose is running
unattended for long stretches, the more capable tool is the wrong one.

This driver does keep herdr's *pattern*: one agent per unit of work, its own git
worktree off the main checkout, its own branch, and it ends in a pull request for
a human to merge.

## Durability

The supervisor is a detached process. It survives losing this session or the
terminal, and it restarts cleanly from its own state directory after a crash:
agents are tracked in `.meta` files, so a fresh supervisor reaps whatever
stopped and refills to the floor.

It does **not** survive a reboot. Nothing re-launches it, because that needs an
init system and this driver deliberately installs nothing. If you want it across
reboots, wrap the command in a supervisor you already run — a systemd *user*
unit with `Restart=always` plus lingering, or whatever your session starts. That
is a deliberate omission, not an oversight: installing a service is not
something a build tool should do to your machine.

## Adding a model to the pool

1. `opencode models <provider>` to see what is offered.
2. Probe it — run one trivial prompt and check it answers. A model that appears in
   the list is not a model that works.
3. Add it to `MODEL_POOL` in `fleet.sh`. Interleave providers.
4. Note it in this file if it was surprising, especially a dead one, so the next
   coordinator does not repeat the probe.

## What the supervisor does

Each pass it reaps agents that have stopped — tearing down one that opened a pull
request, and reporting the log tail of one that stopped without one — then refills
up to `--min`. It takes the oldest open issue that no open pull request already
covers, so a second fleet pointed at the same repository will not duplicate work.
Run with `--once` to reconcile a single pass, which is what you want under cron
or in a test.

It does retry a failed agent, up to `FLEET_MAX_ATTEMPTS` (default 3) per
`kind/slug`. The budget exists because a single failure is usually a dropped
connection or a lost model route, and retiring an issue for the life of the
queue on one failure throws away a working issue. Three strikes is a real
signal: read that agent's log and fix the brief rather than letting the fleet
churn on it.

A retry **continues** the branch rather than resetting it, and that is the part
that matters for long runs. When an agent stops without a PR, teardown first
commits whatever is in the worktree onto the kept branch — otherwise
`worktree remove --force` deletes uncommitted files and the salvage promise in
its own message is a lie. The next attempt then checks the branch out where it
stands and keeps going. Four locales had already exhausted three attempts with
their work destroyed on each retry, so `FLEET_MAX_ATTEMPTS_LOCALE` defaults to 5
(`FLEET_MAX_ATTEMPTS` is 3 for species, which usually finish in one). A locale is
one manifest plus 8 to 12 species records and a flora catalog; the budget follows
the work, not the other way round.

It does not merge anything.

Two failures it must not confuse. An unreachable GitHub is reported as
`GH_UNREACHABLE` and left alone until the next poll, never as "no work left"
and never as "this agent opened no PR" — reaping on a network blip destroyed
finished worktrees. A genuinely empty queue is `STARVED`, and that line is
emitted on the transition only.

## Extending it

Work items carry an explicit `kind`, and both kinds run through the same driver:
`species-request`+`animal` issues go to `brief-species.md`, `locale-request`
issues to `brief-locale.md`. Branches are namespaced `<kind>-<issue>-<slug>` and
worktrees are namespaced by kind, because a locale and a species can carry the
same slug and must not share a worktree or a retry budget.

Locale work is heavier — 8 to 12 species plus a flora catalog, and a different
validator (`validate.py --locale <id>`) — which is why it gets its own brief
rather than a branch in the species one.
