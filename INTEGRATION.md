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

## PR #160 Vancouver integration note

The locale repair starts from PR head `0eddd094d983433211b1aabcea5f67236e3a1ee0`
and reconciles against current `origin/main` `fdd777ed1ccb82dbc857210adf432e7d6da96dfc`.
The existing nine main species records and their non-`CA-BC` curves were
compared after removing only the new `CA-BC` activity rows and their two source
entries; all nine matched current main exactly.

The locale adds `CA-BC` activity rows for those nine species and includes three
new records: Anna's hummingbird, Douglas's squirrel, and Pacific chorus frog.
EltonTraits' inspected CC0 rows report Anna's hummingbird diet as 90% nectar and
10% invertebrates, and Douglas's squirrel diet as 20% vertebrate endotherms,
10% unknown vertebrates, 20% fruit, 10% nectar, 20% seed, and 20% other plant
material. The squirrel's `PlantO` category is mapped to `browse` because the
species schema has no `plant-other` diet category. The Figshare item API
advertises CC0 for EltonTraits and CC BY 4.0 for AmphiBIO. The frog's March to
May call window follows the peak-season survey period reported for Saanich,
British Columbia, by Green, Govindarajulu, and Higgs (2021), licensed CC BY 4.0.

The locale's rounded public centroid is 49.26, -123.11. Wikidata supplies the
coordinates; the OpenTopoData SRTM 30 m query at that point reports 47 m. The
source record identifies NASA/USGS SRTM data as public domain.

All new BC activity queries filter iNaturalist to CC0/CC BY and GBIF to CC0/CC
BY; each has at least 300 records. The nine existing species retain their other
main-branch curves, including any pre-existing non-commercial source warnings
on those unrelated regions. No new BC curve uses a non-commercial source.

Behavior and season limits: Anna's hummingbird feeds with the supported flight
gait because schema v0.1 has no separate hover pose; its local behavior omits
the generic ground-hop and nest-month branches. The Douglas's squirrel uses the
shared ground-forager program as a limited walk/forage/rest/flee approximation;
it does not simulate climbing or cone caching. The frog uses the shared
nocturnal anuran FSM with calls limited to March through May. That is the local
study's peak calling survey window, not a claim that calling cannot occur
outside it. No frog hibernation threshold is asserted.

Validation includes the Vancouver locale report, repository self-check, focused
regression tests for the corrected diet and resolved frog month gate, and
headless preview rendering smoke checks for all poses declared by the three
new species. The preview checks confirm rendering; they are not a biological
identification or pose-quality assessment. The branch is prepared locally and
remains under the publication hold.
