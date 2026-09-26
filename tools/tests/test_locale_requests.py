"""Tests for tools/issues/locale_requests.py (LOC-M16)."""

from __future__ import annotations

import importlib.util
import json
import re
import sys

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "tools" / "issues" / "locale_requests.py"


@pytest.fixture(scope="module")
def lr():
    spec = importlib.util.spec_from_file_location("speeeecies_locale_requests", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def locale_schema():
    return json.loads((REPO_ROOT / "schema" / "v0.1" / "locale.schema.json").read_text(encoding="utf-8"))


def test_about_twenty_places_with_unique_ids_and_titles(lr):
    assert 18 <= len(lr.PLACES) <= 22
    assert len({p.id for p in lr.PLACES}) == len(lr.PLACES)
    assert len({p.title for p in lr.PLACES}) == len(lr.PLACES)
    assert "london-uk" not in {p.id for p in lr.PLACES}  # the worked example is done


def test_places_fit_the_locale_schema(lr, locale_schema):
    props = locale_schema["properties"]
    for p in lr.PLACES:
        assert re.fullmatch(props["id"]["pattern"], p.id), p.id
        assert re.fullmatch(props["country"]["pattern"], p.country), p.id
        assert re.fullmatch(props["activity_region"]["pattern"], p.region), p.id
        assert p.region.split("-")[0] == p.country, p.id
        assert re.fullmatch(props["tz"]["pattern"], p.tz), p.id
        assert p.koppen in props["koppen"]["enum"], p.id
        assert p.plot_template in props["plot_template"]["enum"], p.id
        for coord in (p.lat, p.lon):
            assert round(coord, 2) == coord, p.id
        assert p.continent in lr.CONTINENT_LABELS, p.id


def test_plot_templates_match_the_schema_enum(lr, locale_schema):
    assert set(lr.PLOT_TEMPLATES) == set(locale_schema["properties"]["plot_template"]["enum"])


def test_every_place_lists_8_to_12_known_distinct_species(lr):
    for p in lr.PLACES:
        assert 8 <= len(p.species) <= 12, p.id
        assert len(set(p.species)) == len(p.species), p.id
        for name in p.species:
            assert name in lr.TAXA, f"{p.id}: {name} missing from TAXA"


def test_taxa_table_has_no_unused_entries(lr):
    used = {n for p in lr.PLACES for n in p.species}
    assert set(lr.TAXA) == used


def test_body_marks_existing_species_and_has_the_essentials(lr):
    dublin = next(p for p in lr.PLACES if p.id == "dublin-ie")
    body = lr.render_body(dublin)
    assert "| *Turdus merula* | Eurasian Blackbird | yes (`turdus-merula`) |" in body
    assert "| *Pica pica* | Eurasian Magpie | no |" in body
    for needle in (
        "`IE-D`", "53.35, -6.26", "`Europe/Dublin`", "`Cfb`", "`rowhouse-garden`",
        "https://www.inaturalist.org/places/6719", "`IRL.6_1`",
        "--region IE-D --inat-place-id 6719 --gbif-gadm-gid IRL.6_1",
        "uv run tools/validate.py --locale dublin-ie --report",
        "Definition of done", "https://www.youtube.com/@jt55401/live",
    ):
        assert needle in body, needle


def test_body_without_elevation_says_to_confirm(lr):
    setagaya = next(p for p in lr.PLACES if p.elevation_m is None)
    assert "to confirm" in lr.render_body(setagaya)


def test_species_snapshot_is_real_and_bodies_ignore_later_species(lr, tmp_path):
    # Species are never removed, so the snapshot stays a subset of species/.
    for slug in lr.SPECIES_SNAPSHOT:
        assert (REPO_ROOT / "species" / slug / "species.json").is_file(), slug
    # Rendering reads only the snapshot: the live directory cannot make out/ stale.
    assert "REPO_ROOT" not in lr.render_body.__code__.co_names


def test_committed_bodies_are_current_and_lint_clean(lr):
    rendered = lr.render_all()
    assert lr.lint_bodies(rendered) == []
    for rel, text in rendered.items():
        assert (REPO_ROOT / rel).read_text(encoding="utf-8") == text, f"{rel} is stale; rerun the generator"
    committed = {f"tools/issues/out/{p.name}" for p in lr.OUT_DIR.glob("*.md")}
    assert committed == set(rendered)


def test_lint_catches_a_leak(lr):
    # Assembled at runtime so --self-check does not flag this test file.
    leak = "meet me at 12 Oak " + "Street, see /" + "home/someone/notes"
    problems = lr.lint_bodies({"x.md": leak})
    assert any("street address" in p for p in problems)
    assert any("home-directory path" in p for p in problems)


class FakeGh:
    def __init__(self, labels, titles):
        self.labels = labels
        self.titles = titles
        self.calls: list[list[str]] = []

    def __call__(self, args):
        self.calls.append(args)
        if args[:2] == ["label", "list"]:
            return json.dumps([{"name": n} for n in self.labels])
        if args[:2] == ["issue", "list"]:
            return json.dumps([{"title": t} for t in self.titles])
        return ""


def test_post_is_idempotent_and_creates_missing_labels(lr):
    first = lr.PLACES[0]
    fake = FakeGh(labels=["Europe", "asia", "africa", "oceania", "south-america"], titles=[first.title])
    log = lr.post(fake, dry_run=False)
    created = [c for c in fake.calls if c[:2] == ["issue", "create"]]
    assert len(created) == len(lr.PLACES) - 1
    assert all(first.title not in c for c in created)
    assert f"skip (exists): {first.title}" in log
    made_labels = sorted(c[2] for c in fake.calls if c[:2] == ["label", "create"])
    assert made_labels == ["locale-request", "north-america"]
    for c in created:
        assert c[c.index("--label") + 1] == "locale-request"

    fake_again = FakeGh(labels=list(lr.CONTINENT_LABELS) + ["locale-request"], titles=[p.title for p in lr.PLACES])
    lr.post(fake_again, dry_run=False)
    assert not [c for c in fake_again.calls if c[1] == "create"]


def test_post_dry_run_changes_nothing(lr):
    fake = FakeGh(labels=[], titles=[])
    log = lr.post(fake, dry_run=True)
    assert not [c for c in fake.calls if c[1] == "create"]
    assert sum(line.startswith("create: ") for line in log) == len(lr.PLACES)
