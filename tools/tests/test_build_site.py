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
