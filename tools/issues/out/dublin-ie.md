<!-- title: Locale: A Dublin garden (dublin-ie) -->
**A Dublin garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/dublin-ie/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `dublin-ie` |
| `name` | A Dublin garden |
| `country` | `IE` |
| `activity_region` | `IE-D` (County Dublin) |
| `public_lat`, `public_lon` | 53.35, -6.26: the public city centroid from Wikidata [Q1761](https://www.wikidata.org/wiki/Q1761) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Europe/Dublin` |
| `koppen` | `Cfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Dublin) (CC BY-SA); confirm |
| `elevation_m` | 20 m, from Wikidata [Q1761](https://www.wikidata.org/wiki/Q1761) `P2044` (CC0) |
| `plot_template` | `rowhouse-garden` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [6719](https://www.inaturalist.org/places/6719)
- GBIF GADM gid for the activity region: [`IRL.6_1`](https://www.gbif.org/occurrence/search?gadm_gid=IRL.6_1)
- GBIF country page: https://www.gbif.org/country/IE/summary
- National Biodiversity Data Centre: https://biodiversityireland.ie/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Dublin) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region IE-D --inat-place-id 6719 --gbif-gadm-gid IRL.6_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 9 of these existed under `species/` (`turdus-merula`, `erithacus-rubecula`, `passer-domesticus`, `cyanistes-caeruleus`, `pica-pica`, `parus-major`, `vulpes-vulpes`, `sciurus-carolinensis`, `erinaceus-europaeus`); they still need a curve for `IE-D`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus merula* | Eurasian Blackbird | yes (`turdus-merula`) | [2490719](https://www.gbif.org/species/2490719) | [12716](https://www.inaturalist.org/taxa/12716) |  |
| *Erithacus rubecula* | European Robin | yes (`erithacus-rubecula`) | [2492462](https://www.gbif.org/species/2492462) | [13094](https://www.inaturalist.org/taxa/13094) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Cyanistes caeruleus* | Eurasian Blue Tit | yes (`cyanistes-caeruleus`) | [2487879](https://www.gbif.org/species/2487879) | [144849](https://www.inaturalist.org/taxa/144849) |  |
| *Pica pica* | Eurasian Magpie | yes (`pica-pica`) | [5229490](https://www.gbif.org/species/5229490) | [891696](https://www.inaturalist.org/taxa/891696) |  |
| *Corvus cornix* | Hooded Crow | no | [2482515](https://www.gbif.org/species/2482515) | [144757](https://www.inaturalist.org/taxa/144757) |  |
| *Coloeus monedula* | Eurasian Jackdaw | no | [6100954](https://www.gbif.org/species/6100954) | [336399](https://www.inaturalist.org/taxa/336399) |  |
| *Parus major* | Great Tit | yes (`parus-major`) | [9705453](https://www.gbif.org/species/9705453) | [203153](https://www.inaturalist.org/taxa/203153) |  |
| *Vulpes vulpes* | Red Fox | yes (`vulpes-vulpes`) | [5219243](https://www.gbif.org/species/5219243) | [42069](https://www.inaturalist.org/taxa/42069) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Erinaceus europaeus* | Common Hedgehog | yes (`erinaceus-europaeus`) | [5219616](https://www.gbif.org/species/5219616) | [43042](https://www.inaturalist.org/taxa/43042) |  |
| *Rana temporaria* | European Common Frog | no | [2426805](https://www.gbif.org/species/2426805) | [25591](https://www.inaturalist.org/taxa/25591) |  |

### Notes

- Most of these species already exist, so this is a good first locale.
- Wikidata files Dublin under Leinster (IE-L); the county code IE-D matches the GADM gid above.

### Plants

Ship `locales/dublin-ie/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/dublin-ie/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `IE-D`
- [ ] `locales/dublin-ie/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale dublin-ie --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Dublin garden (dublin-ie)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
