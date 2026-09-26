## What this adds

<!-- species: <common name> (<Scientific name>)
     or locale: <place> (<id>) -->

Closes #

## Validate report

<!-- Paste the output of:
uv run tools/validate.py species/<slug> --write-attribution --report
and, for a locale:
uv run tools/validate.py --locale <id> --report
uv run tools/validate.py --self-check
It must show no errors. -->

## Checklist

### Species

- [ ] Closes the linked species-request issue
- [ ] Validate report pasted above, with no errors
- [ ] `species/<slug>/ATTRIBUTION.md` regenerated (`--write-attribution`) and committed
- [ ] Activity curves generated with `tools/fetch_activity.py` for every suggested region
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

<!-- Justify each CC BY-SA, ODbL, or NC source here: why nothing better was available. -->
