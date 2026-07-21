#!/usr/bin/env python3
"""Convert a photo to ASCII art for the portrait panel.

Usage: python3 img_to_ascii.py <input_image> <output.txt> [width]

Requires Pillow and numpy. Suppresses bright, non-skin-toned background
(sky, haze, foliage) so only the subject renders, then maps grayscale to
ASCII density characters.
"""
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

CHARS = "@%#*+=-:. "  # dark -> light


def isolate_subject(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("RGB")).astype("int16")
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    gray = np.array(img.convert("L")).astype("int16")

    bright = gray > 150
    skin_like = (r - g > 12) & (r - b > 10)
    background = bright & ~skin_like

    out = gray.copy()
    out[background] = 255
    return Image.fromarray(out.astype("uint8"))


def image_to_ascii(path: str, out_path: str, width: int = 60) -> list[str]:
    img = Image.open(path)
    img = isolate_subject(img)
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageOps.autocontrast(img, cutoff=1)

    w, h = img.size
    aspect = h / w
    new_h = max(1, int(aspect * width * 0.5))  # terminal chars are ~2x taller than wide
    img = img.resize((width, new_h))

    pixels = list(img.getdata())
    chars = [CHARS[min(len(CHARS) - 1, p * len(CHARS) // 256)] for p in pixels]

    lines = ["".join(chars[i * width:(i + 1) * width]) for i in range(new_h)]

    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    return lines


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 img_to_ascii.py <input_image> <output.txt> [width]")
        sys.exit(1)
    src, out = sys.argv[1], sys.argv[2]
    width_arg = int(sys.argv[3]) if len(sys.argv) > 3 else 78
    print("\n".join(image_to_ascii(src, out, width_arg)))
