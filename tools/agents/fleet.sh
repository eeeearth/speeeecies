#!/usr/bin/env bash
# fleet.sh - coordinate several coding agents contributing species records in
# parallel, each in its own git worktree and branch, each ending in a pull
# request.
#
# One agent, one issue, one worktree, one branch, one PR. The fleet never merges
# and never touches main; a human does that.
#
#   tools/agents/fleet.sh list-issues
#   tools/agents/fleet.sh probe-models
#   tools/agents/fleet.sh spawn   --issue 33 --slug tiliqua-scincoides \
#                                 --scientific "Tiliqua scincoides"
#   tools/agents/fleet.sh status  [slug]
#   tools/agents/fleet.sh teardown <slug> [--force]
#   tools/agents/fleet.sh supervise [--min 3] [--max 5] [--once]
#
# Requirements: git, gh (authed, with write access), and an agent CLI on PATH
# that can run headless. This script defaults to `opencode run`; override with
# AGENT_BIN / AGENT_MODEL.
set -euo pipefail

# Resolve this script's own directory so the harness finds its own templates
# whichever checkout it is invoked from. The common failure here is running an
# unmerged harness from the main checkout, where tools/agents/ does not exist
# yet; anchoring to the script directory makes that impossible.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

# Resolved leniently: render-brief needs no repo, so the commands that do need
# one re-check rather than letting every invocation die outside a checkout.
REPO=$(git rev-parse --show-toplevel 2>/dev/null || true)
GH_REPO=${GH_REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")}
[ -n "$GH_REPO" ] || { echo "cannot determine the GitHub repo; set GH_REPO=<owner/name>" >&2; exit 2; }

# Worktrees land in a `worktrees/` sibling of the checkout, so a run stays
# inside the project directory instead of scattering across $HOME. An exported
# WORKTREE_ROOT still wins, which is how a caller redirects a whole run.
WORKTREE_ROOT=${WORKTREE_ROOT:-$(dirname "$REPO")/worktrees}
STATE_DIR=${FLEET_STATE_DIR:-$HOME/.local/state/speeeecies-fleet}
AGENT_BIN=${AGENT_BIN:-opencode}
BASE_REF=${BASE_REF:-origin/main}
FLEET_MIN=${FLEET_MIN:-3}
# FLEET_MAX is a CEILING, never a target, and the refill loop deliberately aims at
# FLEET_MIN. Growing toward the ceiling is a host decision, not a fleet decision:
# this box runs a 79C CPU package with no fan telemetry at all (hwmon exposes zero
# fan*_input nodes, so the machine broker cannot prove cooling is working either),
# and it reports state DEGRADED. The brief asks for "3-5 agents"; running the floor
# is inside that range and is the safe end of it. Raise FLEET_MIN to use the rest of
# the range once the host can show it has thermal headroom -- do not raise it because
# the queue is deep.
FLEET_MAX=${FLEET_MAX:-5}
POLL_SECONDS=${POLL_SECONDS:-60}
FLEET_MAX_ATTEMPTS=${FLEET_MAX_ATTEMPTS:-3}
# Longest run of consecutive spawns one provider may serve while it is behind on the
# lifetime tally. Catching up a 15-spawn skew by serving the lagging route fifteen
# times in a row is hammering one quota, which is the opposite of the balance the
# brief asks for. The lagging provider still gets the extra turns -- two of every
# three while it is behind -- so the skew closes over a long window instead.
FLEET_MAX_PROVIDER_STREAK=${FLEET_MAX_PROVIDER_STREAK:-2}
# A locale is one manifest plus 8-12 species records and a flora catalog, so
# it exhausts an agent's budget far more often than a single species does.
# Retiring a locale after three tries was throwing away unfinished work that a
# fourth would have finished; four locales have now burned all three.
FLEET_MAX_ATTEMPTS_LOCALE=${FLEET_MAX_ATTEMPTS_LOCALE:-5}
# How long a spawn attempt counts against a slug's retry budget. The budget used to
# be permanent: nothing ever decremented it except a model-route refund, so an agent
# that ran and produced no PR spent an attempt exactly as if the ISSUE were
# unworkable. At a 54% no-PR rate that drained the queue outright -- every candidate
# reached its cap without the issue ever being tested, and the fleet sat at
# state=STARVED with three perfectly spawnable issues in front of it. Attempts now
# expire, so a budget regenerates while churn inside any single window stays bounded.
FLEET_ATTEMPT_COOLDOWN_SECONDS=${FLEET_ATTEMPT_COOLDOWN_SECONDS:-86400}
BRANCH_PREFIX=${BRANCH_PREFIX:-$(gh api user -q .login 2>/dev/null || echo contributor)}
BRIEF_SPECIES=${BRIEF_SPECIES:-$SCRIPT_DIR/brief-species.md}
BRIEF_LOCALE=${BRIEF_LOCALE:-$SCRIPT_DIR/brief-locale.md}
BRIEF_TEMPLATE=${BRIEF_TEMPLATE:-}
PERMISSIONS=${PERMISSIONS:-$SCRIPT_DIR/agent-permissions.json}
RECIPES=${RECIPES:-$SCRIPT_DIR/recipes.md}
VISUAL_CHECK=${VISUAL_CHECK:-0}


mkdir -p "$WORKTREE_ROOT" "$STATE_DIR"
# Archive of past agent runs. Teardown moves logs here instead of deleting them,
# so a slug that failed before it succeeded still leaves evidence behind.
mkdir -p "$STATE_DIR/archive" 2>/dev/null || true

# --- the free-tier model pool ------------------------------------------------
# Probed working. The same model published under two provider ids is two routes
# with separate quotas, so using both spreads load across both aggregate limits
# instead of exhausting one. Extend a pool after `probe-models` finds a model
# that works; never add one you have not probed.
# DEAD: ling-3.0-flash-fin-free returns "Not Found: Cannot find any route".
#
# Zen and Go are cycled independently rather than as one list. A single cursor
# over a combined list cannot balance them: with six zen routes and two go ones
# it serves three zen spawns per go one, which is what it did (17 zen, 6 go).
# Split by capability, not just by provider. These two lists were one list, so the
# cursor served a *flash* and a *lightning* route as often as the largest free model
# -- the brief asks for larger, research-capable routes, and rotating a 1B-class
# model against nemotron-3-ultra at equal frequency is the opposite of that. The
# small ones are kept, probed and known-good, but are not auto-rotated: they are
# here for an operator to reach for when a primary route is failing and the work
# does not need the capability.
MODEL_POOL_ZEN=(
  "opencode/nemotron-3-ultra-free"            # largest free model
  "opencode/space-bunny-free"                 # same model as the go route
  "opencode/longcat-2.5-preview-free"
  "opencode/muse-spark-1.3-contributor-free"  # contributor tier
)
MODEL_POOL_ZEN_FALLBACK=(
  "opencode/nemotron-3.5-lightning-free"      # fast, small
  "opencode/mimo-v2.6-flash-free"             # flash, small
)
MODEL_POOL_GO=(
  "opencode-go/space-bunny-free"
  "opencode-go/longcat-2.5-preview-free"
)
# No probed go route is both large and cheap enough to displace the two above, so
# the go fallback list is deliberately empty rather than invented.
MODEL_POOL_GO_FALLBACK=()
# Everything probed, for `probe-models`. Not the rotation order.
MODEL_POOL=( "${MODEL_POOL_ZEN[@]}" "${MODEL_POOL_GO[@]}" \
             "${MODEL_POOL_ZEN_FALLBACK[@]}" "${MODEL_POOL_GO_FALLBACK[@]}" )
model_variant() {
  case "$1" in
    *nemotron-3.5-lightning*) echo "medium" ;;
    *)                        echo "high" ;;
  esac
}

# --- helpers -----------------------------------------------------------------
say()  { printf '%s\n' "$*"; }
die()  { printf '%s\n' "$*" >&2; exit 1; }

slug_ok() { case "$1" in ''|*[!a-z0-9-]*) return 1;; *) return 0;; esac; }

need_repo() { [ -n "$REPO" ] || die "not inside a git repository; run this from a checkout of the project"; }

# Always exit 0. A missing or unreadable meta is an expected state -- a pidfile
# can outlive its meta, and the orphan sweep exists precisely to clean that up --
# but sed failing inside the pipeline made pipefail fail the caller's assignment,
# so the caller died before reaching its own guard. An orphan pidfile therefore
# killed the supervisor instead of being reaped.
meta_get() { sed -n "s/^$2=//p" "$STATE_DIR/$1.meta" 2>/dev/null | head -1 || true; }

provider_of() {  # which provider the cursor points at, honouring a backoff marker
  local p
  p=$(cat "$STATE_DIR/provider_cursor" 2>/dev/null || echo zen)
  if [ -f "$STATE_DIR/provider_fail_$p" ]; then
    case "$p" in zen) p=go;; *) p=zen;; esac
  fi
  printf '%s' "$p"
}

provider_note_failure() {  # provider; skip it for one turn after a route failure
  : > "$STATE_DIR/provider_fail_$1"
}

# Spawns served per provider, straight from the tally. Returns 0 for a provider
# with no row yet, so a fresh state dir compares as level instead of erroring.
provider_tally() {  # provider -> integer
  local v
  v=$(awk -v k="$1" '$1==k {print $2}' "$STATE_DIR/provider_counts" 2>/dev/null | tail -1) || v=""
  printf '%s' "${v:-0}"
}

provider_of_model() {  # model id -> zen|go
  case "$1" in opencode-go/*) echo go;; *) echo zen;; esac
}

# Running counts per provider. The status line only shows which model is next,
# which cannot answer "is this fleet actually balanced over time"; that needs a
# tally of what was really served.
note_spawn_provider() {  # model id; tally what was really served per provider
  local p f cur
  p=$(provider_of_model "$1")
  f="$STATE_DIR/provider_counts"
  # A fresh state dir has no tally yet. An awk failure inside a pipeline is fatal
  # under pipefail even with stderr suppressed, so that killed the first spawn on a
  # clean state dir -- after the agent launched, before queue.tsv was written.
  [ -f "$f" ] || : > "$f" 2>/dev/null || return 0
  cur=$(awk -v k="$p" '$1==k {print $2}' "$f" 2>/dev/null | tail -1) || cur=""
  printf '%s %s\n' "$p" "$(( ${cur:-0} + 1 ))" > "$f.tmp"
  awk -v k="$p" '$1!=k' "$f" 2>/dev/null >> "$f.tmp" || true
  mv "$f.tmp" "$f"
}

# Write a state file, reporting failure instead of dying. These writes run in the
# main poll loop where errexit is ACTIVE, so a full or read-only state dir killed
# the supervisor mid-poll -- and with it every running agent, since nothing
# reaps or refills without it. A state write failing is a degraded fleet, not a
# reason to stop working.
write_state() {  # path; stdin -> path. 0 on success.
  local path="$1"
  cat > "$path" 2>/dev/null || {
    say "WARNING could not write $path (state dir full or read-only?)"
    return 1
  }
  return 0
}

reconcile_provider_counts() {
  # Rebuild the tally from the spawn lines the log already records, so the two
  # cannot drift. It had drifted: provider_counts read one higher than any
  # count derivable from supervisor.log, which is exactly the property the tally
  # exists to provide. Counting the log makes the count auditable by
  # construction instead of by parallel bookkeeping.
  local log="$STATE_DIR/supervisor.log" f="$STATE_DIR/provider_counts"
  local z=0 g=0 m n=0
  [ -f "$log" ] || return 0
  # The spawn line reads "... (issue N, model <id>)" -- space, not "model=".
  while read -r m; do
    [ -n "$m" ] || continue
    n=$((n + 1))
    if [ "$(provider_of_model "$m")" = go ]; then g=$((g + 1)); else z=$((z + 1)); fi
  done < <(sed -n 's/^spawned .*, model \([^)]*\)).*/\1/p' "$log" 2>/dev/null)
  # Refuse to publish a tally that contradicts the log's own spawn count. A
  # pattern typo here would otherwise silently reset a correct tally to zero,
  # which is precisely the drift this function exists to remove.
  local logged; logged=$(grep -c '^spawned ' "$log" 2>/dev/null) || logged=0
  if [ "$logged" -gt 0 ] && [ "$n" -ne "$logged" ]; then
    say "WARNING: parsed $n models from $logged spawn lines; keeping the existing tally rather than publishing a wrong one"
    return 0
  fi
  printf 'zen %s\ngo %s\n' "$z" "$g" > "$f.tmp" 2>/dev/null && mv "$f.tmp" "$f"
  say "reconciled the provider tally from the log: zen=$z go=$g"
}

note_route_failure() {  # slug; 0 when the agent died on routing, 1 otherwise
  local model
  model=$(meta_get "$1" model)
  [ -n "$model" ] && [ -f "$STATE_DIR/$1.log" ] || return 1
  # Tail only. Grepping the whole log refunded the attempt whenever an agent so
  # much as mentioned a rate limit while researching, which is not a routing
  # death and must not give the issue a free pass.
  # 429 only counts as a status, never as a digit run: a species log cites
  # Wikidata property ids like P4293, and a bare 429 alternative matched inside
  # it. It now has to look like a status. "api" is deliberately NOT a context
  # word, because every species log says "the Wikidata API"; the words that
  # actually indicate the agent's own provider failing are below.
  local recent
  recent=$(tail -40 "$STATE_DIR/$1.log" 2>/dev/null) || return 1

  # Unambiguous routing deaths.
  if grep -qiE "cannot find any route|no route (found|to)|model [^ ]+ .{0,24}(not (found|available)|unavailable|overloaded|deprecated)|(rate limit|too many requests|quota exceeded).{0,60}(opencode|provider|router|credential|api key|token|model)|(opencode|provider|router|credential|api key|token|model).{0,60}(rate limit|too many requests|quota exceeded)" <<<"$recent"; then
    provider_note_failure "$(provider_of_model "$model")"
    return 0
  fi

  # A 429 counts as a routing death only when it also names the provider. A real
  # agent log here carries `FETCH-ERROR: HTTP Error 429: Too Many Requests` when
  # Wikidata throttles a fetch, and `<urlopen error 429>` when urllib does;
  # matching those marked a healthy provider as failed and refunded an attempt
  # the agent had earned. Enumerating the fetchers' own wording does not close
  # this -- every marker added matched one tool and missed the next -- so the
  # test is inverted instead: without provider context, a 429 is not the
  # provider failing. That errs toward missing a backoff rather than blaming a
  # healthy model and discarding real work.
  if grep -qiE '(opencode|provider|router|credential|api key|token|model)[^\n]{0,80}(429|too many requests)|(429|too many requests)[^\n]{0,80}(opencode|provider|router|credential|api key|token|model)' <<<"$recent"; then
    provider_note_failure "$(provider_of_model "$model")"
    return 0
  fi
  return 1
}

refund_attempt() {  # kind slug; a dead model route is not the issue's fault
  local q="$STATE_DIR/queue.tsv" last
  [ -f "$q" ] || return 0
  last=$(awk -F'\t' -v k="$1/$2" '$2 "/" $3 == k { n = NR } END { print n + 0 }' "$q")
  [ "$last" -gt 0 ] || return 0
  awk -F'\t' -v n="$last" 'NR != n' "$q" > "$q.tmp" && mv "$q.tmp" "$q"
  say "refunded one retry attempt for $2: the failure was a model route, not the issue"
}

next_model() {  # peek only, never mutates: the status line calls this every poll
  local p i n
  p=$(provider_of)
  i=$(cat "$STATE_DIR/model_cursor_$p" 2>/dev/null || echo 0)
  if [ "$p" = zen ]; then
    n=${#MODEL_POOL_ZEN[@]}
    if [ "$n" -gt 0 ]; then printf '%s' "${MODEL_POOL_ZEN[$(( i % n ))]}"; return 0; fi
  else
    n=${#MODEL_POOL_GO[@]}
    if [ "$n" -gt 0 ]; then printf '%s' "${MODEL_POOL_GO[$(( i % n ))]}"; return 0; fi
  fi
  case "$p" in
    zen) n=${#MODEL_POOL_GO[@]}; [ "$n" -gt 0 ] && printf '%s' "${MODEL_POOL_GO[0]}" && return 0 ;;
    *)   n=${#MODEL_POOL_ZEN[@]}; [ "$n" -gt 0 ] && printf '%s' "${MODEL_POOL_ZEN[0]}" && return 0 ;;
  esac
  return 1
}

advance_model() {  # step that provider's own cursor, then hand over to the other
  local p i n other
  p=$(provider_of)
  i=$(cat "$STATE_DIR/model_cursor_$p" 2>/dev/null || echo 0)
  if [ "$p" = zen ]; then n=${#MODEL_POOL_ZEN[@]}; else n=${#MODEL_POOL_GO[@]}; fi
  if [ "$n" -gt 0 ]; then
    printf '%s\n' "$(( (i + 1) % n ))" > "$STATE_DIR/model_cursor_$p"
  fi
  rm -f "$STATE_DIR"/provider_fail_* 2>/dev/null || true
  # Serve whoever is behind, not simply the other one. Strict alternation froze a
  # lifetime skew in place: the tally read zen 40 / go 25 and every handover since
  # preserved that 15-spawn gap instead of closing it. Going by the lower count
  # converges the skew and then degrades to plain alternation once they are level,
  # which is what "balance their usage" actually asks for.
  local z_tally g_tally streak
  z_tally=$(provider_tally zen) || z_tally=0
  g_tally=$(provider_tally go) || g_tally=0
  streak=$(cat "$STATE_DIR/provider_streak" 2>/dev/null || echo 0) || streak=0
  case "$streak" in ''|*[!0-9]*) streak=0 ;; esac
  # Defaulted at the point of use as well as at the top of the file: these functions
  # get exercised by harnesses that supply STATE_DIR and the pools but not every
  # global, and under `set -u` one unbound knob aborts the caller mid-spawn.
  local max_streak="${FLEET_MAX_PROVIDER_STREAK:-2}"
  # next_model serves the current cursor BEFORE advance_model runs, so the run length
  # if this provider is kept is streak+1, not streak. Comparing streak alone let the
  # run reach FLEET_MAX_PROVIDER_STREAK+1 -- a cap of 2 permitting 3 in a row.
  if [ "$(( streak + 1 ))" -ge "$max_streak" ]; then
    # This provider has had its bounded burst. Alternate even though it is still
    # behind: closing the remaining skew is worth less than not pinning one route.
    case "$p" in zen) other=go;; *) other=zen;; esac
  elif [ "$z_tally" -lt "$g_tally" ]; then other=zen
  elif [ "$g_tally" -lt "$z_tally" ]; then other=go
  else case "$p" in zen) other=go;; *) other=zen;; esac
  fi
  # Persist the streak, and fail closed if it cannot be recorded. Unguarded, a
  # failed write aborted advance_model under `set -e` before provider_cursor was
  # updated -- and advance_model runs after the agent has already launched, so the
  # next spawn then read a stale cursor and the wedge looked like a route failure.
  # If the streak cannot be stored, the cap bookkeeping cannot be trusted, so hand
  # over rather than keep the same provider: that keeps the burst bounded even when
  # the state dir is unwritable, and still returns a usable cursor.
  local next_streak=0
  if [ "$other" = "$p" ]; then next_streak=$(( streak + 1 )); fi
  if ! printf '%s\n' "$next_streak" | write_state "$STATE_DIR/provider_streak"; then
    say "WARNING could not persist the provider streak; alternating rather than risk an unbounded run"
    case "$p" in zen) other=go;; *) other=zen;; esac
  fi
  # Guarded too: a cursor that cannot be written is survivable, an aborted
  # advance_model after a committed spawn is not.
  printf '%s\n' "$other" | write_state "$STATE_DIR/provider_cursor" || true
}

# The value of a pid's --dir argument, read from NUL-separated argv. Empty when
# the process has no --dir. This must be exact argv, never a substring of the
# rendered command line: the whole brief is passed via --auto "$(cat brief)", so
# every agent's command line names every other agent's worktree, and a substring
# match reported --dir /wt/species-foo-bar as a hit for /wt/species-foo.
pid_arg_dir() {
  local pid="$1" arg prev="" dir=""
  [ -r "/proc/$pid/cmdline" ] || return 0
  while IFS= read -r -d '' arg; do
    [ "$prev" = "--dir" ] && dir="$arg"
    prev="$arg"
  done < "/proc/$pid/cmdline"
  printf '%s' "$dir"
}

# 0 when some live agent process has --dir exactly equal to this worktree.
agent_for_worktree() {  # worktree -> 0/1
  local wt="$1" p d
  [ -n "$wt" ] || return 1
  for p in $(pgrep -f -- "$AGENT_BIN run" 2>/dev/null); do
    d=$(pid_arg_dir "$p")
    [ "$d" = "$wt" ] && return 0
  done
  return 1
}

# 0 when a process in the leader's group has --dir exactly equal to the
# worktree: proof the pid still serves this agent rather than being a recycled,
# unrelated process.
group_serves_worktree() {  # worktree leader -> 0/1
  local wt="$1" leader="$2" p d
  [ -n "$wt" ] && [ -n "$leader" ] || return 1
  for p in $(ps -eo pid,pgid --no-headers 2>/dev/null | awk -v g="$leader" '$2==g {print $1}'); do
    d=$(pid_arg_dir "$p")
    [ "$d" = "$wt" ] && return 0
  done
  return 1
}

agent_running() {  # slug -> 0 running, 1 not
  local pf="$STATE_DIR/$1.pid" pid wt
  wt=$(meta_get "$1" worktree)
  # A deleted worktree means the agent cannot commit and is working out of a
  # directory that no longer exists. It was still counted as live, so the fleet
  # reported healthy while an agent was stranded.
  [ -d "$wt" ] || return 1
  # Without a worktree there is nothing to match a process against, and the
  # comparison below would be "" = "" -- true for any process with no --dir,
  # counting it live forever. Unknown means not-running.
  [ -n "$wt" ] || return 1
  if [ -f "$pf" ]; then
    pid=$(tr -dc '0-9' < "$pf" 2>/dev/null)
    # `kill -0` alone is not proof: a pid can be recycled, and then the fleet
    # would count an unrelated process as its agent and later signal it.
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      [ "$(pid_arg_dir "$pid")" = "$wt" ] && return 0
      group_serves_worktree "$wt" "$pid" && return 0
      return 1
    fi
    return 1
  fi
  agent_for_worktree "$wt"
}

stop_signal() {  # pid -> 0. Signals the pid's process group, waits, escalates.
  local pid="$1" i pgid self
  [ -n "$pid" ] || return 0
  pgid=$(awk '{print $5}' "/proc/$pid/stat" 2>/dev/null)
  self=$(awk '{print $5}' "/proc/$$/stat" 2>/dev/null)
  # Never signal the group we are in. A stale pidfile whose pid has been
  # recycled into this shell's own group would otherwise make `kill -- -$pgid`
  # terminate the supervisor, which is worse than leaking an agent.
  if [ -n "$pgid" ] && [ -n "$self" ] && [ "$pgid" = "$self" ]; then
    say "  pid $pid shares this process group; refusing to signal it"
    return 1
  fi
  if [ -n "$pgid" ] && [ "$pgid" != "$pid" ]; then
    kill -TERM -- "-$pgid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || return 0
  else
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || return 0
  fi
  # `sleep 9>&-`: children spawned here inherit the lock fd otherwise. An
  # orphaned poll sleep, reparented to init when the supervisor was killed, kept
  # holding it, so an immediate restart was refused with "another supervisor
  # already holds" while no supervisor existed.
  for i in $(seq 1 10); do kill -0 "$pid" 2>/dev/null || break; sleep 1 9>&-; done
  if kill -0 "$pid" 2>/dev/null; then
    say "  pid $pid ignored SIGTERM; sending SIGKILL to the group"
    if [ -n "$pgid" ] && [ "$pgid" != "$pid" ]; then
      kill -KILL -- "-$pgid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
    else
      kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
    fi
    sleep 1 9>&-
  fi
  return 0
}

stop_agent() {  # slug -> 0. Signals the whole process group and waits it out.
  local pf="$STATE_DIR/$1.pid" pid i wt
  # Read once, for both branches. It used to be assigned only inside the no-pidfile
  # branch, so the ordinary pidfile path reached an unbound `wt` under `set -u`
  # and aborted -- which meant a forced teardown removed the worktree and the
  # metadata while leaving the agent running, the exact failure all of this
  # process ownership work exists to prevent.
  wt=$(meta_get "$1" worktree)
  # An unknown worktree is a failure to identify the process, never a match. A
  # pidfile whose meta is gone yields wt="", and so does pid_arg_dir for a
  # process with no --dir; comparing "" to "" passed the ownership guard and
  # stop_signal then signalled whatever group it was handed, which is how the
  # supervisor terminated itself.
  if [ -z "$wt" ]; then
    say "  no worktree recorded for $1; not signalling anything"
    rm -f "$pf"
    return 0
  fi
  # No pidfile does not mean nothing is running: agents launched before the
  # pidfile existed have none, and returning early is how teardown came to mean
  # "remove the metadata" while the process carried on in a deleted directory.
  # Matching is exact --dir argv equality for the reason given above pid_arg_dir.
  if [ ! -f "$pf" ]; then
    local stopped_all=0
    for pid in $(pgrep -f -- "$AGENT_BIN run" 2>/dev/null); do
      [ "$(pid_arg_dir "$pid")" = "$wt" ] || continue
      say "  no pidfile for $1; stopping its agent on $wt (pid $pid)"
      # stop_signal refuses when the target shares our process group, and can
      # fail to signal. Ignoring that made a refusal indistinguishable from a
      # successful stop: rc=0 and "stopping" logged while the agent ran on.
      if ! stop_signal "$pid"; then
        stopped_all=1
      elif [ -r "/proc/$pid/stat" ] \
           && [ "$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null)" != Z ]; then
        say "  pid $pid survived the stop"
        stopped_all=1
      fi
    done
    return $((stopped_all))
  fi
  pid=$(tr -dc '0-9' < "$pf" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    # Only signal a group this worktree owns. Trusting a bare kill -0 lets a
    # recycled pid be counted as our agent and then killed.
    if [ "$(pid_arg_dir "$pid")" != "$wt" ] && ! group_serves_worktree "$wt" "$pid"; then
      say "  pid $pid does not serve $wt; treating the pidfile as stale, not signalling"
      rm -f "$pf"
      return 0
    fi
    say "stopping $1 (pid $pid) and its process group"
    # stop_signal refuses when the target shares our own process group, and can
    # fail to signal. Ignoring that made a refusal indistinguishable from a
    # successful stop: the caller logged "stopped" and carried on while the agent
    # was still running. Report what actually happened.
    if ! stop_signal "$pid"; then
      say "  $1 was NOT stopped; it shares this process group or could not be signalled"
      rm -f "$pf"
      return 1
    fi
    # A killed child that has not been reaped keeps its /proc entry and still
    # answers `kill -0`, so that alone reports a successful SIGKILL as a survivor.
    # Read the process state: Z means it is gone.
    if [ -r "/proc/$pid/stat" ] \
       && [ "$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null)" != Z ]; then
      say "  $1 survived the stop (pid $pid still alive)"
      rm -f "$pf"
      return 1
    fi
    say "  $1 stopped"
  fi
  rm -f "$pf"
  return 0
}

# The researched recipe for one issue, out of recipes.md. Markers are matched
# exactly, so recipe:9 never matches recipe:39: the closing ` -->` is part of
# the pattern.
recipe_for_issue() {  # issue -> recipe text on stdout, empty if none
  local issue="$1"
  [ -f "$RECIPES" ] || return 0
  # Exact string match, not regex: `recipe:9 -->` must not match `recipe:39 -->`.
  awk -v want="$issue" '
    $0 == "<!-- recipe:" want " -->" { inblock = 1; next }
    $0 == "<!-- /recipe:" want " -->" { inblock = 0 }
    inblock { print }
  ' "$RECIPES"
}

render_brief() {  # issue slug sci regions worktree branch outfile [kind] [template]
  local issue="$1" slug="$2" sci="$3" regions="$4" wpath="$5" branch="$6" out="$7" recipe
  local kind="${8:-species}" template="${9:-}" status="${10:-}"
  if [ -z "$template" ]; then
    if [ "$kind" = locale ]; then template="$BRIEF_LOCALE"; else template="$BRIEF_SPECIES"; fi
  fi
  [ -f "$template" ] || die "brief template not found: $template"
  recipe=$(recipe_for_issue "$issue")
  [ -n "$recipe" ] || recipe="No researched recipe for issue #$issue. Use the general table in this brief, and say in the PR that you had no recipe."

  # python3, not sed: recipe text carries slashes and ampersands, which are
  # meaningful in a sed replacement.
  ISSUE="$issue" SLUG="$slug" SCIENTIFIC="$sci" REGIONS="$regions" \
  WORKTREE="$wpath" BRANCH="$branch" BASE_REF="$BASE_REF" REPO="$REPO" \
GH_REPO="$GH_REPO" VISUAL_CHECK="$VISUAL_CHECK" RECIPE="$recipe" KIND="$kind" \
    STATUSFILE="$status" \
    python3 -c '
import os, sys
tpl, out = sys.argv[1], sys.argv[2]
with open(tpl, encoding="utf-8") as fh:
    text = fh.read()
for key, val in os.environ.items():
    text = text.replace("{{%s}}" % key, val)
with open(out, "w", encoding="utf-8") as fh:
    fh.write(text)
' "$template" "$out"

  local leftover
  leftover=$(grep -o '{{[A-Z_]*}}' "$out" 2>/dev/null | sort -u | tr '\n' ' ' || true)
  [ -z "$leftover" ] || die "brief still has unsubstituted placeholders: $leftover"
}

pr_field() {  # slug field jq-expr; GHERR when the lookup itself failed
  local br jq err
  br=$(meta_get "$1" branch)
  [ -n "$br" ] || { echo "-"; return; }
  # Default to the bare field rather than $3 bare: `set -u` makes a missing third
  # argument fatal, and that killed the supervisor the first time an agent
  # finished, which is exactly when the reap loop needs to run.
  jq=${3:-".$2"}
  err=$(gh pr view "$br" --repo "$GH_REPO" --json "$2" -q "$jq" 2>&1) && {
    printf '%s' "$err"; return 0; }
  # "no pull requests found" is a real answer: the agent opened nothing. Anything
  # else is GitHub being unreachable, which must not be read as "no PR" or the
  # reap destroys a finished agent's worktree and retries its issue.
  case "$err" in
    *"no pull requests found"*|*"Could not resolve to a"*|*"not found"*) echo "-" ;;
    *) echo "GHERR" ;;
  esac
}

cmd_list_issues() {
  need_repo
  # Open, unassigned work: species-request+animal and locale-request. Skips
  # anything already carried by an open PR so two fleets never duplicate work.
  # Columns: issue, slug, kind, title. A locale slug is the locale id, which the
  # issue title carries in its final parentheses.
  # Not `|| true`: the caller must be able to tell a failed query from an empty
  # result, or a GitHub outage reads as "no work left".
  gh issue list --repo "$GH_REPO" --state open --limit 200 --json number,title,labels,assignees \
    | python3 -c '
import json,sys
iss=json.load(sys.stdin)
for i in iss:
    labs={l["name"] for l in i["labels"]}
    if i["assignees"]: continue
    t=i["title"]
    kind=None
    if "species-request" in labs and "animal" in labs and "phase-2" not in labs:
        kind="species"
    elif "locale-request" in labs and "phase-2" not in labs:
        kind="locale"
    if kind is None: continue
    tail=t[t.rindex("(")+1:-1].strip() if "(" in t and t.rstrip().endswith(")") else ""
    slug=tail.lower().replace(" ","-") if tail else ""
    if kind=="locale" and not slug: continue
    print(f'"'"'{i["number"]}\t{slug}\t{kind}\t{t}'"'"')
' | while IFS=$'\t' read -r n slug kind title; do
      [ -n "$slug" ] || { slug=$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-'); }
      pr_st=0; pr_for_slug "$slug" "$kind" >/dev/null 2>&1 || pr_st=$?
      # Propagate a failed lookup so the supervisor reports GH_UNREACHABLE
      # instead of treating the issue as free and duplicating a live agent.
      if [ "$pr_st" = 2 ]; then exit 2; fi
      if [ "$pr_st" = 0 ]; then continue; fi
      record_exists "$slug" "$kind" && continue
      printf '%s\t%s\t%s\t%s\n' "$n" "$slug" "$kind" "$title"
    done
}

# Is there already an open PR touching species/<slug>/ ?
pr_for_slug() {  # slug kind; a locale lives under locales/, a species under species/
  local slug="$1" kind="${2:-species}" dir n
  [ -n "$slug" ] || return 1
  case "$kind" in locale) dir="locales/$slug/";; *) dir="species/$slug/";; esac
  # A failed lookup must not read as "no PR": the caller would then spawn a
  # second agent for an issue whose first agent already has a PR open.
  n=$(gh pr list --repo "$GH_REPO" --state open --limit 100 --json number,files \
          -q "[.[] | select(any(.files[]; .path | startswith(\"$dir\")))] | length" 2>&1) || return 2
  case "$n" in
    ''|*[!0-9]*) return 2 ;;
  esac
  [ "$n" != "0" ]
}

# Some request issues outlive the work that satisfied them: #2 and #3 still ask
# for records PR #42 already added, so building them again would collide.
record_exists() {  # slug kind; either work type counts as already merged
  need_repo
  local slug="$1" kind="${2:-species}"
  case "$kind" in
    locale) git -C "$REPO" cat-file -e "$BASE_REF:locales/$slug/locale.json" 2>/dev/null ;;
    *)      git -C "$REPO" cat-file -e "$BASE_REF:species/$slug/species.json" 2>/dev/null ;;
  esac
}

cmd_probe_models() {
  need_repo
  # Confirm each pooled model still answers before trusting the rotation. The
  # prompt is a positional argument: `opencode run` does not read it from stdin.
  local m ok
  for m in "${MODEL_POOL[@]}"; do
    if timeout 300 "$AGENT_BIN" run --model "$m" --dir "$REPO" \
         'Reply with exactly: PROBE_OK' 2>/dev/null | grep -q PROBE_OK; then
      ok=1
    else
      ok=0
    fi
    printf '%-46s %s\n' "$m" "$([ "$ok" = 1 ] && echo ok || echo FAIL)"
  done
}

cmd_spawn() {
  need_repo
  local issue slug sci model variant kind pr_st
  issue=""; slug=""; sci=""; model=""; variant=""; kind="species"
  while [ $# -gt 0 ]; do
    case "$1" in
      --issue) issue=$2; shift 2;;
      --slug) slug=$2; shift 2;;
      --scientific) sci=$2; shift 2;;
      --kind) kind=$2; shift 2;;
      --model) model=$2; shift 2;;
      --variant) variant=$2; shift 2;;
      *) die "unknown argument: $1";;
    esac
  done
  case "$kind" in species|locale) :;; *) die "--kind must be species or locale: $kind";; esac
  [ -n "$issue" ] && [ -n "$slug" ] || die "need --issue --slug"
  # A locale has no scientific name; its slug is the locale id. Species do.
  if [ "$kind" = species ]; then
    [ -n "$sci" ] || die "need --scientific for a species"
  else
    sci="$slug"
  fi
  slug_ok "$slug" || die "slug must be lowercase letters, digits and dashes: $slug"
  local brief_tpl
  if [ -n "$BRIEF_TEMPLATE" ]; then
    brief_tpl="$BRIEF_TEMPLATE"
  elif [ "$kind" = locale ]; then
    brief_tpl="$BRIEF_LOCALE"
  else
    brief_tpl="$BRIEF_SPECIES"
  fi
  [ -f "$brief_tpl" ] || die "brief template not found: $brief_tpl"
  slug=$(printf '%s' "$slug" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
  slug_ok "$slug" || die "slug must normalise to lowercase letters, digits and dashes: $slug"

  local state
  state=$(gh issue view "$issue" --repo "$GH_REPO" --json state,assignees \
          -q '.state + "|" + ([.assignees[].login] | join(","))' 2>/dev/null || echo "ERR|")
  case "$state" in
    OPEN\|) : ;;
    OPEN\|*) die "issue $issue is already assigned to ${state#OPEN|}; leave it to them";;
    *) die "issue $issue is not an open species-request animal issue (got '$state')";;
  esac
  pr_st=0; pr_for_slug "$slug" "$kind" || pr_st=$?
  case "$pr_st" in
    2) die "cannot verify whether $kind/$slug/ already has a PR (GitHub unreachable); refusing to risk a duplicate" ;;
    0) die "an open PR already touches $kind/$slug/; pick another issue" ;;
  esac
  if record_exists "$slug" "$kind"; then
    case "$kind" in
      locale) die "locales/$slug/locale.json already exists on $BASE_REF; the issue is stale";;
      *) die "species/$slug/species.json already exists on $BASE_REF; the issue is stale";;
    esac
  fi

  [ -n "$model" ] || model=$(next_model)
  [ -n "$variant" ] || variant=$(model_variant "$model")

  local branch wpath
  branch="$BRANCH_PREFIX/$kind-$issue-$slug"
  wpath="$WORKTREE_ROOT/$kind-$slug"
  # Count the attempt BEFORE the spawn can fail. The row used to be appended only
  # on a committed spawn, so a slug blocked by a permanent collision never
  # incremented the ledger and was retried forever: one slug logged 217 refusals
  # while sitting at 1 of 3 attempts, and the retry budget the code relies on to
  # "stop retrying a genuinely broken issue" never engaged. Placed after the
  # issue-state and duplicate-PR checks so those do not burn budget, and before
  # the collision check so they do. refund_attempt still strips the row when the
  # death was a model route rather than the issue's fault.
  # Fourth column is the epoch the attempt was spent, so the budget can expire.
  printf '%s\t%s\t%s\t%s\n' "$issue" "$kind" "$slug" "$(date +%s)" \
    >> "$STATE_DIR/queue.tsv"
  [ -e "$wpath" ] && die "worktree path already exists: $wpath"
  # A leftover branch is a retry, not a fatal collision, and cmd_spawn is called
  # directly from the refill loop, so a die() here would exit the whole supervisor.
  # Continue the branch where it stands: a locale can legitimately need several
  # attempts, and resetting to base discarded everything the previous attempt built.
  local worktree_add
  if git -C "$REPO" show-ref --quiet "refs/heads/$branch"; then
    say "retrying $slug: continuing $branch at $(git -C "$REPO" rev-parse --short "$branch")"
    worktree_add=(git worktree add "$wpath" "$branch")
  else
    worktree_add=(git worktree add -b "$branch" "$wpath" "$BASE_REF")
  fi

  # Prune first: an earlier spawn that died after `git worktree add` left a
  # registration with no directory, and git then refuses the path forever
  # with "missing but already registered worktree" -- the slug is wedged.
  # The status must be checked by hand. cmd_spawn is invoked as
  # `if ! spawn_err=$( ( cmd_spawn ... ) 2>&1 )`, and bash suspends `set -e`
  # inside a condition context, so a failed `git worktree add` did not abort
  # anything: the spawn carried on, wrote a .meta and a .pid for an agent that
  # never existed, and logged "spawned". The branch was already checked out by a
  # worktree outside WORKTREE_ROOT, git refused, and the fleet counted a phantom
  # and reported live=3 with two real agents. stderr is deliberately not
  # redirected: git's own `fatal:` is the useful diagnostic here.
  if ! ( cd "$REPO" && git worktree prune && git fetch --quiet origin && "${worktree_add[@]}" ) >/dev/null; then
    say "could not create a worktree for $slug at $wpath"
    return 1
  fi
  # Undo a partially-created spawn. An EXIT trap cannot do this job: it fires
  # when the shell exits, expanding $slug and $wpath long after this function's
  # locals were gone, and it printed `slug: unbound variable` while leaking the
  # very worktree it was meant to undo. Guarded `return 1` paths return from a
  # function, so it never fired for them at all.
  # 0 when the launched agent published its pidfile. Bounded, so a slow start
  # cannot stall the refill loop while it waits for an agent that never comes.
  spawn_started() {
    local slug="$1" i p
    for i in $(seq 1 10); do
      p="$STATE_DIR/$slug.pid"
      # -f as well as -s: `-s` is TRUE for a directory (it has a nonzero size),
      # so a directory at the pidfile path satisfied this check and a launch that
      # never happened was reported as started. Also require a numeric pid, since
      # anything truncated to digits could come from a partially written file.
      if [ -f "$p" ] && [ -s "$p" ] && tr -dc '0-9' < "$p" | grep -q '[0-9]'; then
        return 0
      fi
      sleep 0.2 9>&-
    done
    return 1
  }

  # launch_tmp is assigned further down, and a failure before that point made this
  # reference unbound under `set -u`, so the rollback aborted before removing the
  # worktree it was called to undo.
  local launch_tmp=""
  # force=1 for a launch that failed after publication: there the .meta is the
  # thing being undone, so its presence must not suppress the worktree removal.
  spawn_rollback() {
    local force="${1:-0}"
    [ "$force" = 1 ] || [ ! -f "$STATE_DIR/$slug.meta" ] || return 0
    [ -d "$wpath" ] || return 0
    say "rolling back the worktree for $slug"
    git -C "$REPO" worktree remove --force "$wpath" 2>/dev/null
    git -C "$REPO" worktree prune 2>/dev/null
    [ -n "$launch_tmp" ] && rm -f "$launch_tmp" 2>/dev/null
    rm -f "$launch" 2>/dev/null
    return 0
  }

  # Region hints come from the issue body, so the agent does not have to guess.
  local regions
  # shellcheck disable=SC2016
  regions=$(gh issue view "$issue" --repo "$GH_REPO" --json body \
            | python3 -c 'import json,re,sys
b=json.load(sys.stdin)["body"] or ""
m=re.search(r"[Ss]uggested regions.*?\n(.*?)(\n\n|\Z)", b, re.S)
print(" ".join(re.findall(r"`([A-Z]{2}(?:-[A-Z0-9]{1,3})?)`", m.group(1))) if m else "")') \
    || regions=""

  local log="$STATE_DIR/$slug.log" status="$STATE_DIR/$slug.status.md" launch="$STATE_DIR/$slug.launch.sh"
  # Declared before first use: render_brief takes the status path, and reading it
  # one line earlier was an unbound-variable crash under `set -u` that broke every spawn.
  local brief="$STATE_DIR/$slug.brief.md"
  # No fallback scrape of the issue body: it matched every two-letter uppercase
  # token, so licence text became "regions" (an agent was told to fetch curves for
  # "CC BY-SA US-CO PR CC BY NC"). The brief already tells the agent to read the
  # suggested-regions section itself when this is empty, which is honest.

  # In a subshell: render_brief calls die on a leftover placeholder, and die exits
  # the shell. Called directly that bypassed this guard entirely and leaked the
  # worktree -- the `|| spawn_rollback` could never run.
  ( render_brief "$issue" "$slug" "$sci" "$regions" "$wpath" "$branch" "$brief" \
      "$kind" "$brief_tpl" "$status" ) \
    || { say "could not render the brief for $slug"; spawn_rollback; return 1; }

  printf '# %s\nissue: %s\nscientific: %s\nbranch: %s\nworktree: %s\nmodel: %s\nregions: %s\nstarted: %s\n\n' \
    "$slug" "$issue" "$sci" "$branch" "$wpath" "$model" "$regions" "$(date -u +%FT%TZ)" > "$status" \
    || { say "could not write the status file for $slug"; spawn_rollback; return 1; }
  # kind is persisted because teardown and status look the PR up by directory, and
# a locale's PR touches locales/ while a species record touches species/. Without
# it a finished locale agent reads as "no PR", its worktree is destroyed and its
# issue is retried from scratch.
# Build and verify the launcher BEFORE publishing the agent. Writing .meta first
# meant a launcher that could not be created -- `$launch` already a directory,
# say -- still left a .meta behind and logged "spawned" with no process behind it.
# errexit does not catch that: cmd_spawn runs inside `if ! spawn_err=$( ... )`,
# and bash suspends `set -e` in a condition context. The phantom was reaped on
# the next poll, which died tailing a log that was never created.
  launch_tmp="$launch.building"
  cat > "$launch_tmp" <<LAUNCHER
#!/usr/bin/env bash
# Drop the supervisor's lock fd before doing anything else. bash does not set
# close-on-exec on it, so every agent inherited the open file description and
# the flock stayed held for the lifetime of the fleet: a second supervisor could
# never start, because the agents were holding the lock meant to exclude one.
exec 9>&-
exec > "$log" 2>&1
# Fail closed. If the pidfile cannot be published the supervisor cannot see or
# stop this agent, so it must not run at all: continuing left a live process in a
# worktree the parent then force-removed, the one failure that loses work outright.
echo \$\$ > "$STATE_DIR/$slug.pid" || {
  echo "=== fleet.sh spawn FAILED: could not publish $slug.pid" >&2
  exit 8
  }
[ -s "$STATE_DIR/$slug.pid" ] || {
  echo "=== fleet.sh spawn FAILED: $slug.pid is empty" >&2
  exit 8
  }
echo "=== fleet.sh spawn \$(date -u +%FT%TZ) model=$model variant=$variant"
cd "$wpath" || exit 9
[ -f "$PERMISSIONS" ] && export OPENCODE_CONFIG="$PERMISSIONS"
"$AGENT_BIN" run --model "$model" --variant "$variant" --dir "$wpath" \
  --title "$kind $sci #$issue" --auto "\$(cat "$brief")"
rc=\$?
echo "=== agent exited rc=\$rc \$(date -u +%FT%TZ)"
LAUNCHER
  # Each step checked by hand. Nothing is watching over this window: the EXIT trap
  # that used to is gone, because it expanded $slug and $wpath at shell exit --
  # long after this function's locals were gone -- and printed
  # `slug: unbound variable` while leaking the very worktree it was meant to undo.
  # Every fallible step from here to the commit point therefore rolls back
  # explicitly.
  if [ ! -s "$launch_tmp" ]; then
    say "could not write the launcher for $slug"
    rm -f "$launch_tmp"
    spawn_rollback
    return 1
  fi
  if ! chmod +x "$launch_tmp" 2>/dev/null; then
    say "could not make the launcher executable for $slug"
    rm -f "$launch_tmp"
    spawn_rollback
    return 1
  fi
  # -T is load-bearing. Plain `mv -f src dst` where dst is an existing directory
  # moves src *into* it and still exits 0, so a launcher path that was really a
  # directory installed successfully and the spawn logged "spawned" with no agent
  # behind it. -T treats dst as a file and fails instead.
  if ! mv -fT "$launch_tmp" "$launch" 2>/dev/null; then
    say "could not install the launcher for $slug"
    rm -f "$launch_tmp"
    spawn_rollback
    return 1
  fi
  # -f as well as -x: a directory is "executable" because it is searchable, so an
  # -x-only check passed a launcher path that was really a directory.
  if [ ! -f "$launch" ] || [ ! -x "$launch" ]; then
    say "the launcher for $slug is not an executable file"
    rm -f "$launch"
    spawn_rollback
    return 1
  fi

# Publish the agent BEFORE launching it. The asymmetry matters: a .meta with no
# live process is recoverable -- agent_running reports it dead and the reap loop
# tears it down next poll -- whereas a running process with no .meta is invisible
# to everything, unable to be counted, found, or stopped. That is how agents ended
# up stranded in deleted worktrees. Ownership first, then the process.
printf 'workspace=none\nagent=%s\nworktree=%s\nbranch=%s\nissue=%s\nslug=%s\nkind=%s\nscientific=%s\nmodel=%s\nvariant=%s\nregions=%s\nlog=%s\nstatus=%s\nbrief=%s\nmain=%s\n' \
  "$slug" "$wpath" "$branch" "$issue" "$slug" "$kind" "$sci" "$model" "$variant" "$regions" "$log" "$status" "$brief" "$REPO" \
  > "$STATE_DIR/$slug.meta" \
  || { say "could not publish metadata for $slug"
       spawn_rollback
       rm -rf "$STATE_DIR/$slug.meta"
       return 1; }

# Detached, so one fleet member's exit cannot take the supervisor down with it.
# 9>&- closes the lock for this spawn too: the launcher closes it as its first
# act, but setsid holds it in between.
# A pidfile left by a previous agent with this slug would satisfy spawn_started and
# make a launch that never happened look successful. rm -rf, not rm -f: a directory
# at this path is corrupt state in a directory the harness owns, and `rm -f` fails
# on a directory -- which aborted the spawn here, before the rollback, leaking the
# worktree this whole mechanism exists to clean up.
rm -rf "$STATE_DIR/$slug.pid"
setsid nohup "$launch" 9>&- </dev/null >/dev/null 2>&1 &
disown 2>/dev/null || true

# The launcher publishes its own pidfile as its first act, so its absence means
# the launch never took. Undo the metadata and the worktree rather than leave a
# meta describing an agent that does not exist.
if ! spawn_started "$slug"; then
  say "the agent for $slug never started; rolling the spawn back"
  # The .meta must not be able to veto its own removal. `rm -f` fails on an
  # unwritable state dir, and spawn_rollback then saw the file and returned
  # without removing the worktree -- leaking exactly what this path exists to
  # clean up. Roll back with force, then best-effort remove the metadata.
  spawn_rollback 1
  rm -f "$STATE_DIR/$slug.meta" 2>/dev/null
  return 1
fi

  # Step the provider cursor once per committed spawn, so the next one is served
  # by the other provider. Removing this while reordering the spawn left the
  # cursor frozen: one model would be used forever and the rotation the task
  # actually asks for would stop happening.
  advance_model

  say "spawned $slug (issue $issue, model $model)"
  # After the log line: the tally is meant to be auditable against supervisor.log,
  # and counting first left it permanently one ahead of what the log showed.
  note_spawn_provider "$model"
}

cmd_status() {
  if [ $# -ge 1 ]; then
    row "$1"; return
  fi
  shopt -s nullglob
  local metas=("$STATE_DIR"/*.meta)
  [ ${#metas[@]} -gt 0 ] || { say "no agents; looked in $STATE_DIR"; return; }
  for m in "${metas[@]}"; do row "$(basename "$m" .meta)"; done
}

row() {
  local slug="$1" model br run age last pr ci kind
  [ -f "$STATE_DIR/$slug.meta" ] || { printf '%-26s %-40s %s\n' "$slug" "-" "no meta"; return; }
  model=$(meta_get "$slug" model); br=$(meta_get "$slug" branch)
  # Pre-kind metadata has no kind= line; those agents were all species.
  kind=$(meta_get "$slug" kind); [ -n "$kind" ] || kind=species
  if agent_running "$slug"; then run=running; else run=stopped; fi
  age=$(( ( $(date -u +%s) - $(date -u -d "$(sed -n 's/^started: //p' "$STATE_DIR/$slug.status.md" | head -1)" +%s 2>/dev/null || date -u +%s) ) / 60 ))
  # Quoted like the reap loop's: a bare #... is not a jq string, so gh fails and
  # the label comes back GHERR even when the PR exists.
  pr=$(pr_field "$slug" number,state '"#\(.number) \(.state)"')
  ci=$(pr_field "$slug" statusCheckRollup '[.statusCheckRollup[]?.conclusion] | if length==0 then "none" else (join(" ")) end')
  last=$(tail -2 "$STATE_DIR/$slug.log" 2>/dev/null | tr -d '\r' | grep -v '^$' | tail -1 | cut -c1-70)
  printf '%-26s %-7s %-40s %-8s %-6s %-3s %-8s %s\n' "$slug" "$kind" "$model" "$run" "${age}m" "$pr" "$ci" "$last"
}

cmd_teardown() {
  need_repo
  local slug force=0 pr_st
  [ $# -ge 1 ] || die "need a slug"
  slug="$1"; shift || true
  while [ $# -gt 0 ]; do case "$1" in --force) force=1; shift;; *) shift;; esac; done
  [ -f "$STATE_DIR/$slug.meta" ] || die "no metadata for $slug in $STATE_DIR"
  local wt br kind
    wt=$(meta_get "$slug" worktree); br=$(meta_get "$slug" branch)
    # Pre-kind metadata has no kind= line; those agents were all species.
    kind=$(meta_get "$slug" kind); [ -n "$kind" ] || kind=species

  # Never tear down while the agent is mid-flight, unless forced.
  if [ "$force" = 0 ] && agent_running "$slug"; then
    say "$slug is still running; pass --force once its PR is open"
    return 0
  fi
  if [ "$force" = 0 ] && [ -d "$wt" ] && [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
    say "$wt has uncommitted changes; refusing to tear down. Inspect it, then --force."
    return 1
  fi
  # Stop the agent before touching its tree. Teardown removed the worktree and
  # the metadata while leaving the process running, so a retired agent kept
  # working out of a deleted directory; the live fleet briefly held five
  # processes for three agents. Salvaging first would also race an agent that
  # was still writing into the very files being committed.
  # Explicit, because callers use `cmd_teardown ... || true` and errexit cannot be
  # relied on here: a failed stop means the agent is still writing into the tree
  # this is about to commit-and-destroy.
  if ! stop_agent "$slug"; then
    say "refusing to tear down $slug; its agent could not be stopped"
    return 1
  fi
  # Salvage before destroying. Teardown promises the branch is kept "for salvage",
  # but worktree remove --force deletes uncommitted files outright, so a locale
  # agent that got part-way through a dozen species lost all of it. Commit it onto
  # the branch first: that is what makes the promise true, and it gives the next
  # attempt something to continue from instead of restarting at zero.
  local salvage_failed=0
  if [ -d "$wt" ] && [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
    if ( cd "$wt" && git add -A && git -c user.email=fleet@localhost \
           -c user.name=fleet commit -q \
           -m "fleet: salvage work from an agent that stopped without opening a PR" ) 2>/dev/null; then
      say "salvaged uncommitted work from $slug onto $br"
    else
      # Keeping the directory is the point: those files are the only copy, and a
      # human can still lift them out. Removing it here is the exact data loss
      # this whole path exists to prevent.
      salvage_failed=1
      say "could not salvage $slug; keeping $wt so the files can be recovered"
    fi
  fi
  if [ "$salvage_failed" = 1 ]; then
    say "left $wt in place; remove it by hand once the work is recovered"
  else
    [ -d "$wt" ] && git -C "$REPO" worktree remove --force "$wt"
  fi
  git -C "$REPO" worktree prune
  rm -f "$STATE_DIR/$slug.meta" "$STATE_DIR/$slug.status.md" \
        "$STATE_DIR/$slug.brief.md" "$STATE_DIR/$slug.launch.sh" "$STATE_DIR/$slug.pid"
  # Say which of the two happened. "because it is the PR" on its own let an
  # agent that died with no PR look delivered, so its issue went unclaimed.
  pr_st=0; pr_for_slug "$slug" "$kind" || pr_st=$?
  case "$pr_st" in
    2) say "torn down $slug; could NOT verify whether a PR exists (GitHub unreachable), so claiming neither way"
       say "  branch $br and log kept: $STATE_DIR/$slug.log" ;;
    0) # Archived, not deleted. A slug that fails twice and succeeds on the third
       # attempt was deleting the log of the failure on that successful teardown,
       # so the evidence of why it failed was gone by the time anyone looked. The
       # no-PR path already kept its log "for diagnosis"; this is the same
       # reasoning applied to the case that actually destroys it.
       if [ -f "$STATE_DIR/$slug.log" ]; then
         mv "$STATE_DIR/$slug.log" "$STATE_DIR/archive/$slug.log" 2>/dev/null \
           || rm -f "$STATE_DIR/$slug.log"
       fi
       say "torn down $slug; branch kept ($br) because it is the PR" ;;
    *) say "torn down $slug; NO PR was opened, branch $br kept for salvage, issue still needs work"
       say "  agent log kept for diagnosis: $STATE_DIR/$slug.log" ;;
  esac
}

# 0 when the pid is a live fleet supervisor. The stale-lock break below must not
# fire on a recycled pid, or it would break the lock out from under a running
# supervisor, so argv has to contain fleet.sh and supervise as discrete words.
supervisor_alive() {  # pid -> 0/1
  local pid="$1" arg saw_script=0 saw_supervise=0
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  [ -r "/proc/$pid/cmdline" ] || return 1
  while IFS= read -r -d '' arg; do
    case "$arg" in
      */fleet.sh) saw_script=1 ;;
      supervise)  saw_supervise=1 ;;
    esac
  done < "/proc/$pid/cmdline"
  [ "$saw_script" = 1 ] && [ "$saw_supervise" = 1 ] || return 1
  # Shape is not ownership. A process whose argv merely looks like a supervisor
  # must not be able to block recovery of a dead lock, and a supervisor of a
  # DIFFERENT state dir must not have its lock broken by this one. Require that
  # the pid actually holds a descriptor on THIS state directory's lock; only the
  # supervisor that took it can.
  local fd target
  target="$STATE_DIR/supervisor.lock"
  for fd in /proc/"$pid"/fd/*; do
    [ -e "$fd" ] || continue
    [ "$(readlink "$fd" 2>/dev/null || true)" = "$target" ] && return 0
  done
  return 1
}

cmd_supervise() {
  local once=0 holder waited reclaim_owner
  while [ $# -gt 0 ]; do
    case "$1" in --once) once=1; shift;; --min) FLEET_MIN=$2; shift 2;; --max) FLEET_MAX=$2; shift 2;; *) shift;; esac
  done
  [ "$FLEET_MAX" -ge "$FLEET_MIN" ] || die "--max must be >= --min"
  # One supervisor per state directory. Two would race each other through the
  # orphan scan and the STATUS.md sweep, each undoing the other's work on
  # worktrees it does not own. flock is released automatically when this exits.
  #
  # The flock alone is not enough. bash does not set close-on-exec on fd 9, so
  # every child inherits the lock's open file description and keeps holding it
  # after this process dies -- the poll sleep, a `gh` call blocked on the
  # network, anything. I hit exactly that: zero supervisors running, one lock
  # holder with ppid 1, and a replacement refused. Closing fd 9 at each spawn
  # site cannot be complete: there are dozens of gh and git call sites and one
  # omission reintroduces the whole failure. So the lock records its owner, and
  # a lock whose owner is gone is treated as stale. That closes the class rather
  # than the instances.
  exec 9>"$STATE_DIR/supervisor.lock" \
    || die "cannot open lock file in $STATE_DIR"
  if ! flock -n 9; then
    # Serialise the reclaim. Unlinking and recreating the lock is atomic per
    # process but not between them: two contenders can both see a dead owner,
    # both unlink, and end up holding locks on two different inodes -- both
    # convinced they are exclusive. Oracle measured 42 of 80 concurrent trials
    # admitting two supervisors. mkdir is the mutex: atomic, and it leaves no
    # descriptor for a child to inherit.
    local waited=0
    until mkdir "$STATE_DIR/supervisor.reclaim" 2>/dev/null; do
      waited=$((waited + 1))
      # A contender killed between this mkdir and its rm -rf leaves the directory
      # behind. A dead owner is therefore detected on the FIRST iteration rather
      # than after the full wait, which had made every restart burn 30s before
      # recovering; a live owner still gets the whole grace period.
      reclaim_owner=$(tr -dc '0-9' < "$STATE_DIR/supervisor.reclaim/owner" 2>/dev/null)
      if [ -n "$reclaim_owner" ] && ! kill -0 "$reclaim_owner" 2>/dev/null; then
        say "clearing a reclaim mutex orphaned by dead pid $reclaim_owner"
        rm -rf "$STATE_DIR/supervisor.reclaim"
        waited=0
        continue
      fi
      if [ "$waited" -gt 30 ]; then
        die "another supervisor is reclaiming $STATE_DIR/supervisor.lock"
      fi
      sleep 1 9>&-
    done
    printf '%s\n' "$$" > "$STATE_DIR/supervisor.reclaim/owner" 2>/dev/null || true
    # Re-test under the mutex: the contender that won the race may already hold
    # the lock, in which case this one must stand down rather than break it.
    if ! flock -n 9; then
      holder=$(tr -dc '0-9' < "$STATE_DIR/supervisor.owner" 2>/dev/null)
      if [ -n "$holder" ] && ! supervisor_alive "$holder"; then
        say "breaking a supervisor lock orphaned by dead pid $holder"
        rm -f "$STATE_DIR/supervisor.lock"
        exec 9>"$STATE_DIR/supervisor.lock" \
          || die "cannot reopen lock file in $STATE_DIR"
        flock -n 9 || die "another supervisor already holds $STATE_DIR/supervisor.lock"
      else
        rm -rf "$STATE_DIR/supervisor.reclaim" 2>/dev/null
        die "another supervisor already holds $STATE_DIR/supervisor.lock"
      fi
    fi
    rm -rf "$STATE_DIR/supervisor.reclaim" 2>/dev/null
  fi
  # Named .owner, deliberately NOT .pid. The orphan sweep below globs *.pid and
  # treats any pidfile without a matching .meta as a dead agent to reap; a
  # supervisor.pid matched it, and the supervisor promptly called stop_agent on
  # itself and signalled its own process group. Nothing stops a name from being
  # reused carelessly, so the sweep also refuses to act on this file.
  # Guarded, and fatal by design: the stale-lock reclaim reads this to decide
  # whether a lock holder is alive, so without it a crashed supervisor's lock can
  # never be broken. Die with a named reason rather than a raw redirection error.
  printf '%s\n' "$$" | write_state "$STATE_DIR/supervisor.owner" \
    || die "cannot record the lock owner in $STATE_DIR/supervisor.owner (state dir full or read-only?)"
  # Only now, having proved exclusivity. Reconciling first meant a second
  # supervisor rewrote the tally on its way to being refused, which is a write
  # by a process that had not yet established it was allowed to write.
  reconcile_provider_counts
  # Outside the loop on purpose: reset per pass and the transition-only
  # reporting below can never fire.
  local fleet_state=OK prev_state=OK warned_foreign="" foreign_now=""

  while :; do
    # fleet_state is recomputed each pass; prev_state alone carries history.
    # Resetting it here is what lets a recovered fleet report OK again.
    fleet_state=OK
    # Rebuilt from scratch every pass. Declared outside the loop and appended to
    # without ever being cleared, one sighting pinned the fleet to BLOCKED for the
    # lifetime of the process: removing the worktree did not unblock it.
    foreign_now=""
    # Reclaim orphans first. A worktree with no .meta belongs to no agent: the
    # fleet cannot count it, cannot reap it, and every retry of its slug dies on
    # "worktree path already exists". Two of those blocked all remaining species
    # work and spun the loop. Anything here is work no live agent is using, so
    # only remove it when the directory is clean or its branch is already pushed.
    for w in "$WORKTREE_ROOT"/*/; do
      [ -d "$w" ] || continue
      wbase=$(basename "$w")
      case "$wbase" in species-*|locale-*) ;; *) continue ;; esac
      oslug=${wbase#species-}; oslug=${oslug#locale-}
      [ -f "$STATE_DIR/$oslug.meta" ] && continue
      # Never reclaim a worktree an agent is still running in. "No meta" is not
      # sufficient evidence that a slug is unused: a supervisor that died between
      # creating the worktree and writing the meta leaves exactly that state, and
      # the sweep then pulled the tree out from under a live agent. Its cwd became
      # deleted, it could never commit, and nothing could find it again -- three
      # agents lost their work that way, while the fleet reported live=3.
      # ${w%/} because the glob leaves a trailing slash and --dir does not.
      agent_for_worktree "${w%/}" && {
        say "orphan worktree $wbase still has a live agent in it; leaving it alone"
        continue
      }
      if [ -z "$(git -C "$w" status --porcelain 2>/dev/null)" ]; then
        if git -C "$REPO" worktree remove --force "$w" 2>/dev/null; then
          echo "[$(date -u +%FT%TZ)] reclaimed orphan worktree $wbase (no meta, clean)"
        elif [ -n "$(git -C "$w" rev-parse --git-dir 2>/dev/null)" ]; then
          # Clean, and a real git worktree, but this repository cannot remove it:
          # its .git points into a different checkout, so this repo holds no
          # registration for it. It is not ours to delete, and it will wedge its
          # slug on "worktree path already exists". Name it rather than let the
          # spawn fail for a reason nobody can see.
          # Transition-only, like the STARVED report below. This condition
          # persists until a human removes the directory, so logging it every poll
          # wrote 1440 identical lines a day and buried everything else.
          # Recorded whether or not we log it. The state belongs outside the
          # latch: setting it inside meant the heartbeat said OK on every poll
          # after the first warning, while the slug was still wedged.
          foreign_now="$foreign_now $wbase"
          # Space-delimited and matched with case, so two blockers cannot re-arm
          # each other -- a single scalar compared for equality logged all six.
          case " $warned_foreign " in
            *" $wbase "*) : ;;
            *) echo "[$(date -u +%FT%TZ)] WARNING orphan worktree $wbase could not be reclaimed: it is registered to another checkout and will block its slug until removed by hand" ;;
          esac
        fi
      else
        say "orphan worktree $wbase has uncommitted work; leaving it for inspection"
      fi
    done
    git -C "$REPO" worktree prune
    # The latch is rebuilt from what this pass actually saw. A blocker that
    # persists stays quiet; one that is removed and later reappears warns again,
    # because its name is no longer in the list.
    [ "$foreign_now" != "$warned_foreign" ] && warned_foreign="$foreign_now"

    # Orphans. An agent process outliving its metadata is the failure that made
    # the fleet report five members while holding three: the retired one keeps
    # working, and once its slug respawns into the same path the two are
    # indistinguishable by path alone. A pidfile with no meta is unambiguous.
    for pf in "$STATE_DIR"/*.pid; do
      [ -f "$pf" ] || continue
      case "$pf" in */supervisor.pid|*/supervisor.owner) continue;; esac
      oslug=$(basename "$pf" .pid)
      [ -f "$STATE_DIR/$oslug.meta" ] && continue
      stop_agent "$oslug"
      say "reaped an orphaned process for $oslug; its metadata was gone"
    done

    # Scratch-file guard. A PR once shipped STATUS.md and two locale PRs shipped
    # report.md, in both cases because the brief told the agent to write it and a
    # blanket `git add` swept it in. Prompts have failed repeatedly to hold this
    # line -- agents launched before a brief edit keep the old brief for their
    # whole run -- so containment is mechanical: undo the change and say so.
    # A file that is already on the base branch is not pollution, so only paths
    # the agent actually modified are touched.
    for m in "$STATE_DIR"/*.meta; do
      [ -f "$m" ] || continue
      gslug=$(basename "$m" .meta)
      gwt=$(meta_get "$gslug" worktree)
      [ -n "$gwt" ] && [ -d "$gwt" ] || continue
      for scratch in STATUS.md report.md; do
        # Presence on disk *or* in the index. `git diff HEAD` cannot see an
        # untracked file at all, so a scratch file not yet staged walked straight
        # past the guard and was then swept into the commit by the next
        # `git add -A` -- the exact failure the guard exists to prevent. The
        # index check also catches a staged deletion of a base-branch file.
        if [ ! -e "$gwt/$scratch" ] \
           && ! git -C "$gwt" ls-files --error-unmatch "$scratch" >/dev/null 2>&1; then
          continue
        fi
        # `checkout -- <path>` restores the worktree *from the index*, so a
        # staged edit survived it and still shipped while the guard logged a
        # successful revert. Clear index and worktree from HEAD, then confirm:
        # a guard that reports success without cleaning is worse than none.
        # Two different shapes need two different fixes. STATUS.md exists on the
        # base branch, so it has to be restored to its committed contents. A
        # report.md the agent created is not in HEAD at all, so restoring it
        # would fail and the staged copy would ship; it has to be unstaged and
        # deleted instead. Treating them alike warned instead of cleaning.
        if git -C "$gwt" cat-file -e "HEAD:$scratch" 2>/dev/null; then
          if git -C "$gwt" restore --staged --worktree --source=HEAD -- "$scratch" 2>/dev/null \
             && git -C "$gwt" diff --quiet HEAD -- "$scratch" 2>/dev/null; then
            echo "[$(date -u +%FT%TZ)] $gslug: reverted a $scratch edit; scratch files are not part of the contribution"
          else
            echo "[$(date -u +%FT%TZ)] $gslug: WARNING could not revert a staged $scratch edit; check it before merging"
          fi
        else
          # Not in HEAD: unstage it if it was staged, then remove the file.
          git -C "$gwt" rm -q --cached --ignore-unmatch -- "$scratch" 2>/dev/null || true
          rm -f "$gwt/$scratch" 2>/dev/null || true
          if git -C "$gwt" status --porcelain -- "$scratch" 2>/dev/null | grep -q .; then
            echo "[$(date -u +%FT%TZ)] $gslug: WARNING $scratch still present; check it before merging"
          else
            echo "[$(date -u +%FT%TZ)] $gslug: removed the agent-created scratch file $scratch"
          fi
        fi
      done
    done

    # Reap: an agent that finished with a PR leaves the fleet.
    shopt -s nullglob
    for m in "$STATE_DIR"/*.meta; do
      slug=$(basename "$m" .meta)
      agent_running "$slug" && continue
      pr=$(pr_field "$slug" number,state '"#\(.number) \(.state)"')
      case "$pr" in
        \#*) echo "[$(date -u +%FT%TZ)] $slug finished: $pr -> teardown"
             cmd_teardown "$slug" --force || true ;;
        # GitHub could not be reached. Leave the agent and its worktree alone and
        # ask again next poll: reaping here would destroy finished work on a
        # transient outage and burn a retry.
        GHERR) fleet_state=GH_UNREACHABLE
               echo "[$(date -u +%FT%TZ)] $slug: PR lookup failed (GitHub unreachable); leaving it for the next poll" ;;
        *)     # if-guard, not a bare call: note_route_failure returns 1 for a
               # normal no-PR exit, and that must not trip errexit.
               if note_route_failure "$slug"; then
                 refund_attempt "$(meta_get "$slug" kind)" "$slug"
               fi
               echo "[$(date -u +%FT%TZ)] $slug stopped with NO PR (model $(meta_get "$slug" model)); log tail:"
               # Guarded: a phantom or salvaged agent can have a .meta with no log, and an
              # unguarded tail made the supervisor exit on the reap -- which is
              # how a false spawn killed the following poll.
              tail -5 "$STATE_DIR/$slug.log" 2>/dev/null | sed 's/^/    /' \
                || echo "    (no agent log)"
               cmd_teardown "$slug" --force || true ;;
      esac
    done

    # Refill to the floor, never past --max, and never past the floor either: the
    # loop below grows to FLEET_MIN only. See the note on FLEET_MAX for why the
    # ceiling is not a target.
    # A slug is skipped only once it has
    # burned FLEET_MAX_ATTEMPTS tries, so a flaky model route or a dropped
    # connection does not retire an issue for the life of the queue, while a
    # genuinely broken issue still stops being retried.
    local live pick row_pick n sl ti sc spawn_err zen_n go_n
    # Count via array glob, not `ls "$STATE_DIR"/*.meta`. nullglob is set above,
    # so an unmatched glob expands to zero words and bare `ls` would list the
    # current directory instead, reporting the repo root's entry count as the
    # fleet size and silently skipping every refill.
    local metas=("$STATE_DIR"/*.meta)
    live=${#metas[@]}
    if [ "$live" -lt "$FLEET_MIN" ]; then
      # A gh outage must not kill the loop, but it must not masquerade as an
      # empty queue either: report it and keep whatever is already running.
      if ! pick=$(cmd_list_issues); then
        fleet_state=GH_UNREACHABLE
        echo "[$(date -u +%FT%TZ)] issue listing failed (GitHub unreachable); not refilling this poll"
        pick=""
      fi
      # Key on FILENAME, not NR==FNR. queue.tsv is empty on a first run, and with
      # an empty first file NR and FNR advance in lockstep, so NR==FNR stays true
      # for every candidate row and the whole queue is swallowed as "already tried".
      # A slug with a live agent is always skipped, whatever its attempt count:
      # the retry budget would otherwise offer a running agent its own slug.
      local busy
      # Liveness is keyed on the bare slug because the state layer is: .meta,
      # .log, .status.md and .launch.sh are all $slug.*, so two agents sharing a
      # slug would overwrite each other's files. Attempts stay keyed by kind/slug
      # because a species and a locale with the same name are separate issues.
      busy=$(for m in "${metas[@]}"; do basename "$m" .meta; done | paste -sd' ' -)
      if [ -f "$STATE_DIR/queue.tsv" ]; then
        pick=$(printf '%s\n' "$pick" | awk -F'\t' -v q="$STATE_DIR/queue.tsv" \
          -v max="$FLEET_MAX_ATTEMPTS" -v maxloc="$FLEET_MAX_ATTEMPTS_LOCALE" \
          -v cut="$(( $(date +%s) - FLEET_ATTEMPT_COOLDOWN_SECONDS ))" -v busy="$busy" '
          BEGIN { k = split(busy, b, " "); for (i = 1; i <= k; i++) if (b[i] != "") live[b[i]] = 1 }
          # Only attempts inside the cooldown window count. An unstamped row predates
          # the schema and always counted, so it still counts: "N rows = N attempts
          # spent" is the invariant the filter has always had, and silently expiring
          # unstamped rows would retire issues nobody retried. Every row written from
          # now on is stamped, so the ledger drains on its own from here.
          FILENAME == q { if ($3 != "" && ($4 == "" || ($4 + 0) > cut)) n[$2 "/" $3]++; next }
          { if ($2 == "" || $3 == "") next; key = $3 "/" $2; if ($2 in live) next;
            lim = ($3 == "locale") ? maxloc : max;
            if ((key in n) && n[key] >= lim) next; print }
        ' "$STATE_DIR/queue.tsv" -)
      fi
      # Candidates are a queue we shrink, not a list we re-scan. The old advance
      # was `awk 'NR>1 && $2 != s'`, which skips only row 1, so for candidates
      # a b c d the walk went a -> b -> c -> b and the budget ran out before ever
      # reaching d: a single stubborn early issue starved every later one.
      # Keyed by kind/slug, matching how attempts and busy agents are counted.
      pick=$(printf '%s\n' "$pick" | awk -F'\t' '!seen[$3 "/" $2]++')
      local remaining budget
      remaining="$pick"
      # Report starvation once, on the transition. Repeating it every poll turns a
      # one-line state change into log spam that hides real events.
      # Two very different situations both used to report STARVED, and an operator
      # could not tell them apart: the repo having no work at all, versus every open
      # issue already being carried by an open PR. The second is not a malfunction
      # and the fix is human review, so it gets its own state and says so.
      if [ -z "$remaining" ] && [ "$fleet_state" != GH_UNREACHABLE ]; then
        if [ -n "$pick" ]; then
          fleet_state=AWAITING_REVIEW
          if [ "$prev_state" != AWAITING_REVIEW ]; then
            echo "[$(date -u +%FT%TZ)] AWAITING_REVIEW: live=$live below floor $FLEET_MIN, but every open issue is already carried by an open PR or has spent its retry budget; the queue refills when those PRs land"
          fi
        else
          fleet_state=STARVED
          if [ "$prev_state" != STARVED ]; then
            echo "[$(date -u +%FT%TZ)] STARVED: live=$live below floor $FLEET_MIN, no eligible issue left"
          fi
        fi
      fi
      budget=$(printf '%s\n' "$remaining" | grep -c . || true)
      while [ -n "$remaining" ] && [ "$live" -lt "$FLEET_MIN" ] && [ "$budget" -gt 0 ]; do
        budget=$(( budget - 1 ))
        row_pick=$(printf '%s\n' "$remaining" | head -1)
        IFS=$'\t' read -r n sl kind ti <<<"$row_pick"
        # Drop the candidate before the attempt, so neither a refusal nor a
        # success can hand the same row back on the next turn.
        remaining=$(printf '%s\n' "$remaining" \
                    | awk -F'\t' -v k="$kind/$sl" '$3 "/" $2 != k')
        if [ "$kind" = locale ]; then
          sc="$sl"
        else
          sc=$(gh issue view "$n" --repo "$GH_REPO" --json title 2>/dev/null \
               | python3 -c 'import json,sys;t=json.load(sys.stdin)["title"];print(t[t.rindex("(")+1:-1].strip() if "(" in t else "")' 2>/dev/null || true)
          [ -n "$sc" ] || sc="$ti"
        fi
        # A refused spawn must not leave the fleet reporting OK below its floor,
        # and must not block every later candidate behind one bad issue. An
        # unreachable GitHub is the exception: nothing after it will spawn either,
        # so stop the pass rather than walk the whole queue.
        if ! spawn_err=$( ( cmd_spawn --issue "$n" --slug "$sl" \
                                   --scientific "$sc" --kind "$kind" ) 2>&1 ); then
          fleet_state=REFILL_FAILED
          echo "[$(date -u +%FT%TZ)] spawn refused for $sl (issue $n): $spawn_err"
          case "$spawn_err" in
            *nreachable*|*"cannot verify"*)
              fleet_state=GH_UNREACHABLE
              break ;;
          esac
          continue
        fi
        [ -n "$spawn_err" ] && printf '%s\n' "$spawn_err"
        live=$(( live + 1 ))
      done
    fi
    # Invariant, applied last: never report OK while below the floor, whatever
    # path got us here. This is the check a future edit cannot quietly bypass.
    if [ "$live" -lt "$FLEET_MIN" ] && [ "$fleet_state" = OK ]; then
      fleet_state=BELOW_FLOOR
    fi
    # And never report OK while a known blocker is still wedging a slug. Only
    # upgrades an otherwise-OK state, so a more urgent one still wins.
    if [ -n "$foreign_now" ] && [ "$fleet_state" = OK ]; then
      fleet_state=BLOCKED_BY_FOREIGN_WORKTREE
    fi
    zen_n=$(awk '$1=="zen" {print $2}' "$STATE_DIR/provider_counts" 2>/dev/null | tail -1) || true
    go_n=$(awk '$1=="go" {print $2}' "$STATE_DIR/provider_counts" 2>/dev/null | tail -1) || true
    # If even this cannot be written the fleet cannot be observed at all, so
    # report it on stderr too: stdout is the supervisor log, but a stale
    # heartbeat is the thing an operator will be watching.
    if ! printf 'live=%s floor=%s max=%s state=%s zen=%s go=%s at=%s\n' \
         "$live" "$FLEET_MIN" "$FLEET_MAX" "$fleet_state" "${zen_n:-0}" "${go_n:-0}" \
         "$(date -u +%FT%TZ)" | write_state "$STATE_DIR/heartbeat"; then
      fleet_state=STATE_WRITE_FAILED
      echo "[$(date -u +%FT%TZ)] STATE_WRITE_FAILED: heartbeat not written; the fleet is still running but cannot be observed" >&2
      prev_state=$fleet_state
      echo "[$(date -u +%FT%TZ)] fleet=$live (min $FLEET_MIN max $FLEET_MAX) state=$fleet_state next-model=$(next_model)"
      [ "$once" = 1 ] && return 0
      sleep "$POLL_SECONDS" 9>&-
      continue
    fi
    prev_state=$fleet_state

    echo "[$(date -u +%FT%TZ)] fleet=$live (min $FLEET_MIN max $FLEET_MAX) state=$fleet_state next-model=$(next_model)"
    [ "$once" = 1 ] && return 0
    sleep "$POLL_SECONDS" 9>&-
  done
}

cmd_render_brief() {
  local issue slug sci regions out kind
  issue=""; slug=""; sci=""; regions=""; out=""; kind="species"
  while [ $# -gt 0 ]; do
    case "$1" in
      --issue) issue=$2; shift 2;;
      --slug) slug=$2; shift 2;;
      --scientific) sci=$2; shift 2;;
      --kind) kind=$2; shift 2;;
      --regions) regions=$2; shift 2;;
      --out) out=$2; shift 2;;
      *) die "unknown argument: $1";;
    esac
  done
  [ -n "$issue" ] && [ -n "$slug" ] || die "need --issue --slug"
  [ "$kind" = species ] && { [ -n "$sci" ] || die "need --scientific for a species"; }
  [ -n "$out" ] || out="/dev/stdout"
  render_brief "$issue" "$slug" "$sci" "$regions" \
    "$WORKTREE_ROOT/$slug" "$BRANCH_PREFIX/$kind-$issue-$slug" "$out" "$kind" "" \
      "$STATE_DIR/$slug.status.md"
  [ "$out" = "/dev/stdout" ] || say "wrote $out"
}

case "${1:-}" in
  list-issues) shift; cmd_list_issues "$@";;
  probe-models) shift; cmd_probe_models "$@";;
  render-brief) shift; cmd_render_brief "$@";;
  spawn)       shift; cmd_spawn "$@";;
  status)      shift; cmd_status "$@";;
  teardown)    shift; cmd_teardown "$@";;
  supervise)   shift; cmd_supervise "$@";;
  ""|-h|--help|help) sed -n '2,20p' "$0";;
  *) die "unknown command: $1";;
esac
