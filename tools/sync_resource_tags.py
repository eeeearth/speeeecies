"""Generate the public resource-tag snapshot from seeeeds ResourceTag::KNOWN.

Usage: python3 tools/sync_resource_tags.py /path/to/seeeeds/crates/seeeeds-schema/src/ids.rs <git-revision> [--check]
Use a clean seeeeds checkout and pass its full commit SHA. This script has no
runtime dependency on seeeeds; the generated JSON is used by validate.py.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEST = Path(__file__).resolve().parents[1] / "schema" / "v0.1" / "resource-tags.json"
SOURCE_URL = "https://github.com/jt55401/seeeeds/blob/{revision}/crates/seeeeds-schema/src/ids.rs"


def extract_known(source: str) -> list[str]:
    match = re.search(r"pub const KNOWN:.*?=\s*&\[(.*?)\];", source, re.S)
    if not match:
        raise ValueError("seeeeds ResourceTag::KNOWN not found")
    body = match.group(1)
    tags = re.findall(r'"([a-z0-9_:-]+)"', body)
    if not tags or len(tags) != len(set(tags)) or re.sub(r'"[a-z0-9_:-]+"\s*,?\s*', '', body).strip():
        raise ValueError("seeeeds ResourceTag::KNOWN contains unexpected entries")
    return tags


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids_rs", type=Path)
    parser.add_argument("revision", help="full seeeeds commit SHA")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("revision must be a full Git commit SHA")
    snapshot = {
        "source": SOURCE_URL.format(revision=args.revision),
        "known": extract_known(args.ids_rs.read_text(encoding="utf-8")),
    }
    output = json.dumps(snapshot, indent=2) + "\n"
    if args.check:
        if DEST.read_text(encoding="utf-8") != output:
            raise SystemExit(f"{DEST} differs from seeeeds ResourceTag::KNOWN")
    else:
        DEST.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
