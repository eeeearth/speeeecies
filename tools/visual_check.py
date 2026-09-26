#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pybioclip>=2.1.0,<3",
#   "playwright==1.62.0",
#   "pillow>=10,<12",
#   "torch",
#   "torchvision",
# ]
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# torchvision = { index = "pytorch-cpu" }
# ///
"""Render a species' block-mesh model in several poses/angles with a headless
browser and score the images zero-shot with BioCLIP on CPU.

See tools/visual-check.md for usage, resource notes and licences.

Hard machine rules (see tools/visual-check.md for why):
  - Never touch a GPU: CUDA_VISIBLE_DEVICES is forced to "" below, before any
    heavy import, and every model call passes device="cpu".
  - At most 4 CPU threads (torch.set_num_threads(4)).
  - Model weights cache in the default Hugging Face cache (~/.cache/huggingface).
  - Scratch images never go in /tmp and never inside the repo; see --images-dir.
  - The local preview server binds 127.0.0.1 only, on a port in 18170-18179.

Only stdlib is imported at module scope so this file can be imported (for its
pure-Python helpers) without torch, playwright or pybioclip installed -- see
tools/tests/test_visual_check.py. Heavy imports (torch, bioclip, playwright)
happen lazily, inside the functions that need them.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from statistics import mean
from typing import Any

# Forced before any heavy import can happen anywhere in this process, per the
# hard machine rule: never use the GPU. Safe to set unconditionally; it is a
# no-op for the pure-Python code paths tests exercise.
os.environ["CUDA_VISIBLE_DEVICES"] = ""

CPU_THREADS = 4
VIEWPORT_SIZE = 512
PREVIEW_PITCH = 15
PREVIEW_PHASE = 0.25
PREVIEW_READY_TIMEOUT_MS = 30_000
PORT_RANGE = range(18170, 18180)  # 18170-18179 inclusive; see tools/visual-check.md
DEFAULT_PORT = 18171
DEFAULT_YAWS = [35, 90, 200]

DEFAULT_MODEL = "hf-hub:imageomics/bioclip"

# Model weights licence, as recorded on each model's Hugging Face model card.
# See tools/visual-check.md for the full licence write-up (code, weights,
# training data).
MODEL_LICENSES = {
    "hf-hub:imageomics/bioclip": "MIT",
    "hf-hub:imageomics/bioclip-2": "MIT",
}

# Built-in confusable species per taxonomic class, used when a species record
# has no `extensions.visual_check.confusables` of its own. Each tuple is
# (scientific name, English common name). These are common, visually-distinct
# animals a stylised block model of the target might plausibly be mistaken
# for by a human glancing at the preview -- not a claim about BioCLIP's
# nearest neighbours.
DEFAULT_CONFUSABLES: dict[str, list[tuple[str, str]]] = {
    "Mammalia": [
        ("Canis lupus familiaris", "domestic dog"),
        ("Felis catus", "cat"),
        ("Sciurus vulgaris", "red squirrel"),
        ("Lepus europaeus", "brown hare"),
    ],
    "Aves": [
        ("Turdus merula", "Eurasian blackbird"),
        ("Passer domesticus", "house sparrow"),
        ("Parus major", "great tit"),
        ("Columba livia", "rock dove"),
    ],
    "Amphibia": [
        ("Rana temporaria", "common frog"),
        ("Lissotriton vulgaris", "smooth newt"),
        ("Epidalea calamita", "natterjack toad"),
    ],
    # Not enumerated in PLAN.md; chosen here as reasonable, visually varied
    # defaults (a lizard, a snake and a legless lizard often mistaken for one).
    "Reptilia": [
        ("Podarcis muralis", "common wall lizard"),
        ("Natrix natrix", "grass snake"),
        ("Anguis fragilis", "slow worm"),
    ],
    # Also not enumerated in PLAN.md; chosen as common, visually varied insects.
    "Insecta": [
        ("Apis mellifera", "western honey bee"),
        ("Vespula vulgaris", "common wasp"),
        ("Coccinella septempunctata", "seven-spot ladybird"),
        ("Pieris rapae", "small white butterfly"),
    ],
}


class VisualCheckError(RuntimeError):
    """A real error (bad input, render/browser failure, missing files).

    Never raised just because a score is low -- low scores are expected and
    reported, not failures.
    """


# --------------------------------------------------------------------------
# Pure helpers (no heavy imports; safe to unit test without torch/playwright).
# --------------------------------------------------------------------------


def format_label(scientific_name: str, common_name_en: str) -> str:
    return f"{scientific_name} ({common_name_en})"


def parse_str_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def parse_int_list(value: str | None) -> list[int] | None:
    items = parse_str_list(value)
    if items is None:
        return None
    return [int(item) for item in items]


def _format_confusable(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        sci = item.get("id") or item.get("scientific_name")
        common = item.get("common_name_en") or item.get("common_name")
        if sci and common:
            return format_label(sci, common)
        if sci:
            return sci
    raise VisualCheckError(
        f"cannot make a label out of confusable entry: {item!r} "
        "(expected a string, or an object with 'id' and 'common_name_en')"
    )


def build_labels(
    species_id: str,
    common_name_en: str,
    taxonomy_class: str | None,
    extensions: dict | None,
) -> tuple[str, list[str]]:
    """Return (target_label, all_labels) for a species.

    `all_labels` starts with the target, followed by deduplicated confusable
    labels drawn from `extensions.visual_check.confusables` if present, else
    the built-in default for `taxonomy_class`. The target itself is dropped
    from the confusable list if it appears there (e.g. by scientific name).
    """
    target_label = format_label(species_id, common_name_en)

    confusable_items: list[Any]
    ext_confusables = None
    if extensions:
        ext_confusables = (extensions.get("visual_check") or {}).get("confusables")
    if ext_confusables:
        confusable_items = list(ext_confusables)
        confusable_labels = [_format_confusable(item) for item in confusable_items]
    else:
        defaults = DEFAULT_CONFUSABLES.get(taxonomy_class or "", [])
        confusable_labels = [format_label(sci, common) for sci, common in defaults]

    labels = [target_label]
    seen = {target_label}
    for label in confusable_labels:
        if label in seen:
            continue
        # Also drop a confusable that names the target species by scientific
        # name alone (e.g. "Vulpes vulpes" without the common name suffix).
        if label.split(" (", 1)[0] == species_id:
            continue
        seen.add(label)
        labels.append(label)
    return target_label, labels


def compute_summary(images: list[dict], target_label: str) -> dict:
    n = len(images)
    if n == 0:
        return {"mean_target_probability": 0.0, "rank1_rate": 0.0, "n_images": 0}
    target_probs = [float(img.get("probabilities", {}).get(target_label, 0.0)) for img in images]
    rank1 = sum(1 for img in images if img.get("top_label") == target_label)
    return {
        "mean_target_probability": mean(target_probs),
        "rank1_rate": rank1 / n,
        "n_images": n,
    }


def render_markdown_table(images: list[dict], target_label: str) -> str:
    header = "| pose | yaw | top label | top score | target probability |"
    sep = "|---|---|---|---|---|"
    lines = [header, sep]
    for img in images:
        probs = img.get("probabilities", {})
        target_prob = probs.get(target_label, 0.0)
        lines.append(
            f"| {img.get('pose')} | {img.get('yaw')} | {img.get('top_label')} | "
            f"{img.get('top_score', 0.0):.3f} | {target_prob:.3f} |"
        )
    return "\n".join(lines)


def build_report(
    *,
    slug: str,
    model: str,
    target_label: str,
    labels: list[str],
    images: list[dict],
    generated_by: str = "tools/visual_check.py",
    date: str | None = None,
) -> dict:
    """Assemble the exact visual-check.json shape (image paths are names only,
    never absolute paths -- see the PUBLIC SAFETY rule against local paths in
    repo files)."""
    clean_images = []
    for img in images:
        clean_images.append(
            {
                "image": Path(img["image"]).name,
                "pose": img["pose"],
                "yaw": img["yaw"],
                "top_label": img.get("top_label"),
                "top_score": img.get("top_score", 0.0),
                "probabilities": img.get("probabilities", {}),
            }
        )
    return {
        "generated_by": generated_by,
        "date": date or datetime.date.today().isoformat(),
        "device": "cpu",
        "model": model,
        "model_license": MODEL_LICENSES.get(model, "unknown"),
        "target_label": target_label,
        "labels": labels,
        "images": clean_images,
        "summary": compute_summary(clean_images, target_label),
        "advisory": True,
    }


def default_images_dir(slug: str) -> Path:
    """Portable default scratch dir: honours $SPEEEECIES_SCRATCH if set, else
    ~/tmp/speeeecies-visual-check. Never hardcodes a machine-specific path in
    this repo file; override with --images-dir for your own layout (e.g. this
    project's own scratch convention lives outside the repo)."""
    base = os.environ.get("SPEEEECIES_SCRATCH")
    if base:
        root = Path(base)
    else:
        root = Path.home() / "tmp" / "speeeecies-visual-check"
    return root / slug


# --------------------------------------------------------------------------
# Heavy helpers (lazy imports).
# --------------------------------------------------------------------------


def run_build_site(root: Path, out_dir: Path) -> None:
    build_site = root / "tools" / "build_site.py"
    if not build_site.exists():
        raise VisualCheckError(
            f"tools/build_site.py not found under {root} -- it is owned by another "
            "agent in this kit and must exist before an end-to-end run."
        )
    result = subprocess.run(
        [sys.executable, str(build_site), "--out", str(out_dir)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise VisualCheckError(
            f"tools/build_site.py failed (exit {result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


@contextlib.contextmanager
def served_site(directory: Path, port: int):
    if port not in PORT_RANGE:
        raise VisualCheckError(
            f"port {port} is outside the allowed range 18170-18179 for local servers"
        )
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def capture_images(
    base_url: str,
    slug: str,
    poses: list[str],
    yaws: list[int],
    out_dir: Path,
) -> list[dict]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": VIEWPORT_SIZE, "height": VIEWPORT_SIZE})
            for pose in poses:
                for yaw in yaws:
                    url = (
                        f"{base_url}/preview.html?species={slug}&pose={pose}&yaw={yaw}"
                        f"&pitch={PREVIEW_PITCH}&phase={PREVIEW_PHASE}&shot=1"
                    )
                    page.goto(url)
                    try:
                        page.wait_for_function(
                            "window.__previewReady === true || !!window.__previewError",
                            timeout=PREVIEW_READY_TIMEOUT_MS,
                        )
                    except PlaywrightTimeoutError as exc:
                        raise VisualCheckError(
                            f"timed out waiting for the previewer (species={slug} "
                            f"pose={pose} yaw={yaw}): neither __previewReady nor "
                            f"__previewError was set within {PREVIEW_READY_TIMEOUT_MS}ms"
                        ) from exc
                    err = page.evaluate("window.__previewError")
                    if err:
                        raise VisualCheckError(
                            f"previewer reported an error (species={slug} pose={pose} "
                            f"yaw={yaw}): {err}"
                        )
                    name = f"{pose}-{yaw}.png"
                    path = out_dir / name
                    page.screenshot(path=str(path))
                    results.append({"image": name, "pose": pose, "yaw": yaw, "path": str(path)})
        finally:
            browser.close()
    return results


def score_images(image_records: list[dict], labels: list[str], model: str) -> list[dict]:
    import torch

    torch.set_num_threads(CPU_THREADS)
    from bioclip import CustomLabelsClassifier

    classifier = CustomLabelsClassifier(labels, model_str=model, device="cpu")
    paths = [r["path"] for r in image_records]
    raw = classifier.predict(paths)

    per_image: dict[str, dict[str, float]] = {}
    for row in raw:
        per_image.setdefault(row["file_name"], {})[row["classification"]] = float(row["score"])

    scored = []
    for record in image_records:
        probs = per_image.get(record["path"], {})
        if probs:
            top_label = max(probs, key=probs.get)
            top_score = probs[top_label]
        else:
            top_label, top_score = None, 0.0
        scored.append(
            {
                "image": record["image"],
                "pose": record["pose"],
                "yaw": record["yaw"],
                "top_label": top_label,
                "top_score": top_score,
                "probabilities": probs,
            }
        )
    return scored


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def load_species(root: Path, slug: str) -> dict:
    species_path = root / "species" / slug / "species.json"
    if not species_path.exists():
        raise VisualCheckError(f"no species record at {species_path.relative_to(root)}")
    with species_path.open() as f:
        return json.load(f)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a species' block-mesh model in several poses/angles with a "
            "headless browser and score the images zero-shot with BioCLIP on CPU. "
            "Advisory only: exits 0 even on low scores."
        )
    )
    parser.add_argument("slug", help="species directory name, e.g. vulpes-vulpes")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"open_clip hf-hub model string (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--poses",
        default=None,
        help="comma-separated pose names (default: every pose in look.poses)",
    )
    parser.add_argument(
        "--yaws",
        default=",".join(str(y) for y in DEFAULT_YAWS),
        help=f"comma-separated camera yaw angles in degrees (default: {DEFAULT_YAWS})",
    )
    parser.add_argument("--write", action="store_true", help="write species/<slug>/visual-check.json")
    parser.add_argument(
        "--images-dir",
        default=None,
        help="directory for rendered PNGs (default: portable scratch dir; see tools/visual-check.md)",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="repo root (default: two directories up from this script)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"local preview server port, 18170-18179 (default: {DEFAULT_PORT})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    images_dir = Path(args.images_dir).resolve() if args.images_dir else default_images_dir(args.slug)

    try:
        species = load_species(root, args.slug)
        common_name_en = species.get("common_names", {}).get("en")
        if not common_name_en:
            raise VisualCheckError(f"species/{args.slug}/species.json has no common_names.en")
        taxonomy_class = species.get("taxonomy", {}).get("class")
        target_label, labels = build_labels(
            species["id"], common_name_en, taxonomy_class, species.get("extensions")
        )

        poses = parse_str_list(args.poses)
        if poses is None:
            poses = list(species.get("look", {}).get("poses", {}).keys()) or ["idle"]
        yaws = parse_int_list(args.yaws) or DEFAULT_YAWS

        images_dir.mkdir(parents=True, exist_ok=True)
        site_dir = Path(tempfile.mkdtemp(prefix="speeeecies-site-", dir=str(images_dir.parent)))
        try:
            run_build_site(root, site_dir)
            with served_site(site_dir, args.port) as base_url:
                records = capture_images(base_url, args.slug, poses, yaws, images_dir)
            scored = score_images(records, labels, args.model)
        finally:
            shutil.rmtree(site_dir, ignore_errors=True)

        print(render_markdown_table(scored, target_label))
        summary = compute_summary(scored, target_label)
        print(
            f"\nMean target probability: {summary['mean_target_probability']:.3f}  "
            f"Rank-1 rate: {summary['rank1_rate']:.3f}  (n={summary['n_images']})"
        )

        if args.write:
            report = build_report(
                slug=args.slug,
                model=args.model,
                target_label=target_label,
                labels=labels,
                images=scored,
            )
            out_path = root / "species" / args.slug / "visual-check.json"
            with out_path.open("w") as f:
                json.dump(report, f, indent=2)
                f.write("\n")
            print(f"\nwrote {out_path.relative_to(root)}")
    except VisualCheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - surface anything unexpected clearly
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
