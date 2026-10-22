## What this adds

<!-- species: <common name> (<Scientific name>)
     or locale: <place> (<id>) -->

Closes #

<!-- Use Refs # for a partial contribution. Keep incomplete work in draft.
     Only check work you actually performed. -->

## Evidence and scope

<!-- Follow docs/data-quality.md. Keep this concise and reference precise
     provenance entries rather than duplicating the record.
     - Verified taxon names, ranks and identifiers; check date and disagreements.
     - Source locators and transformations for added/changed mass, lifespan,
       diet, range and seasonal claims. Identify authored estimates.
     - Existing records/regions affected; explain every removal or replacement. -->

## Activity and behaviour

<!-- Requested/delivered regions, provider geography, observation counts and
     licence tiers. Identify missing, unusable or authored fallback curves.
     Name the behaviour program and actual enabled months. Explain checks of
     day/night exits, gaits, feeding actions and regional/hemisphere fit.
     State any remaining limitations. -->

## Validate report

<!-- Paste the output of:
uv run tools/validate.py species/<slug> --write-attribution --report
and, for a locale:
uv run tools/validate.py --locale <id> --report
uv run tools/validate.py --self-check
Also run all-species and all-locale validation when requesting review.
Give the tested commit, command results and warning resolutions. A draft may
carry incomplete work, but must state its failures. Do not paste a shell
expression such as $(cat report.md) in place of the actual report. -->

## Preview evidence

<!-- List poses actually inspected and useful views. Link screenshots if
     available. List uninspected poses and request a visual pass if needed.
     Do not claim that public previews prove live-scene acceptance. -->

## Checklist

### Species

- [ ] Closes the linked species-request issue
- [ ] Checked current main and open PRs for the same taxon; claimed the issue
- [ ] Taxon identifiers and source claims checked at their providers
- [ ] Evidence locators, units/statistics and authored transformations documented
- [ ] Validate report pasted above, with no errors
- [ ] `species/<slug>/ATTRIBUTION.md` regenerated (`--write-attribution`) and committed
- [ ] Activity curves generated with `tools/fetch_activity.py` for every suggested region
- [ ] Query scope, licences, counts and usability inspected; gaps/fallbacks disclosed
- [ ] Executed behaviour fits the animal's gaits, diet, time of day and regional seasons
- [ ] Unrelated shared-record fields and regional curves preserved; intentional changes explained
- [ ] Repository self-check, all-species/all-locale validation and applicable tests pass on the submitted commit
- [ ] Previewed and checked every pose (`idle`, each locomotion mode, `perched` if applicable)
- [ ] Licences preferred CC0/CC BY where available; any CC BY-SA or NC source is justified below
- [ ] No personal data, local paths, hostnames, or tokens anywhere in the diff
- [ ] One species per PR (a locale PR may carry the new species it needs)

### Locale (skip for a species-only PR)

- [ ] Closes the linked locale-request issue
- [ ] `locales/<id>/locale.json` passes `uv run tools/validate.py --locale <id> --report`, pasted above
- [ ] Lists at least 8 species under `species/` (aim for 12 or more), each with an activity curve for the locale's `activity_region`
- [ ] `public_lat`/`public_lon` are a public city or district centroid with at most 2 decimals, not a home, yard or street
- [ ] No street address, home path, hostname or private repository anywhere; `uv run tools/validate.py --self-check` passes
- [ ] Every fact has a source with an allow-listed licence (and an attribution unless CC0/public domain)
- [ ] `locales/<id>/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json` (optional but expected: the validator warns without it; plant *species records* are still phase 2, and a flora catalog is not one)

## Non-CC0/CC-BY sources (if any)

<!-- Explain licence choices. CC BY-SA and ODbL are allowed. For each NC
     source, identify the fields it supports and the permissive alternatives
     checked. Verify the terms for the actual material used. -->

## Remaining work

<!-- Unresolved research, representation limits or review questions belong
     here. Maintainers own import and live-release acceptance; contributors
     are not expected to access private systems. -->
