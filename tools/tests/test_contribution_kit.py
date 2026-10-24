"""Check the printable and browser handoff agree, without network or QR libraries."""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / 'site' / 'contribute'
sys.path.insert(0, str(ROOT / 'tools'))


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.prompt = ''
        self.in_prompt = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'textarea' and attrs.get('id') == 'agent-prompt':
            self.in_prompt = True

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.in_prompt = False

    def handle_data(self, data):
        if self.in_prompt:
            self.prompt += data


def test_handoffs_preserve_the_whole_prompt_and_repository():
    manifest = json.loads((KIT / 'qr-manifest.json').read_text())
    prompt = (KIT / 'prompt.txt').read_text().strip()
    variants = {v['id']: v for v in manifest['variants']}
    assert variants['agent-prompt']['payload'] == prompt
    assert manifest['repository_url'] in prompt
    claude = urlsplit(variants['claude-code']['payload'])
    assert claude.scheme == 'https' and claude.netloc == 'claude.ai'
    assert claude.path == '/code/new'
    assert parse_qs(claude.query) == {'q': [prompt], 'repo': ['eeeearth/speeeecies'], 'branch': ['main']}
    codex = urlsplit(variants['codex']['payload'])
    assert codex.scheme == 'codex' and codex.netloc == 'threads' and codex.path == '/new'
    assert parse_qs(codex.query) == {'prompt': [prompt], 'originUrl': [manifest['repository_url'] + '.git']}


def test_page_has_prompt_and_launch_links_without_javascript():
    manifest = json.loads((KIT / 'qr-manifest.json').read_text())
    page = Page((ROOT / 'site' / 'contribute.html').read_text())
    assert page.prompt == (KIT / 'prompt.txt').read_text().strip()
    for variant in manifest['variants'][1:]:
        assert variant['payload'] in page.links
    assert 'contribute/speeeecies-contribution-qr.pdf' in page.links


def test_print_and_scan_assets_are_shipped_with_the_site(tmp_path):
    import build_site
    build_site.build_site(ROOT, tmp_path / 'site')
    kit = tmp_path / 'site' / 'contribute'
    assert (kit / 'speeeecies-contribution-qr.pdf').read_bytes().startswith(b'%PDF-')
    for slug in ('agent-prompt', 'claude-code', 'codex', 'contribute-page'):
        assert (kit / f'{slug}.png').read_bytes().startswith(b'\x89PNG')
        assert '<svg' in (kit / f'{slug}.svg').read_text()
