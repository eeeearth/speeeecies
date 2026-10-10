# PR #93 review addendum

The Guttural toad source says males call throughout the year, with October and
November as the main breeding period. The record scopes its breeding phase to
South Africa (`ZA`) and uses those months for its croak season. The shared
`fsm-anuran-nocturnal-v1` program gates calling with one global month pair, so
`call_m1` and `call_m2` are now 10 and 11. The format cannot express a separate
schedule for each region; this setting represents the documented ZA main
breeding window wherever the shared program runs. Rain-driven and regional
variation remains outside the current model.

Suggested PR-body update:

> The shared anuran FSM now gates calls in October and November, matching the
> record's cited main breeding period and croak season. The source says calling
> can occur year-round; the FSM's single global month pair represents the
> record's ZA main breeding window because this format cannot encode regional
> call schedules.

---

# Atlanta flora resource tag correction

## Release hold

**HOLD merge and publication.** The automatic locale sync fetches public
`main` every 30 minutes and can rebuild and publish changed locale content.
Merging this correction can therefore change the live inputs protected by
eeeearth PR131 while its natural visual acceptance is pending. Keep this PR
as a draft. Merge only after PR131 natural visual acceptance completes, or
after a separately reviewed boundary makes the source update compatible with
that acceptance and its rollback checks. Source review and green CI do not
clear this operational hold.

## Source change

The `Ilex opaca` entry in `locales/ga-atlanta/flora-catalog.json` now uses
`shrub_thicket`. The old value, `shrub_thickel`, was a typo. The catalog's
`declared_tags` remains empty.

The locale validator now rejects a flora `resource_tags` value unless it is a
seeeeds built-in tag, a valid `host:<slug>` tag, or listed in that catalog's
`declared_tags`. The built-in set in `schema/v0.1/resource-tags.json` is
generated from seeeeds `ResourceTag::KNOWN`; its `source` field pins the
upstream revision. When seeeeds changes the set, regenerate the snapshot with
`tools/sync_resource_tags.py` from a clean seeeeds checkout at the revision
being adopted. Run the script with `--check` to verify an existing snapshot.
This keeps validation offline while giving reviewers a reproducible source.

## Verification

The source change was rebased onto public `main` at `fdd777e` before the
checks below. The `INTEGRATION.md` add/add conflict was resolved by retaining
main's PR #93 note above and this Atlanta handoff. Main's unrelated winged
body-plan validation change remains intact. The diff retains seven files.

| Command | Result |
|---|---|
| `uv run --with pytest --with 'jsonschema>=4.18' pytest -q -p no:cacheprovider tools/tests/test_locale.py tools/tests/test_validate.py` | 106 passed, including typo rejection and a valid declared tag |
| `uv run tools/validate.py --locale ga-atlanta --report` | Passed; 12 species, 12 flora taxa, 3 evergreens, no errors |
| `uv run tools/validate.py --locale all --json` | Passed; 33 locales, no locale or flora errors |
| `uv run tools/validate.py --self-check` | Passed; 586 files scanned, 0 findings |
| `python3 tools/sync_resource_tags.py <seeeeds ids.rs> <pinned revision> --check` | Snapshot matches the clean upstream revision named in the JSON |
| `git diff --check` | Passed |

The installed `seeeeds` CLI has no command that runs
`validate_flora_catalog` on an arbitrary existing catalog. Native seeeeds
validation of the corrected file remains a release check. Its `place` command
does not call that validator, so a placement run would not supply this check.

## Release handoff

1. Resolve the release hold above and review the publication and rollback
   boundary with the coordinator.
2. Merge the public source change, then confirm CI is green at the merge
   commit. Automatic locale sync can act on that merge; coordinate this step
   with the release boundary.
3. Run seeeeds `validate_flora_catalog` on the corrected catalog during the
   private import preflight. Confirm `Ilex opaca.resource_tags` contains
   `shrub_thicket` in the staged import and staged pack before publication.
4. Complete the normal private import and rotation checks, including the
   confirmed-release chart update.

This branch changes public source and its validator only. It is ready for
source review under the release hold; no import, pack, service, or rotation
state was changed.
