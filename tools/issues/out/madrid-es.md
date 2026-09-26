<!-- title: Locale: A Madrid courtyard (madrid-es) -->
**A Madrid courtyard**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/madrid-es/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `madrid-es` |
| `name` | A Madrid courtyard |
| `country` | `ES` |
| `activity_region` | `ES-MD` (Community of Madrid) |
| `public_lat`, `public_lon` | 40.42, -3.70: the public city centroid from Wikidata [Q2807](https://www.wikidata.org/wiki/Q2807) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Europe/Madrid` |
| `koppen` | `Csa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Madrid) (CC BY-SA); confirm |
| `elevation_m` | 663 m, from Wikidata [Q2807](https://www.wikidata.org/wiki/Q2807) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10543](https://www.inaturalist.org/places/10543)
- iNaturalist place for the city (species lists): [30028](https://www.inaturalist.org/places/30028)
- GBIF GADM gid for the activity region: [`ESP.8_1`](https://www.gbif.org/occurrence/search?gadm_gid=ESP.8_1)
- GBIF country page: https://www.gbif.org/country/ES/summary
- GBIF Spain: https://www.gbif.es/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Madrid) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region ES-MD --inat-place-id 10543 --gbif-gadm-gid ESP.8_1 --write
```

### Candidate species (12; list at least 8)

3 of these already exist under `species/` (`passer-domesticus`, `turdus-merula`, `erinaceus-europaeus`); they still need a curve for `ES-MD`.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Pica pica* | Eurasian Magpie | no | [5229490](https://www.gbif.org/species/5229490) | [891696](https://www.inaturalist.org/taxa/891696) |  |
| *Turdus merula* | Eurasian Blackbird | yes (`turdus-merula`) | [2490719](https://www.gbif.org/species/2490719) | [12716](https://www.inaturalist.org/taxa/12716) |  |
| *Columba palumbus* | Common Wood-Pigeon | no | [2495455](https://www.gbif.org/species/2495455) | [3048](https://www.inaturalist.org/taxa/3048) |  |
| *Myiopsitta monachus* | Monk Parakeet | no | [2479407](https://www.gbif.org/species/2479407) | [19349](https://www.inaturalist.org/taxa/19349) |  |
| *Sturnus unicolor* | Spotless Starling | no | [2489104](https://www.gbif.org/species/2489104) | [14849](https://www.inaturalist.org/taxa/14849) |  |
| *Apus apus* | Common Swift | no | [5228676](https://www.gbif.org/species/5228676) | [6638](https://www.inaturalist.org/taxa/6638) |  |
| *Serinus serinus* | European Serin | no | [2494200](https://www.gbif.org/species/2494200) | [9236](https://www.inaturalist.org/taxa/9236) |  |
| *Parus major* | Great Tit | no | [9705453](https://www.gbif.org/species/9705453) | [203153](https://www.inaturalist.org/taxa/203153) |  |
| *Erinaceus europaeus* | Common Hedgehog | yes (`erinaceus-europaeus`) | [5219616](https://www.gbif.org/species/5219616) | [43042](https://www.inaturalist.org/taxa/43042) |  |
| *Tarentola mauritanica* | Moorish Gecko | no | [2445034](https://www.gbif.org/species/2445034) | [33602](https://www.inaturalist.org/taxa/33602) |  |
| *Pelophylax perezi* | Iberian Green Frog | no | [2426658](https://www.gbif.org/species/2426658) | [66331](https://www.inaturalist.org/taxa/66331) |  |

### Notes

- Madrid sits on the Csa/BSk boundary; Wikipedia gives Csa.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/madrid-es/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `ES-MD`
- [ ] `uv run tools/validate.py --locale madrid-es --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Madrid courtyard (madrid-es)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
