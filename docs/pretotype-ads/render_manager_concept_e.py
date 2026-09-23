#!/usr/bin/env python3
"""Render TobinAI pretotype Meta video, manager concept E v2d.

Same ~12s beats, TobinAI lines, and free-trial CTA as v2c.
Tagline under the CTA: "Property management. Zero stress."
No price and no city name.

  vertical 1080x1920 → manager-concept-e-v2d-1080x1920.mp4
  square   1080x1080 → manager-concept-e-v2d-1080.mp4

Usage:
  python3 docs/pretotype-ads/render_manager_concept_e.py
  python3 docs/pretotype-ads/render_manager_concept_e.py --stills /tmp/ad-stills
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 30
DURATION = 12.0
OUT_DIR = Path(__file__).resolve().parent

FONT_REG = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
FONT_MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
FONT_SEM = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"

INDIGO = (99, 102, 241)
CYAN = (0, 212, 255)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
INK = (8, 12, 22)

NOTICES = [
    ("LEAK", (56, 189, 248), "Unit 2B", "Kitchen sink won't stop leaking"),
    ("AC", (34, 211, 238), "Unit 4A", "AC died. It's 86° inside"),
    ("LOCK", (251, 191, 36), "Unit 1C", "Front door lock is stuck"),
    ("PIPE", (167, 139, 250), "Unit 3D", "Toilet running all night"),
    ("DISP", (251, 113, 133), "Unit 5A", "Garbage disposal just jammed"),
]


@dataclass(frozen=True)
class Layout:
    name: str
    w: int
    h: int
    outfile: str


VERTICAL = Layout("vertical", 1080, 1920, "manager-concept-e-v2d-1080x1920.mp4")
SQUARE = Layout("square", 1080, 1080, "manager-concept-e-v2d-1080.mp4")

_FONTS: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
_BG: dict[str, Image.Image] = {}
_NOTICES: dict[tuple[str, int, int], Image.Image] = {}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(path, size)
    return _FONTS[key]


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return a if x < a else b if x > b else x


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x: float) -> float:
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_out_back(x: float) -> float:
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def rgba(color: tuple[int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], alpha)


def vertical_gradient(w: int, h: int, c1: tuple[int, int, int], c2: tuple[int, int, int]) -> Image.Image:
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        u = y / max(1, h - 1)
        px[0, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * u) for i in range(3))
    return strip.resize((w, h), Image.Resampling.NEAREST).convert("RGBA")


def build_background(layout: Layout) -> Image.Image:
    img = vertical_gradient(layout.w, layout.h, (7, 11, 22), (13, 20, 40))
    glow = Image.new("RGBA", (layout.w, layout.h), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse(
        [layout.w * 0.05, layout.h * 0.08, layout.w * 0.95, layout.h * 0.42],
        fill=rgba(INDIGO, 80),
    )
    d.ellipse(
        [layout.w * 0.25, layout.h * 0.55, layout.w * 1.05, layout.h * 0.95],
        fill=rgba((14, 116, 144), 50),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img, glow)
    return img


def text_size(text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = fnt.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def paste_text(
    base: Image.Image,
    text: str,
    fnt: ImageFont.FreeTypeFont,
    xy: tuple[float, float],
    fill: tuple[int, int, int],
    alpha: int = 255,
    anchor: str = "lt",
) -> None:
    if alpha <= 0 or not text:
        return
    bbox = fnt.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    layer = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((2 - bbox[0], 2 - bbox[1]), text, font=fnt, fill=rgba(fill, alpha))
    x, y = xy
    if anchor == "mm":
        x -= layer.width / 2
        y -= layer.height / 2
    elif anchor == "mt":
        x -= layer.width / 2
    elif anchor == "lm":
        y -= layer.height / 2
    elif anchor == "rt":
        x -= layer.width
    base.alpha_composite(layer, (int(x), int(y)))


def rounded_card(
    w: int,
    h: int,
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    outline_width: int = 2,
) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=fill, outline=outline, width=outline_width)
    return img


_SHADOWS: dict[tuple[int, int, int], Image.Image] = {}


def shadow_for(w: int, h: int, radius: int = 28) -> Image.Image:
    key = (w, h, radius)
    if key in _SHADOWS:
        return _SHADOWS[key]
    pad = 48
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad + 10, pad + w, pad + 10 + h], radius=radius, fill=(0, 0, 0, 110))
    img = img.filter(ImageFilter.GaussianBlur(18))
    _SHADOWS[key] = img
    return img


def make_notice(width: int, height: int) -> dict[int, Image.Image]:
    """Pre-render the five notification cards at a given size."""
    key_base = (width, height)
    cached = {}
    for i, (label, accent, title, body) in enumerate(NOTICES):
        cache_key = (label, width, height)
        if cache_key in _NOTICES:
            cached[i] = _NOTICES[cache_key]
            continue
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        card = rounded_card(width, height, 28, (16, 22, 38, 238), (255, 255, 255, 32), 2)
        img.alpha_composite(card)
        d = ImageDraw.Draw(img)
        icon = 64 if height >= 120 else 52
        ix, iy = 22, (height - icon) // 2
        d.rounded_rectangle([ix, iy, ix + icon, iy + icon], radius=16, fill=rgba(accent, 255))
        lf = font(FONT_BOLD, 15 if len(label) > 3 else 18)
        paste_text(img, label, lf, (ix + icon / 2, iy + icon / 2 - 1), (8, 12, 22), anchor="mm")
        tx = ix + icon + 18
        paste_text(img, title, font(FONT_SEM, 30 if height >= 130 else 26), (tx, 22 if height >= 130 else 16), WHITE)
        paste_text(img, body, font(FONT_REG, 26 if height >= 130 else 22), (tx, 62 if height >= 130 else 50), MUTED)
        paste_text(img, "now", font(FONT_MED, 20), (width - 22, 24 if height >= 130 else 18), (100, 116, 139), anchor="rt")
        _NOTICES[cache_key] = img
        cached[i] = img
    _ = key_base
    return cached


def paste_center(base: Image.Image, layer: Image.Image, cx: float, cy: float, alpha: int = 255) -> None:
    if alpha <= 0:
        return
    im = layer
    if alpha < 255:
        im = layer.copy()
        band = im.getchannel("A").point(lambda p: p * alpha // 255)
        im.putalpha(band)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def new_frame(layout: Layout) -> Image.Image:
    if layout.name not in _BG:
        _BG[layout.name] = build_background(layout)
    return _BG[layout.name].copy()


def fade_slide_text(
    base: Image.Image,
    text: str,
    fnt: ImageFont.FreeTypeFont,
    center: tuple[float, float],
    fill: tuple[int, int, int],
    local_t: float,
    delay: float,
    rise: float = 28,
) -> None:
    u = ease_out((local_t - delay) / 0.45)
    if u <= 0:
        return
    x, y = center
    paste_text(base, text, fnt, (x, y + (1 - u) * rise), fill, alpha=int(255 * u), anchor="mm")


def draw_hook(local: float, layout: Layout) -> Image.Image:
    """Tired line over the still-chaos notification pile."""
    im = new_frame(layout)
    tall = layout.h > 1400
    placed, scrim = pile_and_scrim(layout)
    for rot, px, py in placed:
        im.alpha_composite(rot, (px, py))
    im = Image.alpha_composite(im, scrim)

    head_size = 84 if tall else 56
    block_y = layout.h * (0.46 if tall else 0.48)
    lines = ["Tired of", "self-managing", "maintenance?"]
    fills = [WHITE, WHITE, CYAN]
    gap = head_size + (8 if tall else 4)
    top = block_y - gap
    for i, (line, col) in enumerate(zip(lines, fills)):
        fade_slide_text(im, line, font(FONT_BOLD, head_size), (layout.w / 2, top + i * gap), col, local, 0.04 + i * 0.12)
    return im


def notice_geometry(layout: Layout) -> tuple[int, int, int, int, int]:
    """Return x, first_y, width, height, gap for the notification stack."""
    if layout.h > 1400:
        width, height, gap = 900, 148, 16
        x = (layout.w - width) // 2
        first_y = 560
    else:
        width, height, gap = 920, 112, 12
        x = (layout.w - width) // 2
        first_y = 250
    return x, first_y, width, height, gap


def draw_barrage(local: float, layout: Layout) -> Image.Image:
    im = new_frame(layout)
    tall = layout.h > 1400
    x, first_y, width, height, gap = notice_geometry(layout)
    cards = make_notice(width, height)
    shadows = shadow_for(width, height)

    # Lock-screen clock stays up so the stack reads as a phone, not a floating list.
    if tall:
        paste_text(im, "9:14", font(FONT_BOLD, 132), (layout.w / 2, 300), WHITE, anchor="mm")
        paste_text(im, "Saturday, September 12", font(FONT_MED, 30), (layout.w / 2, 400), MUTED, anchor="mm")
    else:
        paste_text(im, "9:14  ·  Saturday", font(FONT_BOLD, 42), (layout.w / 2, 128), WHITE, anchor="mm")

    starts = [0.06, 0.46, 0.86, 1.26, 1.66]
    shake = 0.0
    if local > 2.15:
        shake = math.sin(local * 28) * min(7, (local - 2.15) * 10)

    for i, start in enumerate(starts):
        u = ease_out_back((local - start) / 0.32)
        if u <= 0:
            continue
        # Later cards push the stack; each card's rest y is first_y + i * stride
        rest_y = first_y + i * (height + gap)
        # Enter from above
        y = lerp(rest_y - 80, rest_y, min(u, 1))
        y += shake * (0.4 + i * 0.15)
        alpha = int(255 * clamp(u * 1.4))
        sx = x - 48 + int((1 - min(u, 1)) * 30)
        # shadow
        sh = shadows
        if alpha < 255:
            sh = shadows.copy()
            sh.putalpha(sh.getchannel("A").point(lambda p, a=alpha: p * a // 255))
        im.alpha_composite(sh, (sx, int(y) - 48))
        card = cards[i]
        if alpha < 255:
            card = card.copy()
            card.putalpha(card.getchannel("A").point(lambda p, a=alpha: p * a // 255))
        im.alpha_composite(card, (x, int(y)))

    cap_y = first_y + 5 * (height + gap) + (36 if tall else 28)
    if cap_y < layout.h - (220 if tall else 80):
        fade_slide_text(
            im,
            "Five tickets. One night.",
            font(FONT_SEM, 34 if tall else 28),
            (layout.w / 2, cap_y),
            WHITE,
            local,
            1.85,
            rise=12,
        )
    return im


_PILE: dict[str, list[tuple[Image.Image, int, int]]] = {}
_SCRIM: dict[str, Image.Image] = {}


def pile_and_scrim(layout: Layout) -> tuple[list[tuple[Image.Image, int, int]], Image.Image]:
    if layout.name in _PILE:
        return _PILE[layout.name], _SCRIM[layout.name]
    tall = layout.h > 1400
    x, _first_y, width, height, _gap = notice_geometry(layout)
    cards = make_notice(width, height)
    offsets = [(-18, -10, -7), (26, 16, 5), (-8, 8, -3), (18, -18, 6), (-22, 12, -5)]
    base_y = (layout.h * 0.22) if tall else 70
    placed: list[tuple[Image.Image, int, int]] = []
    for i, (dx, dy, ang) in enumerate(offsets):
        rot = cards[i].rotate(ang, expand=True, resample=Image.BICUBIC)
        rot.putalpha(rot.getchannel("A").point(lambda p: int(p * 0.55)))
        placed.append((rot, x + dx, int(base_y + i * (height * 0.62) + dy)))
    scrim = Image.new("RGBA", (layout.w, layout.h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    top = int(layout.h * (0.34 if tall else 0.28))
    bot = int(layout.h * (0.70 if tall else 0.78))
    sd.rectangle([0, top, layout.w, bot], fill=(7, 10, 18, 180))
    scrim = scrim.filter(ImageFilter.GaussianBlur(18))
    _PILE[layout.name] = placed
    _SCRIM[layout.name] = scrim
    return placed, scrim


def draw_overwhelm(local: float, layout: Layout) -> Image.Image:
    im = new_frame(layout)
    tall = layout.h > 1400
    placed, scrim = pile_and_scrim(layout)
    for rot, px, py in placed:
        im.alpha_composite(rot, (px, py))
    im = Image.alpha_composite(im, scrim)

    u = ease_out(local / 0.45)
    head = 78 if tall else 54
    sub = 32 if tall else 26
    cy = layout.h * (0.48 if tall else 0.50)
    lines = ["Every ticket", "lands on you."]
    for i, line in enumerate(lines):
        paste_text(
            im,
            line,
            font(FONT_BOLD, head),
            (layout.w / 2, cy - head * 0.7 + i * (head + 8) + (1 - u) * 20),
            WHITE,
            alpha=int(255 * u),
            anchor="mm",
        )
    paste_text(
        im,
        "You triage. You chase. You text a backup.",
        font(FONT_REG, sub),
        (layout.w / 2, cy + head * 1.15),
        MUTED,
        alpha=int(255 * smooth(clamp((local - 0.35) / 0.4))),
        anchor="mm",
    )
    return im


def make_path_card(width: int, height: int, index: str, title: str, body: str, accent: tuple[int, int, int]) -> Image.Image:
    img = rounded_card(width, height, 32, (18, 26, 46, 245), (255, 255, 255, 36), 2)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([18, 22, 26, height - 23], radius=4, fill=rgba(accent, 255))
    badge = 72 if height >= 200 else 58
    bx, by = 36, (height - badge) // 2
    d.ellipse([bx, by, bx + badge, by + badge], fill=rgba(accent, 255))
    paste_text(img, index, font(FONT_BOLD, 28 if height >= 200 else 22), (bx + badge / 2, by + badge / 2 - 1), (8, 12, 22), anchor="mm")
    tx = bx + badge + 28
    paste_text(img, title, font(FONT_BOLD, 36 if height >= 200 else 28), (tx, 36 if height >= 200 else 24), WHITE)
    # wrap body manually on " / " or by words if needed
    paste_text(img, body, font(FONT_REG, 26 if height >= 200 else 22), (tx, 92 if height >= 200 else 68), MUTED)
    return img


def draw_delegate(local: float, layout: Layout) -> Image.Image:
    im = new_frame(layout)
    tall = layout.h > 1400
    # Product line, wrapped so the full sentence stays on screen.
    if tall:
        value_lines = [
            (0.04, "TobinAI helps you manage", 54, WHITE),
            (0.16, "your maintenance coordination", 54, WHITE),
            (0.28, "autonomously", 54, CYAN),
        ]
        y0, gap, ai_size, ai_y = 340, 66, 40, 580
    else:
        value_lines = [
            (0.04, "TobinAI helps you manage", 40, WHITE),
            (0.16, "your maintenance coordination", 40, WHITE),
            (0.28, "autonomously", 40, CYAN),
        ]
        y0, gap, ai_size, ai_y = 136, 48, 30, 300
    for i, (delay, text, size, color) in enumerate(value_lines):
        fade_slide_text(
            im,
            text,
            font(FONT_BOLD, size),
            (layout.w / 2, y0 + i * gap),
            color,
            local,
            delay,
            rise=14,
        )
    fade_slide_text(
        im,
        "Powered by cutting-edge AI models",
        font(FONT_SEM, ai_size),
        (layout.w / 2, ai_y),
        CYAN,
        local,
        0.55,
        rise=12,
    )

    if tall:
        cw, ch = 920, 230
        y1, y2 = 760, 1030
    else:
        cw, ch = 940, 180
        y1, y2 = 400, 610
    x = (layout.w - cw) // 2

    cards = [
        (
            "01",
            "Your handyman",
            "Routes the ticket to your vendor.",
            (52, 211, 153),
            0.12,
            y1,
        ),
        (
            "02",
            "Or a new vendor",
            "Finds shops. Contacts them after you approve.",
            CYAN,
            0.48,
            y2,
        ),
    ]
    for index, title, body, accent, delay, y in cards:
        u = ease_out((local - delay) / 0.5)
        if u <= 0:
            continue
        card = make_path_card(cw, ch, index, title, body, accent)
        sh = shadow_for(cw, ch, 32)
        dy = int((1 - u) * 50)
        alpha = int(255 * u)
        if alpha < 255:
            card = card.copy()
            card.putalpha(card.getchannel("A").point(lambda p, a=alpha: p * a // 255))
            sh = sh.copy()
            sh.putalpha(sh.getchannel("A").point(lambda p, a=alpha: p * a // 255))
        im.alpha_composite(sh, (x - 48, y + dy - 48))
        im.alpha_composite(card, (x, y + dy))

    fade_slide_text(
        im,
        "Preferred vendors get the text. Strangers wait for your yes.",
        font(FONT_MED, 26 if tall else 22),
        (layout.w / 2, (y2 + ch + 70) if tall else (y2 + ch + 48)),
        MUTED,
        local,
        1.05,
        rise=10,
    )
    return im


def draw_cta(local: float, layout: Layout) -> Image.Image:
    im = new_frame(layout)
    tall = layout.h > 1400
    cy = layout.h * (0.42 if tall else 0.40)

    fade_slide_text(im, "TOBIN", font(FONT_BOLD, 28 if tall else 22), (layout.w / 2, cy - (120 if tall else 90)), CYAN, local, 0.0, rise=8)

    size = 68 if tall else 48
    fade_slide_text(
        im,
        "Sign up for a free trial",
        font(FONT_BOLD, size),
        (layout.w / 2, cy),
        WHITE,
        local,
        0.05,
        rise=16,
    )
    fade_slide_text(
        im,
        "Property management. Zero stress.",
        font(FONT_REG, 30 if tall else 24),
        (layout.w / 2, cy + size),
        MUTED,
        local,
        0.18,
        rise=10,
    )
    return im


# ~12s. Neighbors overlap ~0.3s for a crossfade.
# 0–3 spam, 3–6 tired, 6–10 delegate, 10–12 CTA.
SCENES = [
    (0.0, 3.25, draw_barrage),
    (2.95, 6.25, draw_hook),
    (5.95, 10.25, draw_delegate),
    (9.95, DURATION, draw_cta),
]


def compose(t: float, layout: Layout) -> Image.Image:
    t = clamp(t, 0, DURATION - 1e-6)
    active = [(a, b, fn) for a, b, fn in SCENES if a <= t <= b]
    if not active:
        # Hold whichever scene contains the nearest time.
        a, b, fn = min(SCENES, key=lambda s: min(abs(t - s[0]), abs(t - s[1])))
        return fn(clamp(t - a, 0, b - a), layout)
    if len(active) == 1:
        a, b, fn = active[0]
        return fn(t - a, layout)
    a0, b0, fn0 = active[0]
    a1, b1, fn1 = active[1]
    u = smooth((t - a1) / max(0.001, b0 - a1))
    im0 = fn0(t - a0, layout)
    im1 = fn1(t - a1, layout)
    return Image.blend(im0, im1, u)


def encode(layout: Layout, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{layout.w}x{layout.h}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    n = int(round(DURATION * FPS))
    assert proc.stdin is not None
    try:
        for i in range(n):
            frame = compose(i / FPS, layout).convert("RGB")
            proc.stdin.write(frame.tobytes())
            if i % 60 == 0:
                print(f"  {layout.name}: {i}/{n}", flush=True)
    finally:
        proc.stdin.close()
    err = proc.stderr.read().decode() if proc.stderr else ""
    code = proc.wait()
    if code != 0:
        sys.stderr.write(err[-4000:])
        raise SystemExit(f"ffmpeg failed for {layout.name} ({code})")
    print(f"wrote {dest}", flush=True)


def write_stills(directory: Path, layout: Layout) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    times = [1.4, 2.7, 4.6, 8.2, 11.2]
    for t in times:
        frame = compose(t, layout).convert("RGB")
        path = directory / f"{layout.name}-{t:.1f}.png"
        frame.save(path, optimize=True)
        print(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stills", type=Path, default=None, help="Write preview PNGs here and exit")
    parser.add_argument("--only", choices=["vertical", "square", "both"], default="both")
    args = parser.parse_args()
    layouts = []
    if args.only in ("vertical", "both"):
        layouts.append(VERTICAL)
    if args.only in ("square", "both"):
        layouts.append(SQUARE)
    if args.stills:
        for layout in layouts:
            write_stills(args.stills, layout)
        return
    for layout in layouts:
        encode(layout, OUT_DIR / layout.outfile)


if __name__ == "__main__":
    main()
