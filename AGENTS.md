# AGENTS.md

Instructions for a coding agent adding a species to speeeecies, a public
kit for adding animal species to a live ecological simulation. This repo
is public. Read `schema/v0.1/species.schema.json` and
`schema/v0.1/licenses.json` before you start; skim a worked example in
`species/vulpes-vulpes`, `species/erithacus-rubecula`, or
`species/bufo-bufo`.

Site (schema docs, behaviour guide, previewer, gallery):
https://jt55401.github.io/speeeecies/

## The flow

### a. Pick an issue

Find an open issue labelled **species-request** and **animal**. Skip any
issue that's already claimed (check for a "Claiming this" comment with a
recent, unexpired ETA). Plant issues are labelled **phase-2** — do not
work them. Plants need a data-driven plant preset format that hasn't
landed yet (roadmap item SPEEEECIES-M8); those issues aren't open for
work until it does.

### b. Claim it

Comment on the issue before you start writing:

```
gh issue comment <n> --body "Claiming this: <agent/person>, ETA <date>"
```

This avoids duplicate work. If your ETA passes and you haven't opened a
PR, expect someone else to pick it up.

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

### d. Choose a behaviour

Look through `behaviors/*.json` for a program whose description fits the
species (ground forager, perching songbird, nocturnal anuran, and more may
exist by the time you read this). Set `behavior.program` and override
`behavior.params` as needed — you cannot add params a program doesn't
declare. Only write `species/<slug>/behavior.json` (a program used by this
species alone) if nothing shared fits; explain why in the PR.

### e. Fetch activity curves

For each region you're targeting (the issue usually suggests some, as ISO
3166-1 or 3166-2 codes):

```
uv run tools/fetch_activity.py <slug> --region <ISO> --write
```

This fills `activity.regions[]` and the matching `sources` entries. Run it
once per region.

### f. Validate

```
uv run tools/validate.py species/<slug> --write-attribution --report > report.md
```

Fix errors and rerun until there are none (warnings, e.g. an NC source,
are allowed but justify them in the PR). `--write-attribution` regenerates
`species/<slug>/ATTRIBUTION.md` — always rerun it after any source change
and commit the result.

### g. Preview

```
python3 tools/build_site.py
python3 -m http.server 18160 --bind 127.0.0.1 -d _site
```

Open `http://127.0.0.1:18160/preview.html?species=<slug>` and check every
pose the record declares (`idle`, plus each locomotion mode's pose, plus
`perched` if applicable). Use `?pose=<name>` to switch, `?yaw=`/`?pitch=`
to orbit. Look for parts clipping, colours on the wrong parts, and poses
that don't read as the intended gait.

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
      `fetch_activity.py`
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
