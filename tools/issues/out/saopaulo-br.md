<!-- title: Locale: A São Paulo courtyard (saopaulo-br) -->
**A São Paulo courtyard**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/saopaulo-br/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `saopaulo-br` |
| `name` | A São Paulo courtyard |
| `country` | `BR` |
| `activity_region` | `BR-SP` (São Paulo) |
| `public_lat`, `public_lon` | -23.55, -46.63: the public city centroid from Wikidata [Q174](https://www.wikidata.org/wiki/Q174) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Sao_Paulo` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/São_Paulo) (CC BY-SA); confirm |
| `elevation_m` | 760 m, from Wikidata [Q174](https://www.wikidata.org/wiki/Q174) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [13334](https://www.inaturalist.org/places/13334)
- iNaturalist place for the city (species lists): [25311](https://www.inaturalist.org/places/25311)
- GBIF GADM gid for the activity region: [`BRA.25_1`](https://www.gbif.org/occurrence/search?gadm_gid=BRA.25_1)
- GBIF country page: https://www.gbif.org/country/BR/summary
- SiBBr, Brazil's biodiversity information system: https://www.sibbr.gov.br/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/São_Paulo) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region BR-SP --inat-place-id 13334 --gbif-gadm-gid BRA.25_1 --write
```

### Candidate species (12; list at least 8)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus rufiventris* | Rufous-bellied Thrush | no | [2490718](https://www.gbif.org/species/2490718) | [12738](https://www.inaturalist.org/taxa/12738) |  |
| *Pitangus sulphuratus* | Great Kiskadee | no | [2482755](https://www.gbif.org/species/2482755) | [16956](https://www.inaturalist.org/taxa/16956) |  |
| *Furnarius rufus* | Rufous Hornero | no | [2485821](https://www.gbif.org/species/2485821) | [11275](https://www.inaturalist.org/taxa/11275) |  |
| *Brotogeris tirica* | Plain Parakeet | no | [2479562](https://www.gbif.org/species/2479562) | [19214](https://www.inaturalist.org/taxa/19214) |  |
| *Thraupis sayaca* | Sayaca Tanager | no | [2488622](https://www.gbif.org/species/2488622) | [10293](https://www.inaturalist.org/taxa/10293) |  |
| *Columbina talpacoti* | Ruddy Ground Dove | no | [2495858](https://www.gbif.org/species/2495858) | [3580](https://www.inaturalist.org/taxa/3580) |  |
| *Callithrix penicillata* | Black-tufted-ear Marmoset | no | [5219541](https://www.gbif.org/species/5219541) | [43374](https://www.inaturalist.org/taxa/43374) |  |
| *Callithrix jacchus* | Common Marmoset | no | [5219542](https://www.gbif.org/species/5219542) | [43373](https://www.inaturalist.org/taxa/43373) |  |
| *Didelphis aurita* | Big-eared Opossum | no | [2439928](https://www.gbif.org/species/2439928) | [42657](https://www.inaturalist.org/taxa/42657) |  |
| *Salvator merianae* | Argentine Black-and-white Tegu | no | [5227370](https://www.gbif.org/species/5227370) | [318758](https://www.inaturalist.org/taxa/318758) |  |
| *Hemidactylus mabouia* | Tropical House Gecko | no | [5959942](https://www.gbif.org/species/5959942) | [68492](https://www.inaturalist.org/taxa/68492) |  |
| *Rhinella ornata* | Ornate Forest toad | no | [5216887](https://www.gbif.org/species/5216887) | [67135](https://www.inaturalist.org/taxa/67135) |  |

### Notes

- São Paulo sits on the Cfa/Cwa boundary; Wikipedia gives Cfa.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/saopaulo-br/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `BR-SP`
- [ ] `uv run tools/validate.py --locale saopaulo-br --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A São Paulo courtyard (saopaulo-br)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
