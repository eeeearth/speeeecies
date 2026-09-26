<!-- title: Locale: A Toronto lot (toronto-ca) -->
**A Toronto lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/toronto-ca/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `toronto-ca` |
| `name` | A Toronto lot |
| `country` | `CA` |
| `activity_region` | `CA-ON` (Ontario) |
| `public_lat`, `public_lon` | 43.67, -79.39: the public city centroid from Wikidata [Q172](https://www.wikidata.org/wiki/Q172) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Toronto` |
| `koppen` | `Dfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Toronto) (CC BY-SA); confirm |
| `elevation_m` | 76 m, from Wikidata [Q172](https://www.wikidata.org/wiki/Q172) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [6883](https://www.inaturalist.org/places/6883)
- iNaturalist place for the city (species lists): [27608](https://www.inaturalist.org/places/27608)
- GBIF GADM gid for the activity region: [`CAN.9_1`](https://www.gbif.org/occurrence/search?gadm_gid=CAN.9_1)
- GBIF country page: https://www.gbif.org/country/CA/summary
- iNaturalist.ca: https://inaturalist.ca/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Toronto) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region CA-ON --inat-place-id 6883 --gbif-gadm-gid CAN.9_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 2 of these existed under `species/` (`passer-domesticus`, `sciurus-carolinensis`); they still need a curve for `CA-ON`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Dryobates pubescens* | Downy Woodpecker | no | [9149595](https://www.gbif.org/species/9149595) | [792988](https://www.inaturalist.org/taxa/792988) |  |
| *Spinus tristis* | American Goldfinch | no | [5231640](https://www.gbif.org/species/5231640) | [145310](https://www.inaturalist.org/taxa/145310) |  |
| *Poecile atricapillus* | Black-capped Chickadee | no | [2487805](https://www.gbif.org/species/2487805) | [144815](https://www.inaturalist.org/taxa/144815) |  |
| *Zenaida macroura* | Mourning Dove | no | [2495347](https://www.gbif.org/species/2495347) | [3454](https://www.inaturalist.org/taxa/3454) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Procyon lotor* | Common Raccoon | no | [5218786](https://www.gbif.org/species/5218786) | [41663](https://www.inaturalist.org/taxa/41663) |  |
| *Tamias striatus* | Eastern Chipmunk | no | [2437438](https://www.gbif.org/species/2437438) | [46217](https://www.inaturalist.org/taxa/46217) |  |
| *Sylvilagus floridanus* | Eastern Cottontail | no | [2436886](https://www.gbif.org/species/2436886) | [43111](https://www.inaturalist.org/taxa/43111) |  |
| *Anaxyrus americanus* | American Toad | no | [2422872](https://www.gbif.org/species/2422872) | [64968](https://www.inaturalist.org/taxa/64968) |  |

### Plants

Ship `locales/toronto-ca/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/toronto-ca/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `CA-ON`
- [ ] `locales/toronto-ca/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale toronto-ca --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Toronto lot (toronto-ca)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
