<!-- title: Locale: A Santiago garden (santiago-cl) -->
**A Santiago garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/santiago-cl/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `santiago-cl` |
| `name` | A Santiago garden |
| `country` | `CL` |
| `activity_region` | `CL-RM` (Santiago Metropolitan Region) |
| `public_lat`, `public_lon` | -33.44, -70.65: the public city centroid from Wikidata [Q2887](https://www.wikidata.org/wiki/Q2887) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Santiago` |
| `koppen` | `Csb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Santiago) (CC BY-SA); confirm |
| `elevation_m` | 575 m, from Wikidata [Q2887](https://www.wikidata.org/wiki/Q2887) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [12691](https://www.inaturalist.org/places/12691)
- iNaturalist place for the city (species lists): [27738](https://www.inaturalist.org/places/27738)
- GBIF GADM gid for the activity region: [`CHL.14_1`](https://www.gbif.org/occurrence/search?gadm_gid=CHL.14_1)
- GBIF country page: https://www.gbif.org/country/CL/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Santiago) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region CL-RM --inat-place-id 12691 --gbif-gadm-gid CHL.14_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`passer-domesticus`); they still need a curve for `CL-RM`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus falcklandii* | Austral Thrush | no | [2490775](https://www.gbif.org/species/2490775) | [12751](https://www.inaturalist.org/taxa/12751) |  |
| *Zenaida auriculata* | Eared Dove | no | [2495358](https://www.gbif.org/species/2495358) | [3439](https://www.inaturalist.org/taxa/3439) |  |
| *Myiopsitta monachus* | Monk Parakeet | no | [2479407](https://www.gbif.org/species/2479407) | [19349](https://www.inaturalist.org/taxa/19349) |  |
| *Mimus thenca* | Chilean Mockingbird | no | [5231685](https://www.gbif.org/species/5231685) | [14879](https://www.inaturalist.org/taxa/14879) |  |
| *Zonotrichia capensis* | Rufous-collared Sparrow | no | [5231103](https://www.gbif.org/species/5231103) | [9183](https://www.inaturalist.org/taxa/9183) |  |
| *Milvago chimango* | Chimango Caracara | no | [2481065](https://www.gbif.org/species/2481065) | [1432781](https://www.inaturalist.org/taxa/1432781) | iNaturalist uses Daptrius chimango |
| *Curaeus curaeus* | Austral Blackbird | no | [2484424](https://www.gbif.org/species/2484424) | [10307](https://www.inaturalist.org/taxa/10307) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Vanellus chilensis* | Southern Lapwing | no | [5229146](https://www.gbif.org/species/5229146) | [4867](https://www.inaturalist.org/taxa/4867) |  |
| *Tadarida brasiliensis* | Mexican Free-tailed Bat | no | [2433011](https://www.gbif.org/species/2433011) | [41301](https://www.inaturalist.org/taxa/41301) |  |
| *Liolaemus tenuis* | Blue-Green Smooth-throated Lizard | no | [2460411](https://www.gbif.org/species/2460411) | [39111](https://www.inaturalist.org/taxa/39111) |  |
| *Pleurodema thaul* | Chilean Four-eyed Frog | no | [2423479](https://www.gbif.org/species/2423479) | [23214](https://www.inaturalist.org/taxa/23214) |  |

### Plants

Ship `locales/santiago-cl/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/santiago-cl/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `CL-RM`
- [ ] `locales/santiago-cl/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale santiago-cl --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Santiago garden (santiago-cl)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
