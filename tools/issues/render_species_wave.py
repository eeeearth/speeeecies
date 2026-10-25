#!/usr/bin/env python3
"""Build the checked issue index from the screening state and publish journal."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def table_cell(value: str) -> str:
    return value.replace('\n', ' ').replace('\r', ' ').replace('|', '\\|')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('screen_progress', type=Path)
    parser.add_argument('journal', type=Path)
    parser.add_argument('--excluded', type=Path, help='JSON list of closed, unsuitable issue numbers')
    parser.add_argument('--wave-label', default='species-wave-2026-10b')
    parser.add_argument('--out-json', type=Path)
    parser.add_argument('--out-md', type=Path)
    parser.add_argument('--out-overflow', type=Path)
    args = parser.parse_args()
    if not args.wave_label.startswith('species-wave-'):
        parser.error('--wave-label must start with species-wave-')
    tag = args.wave_label.removeprefix('species-wave-')
    args.out_json = args.out_json or ROOT / f'docs/species-backlog-{tag}.json'
    args.out_md = args.out_md or ROOT / f'docs/species-backlog-{tag}.md'
    args.out_overflow = args.out_overflow or ROOT / f'docs/species-screened-overflow-{tag}.json'
    screening = json.loads(args.screen_progress.read_text())
    accepted = screening['accepted']
    by_key = {item['gbif_usage_key']: item for item in accepted}
    journal = [json.loads(line) for line in args.journal.read_text().splitlines()]
    excluded = set(json.loads(args.excluded.read_text())) if args.excluded else set()
    if excluded - {row['issue_number'] for row in journal}:
        raise ValueError('Excluded issue is absent from the publish journal')
    published = [row for row in journal if row['issue_number'] not in excluded]
    keys = [x['gbif_usage_key'] for x in published]
    if len(keys) != len(set(keys)) or not set(keys) <= by_key.keys():
        raise ValueError('Publish journal has a duplicate or unknown GBIF key')
    records = []
    for row in published:
        item = dict(by_key[row['gbif_usage_key']])
        if row['scientific_name'] != item['scientific_name'] or row['inat_taxon_id'] != item['inat_taxon_id']:
            raise ValueError('Issue journal differs from screening record')
        item.update(issue_number=row['issue_number'], issue_url=row['issue_url'], body_sha256=row['body_sha256'])
        records.append(item)
    records.sort(key=lambda x: x['issue_number'])
    if len({x['inat_taxon_id'] for x in records}) != len(records):
        raise ValueError('Duplicate iNaturalist ID in publish journal')
    posted_keys = {row['gbif_usage_key'] for row in journal}
    overflow = [item for item in accepted if item['gbif_usage_key'] not in posted_keys]
    args.out_overflow.write_text(json.dumps({
        'kind': 'screened, unpublished candidates; recheck current providers and duplicates before release',
        'generated_on_utc': datetime.now(timezone.utc).date().isoformat(),
        'count': len(overflow), 'records': overflow,
    }, indent=2, ensure_ascii=False) + '\n')
    doc = {'batch': args.wave_label,
           'generated_on_utc': datetime.now(timezone.utc).date().isoformat(),
           'count': len(records),
           'excluded_closed_issue_numbers': sorted(excluded),
           'screened_key_count': screening['screened'],
           'screening_rejections': screening['reasons'],
           'scope': 'Animal research requests; accepted provider identity and GBIF country observation lead checked. Traits, native range, regional activity, behaviour, previews and live acceptance remain for contributors and maintainers.',
           'filters': {'basisOfRecord': 'HUMAN_OBSERVATION', 'occurrenceStatus': 'PRESENT',
                       'hasGeospatialIssue': False, 'month': '1,12',
                       'licenses': ['CC0_1_0', 'CC_BY_4_0'],
                       'minimum_month_bearing_count': 300},
           'records': records}
    args.out_json.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
    lines = [f'# Animal species request batch {tag}', '',
             f"{len(records)} research requests, with {len({x['gbif_usage_key'] for x in records})} distinct GBIF species keys and iNaturalist IDs. "
             'This batch adds research tasks to the open animal request queue; it does not add finished records or live scenes.', '',
             '[Browse open requests](https://github.com/eeeearth/speeeecies/issues?q=is%3Aissue+is%3Aopen+label%3Aspecies-request+label%3Aanimal) '
             'and read [AGENTS.md](../AGENTS.md) before claiming one.', '',
             '## Screening and limits', '',
             'Each published lead resolved to an accepted GBIF species and a matching active, non-extinct iNaturalist species during screening. '
             'It had at least 300 GBIF country records with a month, present human-observation status, no flagged geospatial issue and a CC0/CC BY licence. '
             f'The linked query and the provider IDs are in the [machine-readable audit]({args.out_json.name}).', '',
             f"The screen checked {screening['screened']:,} GBIF keys and accepted {len(accepted):,} candidate taxa. "
             'The audit records rejection counts by reason. Published issue count can be lower than accepted count because screening includes a small overflow.', '',
             'These checks do not establish native range, representative seasons, anatomy, behaviour or live-scene fit. '
             'Contributors must recheck provider records and research those claims. '
             'The [later-batch reserve](species-reserve-2026-10.md) is unpublished and has a lower screening status.', '']
    if excluded:
        links = ', '.join(f'[#{number}](https://github.com/eeeearth/speeeecies/issues/{number})' for number in sorted(excluded))
        noun = 'lead was' if len(excluded) == 1 else 'leads were'
        lines += [f'{len(excluded)} unsuitable {noun} closed during the publish audit ({links}) and excluded from this batch.', '']
    lines += ['## Requests', '']
    for continent in ['europe','north-america','south-america','africa','asia','oceania']:
        group = [x for x in records if x['continent'] == continent]
        if not group:
            continue
        lines += [f"### {continent.replace('-', ' ').title()} ({len(group)})", '',
                  '| Issue | Scientific name | Common name | Group | Activity country |',
                  '|---|---|---|---|---|']
        for item in group:
            lines.append(f"| [#{item['issue_number']}]({item['issue_url']}) | *{item['scientific_name']}* | {table_cell(item['common_name'])} | {item['group']} | `{item['region']}` |")
        lines.append('')
    lines += ['## Batch count', '',
              '| Group | Requests |', '|---|---:|']
    for group, count in sorted(Counter(x['group'] for x in records).items()):
        lines.append(f'| {group} | {count} |')
    lines.append('')
    args.out_md.write_text('\n'.join(lines))
    print('Rendered',len(records),'issue links and audit records.')


if __name__ == '__main__':
    main()
