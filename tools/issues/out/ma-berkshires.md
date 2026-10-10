<!-- title: Locale: A Great Barrington woodland lot (ma-berkshires) -->
**A Great Barrington woodland lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/ma-berkshires/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `ma-berkshires` |
| `name` | A Great Barrington woodland lot |
| `country` | `US` |
| `activity_region` | `US-MA` (Massachusetts) |
| `public_lat`, `public_lon` | 42.20, -73.36: the public city centroid from Wikidata [Q1144518](https://www.wikidata.org/wiki/Q1144518) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Dfb`, from the Beck et al. 2018 Köppen-Geiger map (CC BY 4.0, https://www.gloh2o.org/koppen/) for Great Barrington; the [Wikipedia](https://en.wikipedia.org/wiki/Great_Barrington,_Massachusetts) article gives no class; confirm |
| `elevation_m` | 221 m, from Wikidata [Q1144518](https://www.wikidata.org/wiki/Q1144518) `P2044` (CC0) |
| `plot_template` | `rural-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [2](https://www.inaturalist.org/places/2)
- iNaturalist place for Berkshire County, for species lists: [821](https://www.inaturalist.org/places/821)
- GBIF GADM gid for the activity region: [`USA.22_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.22_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the source named in the table above or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-MA --inat-place-id 2 --gbif-gadm-gid USA.22_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`vulpes-vulpes`); they still need a curve for `US-MA`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Meleagris gallopavo* | Wild Turkey | no | [9606290](https://www.gbif.org/species/9606290) | [906](https://www.inaturalist.org/taxa/906) |  |
| *Sayornis phoebe* | Eastern Phoebe | no | [2483606](https://www.gbif.org/species/2483606) | [17008](https://www.inaturalist.org/taxa/17008) |  |
| *Poecile atricapillus* | Black-capped Chickadee | no | [2487805](https://www.gbif.org/species/2487805) | [144815](https://www.inaturalist.org/taxa/144815) |  |
| *Cyanocitta cristata* | Blue Jay | no | [2482593](https://www.gbif.org/species/2482593) | [8229](https://www.inaturalist.org/taxa/8229) |  |
| *Sialia sialis* | Eastern Bluebird | no | [2490941](https://www.gbif.org/species/2490941) | [12942](https://www.inaturalist.org/taxa/12942) |  |
| *Strix varia* | Barred Owl | no | [2497541](https://www.gbif.org/species/2497541) | [19893](https://www.inaturalist.org/taxa/19893) |  |
| *Tamias striatus* | Eastern Chipmunk | no | [2437438](https://www.gbif.org/species/2437438) | [46217](https://www.inaturalist.org/taxa/46217) |  |
| *Erethizon dorsatum* | North American Porcupine | no | [6066824](https://www.gbif.org/species/6066824) | [44026](https://www.inaturalist.org/taxa/44026) | GBIF spells it Erethizon dorsatus |
| *Vulpes vulpes* | Red Fox | yes (`vulpes-vulpes`) | [5219243](https://www.gbif.org/species/5219243) | [42069](https://www.inaturalist.org/taxa/42069) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Notophthalmus viridescens* | Eastern Newt | no | [5218390](https://www.gbif.org/species/5218390) | [27805](https://www.inaturalist.org/taxa/27805) |  |
| *Anaxyrus americanus* | American Toad | no | [2422872](https://www.gbif.org/species/2422872) | [64968](https://www.inaturalist.org/taxa/64968) |  |

### Notes

- Black bears are common in the county but too large for most plots; list one only with a note.

### Plants

Ship `locales/ma-berkshires/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/ma-berkshires/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-MA`
- [ ] `locales/ma-berkshires/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale ma-berkshires --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Great Barrington woodland lot (ma-berkshires)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
