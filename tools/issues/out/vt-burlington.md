<!-- title: Locale: A Burlington street (vt-burlington) -->
**A Burlington street**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/vt-burlington/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `vt-burlington` |
| `name` | A Burlington street |
| `country` | `US` |
| `activity_region` | `US-VT` (Vermont) |
| `public_lat`, `public_lon` | 44.48, -73.21: the public city centroid from Wikidata [Q31058](https://www.wikidata.org/wiki/Q31058) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/New_York` |
| `koppen` | `Dfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Burlington,_Vermont) (CC BY-SA); confirm |
| `elevation_m` | 61 m, from Wikidata [Q31058](https://www.wikidata.org/wiki/Q31058) `P2044` (CC0) |
| `plot_template` | `street-block` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [47](https://www.inaturalist.org/places/47)
- iNaturalist place for Chittenden County, for species lists: [1370](https://www.inaturalist.org/places/1370)
- GBIF GADM gid for the activity region: [`USA.46_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.46_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Burlington,_Vermont) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-VT --inat-place-id 47 --gbif-gadm-gid USA.46_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 2 of these existed under `species/` (`passer-domesticus`, `sciurus-carolinensis`); they still need a curve for `US-VT`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Poecile atricapillus* | Black-capped Chickadee | no | [2487805](https://www.gbif.org/species/2487805) | [144815](https://www.inaturalist.org/taxa/144815) |  |
| *Cardinalis cardinalis* | Northern Cardinal | no | [2490384](https://www.gbif.org/species/2490384) | [9083](https://www.inaturalist.org/taxa/9083) |  |
| *Melospiza melodia* | Song Sparrow | no | [2492196](https://www.gbif.org/species/2492196) | [9100](https://www.inaturalist.org/taxa/9100) |  |
| *Larus delawarensis* | Ring-billed Gull | no | [2481134](https://www.gbif.org/species/2481134) | [4364](https://www.inaturalist.org/taxa/4364) |  |
| *Corvus brachyrhynchos* | American Crow | no | [2482507](https://www.gbif.org/species/2482507) | [8021](https://www.inaturalist.org/taxa/8021) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Sciurus carolinensis* | Eastern Gray Squirrel | yes (`sciurus-carolinensis`) | [5219681](https://www.gbif.org/species/5219681) | [46017](https://www.inaturalist.org/taxa/46017) |  |
| *Procyon lotor* | Common Raccoon | no | [5218786](https://www.gbif.org/species/5218786) | [41663](https://www.inaturalist.org/taxa/41663) |  |
| *Tamias striatus* | Eastern Chipmunk | no | [2437438](https://www.gbif.org/species/2437438) | [46217](https://www.inaturalist.org/taxa/46217) |  |
| *Eptesicus fuscus* | Big Brown Bat | no | [2432352](https://www.gbif.org/species/2432352) | [40509](https://www.inaturalist.org/taxa/40509) |  |
| *Thamnophis sirtalis* | Common Garter Snake | no | [2457522](https://www.gbif.org/species/2457522) | [28362](https://www.inaturalist.org/taxa/28362) |  |

### Notes

- Burlington sits on the Dfa/Dfb boundary; Wikipedia gives Dfa.

### Plants

Ship `locales/vt-burlington/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/vt-burlington/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-VT`
- [ ] `locales/vt-burlington/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale vt-burlington --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Burlington street (vt-burlington)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
