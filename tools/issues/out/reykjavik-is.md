<!-- title: Locale: A Reykjavík garden (reykjavik-is) -->
**A Reykjavík garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/reykjavik-is/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `reykjavik-is` |
| `name` | A Reykjavík garden |
| `country` | `IS` |
| `activity_region` | `IS-1` (Capital Region) |
| `public_lat`, `public_lon` | 64.15, -21.94: the public city centroid from Wikidata [Q1764](https://www.wikidata.org/wiki/Q1764) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Atlantic/Reykjavik` |
| `koppen` | `Cfc`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Reykjavík) (CC BY-SA); confirm |
| `elevation_m` | 8 m, from Wikidata [Q1764](https://www.wikidata.org/wiki/Q1764) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10868](https://www.inaturalist.org/places/10868)
- iNaturalist place for the city (species lists): [33029](https://www.inaturalist.org/places/33029)
- GBIF GADM gid for the activity region: [`ISL.3_1`](https://www.gbif.org/occurrence/search?gadm_gid=ISL.3_1)
- GBIF country page: https://www.gbif.org/country/IS/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Reykjavík) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region IS-1 --inat-place-id 10868 --gbif-gadm-gid ISL.3_1 --write
```

### Candidate species (12; list at least 8)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus iliacus* | Redwing | no | [2490781](https://www.gbif.org/species/2490781) | [12749](https://www.inaturalist.org/taxa/12749) |  |
| *Sturnus vulgaris* | European Starling | no | [9809229](https://www.gbif.org/species/9809229) | [14850](https://www.inaturalist.org/taxa/14850) |  |
| *Anas platyrhynchos* | Mallard | no | [9761484](https://www.gbif.org/species/9761484) | [6930](https://www.inaturalist.org/taxa/6930) |  |
| *Anser anser* | Greylag Goose | no | [2498036](https://www.gbif.org/species/2498036) | [7018](https://www.inaturalist.org/taxa/7018) |  |
| *Chroicocephalus ridibundus* | Black-headed Gull | no | [6065824](https://www.gbif.org/species/6065824) | [144510](https://www.inaturalist.org/taxa/144510) |  |
| *Corvus corax* | Common Raven | no | [2482492](https://www.gbif.org/species/2482492) | [8010](https://www.inaturalist.org/taxa/8010) |  |
| *Troglodytes troglodytes* | Eurasian Wren | no | [5231438](https://www.gbif.org/species/5231438) | [145363](https://www.inaturalist.org/taxa/145363) |  |
| *Acanthis flammea* | Redpoll | no | [5231630](https://www.gbif.org/species/5231630) | [145300](https://www.inaturalist.org/taxa/145300) |  |
| *Plectrophenax nivalis* | Snow Bunting | no | [2491719](https://www.gbif.org/species/2491719) | [117059](https://www.inaturalist.org/taxa/117059) |  |
| *Oryctolagus cuniculus* | European Rabbit | no | [2436940](https://www.gbif.org/species/2436940) | [43151](https://www.inaturalist.org/taxa/43151) |  |
| *Mus musculus* | House Mouse | no | [7429082](https://www.gbif.org/species/7429082) | [44705](https://www.inaturalist.org/taxa/44705) |  |
| *Vulpes lagopus* | Arctic Fox | no | [5219303](https://www.gbif.org/species/5219303) | [233598](https://www.inaturalist.org/taxa/233598) |  |

### Notes

- Iceland has no native amphibians or reptiles, so this list is birds and mammals.
- Arctic foxes are rare inside the city; list one only if a source supports it.
- Reykjavík sits on the Cfc/Dfc boundary; Wikipedia gives Cfc.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/reykjavik-is/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `IS-1`
- [ ] `uv run tools/validate.py --locale reykjavik-is --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Reykjavík garden (reykjavik-is)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
