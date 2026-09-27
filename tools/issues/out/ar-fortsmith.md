<!-- title: Locale: A Fort Smith street (ar-fortsmith) -->
**A Fort Smith street**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/ar-fortsmith/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `ar-fortsmith` |
| `name` | A Fort Smith street |
| `country` | `US` |
| `activity_region` | `US-AR` (Arkansas) |
| `public_lat`, `public_lon` | 35.35, -94.37: the public city centroid from Wikidata [Q79535](https://www.wikidata.org/wiki/Q79535) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Chicago` |
| `koppen` | `Cfa`, [Wikipedia](https://en.wikipedia.org/wiki/Fort_Smith,_Arkansas) (CC BY-SA) describes a humid subtropical climate without giving the code; confirm |
| `elevation_m` | 141 m, from Wikidata [Q79535](https://www.wikidata.org/wiki/Q79535) `P2044` (CC0) |
| `plot_template` | `street-block` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [36](https://www.inaturalist.org/places/36)
- iNaturalist place for Sebastian County, for species lists: [2016](https://www.inaturalist.org/places/2016)
- GBIF GADM gid for the activity region: [`USA.4_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.4_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the source named in the table above or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-AR --inat-place-id 36 --gbif-gadm-gid USA.4_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`passer-domesticus`); they still need a curve for `US-AR`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Mimus polyglottos* | Northern Mockingbird | no | [5231677](https://www.gbif.org/species/5231677) | [14886](https://www.inaturalist.org/taxa/14886) |  |
| *Cyanocitta cristata* | Blue Jay | no | [2482593](https://www.gbif.org/species/2482593) | [8229](https://www.inaturalist.org/taxa/8229) |  |
| *Thryothorus ludovicianus* | Carolina Wren | no | [2493801](https://www.gbif.org/species/2493801) | [7513](https://www.inaturalist.org/taxa/7513) |  |
| *Tyrannus forficatus* | Scissor-tailed Flycatcher | no | [5229687](https://www.gbif.org/species/5229687) | [16783](https://www.inaturalist.org/taxa/16783) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Sciurus niger* | Eastern Fox Squirrel | no | [5219683](https://www.gbif.org/species/5219683) | [46020](https://www.inaturalist.org/taxa/46020) |  |
| *Didelphis virginiana* | Virginia Opossum | no | [2439923](https://www.gbif.org/species/2439923) | [42652](https://www.inaturalist.org/taxa/42652) |  |
| *Mephitis mephitis* | Striped Skunk | no | [5219380](https://www.gbif.org/species/5219380) | [41880](https://www.inaturalist.org/taxa/41880) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Terrapene triunguis* | Three-toed Box Turtle | no | [8877412](https://www.gbif.org/species/8877412) | [1544605](https://www.inaturalist.org/taxa/1544605) |  |

### Notes

- Bat records are sparse here (single research-grade observations of four species in the county).

### Plants

Ship `locales/ar-fortsmith/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/ar-fortsmith/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-AR`
- [ ] `locales/ar-fortsmith/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale ar-fortsmith --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Fort Smith street (ar-fortsmith)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
