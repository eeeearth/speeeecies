<!-- title: Locale: An Accra compound (accra-gh) -->
**An Accra compound**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/accra-gh/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `accra-gh` |
| `name` | An Accra compound |
| `country` | `GH` |
| `activity_region` | `GH-AA` (Greater Accra) |
| `public_lat`, `public_lon` | 5.56, -0.20: the public city centroid from Wikidata [Q3761](https://www.wikidata.org/wiki/Q3761) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Africa/Accra` |
| `koppen` | `Aw`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Accra) (CC BY-SA); confirm |
| `elevation_m` | 61 m, from Wikidata [Q3761](https://www.wikidata.org/wiki/Q3761) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10621](https://www.inaturalist.org/places/10621)
- iNaturalist place for the city (species lists): [30642](https://www.inaturalist.org/places/30642)
- GBIF GADM gid for the activity region: [`GHA7_2`](https://www.gbif.org/occurrence/search?gadm_gid=GHA7_2)
- GBIF country page: https://www.gbif.org/country/GH/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Accra) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region GH-AA --inat-place-id 10621 --gbif-gadm-gid GHA7_2 --write
```

### Candidate species (11; list at least 8)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Crinifer piscator* | Western Plantain-eater | no | [2475211](https://www.gbif.org/species/2475211) | [7248](https://www.inaturalist.org/taxa/7248) |  |
| *Corvinella corvina* | Yellow-billed Shrike | no | [5231300](https://www.gbif.org/species/5231300) | [12057](https://www.inaturalist.org/taxa/12057) |  |
| *Spilopelia senegalensis* | Laughing Dove | no | [6101223](https://www.gbif.org/species/6101223) | [1455922](https://www.inaturalist.org/taxa/1455922) |  |
| *Corvus albus* | Pied Crow | no | [2482519](https://www.gbif.org/species/2482519) | [8038](https://www.inaturalist.org/taxa/8038) |  |
| *Lophoceros nasutus* | African Gray Hornbill | no | [8101752](https://www.gbif.org/species/8101752) | [512166](https://www.inaturalist.org/taxa/512166) |  |
| *Centropus senegalensis* | Senegal Coucal | no | [5231999](https://www.gbif.org/species/5231999) | [1670](https://www.inaturalist.org/taxa/1670) |  |
| *Bubulcus ibis* | Western Cattle-Egret | no | [2480830](https://www.gbif.org/species/2480830) | [411086](https://www.inaturalist.org/taxa/411086) | iNaturalist uses Ardea ibis |
| *Ploceus cucullatus* | Village Weaver | no | [2494058](https://www.gbif.org/species/2494058) | [13796](https://www.inaturalist.org/taxa/13796) |  |
| *Eidolon helvum* | Straw-coloured Fruit Bat | no | [2432851](https://www.gbif.org/species/2432851) | [40827](https://www.inaturalist.org/taxa/40827) |  |
| *Agama picticauda* | Peters's Rock Agama | no | [5226316](https://www.gbif.org/species/5226316) | [797597](https://www.inaturalist.org/taxa/797597) |  |
| *Sclerophrys regularis* | Egyptian Toad | no | [10698146](https://www.gbif.org/species/10698146) | [517048](https://www.inaturalist.org/taxa/517048) |  |

### Notes

- Observations are sparse here (tens per species on iNaturalist); `fetch_activity.py` may fall back to the country (GH) or mark curves low-confidence. Say so in the PR.
- Accra's climate is on the Aw/BSh boundary; confirm the class.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/accra-gh/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `GH-AA`
- [ ] `uv run tools/validate.py --locale accra-gh --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: An Accra compound (accra-gh)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
