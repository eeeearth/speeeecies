#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["qrcode[pil]==8.2", "reportlab==4.4.5"]
# ///
"""Build the contribution page, QR images and four-page PDF from shared text.

Run: uv run tools/build_contribution_kit.py [--check]
The ordinary site build copies the committed outputs without extra dependencies.
"""
from __future__ import annotations

import argparse
from html import escape
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import quote, urlencode

REPO_URL = "https://github.com/eeeearth/speeeecies"
PAGE_URL = "https://eeeearth.github.io/speeeecies/contribute.html"


def variants(prompt: str) -> list[dict]:
    return [
        {
            "id": "agent-prompt", "title": "Any coding agent", "payload": prompt,
            "intro": "Scan to get the full prompt as text, including the repository URL.",
            "steps": ["Use a QR reader that can copy text.", "Paste the prompt into your coding agent.", "Open the repository or your fork and send it when ready."],
            "note": "The smaller QR below opens a browser page with a copy button and all versions.",
            "button": "Open the prompt page", "href": PAGE_URL + "#prompt",
        },
        {
            "id": "claude-code", "title": "Claude Code",
            "payload": "https://claude.ai/code/new?" + urlencode({"q": prompt, "repo": "eeeearth/speeeecies", "branch": "main"}, quote_via=quote),
            "intro": "Scan to open Claude Code with the contribution prompt filled in.",
            "steps": ["Sign in with Claude Code access.", "Connect the repository or select your fork if needed.", "Review the prompt and send it."],
            "note": "Uses the documented mobile/browser link. Repository selection depends on your GitHub connection.",
            "button": "Open Claude Code",
        },
        {
            "id": "codex", "title": "Codex app",
            "payload": "codex://threads/new?" + urlencode({"prompt": prompt, "originUrl": REPO_URL + ".git"}, quote_via=quote),
            "intro": "Scan with a compatible reader to prefill the installed desktop app.",
            "steps": ["Open your repository checkout or fork as a workspace.", "Open the app link, then review and send the prompt."],
            "note": "On a phone, or if the app link does not open, scan the smaller browser QR below and copy the prompt into your usual Codex interface.",
            "button": "Open Codex app",
        },
    ]


def draw_qr(canvas, qr, x, y, size):
    """Draw vector modules, including the four-module white quiet zone."""
    matrix = qr.get_matrix()
    cell = size / len(matrix)
    canvas.setFillColorRGB(1, 1, 1)
    canvas.rect(x, y, size, size, stroke=0, fill=1)
    canvas.setFillColorRGB(0, 0, 0)
    path = canvas.beginPath()
    for row, values in enumerate(matrix):
        for col, dark in enumerate(values):
            if dark:
                path.rect(x + col * cell, y + (len(matrix) - row - 1) * cell, cell, cell)
    canvas.drawPath(path, stroke=0, fill=1)


def make_pdf(prompt, entries, qrs, addenda):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import Paragraph

    buf = BytesIO()
    canvas = Canvas(buf, pagesize=(612, 792), invariant=1, pageCompression=1)
    canvas.setTitle("speeeecies: contribution prompts and QR codes")
    canvas.setAuthor("speeeecies contributors")
    canvas.setSubject("Any coding agent, Claude Code and Codex app")
    green, ink, muted = HexColor('#2f6f4e'), HexColor('#1c1b18'), HexColor('#4b4a45')

    def paragraph(text, x, top, width, size=11, leading=15, color=ink):
        style = ParagraphStyle('kit', fontName='Helvetica', fontSize=size, leading=leading, textColor=color)
        item = Paragraph(escape(text), style)
        _, height = item.wrap(width, 700)
        item.drawOn(canvas, x, top - height)
        return top - height

    for number, entry in enumerate(entries, 1):
        canvas.setFillColor(green)
        canvas.rect(0, 778, 612, 14, stroke=0, fill=1)
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(44, 744, 'SPEEEECIES  /  CONTRIBUTOR KIT')
        canvas.setFillColor(ink)
        canvas.setFont('Helvetica-Bold', 30)
        canvas.drawString(44, 706, 'Contribute an animal species.')
        canvas.setFont('Helvetica-Bold', 20)
        canvas.drawString(44, 672, entry['title'])
        paragraph(entry['intro'], 44, 649, 524, 12, 16)

        draw_qr(canvas, qrs[entry['id']], 44, 354, 252)
        canvas.linkURL(entry.get('href', entry['payload']), (44, 354, 296, 606), relative=0)
        canvas.setFillColor(green)
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(320, 594, 'AFTER SCANNING')
        top = 576
        for index, step in enumerate(entry['steps'], 1):
            top = paragraph(f'{index}. {step}', 320, top, 244, 11, 15) - 12
        top = paragraph(entry['note'], 320, top - 2, 244, 10, 14, muted)
        canvas.setFillColor(green)
        canvas.setFont('Helvetica-Bold', 11)
        button_y = min(372, top - 22)
        canvas.drawString(320, button_y, entry['button'])
        canvas.linkURL(entry.get('href', entry['payload']), (320, button_y - 4, 565, button_y + 14), relative=0)

        canvas.setFillColor(HexColor('#f0efe9'))
        canvas.roundRect(44, 168, 524, 164, 8, stroke=0, fill=1)
        canvas.setFillColor(green)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawString(60, 311, 'THE PROMPT  /  SAME IN EVERY VERSION')
        bottom = paragraph(prompt, 60, 297, 492, 10.3, 14.2)
        if bottom < 181:
            raise ValueError('Prompt exceeds the printable text panel; shorten or reflow it.')

        draw_qr(canvas, qrs['contribute-page'], 44, 57, 78)
        canvas.linkURL(PAGE_URL, (44, 57, 122, 135), relative=0)
        canvas.setFillColor(ink)
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(138, 124, 'Browser guide and copy button')
        paragraph(PAGE_URL, 138, 111, 428, 9, 12, green)
        canvas.linkURL(PAGE_URL, (138, 96, 568, 112), relative=0)
        paragraph(REPO_URL, 138, 88, 428, 9, 12, green)
        canvas.linkURL(REPO_URL, (138, 73, 568, 89), relative=0)
        paragraph('Maintainers review contributions before live publication.', 138, 65, 428, 9, 12, muted)
        canvas.setFillColor(muted)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(44, 28, 'US Letter. Print at actual size, or Fit on A4. Keep the white QR borders.')
        canvas.drawRightString(568, 28, f'{number} / {len(entries) + 1}')
        canvas.showPage()
    canvas.setFillColor(green)
    canvas.rect(0, 778, 612, 14, stroke=0, fill=1)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(44, 744, 'SPEEEECIES  /  REPEAT-WORK ADDENDUM')
    canvas.setFillColor(ink)
    canvas.setFont('Helvetica-Bold', 28)
    canvas.drawString(44, 706, 'Do 10, or keep going.')
    paragraph('Paste one block after the original prompt, or send it in the same conversation. Each species still needs its own evidence and PR.', 44, 683, 524, 11, 15)
    top = 633
    for title, text in addenda:
        canvas.setFillColor(green)
        canvas.setFont('Helvetica-Bold', 15)
        canvas.drawString(44, top, title)
        top = paragraph(text, 44, top - 14, 524, 10.3, 13.5) - 25
    if top < 154:
        raise ValueError('Repeat-work addendum exceeds its PDF page; shorten or reflow it.')
    draw_qr(canvas, qrs['contribute-page'], 44, 57, 78)
    canvas.linkURL(PAGE_URL, (44, 57, 122, 135), relative=0)
    paragraph('Copy the addenda and resume instructions in the browser guide:', 138, 137, 428, 9, 12, muted)
    paragraph(PAGE_URL + '#repeat', 138, 111, 428, 9, 12, green)
    canvas.linkURL(PAGE_URL + '#repeat', (138, 96, 568, 112), relative=0)
    paragraph(REPO_URL, 138, 88, 428, 9, 12, green)
    canvas.linkURL(REPO_URL, (138, 73, 568, 89), relative=0)
    paragraph('Runs within an active agent session. Resume from the saved checkpoint; this does not install a scheduler or restart the session.', 138, 65, 428, 9, 12, muted)
    canvas.setFillColor(muted)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(44, 28, 'US Letter. Print at actual size, or Fit on A4. Keep the white QR borders.')
    canvas.drawRightString(568, 28, f'{len(entries) + 1} / {len(entries) + 1}')
    canvas.showPage()
    canvas.save()
    return buf.getvalue()


def generate(root: Path) -> dict[str, bytes]:
    import qrcode
    from qrcode.image.svg import SvgPathFillImage

    prompt = (root / 'site/contribute/prompt.txt').read_text(encoding='utf-8').strip()
    if not prompt or REPO_URL not in prompt:
        raise ValueError('The contribution prompt must contain the public repository URL.')
    addenda = [(title, (root / f'site/contribute/{slug}.txt').read_text(encoding='utf-8').strip())
               for title, slug in [('Do 10 species', 'repeat-10'), ('Continue until stopped', 'repeat-continuous')]]
    entries = variants(prompt)
    qrs = {}
    outputs = {}
    for entry in entries + [{'id': 'contribute-page', 'payload': PAGE_URL}]:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(entry['payload'])
        qr.make(fit=True)
        qrs[entry['id']] = qr
        for suffix, image in [('png', qr.make_image()), ('svg', qr.make_image(image_factory=SvgPathFillImage))]:
            buf = BytesIO()
            image.save(buf)
            outputs[f"site/contribute/{entry['id']}.{suffix}"] = buf.getvalue()

    manifest = {
        'repository_url': REPO_URL, 'page_url': PAGE_URL,
        'error_correction': 'M', 'quiet_zone_modules': 4,
        'variants': [{'id': e['id'], 'title': e['title'], 'payload': e['payload'], 'qr_version': qrs[e['id']].version} for e in entries],
        'fallback': {'id': 'contribute-page', 'payload': PAGE_URL},
    }
    outputs['site/contribute/qr-manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    outputs['site/contribute/speeeecies-contribution-qr.pdf'] = make_pdf(prompt, entries, qrs, addenda)
    template = (root / 'tools/templates/contribute.html').read_text(encoding='utf-8')
    for key, value in {'PAGE_URL': PAGE_URL, 'REPO_URL': REPO_URL, 'PROMPT': prompt, 'REPEAT_10': addenda[0][1], 'REPEAT_CONTINUOUS': addenda[1][1], 'CLAUDE_URL': entries[1]['payload'], 'CODEX_URL': entries[2]['payload']}.items():
        template = template.replace(f'@@{key}@@', escape(value, quote=True))
    if '@@' in template:
        raise ValueError('Unresolved contribution-page template token')
    outputs['site/contribute.html'] = template.encode()
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the committed generated assets differ')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    outputs = generate(root)
    stale = []
    for name, data in outputs.items():
        path = root / name
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if stale:
        raise SystemExit('Regenerate the contribution kit: ' + ', '.join(stale))
    print(('Checked' if args.check else 'Generated') + f' {len(outputs)} contribution-kit assets.')


if __name__ == '__main__':
    main()
