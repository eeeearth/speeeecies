<!-- title: Locale: A Buenos Aires patio (buenosaires-ar) -->
**A Buenos Aires patio**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/buenosaires-ar/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `buenosaires-ar` |
| `name` | A Buenos Aires patio |
| `country` | `AR` |
| `activity_region` | `AR-C` (Buenos Aires City) |
| `public_lat`, `public_lon` | -34.60, -58.38: the public city centroid from Wikidata [Q1486](https://www.wikidata.org/wiki/Q1486) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Argentina/Buenos_Aires` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Buenos_Aires) (CC BY-SA); confirm |
| `elevation_m` | 25 m, from Wikidata [Q1486](https://www.wikidata.org/wiki/Q1486) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10434](https://www.inaturalist.org/places/10434)
- iNaturalist place for the city (species lists): [14264](https://www.inaturalist.org/places/14264)
- GBIF GADM gid for the activity region: [`ARG.5_1`](https://www.gbif.org/occurrence/search?gadm_gid=ARG.5_1)
- GBIF country page: https://www.gbif.org/country/AR/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Buenos_Aires) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region AR-C --inat-place-id 10434 --gbif-gadm-gid ARG.5_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`passer-domesticus`); they still need a curve for `AR-C`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Furnarius rufus* | Rufous Hornero | no | [2485821](https://www.gbif.org/species/2485821) | [11275](https://www.inaturalist.org/taxa/11275) |  |
| *Pitangus sulphuratus* | Great Kiskadee | no | [2482755](https://www.gbif.org/species/2482755) | [16956](https://www.inaturalist.org/taxa/16956) |  |
| *Turdus rufiventris* | Rufous-bellied Thrush | no | [2490718](https://www.gbif.org/species/2490718) | [12738](https://www.inaturalist.org/taxa/12738) |  |
| *Mimus saturninus* | Chalk-browed Mockingbird | no | [5231675](https://www.gbif.org/species/5231675) | [14878](https://www.inaturalist.org/taxa/14878) |  |
| *Patagioenas picazuro* | Picazuro Pigeon | no | [2495287](https://www.gbif.org/species/2495287) | [3102](https://www.inaturalist.org/taxa/3102) |  |
| *Zenaida auriculata* | Eared Dove | no | [2495358](https://www.gbif.org/species/2495358) | [3439](https://www.inaturalist.org/taxa/3439) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Myiopsitta monachus* | Monk Parakeet | no | [2479407](https://www.gbif.org/species/2479407) | [19349](https://www.inaturalist.org/taxa/19349) |  |
| *Zonotrichia capensis* | Rufous-collared Sparrow | no | [5231103](https://www.gbif.org/species/5231103) | [9183](https://www.inaturalist.org/taxa/9183) |  |
| *Didelphis albiventris* | White-eared Opossum | no | [2439930](https://www.gbif.org/species/2439930) | [42658](https://www.inaturalist.org/taxa/42658) |  |
| *Salvator merianae* | Argentine Black-and-white Tegu | no | [5227370](https://www.gbif.org/species/5227370) | [318758](https://www.inaturalist.org/taxa/318758) |  |
| *Rhinella arenarum* | Argentine Toad | no | [5216921](https://www.gbif.org/species/5216921) | [67093](https://www.inaturalist.org/taxa/67093) |  |

### Plants

Ship `locales/buenosaires-ar/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/buenosaires-ar/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `AR-C`
- [ ] `locales/buenosaires-ar/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale buenosaires-ar --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Buenos Aires patio (buenosaires-ar)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
