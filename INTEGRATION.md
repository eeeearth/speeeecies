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

---

# PR #97 Australian magpie integration note

## Heads reviewed

- Integration base: `origin/main` at `fdd777ed1ccb82dbc857210adf432e7d6da96dfc`.
- Earlier contribution reviewed: PR #97 head `017fb54b57f6e2c310fcbeb30656489f286e6a93`.
- This change takes only the refreshed national AU activity row and its two query sources from that contribution. All existing species fields and the AU-NSW activity row remain identical to the integration base.

## National AU curve evidence

Fetched 2026-10-10 with `tools/fetch_activity.py gymnorhina-tibicen --region AU --write`.

- iNaturalist: taxon 8575, Australia place 6744, verifiable observations filtered to CC0/CC BY; tier A, 9,912 observations, above the 300 minimum.
- GBIF: taxon key 2489450, country AU, occurrence records filtered to CC0 1.0 / CC BY 4.0; tier A, 1,950,290 records, above the 300 minimum.
- The fetcher normalizes each source against monthly Aves records to reduce observation-effort seasonality, then averages the two source curves. Combined source count: 1,960,202.
- Stored Jan-Dec curve: `[0.88, 0.91, 0.96, 1.00, 0.91, 0.97, 0.82, 0.81, 0.84, 0.87, 0.87, 0.88]`.

The previous PR snapshot had 9,856 iNaturalist and 1,939,153 GBIF records. Counts have changed since that fetch; this branch records the fresh counts and regenerated attribution. The existing AU-NSW curve and its sources were verified as unchanged JSON values against `origin/main`.

## Source decisions and limits

The existing seasonal record remains unchanged: breeding July-November and the current southern-season behavior parameters (`nest_m1=7`, `nest_m2=11`). The March-May values from PR #97 were copied from a northern-spring behavior default and were not imported. The prior PR's `mdd_id: 61731` was also not imported because it was an unexplained Mammal Diversity Database identifier on a bird. Current-main taxonomy and all other species data remain unchanged.

The AU curve describes the national distribution of eligible observations after class-level effort adjustment. It is not a breeding calendar or a direct population-abundance estimate. Aggregating Australia can hide local seasonal differences; the existing AU-NSW curve remains available for that region. Observation totals and curves may change when the APIs are fetched again.

## Checks

- Species validation and attribution regeneration: 0 errors, 0 warnings; provenance 38/38.
- All-locale validation: 33 locales, 0 failures.
- Repository self-check: 584 files, 0 findings.
- Focused preservation and curve checks: AU-NSW and all pre-existing non-activity fields match `origin/main`; new query metadata and A-tier counts pass; stored curve recomputes from the cached species and class-baseline API responses.
- Behavior and poses were unchanged, so no pose smoke was needed.
