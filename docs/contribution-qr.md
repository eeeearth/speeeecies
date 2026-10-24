# Contribution QR kit

The public guide is [contribute.html](https://eeeearth.github.io/speeeecies/contribute.html).
It offers a plain-text prompt QR, a prefilled Claude Code link and a prefilled
Codex desktop app link. A smaller HTTPS guide QR provides a browser fallback.
The PDF has one US Letter page per version, with vector QR modules, the complete
prompt and clickable links. It also prints on A4 with Fit selected.

## Update the kit

1. Edit `site/contribute/prompt.txt` for the shared prompt. Keep its public
   repository URL and the direction to follow current `AGENTS.md` and
   `docs/data-quality.md`.
2. Edit `tools/templates/contribute.html` for page copy. Styles and the optional
   clipboard button live in `site/css/contribute.css` and `site/js/contribute.js`.
3. Run `uv run tools/build_contribution_kit.py`. Commit its generated page,
   PDF, PNG/SVG images and `qr-manifest.json` together.
4. Run `uv run tools/build_contribution_kit.py --check` and
   `uv run tools/verify_contribution_kit.py`. The latter independently decodes
   all PNGs and every PDF QR after rendering at 150 dpi, compares exact payloads,
   and checks PDF text and links.
5. Render and visually inspect every PDF page; check the site on mobile and
   desktop, including clipboard failure and JavaScript-disabled behaviour.

The regular site build copies these committed files. It needs no QR, PDF or
browser dependencies. Generation dependencies are pinned in the generator's
PEP 723 header. The standard test suite checks prompt/link agreement and that
the site build ships the assets. The decoding check is a separate developer
command with its own dependencies.

## Link behaviour

Formats checked 24 October 2026:

- [Claude's documented universal links](https://support.claude.com/en/articles/14898120-open-the-claude-mobile-app-with-a-link)
  support `https://claude.ai/code/new` with `q`, `repo` and `branch`. GitHub
  repository selection depends on the contributor's connected account.
- [Codex's documented app links](https://learn.chatgpt.com/docs/reference/commands#deep-links)
  support `codex://threads/new` with `prompt` and `originUrl`. The repository
  hint matches a workspace already known to the app. It does not clone a repo.

Both links prefill a composer for the contributor to review and send. They
require the corresponding product access. A scanner or phone may not handle
the Codex desktop URL scheme; the guide QR and plain text remain available.
Do not add guessed web parameters or claim that scanning automatically starts
an authenticated coding task.
