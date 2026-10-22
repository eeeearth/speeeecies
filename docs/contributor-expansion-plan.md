# Contributor expansion: evidence quality and species backlog

## Outcome

Prepare a substantially larger animal contribution queue while reducing
avoidable review rounds. The first batch targets 300 distinct species with
verified taxon pointers and a country-level activity-data starting point.
The [published batch and audit manifest](species-backlog-2026-10.md) contain
all 300 issue links. Requests describe research still required; they do not
certify a finished species record or promise that it will enter a live locale.

## What the review found

The PR history identifies several different causes of rework:

| Cause | Change in this plan |
|---|---|
| Plausible but unrelated citations, unverified IDs, wrong dataset columns | Require direct source checks, provider/rank resolution and precise locators for claims |
| Copied behaviour defaults produce incorrect seasons, gaits or night activity | Require inspection of executable actions, actual month sets and active-state exits |
| Sparse observation data presented as adequate seasonal evidence | Require query/count/usability review and explicit fallback semantics |
| Shared records replaced wholesale, dropping other locales' data | Require comparison with current main and preservation of unrelated regions and fields |
| Briefs instruct agents to trust recipes or accept known behaviour mismatches | Align the fleet briefs and recipes with the evidence requirements |
| Reviews themselves suggest unverified values or misstate allowed licences | Require source checking of review suggestions and keep the licence policy authoritative |
| Partial submissions presented as complete | Use draft PRs and report actual validation and preview status |

Historical examples are linked in `data-quality.md`. Findings attached to an
old commit are not automatically findings against the repaired head.

## Execution

1. **Update the instructions agents actually receive.** Keep `AGENTS.md` as
   the entry point and place detailed checks in `docs/data-quality.md`.
   Align the species and locale fleet briefs, recipe caveats, contributor
   guide and PR template. Preserve the public-only contributor workflow.
2. **Build an auditable candidate list.** Exclude species represented in main,
   open PRs, retained branches or existing requests. Deduplicate scientific
   names and provider identifiers, including known synonyms. Resolve each
   selected GBIF and iNaturalist identifier to a matching active species.
3. **Screen for an activity-data starting point.** Query GBIF by country,
   taxon group, human-observation basis, present occurrence status, usable
   geospatial flags, recorded month and CC0/CC BY licence. Require at least
   300 matching month-bearing records in the proposed country. Keep the query
   and count with each candidate. This screen does not establish nativeness,
   population abundance, trait evidence or a representative activity curve.
4. **Review representation and distribute the work.** Cover the six inhabited
   continents with birds, mammals, squamates and amphibians. Prefer enough
   data to let contributors make progress. Exclude domestic-only targets,
   extinct taxa, unresolved cross-provider name matches and fully aquatic
   mammals requiring a separate representation design. Check the final list
   for remaining inappropriate candidates rather than filling a quota blindly.
5. **Publish specific requests.** Each issue names one species, its primary
   country, checked taxon links, the observation query, group-specific research
   pitfalls and completion requirements. Apply `species-request`, `animal`,
   `help wanted` and the geographic label. Keep incomplete research explicit;
   do not automatically label these `good first issue`.
6. **Make the larger queue usable.** Raise the fleet's issue-list limit from
   200 to 1,000 so this batch does not hide older open requests. Keep a public
   manifest with taxon IDs, source queries and posted issue numbers. Publish
   serially with rate-limit handling, and resume by recorded issue identity.
7. **Check the result.** Review the instruction diff for contradictions,
   render the fleet briefs through the existing tests, run the public checks,
   and read back every created issue to verify its body and labels. Confirm
   that the batch has no duplicate names or provider identifiers.

## What contributors must demonstrate

A review-ready contribution has checked taxonomy and licence terms, evidence
for its biological claims, transparent estimates, usable or explicitly
provisional activity, fitting executable behaviour, preserved shared data and
the public validation results. Preview limitations must be stated accurately.

These requirements should not reward invented precision. Optional fields can
remain absent. Defensible authored estimates remain allowed with clear
provenance. Contradictory biology, unsupported licence claims and lost shared
data need correction. Cosmetic polishing and additional optional measurements
can be follow-up work when the maintainer accepts that scope.

## Follow-up after observing the next submissions

Measure repeated blockers and review rounds by category before adding more
rules. Candidate validator improvements include checking reachable gaits,
exposing substituted month sets, and detecting dropped activity regions in a
PR diff. These need their own design and tests; this documentation change does
not claim to automate scientific review.

Avoid requiring contributors to access the private simulator. Public review,
merge permission, import success and natural-scene acceptance are distinct
events. Maintainers own release holds and their clearance conditions.
