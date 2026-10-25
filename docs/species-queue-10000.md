# Species request queue toward 10,000

The contribution target is 10,000 distinct animal species requests over time.
The first operating milestone is 1,000 **open** requests. Check each issue's
claim before starting; open requests with active ETAs are temporarily taken.
The [first screened batch](species-backlog-2026-10.md) published 300 requests.
The [second batch](species-backlog-2026-10b.md) fills the open queue to the
milestone. A closed issue no longer counts as available work, so each release
starts by checking the current open count and existing records and PRs.

Seven older requests, [#2](https://github.com/eeeearth/speeeecies/issues/2),
[#3](https://github.com/eeeearth/speeeecies/issues/3),
[#5](https://github.com/eeeearth/speeeecies/issues/5),
[#11](https://github.com/eeeearth/speeeecies/issues/11),
[#30](https://github.com/eeeearth/speeeecies/issues/30),
[#32](https://github.com/eeeearth/speeeecies/issues/32) and
[#33](https://github.com/eeeearth/speeeecies/issues/33), already have species
records on `main`. They now track their missing suggested country activity
curves under `activity-coverage` and no longer count as species requests.
[Issue #12](https://github.com/eeeearth/speeeecies/issues/12) also has a
record, but its existing claim runs through October 30. It remains unchanged
until that work is resolved; check its claim and PR before reclassifying it.
This release aims for 1,001 open labelled requests so at least 1,000 still
need a species record while #12 remains in that queue.
During the second batch audit, [#522](https://github.com/eeeearth/speeeecies/issues/522)
was closed as domestic-only. [#567](https://github.com/eeeearth/speeeecies/issues/567),
[#711](https://github.com/eeeearth/speeeecies/issues/711),
[#757](https://github.com/eeeearth/speeeecies/issues/757) and
[#993](https://github.com/eeeearth/speeeecies/issues/993) were closed as
fully aquatic. They are excluded from the live batch count; the publisher
replaces their open slots.

The [reserve inventory](species-reserve-2026-10.md) holds 9,000 **unpublished
GBIF discovery leads**, assigned to nine later batches. A key in the reserve
is not yet a researched issue. Its country has at least 300 month-bearing,
CC0/CC BY human observations under the recorded filters. Taxon acceptance,
iNaturalist identity, synonyms, current duplicates, native range and
representation still need checking before publication. The reserve is an
ordered source of candidates, with unsuitable leads replaced through a new
discovery pass. It makes the long-term target concrete without sending
contributors to unverified tasks.

The [screened overflow](species-screened-overflow-2026-10b.json) records
accepted candidates left after the first 1,000-open milestone. Use those
before drawing from the lower-confidence reserve, while rechecking current
provider identity, issues, records and PRs. They are not published tasks.

## Replenishment rule

When fewer than 300 open animal requests remain, prepare the next
reserve batch. Check active claims too; if fewer than 300 are actually
available while the open total is higher, release a vetted batch early.
Screen it against current `main`, all issues, retained work and open PRs.
Confirm accepted GBIF and active, non-extinct iNaturalist species at
matching rank, with the same country observation starting point used for the
second batch. Publish enough specific requests to bring the open queue toward
1,000, or set a higher temporary open target when many existing requests are
claimed. Keep one species per issue. If a batch loses candidates to duplicates,
taxonomic changes or thin data, draw replacements from a fresh discovery query.

Check the live open count with:

```sh
gh api -X GET search/issues \
  -f q='repo:eeeearth/speeeecies is:issue is:open label:species-request label:animal' \
  -f per_page=1 --jq .total_count
```

The issue body supplies checked taxon and observation links, group-specific
research cautions and the [contributor acceptance requirements](../AGENTS.md).
Contributors still verify the scientific claims and licences, build the record,
run the public checks and open one PR. Maintainers decide on merge, private
import and live-scene acceptance. Finished records and issues are counted
separately.

## Operating a batch

The scripts in [`tools/issues/`](../tools/issues/) cache provider responses and
record every published issue. Use a scratch directory on the bulk disk. Update
the two GitHub snapshots immediately before screening:

```sh
export SPEEEECIES_WAVE_SCRATCH="$HOME/tmp/speeeecies-wave-<date>"
mkdir -p "$SPEEEECIES_WAVE_SCRATCH"
gh issue list --repo eeeearth/speeeecies --state all --limit 20000 --json number,title,body,state,labels,url > "$SPEEEECIES_WAVE_SCRATCH/issues-existing.json"
gh pr list --repo eeeearth/speeeecies --state open --limit 200 --json number,title,headRefName,files,url > "$SPEEEECIES_WAVE_SCRATCH/open-prs.json"
python3 tools/issues/discover_species_candidates.py
python3 tools/issues/screen_species_candidates.py
python3 tools/issues/species_wave.py "$SPEEEECIES_WAVE_SCRATCH/screen-progress.json" "$SPEEEECIES_WAVE_SCRATCH/published.jsonl"
```

The last command prints one issue as a preview. Check its identity and links
before adding `--publish --target-open 1000 --wave-label species-wave-<id>`.
Create the matching label first. The publisher writes serially, respects
GitHub's secondary content rate limit and records an append-only journal.
If a POST has an uncertain network result, inspect the issue marker on GitHub
before resuming. Avoid a second posting process for the same wave.

Build or refresh the unpublished reserve only after screening has finished.
The screened order excludes rejected keys as well as accepted ones:

```sh
python3 tools/issues/prepare_species_reserve.py \
  "$SPEEEECIES_WAVE_SCRATCH/discovered.json" \
  "$SPEEEECIES_WAVE_SCRATCH/screen-progress.json" \
  "$SPEEEECIES_WAVE_SCRATCH/issues-existing.json" \
  docs/species-reserve-2026-10.json \
  --journal "$SPEEEECIES_WAVE_SCRATCH/published.jsonl" \
  --screened-order "$SPEEEECIES_WAVE_SCRATCH/screened-order.json"
```

The command writes the JSON inventory and its Markdown summary. Use
`--blocked-key <GBIF key>` for a lead rejected during a later manual audit.
Check the unused lead count before claiming that the full 9,000 are staged.

For the screened overflow, set `SPEEEECIES_WAVE_DISCOVERED` to
`docs/species-screened-overflow-2026-10b.json`, leave
`SPEEEECIES_WAVE_BATCH` unset, and use a new scratch directory with fresh
GitHub snapshots. The screen rechecks the provider identities and observation
count before an issue can be published.

For a later batch, set `SPEEEECIES_WAVE_DISCOVERED` to the reserve JSON,
`SPEEEECIES_WAVE_BATCH` to one of 1 through 9, and
`SPEEEECIES_WAVE_TARGET` to the number of newly screened candidates you need.
Use a **new scratch directory** and fresh GitHub snapshots. The screening
script reconstructs the GBIF queries from each reserved key and country.
Check current provider data again; the saved observation count is historical.
Render the final issue index from the journal with
`python3 tools/issues/render_species_wave.py "$SPEEEECIES_WAVE_SCRATCH/screen-progress.json" "$SPEEEECIES_WAVE_SCRATCH/published.jsonl" --wave-label species-wave-<id>`.
If any unsuitable issue was closed during the run, pass `--excluded` with a JSON
list of its issue numbers. Read back the live open count before announcing the
milestone.
