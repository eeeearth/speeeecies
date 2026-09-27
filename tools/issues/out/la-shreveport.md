<!-- title: Locale: A Shreveport lot (la-shreveport) -->
**A Shreveport lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/la-shreveport/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `la-shreveport` |
| `name` | A Shreveport lot |
| `country` | `US` |
| `activity_region` | `US-LA` (Louisiana) |
| `public_lat`, `public_lon` | 32.51, -93.76: the public city centroid from Wikidata [Q80517](https://www.wikidata.org/wiki/Q80517) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Chicago` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Shreveport,_Louisiana) (CC BY-SA); confirm |
| `elevation_m` | 46 m, from Wikidata [Q80517](https://www.wikidata.org/wiki/Q80517) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [27](https://www.inaturalist.org/places/27)
- iNaturalist place for Caddo Parish, for species lists: [1450](https://www.inaturalist.org/places/1450)
- GBIF GADM gid for the activity region: [`USA.19_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.19_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Shreveport,_Louisiana) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-LA --inat-place-id 27 --gbif-gadm-gid USA.19_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`sciurus-carolinensis`); they still need a curve for `US-LA`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Mimus polyglottos* | Northern Mockingbird | no | [5231677](https://www.gbif.org/species/5231677) | [14886](https://www.inaturalist.org/taxa/14886) |  |
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Sialia sialis* | Eastern Bluebird | no | [2490941](https://www.gbif.org/species/2490941) | [12942](https://www.inaturalist.org/taxa/12942) |  |
| *Ictinia mississippiensis* | Mississippi Kite | no | [2480719](https://www.gbif.org/species/2480719) | [5416](https://www.inaturalist.org/taxa/5416) |  |
| *Thryothorus ludovicianus* | Carolina Wren | no | [2493801](https://www.gbif.org/species/2493801) | [7513](https://www.inaturalist.org/taxa/7513) |  |
| *Melanerpes carolinus* | Red-bellied Woodpecker | no | [2478106](https://www.gbif.org/species/2478106) | [18205](https://www.inaturalist.org/taxa/18205) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Didelphis virginiana* | Virginia Opossum | no | [2439923](https://www.gbif.org/species/2439923) | [42652](https://www.inaturalist.org/taxa/42652) |  |
| *Dasypus mexicanus* | Mexican Long-nosed Armadillo | no | [2440779](https://www.gbif.org/species/2440779) | [1647419](https://www.inaturalist.org/taxa/1647419) | GBIF uses Dasypus novemcinctus, which iNaturalist splits |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Anolis carolinensis* | Green Anole | no | [2466939](https://www.gbif.org/species/2466939) | [36514](https://www.inaturalist.org/taxa/36514) |  |
| *Dryophytes cinereus* | Green Treefrog | no | [10810025](https://www.gbif.org/species/10810025) | [1668858](https://www.inaturalist.org/taxa/1668858) |  |

### Notes

- Bat records are very sparse here (one research-grade observation in the parish); if `fetch_activity.py` widens to the country (US), say so in the PR.

### Plants

Ship `locales/la-shreveport/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/la-shreveport/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-LA`
- [ ] `locales/la-shreveport/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale la-shreveport --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Shreveport lot (la-shreveport)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
