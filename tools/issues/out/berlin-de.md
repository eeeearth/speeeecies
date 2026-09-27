<!-- title: Locale: A Berlin courtyard (berlin-de) -->
**A Berlin courtyard**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/berlin-de/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `berlin-de` |
| `name` | A Berlin courtyard |
| `country` | `DE` |
| `activity_region` | `DE-BE` (Berlin) |
| `public_lat`, `public_lon` | 52.52, 13.38: the public city centroid from Wikidata [Q64](https://www.wikidata.org/wiki/Q64) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Europe/Berlin` |
| `koppen` | `Cfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Berlin) (CC BY-SA); confirm |
| `elevation_m` | 34 m, from Wikidata [Q64](https://www.wikidata.org/wiki/Q64) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [12872](https://www.inaturalist.org/places/12872)
- iNaturalist place for the city (species lists): [29472](https://www.inaturalist.org/places/29472)
- GBIF GADM gid for the activity region: [`DEU.3_1`](https://www.gbif.org/occurrence/search?gadm_gid=DEU.3_1)
- GBIF country page: https://www.gbif.org/country/DE/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Berlin) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region DE-BE --inat-place-id 12872 --gbif-gadm-gid DEU.3_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 8 of these existed under `species/` (`passer-domesticus`, `turdus-merula`, `columba-palumbus`, `parus-major`, `cyanistes-caeruleus`, `vulpes-vulpes`, `erinaceus-europaeus`, `bufo-bufo`); they still need a curve for `DE-BE`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Turdus merula* | Eurasian Blackbird | yes (`turdus-merula`) | [2490719](https://www.gbif.org/species/2490719) | [12716](https://www.inaturalist.org/taxa/12716) |  |
| *Corvus cornix* | Hooded Crow | no | [2482515](https://www.gbif.org/species/2482515) | [144757](https://www.inaturalist.org/taxa/144757) |  |
| *Columba palumbus* | Common Wood-Pigeon | yes (`columba-palumbus`) | [2495455](https://www.gbif.org/species/2495455) | [3048](https://www.inaturalist.org/taxa/3048) |  |
| *Sturnus vulgaris* | European Starling | no | [9809229](https://www.gbif.org/species/9809229) | [14850](https://www.inaturalist.org/taxa/14850) |  |
| *Parus major* | Great Tit | yes (`parus-major`) | [9705453](https://www.gbif.org/species/9705453) | [203153](https://www.inaturalist.org/taxa/203153) |  |
| *Cyanistes caeruleus* | Eurasian Blue Tit | yes (`cyanistes-caeruleus`) | [2487879](https://www.gbif.org/species/2487879) | [144849](https://www.inaturalist.org/taxa/144849) |  |
| *Sciurus vulgaris* | Eurasian Red Squirrel | no | [8211070](https://www.gbif.org/species/8211070) | [46001](https://www.inaturalist.org/taxa/46001) |  |
| *Vulpes vulpes* | Red Fox | yes (`vulpes-vulpes`) | [5219243](https://www.gbif.org/species/5219243) | [42069](https://www.inaturalist.org/taxa/42069) |  |
| *Erinaceus europaeus* | Common Hedgehog | yes (`erinaceus-europaeus`) | [5219616](https://www.gbif.org/species/5219616) | [43042](https://www.inaturalist.org/taxa/43042) |  |
| *Procyon lotor* | Common Raccoon | no | [5218786](https://www.gbif.org/species/5218786) | [41663](https://www.inaturalist.org/taxa/41663) |  |
| *Bufo bufo* | European Toad | yes (`bufo-bufo`) | [5217160](https://www.gbif.org/species/5217160) | [326296](https://www.inaturalist.org/taxa/326296) |  |

### Notes

- Berlin sits on the Cfb/Dfb boundary; Wikipedia gives Cfb.
- Raccoons (Procyon lotor) are introduced here; say so in the species record's notes.

### Plants

Ship `locales/berlin-de/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/berlin-de/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `DE-BE`
- [ ] `locales/berlin-de/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale berlin-de --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Berlin courtyard (berlin-de)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
