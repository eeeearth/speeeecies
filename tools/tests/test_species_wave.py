"""Check that the public backlog handoff preserves identity and batch boundaries."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'issues'))
import prepare_species_reserve
import species_wave


def test_issue_body_contains_resolvable_taxa_and_activity_query():
    item = {
        'scientific_name': 'Testus example', 'common_name': 'Example animal',
        'slug': 'testus-example', 'gbif_usage_key': 987654321, 'inat_taxon_id': 123456789,
        'group': 'Aves', 'family': 'Exampleidae', 'continent': 'europe', 'region': 'FI',
        'gbif_country_month_bearing_count': 429,
        'gbif_discovery_url': 'https://api.gbif.org/v1/occurrence/search?facet=speciesKey',
    }
    body = species_wave.body_for(item, '2026-10-25')
    assert 'species-backlog:2026-10b:987654321:123456789' in body
    assert 'speciesKey=987654321' in body and 'country=FI' in body
    assert 'month=1%2C12' in body and '429' in body
    assert 'docs/data-quality.md' in body and 'ATTRIBUTION.md' in body


def test_reserve_has_unique_keys_and_nine_even_batches():
    leads = [
        {'gbif_usage_key': 90000000 + i, 'group': 'Aves',
         'best': {'region': 'FI', 'continent': 'europe', 'count': 300 + i},
         'countries': [{'region': 'FI'}]}
        for i in range(9)
    ]
    result = prepare_species_reserve.prepare(leads, [], [], count=9)
    assert len(result['records']) == 9
    assert len({x['gbif_usage_key'] for x in result['records']}) == 9
    assert set(result['batches'].values()) == {1}


def test_reserve_excludes_checked_rejections_and_posted_keys():
    leads = [
        {'gbif_usage_key': 90000100 + i, 'group': 'Aves',
         'best': {'region': 'FI', 'continent': 'europe', 'count': 300 + i},
         'countries': [{'region': 'FI'}]}
        for i in range(11)
    ]
    result = prepare_species_reserve.prepare(
        leads, [], [], count=9, additional_taken={90000100, 90000101}
    )
    assert {x['gbif_usage_key'] for x in result['records']} == set(range(90000102, 90000111))


def test_future_reserve_recognizes_published_wave_marker():
    keys = prepare_species_reserve.existing_keys([
        {'body': '<!-- species-backlog:2026-10b:987654321:123456 -->'}
    ])
    assert 987654321 in keys


def test_published_batches_and_unpublished_reserve_are_disjoint():
    docs = ROOT / 'docs'
    first = json.loads((docs / 'species-backlog-2026-10.json').read_text())
    second = json.loads((docs / 'species-backlog-2026-10b.json').read_text())
    reserve = json.loads((docs / 'species-reserve-2026-10.json').read_text())
    overflow = json.loads((docs / 'species-screened-overflow-2026-10b.json').read_text())
    groups = [set(item['gbif_usage_key'] for item in doc['records']) for doc in (first, second, reserve, overflow)]
    assert all(len(keys) == doc['count'] for keys, doc in zip(groups[:2], (first, second)))
    assert len(groups[2]) == 9000
    assert len(groups[3]) == overflow['count']
    assert reserve['screened_key_count_excluded'] == second['screened_key_count']
    assert any(item['group'] == 'Reptilia' for item in second['records'])
    existing_record_keys = {
        json.loads(path.read_text())['external']['gbif_usage_key']
        for path in (ROOT / 'species').glob('*/species.json')
    }
    assert not groups[1] & existing_record_keys
    assert not groups[3] & existing_record_keys
    assert all(not groups[i] & groups[j] for i in range(4) for j in range(i + 1, 4))
    first_inat = {item['inat_taxon_id'] for item in first['records']}
    second_inat = {item['inat_taxon_id'] for item in second['records']}
    overflow_inat = {item['inat_taxon_id'] for item in overflow['records']}
    assert len(first_inat) == first['count'] and len(second_inat) == second['count']
    assert len(overflow_inat) == overflow['count']
    assert not first_inat & second_inat and not first_inat & overflow_inat and not second_inat & overflow_inat
    assert sum(reserve['batches'].values()) == 9000
    assert all(count == 1000 for count in reserve['batches'].values())
