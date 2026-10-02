# Status: species/callithrix-jacchus (issue #25)

- 2026-09-30: Claimed issue #25 (comment with ETA 2026-10-01). Copied sciurus-carolinensis template. Starting research.
- 2026-09-30: Researched (Wikipedia, Wikidata, GBIF, ITIS, NCBI, EltonTraits, PanTHERIA). Wrote species.json + bespoke behavior.json (fsm-arboreal-forager-v1: forage -> social_groom -> sentinel -> rest). Fetched BR activity curve (1468 obs).
- 2026-09-30: Validated: 0 errors, 1 warning (MissingShoulderHeight, same as all quadruped records). Self-check clean, 187 pytest pass, attribution diff clean. Previewed all poses (idle/walk/rest + 3/4 + front angles) in headless Chrome; fixed tail carriage (was sticking straight up, now hangs naturally). No clipping found.
- 2026-09-30: Committed and pushed. Opened PR #104: https://github.com/eeeearth/speeeecies/pull/104
- 2026-09-30: CI green — `validate` check SUCCESS (28s). PR #104 is OPEN, MERGEABLE, mergeState CLEAN.

## Final report

- PR: https://github.com/eeeearth/speeeecies/pull/104
- CI: green (validate: SUCCESS)
- Validator: 0 errors, 1 warning (MissingShoulderHeight — same warning every quadruped record carries; no sourced shoulder height available, field omitted rather than invented)
- Provenance: 39/39 datums covered, cleanliness 73
- Behaviour: took the "honest" option from the recipe — bespoke `fsm-arboreal-forager-v1` (forage -> social_groom -> sentinel -> rest) with a conspecifics predicate on the social_groom transition; diurnal rest params -90/-6. The issue asked for a new arboreal forager program and the shared ground-forager program models a solitary ground-dweller.
- Diet: coordinator's recipe split (fruit 0.4 / invertebrate 0.3 / browse 0.2 / nectar 0.1), exudates mapped to browse, marked derived with the EltonTraits/Wikipedia reconciliation in the provenance note.
- Activity: BR curve fetched with fetch_activity.py (iNaturalist 415 + GBIF 1053 observations).
- Preview: every declared pose checked (idle, walk, rest) plus 3/4 and front orbits; tail carriage corrected after rendering; no clipping or misplaced colours.
- Not done: visual_check.py (BioCLIP) not run — advisory only, and it would need a ~1 GB model download on CPU; the previewer check above was done instead. No species-local issues otherwise.

I'm done boss
