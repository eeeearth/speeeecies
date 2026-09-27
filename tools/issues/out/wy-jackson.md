<!-- title: Locale: A Jackson Hole lot (wy-jackson) -->
**A Jackson Hole lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/wy-jackson/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `wy-jackson` |
| `name` | A Jackson Hole lot |
| `country` | `US` |
| `activity_region` | `US-WY` (Wyoming) |
| `public_lat`, `public_lon` | 43.48, -110.77: the public city centroid from Wikidata [Q871285](https://www.wikidata.org/wiki/Q871285) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Denver` |
| `koppen` | `Dfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Jackson,_Wyoming) (CC BY-SA); confirm |
| `elevation_m` | 1901 m, from Wikidata [Q871285](https://www.wikidata.org/wiki/Q871285) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [15](https://www.inaturalist.org/places/15)
- iNaturalist place for Teton County, for species lists: [1784](https://www.inaturalist.org/places/1784)
- GBIF GADM gid for the activity region: [`USA.51_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.51_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Jackson,_Wyoming) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-WY --inat-place-id 15 --gbif-gadm-gid USA.51_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Corvus corax* | Common Raven | no | [2482492](https://www.gbif.org/species/2482492) | [8010](https://www.inaturalist.org/taxa/8010) |  |
| *Pica hudsonia* | Black-billed Magpie | no | [5229487](https://www.gbif.org/species/5229487) | [143853](https://www.inaturalist.org/taxa/143853) |  |
| *Sialia currucoides* | Mountain Bluebird | no | [2490935](https://www.gbif.org/species/2490935) | [12936](https://www.inaturalist.org/taxa/12936) |  |
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Poecile gambeli* | Mountain Chickadee | no | [2487825](https://www.gbif.org/species/2487825) | [144816](https://www.inaturalist.org/taxa/144816) |  |
| *Junco hyemalis* | Dark-eyed Junco | no | [9362842](https://www.gbif.org/species/9362842) | [10094](https://www.inaturalist.org/taxa/10094) |  |
| *Odocoileus hemionus* | Mule Deer | no | [2440974](https://www.gbif.org/species/2440974) | [42220](https://www.inaturalist.org/taxa/42220) |  |
| *Urocitellus armatus* | Uinta Ground Squirrel | no | [8151861](https://www.gbif.org/species/8151861) | [179994](https://www.inaturalist.org/taxa/179994) |  |
| *Tamiasciurus hudsonicus* | American Red Squirrel | no | [2437282](https://www.gbif.org/species/2437282) | [46260](https://www.inaturalist.org/taxa/46260) |  |
| *Myotis lucifugus* | Little Brown Bat | no | [2432406](https://www.gbif.org/species/2432406) | [40346](https://www.inaturalist.org/taxa/40346) |  |
| *Thamnophis elegans* | Western Terrestrial Garter Snake | no | [2457545](https://www.gbif.org/species/2457545) | [28398](https://www.inaturalist.org/taxa/28398) |  |
| *Pseudacris maculata* | Boreal Chorus Frog | no | [2428169](https://www.gbif.org/species/2428169) | [24255](https://www.inaturalist.org/taxa/24255) |  |

### Notes

- Most county records are the national parks' big game (bison, elk, moose, bears); pick what a lot in the town sees.
- Bat records are sparse here (a few research-grade myotis observations in the county).

### Plants

Ship `locales/wy-jackson/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/wy-jackson/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-WY`
- [ ] `locales/wy-jackson/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale wy-jackson --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Jackson Hole lot (wy-jackson)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
