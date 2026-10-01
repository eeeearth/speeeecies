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
FLEET_MAX=${FLEET_MAX:-5}
POLL_SECONDS=${POLL_SECONDS:-60}
FLEET_MAX_ATTEMPTS=${FLEET_MAX_ATTEMPTS:-3}
# A locale is one manifest plus 8-12 species records and a flora catalog, so
# it exhausts an agent's budget far more often than a single species does.
# Retiring a locale after three tries was throwing away unfinished work that a
# fourth would have finished; four locales have now burned all three.
FLEET_MAX_ATTEMPTS_LOCALE=${FLEET_MAX_ATTEMPTS_LOCALE:-5}
BRANCH_PREFIX=${BRANCH_PREFIX:-$(gh api user -q .login 2>/dev/null || echo contributor)}
BRIEF_SPECIES=${BRIEF_SPECIES:-$SCRIPT_DIR/brief-species.md}
BRIEF_LOCALE=${BRIEF_LOCALE:-$SCRIPT_DIR/brief-locale.md}
BRIEF_TEMPLATE=${BRIEF_TEMPLATE:-}
PERMISSIONS=${PERMISSIONS:-$SCRIPT_DIR/agent-permissions.json}
RECIPES=${RECIPES:-$SCRIPT_DIR/recipes.md}
VISUAL_CHECK=${VISUAL_CHECK:-0}


mkdir -p "$WORKTREE_ROOT" "$STATE_DIR"

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
MODEL_POOL_ZEN=(
  "opencode/nemotron-3-ultra-free"            # largest free model
  "opencode/space-bunny-free"                 # same model as the go route
  "opencode/nemotron-3.5-lightning-free"      # fast
  "opencode/longcat-2.5-preview-free"
  "opencode/mimo-v2.6-flash-free"
  "opencode/muse-spark-1.3-contributor-free"  # contributor tier
)
MODEL_POOL_GO=(
  "opencode-go/space-bunny-free"
  "opencode-go/longcat-2.5-preview-free"
)
MODEL_POOL=( "${MODEL_POOL_ZEN[@]}" "${MODEL_POOL_GO[@]}" )
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

meta_get() { sed -n "s/^$2=//p" "$STATE_DIR/$1.meta" 2>/dev/null | head -1; }

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
  case "$p" in zen) other=go;; *) other=zen;; esac
  printf '%s\n' "$other" > "$STATE_DIR/provider_cursor"
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
  # No pidfile does not mean nothing is running. Agents launched before the
  # pidfile existed have none, and returning early is how teardown came to
  # mean "remove the metadata" while the process carried on in a deleted
  # directory. Fall back to matching the worktree, so an agent of unknown
  # vintage still gets stopped.
  # No pidfile does not mean nothing is running: agents launched before the
  # pidfile existed have none, and returning early is how teardown came to mean
  # "remove the metadata" while the process carried on in a deleted directory.
  # Matching is exact --dir argv equality for the reason given above pid_arg_dir.
  if [ ! -f "$pf" ]; then
    wt=$(meta_get "$1" worktree)
    for pid in $(pgrep -f -- "$AGENT_BIN run" 2>/dev/null); do
      [ "$(pid_arg_dir "$pid")" = "$wt" ] || continue
      say "  no pidfile for $1; stopping its agent on $wt (pid $pid)"
      stop_signal "$pid"
    done
    return 0
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
    stop_signal "$pid"
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
  ( cd "$REPO" && git worktree prune && git fetch --quiet origin && "${worktree_add[@]}" ) >/dev/null
  # Transaction boundary. A spawn that dies between here and the .meta write
  # leaves a worktree the supervisor cannot count, cannot reap, and retries
  # around -- it leaked three before this existed. Undo the worktree on any
  # exit until the metadata makes the spawn real.
  trap 'if [ ! -f "$STATE_DIR/$slug.meta" ] && [ -d "$wpath" ]; then git -C "$REPO" worktree remove --force "$wpath" 2>/dev/null; git -C "$REPO" worktree prune 2>/dev/null; fi' EXIT

  # Region hints come from the issue body, so the agent does not have to guess.
  local regions
  # shellcheck disable=SC2016
  regions=$(gh issue view "$issue" --repo "$GH_REPO" --json body \
            | python3 -c 'import json,re,sys
b=json.load(sys.stdin)["body"] or ""
m=re.search(r"[Ss]uggested regions.*?\n(.*?)(\n\n|\Z)", b, re.S)
print(" ".join(re.findall(r"`([A-Z]{2}(?:-[A-Z0-9]{1,3})?)`", m.group(1))) if m else "")')

  local log="$STATE_DIR/$slug.log" status="$STATE_DIR/$slug.status.md" launch="$STATE_DIR/$slug.launch.sh"
  # Declared before first use: render_brief takes the status path, and reading it
  # one line earlier was an unbound-variable crash under `set -u` that broke every spawn.
  local brief="$STATE_DIR/$slug.brief.md"
  # No fallback scrape of the issue body: it matched every two-letter uppercase
  # token, so licence text became "regions" (an agent was told to fetch curves for
  # "CC BY-SA US-CO PR CC BY NC"). The brief already tells the agent to read the
  # suggested-regions section itself when this is empty, which is honest.

  render_brief "$issue" "$slug" "$sci" "$regions" "$wpath" "$branch" "$brief" \
    "$kind" "$brief_tpl" "$status"

  printf '# %s\nissue: %s\nscientific: %s\nbranch: %s\nworktree: %s\nmodel: %s\nregions: %s\nstarted: %s\n\n' \
    "$slug" "$issue" "$sci" "$branch" "$wpath" "$model" "$regions" "$(date -u +%FT%TZ)" > "$status"
  # kind is persisted because teardown and status look the PR up by directory, and
# a locale's PR touches locales/ while a species record touches species/. Without
# it a finished locale agent reads as "no PR", its worktree is destroyed and its
# issue is retried from scratch.
printf 'workspace=none\nagent=%s\nworktree=%s\nbranch=%s\nissue=%s\nslug=%s\nkind=%s\nscientific=%s\nmodel=%s\nvariant=%s\nregions=%s\nlog=%s\nstatus=%s\nbrief=%s\nmain=%s\n' \
    "$slug" "$wpath" "$branch" "$issue" "$slug" "$kind" "$sci" "$model" "$variant" "$regions" "$log" "$status" "$brief" "$REPO" \
    > "$STATE_DIR/$slug.meta"
  # The spawn is committed: the supervisor can now see and reap this agent.
  trap - EXIT

  cat > "$launch" <<LAUNCHER
#!/usr/bin/env bash
# Drop the supervisor's lock fd before doing anything else. bash does not set
# close-on-exec on it, so every agent inherited the open file description and
# the flock stayed held for the lifetime of the fleet: a second supervisor could
# never start, because the agents were holding the lock meant to exclude one.
exec 9>&-
exec > "$log" 2>&1
echo \$\$ > "$STATE_DIR/$slug.pid"
echo "=== fleet.sh spawn \$(date -u +%FT%TZ) model=$model variant=$variant"
cd "$wpath" || exit 9
[ -f "$PERMISSIONS" ] && export OPENCODE_CONFIG="$PERMISSIONS"
"$AGENT_BIN" run --model "$model" --variant "$variant" --dir "$wpath" \
  --title "$kind $sci #$issue" --auto "\$(cat "$brief")"
rc=\$?
echo "=== agent exited rc=\$rc \$(date -u +%FT%TZ)"
LAUNCHER
  chmod +x "$launch"

  # Detached, so one fleet member's exit cannot take the supervisor down with it.
  # 9>&- closes the lock for this spawn too: the launcher closes it as its first
  # act, but setsid holds it in between.
  setsid nohup "$launch" 9>&- </dev/null >/dev/null 2>&1 &
  disown 2>/dev/null || true
  advance_model

  printf '%s\t%s\t%s\n' "$issue" "$kind" "$slug" >> "$STATE_DIR/queue.tsv"
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
  stop_agent "$slug"
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
    0) rm -f "$STATE_DIR/$slug.log"
       say "torn down $slug; branch kept ($br) because it is the PR" ;;
    *) say "torn down $slug; NO PR was opened, branch $br kept for salvage, issue still needs work"
       say "  agent log kept for diagnosis: $STATE_DIR/$slug.log" ;;
  esac
}

cmd_supervise() {
  local once=0
  while [ $# -gt 0 ]; do
    case "$1" in --once) once=1; shift;; --min) FLEET_MIN=$2; shift 2;; --max) FLEET_MAX=$2; shift 2;; *) shift;; esac
  done
  [ "$FLEET_MAX" -ge "$FLEET_MIN" ] || die "--max must be >= --min"
  # One supervisor per state directory. Two would race each other through the
  # orphan scan and the STATUS.md sweep, each undoing the other's work on
  # worktrees it does not own. flock is released automatically when this exits.
  exec 9>"$STATE_DIR/supervisor.lock" \
    || die "cannot open lock file in $STATE_DIR"
  flock -n 9 || die "another supervisor already holds $STATE_DIR/supervisor.lock"
  # Only now, having proved exclusivity. Reconciling first meant a second
  # supervisor rewrote the tally on its way to being refused, which is a write
  # by a process that had not yet established it was allowed to write.
  reconcile_provider_counts
  # Outside the loop on purpose: reset per pass and the transition-only
  # reporting below can never fire.
  local fleet_state=OK prev_state=OK

  while :; do
    # fleet_state is recomputed each pass; prev_state alone carries history.
    # Resetting it here is what lets a recovered fleet report OK again.
    fleet_state=OK
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
      if [ -z "$(git -C "$w" status --porcelain 2>/dev/null)" ]; then
        git -C "$REPO" worktree remove --force "$w" 2>/dev/null \
          && echo "[$(date -u +%FT%TZ)] reclaimed orphan worktree $wbase (no meta, clean)"
      else
        say "orphan worktree $wbase has uncommitted work; leaving it for inspection"
      fi
    done
    git -C "$REPO" worktree prune

    # Orphans. An agent process outliving its metadata is the failure that made
    # the fleet report five members while holding three: the retired one keeps
    # working, and once its slug respawns into the same path the two are
    # indistinguishable by path alone. A pidfile with no meta is unambiguous.
    for pf in "$STATE_DIR"/*.pid; do
      [ -f "$pf" ] || continue
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
               tail -5 "$STATE_DIR/$slug.log" | sed 's/^/    /'
               cmd_teardown "$slug" --force || true ;;
      esac
    done

    # Refill to the floor, never past --max. A slug is skipped only once it has
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
          -v max="$FLEET_MAX_ATTEMPTS" -v maxloc="$FLEET_MAX_ATTEMPTS_LOCALE" -v busy="$busy" '
          BEGIN { k = split(busy, b, " "); for (i = 1; i <= k; i++) if (b[i] != "") live[b[i]] = 1 }
          FILENAME == q { if ($3 != "") n[$2 "/" $3]++; next }
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
      if [ -z "$remaining" ] && [ "$fleet_state" != GH_UNREACHABLE ]; then
        if [ "$prev_state" != STARVED ]; then
          echo "[$(date -u +%FT%TZ)] STARVED: live=$live below floor $FLEET_MIN, no eligible issue left"
        fi
        fleet_state=STARVED
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
    zen_n=$(awk '$1=="zen" {print $2}' "$STATE_DIR/provider_counts" 2>/dev/null | tail -1) || true
    go_n=$(awk '$1=="go" {print $2}' "$STATE_DIR/provider_counts" 2>/dev/null | tail -1) || true
    printf 'live=%s floor=%s max=%s state=%s zen=%s go=%s at=%s\n' \
      "$live" "$FLEET_MIN" "$FLEET_MAX" "$fleet_state" "${zen_n:-0}" "${go_n:-0}" \
      "$(date -u +%FT%TZ)" > "$STATE_DIR/heartbeat"
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
