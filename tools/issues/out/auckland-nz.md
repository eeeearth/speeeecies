<!-- title: Locale: An Auckland garden (auckland-nz) -->
**An Auckland garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/auckland-nz/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `auckland-nz` |
| `name` | An Auckland garden |
| `country` | `NZ` |
| `activity_region` | `NZ-AUK` (Auckland) |
| `public_lat`, `public_lon` | -36.85, 174.77: the public city centroid from Wikidata [Q37100](https://www.wikidata.org/wiki/Q37100) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Pacific/Auckland` |
| `koppen` | `Cfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Auckland) (CC BY-SA); confirm |
| `elevation_m` | 196 m, from Wikidata [Q37100](https://www.wikidata.org/wiki/Q37100) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [8345](https://www.inaturalist.org/places/8345)
- GBIF GADM gid for the activity region: [`NZL.1_1`](https://www.gbif.org/occurrence/search?gadm_gid=NZL.1_1)
- GBIF country page: https://www.gbif.org/country/NZ/summary
- iNaturalist NZ: https://inaturalist.nz/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Auckland) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region NZ-AUK --inat-place-id 8345 --gbif-gadm-gid NZL.1_1 --write
```

### Candidate species (12; list at least 8)

On 2026-09-26, 3 of these existed under `species/` (`turdus-merula`, `passer-domesticus`, `erinaceus-europaeus`); they still need a curve for `NZ-AUK`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Prosthemadera novaeseelandiae* | Tūī | no | [2487029](https://www.gbif.org/species/2487029) | [12580](https://www.inaturalist.org/taxa/12580) |  |
| *Hemiphaga novaeseelandiae* | New Zealand Pigeon | no | [2495905](https://www.gbif.org/species/2495905) | [204520](https://www.inaturalist.org/taxa/204520) |  |
| *Rhipidura fuliginosa* | New Zealand Fantail | no | [5231730](https://www.gbif.org/species/5231730) | [244276](https://www.inaturalist.org/taxa/244276) |  |
| *Todiramphus sanctus* | Sacred Kingfisher | no | [2475802](https://www.gbif.org/species/2475802) | [2464](https://www.inaturalist.org/taxa/2464) |  |
| *Zosterops lateralis* | Silvereye | no | [2489396](https://www.gbif.org/species/2489396) | [202505](https://www.inaturalist.org/taxa/202505) |  |
| *Turdus merula* | Eurasian Blackbird | yes (`turdus-merula`) | [2490719](https://www.gbif.org/species/2490719) | [12716](https://www.inaturalist.org/taxa/12716) |  |
| *Acridotheres tristis* | Common Myna | no | [2489005](https://www.gbif.org/species/2489005) | [204454](https://www.inaturalist.org/taxa/204454) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Erinaceus europaeus* | Common Hedgehog | yes (`erinaceus-europaeus`) | [5219616](https://www.gbif.org/species/5219616) | [43042](https://www.inaturalist.org/taxa/43042) |  |
| *Trichosurus vulpecula* | Common Brushtail Possum | no | [2440254](https://www.gbif.org/species/2440254) | [42808](https://www.inaturalist.org/taxa/42808) |  |
| *Lampropholis delicata* | Dark-flecked Garden Sunskink | no | [5225256](https://www.gbif.org/species/5225256) | [38293](https://www.inaturalist.org/taxa/38293) |  |
| *Ranoidea aurea* | Green-and-Golden Bell Frog | no | [10595763](https://www.gbif.org/species/10595763) | [517069](https://www.inaturalist.org/taxa/517069) |  |

### Notes

- Wikidata's elevation (196 m) looks high for the city centre; confirm it against another public source.
- Hedgehogs, possums, mynas and the garden skink are introduced in New Zealand.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/auckland-nz/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `NZ-AUK`
- [ ] `uv run tools/validate.py --locale auckland-nz --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: An Auckland garden (auckland-nz)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
