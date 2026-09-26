"""Tests for tools/build_site.py. Run with:
uv run --with pytest pytest tools/tests -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_site  # noqa: E402


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "site" / "js").mkdir(parents=True)
    (repo / "site" / "css").mkdir(parents=True)
    (repo / "site" / "index.html").write_text("<html>index</html>", encoding="utf-8")
    (repo / "site" / "js" / "blockmesh.js").write_text("export function buildModel(){}", encoding="utf-8")
    (repo / "site" / "css" / "site.css").write_text("body{}", encoding="utf-8")

    (repo / "schema" / "v0.1").mkdir(parents=True)
    (repo / "schema" / "v0.1" / "species.schema.json").write_text("{}", encoding="utf-8")

    (repo / "behaviors").mkdir(parents=True)
    (repo / "behaviors" / "fsm-test-v1.json").write_text(
        json.dumps({"id": "fsm-test-v1", "kind": "fsm"}), encoding="utf-8"
    )

    return repo


def write_species(repo: Path, slug: str, common_name: str, klass: str, body_plan: str) -> None:
    species_dir = repo / "species" / slug
    species_dir.mkdir(parents=True)
    data = {
        "slug": slug,
        "id": common_name.title(),
        "common_names": {"en": common_name},
        "taxonomy": {"class": klass},
        "look": {"body_plan": body_plan},
    }
    (species_dir / "species.json").write_text(json.dumps(data), encoding="utf-8")
    (species_dir / "ATTRIBUTION.md").write_text(f"# {common_name}\n\nSome credit line.\n", encoding="utf-8")


def test_build_site_copies_static_dirs(tmp_path):
    repo = make_repo(tmp_path)
    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    assert (out / "index.html").read_text(encoding="utf-8") == "<html>index</html>"
    assert (out / "js" / "blockmesh.js").is_file()
    assert (out / "css" / "site.css").is_file()
    assert (out / "schema" / "v0.1" / "species.schema.json").is_file()
    assert (out / "behaviors" / "fsm-test-v1.json").is_file()


def test_species_index_lists_every_species(tmp_path):
    repo = make_repo(tmp_path)
    write_species(repo, "vulpes-vulpes", "red fox", "Mammalia", "quadruped")
    write_species(repo, "bufo-bufo", "common toad", "Amphibia", "anuran")

    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    index = json.loads((out / "species" / "index.json").read_text(encoding="utf-8"))
    slugs = {e["slug"] for e in index}
    assert slugs == {"vulpes-vulpes", "bufo-bufo"}

    fox = next(e for e in index if e["slug"] == "vulpes-vulpes")
    assert fox["common_name_en"] == "red fox"
    assert fox["class"] == "Mammalia"
    assert fox["body_plan"] == "quadruped"
    assert fox["path"] == "species/vulpes-vulpes/species.json"

    assert (out / "species" / "vulpes-vulpes" / "species.json").is_file()


def test_species_index_empty_when_no_species_dir(tmp_path):
    repo = make_repo(tmp_path)
    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    index = json.loads((out / "species" / "index.json").read_text(encoding="utf-8"))
    assert index == []


def test_species_index_skips_malformed_species_json(tmp_path, capsys):
    repo = make_repo(tmp_path)
    write_species(repo, "vulpes-vulpes", "red fox", "Mammalia", "quadruped")
    bad_dir = repo / "species" / "broken-species"
    bad_dir.mkdir(parents=True)
    (bad_dir / "species.json").write_text("{not valid json", encoding="utf-8")

    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    index = json.loads((out / "species" / "index.json").read_text(encoding="utf-8"))
    assert [e["slug"] for e in index] == ["vulpes-vulpes"]
    assert "broken-species" in capsys.readouterr().err


def test_attribution_md_concatenates_species_attributions(tmp_path):
    repo = make_repo(tmp_path)
    write_species(repo, "vulpes-vulpes", "red fox", "Mammalia", "quadruped")
    write_species(repo, "bufo-bufo", "common toad", "Amphibia", "anuran")

    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    attribution = (out / "ATTRIBUTION.md").read_text(encoding="utf-8")
    assert "# Attribution" in attribution
    assert "red fox" in attribution
    assert "common toad" in attribution
    assert "Some credit line." in attribution


def test_docs_copied_when_present(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "AGENTS.md").write_text("agent guide", encoding="utf-8")
    (repo / "ROADMAP.md").write_text("roadmap", encoding="utf-8")
    # CONTRIBUTING.md and PLAN.md intentionally absent.

    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    assert (out / "docs" / "AGENTS.md").read_text(encoding="utf-8") == "agent guide"
    assert (out / "docs" / "ROADMAP.md").read_text(encoding="utf-8") == "roadmap"
    assert not (out / "docs" / "CONTRIBUTING.md").exists()
    assert not (out / "docs" / "PLAN.md").exists()


def test_build_site_is_idempotent_when_rerun(tmp_path):
    repo = make_repo(tmp_path)
    write_species(repo, "vulpes-vulpes", "red fox", "Mammalia", "quadruped")
    out = tmp_path / "_site"

    build_site.build_site(repo, out)
    build_site.build_site(repo, out)

    index = json.loads((out / "species" / "index.json").read_text(encoding="utf-8"))
    assert [e["slug"] for e in index] == ["vulpes-vulpes"]


def test_behaviors_index_lists_every_shared_program(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "behaviors" / "bt-other-v1.json").write_text(
        json.dumps(
            {
                "id": "bt-other-v1",
                "kind": "bt",
                "description": "Another shared program.",
                "params": {"flee_m": 6},
            }
        ),
        encoding="utf-8",
    )

    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    index = json.loads((out / "behaviors" / "index.json").read_text(encoding="utf-8"))
    ids = {e["id"] for e in index}
    assert ids == {"fsm-test-v1", "bt-other-v1"}

    other = next(e for e in index if e["id"] == "bt-other-v1")
    assert other["kind"] == "bt"
    assert other["description"] == "Another shared program."
    assert other["params"] == {"flee_m": 6}
    assert other["path"] == "behaviors/bt-other-v1.json"
    assert (out / "behaviors" / "bt-other-v1.json").is_file()


def test_refuses_out_dir_equal_to_repo_root(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc = build_site.main(["--out", str(repo), "--repo-root", str(repo)])
    assert rc == 2
    assert "unsafe" in capsys.readouterr().err
    # The would-be-deleted sources must still be intact.
    assert (repo / "schema" / "v0.1" / "species.schema.json").is_file()
    assert (repo / "behaviors" / "fsm-test-v1.json").is_file()


def test_refuses_out_dir_that_is_repo_root_via_dot(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc = build_site.main(["--out", ".", "--repo-root", str(repo)])
    assert rc == 2
    assert (repo / "schema" / "v0.1" / "species.schema.json").is_file()


def test_refuses_out_dir_that_is_an_ancestor_of_repo_root(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc = build_site.main(["--out", str(tmp_path), "--repo-root", str(repo)])
    assert rc == 2
    assert (repo / "site" / "index.html").is_file()


def test_refuses_out_dir_equal_to_a_source_dir(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc = build_site.main(["--out", str(repo / "species"), "--repo-root", str(repo)])
    assert rc == 2


def test_refuses_out_dir_inside_a_source_dir(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc = build_site.main(["--out", str(repo / "schema" / "nested"), "--repo-root", str(repo)])
    assert rc == 2
    assert (repo / "schema" / "v0.1" / "species.schema.json").is_file()


def test_allows_normal_out_dir_next_to_repo(tmp_path):
    repo = make_repo(tmp_path)
    out = tmp_path / "_site"
    rc = build_site.main(["--out", str(out), "--repo-root", str(repo)])
    assert rc == 0
    assert (out / "index.html").is_file()


def test_unsafe_out_dir_reason_helper_directly():
    repo_root = Path("/repo")
    assert build_site.unsafe_out_dir_reason(Path("/repo"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/repo/schema"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/repo/schema/nested"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/repo/species"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/repo/behaviors"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/repo/site"), repo_root) is not None
    assert build_site.unsafe_out_dir_reason(Path("/somewhere/_site"), repo_root) is None
    assert build_site.unsafe_out_dir_reason(Path("/repo_other"), repo_root) is None


def test_behaviors_index_skips_malformed_program(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "behaviors" / "broken.json").write_text("{not valid json", encoding="utf-8")

    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    index = json.loads((out / "behaviors" / "index.json").read_text(encoding="utf-8"))
    assert [e["id"] for e in index] == ["fsm-test-v1"]
    assert "broken" in capsys.readouterr().err


def test_locales_index_lists_every_locale_with_common_names(tmp_path):
    repo = make_repo(tmp_path)
    write_species(repo, "vulpes-vulpes", "red fox", "Mammalia", "quadruped")
    locale_dir = repo / "locales" / "test-town"
    locale_dir.mkdir(parents=True)
    (locale_dir / "locale.json").write_text(
        json.dumps(
            {
                "id": "test-town",
                "name": "A test garden",
                "country": "GB",
                "activity_region": "GB-ENG",
                "plot_template": "rowhouse-garden",
                "koppen": "Cfb",
                "public_lat": 51.51,
                "public_lon": -0.13,
                "blurb": "A small garden.",
                "species": ["vulpes-vulpes", "bufo-bufo"],
                "flora_wishlist": ["Hedera helix"],
                "contributors": [{"name": "someone"}],
            }
        ),
        encoding="utf-8",
    )
    (repo / "locales" / "not-a-locale").mkdir()
    out = tmp_path / "_site"
    build_site.build_site(repo, out)

    index = json.loads((out / "locales" / "index.json").read_text(encoding="utf-8"))
    assert [e["id"] for e in index] == ["test-town"]
    entry = index[0]
    assert entry["species"] == [
        {"slug": "vulpes-vulpes", "common_name_en": "red fox"},
        {"slug": "bufo-bufo", "common_name_en": ""},
    ]
    assert entry["contributors"] == ["someone"]
    assert entry["path"] == "locales/test-town/locale.json"
    assert (out / "locales" / "test-town" / "locale.json").is_file()


def test_locales_index_empty_without_locales_dir(tmp_path):
    repo = make_repo(tmp_path)
    out = tmp_path / "_site"
    build_site.build_site(repo, out)
    assert json.loads((out / "locales" / "index.json").read_text(encoding="utf-8")) == []


def test_locales_index_tolerates_null_lists(tmp_path):
    repo = make_repo(tmp_path)
    locale_dir = repo / "locales" / "odd-town"
    locale_dir.mkdir(parents=True)
    (locale_dir / "locale.json").write_text(
        json.dumps({"id": "odd-town", "species": None, "flora_wishlist": None, "contributors": None}),
        encoding="utf-8",
    )
    out = tmp_path / "_site"
    build_site.build_site(repo, out)
    entry = json.loads((out / "locales" / "index.json").read_text(encoding="utf-8"))[0]
    assert entry["species"] == [] and entry["flora_wishlist"] == [] and entry["contributors"] == []
