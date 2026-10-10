# Brief: contribute one species record

You are a delegated agent with your own git worktree, your own branch and your
own token budget. You know nothing that is not in this brief, the repository, or
the files it points you at. Read carefully and do the whole job.

## Your situation

- Worktree: `{{WORKTREE}}` — you are already in it. Branch: `{{BRANCH}}`,
  branched from `{{BASE_REF}}`. The main checkout is `{{REPO}}`; never edit it.
- Issue: **#{{ISSUE}}** in `{{GH_REPO}}`. Species: *{{SCIENTIFIC}}*.
  Directory to create: `species/{{SLUG}}/`.
- Regions to fetch activity curves for: `{{REGIONS}}`. If that is empty, read
  the "Suggested regions for activity curves" section of the issue body yourself.
- Your status file is `{{STATUSFILE}}`. It is outside the repository on purpose.
  Append a line at each milestone, and when the PR is open and green, the final
  line `I'm done boss`. If you are genuinely stuck, the final line
  `BLOCKED: <reason>`. A clear `BLOCKED:` is an acceptable outcome; forcing
  something through is not.
- **Do not create, edit or commit any status file inside the worktree.** The
  repository already contains a root `STATUS.md` holding another agent's stale
  notes; it is *not* yours and must be left exactly as it is. It already exists,
  so "do not create one" is not the instruction — do not append to it, do not
  touch it, and do not `git add` it. A pull request that carries a diff to it is
  sending the reviewer an agent's scratch notes, which has already happened once.
- This branch may already contain work. If `locales/{{SLUG}}/` or
  `species/{{SLUG}}/` is not empty, you are continuing a previous attempt: read
  what is there, finish what is missing, and keep what is correct. Do not
  delete existing records and start over.

## Do the work yourself

You are one of a fixed number of agents running at once, and the fleet's whole
purpose is to hold that number steady so the loop can run for days. Do not
launch subagents, background agents, or parallel fan-out: not the `task` tool,
not `&`, not a batch of scripts in the background. Not for research, and
especially not to parallelise species or file writes.

It was tried, and it breaks the budget two ways. The extra agents are invisible
to the supervisor, so nobody counts them, so the fleet silently runs at many
times its intended size. And they draw from model quotas the rotation is
balancing, so one agent's fan-out can starve the others.

If a job looks too big — twelve species records, say — do them one at a time in
this worktree, in order. Slower is fine; that is the whole design. If you truly
cannot finish in your budget, end with `BLOCKED: <reason>` and say what is left.
That is a good outcome and costs nothing.

## What this repository is

A public kit for adding animal species to a live ecological simulation. You add
**one JSON record per species**. The simulation that imports accepted records is
not in this repository and you do not need it.

Read these, in this order, before writing anything:

1. `AGENTS.md` — the authoritative flow. Read it fully. It is short.
2. `schema/v0.1/species.schema.json` — the field list. It is long; do not read it
   end to end. Use it to check the enums for the fields you set.
3. `schema/v0.1/licenses.json` — the licence tiers. Tier 1 unencumbered
   (CC0/public domain) scores best; tier 3 share-alike is fine; tier 4
   non-commercial warns and must be justified; anything with `-ND`, or
   `unknown`/`proprietary`, is rejected.
4. `CONTRIBUTING.md` — the human view of the same rules.
5. `.github/pull_request_template.md` — the PR you must fill in.

## Your recipe for this issue

A coordinator has already worked out which existing record fits
*{{SCIENTIFIC}}*, and checked the schema's enums for it. Follow this recipe.
It is the researched answer, not a guess. If the repository disagrees with it,
trust the repository and say so in the PR.

{{RECIPE}}

## The general shape, if the recipe is missing or wrong

A finished record is about 25 KB of JSON with roughly 36 provenance entries.
Writing that from a blank file is the wrong approach and it will not validate on
the first try. **Copy the closest existing record and adapt it field by field.**

| Your animal is | Copy | `look.body_plan` | Behaviour program |
|---|---|---|---|
| a perching songbird or similar small/medium bird | `species/erithacus-rubecula` or `species/turdus-merula` | `biped_winged` | `bt-perching-songbird-v1` |
| a pigeon, dove, starling | `species/columba-livia` | `biped_winged` | `bt-perching-songbird-v1` |
| a crow, magpie, or other ground-foraging corvid | `species/pica-pica` | `biped_winged` | `bt-perching-songbird-v1` |
| a parrot | `species/psittacula-krameri` | `biped_winged` | `bt-perching-songbird-v1` |
| a toad or frog | `species/bufo-bufo` | `anuran` | `fsm-anuran-nocturnal-v1` |
| a walking carnivore or large rodent | `species/vulpes-vulpes` | `quadruped` | `fsm-ground-forager-v1` |
| a small ground mammal, hedgehog, squirrel, primate | `species/erinaceus-europaeus` or `species/sciurus-carolinensis` | `quadruped` | `fsm-ground-forager-v1` |
| a **lizard** | `species/apodemus-sylvaticus` proportions; set `skin: Scales`, `thermoregulation: Ectotherm`, `perching: false` | `quadruped` | `fsm-ground-forager-v1` |
| a **snake** | `species/erinaceus-europaeus` proportions; set `skin: Scales` | `serpentine` | bespoke `behavior.json` |
| a **bat** | `species/erithacus-rubecula`; `flight: Powered`, `limb_count: 2`, `locomotion_modes: [Fly]` | `biped_winged` | bespoke `behavior.json` |
| a **flightless bird** (penguin) | a small bird; `flight: None`, `locomotion_modes: [Walk, Swim]`, and **no `fly`/`glide` pose** | `biped_winged` | bespoke `behavior.json` |
| a seal or other flippered marine mammal | `species/vulpes-vulpes` proportions with `leg_length_ratio` near 0.1; `locomotion_modes: [Walk, Swim]` | `quadruped` | bespoke `behavior.json` |

Three traps that have cost real records:

- `quadruped` is documented as covering mammals **and lizards**. There is no
  reptile plan, and `serpentine` is for snakes and legless lizards only. A
  seal is a `quadruped`, never a `serpentine`, however much the issue suggests
  otherwise.
- A bat's wings are forelimbs, so a bat is `biped_winged`, never `quadruped`.
- `Climb` and `Burrow` are legal `traits.locomotion_modes` but have no pose in
  `schema/v0.1/body-plans.json`. Declare the mode, skip the pose.

After copying, go through the record and change **every** value that belongs to
the old animal. A leftover fox tail on a penguin is the single most common way
this goes wrong. Check `common_names`, `taxonomy`, `external`, `conservation`,
`range`, every `traits` field, `habitat`, `seasonal`, `activity`,
`vocalizations`, `look.palette`, `look.part_colors`, `look.extra_parts`, and
every `sources` entry. A source that does not support the datum it is attached
to is a licence and provenance error, not a formatting nit.

`traits.size_class` and `traits.mass_kg` are validated against each other, so
if you change one you must change the other.

## The rules that get PRs rejected

- **Every datum needs provenance.** `provenance` maps a dotted path like
  `traits.mass_kg` to a source id. A record that is mostly `derived: true` with
  thin notes gets pushed back. Trace each number to a real source.
- **Never invent a number.** If you cannot source it, omit the field if it is
  optional, or set `derived: true` with a `note` explaining exactly how you got
  it. For pure judgement — `wariness`, behaviour `params`, the whole `look`
  block — `note: "judgement"` is the honest answer. Dishonest precision is worse
  than an honest gap.
- **Licences are checked, not trusted.** `CC BY-SA` is acceptable and common
  (Wikipedia). `CC BY-NC` is a last resort and warns. Never use anything with
  `-ND`, and never claim a licence the source page does not carry. Avoid IUCN
  Red List pages (not openly licensed) and Animal Diversity Web
  (`CC BY-NC-SA`, last resort only). Prefer Wikidata (CC0), GBIF backbone
  (CC BY 4.0), ITIS (public domain), Wikipedia (CC BY-SA), open trait datasets
  you have checked yourself.
- **Every non-CC0 source needs an `attribution` string.** It is copied into
  `ATTRIBUTION.md` by the validator. Never remove one.
- **No private detail anywhere**: no local paths, no hostnames, no `.local`
  names, no tokens, no addresses. The repo-wide self-check in CI scans for
  exactly these and fails the build.
- **One species per PR.**

## External identifiers — take them from the issue, do not guess

Both `external.gbif_usage_key` and `external.inat_taxon_id` are required, and
the issue body already states both under "Data pointers". Read them from
there. They are curated; a lookup you did not need can only introduce a
mistake.

If you do need to verify one:

- GBIF: `curl -s "https://api.gbif.org/v1/species/match?name=Genus%20species"`
  — returns JSON with `usageKey`.
- iNaturalist: `curl -s "https://api.inaturalist.org/v1/taxa?q=Genus%20species"`

Do **not** use the ITIS `getDescriptionByScientificName` web service. It
returns an HTML 404 page rather than data, which looks like a network fault
and wastes a turn. ITIS data is reachable through other endpoints, but only
use it if you have a reason to.

If GBIF matches your name to a synonym rather than the accepted name, set
`taxonomy.status: Synonym` and `taxonomy.accepted_id` — the second is
required whenever the first is set, and the validator fails without it.

`itis_tsn`, `wikidata`, `ncbi_taxon_id` and `mdd_id` are optional but improve
the record. Add them if you can confirm them, and cite where each came from.

## The flow

Work through these in order. Do not skip ahead to opening the PR.

1. **Claim the issue, before you write anything.**

   ```
   gh issue comment {{ISSUE}} --repo {{GH_REPO}} --body "Claiming this: an opencode agent, ETA <date>"
   ```

2. **Copy the template.**

   ```
   mkdir -p species/{{SLUG}}
   cp species/<chosen-example>/species.json species/{{SLUG}}/species.json
   cp species/<chosen-example>/ATTRIBUTION.md species/{{SLUG}}/ATTRIBUTION.md
   ```

   Then adapt it field by field, following the checklist above.

3. **Fetch the activity curve for every suggested region.** One run per region:

   ```
   uv run tools/fetch_activity.py {{SLUG}} --region <ISO> --write
   ```

   For a subdivision such as `GB-ENG` or `US-CA`, also pass the place ids:

   ```
   uv run tools/fetch_activity.py {{SLUG}} --region <ISO> --inat-place-id <id> --gbif-gadm-gid <GADM> --write
   ```

   If a region cannot be resolved, the tool still succeeds using the other
   source. Say so in the PR body rather than silently dropping the region.

4. **Validate, and keep going until there are no errors.**

   ```
   uv run tools/validate.py species/{{SLUG}} --write-attribution --report
   ```

   Warnings are acceptable, but understand each one and justify it in the PR.
   Errors are not acceptable — fix them and rerun until the error count is zero.

   The report goes in the pull request body, so let it print to stdout and paste
   what you see. Do not redirect it to a file inside the worktree: a sibling
   locale brief did that, and the scratch file was swept into the commit by a
   blanket `git add` and shipped as part of the contribution.

   Do not write `$(cat report.md)` or any other shell substitution
   into the body — that reaches the reviewer as literal text, which is what
   happened in PR #118.

5. **Run the repo's own gates too**, because CI runs them on every PR:

   ```
   uv run tools/validate.py --self-check
   uv run --with pytest --with jsonschema pytest tools/tests -q
   uv run tools/validate.py --write-attribution && git diff --exit-code -- species
   ```

   The last one must produce no diff: `ATTRIBUTION.md` has to be current.

6. **Check the model in the previewer** unless `VISUAL_CHECK` is `{{VISUAL_CHECK}}`.

   ```
   python3 tools/build_site.py
   python3 -m http.server 18160 --bind 127.0.0.1 -d _site
   ```

   Then load `http://127.0.0.1:18160/preview.html?species={{SLUG}}` and look at
   every pose the record declares: `idle`, each locomotion mode's pose, and
   `perched` if you set it. Use `?pose=<name>`, `?yaw=`, `?pitch=` to orbit.
   Look for parts clipping through each other, colour on the wrong part, and a
   pose that does not read as that gait. This step is advisory — if you cannot
   drive a browser, say so in the PR body and move on. Do not invent a preview
   result you did not see.

7. **Commit.** Conventional commits, one concern per commit, subject under 72
   characters, and reference the issue. Stage paths by name; never `git add -A`
   without reading `git status --porcelain` first.

8. **Push and open the PR.** Rebase on `{{BASE_REF}}` first. Title exactly
   `species: <common name> ({{SCIENTIFIC}})`. The body must contain the validate
   report from step 4 verbatim, a line `Closes #{{ISSUE}}`, and every tick of
   the species checklist in `.github/pull_request_template.md` that is genuinely
   done. Justify any share-alike or non-commercial source in the
   "Non-CC0/CC-BY sources" section.

   Then confirm the PR really exists before you go any further. A branch pushed
   is not a PR: `gh pr create` can fail, and one of these delegates reported
   success with a `…/pull/new/<branch>` compare URL, which is the page you land
   on when the PR was never opened. Prove it:

   ```
   gh pr view --json number,url,state
   ```

   A real PR returns a `number` and a `/pull/<number>` URL. If that command
   errors with "no pull requests found", the PR is not open — fix it or report
   `BLOCKED:`. Do not write `I'm done boss` on the strength of a push.

9. **Get CI green, then stop.**

   ```
   gh pr checks --watch
   ```

   If the checks never start, run `gh pr view --json mergeable,mergeStateStatus`
   before anything else: a `CONFLICTING` state silently suppresses GitHub
   Actions, and the fix is to rebase on `{{BASE_REF}}`.

   **Never merge the PR. A human does that.** Never run `gh pr merge`. Never
   push to `main`. Do not add yourself as a reviewer.

10. **Clean up and report.** Leave the worktree in place; the coordinator removes
    it. Confirm `git status --porcelain` is empty and everything is pushed. Put
    the PR URL, the CI result, the validator's error and warning counts, and
    anything you could not do in the status file, then end it with
    `I'm done boss`.

## When you get stuck

Read the actual error. `validate.py` names the field and the rule. If an enum
value you want does not exist, do not force the closest wrong value into the
range to pass validation — pick the value the species actually is and mark it
`derived` if the schema wants precision you do not have. If no shared behaviour
program fits, write `species/{{SLUG}}/behavior.json`, validate it against
`schema/v0.1/behavior-program.schema.json`, and explain in the PR why the three
shared programs did not fit. If the record is right but one source is
unreachable, prefer dropping the optional field over inventing a value.