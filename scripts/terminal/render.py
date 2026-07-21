#!/usr/bin/env python3
"""Render the dual-terminal hero as a deterministic frame sequence and encode it.

    python3 scripts/terminal/render.py --build wide
    python3 scripts/terminal/render.py --build stack

Design constraints this file enforces (see GITHUB_PROFILE_ANIMATION_PLAN.md):

  * Frame 0 is authored: card chrome, control dots, titles and prompts are all
    painted before any animation. GitHub renders embedded SVG statically, so the
    hero must never rely on motion to become legible.
  * Everything is drawn at 2x and Lanczos-downsampled to 1x, so the browser only
    ever downscales. This is what keeps small monospace text sharp.
  * A single canvas holds both panels, so they are frame-locked and cannot drift.
  * A fixed palette is used for quantisation. Per-frame adaptive palettes cause
    colour drift between frames and destroy GIF delta compression.
  * Output is deterministic: no randomness, no timestamps, sorted iteration.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - dependency guard
    sys.exit(f"missing dependency: {exc}. Run: make setup")

sys.path.insert(0, str(Path(__file__).parent))
import content as C  # noqa: E402

SCALE = 2
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FONT_REGULAR, FONT_BOLD = 0, 1
ADVANCE_RATIO = 0.6  # Menlo: advance width / point size (measured)

BG = (11, 16, 22)
CARD = (17, 28, 40)
TITLEBAR = (22, 34, 47)
BORDER = (31, 45, 61)
TEXT = (230, 237, 243)
ACCENT = (102, 194, 205)
MUTED = (139, 152, 165)
PROMPT = (126, 231, 135)
PORTRAIT = (159, 179, 200)  # muted steel: keeps cyan as the single accent
DOTS = [(255, 95, 87), (254, 188, 46), (40, 200, 64)]

PALETTE = [BG, CARD, TITLEBAR, BORDER, TEXT, ACCENT, MUTED, PROMPT, PORTRAIT, *DOTS]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, index=FONT_BOLD if bold else FONT_REGULAR)


@dataclass
class Layout:
    """All geometry in 2x device pixels."""

    canvas_w: int
    canvas_h: int
    left_x: int
    left_w: int
    right_x: int
    right_w: int
    card_y: int
    card_h: int
    stacked: bool
    portrait_font: int
    portrait_line: int
    body_font: int
    body_line: int
    name_font: int
    right_card_y: int = 0
    right_card_h: int = 0

    titlebar: int = 30 * SCALE
    radius: int = 10 * SCALE
    pad_x: int = 22 * SCALE
    pad_y: int = 18 * SCALE


@dataclass
class State:
    """What is visible at a given moment."""

    portrait_rows: int = 0
    typed: int = 0
    show_name: bool = False
    roles: int = 0
    fields: int = 0
    cursor: bool = True

    def key(self) -> tuple:
        return (self.portrait_rows, self.typed, self.show_name, self.roles, self.fields, self.cursor)


@dataclass
class Timeline:
    events: list[tuple[int, State]] = field(default_factory=list)

    def at(self, t_ms: int, st: State) -> None:
        self.events.append((t_ms, st))


def content_height(lay: Layout, cfg: dict) -> int:
    """Exact height the identity card needs, derived from the same offsets draw_frame uses."""
    bl = lay.body_line
    blocks = 0.55 + 1.6 + 1.25 + len(cfg["roles"]) + 0.55 + len(cfg["fields"])
    cursor_allow = int(bl * 0.7)
    return lay.titlebar + 2 * lay.pad_y + int(bl * blocks) + cursor_allow


def build_layout(stacked: bool, cols: int, rows: int, cfg: dict) -> Layout:
    """Solve font sizes so the portrait block fits its card at the true aspect."""
    margin = 14 * SCALE
    if not stacked:
        canvas_w, canvas_h = 1280 * SCALE, 520 * SCALE
        gutter = 28 * SCALE
        usable = canvas_w - 2 * margin
        left_w = int(usable * 0.394)  # 39.4% / 58.4% split of the composition
        right_x = margin + left_w + gutter
        right_w = canvas_w - margin - right_x
        lay = Layout(
            canvas_w=canvas_w, canvas_h=canvas_h,
            left_x=margin, left_w=left_w, right_x=right_x, right_w=right_w,
            card_y=margin, card_h=canvas_h - 2 * margin, stacked=False,
            portrait_font=0, portrait_line=0,
            body_font=32, body_line=64, name_font=48,
        )
        lay.right_card_y, lay.right_card_h = lay.card_y, lay.card_h
    else:
        # Deliberately narrow. The <img width="100%"> fills GitHub's ~308px
        # mobile column regardless of native size, so a smaller canvas is
        # downscaled less and the baked-in text stays legible.
        canvas_w = 420 * SCALE
        lay = Layout(
            canvas_w=canvas_w, canvas_h=0,
            left_x=margin, left_w=canvas_w - 2 * margin,
            right_x=margin, right_w=canvas_w - 2 * margin,
            card_y=margin, card_h=0, stacked=True,
            portrait_font=0, portrait_line=0,
            body_font=28, body_line=50, name_font=38,
        )

    # Fit the portrait grid inside the left card without distorting it.
    inner_w = lay.left_w - 2 * lay.pad_x
    if not stacked:
        inner_h = lay.card_h - lay.titlebar - 2 * lay.pad_y
    else:
        inner_h = 10**6  # height is derived from width in the stacked build

    adv = inner_w / cols
    line = adv / 0.456
    if rows * line > inner_h:
        line = inner_h / rows
        adv = line * 0.456
    lay.portrait_font = max(6, int(adv / ADVANCE_RATIO))
    lay.portrait_line = max(6, int(line))

    if stacked:
        block_h = rows * lay.portrait_line
        lay.card_h = block_h + lay.titlebar + 2 * lay.pad_y
        body_block = content_height(lay, cfg)
        lay.right_card_y = lay.card_y + lay.card_h + 20 * SCALE
        lay.right_card_h = body_block
        lay.canvas_h = lay.right_card_y + body_block + 14 * SCALE
    else:
        need = content_height(lay, cfg)
        if need > lay.card_h:
            sys.exit(
                f"identity content needs {need//SCALE}px but the card is "
                f"{lay.card_h//SCALE}px. Shorten content.py or raise the canvas height."
            )

    return lay


def rounded_card(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, lay: Layout, title: str) -> None:
    d.rounded_rectangle([x, y, x + w, y + h], lay.radius, fill=CARD, outline=BORDER, width=SCALE)
    # Title bar: rounded on top, squared where it meets the body.
    d.rounded_rectangle([x, y, x + w, y + lay.titlebar + lay.radius], lay.radius, fill=TITLEBAR)
    d.rectangle([x + SCALE, y + lay.titlebar, x + w - SCALE, y + lay.titlebar + lay.radius], fill=CARD)
    d.line([x, y + lay.titlebar, x + w, y + lay.titlebar], fill=BORDER, width=SCALE)

    r = 5 * SCALE
    cy = y + lay.titlebar // 2
    for i, col in enumerate(DOTS):
        cx = x + 16 * SCALE + i * 14 * SCALE
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    f = font(int(13 * SCALE))
    d.text((x + 76 * SCALE, cy), title, font=f, fill=MUTED, anchor="lm")


def draw_frame(st: State, lay: Layout, cfg: dict, portrait: list[str]) -> Image.Image:
    img = Image.new("RGB", (lay.canvas_w, lay.canvas_h), BG)
    d = ImageDraw.Draw(img)

    # ---- left card: ASCII portrait -------------------------------------
    rounded_card(d, lay.left_x, lay.card_y, lay.left_w, lay.card_h, lay, cfg["title_left"])
    pf = font(lay.portrait_font)
    grid_w = max(pf.getlength(r) for r in portrait) if portrait else 0
    px = lay.left_x + (lay.left_w - grid_w) / 2
    py = lay.card_y + lay.titlebar + lay.pad_y
    for i, row in enumerate(portrait[: st.portrait_rows]):
        d.text((px, py + i * lay.portrait_line), row, font=pf, fill=PORTRAIT)

    # ---- right card: identity -------------------------------------------
    rx, ry = lay.right_x, lay.right_card_y
    rw, rh = lay.right_w, lay.right_card_h
    rounded_card(d, rx, ry, rw, rh, lay, cfg["title_right"])

    bf = font(lay.body_font)
    nf = font(lay.name_font, bold=True)
    adv = bf.getlength("M")
    tx = rx + lay.pad_x + 6 * SCALE
    y = ry + lay.titlebar + lay.pad_y + int(lay.body_line * 0.55)

    # prompt + typed command
    d.text((tx, y), "$", font=bf, fill=PROMPT)
    typed = cfg["command"][: st.typed]
    d.text((tx + adv * 2, y), typed, font=bf, fill=TEXT)
    if st.cursor and st.typed < len(cfg["command"]):
        cxx = tx + adv * (2 + len(typed))
        d.rectangle([cxx, y + 2, cxx + adv * 0.9, y + lay.body_font], fill=ACCENT)

    y += int(lay.body_line * 1.6)
    if st.show_name:
        d.text((tx, y), C.NAME, font=nf, fill=TEXT)
    y += int(lay.body_line * 1.25)

    for role in cfg["roles"][: st.roles]:
        d.text((tx, y), ">", font=bf, fill=ACCENT)
        d.text((tx + adv * 2, y), role, font=bf, fill=MUTED)
        y += lay.body_line
    y += (len(cfg["roles"]) - st.roles) * lay.body_line + int(lay.body_line * 0.55)

    label_w = max(len(k) for k, _ in cfg["fields"]) + 2
    for key, val in cfg["fields"][: st.fields]:
        d.text((tx, y), key, font=bf, fill=ACCENT)
        d.text((tx + adv * label_w, y), val, font=bf, fill=TEXT)
        y += lay.body_line

    # resting cursor once everything has landed
    if st.fields == len(cfg["fields"]) and st.cursor:
        d.rectangle([tx, y + 8, tx + adv * 0.9, y + lay.body_font], fill=ACCENT)

    return img.resize((lay.canvas_w // SCALE, lay.canvas_h // SCALE), Image.LANCZOS)


def build_timeline(rows: int, cfg: dict) -> Timeline:
    """The §10 schedule. Times in ms; state is sampled at each boundary."""
    tl = Timeline()
    cmd_len = len(cfg["command"])
    n_roles, n_fields = len(cfg["roles"]), len(cfg["fields"])

    step = 3  # portrait rows revealed per frame
    reveal_steps = (rows + step - 1) // step

    def portrait_at(t: int) -> int:
        if t < 600:
            return 0
        done = (t - 600) // 190
        return min(rows, done * step)

    marks: list[int] = [0, 300]
    marks += [600 + i * 190 for i in range(reveal_steps + 1)]
    marks += [1200 + i * 95 for i in range(cmd_len + 1)]
    marks += [2150, 2400, 2600, 2800, 3400, 4200, 5000, 6300, 6900, 7600, 8400, 9200, 13500]
    marks = sorted(set(m for m in marks if m <= 13500))

    for t in marks:
        st = State()
        st.portrait_rows = portrait_at(t)
        st.typed = 0 if t < 1200 else min(cmd_len, (t - 1200) // 95)
        st.show_name = t >= 2150
        st.roles = 0 if t < 2400 else min(n_roles, (t - 2400) // 200 + 1)
        if t < 3400:
            st.fields = 0
        else:
            st.fields = min(n_fields, (t - 3400) // 800 + 1)
        # cursor blinks only while idle before typing starts
        st.cursor = True if t >= 1200 else (t // 530) % 2 == 0
        tl.at(t, st)

    return tl


def encode_gif(frames: list[tuple[Image.Image, int]], out: Path, loop_forever: bool) -> None:
    pal = Image.new("P", (1, 1))
    flat: list[int] = []
    for c in PALETTE:
        flat.extend(c)
    flat.extend([0, 0, 0] * (256 - len(PALETTE)))
    pal.putpalette(flat)

    quantised = [im.quantize(palette=pal, dither=Image.NONE) for im, _ in frames]
    durations = [d for _, d in frames]

    kwargs = dict(
        save_all=True,
        append_images=quantised[1:],
        duration=durations,
        optimize=True,
        disposal=1,
    )
    if loop_forever:
        kwargs["loop"] = 0  # infinite
    # omitting `loop` entirely => no Netscape block => plays once and rests

    out.parent.mkdir(parents=True, exist_ok=True)
    quantised[0].save(out, format="GIF", **kwargs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", choices=["wide", "stack"], default="wide")
    ap.add_argument("--loop", action="store_true", help="infinite loop instead of play-once")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--still", type=Path, default=None, help="also write the final frame as PNG")
    args = ap.parse_args()

    stacked = args.build == "stack"
    cfg = C.STACK if stacked else C.WIDE
    src = Path("assets/data/portrait-stack.txt" if stacked else "assets/data/portrait.txt")
    if not src.exists():
        sys.exit(f"missing {src}. Run: make portrait")

    portrait = src.read_text().rstrip("\n").split("\n")
    rows, cols = len(portrait), len(portrait[0])
    lay = build_layout(stacked, cols, rows, cfg)

    # Enforce the line-length budget rather than discovering overflow visually.
    bf = font(lay.body_font)
    limit = lay.right_w - 2 * lay.pad_x - 12 * SCALE
    label_w = max(len(k) for k, _ in cfg["fields"]) + 2
    adv = bf.getlength("M")
    for key, val in cfg["fields"]:
        if adv * label_w + bf.getlength(val) > limit:
            sys.exit(f"line too long for {args.build} card: {key} {val!r}")
    for role in cfg["roles"]:
        if adv * 2 + bf.getlength(role) > limit:
            sys.exit(f"role too long for {args.build} card: {role!r}")

    tl = build_timeline(rows, cfg)

    frames: list[tuple[Image.Image, int]] = []
    cache: dict[tuple, Image.Image] = {}
    for i, (t, st) in enumerate(tl.events):
        nxt = tl.events[i + 1][0] if i + 1 < len(tl.events) else t + 3000
        dur = nxt - t
        if dur <= 0:
            continue
        k = st.key()
        if k not in cache:
            cache[k] = draw_frame(st, lay, cfg, portrait)
        if frames and frames[-1][0] is cache[k]:
            frames[-1] = (frames[-1][0], frames[-1][1] + dur)
        else:
            frames.append((cache[k], dur))

    out = args.out or Path(f"assets/generated/hero-{args.build}.gif")
    encode_gif(frames, out, args.loop)

    if args.still:
        args.still.parent.mkdir(parents=True, exist_ok=True)
        frames[-1][0].save(args.still, format="PNG", optimize=True)

    total = sum(d for _, d in frames)
    kb = out.stat().st_size / 1024
    print(
        f"{args.build}: {lay.canvas_w // SCALE}x{lay.canvas_h // SCALE}  "
        f"{len(frames)} frames  {total/1000:.1f}s  {kb:.0f} KB  -> {out}"
    )


if __name__ == "__main__":
    main()
