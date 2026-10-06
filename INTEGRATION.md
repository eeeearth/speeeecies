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

| Command | Result |
|---|---|
| `uv run --with pytest --with 'jsonschema>=4.18' pytest -q tools/tests` | 189 passed, including typo rejection and a valid declared tag |
| `uv run tools/validate.py --locale ga-atlanta --report` | Passed; 12 species, 12 flora taxa, 3 evergreens, no errors |
| `uv run tools/validate.py --locale all --json` | Passed; 18 locales, no locale or flora errors |
| `uv run tools/validate.py --self-check` | Passed; 355 files scanned, 0 findings |
| `python3 tools/sync_resource_tags.py <seeeeds ids.rs> <pinned revision> --check` | Snapshot matches the clean upstream revision named in the JSON |
| `git diff --check` | Passed |

The installed `seeeeds` CLI has no command that runs
`validate_flora_catalog` on an arbitrary existing catalog. Native seeeeds
validation of the corrected file remains a release check. Its `place` command
does not call that validator, so a placement run would not supply this check.

## Release handoff

1. Review and merge the public source change, then confirm CI is green at the
   merge commit.
2. Run seeeeds `validate_flora_catalog` on the corrected catalog during the
   private import preflight.
3. Confirm `Ilex opaca.resource_tags` contains `shrub_thicket` in the staged
   import and staged pack before publication.
4. Complete the normal private import and rotation checks after the separate
   live application acceptance work is complete.

This branch changes public source and its validator only. It is ready for
review; no import, pack, service, or rotation state was changed.
