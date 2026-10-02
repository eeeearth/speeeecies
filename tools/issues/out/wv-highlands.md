<!-- title: Locale: A Canaan Valley lot (wv-highlands) -->
**A Canaan Valley lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/wv-highlands/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `wv-highlands` |
| `name` | A Canaan Valley lot |
| `country` | `US` |
| `activity_region` | `US-WV` (West Virginia) |
| `public_lat`, `public_lon` | 39.13, -79.38: the public city centroid from Wikidata [Q5029191](https://www.wikidata.org/wiki/Q5029191) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Dfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Davis,_West_Virginia) (CC BY-SA); confirm |
| `elevation_m` | to confirm (Wikidata [Q5029191](https://www.wikidata.org/wiki/Q5029191) has no elevation) |
| `plot_template` | `rural-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [33](https://www.inaturalist.org/places/33)
- iNaturalist place for Tucker County, for species lists: [752](https://www.inaturalist.org/places/752)
- GBIF GADM gid for the activity region: [`USA.49_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.49_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Davis,_West_Virginia) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-WV --inat-place-id 33 --gbif-gadm-gid USA.49_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Junco hyemalis* | Dark-eyed Junco | no | [9362842](https://www.gbif.org/species/9362842) | [10094](https://www.inaturalist.org/taxa/10094) |  |
| *Poecile atricapillus* | Black-capped Chickadee | no | [2487805](https://www.gbif.org/species/2487805) | [144815](https://www.inaturalist.org/taxa/144815) |  |
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Bombycilla cedrorum* | Cedar Waxwing | no | [2484609](https://www.gbif.org/species/2484609) | [7428](https://www.inaturalist.org/taxa/7428) |  |
| *Geothlypis trichas* | Common Yellowthroat | no | [2489670](https://www.gbif.org/species/2489670) | [9721](https://www.inaturalist.org/taxa/9721) |  |
| *Meleagris gallopavo* | Wild Turkey | no | [9606290](https://www.gbif.org/species/9606290) | [906](https://www.inaturalist.org/taxa/906) |  |
| *Odocoileus virginianus* | White-tailed Deer | no | [2440965](https://www.gbif.org/species/2440965) | [42223](https://www.inaturalist.org/taxa/42223) |  |
| *Tamiasciurus hudsonicus* | American Red Squirrel | no | [2437282](https://www.gbif.org/species/2437282) | [46260](https://www.inaturalist.org/taxa/46260) |  |
| *Lepus americanus* | Snowshoe Hare | no | [2436794](https://www.gbif.org/species/2436794) | [43132](https://www.inaturalist.org/taxa/43132) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Desmognathus ochrophaeus* | Allegheny Mountain Dusky Salamander | no | [2431199](https://www.gbif.org/species/2431199) | [27390](https://www.inaturalist.org/taxa/27390) |  |
| *Notophthalmus viridescens* | Eastern Newt | no | [5218390](https://www.gbif.org/species/5218390) | [27805](https://www.inaturalist.org/taxa/27805) |  |

### Notes

- A high valley (about 1,000 m) of wet meadow and spruce; the Köppen class comes from the Davis article.
- Bat records are sparse here (2 research-grade big brown bat observations in the county).

### Plants

Ship `locales/wv-highlands/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/wv-highlands/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-WV`
- [ ] `locales/wv-highlands/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale wv-highlands --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Canaan Valley lot (wv-highlands)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
