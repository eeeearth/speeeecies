<!-- title: Locale: A Nairobi compound (nairobi-ke) -->
**A Nairobi compound**: a locale for the [live ecological simulation](https://www.youtube.com/@jt55401/live)'s rotation. Whoever takes this (often a coding agent) writes `locales/nairobi-ke/locale.json` and any missing species, following "Contribute a locale" in [AGENTS.md](https://github.com/eeeearth/speeeecies/blob/main/AGENTS.md). The worked example is [`locales/london-uk/`](https://github.com/eeeearth/speeeecies/tree/main/locales/london-uk).

### Suggested manifest values

| Field | Suggestion |
|---|---|
| `id` | `nairobi-ke` |
| `name` | A Nairobi compound |
| `country` | `KE` |
| `activity_region` | `KE-30` (Nairobi City County) |
| `public_lat`, `public_lon` | -1.29, 36.82: the public city centroid from Wikidata [Q3870](https://www.wikidata.org/wiki/Q3870) `P625` (CC0), rounded to 2 decimals |
| `tz` | `Africa/Nairobi` |
| `koppen` | `Cwb`, from the climate section of [Wikipedia](https://en.wikipedia.org/wiki/Nairobi) (CC BY-SA); confirm |
| `elevation_m` | 1661 m, from Wikidata [Q3870](https://www.wikidata.org/wiki/Q3870) `P2044` (CC0) |
| `plot_template` | `suburban-lot` |

Use the city or district centroid only: never a street address, a house, or your own garden.

### Data pointers

- iNaturalist place for the activity region: [10957](https://www.inaturalist.org/places/10957)
- GBIF GADM gid for the activity region: [`KEN.30_1`](https://www.gbif.org/occurrence/search?gadm_gid=KEN.30_1)
- GBIF country page: https://www.gbif.org/country/KE/summary
- Climate normals: the maintainers' import derives weather from climate normals at the centroid, so you do not supply them. For the Köppen class, see the climate table on [Wikipedia](https://en.wikipedia.org/wiki/Nairobi) or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals

Activity curves for this region, per species:

```
uv run tools/fetch_activity.py <slug> --region KE-30 --inat-place-id 10957 --gbif-gadm-gid KEN.30_1 --write
```

### Candidate species (12; list at least 8; aim for 12 or more)

On 2026-09-26, 0 of these existed under `species/`. Check `species/` for any added since.
Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. Search open `species-request` issues first, and claim any you take.

| Species | Common name | In `species/` on 2026-09-26 | GBIF | iNaturalist | Note |
|---|---|---|---|---|---|
| *Bostrychia hagedash* | Hadada Ibis | no | [5229203](https://www.gbif.org/species/5229203) | [3743](https://www.inaturalist.org/taxa/3743) |  |
| *Milvus migrans* | Black Kite | no | [5229167](https://www.gbif.org/species/5229167) | [5268](https://www.inaturalist.org/taxa/5268) |  |
| *Turdus abyssinicus* | Abyssinian Thrush | no | [7340241](https://www.gbif.org/species/7340241) | [145081](https://www.inaturalist.org/taxa/145081) |  |
| *Ploceus baglafecht* | Baglafecht Weaver | no | [2494061](https://www.gbif.org/species/2494061) | [13805](https://www.inaturalist.org/taxa/13805) |  |
| *Cinnyris venustus* | Variable Sunbird | no | [7340636](https://www.gbif.org/species/7340636) | [145188](https://www.inaturalist.org/taxa/145188) |  |
| *Pycnonotus barbatus* | Common Bulbul | no | [2486147](https://www.gbif.org/species/2486147) | [14588](https://www.inaturalist.org/taxa/14588) |  |
| *Motacilla aguimp* | African Pied Wagtail | no | [7405711](https://www.gbif.org/species/7405711) | [13701](https://www.inaturalist.org/taxa/13701) |  |
| *Corvus albus* | Pied Crow | no | [2482519](https://www.gbif.org/species/2482519) | [8038](https://www.inaturalist.org/taxa/8038) |  |
| *Cercopithecus mitis* | Blue Monkey | no | [5219578](https://www.gbif.org/species/5219578) | [43486](https://www.inaturalist.org/taxa/43486) |  |
| *Chlorocebus pygerythrus* | Vervet Monkey | no | [7262034](https://www.gbif.org/species/7262034) | [68137](https://www.inaturalist.org/taxa/68137) |  |
| *Sclerophrys gutturalis* | Guttural Toad | no | [9456514](https://www.gbif.org/species/9456514) | [517053](https://www.inaturalist.org/taxa/517053) |  |
| *Trioceros jacksonii* | Jackson's Chameleon | no | [8371864](https://www.gbif.org/species/8371864) | [32807](https://www.inaturalist.org/taxa/32807) |  |

### Notes

- Many Nairobi observations come from Nairobi National Park; pick garden animals, not the park's big game.

### Plants

Ship `locales/nairobi-ke/flora-catalog.json`: at least 8 plant taxa, at least 2 of them evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`](https://github.com/eeeearth/speeeecies/blob/main/schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it stands in for. See "Writing `flora-catalog.json`" in [`docs/locale-richness.md`](https://github.com/eeeearth/speeeecies/blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`](https://github.com/eeeearth/speeeecies/blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable taxon resembles in the manifest's `flora_wishlist`, by name only.

### Definition of done

- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`
- [ ] `locales/nairobi-ke/locale.json` with a sourced centroid, climate, `blurb` and `facts` (allow-listed licences, attribution unless CC0 or public domain)
- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `KE-30`
- [ ] `locales/nairobi-ke/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, each `taxon` from `schema/v0.1/flora-taxa.json`
- [ ] `uv run tools/validate.py --locale nairobi-ke --report > report.md` passes
- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve `fetch_activity.py` recorded under CC BY-NC) is justified in the PR body
- [ ] The `validate` CI workflow is green on the PR
- [ ] PR titled `locale: A Nairobi compound (nairobi-ke)`, with the report and `Closes #<this issue>`

Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation automatically, and the PR gets a comment saying when it first appears on the [stream](https://www.youtube.com/@jt55401/live). See the locales page: https://eeeearth.github.io/speeeecies/locales.html
