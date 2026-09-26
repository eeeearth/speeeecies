<!-- title: Locale: A Paris courtyard (paris-fr) -->
**A Paris courtyard**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/paris-fr/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `paris-fr` |
| `name` | A Paris courtyard |
| `country` | `FR` |
| `activity_region` | `FR-IDF` (Île-de-France) |
| `public_lat`, `public_lon` | 48.86, 2.35: the public city centroid from Wikidata [Q90](https://www.wikidata.org/wiki/Q90) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Europe/Paris` |
| `koppen` | `Cfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Paris) (CC BY-SA); confirm |
| `elevation_m` | 48 m, from Wikidata [Q90](https://www.wikidata.org/wiki/Q90) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10577](https://www.inaturalist.org/places/10577)
- iNaturalist place for the city (species lists): [99545](https://www.inaturalist.org/places/99545)
- GBIF GADM gid for the activity region: [`FRA.8_1`](https://www.gbif.org/occurrence/search?gadm_gid=FRA.8_1)
- GBIF country page: https://www.gbif.org/country/FR/summary
- OpenObs (INPN): https://openobs.mnhn.fr/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Paris) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region FR-IDF --inat-place-id 10577 --gbif-gadm-gid FRA.8_1 --write
```

### Candidate species (12; list at least 8)

6 of these already exist under `species/` (`turdus-merula`, `passer-domesticus`, `cyanistes-caeruleus`, `erithacus-rubecula`, `erinaceus-europaeus`, `bufo-bufo`); they still need a curve for `FR-IDF`.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Columba palumbus* | Common Wood-Pigeon | no | [2495455](https://www.gbif.org/species/2495455) | [3048](https://www.inaturalist.org/taxa/3048) |  |
| *Corvus corone* | Carrion Crow | no | [9409796](https://www.gbif.org/species/9409796) | [204496](https://www.inaturalist.org/taxa/204496) |  |
| *Turdus merula* | Eurasian Blackbird | yes (`turdus-merula`) | [2490719](https://www.gbif.org/species/2490719) | [12716](https://www.inaturalist.org/taxa/12716) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Cyanistes caeruleus* | Eurasian Blue Tit | yes (`cyanistes-caeruleus`) | [2487879](https://www.gbif.org/species/2487879) | [144849](https://www.inaturalist.org/taxa/144849) |  |
| *Erithacus rubecula* | European Robin | yes (`erithacus-rubecula`) | [2492462](https://www.gbif.org/species/2492462) | [13094](https://www.inaturalist.org/taxa/13094) |  |
| *Psittacula krameri* | Rose-ringed Parakeet | no | [2479226](https://www.gbif.org/species/2479226) | [18911](https://www.inaturalist.org/taxa/18911) |  |
| *Parus major* | Great Tit | no | [9705453](https://www.gbif.org/species/9705453) | [203153](https://www.inaturalist.org/taxa/203153) |  |
| *Erinaceus europaeus* | Common Hedgehog | yes (`erinaceus-europaeus`) | [5219616](https://www.gbif.org/species/5219616) | [43042](https://www.inaturalist.org/taxa/43042) |  |
| *Podarcis muralis* | Common Wall Lizard | no | [2469188](https://www.gbif.org/species/2469188) | [55990](https://www.inaturalist.org/taxa/55990) |  |
| *Pipistrellus pipistrellus* | Common Pipistrelle | no | [5218465](https://www.gbif.org/species/5218465) | [40364](https://www.inaturalist.org/taxa/40364) |  |
| *Bufo bufo* | European Toad | yes (`bufo-bufo`) | [5217160](https://www.gbif.org/species/5217160) | [326296](https://www.inaturalist.org/taxa/326296) |  |

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/paris-fr/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `FR-IDF`
- [ ] `uv run tools/validate.py --locale paris-fr --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Paris courtyard (paris-fr)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
