#!/usr/bin/env python3
"""Turn cached GBIF discovery leads into nine unpublished 1,000-key batches.

Usage: python3 tools/issues/prepare_species_reserve.py DISCOVERED SCREEN_PROGRESS ISSUES_JSON OUTPUT
       --journal PUBLISHED_JSONL --screened-order SCREENED_ORDER_JSON
The output is a discovery inventory, not a set of validated or published issues.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ('Aves', 'Mammalia', 'Reptilia', 'Amphibia')


def existing_keys(issues: list[dict]) -> set[int]:
    keys = {int(x['gbif_usage_key']) for x in json.loads((ROOT / 'docs/species-backlog-2026-10.json').read_text())['records']}
    for issue in issues:
        keys.update(map(int, re.findall(r'GBIF usage key:\s*`?(\d+)', issue.get('body') or '')))
        keys.update(int(key) for key in re.findall(r'species-backlog:[^:\s]+:(\d+):\d+', issue.get('body') or ''))
    prior = json.loads((ROOT / 'docs/species-prior-taxa-2026-10.json').read_text())['issues']
    for item in prior.values():
        keys.update(int(item[k]) for k in ('usageKey','acceptedUsageKey') if item.get(k))
    for path in (ROOT / 'species').glob('*/species.json'):
        keys.add(json.loads(path.read_text())['external']['gbif_usage_key'])
    return keys


def prepare(discovered: list[dict], screened: list[dict], issues: list[dict], count: int = 9000,
            additional_taken: set[int] | None = None) -> dict:
    taken = existing_keys(issues) | {x['gbif_usage_key'] for x in screened} | (additional_taken or set())
    leads = [x for x in discovered if x['gbif_usage_key'] not in taken and x['group'] in GROUPS]
    leads.sort(key=lambda x: (-x['best']['count'], -len(x['countries']), x['gbif_usage_key']))
    if len(leads) < count:
        raise ValueError(f'Only {len(leads)} distinct unused GBIF keys; need {count}. Expand discovery countries or filters before claiming a reserve.')
    available_count = len(leads)
    leads = leads[:count]
    per_batch = Counter()
    per_bucket = Counter()
    records = []
    for hit in leads:
        bucket = (hit['group'], hit['best']['continent'])
        batch = min((b for b in range(1, 10) if per_batch[b] < count // 9),
                    key=lambda b: (per_bucket[(b, *bucket)], per_batch[b], b))
        per_batch[batch] += 1
        per_bucket[(batch, *bucket)] += 1
        records.append({'gbif_usage_key': hit['gbif_usage_key'], 'group': hit['group'],
                        'region': hit['best']['region'], 'continent': hit['best']['continent'],
                        'month_bearing_count': hit['best']['count'], 'later_batch': batch})
    assert len(records) == count and all(per_batch[b] == count // 9 for b in range(1, 10))
    assert len({x['gbif_usage_key'] for x in records}) == count
    return {
        'kind': 'unpublished GBIF discovery leads; taxonomy, iNaturalist identity, representation and duplicates by accepted name require screening before release',
        'generated_on_utc': datetime.now(timezone.utc).date().isoformat(),
        'discovery_lead_count': len(discovered),
        'discovery_country_count': len({country['region'] for hit in discovered for country in hit['countries']}),
        'unused_lead_count_before_selection': available_count,
        'target_after_initial_queue': count,
        'batches': {str(b): per_batch[b] for b in range(1, 10)},
        'filters': {'basisOfRecord': 'HUMAN_OBSERVATION', 'occurrenceStatus': 'PRESENT',
                    'hasGeospatialIssue': False, 'month': '1,12',
                    'licenses': ['CC0_1_0', 'CC_BY_4_0'], 'minimum_month_bearing_count': 300},
        'reptile_discovery_scope': 'GBIF class Squamata; turtles and crocodilians were not queried',
        'gbif_species_url_prefix': 'https://api.gbif.org/v1/species/',
        'records': sorted(records, key=lambda x: (x['later_batch'], x['group'], x['continent'], -x['month_bearing_count'], x['gbif_usage_key'])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('discovered', type=Path)
    parser.add_argument('screen_progress', type=Path)
    parser.add_argument('issues_json', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--out-md', type=Path, help='Defaults to OUTPUT with .md suffix')
    parser.add_argument('--journal', type=Path, help='Exclude all already published GBIF keys')
    parser.add_argument('--screened-order', type=Path, help='Ordered GBIF keys used by the screen; excludes every checked key, including rejected leads')
    parser.add_argument('--blocked-key', type=int, action='append', default=[], help='Exclude a screened unsuitable key')
    args = parser.parse_args()
    additional_taken = set(args.blocked_key)
    if args.journal:
        additional_taken.update(json.loads(line)['gbif_usage_key'] for line in args.journal.read_text().splitlines())
    if args.screened_order:
        checked_count = json.loads(args.screen_progress.read_text())['screened']
        additional_taken.update(json.loads(args.screened_order.read_text())[:checked_count])
    screening = json.loads(args.screen_progress.read_text())
    doc = prepare(json.loads(args.discovered.read_text()),
                  screening['accepted'],
                  json.loads(args.issues_json.read_text()), additional_taken=additional_taken)
    if args.screened_order:
        doc['screened_key_count_excluded'] = screening['screened']
    header = {key: value for key, value in doc.items() if key != 'records'}
    rows = [f"    {json.dumps(item, separators=(',', ':'), ensure_ascii=False)}" for item in doc['records']]
    args.output.write_text(json.dumps(header, indent=2, ensure_ascii=False)[:-2] +
                           ',\n  "records": [\n' + ',\n'.join(rows) + '\n  ]\n}\n')
    lines = [
        '# Nine later species-request batches', '',
        'This inventory holds 9,000 unpublished GBIF species keys, divided into nine batches of 1,000. '
        'They are discovery leads, not accepted GitHub tasks. Each key had at least 300 country-level '
        'month-bearing human observations under the recorded CC0/CC BY filters when discovered. '
        'The counts and countries are starting points for research, not range or seasonal-activity claims.', '',
        f"The discovery pass found {doc['discovery_lead_count']:,} distinct GBIF keys across "
        f"{doc['discovery_country_count']} countries. After excluding known and screened keys, "
        f"{doc['unused_lead_count_before_selection']:,} remained; the 9,000 highest-count leads were staged.", '',
        'Before publishing a batch, check current GBIF acceptance and exact iNaturalist identity, '
        'deduplicate against species records, all issues, open PRs and retained work, and reject unsuitable '
        'or domestic-only taxa. Re-run the observation query. Replace rejected keys through a new discovery '
        'pass so the public queue receives only screened leads. [The operating rule](species-queue-10000.md) '
        'starts that work when fewer than 300 open requests remain, or earlier if active claims leave fewer '
        'than 300 available.', '',
        'The [JSON inventory](species-reserve-2026-10.json) records every key, proposed country, discovery '
        'count and assigned batch. Provider identities and biological suitability have not been verified for '
        'these later leads.', '',
        '| Later batch | Leads | Birds | Mammals | Reptiles | Amphibians |',
        '|---:|---:|---:|---:|---:|---:|',
    ]
    for batch in range(1, 10):
        counts = Counter(x['group'] for x in doc['records'] if x['later_batch'] == batch)
        lines.append(f"| {batch} | {doc['batches'][str(batch)]} | {counts['Aves']} | {counts['Mammalia']} | {counts['Reptilia']} | {counts['Amphibia']} |")
    lines += ['', 'Birds dominate the current discovery pool. The reptile discovery source covers squamates '
              'only. Later passes should add turtle and crocodilian classes and review the group mix before '
              'publication; equal batch sizes do not imply equal group coverage.', '']
    (args.out_md or args.output.with_suffix('.md')).write_text('\n'.join(lines))
    print('Staged',len(doc['records']),'distinct GBIF keys in nine later batches; no issues published.')


if __name__ == '__main__':
    main()
