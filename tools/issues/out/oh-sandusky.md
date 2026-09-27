<!-- title: Locale: A Sandusky shore lot (oh-sandusky) -->
**A Sandusky shore lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/oh-sandusky/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `oh-sandusky` |
| `name` | A Sandusky shore lot |
| `country` | `US` |
| `activity_region` | `US-OH` (Ohio) |
| `public_lat`, `public_lon` | 41.45, -82.71: the public city centroid from Wikidata [Q608207](https://www.wikidata.org/wiki/Q608207) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Dfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Sandusky,_Ohio) (CC BY-SA); confirm |
| `elevation_m` | 182 m, from Wikidata [Q608207](https://www.wikidata.org/wiki/Q608207) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [31](https://www.inaturalist.org/places/31)
- iNaturalist place for Erie County, for species lists: [2775](https://www.inaturalist.org/places/2775)
- GBIF GADM gid for the activity region: [`USA.36_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.36_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Sandusky,_Ohio) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-OH --inat-place-id 31 --gbif-gadm-gid USA.36_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Haliaeetus leucocephalus* | Bald Eagle | no | [2480446](https://www.gbif.org/species/2480446) | [5305](https://www.inaturalist.org/taxa/5305) |  |
| *Ardea herodias* | Great Blue Heron | no | [9630752](https://www.gbif.org/species/9630752) | [4956](https://www.inaturalist.org/taxa/4956) |  |
| *Larus delawarensis* | Ring-billed Gull | no | [2481134](https://www.gbif.org/species/2481134) | [4364](https://www.inaturalist.org/taxa/4364) |  |
| *Agelaius phoeniceus* | Red-winged Blackbird | no | [9409198](https://www.gbif.org/species/9409198) | [9744](https://www.inaturalist.org/taxa/9744) |  |
| *Tachycineta bicolor* | Tree Swallow | no | [2489181](https://www.gbif.org/species/2489181) | [11935](https://www.inaturalist.org/taxa/11935) |  |
| *Melanerpes erythrocephalus* | Red-headed Woodpecker | no | [2478130](https://www.gbif.org/species/2478130) | [18204](https://www.inaturalist.org/taxa/18204) |  |
| *Blarina brevicauda* | Northern Short-tailed Shrew | no | [2435862](https://www.gbif.org/species/2435862) | [63113](https://www.inaturalist.org/taxa/63113) |  |
| *Sciurus niger* | Eastern Fox Squirrel | no | [5219683](https://www.gbif.org/species/5219683) | [46020](https://www.inaturalist.org/taxa/46020) |  |
| *Procyon lotor* | Common Raccoon | no | [5218786](https://www.gbif.org/species/5218786) | [41663](https://www.inaturalist.org/taxa/41663) |  |
| *Lasiurus borealis* | Eastern Red Bat | no | [5218543](https://www.gbif.org/species/5218543) | [40522](https://www.inaturalist.org/taxa/40522) |  |
| *Nerodia sipedon* | Common Watersnake | no | [5223334](https://www.gbif.org/species/5223334) | [29305](https://www.inaturalist.org/taxa/29305) |  |
| *Chrysemys picta* | Painted Turtle | no | [2443133](https://www.gbif.org/species/2443133) | [39771](https://www.inaturalist.org/taxa/39771) |  |

### Notes

- A coastal lot on Sandusky Bay, Lake Erie: `suburban-lot` with the shore along one edge.
- The Lake Erie islands' water snakes are a protected subspecies of the common watersnake.
- iNaturalist's "Sandusky" search finds Sandusky County first; Sandusky city is in Erie County.

### Plants

Ship `locales/oh-sandusky/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/oh-sandusky/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-OH`
- [ ] `locales/oh-sandusky/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale oh-sandusky --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Sandusky shore lot (oh-sandusky)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
