<!-- title: Locale: A Burns ranch lot (or-highdesert) -->
**A Burns ranch lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/or-highdesert/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `or-highdesert` |
| `name` | A Burns ranch lot |
| `country` | `US` |
| `activity_region` | `US-OR` (Oregon) |
| `public_lat`, `public_lon` | 43.59, -119.05: the public city centroid from Wikidata [Q6178257](https://www.wikidata.org/wiki/Q6178257) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Los_Angeles` |
| `koppen` | `BSk`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Burns,_Oregon) (CC BY-SA); confirm |
| `elevation_m` | 1264 m, from Wikidata [Q6178257](https://www.wikidata.org/wiki/Q6178257) `P2044` (CC0) |
| `plot_template` | `rural-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10](https://www.inaturalist.org/places/10)
- iNaturalist place for Harney County, for species lists: [1849](https://www.inaturalist.org/places/1849)
- GBIF GADM gid for the activity region: [`USA.38_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.38_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Burns,_Oregon) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-OR --inat-place-id 10 --gbif-gadm-gid USA.38_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Antigone canadensis* | Sandhill Crane | no | [2474953](https://www.gbif.org/species/2474953) | [508048](https://www.inaturalist.org/taxa/508048) | GBIF files it as a synonym of Grus canadensis |
| *Buteo jamaicensis* | Red-tailed Hawk | no | [2480542](https://www.gbif.org/species/2480542) | [5212](https://www.inaturalist.org/taxa/5212) |  |
| *Bubo virginianus* | Great Horned Owl | no | [5959118](https://www.gbif.org/species/5959118) | [20044](https://www.inaturalist.org/taxa/20044) |  |
| *Pica hudsonia* | Black-billed Magpie | no | [5229487](https://www.gbif.org/species/5229487) | [143853](https://www.inaturalist.org/taxa/143853) |  |
| *Sialia currucoides* | Mountain Bluebird | no | [2490935](https://www.gbif.org/species/2490935) | [12936](https://www.inaturalist.org/taxa/12936) |  |
| *Sturnella neglecta* | Western Meadowlark | no | [9596413](https://www.gbif.org/species/9596413) | [9535](https://www.inaturalist.org/taxa/9535) |  |
| *Tyrannus verticalis* | Western Kingbird | no | [5229675](https://www.gbif.org/species/5229675) | [16791](https://www.inaturalist.org/taxa/16791) |  |
| *Odocoileus hemionus* | Mule Deer | no | [2440974](https://www.gbif.org/species/2440974) | [42220](https://www.inaturalist.org/taxa/42220) |  |
| *Urocitellus beldingi* | Belding's Ground Squirrel | no | [8428945](https://www.gbif.org/species/8428945) | [179995](https://www.inaturalist.org/taxa/179995) |  |
| *Lepus californicus* | Black-tailed Jackrabbit | no | [2436801](https://www.gbif.org/species/2436801) | [43130](https://www.inaturalist.org/taxa/43130) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Pituophis catenifer* | Gopher Snake | no | [2453826](https://www.gbif.org/species/2453826) | [29044](https://www.inaturalist.org/taxa/29044) |  |

### Notes

- Sagebrush steppe at the edge of the Harney Basin wetlands; many county records come from Malheur National Wildlife Refuge, so prefer animals a ranch yard sees.
- Bat records are sparse here (2 research-grade big brown bat observations in the county).

### Plants

Ship `locales/or-highdesert/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/or-highdesert/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-OR`
- [ ] `locales/or-highdesert/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale or-highdesert --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Burns ranch lot (or-highdesert)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
