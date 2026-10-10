<!-- title: Locale: A Tulsa street (ok-tulsa) -->
**A Tulsa street**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/ok-tulsa/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `ok-tulsa` |
| `name` | A Tulsa street |
| `country` | `US` |
| `activity_region` | `US-OK` (Oklahoma) |
| `public_lat`, `public_lon` | 36.13, -95.94: the public city centroid from Wikidata [Q44989](https://www.wikidata.org/wiki/Q44989) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Chicago` |
| `koppen` | `Cfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Tulsa,_Oklahoma) (CC BY-SA); confirm |
| `elevation_m` | 223 m, from Wikidata [Q44989](https://www.wikidata.org/wiki/Q44989) `P2044` (CC0) |
| `plot_template` | `street-block` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [12](https://www.inaturalist.org/places/12)
- iNaturalist place for Tulsa County, for species lists: [2981](https://www.inaturalist.org/places/2981)
- GBIF GADM gid for the activity region: [`USA.37_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.37_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Tulsa,_Oklahoma) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-OK --inat-place-id 12 --gbif-gadm-gid USA.37_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`passer-domesticus`); they still need a curve for `US-OK`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Mimus polyglottos* | Northern Mockingbird | no | [5231677](https://www.gbif.org/species/5231677) | [14886](https://www.inaturalist.org/taxa/14886) |  |
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Quiscalus mexicanus* | Great-tailed Grackle | no | [9476062](https://www.gbif.org/species/9476062) | [9607](https://www.inaturalist.org/taxa/9607) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Cyanocitta cristata* | Blue Jay | no | [2482593](https://www.gbif.org/species/2482593) | [8229](https://www.inaturalist.org/taxa/8229) |  |
| *Tyrannus forficatus* | Scissor-tailed Flycatcher | no | [5229687](https://www.gbif.org/species/5229687) | [16783](https://www.inaturalist.org/taxa/16783) |  |
| *Ictinia mississippiensis* | Mississippi Kite | no | [2480719](https://www.gbif.org/species/2480719) | [5416](https://www.inaturalist.org/taxa/5416) |  |
| *Sciurus niger* | Eastern Fox Squirrel | no | [5219683](https://www.gbif.org/species/5219683) | [46020](https://www.inaturalist.org/taxa/46020) |  |
| *Didelphis virginiana* | Virginia Opossum | no | [2439923](https://www.gbif.org/species/2439923) | [42652](https://www.inaturalist.org/taxa/42652) |  |
| *Mus musculus* | House Mouse | no | [7429082](https://www.gbif.org/species/7429082) | [44705](https://www.inaturalist.org/taxa/44705) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Hemidactylus turcicus* | Mediterranean House Gecko | no | [5221528](https://www.gbif.org/species/5221528) | [34435](https://www.inaturalist.org/taxa/34435) |  |

### Notes

- The Mediterranean house gecko is introduced here.

### Plants

Ship `locales/ok-tulsa/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/ok-tulsa/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-OK`
- [ ] `locales/ok-tulsa/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale ok-tulsa --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Tulsa street (ok-tulsa)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
