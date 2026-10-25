#!/usr/bin/env python3
"""Publish screened species requests serially until the open animal queue reaches a target.

Usage: python3 tools/issues/species_wave.py SCREEN_PROGRESS JOURNAL --target-open 1000 --publish
SCREEN_PROGRESS is a resumable JSON file with an ``accepted`` list. JOURNAL is
append-only JSONL; keep both outside the tracked repository while publishing.
The script stops on uncertain POST failures so an operator can check GitHub
before resuming. It does not generate or validate the biological leads.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO = 'eeeearth/speeeecies'
BASE = 'https://api.github.com'
LABELS = ('species-request', 'animal', 'help wanted')
INTERVAL_SECONDS = 3.0  # Serial requests; pause on GitHub's hourly content ceiling.


def activity_url(item: dict) -> str:
    params = [('country', item['region']), ('speciesKey', str(item['gbif_usage_key'])),
              ('license', 'CC0_1_0'), ('license', 'CC_BY_4_0'),
              ('basisOfRecord', 'HUMAN_OBSERVATION'), ('occurrenceStatus', 'PRESENT'),
              ('hasGeospatialIssue', 'false'), ('month', '1,12'), ('limit', '0')]
    return 'https://api.gbif.org/v1/occurrence/search?' + urlencode(params)


def body_for(item: dict, checked_on: str, wave_tag: str = '2026-10b') -> str:
    name = item['scientific_name']
    key = item['gbif_usage_key']
    inat = item['inat_taxon_id']
    slug = item['slug']
    region = item['region']
    group_notes = {
        'Aves': 'Check walking, hopping, perching and flight against the actual program actions; source breeding and migration months for the requested region.',
        'Mammalia': 'Check walking, climbing, swimming or flying against the actual program actions; source local seasonal and day/night activity.',
        'Reptilia': 'Check the actual locomotion and basking or shelter actions; source seasonal activity for the requested region.',
        'Amphibia': 'Separate adult traits from larval traits; check hopping, walking and swimming actions and source local calling or breeding months.',
    }
    return f'''### Research target

- **Scientific name:** *{name}* (family {item['family'] or 'to verify'}; {item['group']}).
- **Proposed activity country:** `{region}` in {item['continent'].replace('-', ' ').title()}. Verify local presence and native or introduced status independently.
- **Record:** `species/{slug}/species.json`, with attribution and a fitting behaviour program. This request does not itself add a live locale.

### Checked data pointers

- [GBIF accepted species {key}](https://api.gbif.org/v1/species/{key}) and [iNaturalist active species {inat}](https://api.inaturalist.org/v1/taxa/{inat}) matched *{name}* at species rank on {checked_on}. Recheck both before use; explain any provider disagreement.
- [GBIF discovery query]({item['gbif_discovery_url']}) found **{item['gbif_country_month_bearing_count']:,}** records for this species key in `{region}` under the batch filters on {checked_on}: present human observations, a recorded month, no flagged geospatial issue, and CC0/CC BY licences. [Refresh the direct species query]({activity_url(item)}).

The observation count is a research lead. It does not prove native range, monthly representativeness, trait values or suitability for a live scene. Check all twelve months and the fetcher's source tiers and usability flags. Country counts do not establish subdivision coverage.

### Research and representation

- {group_notes[item['group']]}
- Find openly licensed sources for biological claims, with precise locators. Distinguish measurements, conversions and judgement. Leave unsupported optional fields out; disclose required blockers.
- Check executable behaviour transitions and actual enabled month sets. Document a representation limit if the shared programs cannot express the species honestly.

### Acceptance criteria

- [ ] Check current records, all open PRs, existing issues, synonyms and provider IDs, then [claim this issue](https://github.com/{REPO}/blob/main/AGENTS.md) with an ETA. Work on one species issue at a time.
- [ ] Add the record with full provenance and regenerated `ATTRIBUTION.md`. Explain any NC source and permissive alternatives checked.
- [ ] Run `uv run tools/fetch_activity.py {slug} --region {region} --write`; inspect the raw query, counts and all monthly values. Disclose provisional or unusable curves.
- [ ] Validate the record, all species and locales, self-check, tests and attribution freshness on the submitted commit as required by [AGENTS.md](https://github.com/{REPO}/blob/main/AGENTS.md).
- [ ] Preview every declared pose and report actual results. Preserve unrelated data in any shared record.
- [ ] Open one species PR with evidence, validation results and this issue link; keep incomplete work in draft. Maintainers handle merging, private import and live-scene acceptance.

Read [the data-quality guide](https://github.com/{REPO}/blob/main/docs/data-quality.md). Claim with `Claiming this: <agent/person>, ETA <date/time and timezone>` after checking for an active claim or partial PR.

<!-- species-backlog:{wave_tag}:{key}:{inat} -->
'''


def api(url: str, token: str, data: dict | None = None) -> dict:
    headers = {'Accept': 'application/vnd.github+json', 'Authorization': f'Bearer {token}',
               'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'speeeecies species-wave publisher'}
    payload = json.dumps(data).encode() if data is not None else None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    req = Request(url, data=payload, headers=headers, method='POST' if payload is not None else 'GET')
    with urlopen(req, timeout=45) as response:
        return json.load(response)


def open_count(token: str) -> int:
    query = urlencode({'q': f'repo:{REPO} is:issue is:open label:species-request label:animal', 'per_page': 1})
    return int(api(BASE + '/search/issues?' + query, token)['total_count'])


def journal_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('screen_progress', type=Path)
    parser.add_argument('journal', type=Path)
    parser.add_argument('--target-open', type=int, default=1000)
    parser.add_argument('--wave-label', default='species-wave-2026-10b')
    parser.add_argument('--screen-target', type=int, default=720)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    if args.target_open < 1 or args.screen_target < 1:
        parser.error('targets must be positive')
    if not args.wave_label.startswith('species-wave-'):
        parser.error('--wave-label must start with species-wave-')
    wave_tag = args.wave_label.removeprefix('species-wave-')
    state = json.loads(args.screen_progress.read_text())
    if not state['accepted']:
        raise SystemExit('No screened candidates yet')
    sample = state['accepted'][0]
    if not args.publish:
        print(f"species: {sample['common_name']} ({sample['scientific_name']})\n\n" + body_for(sample, sample.get('screened_on_utc', datetime.now(timezone.utc).date().isoformat()), wave_tag))
        return
    token = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
    posted = journal_rows(args.journal)
    posted_keys = {int(row['gbif_usage_key']) for row in posted}
    posted_names = {row['scientific_name'].lower() for row in posted}
    current = open_count(token)
    print('open animal requests', current, 'target', args.target_open, 'already posted in this wave', len(posted), flush=True)
    last_write = 0.0
    since_count = 0
    backoff = 60
    rate_failures = 0
    while current < args.target_open:
        state = json.loads(args.screen_progress.read_text())
        available = [x for x in state['accepted'] if x['gbif_usage_key'] not in posted_keys and x['scientific_name'].lower() not in posted_names]
        if not available:
            if len(state['accepted']) >= args.screen_target:
                raise SystemExit(f'Screened pool exhausted with {current} open; screen more candidates before resuming')
            time.sleep(5)
            continue
        item = available[0]
        title = f"species: {item['common_name']} ({item['scientific_name']})"
        body = body_for(item, item.get('screened_on_utc', datetime.now(timezone.utc).date().isoformat()), wave_tag)
        payload = {'title': title, 'body': body, 'labels': [*LABELS, args.wave_label, item['continent']]}
        pause = INTERVAL_SECONDS - (time.monotonic() - last_write)
        if pause > 0:
            time.sleep(pause)
        try:
            result = api(f'{BASE}/repos/{REPO}/issues', token, payload)
        except HTTPError as exc:
            message = exc.read().decode('utf-8', 'replace')[:500]
            if exc.code in (403, 429) and 'rate limit' in message.lower():
                rate_failures += 1
                if rate_failures >= 5:
                    raise RuntimeError('GitHub content limit persisted through five retries; stop publishing and resume from the journal after a longer cooldown') from exc
                if exc.headers.get('X-RateLimit-Remaining') == '0':
                    delay = max(60, int(exc.headers.get('X-RateLimit-Reset', '0')) - int(time.time()) + 5)
                elif exc.headers.get('Retry-After'):
                    delay = max(60, int(exc.headers['Retry-After']))
                else:
                    delay = backoff
                    backoff = min(backoff * 2, 300)
                print('GitHub content limit; waiting', delay, 'seconds before a retry', flush=True)
                time.sleep(delay)
                current = open_count(token)
                continue
            raise RuntimeError(f'GitHub issue creation failed ({exc.code}): {message}') from exc
        # For connection errors after a POST, stop: the server may have created
        # an issue. Inspect GitHub by marker before resuming to avoid duplicates.
        last_write = time.monotonic()
        backoff = 60
        rate_failures = 0
        marker = f"species-backlog:{wave_tag}:{item['gbif_usage_key']}:{item['inat_taxon_id']}"
        if result['title'] != title or marker not in result.get('body', '') or result.get('state') != 'open':
            raise RuntimeError('Issue read-back mismatch: ' + result.get('html_url', '?'))
        if set(payload['labels']) - {label['name'] for label in result.get('labels', [])}:
            raise RuntimeError('Issue labels missing: ' + result['html_url'])
        row = {'issue_number': result['number'], 'issue_url': result['html_url'],
               'scientific_name': item['scientific_name'], 'gbif_usage_key': item['gbif_usage_key'],
               'inat_taxon_id': item['inat_taxon_id'], 'body_sha256': hashlib.sha256(body.encode()).hexdigest()}
        with args.journal.open('a') as out:
            out.write(json.dumps(row, separators=(',', ':')) + '\n')
            out.flush()
            os.fsync(out.fileno())
        posted_keys.add(item['gbif_usage_key'])
        posted_names.add(item['scientific_name'].lower())
        current += 1
        since_count += 1
        if since_count >= 25 or current >= args.target_open:
            current = open_count(token)
            since_count = 0
            print('posted wave', len(posted_keys), 'open', current, 'target', args.target_open, flush=True)
    print('TARGET REACHED:', current, 'open animal requests; wave issues', len(posted_keys), flush=True)


if __name__ == '__main__':
    main()
