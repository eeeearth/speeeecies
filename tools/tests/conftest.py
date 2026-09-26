"""Shared pytest fixtures for tools/validate.py tests.

Builds a hermetic fake repo root under `tmp_path`: the real `schema/v0.1`
and `behaviors/` are copied in, and tests write `species/<slug>/species.json`
under it. The validator module is imported directly from its file (it is a
PEP 723 script, so plain `import` also works; importlib keeps this test
suite independent of `sys.path`).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_PY = REPO_ROOT / "tools" / "validate.py"


def _load_validate_module():
    spec = importlib.util.spec_from_file_location("speeeecies_validate", VALIDATE_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def validate_module():
    return _load_validate_module()


@pytest.fixture
def fake_root(tmp_path) -> Path:
    """A tmp_path pre-populated with the real schema/ and behaviors/ dirs."""
    shutil.copytree(REPO_ROOT / "schema", tmp_path / "schema")
    shutil.copytree(REPO_ROOT / "behaviors", tmp_path / "behaviors")
    (tmp_path / "species").mkdir()
    return tmp_path


def minimal_species(slug: str = "vulpes-vulpes") -> dict:
    """A minimal species record that should pass every check cleanly."""
    return {
        "format": "speeeecies/species",
        "format_version": "0.1",
        "id": "Vulpes vulpes",
        "slug": slug,
        "common_names": {"en": "Red fox"},
        "taxonomy": {
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "class": "Mammalia",
            "order": "Carnivora",
            "family": "Canidae",
            "genus": "Vulpes",
        },
        "external": {"gbif_usage_key": 5219243, "inat_taxon_id": 42069},
        "range": {"native": ["GB", "US"]},
        "traits": {
            "body_plan": "Vertebrate",
            "limb_count": 4,
            "locomotion_modes": ["Walk", "Gallop"],
            "thermoregulation": "Endotherm",
            "skin": "Fur",
            "flight": "None",
            "mass_kg": 5.5,
            "mass_range_kg": [4.0, 8.0],
            "length_m": 1.1,
            "shoulder_height_m": 0.4,
            "speed_ms": {"walk": 1.5, "gallop": 14.0},
            "lifespan_y": 5,
            "diet": {"invertebrate": 0.3, "vertebrate": 0.5, "fruit": 0.2},
            "social": {"structure": "Solitary", "group_size": [1, 1]},
            "activity_pattern": "Crepuscular",
            "defense": "Flee",
            "wariness": 0.7,
        },
        "habitat": {
            "use": {"ground": 1.0},
            "resources": [
                {"tag": "small_vertebrate", "kind": "Predation", "weight": 0.5},
                {"tag": "invertebrate", "kind": "Predation", "weight": 0.3},
                {"tag": "burrow", "kind": "Shelter", "weight": 1.0},
            ],
            "human_tolerance": {"urban_affinity": "Adapter"},
            "density_per_ha": {"min": 0.1, "typical": 0.5, "max": 2.0},
        },
        "seasonal": {
            "strategy": "ActiveYearRound",
            "phases": [{"name": "mating", "start": "01-01", "end": "02-15"}],
            "life_stages": [{"stage": "Juvenile"}, {"stage": "Adult"}],
        },
        "activity": {
            "regions": [
                {
                    "region": "GB",
                    "monthly": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
                    "method": "mean(gbif_share, inat_share)",
                    "sources": ["src-activity"],
                }
            ]
        },
        "behavior": {"program": "fsm-ground-forager-v1", "params": {}},
        "vocalizations": [
            {
                "call_id": "bark",
                "context": "Bark",
                "season_months": [],
                "time_windows": [],
                "cooldown_s": 30,
                "description": "A sharp triple bark used at night.",
            }
        ],
        "look": {
            "body_plan": "quadruped",
            "proportions": {},
            "palette": {"body": "#a04020"},
            "poses": {"idle": {}, "walk": {}, "gallop": {}, "rest": {}},
        },
        "sources": [
            {
                "id": "src-main",
                "url": "https://example.org/fox",
                "title": "Fox facts",
                "license": "CC0-1.0",
                "accessed": "2026-01-01",
            },
            {
                "id": "src-activity",
                "url": "https://example.org/activity",
                "title": "Activity data",
                "license": "CC0-1.0",
                "accessed": "2026-01-01",
            },
        ],
        "provenance": {
            "taxonomy": {"sources": ["src-main"], "confidence": "High"},
            "external": {"sources": ["src-main"], "confidence": "High"},
            "range": {"sources": ["src-main"], "confidence": "High"},
            "traits": {"sources": ["src-main"], "confidence": "Medium"},
            "habitat": {"sources": ["src-main"], "confidence": "Medium"},
            "seasonal.strategy": {"sources": ["src-main"], "confidence": "Medium"},
            "seasonal.phases": {"sources": ["src-main"], "confidence": "Low"},
            "seasonal.life_stages": {"sources": ["src-main"], "confidence": "Low"},
            "vocalizations.bark": {"sources": ["src-main"], "confidence": "Medium"},
            "look": {"sources": [], "confidence": "Low", "derived": True, "note": "authored for the previewer"},
            "behavior": {"sources": [], "confidence": "Low", "derived": True, "note": "chosen by contributor"},
        },
    }


def write_species(root: Path, slug: str, species: dict) -> Path:
    species_dir = root / "species" / slug
    species_dir.mkdir(parents=True, exist_ok=True)
    (species_dir / "species.json").write_text(json.dumps(species, indent=2), encoding="utf-8")
    return species_dir


@pytest.fixture
def make_species():
    def _make(slug: str = "vulpes-vulpes", **overrides) -> dict:
        species = minimal_species(slug)
        species.update(copy.deepcopy(overrides))
        return species

    return _make
