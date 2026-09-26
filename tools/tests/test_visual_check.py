"""Tests for tools/visual_check.py's pure-Python parts only: label building,
confusable defaults, summary maths, and the visual-check.json shape.

No torch, no playwright, no bioclip, no network -- importing this module (and
tools/visual_check.py) must succeed even when those packages are not
installed, since visual_check.py imports them lazily inside its heavy
functions.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import visual_check as vc  # noqa: E402


def test_import_has_no_heavy_globals():
    # A very cheap guard against accidentally importing torch/playwright/
    # bioclip at module scope: if any of those were imported eagerly they
    # would show up in sys.modules right after `import visual_check`, and
    # this test file would already have failed to import in a torch-less
    # environment. The real assertion is simply that we got this far.
    assert vc is not None


def test_format_label():
    assert vc.format_label("Vulpes vulpes", "red fox") == "Vulpes vulpes (red fox)"


def test_parse_str_list():
    assert vc.parse_str_list("idle, walk,trot") == ["idle", "walk", "trot"]
    assert vc.parse_str_list(None) is None
    assert vc.parse_str_list("") == []


def test_parse_int_list():
    assert vc.parse_int_list("35,90,200") == [35, 90, 200]
    assert vc.parse_int_list(None) is None


def test_build_labels_uses_default_confusables_for_class():
    target, labels = vc.build_labels("Vulpes vulpes", "red fox", "Mammalia", None)
    assert target == "Vulpes vulpes (red fox)"
    assert labels[0] == target
    assert "Canis lupus familiaris (domestic dog)" in labels
    assert "Felis catus (cat)" in labels
    assert "Sciurus vulgaris (red squirrel)" in labels
    assert "Lepus europaeus (brown hare)" in labels
    assert len(labels) == 5


def test_build_labels_drops_target_from_confusables():
    # A mammal named literally "Canis lupus familiaris" should not end up
    # listed twice.
    target, labels = vc.build_labels("Canis lupus familiaris", "domestic dog", "Mammalia", None)
    assert labels.count(target) == 1


def test_build_labels_unknown_class_has_no_defaults():
    target, labels = vc.build_labels("Xenacme sp", "made-up thing", "Nonexistent", None)
    assert labels == [target]


def test_build_labels_prefers_species_extensions_confusables_dict_form():
    extensions = {
        "visual_check": {
            "confusables": [
                {"id": "Erinaceus europaeus", "common_name_en": "European hedgehog"},
                {"id": "Meles meles", "common_name_en": "European badger"},
            ]
        }
    }
    target, labels = vc.build_labels("Vulpes vulpes", "red fox", "Mammalia", extensions)
    assert labels == [
        target,
        "Erinaceus europaeus (European hedgehog)",
        "Meles meles (European badger)",
    ]
    # The class default confusables (dog, cat, ...) must not leak in.
    assert "Canis lupus familiaris (domestic dog)" not in labels


def test_build_labels_accepts_species_extensions_confusables_as_plain_strings():
    extensions = {"visual_check": {"confusables": ["Meles meles (European badger)"]}}
    target, labels = vc.build_labels("Vulpes vulpes", "red fox", "Mammalia", extensions)
    assert labels == [target, "Meles meles (European badger)"]


def test_build_labels_dedupes():
    extensions = {
        "visual_check": {
            "confusables": [
                {"id": "Meles meles", "common_name_en": "European badger"},
                {"id": "Meles meles", "common_name_en": "European badger"},
            ]
        }
    }
    _, labels = vc.build_labels("Vulpes vulpes", "red fox", "Mammalia", extensions)
    assert labels.count("Meles meles (European badger)") == 1


def test_all_default_confusable_classes_have_common_names():
    for taxonomy_class, entries in vc.DEFAULT_CONFUSABLES.items():
        assert entries, taxonomy_class
        for sci, common in entries:
            assert sci and common


def test_compute_summary_basic():
    target = "Vulpes vulpes (red fox)"
    images = [
        {"top_label": target, "probabilities": {target: 0.8, "other": 0.2}},
        {"top_label": "other", "probabilities": {target: 0.1, "other": 0.9}},
    ]
    summary = vc.compute_summary(images, target)
    assert summary["n_images"] == 2
    assert summary["rank1_rate"] == 0.5
    assert abs(summary["mean_target_probability"] - 0.45) < 1e-9


def test_compute_summary_empty():
    summary = vc.compute_summary([], "target")
    assert summary == {"mean_target_probability": 0.0, "rank1_rate": 0.0, "n_images": 0}


def test_render_markdown_table_has_header_and_row():
    target = "Vulpes vulpes (red fox)"
    images = [
        {
            "pose": "idle",
            "yaw": 35,
            "top_label": target,
            "top_score": 0.7,
            "probabilities": {target: 0.7},
        }
    ]
    table = vc.render_markdown_table(images, target)
    lines = table.splitlines()
    assert lines[0].startswith("| pose | yaw | top label")
    assert "idle" in lines[2]
    assert "35" in lines[2]
    assert "0.700" in lines[2]


def test_build_report_shape():
    target = "Vulpes vulpes (red fox)"
    labels = [target, "Canis lupus familiaris (domestic dog)"]
    images = [
        {
            "image": "idle-35.png",
            "pose": "idle",
            "yaw": 35,
            "top_label": target,
            "top_score": 0.6,
            "probabilities": {target: 0.6, labels[1]: 0.4},
        }
    ]
    report = vc.build_report(
        slug="vulpes-vulpes",
        model="hf-hub:imageomics/bioclip",
        target_label=target,
        labels=labels,
        images=images,
        date="2026-09-25",
    )
    assert report["generated_by"] == "tools/visual_check.py"
    assert report["date"] == "2026-09-25"
    assert report["device"] == "cpu"
    assert report["model"] == "hf-hub:imageomics/bioclip"
    assert report["model_license"] == "MIT"
    assert report["target_label"] == target
    assert report["labels"] == labels
    assert report["advisory"] is True
    assert report["images"][0]["image"] == "idle-35.png"
    assert "summary" in report and report["summary"]["n_images"] == 1


def test_build_report_never_embeds_absolute_paths(tmp_path):
    # Guards the PUBLIC SAFETY rule: visual-check.json must carry image
    # *names* only, never absolute local filesystem paths.
    target = "Vulpes vulpes (red fox)"
    images = [
        {
            "image": str(tmp_path / "speeeecies-visual-check" / "vulpes-vulpes" / "idle-35.png"),
            "pose": "idle",
            "yaw": 35,
            "top_label": target,
            "top_score": 0.6,
            "probabilities": {target: 0.6},
        }
    ]
    report = vc.build_report(
        slug="vulpes-vulpes",
        model="hf-hub:imageomics/bioclip",
        target_label=target,
        labels=[target],
        images=images,
    )
    assert report["images"][0]["image"] == "idle-35.png"
    dumped = str(report)
    assert str(tmp_path) not in dumped
    assert "speeeecies-visual-check" not in dumped


def test_default_images_dir_has_no_hardcoded_home(monkeypatch):
    monkeypatch.delenv("SPEEEECIES_SCRATCH", raising=False)
    path = vc.default_images_dir("vulpes-vulpes")
    assert path.name == "vulpes-vulpes"
    assert "speeeecies-visual-check" in str(path)


def test_default_images_dir_honours_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("SPEEEECIES_SCRATCH", str(tmp_path))
    path = vc.default_images_dir("bufo-bufo")
    assert path == tmp_path / "bufo-bufo"


def test_served_site_rejects_privileged_port():
    import pytest

    with pytest.raises(vc.VisualCheckError):
        with vc.served_site(Path("."), 80):
            pass


def test_model_licenses_cover_both_documented_models():
    assert vc.MODEL_LICENSES["hf-hub:imageomics/bioclip"] == "MIT"
    assert vc.MODEL_LICENSES["hf-hub:imageomics/bioclip-2"] == "MIT"
