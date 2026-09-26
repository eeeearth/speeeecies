"""Tests for tools/fetch_activity.py. No network access: HTTP is either a
hand-built fake client (dependency injection) or --offline reading from a
pre-populated fixture cache dir under tools/tests/fixtures/fetch_activity/.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fetch_activity"

spec = importlib.util.spec_from_file_location("fetch_activity", TOOLS_DIR / "fetch_activity.py")
fa = importlib.util.module_from_spec(spec)
sys.modules["fetch_activity"] = fa
spec.loader.exec_module(fa)


# --------------------------------------------------------------------------
# Fake HTTP client for dependency injection
# --------------------------------------------------------------------------


class FakeClient:
    """A stand-in for HttpClient: url -> canned JSON dict, or url -> Exception."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls = []

    def get_json(self, url):
        self.calls.append(url)
        resp = self.responses.get(url)
        if resp is None:
            raise AssertionError(f"unexpected URL requested: {url}")
        if isinstance(resp, Exception):
            raise resp
        return resp


def inat_histogram(counts: dict) -> dict:
    return {"total_results": 12, "results": {"month_of_year": {str(k): v for k, v in counts.items()}}}


def gbif_facets(counts: dict, total=None) -> dict:
    return {
        "count": total if total is not None else sum(counts.values()),
        "facets": [
            {
                "field": "MONTH",
                "counts": [{"name": str(k), "count": v} for k, v in counts.items()],
            }
        ],
    }


# --------------------------------------------------------------------------
# Pure math: counting, normalisation, share, rounding
# --------------------------------------------------------------------------


def test_counts_from_inat_histogram():
    data = inat_histogram({1: 5, 2: 10})
    assert fa.counts_from_inat_histogram(data) == {1: 5, 2: 10}


def test_counts_from_gbif_facets():
    data = gbif_facets({8: 5289, 10: 5211})
    assert fa.counts_from_gbif_facets(data) == {8: 5289, 10: 5211}


def test_counts_from_gbif_facets_missing_month_field():
    assert fa.counts_from_gbif_facets({"facets": []}) == {}


def test_monthly_list_fills_zero_for_missing_months():
    assert fa.monthly_list({1: 5, 12: 3}) == [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3]


def test_share_curve_normalises_to_peak_one():
    species = [10, 20, 5]
    baseline = [10, 10, 10]
    # raw ratios: 1.0, 2.0, 0.5 -> peak 2.0 -> normalised: 0.5, 1.0, 0.25
    assert fa.share_curve(species, baseline) == pytest.approx([0.5, 1.0, 0.25])


def test_share_curve_zero_baseline_yields_zero_share():
    species = [10, 0, 5]
    baseline = [0, 0, 10]
    # month 0: baseline 0 -> share 0; month 2: 5/10=0.5 -> peak 0.5 -> normalised 1.0
    assert fa.share_curve(species, baseline) == pytest.approx([0.0, 0.0, 1.0])


def test_share_curve_all_zero_baseline_yields_all_zero():
    assert fa.share_curve([1, 2, 3], [0, 0, 0]) == [0.0, 0.0, 0.0]


def test_finalize_curve_rounds_and_renormalises_peak_to_one():
    curve = [0.3333333, 0.6666666, 1.0 / 3]
    out = fa.finalize_curve(curve)
    assert max(out) == 1.0
    assert out == [round(v, 2) for v in out]


def test_finalize_curve_all_zero():
    assert fa.finalize_curve([0.0, 0.0, 0.0]) == [0.0] * 3


def test_mean_curves_averages_elementwise():
    assert fa.mean_curves([1.0, 0.0], [0.0, 1.0]) == [0.5, 0.5]


# --------------------------------------------------------------------------
# Tier widening
# --------------------------------------------------------------------------


def test_inat_tier_widens_when_below_min_obs():
    place_id = 6857
    taxon_id = 42069
    class_taxon_id = 40151
    url_a = fa.build_inat_url(taxon_id, place_id, "A")
    url_b = fa.build_inat_url(taxon_id, place_id, "B")
    url_c = fa.build_inat_url(taxon_id, place_id, "C")
    baseline_url_c = fa.build_inat_url(class_taxon_id, place_id, "C")

    client = FakeClient(
        {
            url_a: inat_histogram({1: 10}),  # total 10, below min_obs
            url_b: inat_histogram({1: 50}),  # total 50, still below min_obs
            url_c: inat_histogram({m: 40 for m in fa.MONTHS}),  # total 480, usable
            f"https://api.inaturalist.org/v1/taxa/{taxon_id}": {
                "results": [{"ancestors": [{"rank": "class", "id": class_taxon_id, "name": "Mammalia"}]}]
            },
            baseline_url_c: inat_histogram({m: 100 for m in fa.MONTHS}),
        }
    )
    outcome = fa.fetch_inat(client, taxon_id, place_id, min_obs=300)
    assert outcome.tier == "C"
    assert outcome.usable is True
    assert outcome.total == 480
    # every tier A, B, C should have been attempted before settling on C
    tried = [a["tier"] for a in outcome.attempts]
    assert tried == ["A", "B", "C"]


def test_inat_stops_widening_once_min_obs_met():
    place_id = 1
    taxon_id = 2
    class_taxon_id = 3
    url_a = fa.build_inat_url(taxon_id, place_id, "A")
    baseline_url_a = fa.build_inat_url(class_taxon_id, place_id, "A")
    client = FakeClient(
        {
            url_a: inat_histogram({m: 30 for m in fa.MONTHS}),  # total 360 >= min_obs
            f"https://api.inaturalist.org/v1/taxa/{taxon_id}": {
                "results": [{"ancestors": [{"rank": "class", "id": class_taxon_id}]}]
            },
            baseline_url_a: inat_histogram({m: 60 for m in fa.MONTHS}),
        }
    )
    outcome = fa.fetch_inat(client, taxon_id, place_id, min_obs=300)
    assert outcome.tier == "A"
    assert outcome.usable is True
    assert [a["tier"] for a in outcome.attempts] == ["A"]


def test_gbif_tiers_skip_b_and_widen_a_to_c():
    taxon_key = 5219243
    class_key = 359
    area = ("country", "GB")
    url_a = fa.build_gbif_url(taxon_key, area, "A")
    url_c = fa.build_gbif_url(taxon_key, area, "C")
    baseline_url_c = fa.build_gbif_url(class_key, area, "C")
    client = FakeClient(
        {
            url_a: gbif_facets({1: 5}, total=5),
            url_c: gbif_facets({m: 30 for m in fa.MONTHS}, total=360),
            f"https://api.gbif.org/v1/species/{taxon_key}": {"classKey": class_key},
            baseline_url_c: gbif_facets({m: 60 for m in fa.MONTHS}, total=720),
        }
    )
    outcome = fa.fetch_gbif(client, taxon_key, area, min_obs=300)
    assert outcome.tier == "C"
    assert [a["tier"] for a in outcome.attempts] == ["A", "C"]
    assert outcome.usable is True


# --------------------------------------------------------------------------
# Fallback logic
# --------------------------------------------------------------------------


def test_fallback_uses_gbif_when_inat_sparse():
    inat = fa.SourceOutcome(name="inat", tier="C", total=10, usable=False, share=[0.1] * 12)
    gbif = fa.SourceOutcome(name="gbif", tier="A", total=1000, usable=True, share=[1.0] + [0.0] * 11)
    result, notes = fa.combine_sources(inat, gbif)
    assert result.method == "gbif_share"
    assert result.used == ["gbif"]
    assert result.observations == 1000
    assert any("iNaturalist not used" in n for n in notes)


def test_fallback_uses_inat_when_gbif_missing():
    inat = fa.SourceOutcome(name="inat", tier="A", total=1000, usable=True, share=[1.0] + [0.0] * 11)
    gbif = fa.SourceOutcome(name="gbif", skipped_reason="ISO 3166-2 without --gbif-gadm-gid")
    result, notes = fa.combine_sources(inat, gbif)
    assert result.method == "inat_share"
    assert result.used == ["inat"]
    assert any("GBIF not used" in n for n in notes)


def test_both_usable_means_curves():
    inat = fa.SourceOutcome(name="inat", tier="A", total=500, usable=True, share=[1.0, 0.0])
    gbif = fa.SourceOutcome(name="gbif", tier="A", total=500, usable=True, share=[0.0, 1.0])
    result, notes = fa.combine_sources(inat, gbif)
    assert result.method == "mean(inat_share, gbif_share)"
    assert result.used == ["inat", "gbif"]
    assert result.observations == 1000
    assert result.monthly == [1.0, 1.0]  # (0.5, 0.5) renormalised to peak 1


def test_neither_usable_but_some_data_uses_best_available_with_warning():
    inat = fa.SourceOutcome(name="inat", tier="C", total=5, usable=False, share=[1.0, 0.0])
    gbif = fa.SourceOutcome(name="gbif", tier="C", total=50, usable=False, share=[0.0, 1.0])
    result, notes = fa.combine_sources(inat, gbif)
    assert result.method == "gbif_share"  # gbif had more records
    assert result.observations == 50
    assert any("WARNING" in n for n in notes)


def test_neither_usable_and_no_data_returns_none():
    inat = fa.SourceOutcome(name="inat", error="boom")
    gbif = fa.SourceOutcome(name="gbif", error="boom")
    result, notes = fa.combine_sources(inat, gbif)
    assert result is None


# --------------------------------------------------------------------------
# Licence id chosen per tier
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tier,expected",
    [("A", "CC-BY-4.0"), ("B", "CC-BY-SA-4.0"), ("C", "CC-BY-NC-4.0")],
)
def test_tier_spdx_mapping(tier, expected):
    assert fa.TIER_SPDX[tier] == expected


def test_inat_attribution_widens_with_tier():
    assert "CC BY-SA" not in fa.inat_attribution("A")
    assert "CC BY-SA" in fa.inat_attribution("B")
    assert "CC BY-NC" in fa.inat_attribution("C")


def test_gbif_attribution_widens_with_tier():
    assert "CC BY-NC" not in fa.gbif_attribution("A", "2026-01-01")
    assert "CC BY-NC" in fa.gbif_attribution("C", "2026-01-01")


# --------------------------------------------------------------------------
# species.json merge
# --------------------------------------------------------------------------


def _sample_species():
    return {
        "format": "speeeecies/v0.1",
        "id": "Vulpes vulpes",
        "sources": [
            {
                "id": "some-other-source",
                "url": "https://example.org/a",
                "title": "Existing source",
                "license": "CC0-1.0",
                "accessed": "2025-01-01",
                "kind": "literature",
            }
        ],
        "activity": {
            "regions": [
                {
                    "region": "FR",
                    "monthly": [1.0] * 12,
                    "method": "gbif_share",
                    "observations": 10,
                    "sources": ["gbif-activity-fr"],
                }
            ]
        },
    }


def test_merge_replaces_existing_region_and_keeps_others():
    data = _sample_species()
    new_entry = {
        "region": "GB",
        "monthly": [0.5] * 12,
        "method": "mean(inat_share, gbif_share)",
        "observations": 999,
        "sources": ["inat-activity-gb", "gbif-activity-gb"],
    }
    fa.merge_into_species(data, "GB", new_entry, [])
    regions = data["activity"]["regions"]
    assert len(regions) == 2
    assert regions[0]["region"] == "FR"  # untouched, kept at original position
    assert regions[1] == new_entry

    # replacing GB again should overwrite in place, not append
    newer_entry = dict(new_entry, observations=1234)
    fa.merge_into_species(data, "GB", newer_entry, [])
    regions = data["activity"]["regions"]
    assert len(regions) == 2
    assert regions[1]["observations"] == 1234


def test_merge_adds_and_updates_sources_preserving_other_entries():
    data = _sample_species()
    rec = fa.build_source_record(
        "gbif-activity-gb", "https://api.gbif.org/v1/occurrence/search?x", "GBIF for GB",
        "A", fa.gbif_attribution("A", "2026-09-25"), "2026-09-25",
    )
    fa.merge_into_species(data, "GB", {"region": "GB", "monthly": [0.0] * 12, "method": "gbif_share",
                                        "observations": 1, "sources": ["gbif-activity-gb"]}, [rec])
    ids = [s["id"] for s in data["sources"]]
    assert ids == ["some-other-source", "gbif-activity-gb"]

    # update: same id should replace in place, not duplicate
    rec2 = dict(rec, license="CC-BY-NC-4.0")
    fa.merge_into_species(data, "GB", {"region": "GB", "monthly": [0.0] * 12, "method": "gbif_share",
                                        "observations": 2, "sources": ["gbif-activity-gb"]}, [rec2])
    assert len(data["sources"]) == 2
    assert data["sources"][1]["license"] == "CC-BY-NC-4.0"


def test_merge_preserves_key_order_on_write(tmp_path):
    species_dir = tmp_path / "species" / "vulpes-vulpes"
    species_dir.mkdir(parents=True)
    species_path = species_dir / "species.json"
    original = _sample_species()
    # deliberately ordered keys: format, id, sources, activity
    species_path.write_text(json.dumps(original, indent=2), encoding="utf-8")

    data = json.loads(species_path.read_text(encoding="utf-8"))
    fa.merge_into_species(data, "FR", dict(data["activity"]["regions"][0], observations=42), [])
    species_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    text = species_path.read_text(encoding="utf-8")
    assert text.index('"format"') < text.index('"id"') < text.index('"sources"') < text.index('"activity"')
    reloaded = json.loads(text)
    assert reloaded["activity"]["regions"][0]["observations"] == 42


# --------------------------------------------------------------------------
# End-to-end offline run using fixtures (fixtures/fetch_activity/*.json,
# installed into a temp cache dir at their content-hash path).
# --------------------------------------------------------------------------


def _install_fixture(cache_dir: Path, url: str, fixture_name: str) -> None:
    src = FIXTURES_DIR / fixture_name
    dest = fa.cache_path(cache_dir, url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def test_offline_end_to_end_gbif_only(tmp_path):
    """A GB-subdivision-like scenario where iNat is skipped (no place id given
    and region is treated as a country here, but iNat data is deliberately
    left uninstalled to force a fetch error -> GBIF-only fallback)."""
    root = tmp_path / "repo"
    species_dir = root / "species" / "vulpes-vulpes"
    species_dir.mkdir(parents=True)
    species_json = {
        "format": "speeeecies/v0.1",
        "id": "Vulpes vulpes",
        "taxonomy": {"class": "Mammalia"},
        "external": {"gbif_usage_key": 5219243, "inat_taxon_id": 42069},
        "sources": [],
        "activity": {"regions": []},
    }
    (species_dir / "species.json").write_text(json.dumps(species_json, indent=2), encoding="utf-8")

    cache_dir = tmp_path / "cache"

    # Install only GBIF fixtures; iNat country-lookup fixtures are absent so
    # the country-place-id resolution fails offline and iNat is unusable.
    area = ("country", "GB")
    url_a = fa.build_gbif_url(5219243, area, "A")
    _install_fixture(cache_dir, url_a, "gbif_occurrence_gb_tier_a.json")
    baseline_url_a = fa.build_gbif_url(359, area, "A")
    _install_fixture(cache_dir, baseline_url_a, "gbif_occurrence_gb_class_baseline_tier_a.json")
    _install_fixture(
        cache_dir,
        "https://api.gbif.org/v1/species/5219243",
        "gbif_species_5219243.json",
    )

    rc = fa.main(
        [
            "vulpes-vulpes",
            "--region",
            "GB",
            "--min-obs",
            "300",
            "--cache-dir",
            str(cache_dir),
            "--offline",
            "--root",
            str(root),
            "--write",
        ]
    )
    assert rc == 0

    written = json.loads((species_dir / "species.json").read_text(encoding="utf-8"))
    regions = written["activity"]["regions"]
    assert len(regions) == 1
    entry = regions[0]
    assert entry["region"] == "GB"
    assert entry["method"] == "gbif_share"
    assert entry["sources"] == ["gbif-activity-gb"]
    assert max(entry["monthly"]) == 1.0
    assert len(entry["monthly"]) == 12

    ids = [s["id"] for s in written["sources"]]
    assert ids == ["gbif-activity-gb"]
    assert written["sources"][0]["license"] == "CC-BY-4.0"


def test_write_round_trips_non_ascii_common_name(tmp_path):
    """species.json must keep non-ASCII characters literal (UTF-8), not
    \\u-escaped, and the written file must end with a newline."""
    root = tmp_path / "repo"
    species_dir = root / "species" / "bufo-bufo"
    species_dir.mkdir(parents=True)
    species_json = {
        "format": "speeeecies/v0.1",
        "id": "Bufo bufo",
        "common_names": {"en": "Common toad", "de": "Erdkröte"},
        "taxonomy": {"class": "Amphibia"},
        "external": {"gbif_usage_key": 5219243, "inat_taxon_id": 42069},
        "sources": [],
        "activity": {"regions": []},
    }
    (species_dir / "species.json").write_text(json.dumps(species_json, indent=2), encoding="utf-8")

    cache_dir = tmp_path / "cache"
    area = ("country", "GB")
    url_a = fa.build_gbif_url(5219243, area, "A")
    _install_fixture(cache_dir, url_a, "gbif_occurrence_gb_tier_a.json")
    baseline_url_a = fa.build_gbif_url(359, area, "A")
    _install_fixture(cache_dir, baseline_url_a, "gbif_occurrence_gb_class_baseline_tier_a.json")
    _install_fixture(cache_dir, "https://api.gbif.org/v1/species/5219243", "gbif_species_5219243.json")

    rc = fa.main(
        [
            "bufo-bufo",
            "--region",
            "GB",
            "--min-obs",
            "300",
            "--cache-dir",
            str(cache_dir),
            "--offline",
            "--root",
            str(root),
            "--write",
        ]
    )
    assert rc == 0

    raw_text = (species_dir / "species.json").read_text(encoding="utf-8")
    assert "Erdkröte" in raw_text
    assert "\\u" not in raw_text
    assert raw_text.endswith("\n")

    written = json.loads(raw_text)
    assert written["common_names"]["de"] == "Erdkröte"


# --- curve kind (share for endotherms, raw for ectotherms) ---


def test_choose_curve_kind_auto_by_class():
    assert fa.choose_curve_kind("auto", "Aves") == "share"
    assert fa.choose_curve_kind("auto", "Mammalia") == "share"
    assert fa.choose_curve_kind("auto", "Amphibia") == "raw"
    assert fa.choose_curve_kind("auto", "Insecta") == "raw"
    assert fa.choose_curve_kind("share", "Amphibia") == "share"


def test_raw_curve_ignores_baseline_and_keeps_winter_low():
    toad = [14, 153, 516, 350, 314, 498, 540, 469, 365, 132, 27, 5]
    curve = fa.raw_curve(toad)
    assert curve[6] == 1.0
    assert curve[0] < 0.05 and curve[11] < 0.05


def test_combine_sources_labels_method_with_curve_kind():
    a = fa.SourceOutcome(name="inat", tier="A", total=500, usable=True, share=[1.0] + [0.5] * 11)
    b = fa.SourceOutcome(name="gbif", tier="A", total=500, usable=True, share=[1.0] + [0.5] * 11)
    result, _ = fa.combine_sources(a, b, "raw")
    assert result.method == "mean(inat_raw, gbif_raw)"
