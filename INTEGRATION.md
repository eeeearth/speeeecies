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

# PR #151 Burns integration note

Base `origin/main`: `fdd777ed1ccb82dbc857210adf432e7d6da96dfc`. Reconciled PR
head: `03486c3efb38b65700ff50aacae833cf80e23aaa`. The issue #69 claim comments
were reviewed; both list an October 2 ETA and are expired. No duplicate claim
was posted.

The locale uses the public Burns centroid from Wikidata Q6178257, rounded to
43.59, -119.05. Its 1,264 m elevation follows the Wikidata elevation statement;
the same entity also lists a GNIS value of 1,266 m. Oregon's sagebrush habitat
description supports the high-desert setting. The flora catalog has eight
drawable woody taxa and two evergreens. `Calocedrus decurrens` was removed
because its documented Oregon range does not support Burns. Oregon ash is
retained only as a possible planted shade-tree stand-in, with local status
marked unknown. The catalog cannot represent the site's sagebrush and grass
community with the current drawable plant set.

All 12 US-OR curves were regenerated using GBIF occurrence counts, the
repository's `fetch_activity.py`, the GADM `USA.38_1` region, and a 300-record
minimum. Ten curves met the threshold using CC0/CC BY records (Tier A). The
jackrabbit (421 records) and Columbia spotted frog (384) only met it with
CC-BY-NC records (Tier C), retained as last-resort sources and flagged by the
validator. No US-OR iNaturalist data was mixed into these queries. Existing
curves remain on the three records already present on main: Haemorhous
mexicanus, Pica hudsonia, and Spinus tristis. The latter records were changed
only by the US-OR curve, its source/provenance, and regenerated attribution.

The Columbia spotted frog diet now assigns no fish fraction; its 95% insect
and 5% browse split is an explicitly low-confidence authored model, while the
USFS report supports a diet dominated by insects and other arthropods. The
report describes northeastern Oregon breeding from March at lower sites into
June at higher sites. The local frog program removes the nocturnal-only
daylight gate, keeps March-June calling, and labels its temperature thresholds
as model settings. Belding's ground-squirrel total length includes the tail.
Unsupported thrasher wingspan was removed. Several lifespans and diet splits
remain low-confidence modeled values; their notes distinguish these from
source-reported maxima or qualitative diets.

Checks: locale and all-locale validation, repository self-check, focused Burns
regression tests, and browser render smoke for all five frog poses plus bird
and squirrel poses passed. These pose checks establish that declared poses
render; they are not a biological visual-accuracy assessment. Publication is
on hold; no push, merge, or deployment was performed.
