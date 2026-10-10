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

# PR #109 activity repair

The current `main` record and its `IN-KA` curve are preserved byte-for-byte at
field level. PR #109 head `32758cac411b8521c6b33c0a777f06835e1bb114` was used
only as a source of candidate regional data. Its `IN` curve had zero
observations and an estimated method, and it claimed a `TH` curve that was
absent; neither was added. The conflicting NCBI identifier in that PR was
also omitted in favor of the verified identifier already on `main`.

The added `LK` and `MY` curves use current GBIF occurrence-search facets for
GBIF usage key `2422538`, filtered to CC0 1.0 and CC BY 4.0. `LK` has 486
records and `MY` has 396, both above the 300-record threshold. Each curve uses
GBIF tier A alone and the ectotherm raw-count normalization already used by
`tools/fetch_activity.py`. Mixed-license iNaturalist curves from the old PR
were excluded. These are observation-seasonality curves, not abundance or
breeding calendars. The resulting eight source entries have licenses: four
CC BY 4.0, one CC0 1.0, one CC BY-SA 4.0, and two CC BY-NC 4.0. The two NC
entries are the pre-existing `IN-KA` sources retained with the main curve;
the validator reports those two warnings. All 35 provenance entries resolve.
Existing behavior, breeding dates, identifiers, range, and the `IN-KA`
activity row remain unchanged.
