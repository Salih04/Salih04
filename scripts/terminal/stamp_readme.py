#!/usr/bin/env python3
"""Stamp a content hash onto each hero asset URL in README.md.

GitHub proxies README images through camo, which caches by source URL. Without
this, regenerating an asset leaves the profile serving the previous version
indefinitely — the filename never changed, so neither did the cache key.

Appending ?v=<sha256[:8]> gives a new cache key exactly when the bytes change,
while keeping filenames stable. Query strings survive GitHub's sanitizer
(verified against the /markdown API).

    python3 scripts/terminal/stamp_readme.py
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

README = Path("README.md")
ASSET_DIR = "assets/generated"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def main() -> None:
    if not README.exists():
        sys.exit("README.md not found")

    text = README.read_text()
    original = text
    changed: list[str] = []

    # Matches assets/generated/<file>.<ext> with an optional existing ?v=...
    pattern = re.compile(rf"({re.escape(ASSET_DIR)}/[A-Za-z0-9._-]+\.(?:gif|png))(\?v=[0-9a-f]+)?")

    def repl(m: re.Match) -> str:
        rel = m.group(1)
        p = Path(rel)
        if not p.exists():
            print(f"  warn  {rel} referenced but not on disk")
            return m.group(0)
        h = digest(p)
        old = (m.group(2) or "")[3:]
        if old != h:
            changed.append(f"{rel}  {old or '(none)'} -> {h}")
        return f"{rel}?v={h}"

    text = pattern.sub(repl, text)

    if text != original:
        README.write_text(text)
        for line in changed:
            print(f"  stamped {line}")
    else:
        print("  hashes already current")


if __name__ == "__main__":
    main()
