# AGENTS.md

Instructions for a coding agent adding a species to speeeecies, a public
kit for adding animal species to a live ecological simulation. This repo
is public. Read `schema/v0.1/species.schema.json` and
`schema/v0.1/licenses.json` before you start; skim a worked example in
`species/vulpes-vulpes`, `species/erithacus-rubecula`, or
`species/bufo-bufo`.

Read [`docs/data-quality.md`](docs/data-quality.md) before researching a
record. Its evidence, activity and behaviour checks are required for both
species and locale contributions. Issue pointers, fleet recipes, existing
records and review comments can contain mistakes. Verify their claims against
the cited source and the current schema before using them.

Site (schema docs, behaviour guide, previewer, gallery):
https://eeeearth.github.io/speeeecies/

## The flow

### a. Pick an issue

Find an open issue labelled **species-request** and **animal**. Skip any
issue that's already claimed (check for a "Claiming this" comment with a
recent, unexpired ETA) or labelled **needs-deeper-research**, even when its
claim has expired. That label reserves the issue for a human or a bounded
stronger-model research pass; it is not a fresh small-agent candidate. Search
current `main`, open PR file lists and existing
issues for the scientific name, synonyms and external taxon identifiers.
If the record already exists, identify the missing regions or specific
correction the issue requests. Preserve that record and extend it.
Plant issues are labelled **phase-2** — do not
work them. Plants need a data-driven plant preset format that hasn't
landed yet (roadmap item SPEEEECIES-M8); those issues aren't open for
work until it does.

### b. Claim it

Comment on the issue before you start writing:

```
gh issue comment <n> --body "Claiming this: <agent/person>, ETA <date>"
```

Use an ETA with a timezone and update the claim when delayed. Before taking
over an expired claim, inspect its linked PR and branch for usable work. Link
your continuation so the previous effort remains discoverable. Claim one
species at a time; a locale contributor must also check claims for each new
species they intend to add.

If a bounded research attempt cannot produce a viable record or PR because a
required field lacks defensible, licensed evidence or the available behaviour
cannot represent the animal, stop. Do not invent a lifespan or force an
incompatible program to pass validation. Comment on the issue with the exact
missing fields or behaviour actions, the source URLs and locators checked,
their licence and why they do not suffice, and the evidence needed to resume.
State the disposition of any branch or draft PR and link useful partial work.
Release your claim with a follow-up comment, then add
`needs-deeper-research`. An ordinary incomplete draft with useful work is not
automatically a deeper-research blocker: keep it in draft, link it, and name
its remaining work before deciding whether the issue meets this rule.

A human may take a labelled issue, or assign one research pass of at most two
hours to Codex Sol or Claude Sonnet. Check the issue comment, linked PR and
prior branch first; search specifically for the missing evidence and stop when
the two hours expire or those blockers have been resolved.
Do not route this handoff to Luna, Haiku, Astra or Fable. If the pass finds
verifiable licensed evidence and a fitting behaviour, record the URLs,
locators and decision on the issue, clear `needs-deeper-research`, and only
then return it to the ordinary claim queue. If it remains blocked, update the
issue with what was checked and retain the label.

### c. Create the species record

`species/<slug>/species.json`, where `<slug>` is the scientific name
lowercased with spaces turned to hyphens (`Vulpes vulpes` ->
`vulpes-vulpes`; must match the schema's `slug` pattern and equal the
directory name).

Start from the closest worked example — `species/vulpes-vulpes`,
`species/erithacus-rubecula`, or `species/bufo-bufo` — and adapt it field
by field rather than starting blank. Look up external identifiers:

- GBIF usage key: `https://api.gbif.org/v1/species/match?name=<Scientific name>`
- iNaturalist taxon id: `https://api.inaturalist.org/v1/taxa?q=<Scientific name>`

Both are required (`external.gbif_usage_key`, `external.inat_taxon_id`).
`itis_tsn`, `wikidata`, and other external keys are optional but useful —
add them if you find them.

Resolve each identifier at its own provider. Check the returned canonical
name, rank, accepted/synonym status and accepted-name link. Record the date
checked. Resolve provider disagreements in the PR; never silently use a
subspecies identifier for a species or put a GBIF key in `itis_tsn`.
Copy the example's structure, then replace its biological claims and source
coverage. Existing examples are scaffolds that also need checking.

### d. Choose a behaviour

Look through `behaviors/*.json` for a program whose description fits the
species (ground forager, perching songbird, nocturnal anuran, and more may
exist by the time you read this). Set `behavior.program` and override
`behavior.params` as needed — you cannot add params a program doesn't
declare. Only write `species/<slug>/behavior.json` (a program used by this
species alone) if nothing shared fits; explain why in the PR.

Read the executed actions and substituted parameters. Check every gait and
feeding action, day/night exits, and the actual months enabled for each target
region. `month_in` is an explicit set: `[8, 12]` enables August and December.
Inherited April/May entries remain enabled when endpoint parameters change.
A provenance note cannot make an incompatible behaviour acceptable. Use a
fitting program or document the unsupported capability as a blocker.

### e. Fetch activity curves

For each region you're targeting (the issue usually suggests some, as ISO
3166-1 or 3166-2 codes):

```
uv run tools/fetch_activity.py <slug> --region <ISO> --write
```

This fills `activity.regions[]` and the matching `sources` entries. Run it
once per region.

Inspect its query URLs, licence filters, geographic scope, monthly counts and
`usable` flags. Observation frequency is an imperfect activity proxy. A
successful command can still return a low-count fallback. Disclose that case
and use the fallback rules in `docs/data-quality.md`; never invent observations
or change `usable` to make the result appear supported. Confirm native or
introduced status from range evidence independently of occurrence counts.

### f. Validate

```
uv run tools/validate.py species/<slug> --write-attribution --report
```

Fix errors and rerun until there are none (warnings, e.g. an NC source,
are allowed but justify them in the PR). `--write-attribution` regenerates
`species/<slug>/ATTRIBUTION.md` — always rerun it after any source change
and commit the result.

Before requesting review, run the public repository checks on the final
commit, including all species and locales. A shared species can affect many
locales:

```
uv run tools/validate.py --self-check
uv run tools/validate.py --report
uv run tools/validate.py --locale all --report
uv run --with pytest --with jsonschema pytest tools/tests -q
```

Regenerate attribution for every changed record, commit it, then confirm
`uv run tools/validate.py --write-attribution` leaves `git diff -- species`
empty. Keep reports and session notes outside the tracked tree. Stage explicit
paths after reviewing the diff. Do not change root `STATUS.md` or commit a
research dump, private source text, or another contributor's scratch notes.

### g. Preview

```
python3 tools/build_site.py
python3 -m http.server 18060 --bind 127.0.0.1 -d _site
```

The example uses the Codex port block; use your tool's allocated port when
one is specified by your environment. Open
`http://127.0.0.1:18060/preview.html?species=<slug>` and check every
pose the record declares (`idle`, plus each locomotion mode's pose, plus
`perched` if applicable). Use `?pose=<name>` to switch, `?yaw=`/`?pitch=`
to orbit. Look for parts clipping, colours on the wrong parts, and poses
that don't read as the intended gait.

Report the poses actually inspected and any limitations. If browser access is
unavailable, leave the preview checklist unchecked and request a visual pass
in the PR. A BioCLIP score does not replace inspecting the rendered animal.

### h. Visual check (optional, advisory)

```
uv run tools/visual_check.py <slug> --write
```

Runs on CPU only; downloads a BioCLIP model (~1 GB) on first use. It
scores the rendered model zero-shot against the species' name and a few
look-alikes. Block models are stylised — a low score is a hint to look
again, not proof of a mistake. Prefer permissively licensed models and
tools for anything like this (MIT/Apache; BioCLIP's weights qualify) and
name what you used in the PR.

### i. Open the PR

Title: `species: <common name> (<Scientific name>)`. Body: paste the
validate report, write `Closes #<issue number>`, and follow the pull
request template's checklist.

Include the evidence and behaviour summaries from `docs/data-quality.md`,
warnings with their resolutions, and the commit tested. For a partial fix,
use `Refs #<issue number>` and list remaining work. An incomplete submission
belongs in a draft PR. Check off only work you performed. Confirm the PR URL
and CI result; pushing a branch alone does not create a PR.

Address feedback against the current head and identify the commit resolving
each finding. Check suggested replacement values and licences yourself. Ask
for clarification if a review conflicts with the schema or licence policy.
Contributors stop at a review-ready PR; maintainers own merging and deployment.

## Contribute a locale

A locale is a place the live simulation
(https://www.youtube.com/@jt55401/live) can show: a public city or district
centroid, its climate, a generic plot, the plants its garden shows, and
at least 8 (better 12 or more) animal species that live there. It is
`locales/<id>/locale.json`, checked against
`schema/v0.1/locale.schema.json`, plus `locales/<id>/flora-catalog.json`,
checked against `schema/v0.1/flora-catalog.schema.json` (optional, but the
validator warns without it). The worked
example is `locales/london-uk/`; copy both files and adapt them. A locale
with the bare minimum passes validation but looks empty on the stream:
read `docs/locale-richness.md` before you start.

### The flow

1. **Pick and claim** an open issue labelled **locale-request**, exactly as
   for species (comment `Claiming this: <agent/person>, ETA <date>`).
2. **Choose the place and its public centroid.** Take the latitude and
   longitude of the city or district from a public page (Wikidata is
   CC0) and round both to **at most 2 decimals** (about 1 km). Record the
   page in `place_source`. Only public centroid coordinates are accepted:
   never a house, a garden, a yard or a street address, even your own.
3. **Fill in the manifest**: `id` (equal to the directory name, e.g.
   `london-uk`), `name`, `country` (ISO 3166-1), `activity_region` (the
   ISO 3166-2 subdivision, or the country code, whose activity curves the
   species carry; e.g. `GB-ENG`), `tz` (IANA, e.g. `Europe/London`),
   `koppen`, `elevation_m`, `plot_template` (one of `suburban-lot`,
   `rural-lot`, `rowhouse-garden`, `street-block`, `courtyard`), `species`,
   `blurb`, `facts` (each with a `source` and an allow-listed licence,
   plus `attribution` unless it is CC0 or public domain), and optionally
   `flora_wishlist` and `contributors`.
4. **List at least 8 species, and aim for 12 or more**, that exist under
   `species/`: several garden birds (one of them large and conspicuous),
   a few mammals including a nocturnal one, and an amphibian or reptile
   if the plot suits one. Add any that are missing by following the
   species flow above; a locale PR may carry the new species it needs.
   The validator warns (`LocaleFewSpecies`) below 12.
5. **Write `flora-catalog.json`**: at least 8 plant taxa, at least 2 of
   them evergreen, chosen from `schema/v0.1/flora-taxa.json` (the plants
   the simulation can draw), each naming the local species it stands in
   for. Copy `locales/london-uk/flora-catalog.json` and follow
   "Writing `flora-catalog.json`" in `docs/locale-richness.md`. Without a
   catalog the garden gets a generic set of a few large trees for its
   Köppen class.
6. **Fetch an activity curve for the locale's region** for every listed
   species that lacks one. For a subdivision, pass the iNaturalist place id
   and the GADM id:

   ```
   uv run tools/fetch_activity.py <slug> --region GB-ENG --inat-place-id 6858 --gbif-gadm-gid GBR.1_1 --write
   uv run tools/validate.py species/<slug> --write-attribution
   ```

7. **Validate** the locale and the repository:

   ```
   uv run tools/validate.py --locale <id> --report
   uv run tools/validate.py --self-check
   ```

8. **Open the PR** titled `locale: <place> (<id>)` with the report,
   `Closes #<issue number>`, and the locale rows of the PR template
   checked. Check the new page at `locales.html` in the previewed site.

When extending an existing species, retain its unrelated traits, sources,
regional curves and provenance from current `main`. Compare each changed
record with its base and explain every removal or replacement. Check all
locales that use it and run the all-locale validator. Do not resolve a merge
conflict by replacing the entire shared record with your branch's version.
Hemisphere-specific calendars and seasonal phases must be scoped to supported
regions. A global behaviour parameter cannot encode separate regional seasons;
report that limitation instead of claiming it does.

### What the locale check enforces

`validate.py --locale <id>` fails unless:

- the manifest matches `schema/v0.1/locale.schema.json`, its `id` equals
  the directory name, and `activity_region` lies inside `country`;
- it lists at least 8 species, each of which exists under `species/`,
  passes its own validation (so every datum has provenance with an
  allow-listed licence), has 12 monthly activity values for
  `activity_region`, resolves at least one behaviour program, and has a
  block mesh with an `idle` pose and at least one move pose (`walk`,
  `hop`, `fly`, ...);
- `public_lat` and `public_lon` have at most 2 decimals;
- every fact's source has an allow-listed licence and, unless CC0 or
  public domain, an attribution;
- if `flora-catalog.json` exists: it matches
  `schema/v0.1/flora-catalog.schema.json`; every `taxon` is in
  `schema/v0.1/flora-taxa.json` with the same `archetype`, and that
  archetype is one the import can place (not `Shrub`, `Forb`, `Graminoid`
  or `Fern` yet); every entry has a positive `community_weight` for the
  locale id; every source has an allow-listed licence and, unless CC0 or
  public domain, a `title` that serves as the attribution;
- no file in the locale's directory contains text shaped like a street
  address (a number, a capitalised name and `St`, `Ave`, `Rd`, `Ln`, `Dr`,
  `Street`, `Avenue` or `Road`), an absolute home-directory path, a
  hostname ending in `.local`, or an SSH git remote.

It also warns, without failing, when a locale will look sparse: fewer
than 12 species (`LocaleFewSpecies`), no flora catalog
(`LocaleNoFloraCatalog`), fewer than 8 plant taxa (`LocaleSparseFlora`) or
fewer than 2 evergreens (`LocaleFewEvergreens`), and when a catalog
entry's size or evergreen flag differs from the model that is drawn
(`FloraSizeMismatch`, `FloraEvergreenMismatch`). Fix these or explain them
in the PR.

`validate.py --self-check` runs the same text lint over the whole
repository (except `tools/tests/fixtures/`, where the lint's deliberately
bad test strings live). CI runs both on every PR.

### What "validated" means

Public validation checks structure and consistency. The contributor must also
check source accuracy and behaviour as described above. Passing CI does not
prove that a source supports a value or that the animal behaves correctly.

The contribution PR and the live release are separate stages. Contributors
need only the public kit. A maintainer may hold publication while an affected
live release is awaiting acceptance; the hold should identify its owner and
clearance condition in the PR. Contributors should continue source review and
CI work without accessing private imports or changing the live service.

A locale is validated when all of these have happened, in this order:

1. **A maintainer merges the PR to `main`.** This is the human review;
   nothing downstream starts before it.
2. **CI is green at the merge commit**, including the locale check and
   the self-check above.
3. **The maintainers' private import succeeds.** The simulation converts
   the species and their activity curves for the locale's region, derives
   a weather profile from climate normals at the public centroid, builds
   the plot from `plot_template`, takes the locale's `flora-catalog.json`
   (or a default plant catalog for the Köppen climate), and checks that a summer scene contains at least one animal.
   This runs on the maintainers' machine; its output is not published.

Only then does the locale enter the live rotation. A maintainer (or the
import itself) comments on the merged PR to say it is in the rotation and
when it first appears on the stream. If the import fails, the locale stays
out of the rotation and the maintainers follow up on the PR.

### Plants: a flora catalog, not plant records

A locale's `flora-catalog.json` says which plants its garden shows, drawn
with the models in `schema/v0.1/flora-taxa.json` and standing in for the
local species. Plant *species records* are still phase 2: they need a
plant format first (roadmap item SPEEEECIES-M8), so do not write
`species/<slug>/` records for plants or work `phase-2` issues.
`flora_wishlist` lists local plants by name for that later work,
especially ones no drawable taxon resembles.

## Data rules

- **Every datum needs provenance**: a `provenance` entry pointing at one
  or more `sources`, each with a licence. The validator lists anything
  uncovered.
- **Licence preference order**: CC0 / public domain first, then CC BY,
  then CC BY-SA / ODbL. Non-commercial (CC BY-NC, CC BY-NC-SA) is accepted
  only as a last resort, flagged, and kept on its own licence (never
  relicensed into CC BY-SA) — justify every NC source in the PR body. ND
  and unknown/missing licences are rejected; the validator will fail the
  record.
- **Prefer permissively licensed models and tools** wherever you use one
  (MIT/Apache — e.g. BioCLIP's weights for `visual_check.py`) and name
  them in the PR.
- **Never invent a number.** If you can't find a sourced value: omit the
  field if it's optional, or set `derived: true` with a `note` explaining
  exactly how you derived it (e.g. converted units, averaged two sources,
  inferred from a close relative). For values that are pure judgement —
  `wariness`, behaviour `params`, the `look` block — say so honestly:
  `note: "judgement"` (or similar) is fine. Dishonest precision is worse
  than an honest guess.
- **Never strip attribution.** Every non-CC0/public-domain source needs an
  `attribution` string; it flows into `ATTRIBUTION.md` and must never be
  removed, even by later edits.

### Good sources (verify the licence every time — it can change)

- Wikipedia — CC BY-SA
- Wikidata — CC0
- GBIF backbone — CC BY 4.0
- ITIS — public domain
- Open-access papers under CC BY
- Open trait datasets, once you've checked their licence yourself

### Sources to avoid

- Animal Diversity Web — CC BY-NC-SA; last resort only, and flag it
- IUCN Red List pages — not openly licensed
- Most field-guide and charity websites — all rights reserved

## Pre-PR checklist

- [ ] Issue claimed with a comment before work started; issue is labelled
      `species-request` and `animal` (not `phase-2`)
- [ ] `species/<slug>/species.json` validates: `uv run tools/validate.py
      species/<slug> --report` shows no errors
- [ ] `species/<slug>/ATTRIBUTION.md` regenerated with
      `--write-attribution` and committed
- [ ] Activity curves fetched for every suggested region with
      `fetch_activity.py`; missing or provisional regions explicitly listed
- [ ] Identifiers resolve to the stated taxon and rank; range country codes
      and native/introduced status checked independently
- [ ] High-risk claims have source locators and transformations recorded;
      maximum/captive values and authored estimates are labelled accurately
- [ ] Behaviour actions, actual month sets, regional seasons and day/night
      transitions checked against the record and its evidence
- [ ] Existing shared-record fields and regions preserved, or each change
      explained; all species/locales validate on the submitted commit
- [ ] Every pose checked in the previewer
- [ ] Licences preferred CC0/CC BY where possible; any CC BY-SA or NC
      source justified in the PR body
- [ ] No invented numbers; optional fields omitted or marked `derived`
      with a note where sourcing wasn't possible
- [ ] PR title is `species: <common name> (<Scientific name>)`, body has
      the validate report and `Closes #<issue number>`
- [ ] One species per PR
- [ ] No local paths, hostnames, tokens, or other private details in any
      committed file

## What reviewers look for

- **Provenance density**: does every field trace to a real source, or are
  there unexplained numbers? A record that's mostly `derived: true` with
  thin notes gets pushed back.
- **Licence honesty**: is the licence tier actually what the source says?
  Reviewers spot-check `sources[].url` against `sources[].license`.
- **NC justification**: if any source is NC, does the PR explain why
  nothing better was available?
- **Behaviour fit**: does the chosen program (shared or bespoke) actually
  match how the species behaves, or was it picked for convenience?
- **Preview quality**: do all poses look right — no clipping, sensible
  proportions for the body plan, colours on the right parts?
- **Schema fit, not schema abuse**: values within the ranges the schema
  expects (e.g. `size_class` actually matching `mass_kg`), not squeezed to
  pass validation.
- **Attribution completeness**: `ATTRIBUTION.md` present, current, and
  matching `sources`.
