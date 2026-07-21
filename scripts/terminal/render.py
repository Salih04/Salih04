#!/usr/bin/env python3
"""Render the dual-terminal hero as a deterministic frame sequence and encode it.

    python3 scripts/terminal/render.py --build wide --loop
    python3 scripts/terminal/render.py --build stack --loop

Design constraints this file enforces (see scripts/README.md):

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
EMOJI_PATH = "/System/Library/Fonts/Apple Color Emoji.ttc"
FONT_REGULAR, FONT_BOLD = 0, 1
ADVANCE_RATIO = 0.6  # Menlo: advance width / point size (measured)
WAVE = "\U0001F44B"

BG = (11, 16, 22)
CARD = (17, 28, 40)
TITLEBAR = (22, 34, 47)
BORDER = (31, 45, 61)
TEXT = (230, 237, 243)
ACCENT = (102, 194, 205)
MUTED = (139, 152, 165)
PROMPT = (126, 231, 135)
PORTRAIT = (159, 179, 200)
PILL_EDGE = (46, 96, 116)
DOTS = [(255, 95, 87), (254, 188, 46), (40, 200, 64)]

BASE_PALETTE = [BG, CARD, TITLEBAR, BORDER, TEXT, ACCENT, MUTED, PROMPT, PORTRAIT, PILL_EDGE, *DOTS]

# Timing (ms)
BLINK_MS = 530
PORTRAIT_START, PORTRAIT_STEP = 600, 105
TYPE_START, TYPE_MS = 1200, 95
NAME_AT = 2150
FIELDS_AT, FIELD_STEP = 2700, 260
SKILLS_AT, SKILL_STEP = 3900, 85
CONNECT_AT = 4900
ROT_START = 5300
ROT_TYPE, ROT_DEL, ROT_HOLD, ROT_GAP = 45, 25, 1000, 200

_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}
_emoji_cache: dict[int, Image.Image] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    k = (size, bold)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONT_PATH, size, index=FONT_BOLD if bold else FONT_REGULAR)
    return _font_cache[k]


def emoji(height: int) -> Image.Image:
    """The wave emoji as an RGBA bitmap. Menlo has no emoji coverage."""
    if height not in _emoji_cache:
        f = ImageFont.truetype(EMOJI_PATH, 160)
        im = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((20, 20), WAVE, font=f, embedded_color=True)
        im = im.crop(im.getbbox())
        w = max(1, int(im.width * height / im.height))
        _emoji_cache[height] = im.resize((w, height), Image.LANCZOS)
    return _emoji_cache[height]


@dataclass
class Layout:
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
    name_font: int
    small_font: int
    pill_font: int
    right_card_y: int = 0
    right_card_h: int = 0

    titlebar: int = 30 * SCALE
    radius: int = 10 * SCALE
    pad_x: int = 22 * SCALE
    pad_y: int = 18 * SCALE


@dataclass
class State:
    portrait_rows: int = 0
    typed: int = 0
    show_name: bool = False
    rot_i: int = 0
    rot_n: int = 0
    rot_active: bool = False
    fields: int = 0
    skills: int = 0
    connect: bool = False
    cursor: bool = True

    def key(self) -> tuple:
        return (self.portrait_rows, self.typed, self.show_name, self.rot_i, self.rot_n,
                self.rot_active, self.fields, self.skills, self.connect, self.cursor)


@dataclass
class Timeline:
    events: list[tuple[int, State]] = field(default_factory=list)


# ---------------------------------------------------------------- layout ----

def pill_rows(cfg: dict, lay: Layout, inner_w: int) -> list[list[tuple[str, int]]]:
    """Greedy wrap of skill pills into rows that fit inner_w."""
    pf = font(lay.pill_font)
    pad = 14 * SCALE
    gap = 9 * SCALE
    rows: list[list[tuple[str, int]]] = [[]]
    used = 0
    for s in cfg["skills"]:
        w = int(pf.getlength(s)) + 2 * pad
        add = w if not rows[-1] else w + gap
        if used + add > inner_w and rows[-1]:
            rows.append([])
            used = w
            rows[-1].append((s, w))
        else:
            used += add
            rows[-1].append((s, w))
    return rows


def right_content_height(lay: Layout, cfg: dict) -> int:
    rows = pill_rows(cfg, lay, lay.right_w - 2 * lay.pad_x)
    h = lay.titlebar + lay.pad_y
    h += int(lay.small_font * 1.5)            # $ whoami
    h += int(lay.name_font * 1.5)             # greeting + name
    h += int(lay.body_font * 2.1)             # rotating line
    h += len(cfg["fields"]) * int(lay.body_font * 1.6)
    h += int(lay.small_font * 1.0)            # gap before SKILLS
    h += int(lay.small_font * 1.9)            # SKILLS label
    h += len(rows) * int(lay.pill_font * 2.3)
    h += int(lay.small_font * 0.9)            # gap after pills
    h += int(lay.small_font * 2.1)            # connect line
    h += lay.pad_y
    return h


def build_layout(stacked: bool, cols: int, rows: int, cfg: dict) -> Layout:
    margin = 14 * SCALE
    if not stacked:
        canvas_w = 1280 * SCALE
        gutter = 28 * SCALE
        usable = canvas_w - 2 * margin
        left_w = int(usable * 0.38)
        right_x = margin + left_w + gutter
        lay = Layout(
            canvas_w=canvas_w, canvas_h=0,
            left_x=margin, left_w=left_w,
            right_x=right_x, right_w=canvas_w - margin - right_x,
            card_y=margin, card_h=0, stacked=False,
            portrait_font=0, portrait_line=0,
            body_font=40, name_font=76, small_font=32, pill_font=32,
        )
        card_h = right_content_height(lay, cfg)
        lay.card_h = card_h
        lay.canvas_h = card_h + 2 * margin
        lay.right_card_y, lay.right_card_h = lay.card_y, card_h
    else:
        canvas_w = 460 * SCALE
        lay = Layout(
            canvas_w=canvas_w, canvas_h=0,
            left_x=margin, left_w=canvas_w - 2 * margin,
            right_x=margin, right_w=canvas_w - 2 * margin,
            card_y=margin, card_h=0, stacked=True,
            portrait_font=0, portrait_line=0,
            body_font=30, name_font=52, small_font=26, pill_font=26,
        )

    # Fit the portrait grid inside the left card without distorting it.
    inner_w = lay.left_w - 2 * lay.pad_x
    inner_h = (lay.card_h - lay.titlebar - 2 * lay.pad_y) if not stacked else 10**6
    adv = inner_w / cols
    line = adv / 0.456
    if rows * line > inner_h:
        line = inner_h / rows
        adv = line * 0.456
    lay.portrait_font = max(6, int(adv / ADVANCE_RATIO))
    lay.portrait_line = max(6, int(line))

    if stacked:
        lay.card_h = rows * lay.portrait_line + lay.titlebar + 2 * lay.pad_y
        lay.right_card_y = lay.card_y + lay.card_h + 20 * SCALE
        lay.right_card_h = right_content_height(lay, cfg)
        lay.canvas_h = lay.right_card_y + lay.right_card_h + margin

    return lay


# --------------------------------------------------------------- drawing ----

def rounded_card(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, lay: Layout, title: str) -> None:
    d.rounded_rectangle([x, y, x + w, y + h], lay.radius, fill=CARD, outline=BORDER, width=SCALE)
    d.rounded_rectangle([x, y, x + w, y + lay.titlebar + lay.radius], lay.radius, fill=TITLEBAR)
    d.rectangle([x + SCALE, y + lay.titlebar, x + w - SCALE, y + lay.titlebar + lay.radius], fill=CARD)
    d.line([x, y + lay.titlebar, x + w, y + lay.titlebar], fill=BORDER, width=SCALE)

    r = 5 * SCALE
    cy = y + lay.titlebar // 2
    for i, col in enumerate(DOTS):
        cx = x + 16 * SCALE + i * 14 * SCALE
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    d.text((x + w / 2, cy), title, font=font(int(13 * SCALE)), fill=MUTED, anchor="mm")


def draw_frame(st: State, lay: Layout, cfg: dict, portrait: list[str]) -> Image.Image:
    img = Image.new("RGB", (lay.canvas_w, lay.canvas_h), BG)
    d = ImageDraw.Draw(img)

    # ---- left: ASCII portrait
    rounded_card(d, lay.left_x, lay.card_y, lay.left_w, lay.card_h, lay, cfg["title_left"])
    pf = font(lay.portrait_font)
    grid_w = max(pf.getlength(r) for r in portrait) if portrait else 0
    px = lay.left_x + (lay.left_w - grid_w) / 2
    block_h = len(portrait) * lay.portrait_line
    py = lay.card_y + lay.titlebar + (lay.card_h - lay.titlebar - block_h) / 2
    for i, row in enumerate(portrait[: st.portrait_rows]):
        d.text((px, py + i * lay.portrait_line), row, font=pf, fill=PORTRAIT)

    # ---- right: identity
    rx, ry, rw = lay.right_x, lay.right_card_y, lay.right_w
    rounded_card(d, rx, ry, rw, lay.right_card_h, lay, cfg["title_right"])

    bf, sf, nf = font(lay.body_font), font(lay.small_font), font(lay.name_font, bold=True)
    adv = bf.getlength("M")
    tx = rx + lay.pad_x + 6 * SCALE
    y = ry + lay.titlebar + lay.pad_y

    # $ whoami
    d.text((tx, y), "$", font=sf, fill=PROMPT)
    typed = cfg["command"][: st.typed]
    d.text((tx + sf.getlength("M") * 2, y), typed, font=sf, fill=MUTED)
    if st.typed < len(cfg["command"]) and st.cursor:
        cx = tx + sf.getlength("M") * (2 + len(typed))
        d.rectangle([cx, y + 4, cx + sf.getlength("M") * 0.85, y + lay.small_font], fill=ACCENT)
    y += int(lay.small_font * 1.5)

    # Hi 👋 I'm Salih Camcı
    if st.show_name:
        cx = tx
        d.text((cx, y), C.GREETING, font=nf, fill=TEXT)
        cx += nf.getlength(C.GREETING) + nf.getlength(" ") * 0.6
        em = emoji(int(lay.name_font * 0.92))
        img.paste(em, (int(cx), int(y + lay.name_font * 0.12)), em)
        cx += em.width + nf.getlength(" ") * 0.8
        d.text((cx, y), C.GREETING_TAIL, font=nf, fill=TEXT)
        cx += nf.getlength(C.GREETING_TAIL + " ")
        d.text((cx, y), C.NAME, font=nf, fill=ACCENT)
    y += int(lay.name_font * 1.5)

    # rotating role line
    if st.rot_active:
        d.text((tx, y), ">", font=bf, fill=ACCENT)
        phrase = cfg["rotate"][st.rot_i][: st.rot_n]
        d.text((tx + adv * 2, y), phrase, font=bf, fill=TEXT)
        cx = tx + adv * (2 + len(phrase))
        if st.cursor:
            d.rectangle([cx + adv * 0.1, y + 4, cx + adv * 0.9, y + lay.body_font], fill=ACCENT)
    y += int(lay.body_font * 2.1)

    # ~/field  ->  value
    label_w = max(len(k) for k, _ in cfg["fields"]) + 2
    for key, val in cfg["fields"][: st.fields]:
        d.text((tx, y), key, font=bf, fill=ACCENT)
        d.text((tx + adv * label_w, y), "→", font=bf, fill=MUTED)
        d.text((tx + adv * (label_w + 2), y), val, font=bf, fill=TEXT)
        y += int(lay.body_font * 1.6)
    y += (len(cfg["fields"]) - st.fields) * int(lay.body_font * 1.6)
    y += int(lay.small_font * 1.0)

    # SKILLS
    if st.skills > 0:
        d.text((tx, y), "S K I L L S", font=sf, fill=MUTED)
    y += int(lay.small_font * 1.9)

    rows_ = pill_rows(cfg, lay, rw - 2 * lay.pad_x)
    pfp = font(lay.pill_font)
    pad, gap = 14 * SCALE, 9 * SCALE
    ph = int(lay.pill_font * 1.75)
    shown = 0
    for row in rows_:
        cx = tx
        for label, w in row:
            if shown < st.skills:
                d.rounded_rectangle([cx, y, cx + w, y + ph], ph // 2, outline=PILL_EDGE, width=SCALE)
                d.text((cx + pad, y + ph / 2), label, font=pfp, fill=ACCENT, anchor="lm")
            shown += 1
            cx += w + gap
        y += int(lay.pill_font * 2.3)
    y += int(lay.small_font * 0.9)

    # $ connect --with GitHub · LinkedIn · Portfolio
    if st.connect:
        d.text((tx, y), "$", font=sf, fill=PROMPT)
        cx = tx + sf.getlength("M") * 2
        d.text((cx, y), "connect --with", font=sf, fill=MUTED)
        cx += sf.getlength("connect --with  ")
        for i, name in enumerate(cfg["connect"]):
            if i:
                d.text((cx, y), "·", font=sf, fill=MUTED)
                cx += sf.getlength("  ")
            d.text((cx, y), name, font=sf, fill=ACCENT)
            cx += sf.getlength(name + "  ")

    return img.resize((lay.canvas_w // SCALE, lay.canvas_h // SCALE), Image.LANCZOS)


# -------------------------------------------------------------- timeline ----

def rotation_events(phrases: list[str], start: int) -> tuple[list[tuple[int, int, int]], int]:
    """(t, phrase_index, chars_visible) for one full pass; plus the end time."""
    out: list[tuple[int, int, int]] = []
    t = start
    for i, p in enumerate(phrases):
        for n in range(len(p) + 1):
            out.append((t, i, n))
            t += ROT_TYPE
        t += ROT_HOLD
        for n in range(len(p), -1, -1):
            out.append((t, i, n))
            t += ROT_DEL
        t += ROT_GAP
    return out, t


def build_timeline(rows: int, cfg: dict) -> tuple[Timeline, int]:
    tl = Timeline()
    cmd_len = len(cfg["command"])
    n_fields = len(cfg["fields"])
    n_skills = len(cfg["skills"])

    rot, loop_end = rotation_events(cfg["rotate"], ROT_START)
    rot_by_t = {t: (i, n) for t, i, n in rot}

    marks: list[int] = [0]
    marks += [i * BLINK_MS for i in range(1, TYPE_START // BLINK_MS + 1)]
    marks += [PORTRAIT_START + i * PORTRAIT_STEP for i in range(rows + 1)]
    marks += [TYPE_START + i * TYPE_MS for i in range(cmd_len + 1)]
    marks += [NAME_AT]
    marks += [FIELDS_AT + i * FIELD_STEP for i in range(n_fields)]
    marks += [SKILLS_AT + i * SKILL_STEP for i in range(n_skills)]
    marks += [CONNECT_AT]
    marks += [t for t, _, _ in rot]
    marks = sorted(set(m for m in marks if m <= loop_end))

    last_rot = (0, 0)
    for t in marks:
        st = State()
        st.portrait_rows = 0 if t < PORTRAIT_START else min(rows, (t - PORTRAIT_START) // PORTRAIT_STEP)
        st.typed = 0 if t < TYPE_START else min(cmd_len, (t - TYPE_START) // TYPE_MS)
        st.show_name = t >= NAME_AT
        st.fields = 0 if t < FIELDS_AT else min(n_fields, (t - FIELDS_AT) // FIELD_STEP + 1)
        st.skills = 0 if t < SKILLS_AT else min(n_skills, (t - SKILLS_AT) // SKILL_STEP + 1)
        st.connect = t >= CONNECT_AT
        if t in rot_by_t:
            last_rot = rot_by_t[t]
        st.rot_active = t >= ROT_START
        st.rot_i, st.rot_n = last_rot
        # Blink while idle before typing; the rotating caret is always on once
        # rotation starts, which is what makes the line read as "being typed".
        st.cursor = (t // BLINK_MS) % 2 == 0 if t < TYPE_START else True
        tl.events.append((t, st))

    return tl, loop_end


# --------------------------------------------------------------- encoding ---

def fixed_palette(sample: Image.Image | None = None) -> Image.Image:
    """Stable palette. Emoji colours are folded in so the wave survives quantisation."""
    cols = list(BASE_PALETTE)
    if sample is not None:
        q = sample.convert("RGB").quantize(colors=32)
        pal = q.getpalette() or []
        for i in range(32):
            c = tuple(pal[i * 3:i * 3 + 3])
            if len(c) == 3 and c not in cols:
                cols.append(c)
    cols = cols[:256]
    pal_img = Image.new("P", (1, 1))
    flat: list[int] = []
    for c in cols:
        flat.extend(c)
    flat.extend([0, 0, 0] * (256 - len(cols)))
    pal_img.putpalette(flat)
    return pal_img


def encode_gif(frames: list[tuple[Image.Image, int]], out: Path, loop_forever: bool, pal: Image.Image) -> None:
    quantised = [im.quantize(palette=pal, dither=Image.NONE) for im, _ in frames]
    kwargs = dict(save_all=True, append_images=quantised[1:],
                  duration=[d for _, d in frames], optimize=True, disposal=1)
    if loop_forever:
        kwargs["loop"] = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    quantised[0].save(out, format="GIF", **kwargs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", choices=["wide", "stack"], default="wide")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--still", type=Path, default=None)
    args = ap.parse_args()

    stacked = args.build == "stack"
    cfg = C.STACK if stacked else C.WIDE
    src = Path("assets/data/portrait-stack.txt" if stacked else "assets/data/portrait.txt")
    if not src.exists():
        sys.exit(f"missing {src}. Run: make portrait")

    portrait = src.read_text().rstrip("\n").split("\n")
    rows, cols = len(portrait), len(portrait[0])
    lay = build_layout(stacked, cols, rows, cfg)

    # Budget check: fail loudly rather than clipping.
    bf = font(lay.body_font)
    adv = bf.getlength("M")
    limit = lay.right_w - 2 * lay.pad_x - 12 * SCALE
    label_w = max(len(k) for k, _ in cfg["fields"]) + 2
    for key, val in cfg["fields"]:
        if adv * (label_w + 2) + bf.getlength(val) > limit:
            sys.exit(f"field too long for {args.build}: {key} {val!r}")
    for p in cfg["rotate"]:
        if adv * 3 + bf.getlength(p) > limit:
            sys.exit(f"rotate line too long for {args.build}: {p!r}")

    tl, loop_end = build_timeline(rows, cfg)

    frames: list[tuple[Image.Image, int]] = []
    cache: dict[tuple, Image.Image] = {}
    for i, (t, st) in enumerate(tl.events):
        nxt = tl.events[i + 1][0] if i + 1 < len(tl.events) else loop_end + 400
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

    pal = fixed_palette(sample=frames[-1][0])
    out = args.out or Path(f"assets/generated/hero-{args.build}.gif")
    encode_gif(frames, out, args.loop, pal)

    if args.still:
        args.still.parent.mkdir(parents=True, exist_ok=True)
        frames[-1][0].quantize(palette=pal, dither=Image.NONE).save(
            args.still, format="PNG", optimize=True)

    total = sum(d for _, d in frames)
    print(f"{args.build}: {lay.canvas_w // SCALE}x{lay.canvas_h // SCALE}  "
          f"{len(frames)} frames  {total/1000:.1f}s  {out.stat().st_size/1024:.0f} KB  -> {out}")


if __name__ == "__main__":
    main()
