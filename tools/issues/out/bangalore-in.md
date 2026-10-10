<!-- title: Locale: A Bangalore terrace (bangalore-in) -->
**A Bangalore terrace**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/bangalore-in/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `bangalore-in` |
| `name` | A Bangalore terrace |
| `country` | `IN` |
| `activity_region` | `IN-KA` (Karnataka) |
| `public_lat`, `public_lon` | 12.98, 77.59: the public city centroid from Wikidata [Q1355](https://www.wikidata.org/wiki/Q1355) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Asia/Kolkata` |
| `koppen` | `Aw`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Bengaluru) (CC BY-SA); confirm |
| `elevation_m` | 920 m, from Wikidata [Q1355](https://www.wikidata.org/wiki/Q1355) `P2044` (CC0) |
| `plot_template` | `rowhouse-garden` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [7043](https://www.inaturalist.org/places/7043)
- iNaturalist place for the city (species lists): [32239](https://www.inaturalist.org/places/32239)
- GBIF GADM gid for the activity region: [`IND.16_1`](https://www.gbif.org/occurrence/search?gadm_gid=IND.16_1)
- GBIF country page: https://www.gbif.org/country/IN/summary
- India Biodiversity Portal: https://indiabiodiversity.org/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Bengaluru) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region IN-KA --inat-place-id 7043 --gbif-gadm-gid IND.16_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`psittacula-krameri`); they still need a curve for `IN-KA`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Milvus migrans* | Black Kite | no | [5229167](https://www.gbif.org/species/5229167) | [5268](https://www.inaturalist.org/taxa/5268) |  |
| *Pycnonotus jocosus* | Red-whiskered Bulbul | no | [2486151](https://www.gbif.org/species/2486151) | [14591](https://www.inaturalist.org/taxa/14591) |  |
| *Leptocoma zeylonica* | Purple-rumped Sunbird | no | [7340855](https://www.gbif.org/species/7340855) | [145146](https://www.inaturalist.org/taxa/145146) |  |
| *Spilopelia chinensis* | Spotted Dove | no | [6101224](https://www.gbif.org/species/6101224) | [1455918](https://www.inaturalist.org/taxa/1455918) |  |
| *Psittacula krameri* | Rose-ringed Parakeet | yes (`psittacula-krameri`) | [2479226](https://www.gbif.org/species/2479226) | [18911](https://www.inaturalist.org/taxa/18911) |  |
| *Acridotheres tristis* | Common Myna | no | [2489005](https://www.gbif.org/species/2489005) | [204454](https://www.inaturalist.org/taxa/204454) |  |
| *Copsychus saularis* | Oriental Magpie-Robin | no | [2492680](https://www.gbif.org/species/2492680) | [204491](https://www.inaturalist.org/taxa/204491) |  |
| *Corvus splendens* | House Crow | no | [2482499](https://www.gbif.org/species/2482499) | [8031](https://www.inaturalist.org/taxa/8031) |  |
| *Funambulus palmarum* | Three-striped Palm Squirrel | no | [2437246](https://www.gbif.org/species/2437246) | [45938](https://www.inaturalist.org/taxa/45938) |  |
| *Pteropus medius* | Indian Flying Fox | no | [5787518](https://www.gbif.org/species/5787518) | [1641421](https://www.inaturalist.org/taxa/1641421) |  |
| *Duttaphrynus melanostictus* | Asian Common Toad | no | [2422538](https://www.gbif.org/species/2422538) | [62345](https://www.inaturalist.org/taxa/62345) |  |
| *Hemidactylus frenatus* | Asian House Gecko | no | [9537238](https://www.gbif.org/species/9537238) | [51940](https://www.inaturalist.org/taxa/51940) |  |

### Notes

- There is no terrace template; `rowhouse-garden` is the closest generic plot.

### Plants

Ship `locales/bangalore-in/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/bangalore-in/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `IN-KA`
- [ ] `locales/bangalore-in/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale bangalore-in --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Bangalore terrace (bangalore-in)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
