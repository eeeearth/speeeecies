# Status: species/callithrix-jacchus (issue #25)

- 2026-09-30: Claimed issue #25 (comment with ETA 2026-10-01). Copied sciurus-carolinensis template. Starting research.
- 2026-09-30: Researched (Wikipedia, Wikidata, GBIF, ITIS, NCBI, EltonTraits, PanTHERIA). Wrote species.json + bespoke behavior.json (fsm-arboreal-forager-v1: forage -> social_groom -> sentinel -> rest). Fetched BR activity curve (1468 obs).
- 2026-09-30: Validated: 0 errors, 1 warning (MissingShoulderHeight, same as all quadruped records). Self-check clean, 187 pytest pass, attribution diff clean. Previewed all poses (idle/walk/rest + 3/4 + front angles) in headless Chrome; fixed tail carriage (was sticking straight up, now hangs naturally). No clipping found.
- 2026-09-30: Committed and pushed. Opened PR #104: https://github.com/jt55401/speeeecies/pull/104
- 2026-09-30: CI green — `validate` check SUCCESS (28s). PR #104 is OPEN, MERGEABLE, mergeState CLEAN.

## Final report

- PR: https://github.com/jt55401/speeeecies/pull/104
- CI: green (validate: SUCCESS)
- Validator: 0 errors, 1 warning (MissingShoulderHeight — same warning every quadruped record carries; no sourced shoulder height available, field omitted rather than invented)
- Provenance: 39/39 datums covered, cleanliness 73
- Behaviour: took the "honest" option from the recipe — bespoke `fsm-arboreal-forager-v1` (forage -> social_groom -> sentinel -> rest) with a conspecifics predicate on the social_groom transition; diurnal rest params -90/-6. The issue asked for a new arboreal forager program and the shared ground-forager program models a solitary ground-dweller.
- Diet: coordinator's recipe split (fruit 0.4 / invertebrate 0.3 / browse 0.2 / nectar 0.1), exudates mapped to browse, marked derived with the EltonTraits/Wikipedia reconciliation in the provenance note.
- Activity: BR curve fetched with fetch_activity.py (iNaturalist 415 + GBIF 1053 observations).
- Preview: every declared pose checked (idle, walk, rest) plus 3/4 and front orbits; tail carriage corrected after rendering; no clipping or misplaced colours.
- Not done: visual_check.py (BioCLIP) not run — advisory only, and it would need a ~1 GB model download on CPU; the previewer check above was done instead. No species-local issues otherwise.

I'm done boss

# Status: locale co-coloradosprings (issue #86)

- 2026-09-30: Claimed issue #86 (comment, ETA 2026-10-03). Read AGENTS.md "Contribute a locale", docs/locale-richness.md, the schemas, and the london-uk worked example. Confirmed none of the 12 candidate species exist under `species/` (21 records, all European/oceanic).
- 2026-09-30: Verified GBIF usage keys + iNaturalist taxon ids for 12 chosen species against the live APIs, and pulled ITIS TSN / Wikidata Q / NCBI id / authorship / order from GBIF, Wikidata and ITIS. Chose: Pica hudsonia, Turdus migratorius, Haemorhous mexicanus, Colaptes auratus, Junco hyemalis, Sciurus niger, Procyon lotor, Sylvilagus audubonii, Aphelocoma woodhouseii, Bubo virginianus, Sceloporus consobrinus, Thamnophis elegans (Big Brown Bat dropped: no bat body plan or behaviour program in v0.1; Great Horned Owl covers the nocturnal slot with `biped_winged` + bt-perching-songbird-v1).
- 2026-09-30: Created species-request issues #120-#131 for the 12 and claimed each with an ETA.
- 2026-09-30: Wrote and validated 5 of the 12 species records, each 0 errors / 0 warnings: pica-hudsonia, turdus-migratorius, haemorhous-mexicanus, colaptes-auratus, junco-hyemalis. All with US-CO activity curves via fetch_activity.py (inat place 34 + GBIF GADM USA.6_1, tier A on both). Recorded honest gaps where no CC0/CC-BY lifespan figure exists (haemorhous, colaptes, junco): lifespan_y is marked derived with the close-relative anchor and the assumption stated in the provenance note.
- 2026-09-30: 8 of 12 species records written and validated — the locale minimum is now met. Added the mammals: sciurus-niger (note: Wikipedia puts Colorado inside the fox squirrel's NATIVE range, contradicting the issue's "introduced in Colorado" note; followed the source), procyon-lotor (empty vocalizations + an honest note: the Wikipedia article contains no call description; Colorado raccoon records are thin so fetch_activity.py fell to tier C, giving two CC-BY-NC activity sources to justify), sylvilagus-audubonii (also empty vocalizations; sourced elevation ceiling 1830 m sits just below the Colorado Springs centroid's 1839 m, recorded honestly).
- 2026-09-30: Checkpoint commit of the 8 species before continuing.
