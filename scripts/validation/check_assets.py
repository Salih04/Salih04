#!/usr/bin/env python3
"""Gate the committed hero assets: size budget, animation sanity, privacy, determinism.

    python3 scripts/validation/check_assets.py

Exits non-zero on any failure so it can run in CI or a pre-commit hook.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

BUDGET_KB = {
    "assets/generated/hero-wide.gif": 1800,
    "assets/generated/hero-stack.gif": 1200,
    "assets/generated/hero-static.png": 150,
}

# Anything matching these must never be tracked by git.
FORBIDDEN_SUFFIXES = (".jpg", ".jpeg", ".heic")

failures: list[str] = []


def ok(msg: str) -> None:
    print(f"  ok    {msg}")


def bad(msg: str) -> None:
    failures.append(msg)
    print(f"  FAIL  {msg}")


print("size budget")
for path, limit in BUDGET_KB.items():
    p = Path(path)
    if not p.exists():
        bad(f"{path} missing — run `make frames`")
        continue
    kb = p.stat().st_size / 1024
    (ok if kb <= limit else bad)(f"{path}  {kb:.0f} KB (limit {limit} KB)")

print("animation sanity")
for path in ("assets/generated/hero-wide.gif", "assets/generated/hero-stack.gif"):
    p = Path(path)
    if not p.exists():
        continue
    with Image.open(p) as im:
        n = getattr(im, "n_frames", 1)
        if n < 2:
            bad(f"{path} has {n} frame(s) — not animated")
            continue
        # Frame 0 must already carry content: a blank opening is the exact
        # failure mode that sank the previous SVG implementation.
        im.seek(0)
        colours = len(im.convert("RGB").getcolors(maxcolors=100000) or [])
        (ok if colours >= 4 else bad)(f"{path}  {n} frames, frame0 has {colours} colours")

print("privacy")
tracked = subprocess.run(
    ["git", "ls-files"], capture_output=True, text=True, check=False
).stdout.split()
leaked = [f for f in tracked if f.lower().endswith(FORBIDDEN_SUFFIXES)]
(bad if leaked else ok)(
    f"source imagery tracked: {leaked}" if leaked else "no source imagery tracked by git"
)

hist = subprocess.run(
    ["git", "log", "--all", "--pretty=format:", "--name-only", "--diff-filter=A"],
    capture_output=True, text=True, check=False,
).stdout.split()
hist_leak = sorted({f for f in hist if f.lower().endswith(FORBIDDEN_SUFFIXES)})
(bad if hist_leak else ok)(
    f"source imagery in history: {hist_leak}" if hist_leak else "no source imagery in git history"
)

print("determinism")
sums = []
for _ in range(2):
    subprocess.run(
        [".venv/bin/python3", "scripts/terminal/render.py", "--build", "wide",
         "--out", "assets/preview/_det.gif"],
        capture_output=True, check=False,
    )
    sums.append(Path("assets/preview/_det.gif").read_bytes())
Path("assets/preview/_det.gif").unlink(missing_ok=True)
(ok if sums[0] == sums[1] else bad)("two consecutive renders are byte-identical")

print()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("all checks passed")
