# GitHub Profile Animation Plan — `Salih04/Salih04`

**Status:** planning only. No production asset was edited, no file removed, nothing committed or pushed.
**Prepared against:** commit `f3d9ed5` on `main`, working tree clean.
**Date of inspection:** 2026-07-21.

---

## 1. Executive verdict

Rebuild the hero around a **single composite animated GIF** containing both terminal panels,
generated deterministically by a local Python frame renderer, committed to the repository, and
paired with a **static first-frame fallback**.

Do **not** rebuild it with animated SVG.

This is not a stylistic preference. During this inspection I confirmed, on real GitHub pages,
that SVG animation does not execute when the SVG is embedded as an image in a README:

- The previous `outputs/portrait.svg` and `outputs/whoami.svg` are driven by CSS `@keyframes`
  (`grep -c "@keyframes"` → 1 each; `grep -c "<animate"` → 0 each). They animate at their raw URL
  and rendered blank inside the README — which is exactly the symptom you reported.
- `capsule-render` emits its banner text as `opacity: 0` plus `animation: fadeIn … forwards`.
  On your profile the gradient rendered and **the text never appeared**, even after many seconds.
  With `forwards` fill-mode, a running animation would have left the text visible permanently.
  It did not run.
- I then tested the strongest counter-example: `DenverCoder1/readme-typing-svg`, which uses **SMIL**
  (`<animate>`), embedded in its own README on github.com. The image loads correctly
  (`complete: true`, `naturalWidth: 380`, `naturalHeight: 50`) and renders **visually empty**,
  identical across two screenshots two seconds apart.

So both SVG animation mechanisms — CSS keyframes and SMIL — failed in the embedded README context
I could observe. Meanwhile the one asset that works flawlessly on your live profile today is
`assets/svg/hero.svg`, which contains **zero** animation (`grep -c "@keyframes\|<animate\|<style"` → 0).

The pattern is unambiguous: **GitHub README renders SVG as a static image.** Raster animation
(GIF) is decoded by the image pipeline rather than the SVG animation engine, and is the format
that thousands of profiles animate with successfully.

One honest caveat, carried into Phase 1 as a gate rather than an assumption: the SMIL observation
was made in the in-app browser pane, which may suppress declarative animation for embedded images.
Your own Brave screenshot independently showed the CSS-animated portrait panel blank, which
corroborates the CSS finding in your real browser. Phase 1 exists to settle SMIL definitively in
*your* browser before we discard it permanently.

**Additional finding worth recording:** your profile README is now **live**. `curl` of
`https://github.com/Salih04` returns `hero.svg` plus the `Tech Stack` and `Featured Projects`
headings, and 47 camo-proxied images. The "Share to Profile" activation you performed worked.

---

## 2. Current repository assessment

### Tracked files (complete list — 3 files)

| Path | Size | Notes |
| :--- | ---: | :--- |
| `.gitignore` | 57 B | `.venv/`, `assets/*`, `!assets/svg/`, `.DS_Store`, `outputs/`, `scripts/` |
| `README.md` | 4 814 B | Current static "modern" layout |
| `assets/svg/hero.svg` | 3 261 B | Static hero. **Renders correctly on the live profile.** |

Working tree is clean. Branch `main` tracks `origin/main`. Four commits.

### Git history

| Commit | Meaning |
| :--- | :--- |
| `0fd89d0` | Original dual-terminal ASCII attempt (added `outputs/`, `scripts/`) |
| `7ddd4a1` | Pivot to conventional layout; **removed** `outputs/` + `scripts/` from tracking |
| `acfe2ef` | Introduced self-hosted `hero.svg`; dropped third-party widget services |
| `f3d9ed5` | Removed camo-unreliable streak widget; reflowed projects |

The terminal implementation still exists in history at `0fd89d0` and is recoverable — nothing was
lost, only untracked.

### Local-only artifacts (present on disk, correctly excluded from git)

| Path | Size | Disposition |
| :--- | ---: | :--- |
| `assets/img.jpg` | 88 470 B | **Original photograph.** Must never be committed. |
| `assets/img_cropped_preview.jpg` | 32 522 B | Working crop (head+shoulders) — the crop that produced the good result |
| `assets/img_cropped_v2.jpg` | 29 736 B | Alternative tighter crop |
| `assets/portrait_masked3.png` | 83 738 B | **Recognizable grayscale photo.** Must never be committed. |
| `assets/portrait_masked.png` / `masked2.png` | 65 769 / 98 072 B | Rejected masking iterations |
| `assets/portrait_processed.png` | 131 447 B | Contour-filter experiment (rejected — lines vanish at low res) |
| `assets/portrait_tonal.png` | 120 979 B | Tonal experiment (rejected — noisy background) |
| `outputs/portrait.svg` | 32 858 B | CSS-keyframe animation, **860 × 971.82 px** |
| `outputs/whoami.svg` | 8 746 B | CSS-keyframe animation |
| `outputs/portrait_ascii.txt` | 2 922 B | 36 rows × 78 cols — **the good ASCII portrait** |
| `outputs/portrait.cast` / `whoami.cast` | 4 091 / 1 232 B | asciinema v2 recordings |
| `scripts/img_to_ascii.py` | 1 923 B | Working converter incl. background suppression |
| `scripts/portrait.sh` / `whoami.sh` | 559 / 1 288 B | Terminal reveal scripts |

### Privacy state — verified clean

```
git log --all --pretty=format: --name-only --diff-filter=A | grep -iE '\.(jpg|jpeg|png|webp|heic)$'
→ NONE — no raster image ever added in any commit
```

The photograph has **never** entered git history in any commit on any ref. The current
`.gitignore` (`assets/*` with `!assets/svg/`) is what protects it. Any new directory under
`assets/` will be ignored by default — which is the safe default, but means generated assets we
*do* want committed need explicit negation rules (Section 14).

### Obsolete / redundant

- Five of the seven `assets/*.png` intermediates are dead ends from the masking search.
- `outputs/*.svg` are the artifacts of the failed architecture; keep as reference until Phase 4 is
  proven, then archive.
- `README.md` currently carries a 22-badge wall across four categories — this competes with, rather
  than supports, a hero.

### Live profile facts (not assumed — fetched)

- `https://raw.githubusercontent.com/Salih04/Salih04/main/assets/svg/hero.svg` → `200`,
  `image/svg+xml`, `3261 b`.
- Profile page serves the README, references `hero.svg`, and proxies 47 images through camo.

---

## 3. Problems in the previous implementations

| # | Problem | Confirmed root cause |
| :-- | :--- | :--- |
| P1 | Portrait panel blank in README, fine at raw URL | `svg-term-cli` output animates via CSS `@keyframes` + `translateX` on a wide film-strip. GitHub renders embedded SVG statically → the strip never moves → frame 0 shows. |
| P2 | Frame 0 was effectively empty | `portrait.sh` began with `clear`, so frame 0 held only a prompt on an 82×42 grid. Scaled into a half-width cell, that is visually blank. |
| P3 | Animation restarted every ~3.3 s | `animation-duration: 3.295069s; animation-iteration-count: infinite; steps(1,end)`. Even where it ran, it would have been a distracting loop with no resting state. |
| P4 | Aspect ratio fought the layout | `portrait.svg` is 860 × 971.82 — taller than wide. The reference composition is landscape. A tall panel next to a short one cannot balance. |
| P5 | Third-party services unreliable | Measured: `github-readme-stats` → **503** (3/3 attempts); `github-profile-trophy` → **402**; `streak-stats` direct → 200 but **camo → 504**; `capsule-render` → 200 but animated text invisible. Only `shields.io` proved dependable. |
| P6 | The static redesign lost the concept | Technically sound, but it is a template. It does not read as built for you. |
| P7 | Validation was insufficient | Correctness was judged from the raw SVG URL. That is precisely the test that cannot detect P1. |

**Design rule derived from P1–P3:** the asset must be *correct in its first painted frame*, and any
motion must be an enhancement on top of an already-complete-looking image — never the mechanism by
which content becomes visible.

---

## 4. Reference-image design analysis

What the references get right, and what we should take:

| Element | Observation | Adopt? |
| :--- | :--- | :--- |
| Dual-panel composition | Two terminal cards, unequal widths, reading left→right: image then identity | **Yes** — this is the core idea |
| Terminal chrome | Rounded corners, three control dots, thin border, title bar | **Yes**, restrained |
| Palette | Deep navy field, off-white text, single cyan accent | **Yes** — matches existing `hero.svg` tokens |
| ASCII portrait | Large, centred, recognizable, monochrome | **Yes** |
| Progressive reveal | Content builds rather than appearing at once | **Yes**, but must not start blank |
| Density | Right panel is skimmable, not a CV dump | **Yes** — hard constraint |
| Glow / neon | Present in some references | **No** — reduce to a single soft accent |
| Decorative noise | Scanlines, matrix rain, clutter | **No** |

The strongest property of the references is **compositional**, not effectual: two aligned cards of
equal height with a small gutter. We reproduce the composition and discard the visual noise.

---

## 5. Proposed final visual system

Inherit the tokens already proven on the live profile in `hero.svg` — this keeps the new hero
consistent with what is already there.

| Token | Value | Contrast on `#0B1016` |
| :--- | :--- | ---: |
| Background (outer) | `#0B1016` | — |
| Card surface | `#111C28` | — |
| Card border | `#1F2D3D` | — |
| Title-bar surface | `#16222F` | — |
| Primary text | `#E6EDF3` | ~15.4:1 |
| Accent (cyan) | `#66C2CD` | ~9.1:1 |
| Muted text | `#8B98A5` | ~7.4:1 |
| Prompt green | `#7EE787` | ~11.6:1 |
| Control dots | `#FF5F57` `#FEBC2E` `#28C840` | decorative |

All text tokens clear WCAG AA (4.5:1) and the two primary ones clear AAA (7:1).

**Typography:** Menlo (confirmed present at `/System/Library/Fonts/Menlo.ttc`). SF Mono and Monaco
are also available. JetBrains Mono is **not** installed — if we want it, it must be vendored into
`assets/fonts/` and the licence noted, otherwise output is not reproducible on another machine.
Since we render to raster, the font is baked in; no font loading occurs on GitHub.

Because the asset paints its own background, it is theme-independent and looks identical in GitHub
light and dark modes — the same property that makes today's `hero.svg` work.

---

## 6. Desktop layout specification

Single composite canvas — **one image, not two** — so the two panels are frame-locked and can never
desynchronise.

```
canvas 1280 × 520   (2× render → 2560 × 1040, downsampled to 1280 × 520)

┌──────────────────────────┐  ┌────────────────────────────────────────┐
│ ● ● ●  portrait          │  │ ● ● ●  salih@basel — zsh               │
├──────────────────────────┤  ├────────────────────────────────────────┤
│                          │  │                                        │
│      ASCII portrait      │  │  $ whoami                              │
│      78 cols × 36 rows   │  │                                        │
│                          │  │  Salih Camcı                           │
│                          │  │  > Software Engineer                   │
│                          │  │  > Incoming MSc Data Science, Basel    │
│                          │  │  > Former Backend Eng Intern, Crytek   │
│                          │  │                                        │
│                          │  │  ~/focus     …                         │
│                          │  │  ~/building  …                         │
│                          │  │  ~/stack     [ ] [ ] [ ]               │
│                          │  │  ~/links     …                         │
└──────────────────────────┘  └────────────────────────────────────────┘
   x:0   w:504  (39.4%)          x:536  w:744  (58.1%)     gutter 32
```

- Left panel **39.4 %**, right panel **58.1 %**, gutter **32 px** — inside your 38–42 / 58–62 brief.
- Equal height (520 px), equal baseline, corner radius 10 px, 1 px border `#1F2D3D`.
- Title bar 30 px with three 10 px dots at 14 px pitch.
- Portrait cell: 78 cols × 36 rows at 5.6 px advance → 437 px wide, fits 504 − 2×24 padding.
- Right cell: monospace 15 px, line-height 24 px, 22 lines of headroom for ~15 used lines.

Rendered into GitHub's ~880 px README column, 1280 px downsamples to ~0.69× — 15 px type lands at
~10.4 px effective. To keep terminal text genuinely crisp the render is done at 2× and the final
GIF is emitted at **1280 × 520** so the browser only ever downscales, never upscales.

---

## 7. Mobile layout specification

GitHub's profile README column on a 375 px viewport is ~343 px. A 1280 px-wide composite scales to
0.27× — 15 px type becomes 4 px. **Unreadable. The wide asset alone cannot satisfy mobile.**

Therefore a second, separately-composed build:

```
canvas 720 × 940   →   stacked

┌────────────────────────────────┐
│ ● ● ●  portrait                │   portrait card, 720 × 430
│        ASCII portrait          │
└────────────────────────────────┘
              gap 24
┌────────────────────────────────┐
│ ● ● ●  salih@basel — zsh       │   identity card, 720 × 486
│  $ whoami …                    │
└────────────────────────────────┘
```

At 343 px this is 0.48× — 17 px type → ~8 px. Still tight, so the mobile build uses **19 px type
and a reduced line set** (drops `~/building`, shortens `~/stack`), trading completeness for
legibility. The dropped content is present in the markdown below the hero, so nothing is lost.

Delivery, in order of preference:

1. `<picture>` with `<source media="(max-width: 600px)" srcset="…stack.gif">` — **Phase 1 must
   verify GitHub preserves `media` on `<source>`.** GitHub documents `<picture>` support for
   `prefers-color-scheme`; width queries are plain HTML the browser resolves, but this is
   unverified and therefore gated.
2. If gated test fails: ship **only the stacked build** as the single universal asset. At an ~880 px
   desktop column it renders at 720 px native — crisp, and still clearly a dual-terminal
   composition, just vertical. This is the safe fallback and costs desktop drama, not quality.
3. Never: two independent side-by-side images at percentage widths — they shrink identically on
   mobile and drift out of sync.

This is **Open Decision D-2** (Section 25).

---

## 8. Portrait-processing pipeline

The pipeline that already produced a good result this session is the baseline; it is retained and
hardened rather than re-invented.

### Stage 1 — Crop (manual, one-time, recorded)
Head-and-shoulders crop. The known-good crop from `assets/img.jpg` (1198 × 879) is
`crop = (250, 170, 980, 879)` → 730 × 709. Record the box in a small JSON sidecar so the run is
reproducible without guesswork.

### Stage 2 — Background suppression
Colour heuristic, calibrated against measured samples from the actual photo:

| Region | Mean RGB (measured) |
| :--- | :--- |
| Sky | `(158, 205, 247)` |
| Hillside | `(195, 203, 204)` |
| Shirt | `(25, 39, 74)` |
| Face | `(208, 177, 178)` |

Rule (verified to isolate cleanly): `background = (gray > 150) AND NOT(r−g > 12 AND r−b > 10)`.
The brightness gate protects the dark shirt; the skin-tone exclusion protects the face against the
bright hazy hillside. Matched pixels are forced to `255`.

Rejected alternatives, with reasons — do not retry blindly:
- `ImageFilter.CONTOUR` line-art: strokes disappear below ~80 columns.
- Pure tonal conversion: hillside and sky become dense ASCII noise around the shoulders.
- `(b−r) > 12 | (g−r) > 8` without a brightness gate: eats the shirt.

### Stage 3 — Tone
`GaussianBlur(1.0)` → `Contrast(1.3)` → `autocontrast(cutoff=1)`. The blur is essential: it removes
single-pixel speckle that becomes isolated `@` glyphs.

### Stage 4 — Resample and map
- Ramp `"@%#*+=-:. "` (dark → light), 10 levels.
- Aspect correction factor **0.5** — must be replaced with a *measured* value:
  `advance_width / line_height` for Menlo at the chosen size. Compute it in the script, do not
  hard-code 0.5, or the portrait will be subtly stretched.
- Target **78 cols × 36 rows** (the current known-good output; `outputs/portrait_ascii.txt` is
  exactly this and is recognizable).
- **Dithering: no.** Floyd–Steinberg on a 10-level ramp at 78 columns adds high-frequency speckle
  that reads as noise, not texture. Evaluate once in Phase 2 and record the comparison; default off.

### Stage 5 — Reveal frames
Rows are emitted progressively into the left card. Reveal in **row order, 3 rows per frame**
(36 rows → 12 reveal steps), which is coherent, fast enough to finish inside the budget, and reads
as a terminal painting output.

### Stage 6 — Privacy
- Source photo and every intermediate raster stay in `assets/source-private/` (git-ignored).
- The only committed portrait-derived artifacts are `portrait.txt` (78×36 characters) and the
  rendered frames inside the GIF.
- A 78 × 36 ten-level quantisation is ~2 808 glyphs of ~3.3 bits — far below what would permit
  reconstruction of a 1198 × 879 photograph. This satisfies your "derived output only" rule.
- `assets/portrait_masked3.png` is a **recognizable grayscale photograph** and must remain ignored.

---

## 9. Right-terminal content and animation sequence

Your draft copy is close; it is slightly long and mixes two registers. Proposed tightening — note
every line is supported by the CV/repo and none of it invents an achievement, metric, or employer.

```
$ whoami

Salih Camcı
> Software Engineer
> Incoming MSc Data Science · University of Basel
> Former Backend Engineering Intern · Crytek

~/focus      backend systems · data science · agentic workflows
~/building   research tooling · AI systems · spatial interfaces
~/stack      Python  Go  SQL  PyTorch  FastAPI  Docker
~/links      github.com/Salih04 · linkedin/in/salih-camci · salih04.github.io
```

Changes from your draft and why:

- `Incoming MSc Data Science student at the University of Basel` → `Incoming MSc Data Science ·
  University of Basel`. Fits one line at 15 px in a 744 px card; "student" is implied by "Incoming".
- Merged `~/links` onto one line — three links do not need three rows.
- `~/stack` capped at **six** tokens. The full stack lives in the markdown below. Six is the most
  that stays scannable in a two-second read.
- Kept `Salih Camcı` with the correct Turkish `ı`. **Verify the chosen font renders U+0131 (ı) and
  U+0130 (İ)** — Menlo does; confirm in Phase 3 and fall back to `Salih Camci` only if it does not.
- Dropped "Hi, I'm" — the terminal framing already establishes voice, and it costs a line.

Skills render as **plain monospace tokens**, not pills and not badges. Pills add per-token
rectangles that inflate the GIF palette and frame deltas for no legibility gain.

---

## 10. Animation timeline

Total **13.5 s**, then rest. Both panels are on one canvas, so this is a single frame sequence.

| t (s) | Left panel | Right panel |
| ---: | :--- | :--- |
| 0.00 | Card, chrome, dots, title, `$` prompt **already visible** | Card, chrome, dots, title, `$` prompt visible |
| 0.00–0.60 | idle, cursor blink 530 ms | idle, cursor blink 530 ms |
| 0.60 | **portrait reveal begins** (3 rows / 190 ms) | — |
| 1.20 | reveal continuing | `whoami` types, 6 chars @ 95 ms |
| 1.77 | | typing ends, 350 ms beat |
| 2.15 | | `Salih Camcı` appears |
| 2.40–3.00 | | three `>` lines, 200 ms apart |
| 3.40 | | `~/focus` line |
| 4.20 | | `~/building` line |
| 5.00 | | `~/stack` tokens, staggered 110 ms |
| 5.90 | **portrait completes** (12 steps × 190 ms + 0.60) | |
| 6.30 | settled | `~/links` line |
| 6.90 | cursor blink only | cursor blink only |
| 6.90–13.50 | **6.6 s resting hold**, both panels complete | |

Design properties this satisfies:
- **Nothing is blank at t=0** — chrome and prompts paint in frame 0 (fixes P2).
- Panels are coordinated but offset: the portrait starts 0.6 s before `whoami` and finishes 0.4 s
  before the last text line, so they converge rather than marching in lockstep.
- The resting hold is ~49 % of the runtime, so a visitor most often lands on the complete state.
- No flashing, no perpetual motion except a single cursor.

**Loop policy — recommended: play once and rest.** GIF without a Netscape loop block plays through
and holds the last frame permanently. That gives a premium single performance and a permanently
readable end state, and it removes the "restarts every few seconds" failure (P3) by construction.
Produce a looping variant (`loop=0`, 6.6 s tail) as an alternative build for you to compare.
This is **Open Decision D-3**.

Note for implementation: encoder loop semantics differ — Pillow `save(loop=None)` omits the loop
block (play once) whereas `loop=0` is infinite; ffmpeg's GIF muxer uses `-loop -1` for no-loop and
`-loop 0` for infinite. Assert the emitted bytes in a test rather than trusting the flag.

---

## 11. Technology compatibility matrix

Ratings: ●●● strong / ●● acceptable / ● weak / ✖ disqualifying.
"Blank first frame" = risk the README shows nothing meaningful initially.

| # | Option | Works embedded in README | Visual fidelity | Size | Text sharpness | Mobile | A11y | Reproducible | Deps | Blank-frame risk | Proxy/sanitizer risk |
| :-- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | CSS `@keyframes` SVG | ✖ **measured fail** (portrait.svg, capsule-render) | ●●● | ●●● | ●●● | ●● | ●● | ●●● | ●●● | **High** | High |
| 2 | SMIL SVG | ✖ **rendered empty** in test (readme-typing-svg) | ●●● | ●●● | ●●● | ●● | ●● | ●●● | ●●● | **High** | High |
| 3 | asciinema `.cast` | ✖ not an image format | — | — | — | — | — | ●●● | ●● | — | — |
| 4 | `svg-term-cli` | ✖ emits option 1 | ●●● | ●● | ●●● | ● | ● | ●● | ●● | **High** | High |
| 5 | **Animated GIF** | ●●● **format GitHub animates today** | ●● | ●● | ●● | ●●● | ●● | ●●● | ●●● | **None** (frame 0 authored) | **None** |
| 6 | Animated WebP | ●● likely, unverified on camo | ●●● | ●●● | ●●● | ●●● | ●● | ●●● | ●● | None | Medium |
| 7 | APNG | ●● likely, served as PNG | ●●● | ● (large) | ●●● | ●●● | ●● | ●●● | ● (`apngasm` absent) | None | Medium |
| 8 | Deterministic frame seq → encoder | ●●● (this is *how* 5/6/7 are built) | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | None | None |
| 9 | Custom static SVG generator | ●●● **proven — `hero.svg` works live** | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | None | None |
| 10 | Static fallback raster | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● | None | None |

Key reads:

- Options **1, 2, 4 are eliminated by measurement**, not by taste. Option 4 is merely a generator
  for option 1, which is why the original attempt failed.
- Option **8 is not a rival** to 5/6/7 — it is the production method that feeds them, and it is
  what makes the result deterministic and re-runnable.
- Option **6 (WebP)** is genuinely better than GIF on size and colour, and `cwebp` + `img2webp` are
  both installed. Its only weakness is that camo behaviour for animated WebP is unverified here.
  Phase 1 tests it; if it passes, it becomes the primary and GIF becomes the fallback.
- Option **7 (APNG)** is dropped: `apngasm` is not installed, and APNG of a 1280 × 520 terminal is
  substantially larger than GIF for no benefit we need.

---

## 12. Recommended rendering architecture

**Deterministic Python frame renderer → PNG frame sequence → GIF (primary) with WebP evaluated as
an upgrade → static PNG fallback.**

```
assets/source-private/photo.jpg        (never committed)
        │  crop.json
        ▼
  portrait/build_portrait.py    →  portrait.txt        (78 × 36, committed)
        │
        ▼
  terminal/render_frames.py     →  frames/*.png        (build artifact, not committed)
        │   • content.yml  (all copy in one file)
        │   • theme.py     (tokens from §5)
        │   • timeline.py  (§10 timings)
        ▼
  terminal/encode.py            →  hero-wide.gif       (committed)
                                →  hero-stack.gif      (committed)
                                →  hero-static.png     (committed, frame @ t=13.4)
```

Why a custom renderer rather than recording a real terminal:

1. **Frame-exact timing control.** `asciinema` records wall-clock jitter from `sleep`; we need the
   §10 timeline to be exact and identical on every run.
2. **Determinism.** Same inputs → byte-identical frames. A terminal recording never reproduces.
3. **Both panels on one canvas**, which is what guarantees synchronisation.
4. **Authored frame 0**, which is the direct fix for P2.
5. No dependency on `asciinema` (two conflicting versions are installed: Homebrew 3.2.1 and pipx
   2.4.0) or on `svg-term-cli`, whose output format is disqualified anyway.

Frames are drawn with Pillow using `ImageDraw.text` at 2× scale with Menlo, then Lanczos-downsampled
to 1× — this is what produces sharp small monospace text.

Encoding: quantise to a **fixed 32-colour palette** derived from §5 (not per-frame adaptive, which
causes inter-frame colour drift and destroys delta compression), emit with per-frame durations from
§10, and enable transparency-based frame differencing. Terminal typing changes very few pixels per
frame, so deltas are small.

`gifsicle` is **not installed** — plan for `ffmpeg` (`palettegen`/`paletteuse`) plus Pillow, and add
`gifsicle` as an optional post-optimiser the script uses if present and skips cleanly if not.

---

## 13. GitHub compatibility and fallback strategy

Hard requirements and how each is met:

| Requirement | Mechanism |
| :--- | :--- |
| No JavaScript | Raster image; none possible |
| No third-party API | All assets committed to this repo |
| No external server | Same |
| Self-hosted | `assets/generated/*.gif` |
| Avoid failed CSS patterns | No SVG animation anywhere in the hero |
| Meaningful content immediately | Frame 0 authored with full chrome + prompts |
| Static fallback | `hero-static.png` behind `<picture>`; also the final GIF frame persists |
| Stable paths | Relative repo paths, as `hero.svg` uses today and which demonstrably works |
| Not oversized | Budget §19 |
| No photo leak | §18 |
| Not broken logged-out | Validated in incognito, §20 |
| Light + dark themes | Asset paints its own background |
| Understandable without animation | Every hero fact is repeated as markdown text below |

Reference syntax (relative paths — proven working for `hero.svg`):

```html
<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/generated/hero-static.png">
  <source media="(max-width: 600px)"              srcset="assets/generated/hero-stack.gif">
  <img src="assets/generated/hero-wide.gif"
       alt="Terminal showing an ASCII portrait beside a whoami command printing: Salih Camcı — Software Engineer; incoming MSc Data Science, University of Basel; former Backend Engineering Intern at Crytek."
       width="100%">
</picture>
```

Both `<source>` elements are **spike-gated in Phase 1**. If GitHub strips `media`, degrade to a bare
`<img>` per Section 7 option 2. The `<img>` fallback is always present, so the worst case is a
correct wide GIF rather than a broken image.

---

## 14. Proposed repository / file structure

```
assets/
  source-private/          ← git-ignored. photo.jpg, crop.json, masked intermediates
  generated/               ← COMMITTED. hero-wide.gif, hero-stack.gif, hero-static.png
  data/                    ← COMMITTED. portrait.txt, content.yml
  svg/                     ← existing. hero.svg retained until Phase 5 cutover
  preview/                 ← git-ignored. contact sheets, frame dumps, size reports
scripts/
  portrait/build_portrait.py
  terminal/render_frames.py
  terminal/encode.py
  terminal/theme.py
  terminal/timeline.py
  validation/check_assets.py
  validation/check_github.py
Makefile                   ← one-command regeneration
GITHUB_PROFILE_ANIMATION_PLAN.md
README.md
```

**`.gitignore` must be rewritten carefully.** Today's `assets/*` + `!assets/svg/` would silently
ignore `assets/generated/` and `assets/data/`. Proposed:

```gitignore
.venv/
.DS_Store

# Ignore everything under assets by default, then allow only derived, publishable output
assets/*
!assets/svg/
!assets/generated/
!assets/data/

# Never publish source imagery or intermediates, wherever they land
assets/source-private/
*.jpg
*.jpeg
*.heic
assets/generated/frames/
assets/preview/
```

The blanket `*.jpg` / `*.heic` rules are deliberate belt-and-braces: they make it impossible to
commit the photograph by accident even if it is moved. `outputs/` and `scripts/` are currently
ignored; `scripts/` must be **un-ignored** so the new pipeline is shareable (Section 22).

---

## 15. Script and dependency plan

### Verified toolchain on this machine

| Tool | Status | Role |
| :--- | :--- | :--- |
| `python3` | ✓ 3.9.6 (system) | renderer |
| `ffmpeg` | ✓ `/opt/anaconda3/bin/ffmpeg` | GIF palette + encode |
| `magick` / `convert` | ✓ Homebrew | inspection, contact sheets |
| `cwebp`, `img2webp` | ✓ Homebrew | WebP evaluation |
| `node`, `npm` | ✓ | not required by the new pipeline |
| `pipx` | ✓ | not required by the new pipeline |
| Menlo, SF Mono, Monaco | ✓ system | rendering font |
| `gifsicle` | ✗ absent | optional optimiser — script must skip gracefully |
| `pngquant`, `oxipng` | ✗ absent | optional PNG optimisation |
| `apngasm` | ✗ absent | APNG dropped |
| JetBrains Mono | ✗ absent | only if vendored + licence recorded |

Python 3.9.6 is the *system* interpreter; a `.venv` already exists in the repo from this session.
Pin to a project venv and require **Pillow ≥ 10** and **numpy**. Note 3.9 supports PEP 585
(`list[str]`) annotations, so the existing `scripts/img_to_ascii.py` style is fine.

### Commands

```
make portrait   # photo → assets/data/portrait.txt
make frames     # portrait.txt + content.yml → frames/*.png
make gif        # frames → hero-wide.gif, hero-stack.gif, hero-static.png
make preview    # contact sheet + byte-size report
make check      # asset budget + determinism assertions
make all        # portrait → frames → gif → check
```

Determinism: fixed palette, no randomness, no timestamps in output, sorted file iteration. `make
check` re-runs `frames` into a temp dir and asserts checksum equality.

Graceful degradation: every script probes its dependencies at start and exits with an actionable
message (`gifsicle not found — skipping optimisation pass (output still valid)`), never a traceback.

---

## 16. Content rewrite proposal

**Hero** carries the §9 copy. **Below the hero**, restrained support:

1. `## Focus` — three lines, prose, no badges.
2. `## Selected work` — 4 projects (down from 5), **plain markdown**, not a table, not SVG cards.
   Plain markdown is chosen because the current table already reflows badly in the narrow profile
   column, and SVG cards would compete with the hero for attention while adding assets to maintain.
3. `## Elsewhere` — three text links.

**Remove the 22-badge wall.** With `~/stack` in the hero, the badge grid is duplicated information
and it is the single largest source of visual noise in the current README. Retain `shields.io` only
if you want the three social badges — it is the one service that measured reliable.

Projects to keep (all verified public via `gh repo list`): `capstone-financeIQ`,
`Applied-Reinforcement-Learning-Highway`, `CLI-Task-Queue-with-Priority-Rules`,
`Face_Mask_Detection_YOLOV8`. Drop `Movie_Recommendation_System` to hold the list at four.

No statistics, no counters, no trophies, no visitor badges.

---

## 17. Accessibility and reduced-motion approach

- **`prefers-reduced-motion`**: served via `<picture>` → `hero-static.png` (spike-gated Phase 1).
  If GitHub strips it, the mitigation is that the animation plays once and rests — a far better
  reduced-motion outcome than an infinite loop, which is an independent reason to prefer play-once.
- **Alt text**: one sentence carrying the actual identity facts, not "terminal animation". Drafted
  in §13.
- **Text duplication**: every fact in the hero also appears as real markdown below, so screen
  readers and text-mode clients lose nothing. The hero is enhancement, never sole carrier.
- **Contrast**: all tokens ≥ 7.4:1 (§5).
- **No flashing**: no element changes faster than the 530 ms cursor; nothing approaches the 3 Hz
  photosensitivity threshold.
- **Motion restraint**: 49 % of runtime is a still hold.

---

## 18. Privacy and security considerations

| Concern | Control |
| :--- | :--- |
| Photograph published | Lives in `assets/source-private/`; ignored by directory rule **and** by blanket `*.jpg`/`*.heic` |
| Photograph in git history | Verified never committed on any ref. Must stay that way — the pipeline never writes to a tracked path |
| Recognizable intermediates | `portrait_masked3.png` is a real grayscale photo; stays ignored. Pipeline writes intermediates only to ignored dirs |
| Reconstruction from ASCII | 78 × 36 at 10 levels ≈ 2 808 glyphs, ~3.3 bits each — cannot reconstruct a 1198 × 879 photo |
| Personal data exposure | Only already-public facts: name, public GitHub, public LinkedIn, public portfolio |
| Email address | Currently in README as a `mailto:` badge. **Open Decision D-4** — keeping it is a scraping trade-off, not a correctness issue |
| Accidental commit | `make check` fails if any file matching source-image patterns is staged; recommend a `pre-commit` hook |
| Third-party exfiltration | None — no external service is contacted at render time |

---

## 19. Performance and file-size budget

| Asset | Budget | Rationale |
| :--- | ---: | :--- |
| `hero-wide.gif` | **≤ 1.8 MB** | ~110 frames @ 1280 × 520, 32 colours, delta-compressed |
| `hero-stack.gif` | **≤ 1.2 MB** | 720 × 940, fewer lines |
| `hero-static.png` | **≤ 150 KB** | single frame, 32-colour palette |
| `portrait.txt` | ~3 KB | 78 × 36 |
| **Total added** | **≤ 3.2 MB** | |

Levers if over budget, in order: cut the resting tail from 6.6 s to 3 s (tail frames are identical
and cheap, so this is a small win); reduce reveal granularity from 3 rows to 4 rows per frame;
drop the palette from 32 to 16 colours; reduce canvas to 1152 × 468.

Terminal content is ideal for GIF: large flat background areas, few colours, and small per-frame
deltas. If measurements land far above budget, that indicates adaptive per-frame palettes leaked in —
check the fixed-palette setting first.

Load behaviour: GitHub camo caches aggressively; first paint is the GIF's frame 0, which is already
a complete-looking terminal.

---

## 20. Verification and browser test matrix

A raw-URL check is explicitly **not** sufficient — that is the test that missed P1.

| # | Check | Method | Pass condition |
| :-- | :--- | :--- | :--- |
| V1 | Raw asset URL | `curl -I raw.githubusercontent.com/...` | 200, correct content-type, size within budget |
| V2 | Camo proxy | `curl -o /dev/null -w '%{http_code}'` on the camo URL from rendered HTML | 200, non-zero bytes |
| V3 | Repo README page | Browser at `/Salih04/Salih04` | Image present, `naturalWidth > 0` |
| V4 | **Profile page** | Browser at `/Salih04` | Same — this is the real target |
| V5 | Logged-out | Incognito, no session | Identical to V4 |
| V6 | Desktop width | 1280 / 1440 viewport | Panels side by side, text crisp |
| V7 | Mobile width | 375 / 414 viewport | No horizontal scroll; portrait recognizable; text legible |
| V8 | First visible frame | Screenshot immediately on load | Chrome, dots, prompts visible — **never blank** |
| V9 | Animation completes | Screenshot at t≈14 s | Both panels fully populated |
| V10 | Rest / loop behaviour | Screenshot at t≈25 s | Matches chosen loop policy; no mid-cycle blank |
| V11 | Hard refresh / cold cache | Cmd-Shift-R, then a fresh camo URL | Animation replays from frame 0 |
| V12 | Reduced motion | OS reduce-motion on | Static served, or (if stripped) animation still rests |
| V13 | Determinism | `make check` | Byte-identical frames across two runs |
| V14 | Privacy | `git status --porcelain` + staged-file scan | No image source staged; history still clean |

`naturalWidth > 0` is the specific probe that distinguishes "loaded but invisible" (the SMIL and
capsule-render failure mode) from "failed to load" — both look identical in a screenshot. Every
image check must assert it.

---

## 21. Phased implementation plan

### Phase 0 — Repository audit
- **Goal:** baseline established. *(Complete — this document.)*
- **Files:** none modified.
- **Acceptance:** inventory, sizes, history, privacy state, toolchain recorded.
- **Validation:** figures in §2 / §15 reproduced by command.
- **Rollback:** n/a. **Complexity:** S. **Depends on:** —

### Phase 1 — GitHub animation compatibility spike ← *highest value, do first*
- **Goal:** settle empirically, on a real GitHub page, what animates and what `<picture>` supports.
- **Files:** a throwaway **public** repo (e.g. `Salih04/render-spike`), never this repo's `main`.
- **Approach:** commit six ~50 KB probes — CSS-keyframe SVG, SMIL SVG, GIF, animated WebP, plus a
  `<picture>` with `max-width` and one with `prefers-reduced-motion`. Each probe is a clock that
  visibly changes. Screenshot at t=0, t=2, t=6 in your Brave browser and in incognito; record
  `naturalWidth` for each.
- **Acceptance:** a table stating, for each, animates yes/no and whether `media` survived.
- **Validation:** V1–V5, V8–V11 against the spike repo.
- **Failure/rollback:** if GIF somehow fails, fall back to a **static** hero (option 9, already
  proven live) and abandon animation — do not ship a broken hero.
- **Complexity:** S–M. **Depends on:** Phase 0.

### Phase 2 — Portrait pipeline
- **Goal:** reproducible `portrait.txt` from a local photo.
- **Files:** `scripts/portrait/build_portrait.py`, `assets/data/portrait.txt`, `crop.json`.
- **Approach:** §8, promoting the proven heuristic out of chat history into a script; replace the
  hard-coded 0.5 aspect factor with a measured value; run the dithering comparison once.
- **Acceptance:** portrait recognizable at 78 × 36; background pure white; two runs byte-identical.
- **Validation:** render to PNG contact sheet, visual review, `make check`.
- **Failure/rollback:** if the heuristic fails on a new photo, fall back to a manual alpha matte
  supplied as a PNG mask.
- **Complexity:** M. **Depends on:** Phase 0.

### Phase 3 — Right-terminal prototype
- **Goal:** identity panel frames, correct typography and timing.
- **Files:** `render_frames.py`, `theme.py`, `timeline.py`, `content.yml`.
- **Approach:** §5/§9/§10. Confirm `ı`/`İ` render. Verify frame 0 is authored, not empty.
- **Acceptance:** all lines fit 744 px without clipping; frame 0 shows chrome and prompt.
- **Validation:** frame dump review; GIF of the right panel alone tested on the spike repo.
- **Failure/rollback:** if lines overflow, shorten copy before enlarging the canvas.
- **Complexity:** M. **Depends on:** 1, 2.

### Phase 4 — Coordinated dual-panel composition
- **Goal:** the real assets.
- **Files:** `encode.py`; outputs `hero-wide.gif`, `hero-stack.gif`, `hero-static.png`.
- **Approach:** single canvas, fixed 32-colour palette, per-frame durations, optional `gifsicle`.
- **Acceptance:** §19 budgets met; §10 timings within ±100 ms; panels frame-locked.
- **Validation:** V8–V11 on the spike repo at both widths; byte sizes recorded.
- **Failure/rollback:** apply §19 levers in order; if still over, drop to the stacked build only.
- **Complexity:** L. **Depends on:** 3.

### Phase 5 — README integration
- **Goal:** new README with hero + restrained support content.
- **Files:** `README.md`, `.gitignore`, `assets/generated/*`.
- **Approach:** §13 markup gated on Phase 1 results; §16 content; retain `hero.svg` until Phase 6
  passes.
- **Acceptance:** renders correctly on the repo README page; no broken images; no badge wall.
- **Validation:** V3, V6, V7.
- **Failure/rollback:** revert `README.md` — `hero.svg` is untouched and still valid.
- **Complexity:** S. **Depends on:** 4.

### Phase 6 — Real profile validation
- **Goal:** prove it on `github.com/Salih04`, the only environment that counts.
- **Files:** none.
- **Approach:** full V1–V14 sweep, logged in and incognito, desktop and mobile widths.
- **Acceptance:** every row passes, especially V4, V5, V7, V8.
- **Failure/rollback:** revert to the previous README commit; profile returns to today's working state.
- **Complexity:** S. **Depends on:** 5.

### Phase 7 — Cleanup and documentation
- **Goal:** another developer can regenerate from a local photo with no chat history.
- **Files:** `scripts/README.md`, `Makefile`, `.gitignore`, archive `outputs/`.
- **Acceptance:** clean clone + own photo + `make all` reproduces assets.
- **Validation:** dry run in a fresh clone.
- **Complexity:** S. **Depends on:** 6.

---

## 22. Exact file disposition

Nothing in this list has been acted on — this is the proposal for the implementation pass.

**Create**
```
assets/data/portrait.txt              assets/data/content.yml
assets/generated/hero-wide.gif        assets/generated/hero-stack.gif
assets/generated/hero-static.png
scripts/portrait/build_portrait.py    scripts/terminal/render_frames.py
scripts/terminal/encode.py            scripts/terminal/theme.py
scripts/terminal/timeline.py          scripts/validation/check_assets.py
scripts/validation/check_github.py    scripts/README.md
Makefile
```

**Modify**
```
README.md     hero swap + §16 content; badge wall removed
.gitignore    per §14 — must un-ignore scripts/ and allow assets/generated + assets/data
```

**Retain untouched**
```
assets/svg/hero.svg          keep through Phase 6 as the rollback target
assets/img.jpg + intermediates   local only, still ignored
outputs/*                    reference for the old approach; archive in Phase 7, do not delete now
scripts/img_to_ascii.py      superseded by build_portrait.py; keep until Phase 2 passes
GITHUB_PROFILE_ANIMATION_PLAN.md
```

**Remove:** nothing in this pass. Per your instruction no file is deleted; `outputs/` is archived
rather than removed, and everything remains recoverable from commit `0fd89d0` regardless.

---

## 23. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation |
| :-- | :--- | :--- | :--- | :--- |
| R1 | GIF also fails to animate in README | Very low | High | Phase 1 gates everything; static hero (proven) is the fallback |
| R2 | `<picture media>` stripped by GitHub | Medium | Medium | Phase 1 gate; fall back to stacked-only build (§7 option 2) |
| R3 | GIF exceeds budget | Medium | Medium | Fixed palette + §19 levers |
| R4 | Mobile text too small | Medium | High | Dedicated stacked build with larger type and reduced line set |
| R5 | Photo committed by accident | Low | **Severe** | Directory ignore + blanket `*.jpg`/`*.heic` + `make check` + pre-commit hook |
| R6 | Background heuristic fails on a new photo | Medium | Low | Manual mask escape hatch (Phase 2 rollback) |
| R7 | Turkish `ı` missing from font | Low | Medium | Verify in Phase 3; Menlo supports it |
| R8 | Text blurred by browser scaling | Medium | Medium | Render 2×, emit 1×, never upscale |
| R9 | Camo caches a stale asset | Medium | Low | Content-hashed filenames on republish; hard-refresh in V11 |
| R10 | Hero animates but reads as gimmick | Low | Medium | Play-once + long rest; restrained palette; no neon |
| R11 | Scope creep back into badge walls | Medium | Low | §16 is a constraint, not a suggestion |

---

## 24. Definition of done

1. `github.com/Salih04` shows the dual-terminal hero, logged in **and** logged out.
2. First painted frame is never blank — chrome, dots and prompts are present immediately.
3. Animation completes within ~14 s and comes to rest in a fully readable state.
4. No infinite short loop; no flashing; no perpetual motion beyond one cursor.
5. Mobile at 375 px: no horizontal scroll, portrait recognizable, identity text legible.
6. Zero third-party runtime dependencies; every asset served from this repository.
7. Total added assets ≤ 3.2 MB.
8. `naturalWidth > 0` asserted for every hero image on the profile page.
9. Static fallback exists and is served under reduced-motion (or the rest-state substitutes).
10. Photograph absent from the working tree's tracked files and from all git history.
11. `make all` regenerates every committed asset from a local photo in a fresh clone.
12. Two consecutive builds produce byte-identical frames.
13. Alt text conveys the identity facts.
14. README below the hero is short: focus, four projects, three links. No badge wall.
15. Rollback is one `git revert` and the current working profile returns.

---

## 25. Open decisions requiring your approval

| ID | Decision | Options | My recommendation |
| :-- | :--- | :--- | :--- |
| **D-1** | Primary format | (a) GIF (b) animated WebP if Phase 1 passes (c) GIF now, WebP later | **(c)** — ship GIF for certainty; revisit WebP once measured |
| **D-2** | Mobile strategy | (a) `<picture media>` two builds (b) stacked build only, universal (c) wide only, accept small mobile | **(a)**, falling back to **(b)**. Not (c) — it breaks your mobile requirement |
| **D-3** | Loop policy | (a) play once + rest (b) loop with 6.6 s pause (c) ship both, you choose | **(a)** — matches "premium, controlled", and is the strongest reduced-motion answer. Build (b) for comparison |
| **D-4** | Email in README | (a) keep `mailto:` badge (b) drop, keep LinkedIn + portfolio | **(b)** — reduces scraping; LinkedIn is a sufficient channel. Your call |
| **D-5** | Hero copy | §9 rewrite vs your original draft | **§9** — but confirm the Turkish spelling `Salih Camcı`, which differs from the Latinised `Salih Camci` used in `hero.svg` and your CV today |
| **D-6** | Font | (a) Menlo, installed (b) vendor JetBrains Mono | **(a)** — zero licence/reproducibility burden; JetBrains Mono is a small aesthetic gain for real cost |
| **D-7** | Project count | 4 vs 5 | **4** — `Movie_Recommendation_System` is the weakest fit |
| **D-8** | Spike location | (a) throwaway public repo (b) branch of this repo | **(a)** — keeps `main` and your live profile untouched during testing |
| **D-9** | Badge wall | Remove entirely vs keep 3 social badges | **Remove the 22-badge tech grid; keep the 3 social badges** (`shields.io` measured reliable) |

**D-1, D-2 and D-3 block Phase 4. D-5 blocks Phase 3.** The rest can be settled during
implementation.
