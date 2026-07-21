#!/usr/bin/env python3
"""Convert a private source photo into a committable ASCII portrait.

    python3 scripts/portrait/build_portrait.py --cols 78 --out assets/data/portrait.txt

The source photograph never leaves assets/source-private/. Only the character
grid produced here is committed: at these dimensions it is a ~10-level
quantisation of a few thousand cells, far too coarse to reconstruct the
original image.

Background suppression uses a brightness gate combined with a skin-tone
exclusion. Both thresholds were calibrated against measured samples from the
source photo:

    sky      (158, 205, 247)      hillside (195, 203, 204)
    shirt    ( 25,  39,  74)      face     (208, 177, 178)

The brightness gate alone would erase the bright hazy hillside but also parts
of the face; the skin-tone term protects the face. The gate protects the dark
shirt, which a pure colour-cast rule would eat.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover - dependency guard
    sys.exit(f"missing dependency: {exc}. Run: make setup")

# Dark -> light. Ten levels; deliberately no dithering (see --dither).
RAMP = "@%#*+=-:. "

BRIGHTNESS_GATE = 150
SKIN_R_MINUS_G = 12
SKIN_R_MINUS_B = 10


def isolate_subject(img: Image.Image) -> Image.Image:
    """Force bright, non-skin-toned pixels to white so only the subject renders."""
    arr = np.array(img.convert("RGB")).astype("int16")
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    gray = np.array(img.convert("L")).astype("int16")

    bright = gray > BRIGHTNESS_GATE
    skin_like = (r - g > SKIN_R_MINUS_G) & (r - b > SKIN_R_MINUS_B)
    background = bright & ~skin_like

    out = gray.copy()
    out[background] = 255
    return Image.fromarray(out.astype("uint8"))


def build(
    src: Path,
    out: Path,
    cols: int,
    cell_ratio: float,
    crop: tuple[int, int, int, int] | None,
    dither: bool,
) -> tuple[int, int]:
    img = Image.open(src)
    if crop:
        img = img.crop(crop)

    src_w, src_h = img.size

    img = isolate_subject(img)
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageOps.autocontrast(img, cutoff=1)

    # Preserve the true image aspect given non-square character cells:
    #   (cols * cell_w) / (rows * cell_h) == src_w / src_h
    #   => rows = cols * cell_ratio * (src_h / src_w)
    rows = max(1, round(cols * cell_ratio * (src_h / src_w)))

    img = img.resize((cols, rows), Image.LANCZOS)
    if dither:
        img = img.convert("P", palette=Image.ADAPTIVE, colors=len(RAMP)).convert("L")

    pixels = list(img.getdata())
    chars = [RAMP[min(len(RAMP) - 1, p * len(RAMP) // 256)] for p in pixels]
    lines = ["".join(chars[i * cols:(i + 1) * cols]) for i in range(rows)]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    return cols, rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=Path("assets/source-private/photo.jpg"))
    ap.add_argument("--out", type=Path, default=Path("assets/data/portrait.txt"))
    ap.add_argument("--cols", type=int, default=78)
    ap.add_argument(
        "--cell-ratio",
        type=float,
        default=0.456,
        help="character advance / line height for the render font (Menlo default)",
    )
    ap.add_argument("--dither", action="store_true", help="off by default: adds speckle at this size")
    args = ap.parse_args()

    if not args.src.exists():
        sys.exit(
            f"source photo not found: {args.src}\n"
            "Place your photo at assets/source-private/photo.jpg (git-ignored)."
        )

    crop = None
    crop_file = args.src.parent / "crop.json"
    if crop_file.exists():
        crop = tuple(json.loads(crop_file.read_text())["crop"])

    cols, rows = build(args.src, args.out, args.cols, args.cell_ratio, crop, args.dither)
    print(f"portrait: {cols} cols x {rows} rows -> {args.out}")


if __name__ == "__main__":
    main()
