<!-- title: Locale: An Albuquerque courtyard (nm-albuquerque) -->
**An Albuquerque courtyard**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/nm-albuquerque/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `nm-albuquerque` |
| `name` | An Albuquerque courtyard |
| `country` | `US` |
| `activity_region` | `US-NM` (New Mexico) |
| `public_lat`, `public_lon` | 35.08, -106.60: the public city centroid from Wikidata [Q7045560](https://www.wikidata.org/wiki/Q7045560) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Denver` |
| `koppen` | `BSk`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Albuquerque,_New_Mexico) (CC BY-SA); confirm |
| `elevation_m` | to confirm (Wikidata [Q7045560](https://www.wikidata.org/wiki/Q7045560) has no elevation) |
| `plot_template` | `courtyard` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [9](https://www.inaturalist.org/places/9)
- iNaturalist place for Bernalillo County, for species lists: [2390](https://www.inaturalist.org/places/2390)
- GBIF GADM gid for the activity region: [`USA.32_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.32_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Albuquerque,_New_Mexico) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-NM --inat-place-id 9 --gbif-gadm-gid USA.32_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`columba-livia`); they still need a curve for `US-NM`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Geococcyx californianus* | Greater Roadrunner | no | [2496459](https://www.gbif.org/species/2496459) | [1986](https://www.inaturalist.org/taxa/1986) |  |
| *Haemorhous mexicanus* | House Finch | no | [8323485](https://www.gbif.org/species/8323485) | [199840](https://www.inaturalist.org/taxa/199840) |  |
| *Columba livia* | Rock Pigeon | yes (`columba-livia`) | [2495414](https://www.gbif.org/species/2495414) | [3017](https://www.inaturalist.org/taxa/3017) |  |
| *Zenaida asiatica* | White-winged Dove | no | [2495370](https://www.gbif.org/species/2495370) | [3460](https://www.inaturalist.org/taxa/3460) |  |
| *Toxostoma curvirostre* | Curve-billed Thrasher | no | [5231688](https://www.gbif.org/species/5231688) | [14912](https://www.inaturalist.org/taxa/14912) |  |
| *Spinus psaltria* | Lesser Goldfinch | no | [5231647](https://www.gbif.org/species/5231647) | [145308](https://www.inaturalist.org/taxa/145308) |  |
| *Archilochus alexandri* | Black-chinned Hummingbird | no | [5228513](https://www.gbif.org/species/5228513) | [6433](https://www.inaturalist.org/taxa/6433) |  |
| *Astur cooperii* | Cooper's Hawk | no | [2480621](https://www.gbif.org/species/2480621) | [1579017](https://www.inaturalist.org/taxa/1579017) | GBIF uses Accipiter cooperii |
| *Sylvilagus audubonii* | Desert Cottontail | no | [2436910](https://www.gbif.org/species/2436910) | [43115](https://www.inaturalist.org/taxa/43115) |  |
| *Otospermophilus variegatus* | Rock Squirrel | no | [7572569](https://www.gbif.org/species/7572569) | [180008](https://www.inaturalist.org/taxa/180008) |  |
| *Tadarida brasiliensis* | Mexican Free-tailed Bat | no | [2433011](https://www.gbif.org/species/2433011) | [41301](https://www.inaturalist.org/taxa/41301) |  |
| *Sceloporus cowlesi* | Southwestern Fence Lizard | no | [7566793](https://www.gbif.org/species/7566793) | [116137](https://www.inaturalist.org/taxa/116137) |  |

### Notes

- The centroid is the Nob Hill neighbourhood item; the Köppen class comes from the Albuquerque article, which gives BSk or BWk depending on the period.

### Plants

Ship `locales/nm-albuquerque/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/nm-albuquerque/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-NM`
- [ ] `locales/nm-albuquerque/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale nm-albuquerque --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: An Albuquerque courtyard (nm-albuquerque)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
