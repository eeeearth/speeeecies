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


# PR #118 review addendum

Prepared on `codex/pr118-albuquerque-fix-20261010` from current `origin/main`
`fdd777ed1ccb82dbc857210adf432e7d6da96dfc`, reconciled from PR head
`1d081311765e2f7f7a30a7d6064ea72852d8079c`. Issue #89 had earlier claims
with expired ETAs; no duplicate claim was posted. Publication remains on hold.

The locale uses the public Nob Hill centroid (Wikidata Q7045560) at 35.08,
-106.60. USGS EPQS at that point returns 1590.43 m, rounded to 1590 m. USGS
SIR 2020-5095 supports BSk for Albuquerque's lower-elevation west side. The
flora catalog retains eight drawable taxa, maps the models to regional plants,
removes the nonlocal saguaro, and records the schema's CC BY-SA license. Honey
mesquite local native status stays Unknown.

The locale has 11 species because `Sceloporus cowlesi` was omitted: the PR's
central New Mexico study is a Society for the Study of Amphibians and Reptiles
paper, not public domain, and the other supplied sources did not establish a
permissive basis for the traits. The 11 retained US-NM activity curves use
GBIF Tier A records only, each above the 300-record minimum. Nine existing
main records receive only the US-NM curve and its source/provenance changes;
all other species fields and regional curves are covered by a regression test.

The two new records use species-local programs. Lesser goldfinch nesting is
explicitly gated April-September from broad species-level evidence; it is not
New Mexico-specific. Cooper's hawk uses a conservative perch/flight/prey FSM;
the current actions cannot model aerial pursuit. ADW is retained as a last-resort
CC BY-NC-SA source for some traits and behavior, which validator reports as a
warning. A year-round phase placeholder remains because the schema requires a
phase; its note says occurrence does not establish territory timing.

Checks: locale validation has no errors and warns that 11 is below the 12-species
richness target. All-locale validation completed without errors; repository
self-check scanned 593 files with zero findings. Four focused regression tests
passed. Browser smoke rendered all 12 poses declared by the two new records.
These rendering checks confirm preview loads and pose selection, not visual
biological accuracy.
