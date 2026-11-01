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

## PR #101 repair review, 2026-10-10

**Refs:** repair base `origin/main` at `fdd777ed1ccb82dbc857210adf432e7d6da96dfc`;
old PR #101 head `8389d82e` (`jt55401/species-33-tiliqua-scincoides`);
repair branch `codex/pr101-blue-tongue-fix-20261010`. The old head predates
main's species record. Its tree diff removes unrelated main content, so it was
reviewed as a candidate record and behavior, not merged wholesale.

### Findings and decisions

- **AU activity:** The old PR's national AU query uses the current Tier A
  filters: iNaturalist `license=cc0,cc-by`, place `6744`, taxon `37456`, and
  GBIF `license=CC0_1_0&license=CC_BY_4_0`, country `AU`, taxon `2462503`.
  Both exceed the 300-observation minimum and the source records correctly
  credit their mixed CC0/CC BY inputs as CC BY 4.0. The old stored totals
  (1,032 and 53,022; 54,054 combined) have changed. A fresh run on 2026-10-10
  returned 1,037 iNaturalist and 53,072 GBIF observations, producing
  `[0.87, 0.62, 0.45, 0.39, 0.23, 0.16, 0.18, 0.43, 0.88, 1.0, 0.81, 0.89]`
  by `mean(inat_raw, gbif_raw)`. This AU row and its two source records were
  added. The pre-existing AU-NSW row, source records, and Sydney locale fit
  were retained.
- **Basking FSM:** The old `fsm-basking-lizard-v1` checks daylight only when
  leaving `shelter`. Its initial state is `bask`; `bask`, `forage`, and `wander`
  retreat on temperature alone. At a warm night between 25 and 35 C they can
  continue outside, and `touched`/`offer` return directly to `bask` after the
  interaction ends. The predicate is ambient temperature, while its cited
  30–35 C value describes *body* temperature. Static schema validity cannot
  establish the intended runtime behavior. The species-local program was not
  carried over; main's `fsm-ground-forager-v1` reference and its diurnal rest
  window remain. That shared program does not explicitly model basking.
- **Lifespan:** `species.schema.json` defines `lifespan_y` as a typical wild
  lifespan and requires it. The old PR itself says its 20-year value comes
  from [captive longevity](https://en.wikipedia.org/wiki/Eastern_blue-tongued_skink#Lifespan),
  with [the French article](https://fr.wikipedia.org/wiki/Tiliqua_scincoides)
  also specifying captivity. The [Koenig et al. 2001 abstract](https://researchers.mq.edu.au/en/publications/the-ecology-of-an-australian-reptile-icon-how-do-blue-tongued-liz/)
  likewise labels its 30-plus years as captive. The main record's 20-year
  value had no wild-specific support. The [Victorian government species
  profile](https://www.wildlife.vic.gov.au/__data/assets/pdf_file/0026/671264/Part-B-Reptiles-Amphibians-Chapter1.pdf)
  gives 12–15 years without specifying conditions. Its midpoint, 13.5, is
  used as a **low-confidence derived proxy**, with that limitation in the
  provenance note. The text is government-authored; [DEECA's copyright
  terms](https://www.deeca.vic.gov.au/copyright) identify CC BY 4.0 for its
  material, excluding third-party content such as the profile photograph.
  No measured typical wild lifespan was found.
- **Existing source link:** Main's `Common_bluetongue` Wikipedia URL returned
  HTTP 404 on 2026-10-10. The live [Tiliqua scincoides article](https://en.wikipedia.org/wiki/Tiliqua_scincoides)
  returned HTTP 200 and states CC BY-SA 4.0. Its source URL, title, access
  date, and credit were updated without removing its existing coverage.

### Verification

- `UV_CACHE_DIR=$HOME/tmp/speeeecies-pr101-uv-cache uv run tools/fetch_activity.py tiliqua-scincoides --region AU --inat-place-id 6744 --cache-dir $HOME/tmp/speeeecies-pr101-activity-cache --write`:
  exit 0; both providers Tier A, 54,109 total observations.
- `UV_CACHE_DIR=$HOME/tmp/speeeecies-pr101-uv-cache uv run tools/validate.py species/tiliqua-scincoides --write-attribution --report`:
  exit 0; 0 errors, 0 warnings, 37/37 provenance, cleanliness 71.
- `UV_CACHE_DIR=$HOME/tmp/speeeecies-pr101-uv-cache uv run tools/validate.py --self-check`:
  exit 0; 585 files scanned, 0 findings.
- `UV_CACHE_DIR=$HOME/tmp/speeeecies-pr101-uv-cache uv run --with pytest --with jsonschema pytest -q tools/tests/test_tiliqua_scincoides_record.py tools/tests/test_fetch_activity.py tools/tests/test_validate.py`:
  exit 0; 99 tests passed. An earlier broader invocation using only
  `--with pytest` had 34 passes and 65 setup errors because `jsonschema`
  was absent; adding that declared validator dependency resolved the errors.
  The new tests read worktree files directly and require no Git history in
  hosted CI.
- `UV_CACHE_DIR=$HOME/tmp/speeeecies-pr101-uv-cache uv run tools/validate.py --locale sydney-au --report`:
  exit 0; this species has activity, behavior, and a walk pose with 0 errors.
  The locale retains its unrelated `LocaleFewSpecies` warning at 11 species.
- A direct comparison of the current JSON against `git show origin/main:species/tiliqua-scincoides/species.json`
  confirmed every pre-existing field other than the justified lifespan and
  source metadata is unchanged, with the AU-NSW row exactly preserved. This
  was a local review check; the committed tests do not use Git history.
- `git diff --check`: exit 0.

No push, merge, private release import, other species, or locale was changed.
Public PR #101 remains gated on private PR #131's natural-scene release check.
