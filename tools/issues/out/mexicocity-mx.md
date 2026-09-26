<!-- title: Locale: A Mexico City rooftop garden (mexicocity-mx) -->
**A Mexico City rooftop garden**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/mexicocity-mx/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `mexicocity-mx` |
| `name` | A Mexico City rooftop garden |
| `country` | `MX` |
| `activity_region` | `MX-CMX` (Mexico City) |
| `public_lat`, `public_lon` | 19.35, -99.14: the public city centroid from Wikidata [Q1489](https://www.wikidata.org/wiki/Q1489) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Mexico_City` |
| `koppen` | `Cwb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Mexico_City) (CC BY-SA); confirm |
| `elevation_m` | 2240 m, from Wikidata [Q1489](https://www.wikidata.org/wiki/Q1489) `P2044` (CC0) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [59014](https://www.inaturalist.org/places/59014)
- iNaturalist place for the city (species lists): [101739](https://www.inaturalist.org/places/101739)
- GBIF GADM gid for the activity region: [`MEX.9_1`](https://www.gbif.org/occurrence/search?gadm_gid=MEX.9_1)
- GBIF country page: https://www.gbif.org/country/MX/summary
- NaturaLista (CONABIO): https://www.naturalista.mx/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Mexico_City) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region MX-CMX --inat-place-id 59014 --gbif-gadm-gid MEX.9_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`passer-domesticus`); they still need a curve for `MX-CMX`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Columbina inca* | Inca Dove | no | [2495863](https://www.gbif.org/species/2495863) | [3544](https://www.inaturalist.org/taxa/3544) |  |
| *Haemorhous mexicanus* | House Finch | no | [8323485](https://www.gbif.org/species/8323485) | [199840](https://www.inaturalist.org/taxa/199840) |  |
| *Quiscalus mexicanus* | Great-tailed Grackle | no | [9476062](https://www.gbif.org/species/9476062) | [9607](https://www.inaturalist.org/taxa/9607) |  |
| *Pyrocephalus rubinus* | Vermilion Flycatcher | no | [2483647](https://www.gbif.org/species/2483647) | [16447](https://www.inaturalist.org/taxa/16447) |  |
| *Saucerottia beryllina* | Berylline Hummingbird | no | [5788537](https://www.gbif.org/species/5788537) | [1289657](https://www.inaturalist.org/taxa/1289657) |  |
| *Turdus rufopalliatus* | Rufous-backed Robin | no | [2490741](https://www.gbif.org/species/2490741) | [12714](https://www.inaturalist.org/taxa/12714) |  |
| *Melozone fusca* | Canyon Towhee | no | [7341622](https://www.gbif.org/species/7341622) | [145289](https://www.inaturalist.org/taxa/145289) |  |
| *Sciurus aureogaster* | Red-bellied Squirrel | no | [5219663](https://www.gbif.org/species/5219663) | [46009](https://www.inaturalist.org/taxa/46009) |  |
| *Didelphis virginiana* | Virginia Opossum | no | [2439923](https://www.gbif.org/species/2439923) | [42652](https://www.inaturalist.org/taxa/42652) |  |
| *Bassariscus astutus* | Ringtail | no | [2433557](https://www.gbif.org/species/2433557) | [41676](https://www.inaturalist.org/taxa/41676) |  |
| *Sceloporus grammicus* | Graphic Spiny Lizard | no | [2451167](https://www.gbif.org/species/2451167) | [36262](https://www.inaturalist.org/taxa/36262) |  |

### Notes

- There is no rooftop template; `courtyard` is the closest generic plot.
- Wikidata's coordinate lies south of the historic centre; any public city-level centroid is fine.
- The city iNaturalist place above is Coyoacán; use the subdivision place for activity curves.

### Plants

Ship `locales/mexicocity-mx/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/mexicocity-mx/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `MX-CMX`
- [ ] `locales/mexicocity-mx/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale mexicocity-mx --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Mexico City rooftop garden (mexicocity-mx)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
