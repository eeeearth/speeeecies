<!-- title: Locale: A Chiang Mai garden (chiangmai-th) -->
**A Chiang Mai garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/chiangmai-th/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `chiangmai-th` |
| `name` | A Chiang Mai garden |
| `country` | `TH` |
| `activity_region` | `TH-50` (Chiang Mai) |
| `public_lat`, `public_lon` | 18.79, 98.98: the public city centroid from Wikidata [Q52028](https://www.wikidata.org/wiki/Q52028) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Asia/Bangkok` |
| `koppen` | `Aw`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Chiang_Mai) (CC BY-SA); confirm |
| `elevation_m` | 310 m, from Wikidata [Q52028](https://www.wikidata.org/wiki/Q52028) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [13320](https://www.inaturalist.org/places/13320)
- iNaturalist place for the city (species lists): [45315](https://www.inaturalist.org/places/45315)
- GBIF GADM gid for the activity region: [`THA.10_1`](https://www.gbif.org/occurrence/search?gadm_gid=THA.10_1)
- GBIF country page: https://www.gbif.org/country/TH/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Chiang_Mai) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region TH-50 --inat-place-id 13320 --gbif-gadm-gid THA.10_1 --write
```

### Candidate species (12; list at least 8)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Pycnonotus jocosus* | Red-whiskered Bulbul | no | [2486151](https://www.gbif.org/species/2486151) | [14591](https://www.inaturalist.org/taxa/14591) |  |
| *Pycnonotus aurigaster* | Sooty-headed Bulbul | no | [2486121](https://www.gbif.org/species/2486121) | [14626](https://www.inaturalist.org/taxa/14626) |  |
| *Spilopelia chinensis* | Spotted Dove | no | [6101224](https://www.gbif.org/species/6101224) | [1455918](https://www.inaturalist.org/taxa/1455918) |  |
| *Acridotheres tristis* | Common Myna | no | [2489005](https://www.gbif.org/species/2489005) | [204454](https://www.inaturalist.org/taxa/204454) |  |
| *Copsychus saularis* | Oriental Magpie-Robin | no | [2492680](https://www.gbif.org/species/2492680) | [204491](https://www.inaturalist.org/taxa/204491) |  |
| *Passer montanus* | Eurasian Tree Sparrow | no | [5231198](https://www.gbif.org/species/5231198) | [13851](https://www.inaturalist.org/taxa/13851) |  |
| *Orthotomus sutorius* | Common Tailorbird | no | [2493028](https://www.gbif.org/species/2493028) | [15347](https://www.inaturalist.org/taxa/15347) |  |
| *Callosciurus finlaysonii* | Finlayson's Squirrel | no | [2437399](https://www.gbif.org/species/2437399) | [45949](https://www.inaturalist.org/taxa/45949) |  |
| *Tamiops mcclellandii* | Himalayan Striped Squirrel | no | [7261516](https://www.gbif.org/species/7261516) | [697692](https://www.inaturalist.org/taxa/697692) |  |
| *Duttaphrynus melanostictus* | Asian Common Toad | no | [2422538](https://www.gbif.org/species/2422538) | [62345](https://www.inaturalist.org/taxa/62345) |  |
| *Hemidactylus platyurus* | Flat-tailed House Gecko | no | [5816059](https://www.gbif.org/species/5816059) | [33376](https://www.inaturalist.org/taxa/33376) |  |
| *Calotes versicolor* | Indian Garden Lizard | no | [9125207](https://www.gbif.org/species/9125207) | [31281](https://www.inaturalist.org/taxa/31281) |  |

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/chiangmai-th/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `TH-50`
- [ ] `uv run tools/validate.py --locale chiangmai-th --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Chiang Mai garden (chiangmai-th)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
