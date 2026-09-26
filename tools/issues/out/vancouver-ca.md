<!-- title: Locale: A Vancouver lot (vancouver-ca) -->
**A Vancouver lot**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/vancouver-ca/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `vancouver-ca` |
| `name` | A Vancouver lot |
| `country` | `CA` |
| `activity_region` | `CA-BC` (British Columbia) |
| `public_lat`, `public_lon` | 49.26, -123.11: the public city centroid from Wikidata [Q24639](https://www.wikidata.org/wiki/Q24639) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Vancouver` |
| `koppen` | `Cfb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Vancouver) (CC BY-SA); confirm |
| `elevation_m` | 2 m, from Wikidata [Q24639](https://www.wikidata.org/wiki/Q24639) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [7085](https://www.inaturalist.org/places/7085)
- iNaturalist place for the city (species lists): [27530](https://www.inaturalist.org/places/27530)
- GBIF GADM gid for the activity region: [`CAN.2_1`](https://www.gbif.org/occurrence/search?gadm_gid=CAN.2_1)
- GBIF country page: https://www.gbif.org/country/CA/summary
- iNaturalist.ca: https://inaturalist.ca/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Vancouver) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region CA-BC --inat-place-id 7085 --gbif-gadm-gid CAN.2_1 --write
```

### Candidate species (12; list at least 8)

On 2026-09-26, 1 of these existed under `species/` (`sciurus-carolinensis`); they still need a curve for `CA-BC`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Corvus brachyrhynchos* | American Crow | no | [2482507](https://www.gbif.org/species/2482507) | [8021](https://www.inaturalist.org/taxa/8021) |  |
| *Melospiza melodia* | Song Sparrow | no | [2492196](https://www.gbif.org/species/2492196) | [9100](https://www.inaturalist.org/taxa/9100) |  |
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Pipilo maculatus* | Spotted Towhee | no | [9709230](https://www.gbif.org/species/9709230) | [9420](https://www.inaturalist.org/taxa/9420) |  |
| *Colaptes auratus* | Northern Flicker | no | [2478259](https://www.gbif.org/species/2478259) | [18236](https://www.inaturalist.org/taxa/18236) |  |
| *Calypte anna* | Anna's Hummingbird | no | [2476674](https://www.gbif.org/species/2476674) | [6317](https://www.inaturalist.org/taxa/6317) |  |
| *Poecile atricapillus* | Black-capped Chickadee | no | [2487805](https://www.gbif.org/species/2487805) | [144815](https://www.inaturalist.org/taxa/144815) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Procyon lotor* | Common Raccoon | no | [5218786](https://www.gbif.org/species/5218786) | [41663](https://www.inaturalist.org/taxa/41663) |  |
| *Tamiasciurus douglasii* | Douglas's Squirrel | no | [2437281](https://www.gbif.org/species/2437281) | [46259](https://www.inaturalist.org/taxa/46259) |  |
| *Pseudacris regilla* | Pacific chorus frog | no | [2428132](https://www.gbif.org/species/2428132) | [24259](https://www.inaturalist.org/taxa/24259) |  |
| *Thamnophis sirtalis* | Common Garter Snake | no | [2457522](https://www.gbif.org/species/2457522) | [28362](https://www.inaturalist.org/taxa/28362) |  |

### Notes

- Vancouver sits on the Cfb/Csb boundary; Wikipedia gives Cfb.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/vancouver-ca/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `CA-BC`
- [ ] `uv run tools/validate.py --locale vancouver-ca --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Vancouver lot (vancouver-ca)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
