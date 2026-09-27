<!-- title: Locale: A Jersey City rowhouse garden (nj-jerseycity) -->
**A Jersey City rowhouse garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/nj-jerseycity/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `nj-jerseycity` |
| `name` | A Jersey City rowhouse garden |
| `country` | `US` |
| `activity_region` | `US-NJ` (New Jersey) |
| `public_lat`, `public_lon` | 40.75, -74.05: the public city centroid from Wikidata [Q7739304](https://www.wikidata.org/wiki/Q7739304) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Jersey_City,_New_Jersey) (CC BY-SA); confirm |
| `elevation_m` | to confirm (Wikidata [Q7739304](https://www.wikidata.org/wiki/Q7739304) has no elevation) |
| `plot_template` | `rowhouse-garden` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [51](https://www.inaturalist.org/places/51)
- iNaturalist place for Hudson County, for species lists: [3020](https://www.inaturalist.org/places/3020)
- GBIF GADM gid for the activity region: [`USA.31_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.31_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Jersey_City,_New_Jersey) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-NJ --inat-place-id 51 --gbif-gadm-gid USA.31_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 3 of these existed under `species/` (`columba-livia`, `passer-domesticus`, `sciurus-carolinensis`); they still need a curve for `US-NJ`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Columba livia* | Rock Pigeon | yes (`columba-livia`) | [2495414](https://www.gbif.org/species/2495414) | [3017](https://www.inaturalist.org/taxa/3017) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Sturnus vulgaris* | European Starling | no | [9809229](https://www.gbif.org/species/9809229) | [14850](https://www.inaturalist.org/taxa/14850) |  |
| *Mimus polyglottos* | Northern Mockingbird | no | [5231677](https://www.gbif.org/species/5231677) | [14886](https://www.inaturalist.org/taxa/14886) |  |
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Zenaida macroura* | Mourning Dove | no | [2495347](https://www.gbif.org/species/2495347) | [3454](https://www.inaturalist.org/taxa/3454) |  |
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Mephitis mephitis* | Striped Skunk | no | [5219380](https://www.gbif.org/species/5219380) | [41880](https://www.inaturalist.org/taxa/41880) |  |
| *Rattus norvegicus* | Brown Rat | no | [2439261](https://www.gbif.org/species/2439261) | [44576](https://www.inaturalist.org/taxa/44576) |  |
| *Lasiurus borealis* | Eastern Red Bat | no | [5218543](https://www.gbif.org/species/5218543) | [40522](https://www.inaturalist.org/taxa/40522) |  |
| *Podarcis siculus* | Italian Wall Lizard | no | [9185677](https://www.gbif.org/species/9185677) | [337045](https://www.inaturalist.org/taxa/337045) |  |

### Notes

- The centroid is The Heights neighbourhood item; the Köppen class comes from the Jersey City article.
- Rock pigeons, house sparrows, starlings, brown rats and the Italian wall lizard are introduced here.

### Plants

Ship `locales/nj-jerseycity/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/nj-jerseycity/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-NJ`
- [ ] `locales/nj-jerseycity/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale nj-jerseycity --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Jersey City rowhouse garden (nj-jerseycity)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
