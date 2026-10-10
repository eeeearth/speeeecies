<!-- title: Locale: A Tokyo suburb (setagaya-jp) -->
**A Tokyo suburb**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/setagaya-jp/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `setagaya-jp` |
| `name` | A Tokyo suburb |
| `country` | `JP` |
| `activity_region` | `JP-13` (Tokyo) |
| `public_lat`, `public_lon` | 35.65, 139.65: the public city centroid from Wikidata [Q231645](https://www.wikidata.org/wiki/Q231645) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Asia/Tokyo` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Setagaya) (CC BY-SA); confirm |
| `elevation_m` | to confirm (Wikidata [Q231645](https://www.wikidata.org/wiki/Q231645) has no elevation) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10935](https://www.inaturalist.org/places/10935)
- iNaturalist place for the city (species lists): [34917](https://www.inaturalist.org/places/34917)
- GBIF GADM gid for the activity region: [`JPN.41_1`](https://www.gbif.org/occurrence/search?gadm_gid=JPN.41_1)
- GBIF country page: https://www.gbif.org/country/JP/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Setagaya) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region JP-13 --inat-place-id 10935 --gbif-gadm-gid JPN.41_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Passer montanus* | Eurasian Tree Sparrow | no | [5231198](https://www.gbif.org/species/5231198) | [13851](https://www.inaturalist.org/taxa/13851) |  |
| *Hypsipetes amaurotis* | Brown-eared Bulbul | no | [7342055](https://www.gbif.org/species/7342055) | [144910](https://www.inaturalist.org/taxa/144910) |  |
| *Spodiopsar cineraceus* | White-cheeked Starling | no | [6100944](https://www.gbif.org/species/6100944) | [547179](https://www.inaturalist.org/taxa/547179) |  |
| *Streptopelia orientalis* | Oriental Turtle-Dove | no | [2495681](https://www.gbif.org/species/2495681) | [2927](https://www.inaturalist.org/taxa/2927) |  |
| *Corvus macrorhynchos* | Large-billed Crow | no | [2482487](https://www.gbif.org/species/2482487) | [8026](https://www.inaturalist.org/taxa/8026) |  |
| *Parus minor* | Asian Tit | no | [5844847](https://www.gbif.org/species/5844847) | [339691](https://www.inaturalist.org/taxa/339691) | iNaturalist lumps it into Parus cinereus (Asian tit) |
| *Zosterops japonicus* | Warbling White-eye | no | [9300456](https://www.gbif.org/species/9300456) | [980262](https://www.inaturalist.org/taxa/980262) |  |
| *Corvus corone* | Carrion Crow | no | [9409796](https://www.gbif.org/species/9409796) | [204496](https://www.inaturalist.org/taxa/204496) |  |
| *Nyctereutes viverrinus* | Japanese Raccoon Dog | no | [6164330](https://www.gbif.org/species/6164330) | [855310](https://www.inaturalist.org/taxa/855310) | GBIF treats it as Nyctereutes procyonoides viverrinus |
| *Bufo japonicus* | Eastern-Japanese Common Toad | no | [5217143](https://www.gbif.org/species/5217143) | [1402613](https://www.inaturalist.org/taxa/1402613) | iNaturalist splits the eastern Japanese population as Bufo formosus; use that taxon id for activity |
| *Plestiodon finitimus* | Japanese five-lined skink | no | [8186233](https://www.gbif.org/species/8186233) | [318747](https://www.inaturalist.org/taxa/318747) |  |
| *Gekko japonicus* | Japanese Giant Gecko | no | [2447295](https://www.gbif.org/species/2447295) | [101316](https://www.inaturalist.org/taxa/101316) |  |

### Notes

- Wikidata has no elevation for Setagaya; take one from a public source and cite it.

### Plants

Ship `locales/setagaya-jp/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/setagaya-jp/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `JP-13`
- [ ] `locales/setagaya-jp/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale setagaya-jp --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Tokyo suburb (setagaya-jp)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
