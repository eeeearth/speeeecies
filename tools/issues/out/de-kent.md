<!-- title: Locale: A Kent County farm lot (de-kent) -->
**A Kent County farm lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/de-kent/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `de-kent` |
| `name` | A Kent County farm lot |
| `country` | `US` |
| `activity_region` | `US-DE` (Delaware) |
| `public_lat`, `public_lon` | 39.10, -75.50: the public city centroid from Wikidata [Q128137](https://www.wikidata.org/wiki/Q128137) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Kent_County,_Delaware) (CC BY-SA); confirm |
| `elevation_m` | to confirm (Wikidata [Q128137](https://www.wikidata.org/wiki/Q128137) has no elevation) |
| `plot_template` | `rural-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [4](https://www.inaturalist.org/places/4)
- iNaturalist place for Kent County, for species lists: [1741](https://www.inaturalist.org/places/1741)
- GBIF GADM gid for the activity region: [`USA.8_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.8_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Kent_County,_Delaware) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-DE --inat-place-id 4 --gbif-gadm-gid USA.8_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`vulpes-vulpes`); they still need a curve for `US-DE`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Haliaeetus leucocephalus* | Bald Eagle | no | [2480446](https://www.gbif.org/species/2480446) | [5305](https://www.inaturalist.org/taxa/5305) |  |
| *Ardea herodias* | Great Blue Heron | no | [9630752](https://www.gbif.org/species/9630752) | [4956](https://www.inaturalist.org/taxa/4956) |  |
| *Agelaius phoeniceus* | Red-winged Blackbird | no | [9409198](https://www.gbif.org/species/9409198) | [9744](https://www.inaturalist.org/taxa/9744) |  |
| *Passerina caerulea* | Blue Grosbeak | no | [5230862](https://www.gbif.org/species/5230862) | [73155](https://www.inaturalist.org/taxa/73155) |  |
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Tyrannus tyrannus* | Eastern Kingbird | no | [5229688](https://www.gbif.org/species/5229688) | [16782](https://www.inaturalist.org/taxa/16782) |  |
| *Vulpes vulpes* | Red Fox | yes (`vulpes-vulpes`) | [5219243](https://www.gbif.org/species/5219243) | [42069](https://www.inaturalist.org/taxa/42069) |  |
| *Sylvilagus floridanus* | Eastern Cottontail | no | [2436886](https://www.gbif.org/species/2436886) | [43111](https://www.inaturalist.org/taxa/43111) |  |
| *Peromyscus leucopus* | White-footed Mouse | no | [2438019](https://www.gbif.org/species/2438019) | [44395](https://www.inaturalist.org/taxa/44395) |  |
| *Lasiurus borealis* | Eastern Red Bat | no | [5218543](https://www.gbif.org/species/5218543) | [40522](https://www.inaturalist.org/taxa/40522) |  |
| *Anaxyrus fowleri* | Fowler's Toad | no | [2422905](https://www.gbif.org/species/2422905) | [64977](https://www.inaturalist.org/taxa/64977) |  |
| *Chrysemys picta* | Painted Turtle | no | [2443133](https://www.gbif.org/species/2443133) | [39771](https://www.inaturalist.org/taxa/39771) |  |

### Notes

- The centroid is the county's; the lot is farmland with a woodlot edge, not the Delaware Bay marshes, which supply many of the county's records.

### Plants

Ship `locales/de-kent/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/de-kent/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-DE`
- [ ] `locales/de-kent/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale de-kent --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Kent County farm lot (de-kent)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
