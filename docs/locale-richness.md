# Locale richness: enough plants and animals to look alive

A locale can pass every check and still look empty on the
[live stream](https://www.youtube.com/@jt55401/live). This page explains
why that happened to the first contributed locale, `london-uk`, what we
changed, and what a new locale should ship so it does not happen again.

## What went wrong with `london-uk`

The first `london-uk` manifest passed validation, but once imported its
garden showed two conifers and an open lawn. Three things caused it.

1. **No plant list.** A locale without a flora catalog gets the
   simulation's generic catalog for its Köppen class. For `Cfb` (oceanic)
   that is six large North American trees (red oak, basswood, black
   cherry, white pine, honey locust, crabapple) with crowns of 8 to 18 m.
   None of them is a London garden plant.
2. **Bare in winter.** Five of those six trees are drawn deciduous. The
   stream picks a random date across the year, so on most winter and
   early-spring dates only the white pines had leaves.
3. **Few animals.** The manifest listed the minimum of 8 species. A June
   scene placed about 16 animals of 8 species. Comparable in-house
   locales show 11 to 13 species and 30 to 40 animals at once.

Nothing in the kit warned about any of this. The only rule was "at least 8
species", and the docs said plants were phase 2 and could not be
contributed.

## What changed

- **Locales can ship plants now.** A locale should include
  `locales/<id>/flora-catalog.json`. It is optional, but without it the
  validator warns and the garden looks bare. The maintainers' import uses it in
  place of the generic catalog. `tools/validate.py --locale <id>` checks it
  against `schema/v0.1/flora-catalog.schema.json`.
- **The validator warns about sparse locales.** These are warnings, so the
  check still passes, but they appear in the report and the PR:

  | Code | When |
  |---|---|
  | `LocaleFewSpecies` | fewer than 12 species |
  | `LocaleNoFloraCatalog` | no `flora-catalog.json` |
  | `LocaleSparseFlora` | fewer than 8 plant taxa |
  | `LocaleFewEvergreens` | fewer than 2 evergreen taxa |

- **`london-uk` is now a full example.** It lists 16 species and a
  13-taxon catalog of London garden trees, 3 of them evergreen. An
  imported June scene now shows 36 to 40 animals of 16 species among 14
  trees.

This is a fix-up, not a numbered roadmap milestone. Plant *species
records* (`species-request` issues labelled `phase-2`, roadmap item
SPEEEECIES-M8) are still closed for work. A flora catalog is a list of
which drawable plants a garden shows; it is not a plant species record.

## Targets for a new locale

| | Minimum (error below) | Target (warning below) |
|---|---|---|
| Animal species | 8 | 12 or more |
| Plant taxa in `flora-catalog.json` | none | 8 or more |
| Evergreen plant taxa | none | 2 or more |

For the animals, aim for a mix that fills the garden at every hour and
season:

- 5 to 8 garden birds, including at least one large, conspicuous one
  (a pigeon, dove, crow or magpie);
- 2 to 4 mammals, including a nocturnal one;
- an amphibian or reptile if the plot has water or cover for one;
- mostly year-round residents, so winter scenes are not empty.

## Writing `flora-catalog.json`

The simulation can only draw the plants in
[`schema/v0.1/flora-taxa.json`](../schema/v0.1/flora-taxa.json), about 80
taxa, most of them North American. For a place elsewhere, choose the
drawable taxon that looks most like each local plant and record the local
species in `stand_in_for`. `london-uk` draws English holly with
*Ilex opaca* and silver birch with *Betula papyrifera*.

Start from [`locales/london-uk/flora-catalog.json`](../locales/london-uk/flora-catalog.json)
and, for each entry:

1. **`taxon`**: a taxon from `flora-taxa.json`.
2. **`archetype`, `evergreen`, `height_m`, `crown_width_m`**: copy them
   from that taxon's row, and set `seasonal` to the opposite of
   `evergreen`. These describe the model that is drawn. Plants are spaced
   by `crown_width_m`, so a value that differs from the drawn model makes
   crowns overlap or leaves gaps (the validator warns above 25%).
3. **`stand_in_for`, `common_name`**: the local species and its common
   name. Drop hybrid signs: `Tilia europaea`, not `Tilia × europaea`.
4. **`community_weight`**: `{"<locale id>": <weight>}`, the plant's
   relative share of the garden. The import multiplies it by 1.0 for
   plants whose `native_status` is `Native` or `NativeAndIntroduced` and
   by 0.3 for the rest. To give an introduced ornamental the same share as
   a native, divide its weight by 0.3. Weights are judgement; say so in the
   `note`.
5. **`native_status`**: `{"<locale id>": "Native" | "Introduced" | ...}`,
   from a licensed source.
6. **`resource_tags`**: what the plant gives animals, using the tags your
   species' `habitat.resources` ask for: `berry`, `fruit`, `seed`,
   `nectar`, `perch`, `shrub_thicket`, `cavity`, `nest_cup`,
   `invertebrate`, `leaf_litter`, `host:<name>`. Matching tags make the
   garden more suitable for your animals.
7. **`provenance`**: every source needs an allow-listed licence, and a
   `title` that doubles as the attribution line unless the licence is CC0
   or public domain.

Include at least two evergreens (holly, yew-like conifers, cypress hedges,
evergreen magnolias) so winter scenes stay green. Prefer small and medium
garden trees, and keep wide-crowned trees (20 m or more) to one or two
with low weights: a small plot fills up quickly, and a plant that does
not fit is left out.

### Shrubs, flowers and grasses are not placed yet

`flora-taxa.json` also lists `Shrub`, `Forb`, `Graminoid` and `Fern`
plants. The simulation can draw them, but the maintainers' current import
rejects any catalog that contains them. The validator reports
`FloraNotPlaceable` for these until the import is upgraded; then
`placeable_archetypes` in `flora-taxa.json` will list them and understory
plants can be added.

## For maintainers

- When the import can place understory plants, add `Shrub`, `Forb`,
  `Graminoid` and `Fern` to `placeable_archetypes` in
  `schema/v0.1/flora-taxa.json`.
- When the simulation's plant models change, regenerate
  `flora-taxa.json` from them (taxon, common name, family, archetype,
  evergreen, mature height and crown width) and update `snapshot`.
