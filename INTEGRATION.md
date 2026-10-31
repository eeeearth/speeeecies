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

# PR #158 Accra repair integration note

Prepared 2026-10-10 in a separate worktree from `origin/main` `fdd777ed1ccb82dbc857210adf432e7d6da96dfc`, using old PR #158 head `7d098c75af6a072a27f586387c6a356529d2779c` as the source of candidate Accra files. The old PR branch had unrelated deletions and stale copies of main records, so only the Accra locale/catalog, seven retained new species records, and three GH-AA additions were carried forward. The PR158 claim on issue #59 already exists; no second claim was posted. Vervet remains absent from the locale, so this repair makes no #16 closure claim.

## Scope and data decisions

- Current main's laughing dove, rock dove, and rose-ringed parakeet records remain unchanged except for appended GH-AA activity rows, GBIF source entries, and regenerated attribution. The current main vervet record is untouched and is not listed in Accra.
- The seven retained additions are village weaver, pied crow, Senegal coucal, African grey hornbill, yellow-billed shrike, western plantain-eater, and western cattle egret. The locale now lists ten species total. This is above the validator minimum of eight but below its target of twelve; no replacements were guessed.
- Straw-coloured fruit bat is omitted because its Accra activity counts (37 iNaturalist, 24 GBIF) are below the 300-record minimum, its existing source mixed non-commercial licenses under an inaccurate `CC-BY-NC-4.0` label, and no supported flight/roost program was available in the shared behaviors. African common toad is omitted because its counts (7 iNaturalist, 118 GBIF) are also below the minimum. Neither unsupported curve nor the bat's incorrect license metadata was copied.
- The six walk-only songbird programs use species-local copies with `walk` forage, no shared behavior edits, and no fixed nest-building month gate. Village weaver retains its declared hop gait. The cattle egret local FSM walks while foraging, uses its declared powered flight to escape threats, and rests when energy is low or the sun is below the authored -6 degree threshold. Threat escape has higher priority than night rest. It has no gallop gait. Unsupported Ghana breeding-month lists and juvenile durations were removed. The schema accepts an empty seasonal phase list when no local month window is supported.
- AVONET wing-chord times three estimates were removed where a source-backed wingspan was not found. The pied crow's cited maximum and cattle egret's 88–96 cm source range remain with upper-bound/midpoint notes. Required lifespan values are explicitly low-confidence simulation estimates, not longevity records.
- The EltonTraits rows were checked directly in the CC0 Figshare item `10.6084/m9.figshare.3559887.v1`. The retained records use the published fractions for village weaver, pied crow, Senegal coucal, yellow-billed shrike, western plantain-eater, and cattle egret. Where the kit lacks a `PlantOther` diet category, village weaver's 10% is combined with seed; hornbill diet shares remain a clearly labeled low-confidence authored split because that taxon is absent from the dataset. AVONET item `10.6084/m9.figshare.16586228` advertises CC BY 4.0 and was used for morphology, not as a source for estimated wingspans.
- GBIF Backbone API responses were checked for all seven accepted names and authorships; the corrections include *Corvinella corvina* (Shaw, 1809), *Crinifer piscator* (Boddaert, 1783), and *Bubulcus ibis* (Linnaeus, 1758).
- The cattle egret record retains the name *Bubulcus ibis* used by its GBIF source. Its cited Spanish Wikipedia source is titled *Ardea ibis* and uses that alternate taxonomic treatment for the same species; accepted-name preference varies by taxonomy.

## Activity evidence

All curves use GBIF Tier A occurrence records filtered to CC0 and CC BY, with at least 300 observations. iNaturalist was skipped because no GH-AA place id was supplied. The fetcher wrote these current counts:

| Species | Region | Records |
|---|---|---:|
| Village weaver | GH-AA | 670 |
| Pied crow | GH-AA | 2,464 |
| Laughing dove | GH-AA | 2,348 |
| Senegal coucal | GH-AA | 1,462 |
| African grey hornbill | GH-AA | 1,635 |
| Yellow-billed shrike | GH-AA | 1,220 |
| Western plantain-eater | GH-AA | 2,001 |
| Western cattle egret | GH-AA | 1,791 |
| Rock dove | GH-AA | 787 |
| Rose-ringed parakeet | GH-AA | 486 |
| Pied crow | KE-30 | 9,384 |

The KE-30 row was fetched from `KEN.30_1` to coordinate with held PR #178. That existing Nairobi worktree was read only and remains untouched. It currently has a different pied-crow behavior program, a different modeled diet, and a KE-30 count of 9,366 from its earlier query. Before the two locale PRs are integrated, use one reconciled pied-crow record and retain both regional curves; this Accra version uses the verified EltonTraits fractions and walk-only feeding behavior.

## Files and checks

Changed paths are `locales/accra-gh/`, `species/{ploceus-cucullatus,corvus-albus,centropus-senegalensis,lophoceros-nasutus,corvinella-corvina,crinifer-piscator,bubulcus-ibis}/`, the three main dove/pigeon/parakeet `species.json` and `ATTRIBUTION.md` files, `schema/v0.1/species.schema.json`, `tools/tests/test_accra_gh_review.py`, and this appended note. The existing PR #93 note above was preserved verbatim.

Focused species validation passes for all seven new records with complete provenance and no license warnings. The three protected main species validate with only their pre-existing NC-source warnings in other regions; no NC source was added for GH-AA. Accra validation reports 0 errors across 11 targets; its ten warnings are the existing non-commercial sources on main records and the locale's ten-species richness warning. All-locale validation reports 0 errors across 221 targets and 285 warnings, including existing repository NC-license, sparse-locale, and model warnings. Repository self-check scanned 608 files with 0 findings. The focused regression file passes all 7 tests. The previewer rendered screenshots for all 57 declared poses across the ten Accra species; contact sheets were visually checked, with no blank canvas or obvious clipping. These are rendering smoke checks, not biological model validation. This remains a local prepared branch under the PR131 publication hold; no remote PR edit, push, merge, or live import was made.
