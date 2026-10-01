# Brief: contribute one locale

You are a delegated agent with your own git worktree, your own branch and your
own token budget. You know nothing that is not in this brief, the repository, or
the files it points you at. Read carefully and do the whole job.

## Your situation

- Worktree: `{{WORKTREE}}` — you are already in it. Branch: `{{BRANCH}}`,
  branched from `{{BASE_REF}}`. The main checkout is `{{REPO}}`; never edit it.
- Issue: **#{{ISSUE}}** in `{{GH_REPO}}`. Locale id: `{{SLUG}}`.
  Directory to create: `locales/{{SLUG}}/`.
- The issue body carries suggested manifest values and data pointers. Use them.
  They are starting points, not answers: confirm each one and correct it against
  a source you actually cite.
- Your status file: append a line at each milestone, and when the PR is open and
  green, the final line `I'm done boss`. If you are genuinely stuck, the final
  line `BLOCKED: <reason>`. A clear `BLOCKED:` is an acceptable outcome;
  forcing something through is not.

## What this repository is

A public kit for the live ecological simulation at
[https://www.youtube.com/@jt55401/live](https://www.youtube.com/@jt55401/live).
A **locale** is a place the stream can show: a public city or district, its
climate, a generic plot, the plants its garden shows, and at least 8 (better 12
or more) animal species that live there.

You add **two JSON files** for the locale. The import that turns accepted
records into scenery is not in this repository and you do not need it.

## Read these first

- `AGENTS.md`, section "Contribute a locale". It is the contract; this brief is
  a summary of it.
- `locales/london-uk/` — the worked example. Copy it field by field. A locale
  written from a blank file will not validate first try.
- `docs/locale-richness.md` — read this before you start. The bare minimum
  validates but looks empty on the stream, and that is the thing reviewers
  push back on.
- `schema/v0.1/locale.schema.json`, `schema/v0.1/flora-catalog.schema.json`,
  and for any species you add, `schema/v0.1/species.schema.json`.

## The flow

### 1. Confirm the id and claim the issue

`id` must equal the directory name and the lowercase-hyphenated form in the
issue title. Comment on the issue before you start:

```
gh issue comment {{ISSUE}} --body "Claiming this: <agent/person>, ETA <date>"
```

### 2. Get the coordinates from a public page

`public_lat` and `public_lon` must have **at most 2 decimals** (about 1 km),
and must be a public city or district centroid. Never a house, a garden, a yard
or a street address, and never your own. Wikidata is CC0 and has `P625` on city
entities; the issue usually names the entity.

The validator rejects any file in the locale directory containing text shaped
like a street address (a number, a capitalised name and `St`, `Ave`, `Rd`, `Ln`,
`Dr`, `Street`, `Avenue` or `Road`), an absolute home-directory path, a hostname
ending in `.local`, or an SSH git remote. Keep the names you write down to the
city.

### 3. Choose the plot

`plot_template` is one of `suburban-lot`, `rural-lot`, `rowhouse-garden`,
`street-block`, `courtyard`. Take the one the issue suggests. It decides which
props the scene gets.

### 4. List at least 8 species, aim for 12 or more

For each species listed under `species`:

- it must exist under `species/`;
- it must pass its own validation, so every one of its data points has
  provenance with an allow-listed licence;
- it must have 12 monthly activity values for `activity_region`;
- it must resolve a behaviour program;
- it must have a block mesh with an `idle` pose and one move pose per
  locomotion mode.

Aim for a mix the way a real place is: several garden birds, at least one large
conspicuous one, a couple of mammals including a nocturnal one, and an amphibian
or reptile if the plot suits them. Check `species/` for anything added since the
issue was written.

**If a species you need does not exist, add it in this same PR** using the
species flow in `AGENTS.md`. Search open `species-request` issues first and
claim any you take. A locale PR carrying the species it needs is expected, not a
scope violation.

Fetch an activity curve for each listed species that lacks one:

```
uv run tools/fetch_activity.py <slug> --region <activity_region> --write
```

For a subdivision rather than a whole country, pass the place ids the issue
body lists:

```
uv run tools/fetch_activity.py <slug> --region GB-ENG --inat-place-id 6858 --gbif-gadm-gid GBR.1_1 --write
```

### 5. Write the flora catalog

`locales/{{SLUG}}/flora-catalog.json` maps plant taxa the simulation can draw
onto the animals they stand in for. You need:

- **at least 8 plant taxa**, and **at least 2 of them evergreen**;
- one taxon per entry, with a positive `community_weight`;
- each entry naming the species it stands in for.

Read "Writing a flora catalog" in `docs/locale-richness.md` and copy
`locales/london-uk/flora-catalog.json` field by field. Without a catalog the
garden gets a generic set of large trees for your Köppen class, which is the
most common reason a locale looks bare.

Only draw from taxa in `schema/v0.1/flora-taxa.json`, and copy each taxon's
`archetype` exactly. `Shrub`, `Forb`, `Graminoid` and `Fern` are not yet
drawable; the import cannot place them and the validator warns.

### 6. Facts and sources

`facts` is a list, and every fact needs a `source` and an allow-listed licence,
plus an `attribution` string unless the source is CC0 or public domain. Licence
preference order: CC0 or public domain first, then CC BY, then CC BY-SA or
ODbL. ND and unknown licences are rejected outright. Non-commercial sources are
last resort, must be justified in the PR body, and must never be relicensed.

Wikidata (CC0) is the reliable source for a centroid, an elevation or a
timezone. Wikipedia (CC BY-SA) is fine for climate and Köppen class. Verify the
licence each time; it changes.

### 7. Validate

```
uv run tools/validate.py --locale {{SLUG}} --report > report.md
uv run tools/validate.py --self-check
```

Both must pass. Fix errors and rerun until they do not. Warnings are allowed but
justify them in the PR.

### 8. Preview

```
python3 tools/build_site.py
python3 -m http.server 18160 --bind 127.0.0.1 -d _site
```

Open `http://127.0.0.1:18160/locales.html` and look at your locale's scene: is
the garden actually planted, does the plot read as the right kind of place, are
the animals plausible for the setting. Then open your locale's page and check the
species entries.

### 9. Open the PR

Title exactly `locale: <the place> (<id>)`. The body must contain the validate
report from step 7 verbatim, a line `Closes #{{ISSUE}}`, the locale rows of the
pull request template that are genuinely done, and a justification for any
non-CC0/CC-BY source.

Then prove the PR exists before you go any further. A branch pushed is not a
PR: `gh pr create` can fail, and a delegate once reported success with a
`…/pull/new/<branch>` compare URL, which is the page you land on when the PR
was never opened.

```
gh pr view --json number,url,state
```

A real PR returns a `number` and a `/pull/<number>` URL. If that errors with "no
pull requests found", the PR is not open — fix it or report `BLOCKED:`. Do not
write `I'm done boss` on the strength of a push.

### 10. Get CI green, then stop

```
gh pr checks --watch
```

If the checks never start, run `gh pr view --json mergeable,mergeStateStatus`
first: a `CONFLICTING` state silently suppresses GitHub Actions, and the fix is
to rebase on `{{BASE_REF}}`.

## Warnings you are allowed to leave, and what to do about them

| Warning | What it means | What to do |
|---|---|---|
| `LocaleFewSpecies` | fewer than 12 species | add more; the scene will read as empty |
| `LocaleNoFloraCatalog` | no catalog | add one; the garden becomes generic trees |
| `LocaleSparseFlora` | fewer than 8 taxa | add taxa |
| `LocaleFewEvergreens` | fewer than 2 evergreen | add evergreen taxa |
| `FloraSizeMismatch` | a taxon's size or evergreen flag differs from the drawn model | align the flag with the model |
| `FloraEvergreenMismatch` | as above | as above |

## Never

- Never invent a number. Omit an optional field, or mark it `derived: true` with
  a note saying exactly how you got it. Dishonest precision is worse than an
  honest gap.
- Never use a private or precise location. Public centroid, 2 decimals.
- Never strip an `attribution` string from a non-CC0 source.
- Never merge, and never push to `main`. You have one branch.
- Never write local paths, hostnames or tokens into a committed file.

## What reviewers look for

- **Richness over minimum compliance.** A locale with 8 species and no catalog
  validates and looks empty. The whole point is that the scene reads as a real
  place.
- **Coordinates that are really public.** A garden, a street or a house fails
  the lint even when the record validates.
- **Provenance on every fact and every species datum.** Reviewers spot-check
  `sources[].url` against `sources[].license`.
- **Flora that matches the climate.** Taxa that cannot grow in your Köppen class
  read as wrong even when the catalog is valid.
- **Honest gaps.** An omitted optional field with a reason beats a plausible
  invention.

## When you get stuck

Read the actual error; the validator names the field and the rule. If an enum
value you want does not exist, do not force the closest wrong value into range
to pass — pick the value the place really is. If you cannot source an elevation,
omit it. If you cannot reach 12 species, ship 8 that are all correct and say so
in the PR rather than padding the list with species that do not live there.

Your recipe, if the fleet researched one for this issue:

{{RECIPE}}