#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["zxing-cpp>=2.3,<4", "pillow>=11,<13", "pymupdf>=1.26,<2"]
# ///
"""Decode the shipped PNGs and rasterized PDF, comparing exact QR payloads.

Run: uv run tools/verify_contribution_kit.py
No camera, external service or PDF renderer executable is needed.
"""
import json
from pathlib import Path

import pymupdf
from PIL import Image
import zxingcpp


def main():
    kit = Path(__file__).resolve().parents[1] / 'site' / 'contribute'
    manifest = json.loads((kit / 'qr-manifest.json').read_text())
    entries = manifest['variants']
    fallback = manifest['fallback']
    for entry in entries + [fallback]:
        decoded = zxingcpp.read_barcodes(Image.open(kit / (entry['id'] + '.png')))
        assert [item.text for item in decoded] == [entry['payload']], entry['id']
    document = pymupdf.open(kit / 'speeeecies-contribution-qr.pdf')
    assert len(document) == len(entries) + 2, 'Wrong PDF page count'
    prompt = ' '.join((kit / 'prompt.txt').read_text().split())
    for page, entry in zip(document, entries):
        # 150 dpi also checks modules after resampling, at a modest print resolution.
        pixmap = page.get_pixmap(dpi=150, alpha=False)
        raster = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
        decoded = zxingcpp.read_barcodes(raster)
        assert sorted(item.text for item in decoded) == sorted([entry['payload'], fallback['payload']]), entry['id']
        assert prompt in ' '.join(page.get_text().split()), 'Prompt missing from PDF text'
        links = {link.get('uri') for link in page.get_links()}
        assert manifest['page_url'] in links
        assert manifest['repository_url'] in links
        if entry['id'] != 'agent-prompt':
            assert entry['payload'] in links, 'PDF launch link differs from QR'
    page = document[-2]
    text = ' '.join(page.get_text().split())
    for slug in ('repeat-10', 'repeat-continuous'):
        assert ' '.join((kit / f'{slug}.txt').read_text().split()) in text, f'{slug} missing from PDF'
    pixmap = page.get_pixmap(dpi=150, alpha=False)
    raster = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
    assert [item.text for item in zxingcpp.read_barcodes(raster)] == [fallback['payload']]
    links = {link.get('uri') for link in page.get_links()}
    assert manifest['page_url'] + '#repeat' in links
    assert manifest['repository_url'] in links
    page = document[-1]
    text = ' '.join(page.get_text().split())
    assert ' '.join((kit / 'getting-tricky.txt').read_text().split()) in text
    examples = json.loads((kit / 'animal-preferences.json').read_text())
    for example in examples:
        assert ' '.join(example['prompt'].split()) in text, example['id']
    pixmap = page.get_pixmap(dpi=150, alpha=False)
    raster = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
    assert [item.text for item in zxingcpp.read_barcodes(raster)] == [fallback['payload']]
    assert page.get_images(), 'Beaver artwork missing from PDF'
    links = {link.get('uri') for link in page.get_links()}
    assert manifest['page_url'] + '#getting-tricky' in links
    assert manifest['repository_url'] in links
    print(f'Decoded {len(entries) + 1} PNGs and {2 * len(entries) + 2} PDF QR codes with exact payload matches.')
    print('PDF prompts and all addenda match the canonical text; guide/repository links are clickable.')


if __name__ == '__main__':
    main()
