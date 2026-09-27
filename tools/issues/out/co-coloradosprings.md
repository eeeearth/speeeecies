<!-- title: Locale: A Colorado Springs street (co-coloradosprings) -->
**A Colorado Springs street**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/co-coloradosprings/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `co-coloradosprings` |
| `name` | A Colorado Springs street |
| `country` | `US` |
| `activity_region` | `US-CO` (Colorado) |
| `public_lat`, `public_lon` | 38.86, -104.79: the public city centroid from Wikidata [Q49258](https://www.wikidata.org/wiki/Q49258) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Denver` |
| `koppen` | `BSk`, from the Beck et al. 2018 Köppen-Geiger map (CC BY 4.0, https://www.gloh2o.org/koppen/) for Colorado Springs; [Wikipedia](https://en.wikipedia.org/wiki/Colorado_Springs,_Colorado) gives Dwa/Cwa; confirm |
| `elevation_m` | 1839 m, from Wikidata [Q49258](https://www.wikidata.org/wiki/Q49258) `P2044` (CC0) |
| `plot_template` | `street-block` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [34](https://www.inaturalist.org/places/34)
- iNaturalist place for El Paso County, for species lists: [2894](https://www.inaturalist.org/places/2894)
- GBIF GADM gid for the activity region: [`USA.6_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.6_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the source named in the table above or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-CO --inat-place-id 34 --gbif-gadm-gid USA.6_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Pica hudsonia* | Black-billed Magpie | no | [5229487](https://www.gbif.org/species/5229487) | [143853](https://www.inaturalist.org/taxa/143853) |  |
| *Aphelocoma woodhouseii* | Woodhouse's Scrub-Jay | no | [5844900](https://www.gbif.org/species/5844900) | [506117](https://www.inaturalist.org/taxa/506117) |  |
| *Haemorhous mexicanus* | House Finch | no | [8323485](https://www.gbif.org/species/8323485) | [199840](https://www.inaturalist.org/taxa/199840) |  |
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Colaptes auratus* | Northern Flicker | no | [2478259](https://www.gbif.org/species/2478259) | [18236](https://www.inaturalist.org/taxa/18236) |  |
| *Junco hyemalis* | Dark-eyed Junco | no | [9362842](https://www.gbif.org/species/9362842) | [10094](https://www.inaturalist.org/taxa/10094) |  |
| *Sciurus niger* | Eastern Fox Squirrel | no | [5219683](https://www.gbif.org/species/5219683) | [46020](https://www.inaturalist.org/taxa/46020) |  |
| *Procyon lotor* | Common Raccoon | no | [5218786](https://www.gbif.org/species/5218786) | [41663](https://www.inaturalist.org/taxa/41663) |  |
| *Sylvilagus audubonii* | Desert Cottontail | no | [2436910](https://www.gbif.org/species/2436910) | [43115](https://www.inaturalist.org/taxa/43115) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Sceloporus consobrinus* | Prairie Lizard | no | [2451277](https://www.gbif.org/species/2451277) | [146413](https://www.inaturalist.org/taxa/146413) |  |
| *Thamnophis elegans* | Western Terrestrial Garter Snake | no | [2457545](https://www.gbif.org/species/2457545) | [28398](https://www.inaturalist.org/taxa/28398) |  |

### Notes

- Use `BSk`: the maintainers' import has no template yet for the dry-winter classes (`Dwa`, `Cwa`) Wikipedia gives.
- Eastern fox squirrels are introduced in Colorado.

### Plants

Ship `locales/co-coloradosprings/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/co-coloradosprings/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-CO`
- [ ] `locales/co-coloradosprings/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale co-coloradosprings --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Colorado Springs street (co-coloradosprings)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
