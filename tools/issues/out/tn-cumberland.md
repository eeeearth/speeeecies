<!-- title: Locale: A Sewanee woods lot (tn-cumberland) -->
**A Sewanee woods lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/tn-cumberland/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `tn-cumberland` |
| `name` | A Sewanee woods lot |
| `country` | `US` |
| `activity_region` | `US-TN` (Tennessee) |
| `public_lat`, `public_lon` | 35.20, -85.92: the public city centroid from Wikidata [Q1987614](https://www.wikidata.org/wiki/Q1987614) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Chicago` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Sewanee,_Tennessee) (CC BY-SA); confirm |
| `elevation_m` | 588 m, from Wikidata [Q1987614](https://www.wikidata.org/wiki/Q1987614) `P2044` (CC0) |
| `plot_template` | `rural-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [45](https://www.inaturalist.org/places/45)
- iNaturalist place for Franklin County, for species lists: [1063](https://www.inaturalist.org/places/1063)
- GBIF GADM gid for the activity region: [`USA.43_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.43_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Sewanee,_Tennessee) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-TN --inat-place-id 45 --gbif-gadm-gid USA.43_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Sialia sialis* | Eastern Bluebird | no | [2490941](https://www.gbif.org/species/2490941) | [12942](https://www.inaturalist.org/taxa/12942) |  |
| *Dryocopus pileatus* | Pileated Woodpecker | no | [5228824](https://www.gbif.org/species/5228824) | [17855](https://www.inaturalist.org/taxa/17855) |  |
| *Strix varia* | Barred Owl | no | [2497541](https://www.gbif.org/species/2497541) | [19893](https://www.inaturalist.org/taxa/19893) |  |
| *Cyanocitta cristata* | Blue Jay | no | [2482593](https://www.gbif.org/species/2482593) | [8229](https://www.inaturalist.org/taxa/8229) |  |
| *Piranga rubra* | Summer Tanager | no | [2488485](https://www.gbif.org/species/2488485) | [9915](https://www.inaturalist.org/taxa/9915) |  |
| *Meleagris gallopavo* | Wild Turkey | no | [9606290](https://www.gbif.org/species/9606290) | [906](https://www.inaturalist.org/taxa/906) |  |
| *Odocoileus virginianus* | White-tailed Deer | no | [2440965](https://www.gbif.org/species/2440965) | [42223](https://www.inaturalist.org/taxa/42223) |  |
| *Dasypus mexicanus* | Mexican Long-nosed Armadillo | no | [2440779](https://www.gbif.org/species/2440779) | [1647419](https://www.inaturalist.org/taxa/1647419) | GBIF uses Dasypus novemcinctus, which iNaturalist splits |
| *Tamias striatus* | Eastern Chipmunk | no | [2437438](https://www.gbif.org/species/2437438) | [46217](https://www.inaturalist.org/taxa/46217) |  |
| *Perimyotis subflavus* | Tricolored Bat | no | [7665644](https://www.gbif.org/species/7665644) | [183166](https://www.inaturalist.org/taxa/183166) |  |
| *Terrapene carolina* | Common Box Turtle | no | [2443173](https://www.gbif.org/species/2443173) | [39814](https://www.inaturalist.org/taxa/39814) |  |
| *Plethodon glutinosus* | Northern Slimy Salamander | no | [2431539](https://www.gbif.org/species/2431539) | [27184](https://www.inaturalist.org/taxa/27184) |  |

### Notes

- Oak-hickory forest on the Cumberland Plateau top.
- Observations are sparse here (about 18,000 research-grade in the county); `fetch_activity.py` may fall back to the state (US-TN). Say so in the PR.

### Plants

Ship `locales/tn-cumberland/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/tn-cumberland/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-TN`
- [ ] `locales/tn-cumberland/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale tn-cumberland --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Sewanee woods lot (tn-cumberland)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
