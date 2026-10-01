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

note_route_failure() {  # slug; back off the provider if the agent died on routing
  local model
  model=$(meta_get "$1" model)
  [ -n "$model" ] && [ -f "$STATE_DIR/$1.log" ] || return 0
  if grep -qiE 'cannot find any route|rate limit|429|too many requests|quota exceeded' \
       "$STATE_DIR/$1.log"; then
    provider_note_failure "$(provider_of_model "$model")"
  fi
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

agent_running() {  # slug -> 0 running, 1 not
  local wt; wt=$(meta_get "$1" worktree)
  [ -n "$wt" ] || return 1
  pgrep -af "$AGENT_BIN run" 2>/dev/null | grep -qF -- "$wt"
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
  local kind="${8:-species}" template="${9:-}"
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

pr_field() {  # slug field jq-expr
  local br jq
  br=$(meta_get "$1" branch)
  [ -n "$br" ] || { echo "-"; return; }
  # Default to the bare field rather than $3 bare: `set -u` makes a missing third
  # argument fatal, and that killed the supervisor the first time an agent
  # finished, which is exactly when the reap loop needs to run.
  jq=${3:-".$2"}
  gh pr view "$br" --repo "$GH_REPO" --json "$2" -q "$jq" 2>/dev/null || echo "-"
}

cmd_list_issues() {
  need_repo
  # Open, unassigned work: species-request+animal and locale-request. Skips
  # anything already carried by an open PR so two fleets never duplicate work.
  # Columns: issue, slug, kind, title. A locale slug is the locale id, which the
  # issue title carries in its final parentheses.
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
      pr_for_slug "$slug" "$kind" >/dev/null 2>&1 && continue
      record_exists "$slug" "$kind" && continue
      printf '%s\t%s\t%s\t%s\n' "$n" "$slug" "$kind" "$title"
    done
}

# Is there already an open PR touching species/<slug>/ ?
pr_for_slug() {  # slug kind; a locale lives under locales/, a species under species/
  local slug="$1" kind="${2:-species}" dir n
  [ -n "$slug" ] || return 1
  case "$kind" in locale) dir="locales/$slug/";; *) dir="species/$slug/";; esac
  n=$(gh pr list --repo "$GH_REPO" --state open --limit 100 --json number,files \
          -q "[.[] | select(any(.files[]; .path | startswith(\"$dir\")))] | length" 2>/dev/null || echo 0)
  [ "${n:-0}" != "0" ]
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
  local issue slug sci model variant kind
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
  pr_for_slug "$slug" "$kind" && die "an open PR already touches $kind/$slug/; pick another issue"
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
  wpath="$WORKTREE_ROOT/$slug"
  [ -e "$wpath" ] && die "worktree path already exists: $wpath"
  # A leftover branch is a retry, not a fatal collision. cmd_spawn is called
  # directly from the refill loop, so die() here would exit the whole supervisor
  # and end the fleet permanently. Reset the branch to base and start over.
  local branch_flag=-b
  if git -C "$REPO" show-ref --quiet "refs/heads/$branch"; then
    branch_flag=-B
    say "retrying $slug: resetting branch $branch to $BASE_REF"
  fi

  ( cd "$REPO" && git fetch --quiet origin && git worktree add "$branch_flag" "$branch" "$wpath" "$BASE_REF" ) >/dev/null

  # Region hints come from the issue body, so the agent does not have to guess.
  local regions
  # shellcheck disable=SC2016
  regions=$(gh issue view "$issue" --repo "$GH_REPO" --json body \
            | python3 -c 'import json,re,sys
b=json.load(sys.stdin)["body"] or ""
m=re.search(r"[Ss]uggested regions.*?\n(.*?)(\n\n|\Z)", b, re.S)
print(" ".join(re.findall(r"`([A-Z]{2}(?:-[A-Z0-9]{1,3})?)`", m.group(1))) if m else "")')

  local brief="$STATE_DIR/$slug.brief.md"
  [ -n "$regions" ] || regions=$(gh issue view "$issue" --repo "$GH_REPO" --json body \
    | python3 -c 'import json,re,sys
b=json.load(sys.stdin)["body"] or ""
print(" ".join(re.findall(r"\b([A-Z]{2}(?:-[A-Z0-9]{1,3})?)\b", b))[:40])')

  render_brief "$issue" "$slug" "$sci" "$regions" "$wpath" "$branch" "$brief" "$kind" "$brief_tpl"

  local log="$STATE_DIR/$slug.log" status="$STATE_DIR/$slug.status.md" launch="$STATE_DIR/$slug.launch.sh"
  printf '# %s\nissue: %s\nscientific: %s\nbranch: %s\nworktree: %s\nmodel: %s\nregions: %s\nstarted: %s\n\n' \
    "$slug" "$issue" "$sci" "$branch" "$wpath" "$model" "$regions" "$(date -u +%FT%TZ)" > "$status"
  printf 'workspace=none\nagent=%s\nworktree=%s\nbranch=%s\nissue=%s\nslug=%s\nscientific=%s\nmodel=%s\nvariant=%s\nregions=%s\nlog=%s\nstatus=%s\nbrief=%s\nmain=%s\n' \
    "$slug" "$wpath" "$branch" "$issue" "$slug" "$sci" "$model" "$variant" "$regions" "$log" "$status" "$brief" "$REPO" \
    > "$STATE_DIR/$slug.meta"

  cat > "$launch" <<LAUNCHER
#!/usr/bin/env bash
exec > "$log" 2>&1
echo "=== fleet.sh spawn \$(date -u +%FT%TZ) model=$model variant=$variant"
cd "$wpath" || exit 9
[ -f "$PERMISSIONS" ] && export OPENCODE_CONFIG="$PERMISSIONS"
"$AGENT_BIN" run --model "$model" --variant "$variant" --dir "$wpath" \
  --title "species $sci #$issue" --auto "\$(cat "$brief")"
rc=\$?
echo "=== agent exited rc=\$rc \$(date -u +%FT%TZ)"
LAUNCHER
  chmod +x "$launch"

  # Detached, so one fleet member's exit cannot take the supervisor down with it.
  setsid nohup "$launch" </dev/null >/dev/null 2>&1 &
  disown 2>/dev/null || true
  advance_model

  printf '%s\t%s\n' "$issue" "$slug" >> "$STATE_DIR/queue.tsv"
  say "spawned $slug (issue $issue, model $model)"
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
  local slug="$1" model br run age last pr ci
  [ -f "$STATE_DIR/$slug.meta" ] || { printf '%-26s %-40s %s\n' "$slug" "-" "no meta"; return; }
  model=$(meta_get "$slug" model); br=$(meta_get "$slug" branch)
  if agent_running "$slug"; then run=running; else run=stopped; fi
  age=$(( ( $(date -u +%s) - $(date -u -d "$(sed -n 's/^started: //p' "$STATE_DIR/$slug.status.md" | head -1)" +%s 2>/dev/null || date -u +%s) ) / 60 ))
    pr=$(pr_field "$slug" number,state "#\(.number) \(.state)")
  ci=$(pr_field "$slug" statusCheckRollup '[.statusCheckRollup[]?.conclusion] | if length==0 then "none" else (join(" ")) end')
  last=$(tail -2 "$STATE_DIR/$slug.log" 2>/dev/null | tr -d '\r' | grep -v '^$' | tail -1 | cut -c1-70)
  printf '%-26s %-40s %-8s %-6s %-3s %-8s %s\n' "$slug" "$model" "$run" "${age}m" "$pr" "$ci" "$last"
}

cmd_teardown() {
  need_repo
  local slug force=0
  [ $# -ge 1 ] || die "need a slug"
  slug="$1"; shift || true
  while [ $# -gt 0 ]; do case "$1" in --force) force=1; shift;; *) shift;; esac; done
  [ -f "$STATE_DIR/$slug.meta" ] || die "no metadata for $slug in $STATE_DIR"
  local wt br; wt=$(meta_get "$slug" worktree); br=$(meta_get "$slug" branch)

  # Never tear down while the agent is mid-flight, unless forced.
  if [ "$force" = 0 ] && agent_running "$slug"; then
    say "$slug is still running; pass --force once its PR is open"
    return 0
  fi
  if [ "$force" = 0 ] && [ -d "$wt" ] && [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
    say "$wt has uncommitted changes; refusing to tear down. Inspect it, then --force."
    return 1
  fi
  [ -d "$wt" ] && git -C "$REPO" worktree remove --force "$wt"
  git -C "$REPO" worktree prune
  rm -f "$STATE_DIR/$slug.meta" "$STATE_DIR/$slug.status.md" \
        "$STATE_DIR/$slug.brief.md" "$STATE_DIR/$slug.launch.sh"
  # Say which of the two happened. "because it is the PR" on its own let an
  # agent that died with no PR look delivered, so its issue went unclaimed.
  if pr_for_slug "$slug"; then
    rm -f "$STATE_DIR/$slug.log"
    say "torn down $slug; branch kept ($br) because it is the PR"
  else
    say "torn down $slug; NO PR was opened, branch $br kept for salvage, issue still needs work"
    say "  agent log kept for diagnosis: $STATE_DIR/$slug.log"
  fi
}

cmd_supervise() {
  local once=0
  while [ $# -gt 0 ]; do
    case "$1" in --once) once=1; shift;; --min) FLEET_MIN=$2; shift 2;; --max) FLEET_MAX=$2; shift 2;; *) shift;; esac
  done
  [ "$FLEET_MAX" -ge "$FLEET_MIN" ] || die "--max must be >= --min"

  while :; do
    # Reap: an agent that finished with a PR leaves the fleet.
    shopt -s nullglob
    for m in "$STATE_DIR"/*.meta; do
      slug=$(basename "$m" .meta)
      agent_running "$slug" && continue
      pr=$(pr_field "$slug" number,state '"#\(.number) \(.state)"')
      case "$pr" in \#*) echo "[$(date -u +%T)] $slug finished: $pr -> teardown"
                        cmd_teardown "$slug" --force || true ;;
           *)   note_route_failure "$slug"
          echo "[$(date -u +%T)] $slug stopped with NO PR (model $(meta_get "$slug" model)); log tail:"
                tail -5 "$STATE_DIR/$slug.log" | sed 's/^/    /'
                cmd_teardown "$slug" --force || true ;;
      esac
    done

    # Refill to the floor, never past --max. A slug is skipped only once it has
    # burned FLEET_MAX_ATTEMPTS tries, so a flaky model route or a dropped
    # connection does not retire an issue for the life of the queue, while a
    # genuinely broken issue still stops being retried.
    local live pick row_pick n sl ti sc fleet_state=OK
    # Count via array glob, not `ls "$STATE_DIR"/*.meta`. nullglob is set above,
    # so an unmatched glob expands to zero words and bare `ls` would list the
    # current directory instead, reporting the repo root's entry count as the
    # fleet size and silently skipping every refill.
    local metas=("$STATE_DIR"/*.meta)
    live=${#metas[@]}
    if [ "$live" -lt "$FLEET_MIN" ]; then
      # `|| true`: a gh outage must not kill the loop. Without an issue list the
      # fleet just waits a poll and tries again.
      pick=$(cmd_list_issues || true)
      # Key on FILENAME, not NR==FNR. queue.tsv is empty on a first run, and with
      # an empty first file NR and FNR advance in lockstep, so NR==FNR stays true
      # for every candidate row and the whole queue is swallowed as "already tried".
      # A slug with a live agent is always skipped, whatever its attempt count:
      # the retry budget would otherwise offer a running agent its own slug.
      local busy
      busy=$(for m in "${metas[@]}"; do basename "$m" .meta; done | paste -sd' ' -)
      if [ -f "$STATE_DIR/queue.tsv" ]; then
        pick=$(printf '%s\n' "$pick" | awk -F'\t' -v q="$STATE_DIR/queue.tsv" \
          -v max="$FLEET_MAX_ATTEMPTS" -v busy="$busy" '
          BEGIN { k = split(busy, b, " "); for (i = 1; i <= k; i++) if (b[i] != "") live[b[i]] = 1 }
          FILENAME == q { if ($2 != "") n[$2]++; next }
          { s = $2; if (s == "" || (s in live)) next; if ((s in n) && n[s] >= max) next; print }
        ' "$STATE_DIR/queue.tsv" -)
      fi
      row_pick=$(printf '%s\n' "$pick" | head -1)
      if [ -z "$row_pick" ]; then
        if [ "$fleet_state" = OK ]; then
          echo "[$(date -u +%T)] STARVED: live=$live below floor $FLEET_MIN, no eligible issue left"
        fi
        fleet_state=STARVED
      fi
      while [ -n "$row_pick" ] && [ "$live" -lt "$FLEET_MIN" ]; do
        IFS=$'\t' read -r n sl kind ti <<<"$row_pick"
        if [ "$kind" = locale ]; then
          sc="$sl"
        else
          sc=$(gh issue view "$n" --repo "$GH_REPO" --json title 2>/dev/null \
               | python3 -c 'import json,sys;t=json.load(sys.stdin)["title"];print(t[t.rindex("(")+1:-1].strip() if "(" in t else "")' 2>/dev/null || true)
          [ -n "$sc" ] || sc="$ti"
        fi
        ( cmd_spawn --issue "$n" --slug "$sl" --scientific "$sc" --kind "$kind" ) || break
        live=$(( live + 1 ))
        row_pick=$(printf '%s\n' "$pick" | awk -F'\t' -v s="$sl" 'NR>1 && $2 != s' | head -1)
      done
    fi
    printf 'live=%s floor=%s max=%s state=%s at=%s\n' \
      "$live" "$FLEET_MIN" "$FLEET_MAX" "$fleet_state" "$(date -u +%FT%TZ)" \
      > "$STATE_DIR/heartbeat"
    echo "[$(date -u +%T)] fleet=$live (min $FLEET_MIN max $FLEET_MAX) state=$fleet_state next-model=$(next_model)"
    [ "$once" = 1 ] && return 0
    sleep "$POLL_SECONDS"
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
    "$WORKTREE_ROOT/$slug" "$BRANCH_PREFIX/$kind-$issue-$slug" "$out" "$kind"
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
