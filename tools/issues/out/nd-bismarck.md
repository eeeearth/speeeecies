<!-- title: Locale: A Bismarck street (nd-bismarck) -->
**A Bismarck street**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/nd-bismarck/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/jt55401/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/jt55401/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `nd-bismarck` |
| `name` | A Bismarck street |
| `country` | `US` |
| `activity_region` | `US-ND` (North Dakota) |
| `public_lat`, `public_lon` | 46.81, -100.78: the public city centroid from Wikidata [Q37066](https://www.wikidata.org/wiki/Q37066) `P625` (CC0), rounded to 2 decimals |
| `tz` | `America/Chicago` |
| `koppen` | `Dfa`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Bismarck,_North_Dakota) (CC BY-SA); confirm |
| `elevation_m` | 514 m, from Wikidata [Q37066](https://www.wikidata.org/wiki/Q37066) `P2044` (CC0) |
| `plot_template` | `street-block` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [13](https://www.inaturalist.org/places/13)
- iNaturalist place for Burleigh County, for species lists: [2962](https://www.inaturalist.org/places/2962)
- GBIF GADM gid for the activity region: [`USA.35_1`](https://www.gbif.org/occurrence/search?gadm_gid=USA.35_1)
- GBIF country page: https://www.gbif.org/country/US/summary
- iNaturalist: https://www.inaturalist.org/ (check each dataset's licence)
- eBird bar charts, for species lists and seasons (eBird data are not openly licensed): https://ebird.org/ (check each dataset's licence)
- USGS North American Breeding Bird Survey (public domain): https://www.pwrc.usgs.gov/bbs/ (check each dataset's licence)
- USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain): https://nas.er.usgs.gov/ (check each dataset's licence)
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Bismarck,_North_Dakota) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region US-ND --inat-place-id 13 --gbif-gadm-gid USA.35_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 1 of these existed under `species/` (`passer-domesticus`); they still need a curve for `US-ND`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Turdus migratorius* | American Robin | no | [9510564](https://www.gbif.org/species/9510564) | [12727](https://www.inaturalist.org/taxa/12727) |  |
| *Passer domesticus* | House Sparrow | yes (`passer-domesticus`) | [5231190](https://www.gbif.org/species/5231190) | [13858](https://www.inaturalist.org/taxa/13858) |  |
| *Zenaida macroura* | Mourning Dove | no | [2495347](https://www.gbif.org/species/2495347) | [3454](https://www.inaturalist.org/taxa/3454) |  |
| *Bombycilla cedrorum* | Cedar Waxwing | no | [2484609](https://www.gbif.org/species/2484609) | [7428](https://www.inaturalist.org/taxa/7428) |  |
| *Colaptes auratus* | Northern Flicker | no | [2478259](https://www.gbif.org/species/2478259) | [18236](https://www.inaturalist.org/taxa/18236) |  |
| *Spinus tristis* | American Goldfinch | no | [5231640](https://www.gbif.org/species/5231640) | [145310](https://www.inaturalist.org/taxa/145310) |  |
| *Poecile atricapillus* | Black-capped Chickadee | no | [2487805](https://www.gbif.org/species/2487805) | [144815](https://www.inaturalist.org/taxa/144815) |  |
| *Buteo jamaicensis* | Red-tailed Hawk | no | [2480542](https://www.gbif.org/species/2480542) | [5212](https://www.inaturalist.org/taxa/5212) |  |
| *Sciurus niger* | Eastern Fox Squirrel | no | [5219683](https://www.gbif.org/species/5219683) | [46020](https://www.inaturalist.org/taxa/46020) |  |
| *Ictidomys tridecemlineatus* | Thirteen-lined Ground Squirrel | no | [7994322](https://www.gbif.org/species/7994322) | [179988](https://www.inaturalist.org/taxa/179988) |  |
| *Lasionycteris noctivagans* | Silver-haired Bat | no | [2432341](https://www.gbif.org/species/2432341) | [40629](https://www.inaturalist.org/taxa/40629) |  |
| *Lithobates pipiens* | Northern Leopard Frog | no | [2427185](https://www.gbif.org/species/2427185) | [66003](https://www.inaturalist.org/taxa/66003) |  |

### Notes

- Bismarck sits on the Dfa/Dfb boundary; Wikipedia gives Dfa/Dfb.
- Bat records are sparse here (2 research-grade silver-haired bat observations in the county); `fetch_activity.py` may need the state curve.

### Plants

Ship `locales/nd-bismarck/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/jt55401/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/jt55401/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/jt55401/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/nd-bismarck/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `US-ND`
- [ ] `locales/nd-bismarck/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale nd-bismarck --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Bismarck street (nd-bismarck)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://jt55401.github.io/speeeecies/locales.html
