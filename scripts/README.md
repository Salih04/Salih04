# Regenerating the hero

The profile hero is a pair of animated GIFs generated locally and committed. Nothing is
fetched at render time, and no third-party service is involved.

## Why GIF and not animated SVG

GitHub renders SVG embedded in a README as a **static image** — neither CSS `@keyframes`
nor SMIL `<animate>` executes. An earlier version of this profile used `svg-term-cli`
output, which animates via CSS keyframes; it worked at the raw asset URL and rendered
blank inside the README. Raster animation is decoded by the image pipeline instead, so
it plays normally.

Consequence for anyone editing this: **the hero must never depend on motion to become
legible.** Frame 0 is authored with full card chrome, titles and prompts already painted.

## Setup

```bash
make setup                                   # .venv + Pillow + numpy
cp /path/to/your/photo.jpg assets/source-private/photo.jpg
```

`assets/source-private/` is git-ignored, as is every `*.jpg` in the repo. The photograph
is never committed — only the derived character grid in `assets/data/portrait.txt`, which
is far too coarse to reconstruct the original.

Adjust the head-and-shoulders crop in `assets/source-private/crop.json` if you swap the
photo. Tighter is better: dead headroom shrinks the face in the final card.

## Build

```bash
make all        # portrait -> frames -> checks
```

| Target | Does |
| :--- | :--- |
| `make portrait` | photo → `assets/data/portrait.txt` (78 cols) and `portrait-stack.txt` (64 cols) |
| `make frames` | → `hero-wide.gif`, `hero-stack.gif`, `hero-static.png` |
| `make check` | size budgets, frame-0-not-blank, privacy, determinism |

## Editing the copy

All hero text lives in `scripts/terminal/content.py`. Line lengths are budget-checked at
build time — if a line is too long for its card, the render **fails loudly** rather than
silently clipping. Shorten the copy; don't widen the canvas.

## How it is served

```html
<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/generated/hero-static.png">
  <source media="(max-width: 600px)"              srcset="assets/generated/hero-stack.gif">
  <img src="assets/generated/hero-wide.gif" width="100%" alt="…">
</picture>
```

GitHub's HTML sanitizer preserves `<source media>` (verified against the `/markdown` API),
so the mobile and reduced-motion variants are both honoured.

## Notes

- Rendered at 2× and Lanczos-downsampled, so the browser only ever downscales — this is
  what keeps small monospace text sharp.
- Quantised against a **fixed** palette. Per-frame adaptive palettes cause colour drift and
  destroy GIF delta compression.
- The GIF omits the Netscape loop block, so it plays once and rests on the final frame.
  Pass `--loop` to `render.py` for an infinitely looping build instead.
- Font is Menlo (macOS system). On another OS, point `FONT_PATH` in `render.py` at any
  monospace TTF and re-measure `ADVANCE_RATIO` (advance width ÷ point size).
