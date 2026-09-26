# Contributing

speeeecies takes contributions as pull requests: one species per PR, or
one locale (a place and its species) per PR.
Coding agents should read [`AGENTS.md`](AGENTS.md) instead of this file —
it has the same flow with more detail. This page is for people.

## Request a species

Open an issue with the **species-request** form (New Issue -> "Species
request"). Give the scientific name, common name, and, if you can, a
continent and a few suggested regions (ISO 3166 country codes). Someone —
often a coding agent — will pick it up.

## Add a species yourself

1. Read `schema/v0.1/species.schema.json` and look at a worked example:
   `species/vulpes-vulpes`, `species/erithacus-rubecula`, or
   `species/bufo-bufo`. Copy the closest one as a starting point.
2. Create `species/<slug>/species.json`, where `<slug>` is the scientific
   name lowercased with hyphens (`vulpes-vulpes`). Look up the GBIF usage
   key at `https://api.gbif.org/v1/species/match?name=<Scientific name>`
   and the iNaturalist taxon id at
   `https://api.inaturalist.org/v1/taxa?q=<Scientific name>`.
3. Pick a shared behaviour program from `behaviors/` and set its
   parameters, or write `species/<slug>/behavior.json` if none fits.
4. Run `uv run tools/fetch_activity.py <slug> --region <ISO> --write` for
   each region you're targeting.
5. Run `uv run tools/validate.py species/<slug> --write-attribution --report`
   until it reports no errors.
6. Preview it: `python3 tools/build_site.py && python3 -m http.server 18160
   --bind 127.0.0.1 -d _site`, then open
   `http://127.0.0.1:18160/preview.html?species=<slug>` and check every
   pose.
7. Open a PR titled `species: <common name> (<Scientific name>)`, paste the
   validate report, and write `Closes #<issue number>`.

### Data rules

- Every value needs a source with an open licence. Prefer CC0 or public
  domain, then CC BY, then CC BY-SA. Non-commercial (NC) sources are a
  last resort — mark them and justify them in the PR body. ND and unknown
  licences are rejected outright.
- Write licence ids exactly as listed in `schema/v0.1/licenses.json`
  (SPDX-style, case-sensitive: `CC-BY-4.0`, not `cc-by-4.0`).
- Never strip attribution, even from sources that don't legally require
  it.
- Never invent a number. If you can't source a value, leave it out (if
  optional) or mark it `derived: true` with a note on how you derived it.
  Authored judgement calls (like `wariness` or behaviour parameters) are
  fine — say so honestly in the `note`.

## Contribute a locale

A locale is a place for the live simulation
(https://www.youtube.com/@jt55401/live) to show: a city or district, its
climate, a generic garden or street plot, and at least 8 animals that live
there. It is one file, `locales/<id>/locale.json`; `locales/london-uk/` is
the worked example and `AGENTS.md` has the step-by-step.

1. Open (or pick up) a **locale-request** issue and comment that you're
   claiming it.
2. Copy `locales/london-uk/locale.json` to `locales/<id>/locale.json` and
   change it. Use the **public centroid** of the city or district, from a
   public page such as Wikidata, rounded to 2 decimals. We only accept
   public centroid coordinates: never your house, your garden or a street
   address.
3. List at least 8 species from `species/`. Add missing ones first, and
   fetch an activity curve for your locale's `activity_region` for each
   species that lacks one (`tools/fetch_activity.py`).
4. Run `uv run tools/validate.py --locale <id> --report` and
   `uv run tools/validate.py --self-check` until both pass, then open a PR
   titled `locale: <place> (<id>)` with the report.

**What "validated" means.** A locale counts as validated only when three
things have happened, in order: a maintainer merged the PR to `main`; CI
was green at that commit, including the locale check and the self-check;
and the maintainers' private import of the locale into the simulation
succeeded (it builds the scene from your species, the climate at the
centroid and the plot template). Then the locale joins the live rotation,
and a comment on your merged PR says so and when it first appears on the
stream.

**Flora is phase 2.** There is no plant format yet, so each locale uses a
default plant catalog for its climate. Put plants you'd like to see in
`flora_wishlist`, by name only.

## Report a data error

Open a regular (blank) issue describing what's wrong and, if you can,
which field and source. If you know the fix, a PR against the affected
`species/<slug>/species.json` is even better.

## Code contributions

Tools under `tools/` are [PEP 723](https://peps.python.org/pep-0723/) `uv`
scripts (stdlib plus minimal declared dependencies) — no separate install
step. Run the test suite before opening a PR:

```
uv run --with pytest --with jsonschema pytest tools/tests -q
```

## Licence of contributions

- Code you contribute is licensed MIT (see `LICENSE`).
- Species and behaviour data you contribute is licensed CC BY-SA 4.0 (see
  `LICENSE-DATA`), except data you mark as coming from a non-commercial
  source, which keeps that source's licence.
- By opening a PR, you agree that the values you authored yourself (not
  copied from a source) are released under those licences.

## Code of conduct

Be kind, and assume good faith. Disagree about data and code, not about
people. If a review comment is blunt, read it as a comment on the record,
not on you. Contributors who can't manage that will be asked to leave the
project.
