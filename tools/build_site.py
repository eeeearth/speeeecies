#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Assemble the speeeecies GitHub Pages site into _site/.

Copies site/*, schema/, behaviors/, species/, locales/ into the output directory,
writes <out>/species/index.json (a summary of every species/<slug>/species.json),
<out>/locales/index.json (a summary of every locales/<id>/locale.json)
and <out>/ATTRIBUTION.md (a concatenation of every species/*/ATTRIBUTION.md,
with a header). Also copies README.md, AGENTS.md, CONTRIBUTING.md, ROADMAP.md, PLAN.md and
docs/locale-richness.md into <out>/docs/ when present. Stdlib only.

Usage: python3 tools/build_site.py [--out _site] [--repo-root DIR]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def repo_root_from(start: Path) -> Path:
    return start.resolve().parent


def copy_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _is_same_or_ancestor(ancestor: Path, other: Path) -> bool:
    """True if `other` is `ancestor` itself, or is nested inside it."""
    try:
        other.relative_to(ancestor)
        return True
    except ValueError:
        return False


def unsafe_out_dir_reason(out_dir: Path, repo_root: Path) -> str | None:
    """Returns a reason string if `out_dir` is unsafe to build into (because
    `build_site()` rmtree's parts of it before copying), else None.

    copy_tree() deletes `dst` (if it already exists) before copying `src`
    into it. `build_site()` calls it with `dst` set to the repo's own
    `schema/`, `behaviors/` and `species/` dirs and every top-level item
    under `site/` -- so an `--out` that resolves to the repo root (or an
    ancestor of it), or to (or inside) any of those source dirs, would
    delete the very sources it is about to copy from."""
    out_dir = out_dir.resolve()
    repo_root = repo_root.resolve()
    if _is_same_or_ancestor(out_dir, repo_root):
        return f"--out resolves to {out_dir}, which is the repo root or an ancestor of it"
    for name in ("site", "schema", "behaviors", "species", "locales"):
        src = repo_root / name
        if _is_same_or_ancestor(src, out_dir):
            return f"--out resolves to {out_dir}, which is (or is inside) {src}"
    return None


def build_species_index(species_dir: Path) -> list[dict]:
    entries = []
    if not species_dir.is_dir():
        return entries
    for child in sorted(species_dir.iterdir()):
        if not child.is_dir():
            continue
        species_json = child / "species.json"
        if not species_json.is_file():
            continue
        try:
            data = json.loads(species_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as err:
            print(f"warning: skipping {species_json}: {err}", file=sys.stderr)
            continue
        slug = data.get("slug", child.name)
        entries.append(
            {
                "slug": slug,
                "id": data.get("id", ""),
                "common_name_en": (data.get("common_names") or {}).get("en", ""),
                "class": ((data.get("taxonomy") or {}).get("class", "")),
                "body_plan": ((data.get("look") or {}).get("body_plan", "")),
                "path": f"species/{slug}/species.json",
            }
        )
    return entries


def build_flora_summary(flora_catalog_json: Path) -> list[dict]:
    """A short summary of a locale's flora-catalog.json entries for
    site/locales.html: common name, the local species it stands in for,
    and whether it's evergreen. Returns [] if the file is missing,
    unreadable, or not shaped as expected -- the site falls back to
    flora_wishlist in that case."""
    if not flora_catalog_json.is_file():
        return []
    try:
        data = json.loads(flora_catalog_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as err:
        print(f"warning: skipping {flora_catalog_json}: {err}", file=sys.stderr)
        return []
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []
    summary = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        common_name = entry.get("common_name")
        if not isinstance(common_name, str) or not common_name:
            continue
        summary.append(
            {
                "common_name": common_name,
                "stand_in_for": entry.get("stand_in_for") if isinstance(entry.get("stand_in_for"), str) else "",
                "evergreen": bool(entry.get("evergreen")),
            }
        )
    return summary


def build_locales_index(locales_dir: Path, species_index: list[dict]) -> list[dict]:
    """A summary of every locales/<id>/locale.json for site/locales.html,
    with each listed species' common name resolved from the species index."""
    common_names = {e["slug"]: e["common_name_en"] for e in species_index}
    entries = []
    if not locales_dir.is_dir():
        return entries
    for child in sorted(locales_dir.iterdir()):
        locale_json = child / "locale.json"
        if not locale_json.is_file():
            continue
        try:
            data = json.loads(locale_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as err:
            print(f"warning: skipping {locale_json}: {err}", file=sys.stderr)
            continue
        entries.append(
            {
                "id": data.get("id", child.name),
                "name": data.get("name", ""),
                "country": data.get("country", ""),
                "activity_region": data.get("activity_region", ""),
                "plot_template": data.get("plot_template", ""),
                "koppen": data.get("koppen", ""),
                "public_lat": data.get("public_lat"),
                "public_lon": data.get("public_lon"),
                "blurb": data.get("blurb", ""),
                "species": [
                    {"slug": slug, "common_name_en": common_names.get(slug, "")}
                    for slug in data.get("species") or []
                    if isinstance(slug, str)
                ],
                "flora_wishlist": [f for f in data.get("flora_wishlist") or [] if isinstance(f, str)],
                "flora": build_flora_summary(child / "flora-catalog.json"),
                "contributors": [
                    c.get("name", "") for c in data.get("contributors") or [] if isinstance(c, dict)
                ],
                "path": f"locales/{child.name}/locale.json",
            }
        )
    return entries


def build_behaviors_index(behaviors_dir: Path) -> list[dict]:
    """A summary of every shared program in behaviors/*.json: id, kind,
    description, params -- so site/behaviors.html can list the real shared
    programs instead of a hard-coded file list."""
    entries = []
    if not behaviors_dir.is_dir():
        return entries
    for child in sorted(behaviors_dir.glob("*.json")):
        try:
            data = json.loads(child.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as err:
            print(f"warning: skipping {child}: {err}", file=sys.stderr)
            continue
        entries.append(
            {
                "id": data.get("id", child.stem),
                "kind": data.get("kind", ""),
                "description": data.get("description", ""),
                "params": data.get("params", {}),
                "path": f"behaviors/{child.name}",
            }
        )
    return entries


def build_attribution(species_dir: Path) -> str:
    header = (
        "# Attribution\n\n"
        "Combined attribution for every species contributed to speeeecies. "
        "Generated by tools/build_site.py; do not edit by hand.\n"
    )
    parts = [header]
    if species_dir.is_dir():
        for child in sorted(species_dir.iterdir()):
            attribution = child / "ATTRIBUTION.md"
            if attribution.is_file():
                parts.append(f"\n---\n\n## {child.name}\n\n")
                parts.append(attribution.read_text(encoding="utf-8"))
    return "".join(parts)


def build_site(repo_root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    site_src = repo_root / "site"
    if not site_src.is_dir():
        raise SystemExit(f"error: {site_src} does not exist")
    for item in site_src.iterdir():
        dst = out_dir / item.name
        if item.is_dir():
            copy_tree(item, dst)
        else:
            shutil.copy2(item, dst)

    copy_tree(repo_root / "schema", out_dir / "schema")
    copy_tree(repo_root / "behaviors", out_dir / "behaviors")
    copy_tree(repo_root / "species", out_dir / "species")
    copy_tree(repo_root / "locales", out_dir / "locales")

    behaviors_dir = out_dir / "behaviors"
    behaviors_dir.mkdir(parents=True, exist_ok=True)
    behaviors_index = build_behaviors_index(repo_root / "behaviors")
    (behaviors_dir / "index.json").write_text(
        json.dumps(behaviors_index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    species_dir = out_dir / "species"
    species_dir.mkdir(parents=True, exist_ok=True)
    index = build_species_index(repo_root / "species")
    (species_dir / "index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )

    locales_dir = out_dir / "locales"
    locales_dir.mkdir(parents=True, exist_ok=True)
    locales_index = build_locales_index(repo_root / "locales", index)
    (locales_dir / "index.json").write_text(
        json.dumps(locales_index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    attribution = build_attribution(repo_root / "species")
    (out_dir / "ATTRIBUTION.md").write_text(attribution, encoding="utf-8")

    docs_dir = out_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in ("README.md", "AGENTS.md", "CONTRIBUTING.md", "ROADMAP.md", "PLAN.md"):
        src = repo_root / name
        if src.is_file():
            shutil.copy2(src, docs_dir / name)
    locale_richness_src = repo_root / "docs" / "locale-richness.md"
    if locale_richness_src.is_file():
        shutil.copy2(locale_richness_src, docs_dir / "locale-richness.md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="_site", help="output directory (default: _site)")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="repository root (default: parent of this script's directory)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from(Path(__file__).parent)
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir

    reason = unsafe_out_dir_reason(out_dir, repo_root)
    if reason is not None:
        print(f"error: refusing to build into an unsafe --out ({reason}); this would delete repo sources", file=sys.stderr)
        return 2

    build_site(repo_root, out_dir)
    print(f"built site into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
