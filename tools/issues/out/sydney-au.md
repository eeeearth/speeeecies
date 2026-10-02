<!-- title: Locale: A Sydney backyard (sydney-au) -->
**A Sydney backyard**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/sydney-au/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `sydney-au` |
| `name` | A Sydney backyard |
| `country` | `AU` |
| `activity_region` | `AU-NSW` (New South Wales) |
| `public_lat`, `public_lon` | -33.87, 151.21: the public city centroid from Wikidata [Q3130](https://www.wikidata.org/wiki/Q3130) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Australia/Sydney` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Sydney) (CC BY-SA); confirm |
| `elevation_m` | 6 m, from Wikidata [Q3130](https://www.wikidata.org/wiki/Q3130) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [6825](https://www.inaturalist.org/places/6825)
- iNaturalist place for the city (species lists): [18684](https://www.inaturalist.org/places/18684)
- GBIF GADM gid for the activity region: [`AUS.5_1`](https://www.gbif.org/occurrence/search?gadm_gid=AUS.5_1)
- GBIF country page: https://www.gbif.org/country/AU/summary
- Atlas of Living Australia: https://www.ala.org.au/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Sydney) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region AU-NSW --inat-place-id 6825 --gbif-gadm-gid AUS.5_1 --write
```

### Candidate species (11; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Threskiornis molucca* | Australian Ibis | no | [2480765](https://www.gbif.org/species/2480765) | [3740](https://www.inaturalist.org/taxa/3740) |  |
| *Manorina melanocephala* | Noisy Miner | no | [2487365](https://www.gbif.org/species/2487365) | [12231](https://www.inaturalist.org/taxa/12231) |  |
| *Cacatua galerita* | Sulphur-crested Cockatoo | no | [2479888](https://www.gbif.org/species/2479888) | [116834](https://www.inaturalist.org/taxa/116834) |  |
| *Gymnorhina tibicen* | Australian Magpie | no | [2489450](https://www.gbif.org/species/2489450) | [8575](https://www.inaturalist.org/taxa/8575) |  |
| *Trichoglossus moluccanus* | Rainbow Lorikeet | no | [6170530](https://www.gbif.org/species/6170530) | [980095](https://www.inaturalist.org/taxa/980095) | GBIF files it as a synonym of Trichoglossus haematodus |
| *Vanellus miles* | Masked Lapwing | no | [5229134](https://www.gbif.org/species/5229134) | [4872](https://www.inaturalist.org/taxa/4872) |  |
| *Trichosurus vulpecula* | Common Brushtail Possum | no | [2440254](https://www.gbif.org/species/2440254) | [42808](https://www.inaturalist.org/taxa/42808) |  |
| *Pteropus poliocephalus* | Grey-headed Flying-fox | no | [5218655](https://www.gbif.org/species/5218655) | [40905](https://www.inaturalist.org/taxa/40905) |  |
| *Intellagama lesueurii* | Australian Water Dragon | no | [8161292](https://www.gbif.org/species/8161292) | [146186](https://www.inaturalist.org/taxa/146186) |  |
| *Tiliqua scincoides* | Common Bluetongue | no | [2462503](https://www.gbif.org/species/2462503) | [37456](https://www.inaturalist.org/taxa/37456) |  |
| *Litoria peronii* | Peron's Tree Frog | no | [2427831](https://www.gbif.org/species/2427831) | [1633155](https://www.inaturalist.org/taxa/1633155) | iNaturalist uses Pengilleyia peronii |

### Plants

Ship `locales/sydney-au/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/sydney-au/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `AU-NSW`
- [ ] `locales/sydney-au/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale sydney-au --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Sydney backyard (sydney-au)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
