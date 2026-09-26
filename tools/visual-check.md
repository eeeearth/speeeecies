# tools/visual_check.py

Renders a species' block-mesh model in several poses and camera angles with a
headless browser, then scores each image zero-shot against the species' own
name and a few look-alike ("confusable") species using
[BioCLIP](https://imageomics.github.io/bioclip-demo/), a CLIP-family vision
model trained on the Tree of Life. Runs entirely on CPU.

**This is advisory, not a gate.** The block models are simple, low-poly boxes
in flat colours -- they are nothing like the photographs BioCLIP was trained
on, so scores are usually low even for a correct model, and `visual_check.py`
never fails the run because of a low score (it exits 0 unless something
actually breaks). What it is good for: catching *gross* errors -- a bird
whose model comes out looking more like a fish or a lizard than like any
bird, a body plan mismatch, a palette that makes two very different animals
score identically. Read the per-pose table for a wildly wrong top label or a
target probability near zero across every pose, not for an absolute score.

## Usage

```
uv run tools/visual_check.py <slug> [options]
```

First time only (reuses the browser install if you already have Playwright
1.62.x's Chromium cached under `~/.cache/ms-playwright`):

```
uv run --with playwright==1.62.0 playwright install chromium
```

Options:

| Flag | Default | What |
|---|---|---|
| `--model` | `hf-hub:imageomics/bioclip` | open_clip hf-hub model string; also accepts `hf-hub:imageomics/bioclip-2` |
| `--poses` | every pose in `look.poses` | comma-separated pose names |
| `--yaws` | `35,90,200` | comma-separated camera yaw angles (degrees) |
| `--write` | off | write `species/<slug>/visual-check.json` |
| `--images-dir` | `$SPEEEECIES_SCRATCH/<slug>` or `~/tmp/speeeecies-visual-check/<slug>` | where rendered PNGs go |
| `--root` | repo root (two directories up from this script) | |
| `--port` | `18171` | local preview server port; binds 127.0.0.1 only |

Rendered PNGs are scratch files and are never written inside the repo.
Point `--images-dir` or `$SPEEEECIES_SCRATCH` at wherever you keep scratch
files.

Exit codes: 0 on a completed run (including a run with poor scores), 1 on a
real error (bad species record, previewer failed, browser or model error), 2
on a usage error.

## What it does

1. Reads `species/<slug>/species.json` for the target's scientific name,
   English common name, taxonomy class, `look.poses`, and any
   `extensions.visual_check.confusables`.
2. Builds the label set: the target as `"<scientific name> (<common name>)"`,
   plus confusable labels (dropping the target itself if it appears there).
3. Runs `tools/build_site.py` into a throwaway directory next to
   `--images-dir`, serves it over `http://127.0.0.1:<port>` (loopback only),
   and opens `preview.html?species=<slug>&pose=<pose>&yaw=<yaw>&pitch=15&phase=0.25&shot=1`
   at 512x512 in headless Chromium for every pose x yaw combination.
4. Waits for `window.__previewReady`; fails clearly (and only then, non-zero
   exit) on `window.__previewError`.
5. Screenshots each frame, then scores every image against every label with
   `bioclip.CustomLabelsClassifier` (CPU, 4 threads).
6. Prints a Markdown table (pose, yaw, top label, top score, target
   probability) and a summary (mean target probability, rank-1 rate).

### Previewer URL contract

`site/preview.html` (see its top-level script) accepts these query
parameters, all optional:

| Param | Meaning |
|---|---|
| `species` | A species slug (`species/<slug>/species.json`); loaded via `fetch`. |
| `pose` | Pose name from the species' `look.poses` (default `idle`). |
| `yaw`, `pitch` | Camera angles in degrees (defaults `35`, `15`). |
| `phase` | Freezes the pose's animation cycle at this fraction in [0,1) instead of playing it, for a stable screenshot. |
| `shot` | `1` hides the header/side panel and sets `window.__previewReady = true` once the model has rendered, or `window.__previewError` (a string) if it failed -- the two globals headless callers (this script) poll for. |

This is the whole contract any headless caller needs; there is no separate
spec file for it.
7. With `--write`, writes `species/<slug>/visual-check.json`:

```json
{
  "generated_by": "tools/visual_check.py",
  "date": "2026-09-25",
  "device": "cpu",
  "model": "hf-hub:imageomics/bioclip",
  "model_license": "MIT",
  "target_label": "Vulpes vulpes (red fox)",
  "labels": ["Vulpes vulpes (red fox)", "Canis lupus familiaris (domestic dog)", "..."],
  "images": [
    {
      "image": "idle-35.png",
      "pose": "idle",
      "yaw": 35,
      "top_label": "Vulpes vulpes (red fox)",
      "top_score": 0.41,
      "probabilities": {"Vulpes vulpes (red fox)": 0.41, "...": 0.1}
    }
  ],
  "summary": {"mean_target_probability": 0.30, "rank1_rate": 0.5, "n_images": 6},
  "advisory": true
}
```

Image entries carry **names only** (`"idle-35.png"`), never the absolute
scratch path they were rendered to -- this repo is public and never gets
local paths written into it.

## Confusables

Default confusables (dropped if they'd equal the target) by
`taxonomy.class`:

- **Mammalia**: *Canis lupus familiaris* (domestic dog), *Felis catus* (cat),
  *Sciurus vulgaris* (red squirrel), *Lepus europaeus* (brown hare)
- **Aves**: *Turdus merula*, *Passer domesticus*, *Parus major*, *Columba
  livia*
- **Amphibia**: *Rana temporaria*, *Lissotriton vulgaris*, *Epidalea
  calamita*
- **Reptilia**: *Podarcis muralis*, *Natrix natrix*, *Anguis fragilis* --
  not enumerated in PLAN.md; chosen here as reasonable, common defaults
- **Insecta**: *Apis mellifera*, *Vespula vulgaris*, *Coccinella
  septempunctata*, *Pieris rapae* -- also not enumerated in PLAN.md, same
  caveat

A species can override this with its own list under
`extensions.visual_check.confusables` (free-form per the schema), either as
plain label strings or as `{"id": "<scientific name>", "common_name_en":
"<name>"}` objects.

## CPU-only, resource notes

Hard rule, enforced in code: `CUDA_VISIBLE_DEVICES` is forced to `""` before
any heavy import, every classifier call passes `device="cpu"`, and
`torch.set_num_threads(4)` is set before scoring. Model weights cache in the
default Hugging Face cache (`~/.cache/huggingface`), not under this repo or
`/tmp`.

Measured on a desktop CPU with `/usr/bin/time -v`, `hf-hub:imageomics/bioclip`,
4 threads, no GPU:

| Run | wall clock | peak RSS |
|---|---|---|
| Single 512x512 image, model not yet downloaded (cold) | ~28s | ~1.6 GiB |
| Single 512x512 image, warm HF cache | ~14s | ~1.6 GiB |
| Full end-to-end (`species/vulpes-vulpes`, all 6 poses x 3 yaws = 18 images: render + score), warm caches | ~33s | ~1.6 GiB |

The fixed cost is almost entirely model load (a few seconds) plus browser
startup; scoring itself runs at roughly 5 images/s once the model is loaded,
and rendering each frame in headless Chromium adds roughly 0.1-0.3s per
image on top. Peak RSS stays flat around 1.6 GiB regardless of image count.

Downloads, one-time:

| | size |
|---|---|
| PyTorch (CPU wheel, `+cpu`, verified in `uv.lock`/cache -- not the CUDA build) | ~190 MB |
| `open-clip-torch`, `torchvision` (CPU), `timm`, `pandas`, `pillow`, `playwright` | ~60 MB |
| BioCLIP weights (`imageomics/bioclip`, `open_clip_pytorch_model.bin`) | ~571 MB |
| **Total** | **~820 MB** |

`--model hf-hub:imageomics/bioclip-2` is also MIT-licensed and slightly newer
(trained on the larger TreeOfLife-200M), but its checkpoint alone is ~1.7 GB
-- about three times the download of `bioclip`, so the smaller, original
model is the default. Pass `--model hf-hub:imageomics/bioclip-2` explicitly
if you want it.

Chromium: reuses whatever build is already cached under
`~/.cache/ms-playwright` for Playwright 1.62.0 (pinned in this script's PEP
723 metadata) -- no browser download needed if you already have it; ~150-300
MB if you don't.

## Licences

| Component | Licence | Source |
|---|---|---|
| `pybioclip` (code) | MIT | `LICENSE` file, github.com/Imageomics/pybioclip |
| `imageomics/bioclip` weights | MIT | model card, huggingface.co/imageomics/bioclip |
| `imageomics/bioclip-2` weights | MIT | model card, huggingface.co/imageomics/bioclip-2 |
| TreeOfLife-10M (bioclip's training data) | Mixed, per-image; images and their licences (predominantly CC BY variants) drawn from iNat21, BIOSCAN-1M and Encyclopedia of Life, recorded per-image in the dataset's `licenses.csv` | dataset card, huggingface.co/datasets/imageomics/TreeOfLife-10M |
| TreeOfLife-200M (bioclip-2's training data) | Dataset repo tagged CC0-1.0 on Hugging Face; consult the dataset card for any per-image caveats before treating individual images as CC0 | dataset card, huggingface.co/datasets/imageomics/TreeOfLife-200M |

Both model checkpoints are MIT (tier 1, score 1.0 under
`schema/v0.1/licenses.json`). We do not redistribute training data or model
weights -- they are downloaded to the local Hugging Face cache at run time --
so only the `pybioclip` code licence and the model weight licence
(`model_license` in `visual-check.json`) are load-bearing for this repo's own
licence policy.
