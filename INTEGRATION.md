# PR #93 review addendum

The Guttural toad source says males call throughout the year, with October and
November as the main breeding period. The record scopes its breeding phase to
South Africa (`ZA`) and uses those months for its croak season. The shared
`fsm-anuran-nocturnal-v1` program gates calling with one global month pair, so
`call_m1` and `call_m2` are now 10 and 11. The format cannot express a separate
schedule for each region; this setting represents the documented ZA main
breeding window wherever the shared program runs. Rain-driven and regional
variation remains outside the current model.

Suggested PR-body update:

> The shared anuran FSM now gates calls in October and November, matching the
> record's cited main breeding period and croak season. The source says calling
> can occur year-round; the FSM's single global month pair represents the
> record's ZA main breeding window because this format cannot encode regional
> call schedules.

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
- The opossum length is a midpoint calculation from the sex-specific head-body ranges and tail range in [Didelphis albiventris](https://es.wikipedia.org/wiki/Didelphis_albiventris): males 45–70 cm, females 41–60 cm, tail 40–65 cm. The female lower bound and male upper bound produce the same derived total-length midpoint, 1.08 m. Its unsupported egg stage, calls, shoulder height, wingspan, and local breeding dates have been removed.
- The kiskadee lifespan value is the USGS Bird Banding Laboratory record of 6 years 11 months (83 months), converted to years. It is documented as maximum longevity, not average or typical lifespan, and is licensed US-Gov-PD. The schema's `lifespan_y` description calls for typical lifespan, so this record-type mismatch remains explicit in provenance.
- [Animal Diversity Web's use conditions](https://animaldiversity.org/about/use_conditions/) state that its text is CC BY-NC-SA 3.0. Its species page remains the source for the opossum wild-lifespan input and carries NC-SA attribution.
- The opossum iNaturalist query includes NC-SA observations and is therefore recorded as CC BY-NC-SA 4.0. Query URLs retain the accepted license filters. EltonTraits remains CC0 as specified by its item metadata.
- The local plant identification is supported by Argentina's [San Isidro algarrobo record](https://www.argentina.gob.ar/capital-humano/cultura/monumentos/algarrobo-en-las-barrancas-de-san-isidro), which identifies a `Prosopis alba` specimen in Buenos Aires and describes it as typical of native talar woodland. Argentina.gob.ar's [terms](https://www.argentina.gob.ar/terminos-y-condiciones) license portal content CC BY 4.0 unless stated otherwise. The drawable `Prosopis glandulosa` remains only a visual stand-in for `Prosopis alba`.

## Remaining limitations

- Opossum (`235` iNaturalist / `230` GBIF) and rat (`40` / `43`) `AR-C` observations fall below the usual 300-observation threshold. Their source records indicate low counts and the curves remain provisional. No better openly licensed regional source was found in this repair.
- The schema requires a seasonal phase. Kiskadee and opossum carry full-year placeholders with explicit notes that no Buenos Aires breeding months are asserted; their behavior programs do not schedule nesting from those placeholders.
- Mockingbird and pigeon lifespan fields remain low-confidence authored placeholders. A sufficiently supported value was not found, so these fields are not represented as measured local lifespans.
- The kiskadee longevity source is a maximum-record source used in a schema field described as typical lifespan; keep that distinction visible in any publication summary.

## Validation and preview

- `uv run tools/validate.py --locale buenosaires-ar --report`: zero errors; warnings identify low-count curves, NC-SA sources, and the omitted opossum shoulder height.
- `uv run tools/validate.py --self-check`: 597 files scanned, zero findings.
- `uv run --with pytest --with jsonschema pytest -p no:cacheprovider -q tools/tests/test_buenosaires_pr161_review.py tools/tests/test_locale.py`: 48 passed after adding regressions for the lifespan record type, opossum range transcription, and flora provenance.
- The site build succeeded. All 19 declared poses rendered in browser preview without JavaScript page errors. These screenshots are rendering smoke checks, not biological accuracy assessments.

## Publication status

Prepared for coordinator review only. PR publication remains on hold while the protected PR #131 release transaction is pending. Do not push or merge from this branch.
