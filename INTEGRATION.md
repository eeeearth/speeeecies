# PR #161 Buenos Aires integration note

## Branch and scope

- Exact PR head reviewed: `d2e7bb9f19a1ab3d4e2fa485597874398bdc3164`.
- Reconciled with `origin/main` at `fdd777ed1ccb82dbc857210adf432e7d6da96dfc`.
- The locale adds `AR-C` activity to its eight pre-existing species. The regression test compares each existing record with `AR-C` removed against a stored canonical hash, so changes to other regional data fail the test.
- Locale additions: `locales/buenosaires-ar/locale.json` and `flora-catalog.json`. Species additions: `didelphis-albiventris`, `mimus-saturninus`, `patagioenas-picazuro`, and `pitangus-sulphuratus`, each with `species.json` and regenerated `ATTRIBUTION.md`. Kiskadee and mockingbird also have species-local `behavior.json` files. Review coverage is in `tools/tests/test_buenosaires_pr161_review.py`.
- No shared behavior program was changed. Local behavior removes unsupported kiskadee nesting dates, applies the supported September–January mockingbird nest gate, and gives picazuro pigeon walking forage, flight escape, and night rest.
- The drawable `Prosopis glandulosa` flora model is used as a visual stand-in for `Prosopis alba` (algarrobo blanco); the catalog no longer says the North American species is native to Buenos Aires.

## Source and license evidence

- The new bird records cite [great kiskadee](https://en.wikipedia.org/wiki/Great_kiskadee), [chalk-browed mockingbird](https://en.wikipedia.org/wiki/Chalk-browed_mockingbird), and [picazuro pigeon](https://pt.wikipedia.org/wiki/Patagioenas_picazuro) reference pages for descriptive facts and sourced ranges. Derived lengths are documented as midpoint calculations in the records.
- The opossum length is a midpoint calculation from the head-body and tail ranges in [Didelphis albiventris](https://es.wikipedia.org/wiki/Didelphis_albiventris). Its unsupported egg stage, calls, shoulder height, wingspan, and local breeding dates have been removed.
- [Animal Diversity Web's use conditions](https://animaldiversity.org/about/use_conditions/) state that its text is CC BY-NC-SA 3.0. Its species pages are used only for wild-lifespan inputs for kiskadee and opossum; both records carry the NC-SA license and attribution.
- The opossum iNaturalist query includes NC-SA observations and is therefore recorded as CC BY-NC-SA 4.0. Query URLs retain the accepted license filters. EltonTraits remains CC0 as specified by its item metadata.
- The flora stand-in is linked to [Prosopis alba](https://en.wikipedia.org/wiki/Neltuma_alba), which is also known as algarrobo blanco. Its local native-status assignment is an explicit model mapping, not a claim about `Prosopis glandulosa`; review the mapping before publication.

## Remaining limitations

- Opossum (`235` iNaturalist / `230` GBIF) and rat (`40` / `43`) `AR-C` observations fall below the usual 300-observation threshold. Their source records indicate low counts and the curves remain provisional. No better openly licensed regional source was found in this repair.
- The schema requires a seasonal phase. Kiskadee and opossum carry full-year placeholders with explicit notes that no Buenos Aires breeding months are asserted; their behavior programs do not schedule nesting from those placeholders.
- Mockingbird and pigeon lifespan fields remain low-confidence authored placeholders. A sufficiently supported value was not found, so these fields are not represented as measured local lifespans.
- The flora model substitution and Buenos Aires native label for `Prosopis alba` should receive coordinator review before publication.

## Validation and preview

- `uv run tools/validate.py --locale buenosaires-ar --report`: zero errors; warnings identify low-count curves, NC-SA sources, and the omitted opossum shoulder height.
- `uv run tools/validate.py --self-check`: 597 files scanned, zero findings.
- `uv run --with pytest --with jsonschema pytest -p no:cacheprovider -q tools/tests/test_buenosaires_pr161_review.py tools/tests/test_locale.py`: 47 passed.
- The site build succeeded. All 19 declared poses rendered in browser preview without JavaScript page errors. These screenshots are rendering smoke checks, not biological accuracy assessments.

## Publication status

Prepared for coordinator review only. PR publication remains on hold while the protected PR #131 release transaction is pending. Do not push or merge from this branch.
