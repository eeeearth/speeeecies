"""Tests for `validate.py --locale` and `--self-check` (LOC-M11)."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from conftest import REPO_ROOT, minimal_species, write_species

FIXTURES = Path(__file__).resolve().parent / "fixtures"
EPITHETS = ["vulpes", "lagopus", "zerda", "corsac", "cana", "chama", "pallida", "velox", "macrotis"]


def fox_species(epithet: str) -> dict:
    slug = f"vulpes-{epithet}"
    species = minimal_species(slug)
    species["id"] = f"Vulpes {epithet}"
    return species


def minimal_locale(slugs: list[str], **overrides) -> dict:
    locale = {
        "format": "speeeecies/locale",
        "format_version": "0.1",
        "id": "test-town",
        "name": "A test garden",
        "country": "GB",
        "activity_region": "GB",
        "public_lat": 51.51,
        "public_lon": -0.13,
        "tz": "Europe/London",
        "koppen": "Cfb",
        "elevation_m": 11,
        "plot_template": "rowhouse-garden",
        "species": slugs,
        "flora_wishlist": ["Hedera helix"],
        "blurb": "A small test garden with a lawn, a border and a pond.",
        "facts": [
            {
                "text": "A fact with a public-domain source.",
                "source": {"url": "https://example.org/fact", "title": "Example fact", "license": "CC0-1.0"},
            }
        ],
    }
    locale.update(copy.deepcopy(overrides))
    return locale


def setup_locale(root: Path, locale: dict, n_species: int = 8, species_fn=fox_species) -> list[str]:
    slugs = []
    for epithet in EPITHETS[:n_species]:
        species = species_fn(epithet)
        write_species(root, species["slug"], species)
        slugs.append(species["slug"])
    if not locale.get("species"):
        locale["species"] = slugs
    locale_dir = root / "locales" / locale["id"]
    locale_dir.mkdir(parents=True, exist_ok=True)
    (locale_dir / "locale.json").write_text(json.dumps(locale, indent=2, ensure_ascii=False), encoding="utf-8")
    return slugs


def run_locale(vm, root: Path, locale_id: str = "test-town"):
    result = vm.run_locales([locale_id], root)
    return result, result.locale_reports[0]


def codes(report) -> set[str]:
    return {f.code for f in report.findings if f.level == "error"}


def test_minimal_locale_passes(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    result, lr = run_locale(validate_module, fake_root)
    assert [f for f in lr.findings if f.level == "error"] == []
    assert len(lr.species_rows) == 8
    assert all(row.activity and row.program and row.move_poses for row in lr.species_rows)
    assert not result.has_errors(strict=False)


def test_street_address_fixture_fails_with_lint_message(validate_module, fake_root):
    locale = json.loads((FIXTURES / "locales" / "street-address.json").read_text(encoding="utf-8"))
    setup_locale(fake_root, locale)
    _, lr = run_locale(validate_module, fake_root)
    hits = [f for f in lr.findings if f.code == "StreetAddress"]
    assert len(hits) == 1
    assert "looks like a street address" in hits[0].message
    assert hits[0].path.startswith("locales/test-town/locale.json:")


def test_too_few_species(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]), n_species=7)
    _, lr = run_locale(validate_module, fake_root)
    # 7 is also below the schema's minItems.
    assert "LocaleTooFewSpecies" in codes(lr)


def test_unknown_species(validate_module, fake_root):
    slugs = [f"vulpes-{e}" for e in EPITHETS[:8]]
    setup_locale(fake_root, minimal_locale(slugs[:7] + ["canis-lupus"]))
    _, lr = run_locale(validate_module, fake_root)
    assert {"LocaleUnknownSpecies", "LocaleTooFewSpecies"} <= codes(lr)


def test_coordinates_with_three_decimals_rejected(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([], public_lat=51.507))
    _, lr = run_locale(validate_module, fake_root)
    assert "LocaleCoordinatePrecision" in codes(lr)


def test_integer_and_one_decimal_coordinates_ok(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([], public_lat=51, public_lon=-0.1))
    _, lr = run_locale(validate_module, fake_root)
    assert "LocaleCoordinatePrecision" not in codes(lr)


def test_missing_activity_for_region(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([], activity_region="GB-ENG"))
    _, lr = run_locale(validate_module, fake_root)
    missing = [f for f in lr.findings if f.code == "LocaleMissingActivity"]
    assert len(missing) == 8
    assert "--region GB-ENG" in missing[0].message


def test_region_outside_country(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([], activity_region="DE"))
    _, lr = run_locale(validate_module, fake_root)
    assert "LocaleRegionCountry" in codes(lr)


def test_missing_move_pose(validate_module, fake_root):
    def still_fox(epithet):
        species = fox_species(epithet)
        species["look"]["poses"] = {"idle": {}, "rest": {}}
        return species

    setup_locale(fake_root, minimal_locale([]), species_fn=still_fox)
    _, lr = run_locale(validate_module, fake_root)
    assert "LocaleMissingMovePose" in codes(lr)


def test_invalid_species_fails_locale(validate_module, fake_root):
    def unlicensed_fox(epithet):
        species = fox_species(epithet)
        species["sources"][0]["license"] = "CC-BY-ND-4.0"
        return species

    setup_locale(fake_root, minimal_locale([]), species_fn=unlicensed_fox)
    _, lr = run_locale(validate_module, fake_root)
    assert "LocaleSpeciesInvalid" in codes(lr)


def test_program_not_found_fails_locale(validate_module, fake_root):
    def lost_fox(epithet):
        species = fox_species(epithet)
        species["behavior"]["program"] = "fsm-nowhere-v1"
        return species

    setup_locale(fake_root, minimal_locale([]), species_fn=lost_fox)
    _, lr = run_locale(validate_module, fake_root)
    assert "LocaleMissingBehavior" in codes(lr)


def test_fact_source_licence_checked(validate_module, fake_root):
    facts = [{"text": "A fact from a share-alike page.", "source": {"url": "https://example.org/a", "title": "A", "license": "CC-BY-SA-4.0"}}]
    setup_locale(fake_root, minimal_locale([], facts=facts))
    _, lr = run_locale(validate_module, fake_root)
    assert "MissingAttribution" in codes(lr)


def test_plot_template_enum(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([], plot_template="my-yard"))
    _, lr = run_locale(validate_module, fake_root)
    assert "Schema" in codes(lr)


def test_id_must_match_directory(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    shutil.move(fake_root / "locales" / "test-town", fake_root / "locales" / "other-town")
    _, lr = run_locale(validate_module, fake_root, "other-town")
    assert "LocaleIdMismatch" in codes(lr)


def test_non_dict_facts_reported_not_crashing(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([], facts=["just a string"]))
    _, lr = run_locale(validate_module, fake_root)
    assert "Schema" in codes(lr)


def test_missing_activity_region_gives_no_bogus_fetch_hint(validate_module, fake_root):
    locale = minimal_locale([])
    del locale["activity_region"]
    setup_locale(fake_root, locale)
    _, lr = run_locale(validate_module, fake_root)
    assert "Schema" in codes(lr)
    assert not any("--region None" in f.message for f in lr.findings)


def test_bad_locale_id(validate_module, fake_root):
    _, lr = run_locale(validate_module, fake_root, "London_UK")
    assert codes(lr) == {"LocaleBadId"}


def test_unknown_locale(validate_module, fake_root):
    _, lr = run_locale(validate_module, fake_root, "nowhere")
    assert codes(lr) == {"LocaleNotFound"}


def test_locale_cli_exit_codes(validate_module, fake_root, capsys):
    setup_locale(fake_root, minimal_locale([]))
    assert validate_module.main(["--root", str(fake_root), "--locale", "test-town", "--report"]) == 0
    assert "Locale `test-town`" in capsys.readouterr().out
    assert validate_module.main(["--root", str(fake_root), "--locale", "nowhere"]) == 1


# ---------------------------------------------------------------------------
# Text lint and --self-check
# ---------------------------------------------------------------------------


def test_lint_fixture_trips_every_rule_once(validate_module):
    text = (FIXTURES / "lint" / "leaky.txt").read_text(encoding="utf-8")
    findings = validate_module.lint_text(text, "leaky.txt")
    assert sorted(f.code for f in findings) == sorted(
        ["StreetAddress", "HomePath", "HomePath", "LocalHostname", "SshRemote", "SshRemote"]
    )


def test_lint_ignores_harmless_text(validate_module):
    harmless = "\n".join(
        [
            "Open http://127.0.0.1:18160/preview.html and see ~/.local/share for caches.",
            "The robin sings from 3 Main perches; see species/erithacus-rubecula.",
            "Clone https://github.com/jt55401/speeeecies over https, not over SSH.",
            "Keep machine settings in settings.local.json, which git ignores.",
        ]
    )
    assert validate_module.lint_text(harmless, "ok.txt") == []


def test_self_check_passes_on_clean_root(validate_module, fake_root):
    n_files, findings = validate_module.run_self_check(fake_root)
    assert n_files > 0
    assert findings == []


def test_self_check_flags_a_leak_and_skips_fixtures(validate_module, fake_root):
    fixtures = fake_root / "tools" / "tests" / "fixtures"
    fixtures.mkdir(parents=True)
    shutil.copy(FIXTURES / "lint" / "leaky.txt", fixtures / "leaky.txt")
    assert validate_module.run_self_check(fake_root)[1] == []
    # Assembled so this test file does not itself trip the repo self-check.
    leak = "/".join(["", "home", "carol", "speeeecies"])
    (fake_root / "notes.md").write_text(f"Staged from {leak} before the PR.\n", encoding="utf-8")
    findings = validate_module.run_self_check(fake_root)[1]
    assert [(f.code, f.path) for f in findings] == [("HomePath", "notes.md:1")]
    assert validate_module.main(["--root", str(fake_root), "--self-check"]) == 1


def test_repo_self_check_passes(validate_module):
    # Tracked files only, so a developer's untracked notes can't fail the suite.
    n_files, findings = validate_module.run_self_check(REPO_ROOT, include_untracked=False)
    assert n_files > 20
    assert findings == [], [f.line() for f in findings]


def test_repo_london_uk_locale_passes(validate_module):
    result = validate_module.run_locales(["london-uk"], REPO_ROOT)
    lr = result.locale_reports[0]
    assert [f.line() for f in lr.findings if f.level == "error"] == []
    assert len(lr.species_rows) >= 8
    assert not result.has_errors(strict=False)


# --- flora catalog and richness (SPEEEECIES-LONDON) ---------------------------

FLORA_TAXA = json.loads((REPO_ROOT / "schema" / "v0.1" / "flora-taxa.json").read_text())
DRAWN = {t["taxon"]: t for t in FLORA_TAXA["taxa"]}
EVERGREEN_TREES = ["Ilex opaca", "Thuja occidentalis"]
DECIDUOUS_TREES = ["Malus coronaria", "Betula papyrifera", "Cercis canadensis", "Amelanchier arborea", "Morus rubra", "Tilia americana"]


def flora_entry(taxon: str, locale_id: str = "test-town", **overrides) -> dict:
    model = DRAWN[taxon]
    entry = {
        "taxon": taxon,
        "stand_in_for": None,
        "common_name": model["common_name"],
        "family": model["family"],
        "archetype": model["archetype"],
        "crown_width_m": model["crown_width_m"],
        "height_m": model["height_m"],
        "seasonal": not model["evergreen"],
        "evergreen": model["evergreen"],
        "stages": ["mature"],
        "resource_tags": ["perch"],
        "community_weight": {locale_id: 1.0},
        "native_status": {locale_id: "Native"},
        "invasive": False,
        "provenance": {
            "sources": [{"url": "https://example.org/plant", "title": "Example plant", "license": "CC0-1.0"}],
            "confidence": "Low",
        },
    }
    entry.update(copy.deepcopy(overrides))
    return entry


def write_flora(root: Path, entries: list[dict], locale_id: str = "test-town") -> None:
    catalog = {"schema_version": 1, "source": {"repo": "speeeecies", "rev": f"locales/{locale_id}"}, "entries": entries}
    (root / "locales" / locale_id / "flora-catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def rich_flora() -> list[dict]:
    return [flora_entry(t) for t in EVERGREEN_TREES + DECIDUOUS_TREES]


def all_codes(report) -> set[str]:
    return {f.code for f in report.findings}


def test_locale_without_flora_catalog_warns_but_passes(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    result, lr = run_locale(validate_module, fake_root)
    assert {"LocaleNoFloraCatalog", "LocaleFewSpecies"} <= all_codes(lr)
    assert lr.flora is None
    assert not result.has_errors(strict=False)
    assert result.has_errors(strict=True)


def test_rich_flora_catalog_is_clean(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    write_flora(fake_root, rich_flora())
    result, lr = run_locale(validate_module, fake_root)
    flora_findings = [f for f in lr.findings if f.path.startswith("flora") or "flora" in f.path]
    assert flora_findings == [], [f.line() for f in flora_findings]
    assert (lr.flora.taxa, lr.flora.evergreen) == (8, 2)
    assert "flora catalog of 8 taxa (2 evergreen)" in validate_module.render_markdown(result)


def test_sparse_flora_warns(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    write_flora(fake_root, [flora_entry("Malus coronaria")])
    result, lr = run_locale(validate_module, fake_root)
    assert {"LocaleSparseFlora", "LocaleFewEvergreens"} <= all_codes(lr)
    assert not result.has_errors(strict=False)


def test_flora_counts_distinct_drawable_taxa(validate_module, fake_root):
    # Two hollies drawn with one model count as one evergreen; an undrawable
    # taxon counts toward nothing.
    setup_locale(fake_root, minimal_locale([]))
    undrawable = flora_entry("Malus coronaria")
    undrawable["taxon"] = "Ilex aquifolium"
    write_flora(fake_root, [flora_entry("Ilex opaca"), flora_entry("Ilex opaca", stand_in_for="Ilex aquifolium"), undrawable])
    _, lr = run_locale(validate_module, fake_root)
    assert (lr.flora.taxa, lr.flora.evergreen) == (1, 1)
    assert {"LocaleSparseFlora", "LocaleFewEvergreens"} <= all_codes(lr)


def test_flora_taxon_must_be_drawable(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    undrawable = flora_entry("Malus coronaria")
    undrawable["taxon"] = "Ilex aquifolium"
    write_flora(fake_root, rich_flora() + [undrawable])
    _, lr = run_locale(validate_module, fake_root)
    assert "FloraUnknownTaxon" in codes(lr)


def test_flora_understory_not_placeable_yet(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    write_flora(fake_root, rich_flora() + [flora_entry("Syringa vulgaris")])
    _, lr = run_locale(validate_module, fake_root)
    assert "FloraNotPlaceable" in codes(lr)


def test_flora_archetype_must_match_model(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    write_flora(fake_root, rich_flora() + [flora_entry("Pinus strobus", archetype="Decurrent")])
    _, lr = run_locale(validate_module, fake_root)
    assert "FloraArchetypeMismatch" in codes(lr)


def test_flora_size_and_evergreen_mismatch_warn(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    write_flora(fake_root, rich_flora() + [flora_entry("Malus coronaria", crown_width_m=20.0, evergreen=True, seasonal=False)])
    result, lr = run_locale(validate_module, fake_root)
    assert {"FloraSizeMismatch", "FloraEvergreenMismatch"} <= all_codes(lr)
    assert not result.has_errors(strict=False)


def test_flora_needs_weight_for_this_locale(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    write_flora(fake_root, rich_flora() + [flora_entry("Malus coronaria", community_weight={"other-town": 1.0})])
    _, lr = run_locale(validate_module, fake_root)
    assert "FloraNoWeight" in codes(lr)


def test_flora_sources_licensed_and_attributed(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    unlicensed = {"sources": [{"url": "https://example.org/a", "license": "All-rights-reserved"}], "confidence": "Low"}
    untitled = {"sources": [{"url": "https://example.org/b", "license": "CC-BY-SA-4.0"}], "confidence": "Low"}
    write_flora(
        fake_root,
        rich_flora() + [flora_entry("Malus coronaria", provenance=unlicensed), flora_entry("Morus rubra", provenance=untitled)],
    )
    _, lr = run_locale(validate_module, fake_root)
    assert {"RejectedLicense", "MissingAttribution"} <= codes(lr)


def test_flora_catalog_schema_enforced(validate_module, fake_root):
    setup_locale(fake_root, minimal_locale([]))
    bad = flora_entry("Malus coronaria")
    del bad["provenance"]["sources"][0]["license"]
    write_flora(fake_root, rich_flora() + [bad])
    _, lr = run_locale(validate_module, fake_root)
    assert "Schema" in codes(lr)


def test_flora_taxa_snapshot_is_consistent():
    placeable = set(FLORA_TAXA["placeable_archetypes"])
    assert placeable < {t["archetype"] for t in FLORA_TAXA["taxa"]}
    assert len(DRAWN) == len(FLORA_TAXA["taxa"]) >= 70
    for t in FLORA_TAXA["taxa"]:
        assert t["height_m"] > 0 and t["crown_width_m"] > 0, t["taxon"]


def test_repo_london_uk_is_rich(validate_module):
    result = validate_module.run_locales(["london-uk"], REPO_ROOT)
    lr = result.locale_reports[0]
    assert len(lr.species_rows) >= validate_module.LOCALE_RECOMMENDED_SPECIES
    assert lr.flora is not None
    assert lr.flora.taxa >= validate_module.FLORA_RECOMMENDED_TAXA
    assert lr.flora.evergreen >= validate_module.FLORA_RECOMMENDED_EVERGREEN
    assert [f.line() for f in lr.findings if f.code.startswith(("Locale", "Flora"))] == []
