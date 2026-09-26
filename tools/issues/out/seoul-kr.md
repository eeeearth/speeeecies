<!-- title: Locale: A Seoul apartment green (seoul-kr) -->
**A Seoul apartment green**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/seoul-kr/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `seoul-kr` |
| `name` | A Seoul apartment green |
| `country` | `KR` |
| `activity_region` | `KR-11` (Seoul) |
| `public_lat`, `public_lon` | 37.56, 126.99: the public city centroid from Wikidata [Q8684](https://www.wikidata.org/wiki/Q8684) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Asia/Seoul` |
| `koppen` | `Dwa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Seoul) (CC BY-SA); confirm |
| `elevation_m` | 38 m, from Wikidata [Q8684](https://www.wikidata.org/wiki/Q8684) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [11005](https://www.inaturalist.org/places/11005)
- iNaturalist place for the city (species lists): [35673](https://www.inaturalist.org/places/35673)
- GBIF GADM gid for the activity region: [`KOR.16_1`](https://www.gbif.org/occurrence/search?gadm_gid=KOR.16_1)
- GBIF country page: https://www.gbif.org/country/KR/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Seoul) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region KR-11 --inat-place-id 11005 --gbif-gadm-gid KOR.16_1 --write
```

### Candidate species (12; list at least 8)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Pica serica* | Oriental Magpie | no | [10704098](https://www.gbif.org/species/10704098) | [827401](https://www.inaturalist.org/taxa/827401) |  |
| *Hypsipetes amaurotis* | Brown-eared Bulbul | no | [7342055](https://www.gbif.org/species/7342055) | [144910](https://www.inaturalist.org/taxa/144910) |  |
| *Streptopelia orientalis* | Oriental Turtle-Dove | no | [2495681](https://www.gbif.org/species/2495681) | [2927](https://www.inaturalist.org/taxa/2927) |  |
| *Passer montanus* | Eurasian Tree Sparrow | no | [5231198](https://www.gbif.org/species/5231198) | [13851](https://www.inaturalist.org/taxa/13851) |  |
| *Parus minor* | Asian Tit | no | [5844847](https://www.gbif.org/species/5844847) | [339691](https://www.inaturalist.org/taxa/339691) | iNaturalist lumps it into Parus cinereus (Asian tit) |
| *Cyanopica cyanus* | Azure-winged Magpie | no | [7341881](https://www.gbif.org/species/7341881) | [72785](https://www.inaturalist.org/taxa/72785) |  |
| *Corvus macrorhynchos* | Large-billed Crow | no | [2482487](https://www.gbif.org/species/2482487) | [8026](https://www.inaturalist.org/taxa/8026) |  |
| *Sciurus vulgaris* | Eurasian Red Squirrel | no | [8211070](https://www.gbif.org/species/8211070) | [46001](https://www.inaturalist.org/taxa/46001) |  |
| *Nyctereutes procyonoides* | Mainland Raccoon Dog | no | [2434552](https://www.gbif.org/species/2434552) | [855311](https://www.inaturalist.org/taxa/855311) |  |
| *Tamias sibiricus* | Siberian Chipmunk | no | [2437450](https://www.gbif.org/species/2437450) | [520585](https://www.inaturalist.org/taxa/520585) | iNaturalist uses Eutamias sibiricus |
| *Dryophytes japonicus* | Japanese Tree Frog | no | [10857535](https://www.gbif.org/species/10857535) | [1668965](https://www.inaturalist.org/taxa/1668965) |  |
| *Pelophylax nigromaculatus* | Black-spotted Frog | no | [2426634](https://www.gbif.org/species/2426634) | [66330](https://www.inaturalist.org/taxa/66330) |  |

### Notes

- There is no apartment-green template; `courtyard` is the closest generic plot.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/seoul-kr/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `KR-11`
- [ ] `uv run tools/validate.py --locale seoul-kr --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Seoul apartment green (seoul-kr)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
