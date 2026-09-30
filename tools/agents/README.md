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
`$WORKTREE_ROOT`, default `$HOME/worktrees/<repo-name>`. Nothing is written
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

`MODEL_POOL` is a round-robin of nine models. The point is not the list, it is
the shape: the same model published under the `opencode/` and `opencode-go/`
provider ids is **two separate quota buckets**, so interleaving the two providers
spreads load across both aggregate limits instead of exhausting one and leaving
the other idle. A persistent cursor in the state directory keeps usage even over
a long run, so no single model degrades first.

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

It does not retry a failed agent, and it does not merge anything. A pull request
that keeps failing CI is a signal to read the agent's log and fix the brief, not
to let the fleet churn on it.

## Extending it

`supervise` currently only refills species records. Locale requests
(`locale-request` issues) are the obvious next kind of work — they are heavier,
carrying 8 to 12 species plus a flora catalog — and the same worktree-per-agent
shape fits them. That needs a second brief template rather than a change to the
driver.