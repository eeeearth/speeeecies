<!-- title: Locale: A Cape Town garden (capetown-za) -->
**A Cape Town garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/capetown-za/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `capetown-za` |
| `name` | A Cape Town garden |
| `country` | `ZA` |
| `activity_region` | `ZA-WC` (Western Cape) |
| `public_lat`, `public_lon` | -33.93, 18.42: the public city centroid from Wikidata [Q5465](https://www.wikidata.org/wiki/Q5465) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Africa/Johannesburg` |
| `koppen` | `Csb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Cape_Town) (CC BY-SA); confirm |
| `elevation_m` | 5 m, from Wikidata [Q5465](https://www.wikidata.org/wiki/Q5465) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [6987](https://www.inaturalist.org/places/6987)
- iNaturalist place for the city (species lists): [52355](https://www.inaturalist.org/places/52355)
- GBIF GADM gid for the activity region: [`ZAF.9_1`](https://www.gbif.org/occurrence/search?gadm_gid=ZAF.9_1)
- GBIF country page: https://www.gbif.org/country/ZA/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Cape_Town) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region ZA-WC --inat-place-id 6987 --gbif-gadm-gid ZAF.9_1 --write
```

### Candidate species (12; list at least 8)

1 of these already exist under `species/` (`sciurus-carolinensis`); they still need a curve for `ZA-WC`.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Bostrychia hagedash* | Hadada Ibis | no | [5229203](https://www.gbif.org/species/5229203) | [3743](https://www.inaturalist.org/taxa/3743) |  |
| *Cinnyris chalybeus* | Southern Double-collared Sunbird | no | [7340753](https://www.gbif.org/species/7340753) | [145157](https://www.inaturalist.org/taxa/145157) |  |
| *Onychognathus morio* | Red-winged Starling | no | [5230739](https://www.gbif.org/species/5230739) | [204554](https://www.inaturalist.org/taxa/204554) |  |
| *Pycnonotus capensis* | Cape Bulbul | no | [2486138](https://www.gbif.org/species/2486138) | [14594](https://www.inaturalist.org/taxa/14594) |  |
| *Numida meleagris* | Helmeted Guineafowl | no | [2473341](https://www.gbif.org/species/2473341) | [1428](https://www.inaturalist.org/taxa/1428) |  |
| *Alopochen aegyptiaca* | Egyptian Goose | no | [2498252](https://www.gbif.org/species/2498252) | [72486](https://www.inaturalist.org/taxa/72486) |  |
| *Spilopelia senegalensis* | Laughing Dove | no | [6101223](https://www.gbif.org/species/6101223) | [1455922](https://www.inaturalist.org/taxa/1455922) |  |
| *Zosterops virens* | Cape White-eye | no | [7857709](https://www.gbif.org/species/7857709) | [472770](https://www.inaturalist.org/taxa/472770) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Procavia capensis* | Rock Hyrax | no | [5219598](https://www.gbif.org/species/5219598) | [43086](https://www.inaturalist.org/taxa/43086) |  |
| *Sclerophrys pantherina* | Western Leopard Toad | no | [10851350](https://www.gbif.org/species/10851350) | [517449](https://www.inaturalist.org/taxa/517449) |  |
| *Bradypodion pumilum* | Cape Dwarf Chameleon | no | [8683892](https://www.gbif.org/species/8683892) | [32954](https://www.inaturalist.org/taxa/32954) |  |

### Notes

- Wikidata's elevation is the city centre at sea level; the suburbs climb Table Mountain's slopes.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/capetown-za/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `ZA-WC`
- [ ] `uv run tools/validate.py --locale capetown-za --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Cape Town garden (capetown-za)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
