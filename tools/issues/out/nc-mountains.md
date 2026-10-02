<!-- title: Locale: A Boone mountain lot (nc-mountains) -->
**A Boone mountain lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/nc-mountains/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `nc-mountains` |
| `name` | A Boone mountain lot |
| `country` | `US` |
| `activity_region` | `US-NC` (North Carolina) |
| `public_lat`, `public_lon` | 36.22, -81.67: the public city centroid from Wikidata [Q893055](https://www.wikidata.org/wiki/Q893055) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Dfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Boone,_North_Carolina) (CC BY-SA); confirm |
| `elevation_m` | 1015.9 m, from Wikidata [Q893055](https://www.wikidata.org/wiki/Q893055) `P2044` (CC0) |
| `plot_template` | `rural-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [30](https://www.inaturalist.org/places/30)
- iNaturalist place for Watauga County, for species lists: [216](https://www.inaturalist.org/places/216)
- GBIF GADM gid for the activity region: [`USA.34_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.34_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Boone,_North_Carolina) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-NC --inat-place-id 30 --gbif-gadm-gid USA.34_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Junco hyemalis* | Dark-eyed Junco | no | [9362842](https://www.gbif.org/species/9362842) | [10094](https://www.inaturalist.org/taxa/10094) |  |
| *Melospiza melodia* | Song Sparrow | no | [2492196](https://www.gbif.org/species/2492196) | [9100](https://www.inaturalist.org/taxa/9100) |  |
| *Meleagris gallopavo* | Wild Turkey | no | [9606290](https://www.gbif.org/species/9606290) | [906](https://www.inaturalist.org/taxa/906) |  |
| *Cyanocitta cristata* | Blue Jay | no | [2482593](https://www.gbif.org/species/2482593) | [8229](https://www.inaturalist.org/taxa/8229) |  |
| *Pipilo erythrophthalmus* | Eastern Towhee | no | [2491205](https://www.gbif.org/species/2491205) | [9424](https://www.inaturalist.org/taxa/9424) |  |
| *Archilochus colubris* | Ruby-throated Hummingbird | no | [5228514](https://www.gbif.org/species/5228514) | [6432](https://www.inaturalist.org/taxa/6432) |  |
| *Odocoileus virginianus* | White-tailed Deer | no | [2440965](https://www.gbif.org/species/2440965) | [42223](https://www.inaturalist.org/taxa/42223) |  |
| *Tamias striatus* | Eastern Chipmunk | no | [2437438](https://www.gbif.org/species/2437438) | [46217](https://www.inaturalist.org/taxa/46217) |  |
| *Glaucomys volans* | Southern Flying Squirrel | no | [2437338](https://www.gbif.org/species/2437338) | [46272](https://www.inaturalist.org/taxa/46272) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Desmognathus orestes* | Blue Ridge Dusky Salamander | no | [2431207](https://www.gbif.org/species/2431207) | [27405](https://www.inaturalist.org/taxa/27405) |  |
| *Thamnophis sirtalis* | Common Garter Snake | no | [2457522](https://www.gbif.org/species/2457522) | [28362](https://www.inaturalist.org/taxa/28362) |  |

### Notes

- The southern Appalachians are a salamander hotspot; a dusky salamander is the plot's amphibian.

### Plants

Ship `locales/nc-mountains/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/nc-mountains/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-NC`
- [ ] `locales/nc-mountains/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale nc-mountains --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Boone mountain lot (nc-mountains)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
