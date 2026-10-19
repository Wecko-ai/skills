#!/usr/bin/env python3
"""Animated karaoke captions -> transparent PNG frame sequence.
Spec-driven (see SKILL.md): chunks of [word, start, end, keyword]. Current
word pops on a white chip; keywords keep the chip after being spoken.
"""
import argparse
import json
import os
import shutil
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
HELV = "/System/Library/Fonts/HelveticaNeue.ttc"
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--frames-dir", required=True)
    p.add_argument("--dur", type=float, required=True)
    p.add_argument("--spec", required=True, help="JSON chunks spec")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--y", type=int, default=1365)
    p.add_argument("--y-late", type=int, default=0,
                   help="if >0, caption Y after --late-after")
    p.add_argument("--late-after", type=float, default=0.0)
    p.add_argument("--font-size", type=int, default=56)
    p.add_argument("--shift", type=float, default=0.20,
                   help="anticipate whisper lag (seconds)")
    p.add_argument("--font", default=HELV)
    p.add_argument("--font-index", type=int, default=1,
                   help="face index in the font file (1 = Bold in the macOS .ttc; use 0 for a single-face .ttf)")
    return p.parse_args()


A = parse()
CHUNKS = json.load(open(A.spec))


def font(size):
    return ImageFont.truetype(A.font, size, index=A.font_index)


def layout(words, f, scale_map, caption_y):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    space = d.textlength(" ", font=f)
    widths = [d.textlength(w[0], font=f) for w in words]
    # greedy wrap measured in pixels: the old single midpoint split let long
    # chunks overflow the 1080px frame
    MAXW = 920
    lines, cur, cur_w = [], [], 0.0
    for i, wpx in enumerate(widths):
        add = wpx if not cur else wpx + space
        if cur and cur_w + add > MAXW:
            lines.append(cur)
            cur, cur_w = [], 0.0
            add = wpx
        cur.append(i)
        cur_w += add
    if cur:
        lines.append(cur)
    asc, desc = f.getmetrics()
    lh = asc + desc + 30
    out = []
    y0 = caption_y - lh * len(lines) / 2
    for li, idxs in enumerate(lines):
        lw = sum(widths[i] for i in idxs) + space * (len(idxs) - 1)
        x = (W - lw) / 2
        for i in idxs:
            out.append((x, y0 + li * lh, i, widths[i], scale_map.get(i, 1.0)))
            x += widths[i] + space
    return out


def render(t):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t += A.shift  # whisper word timings lag the voice: anticipate
    chunk = next((c for c in CHUNKS if c["t0"] <= t < c["t1"]), None)
    if not chunk:
        return img
    words = chunk["words"]
    f = font(A.font_size)
    scale_map = {}
    for i, w in enumerate(words):
        t0, t1 = w[1], w[2]
        if t0 <= t < t1:
            k = min((t - t0) * A.fps / 5, 1.0)
            scale_map[i] = 1.3 - 0.3 * k
    cy = A.y_late if (A.y_late and t >= A.late_after) else A.y
    items = layout(words, f, scale_map, cy)
    d = ImageDraw.Draw(img)
    asc, desc = f.getmetrics()
    th = asc + desc
    for x, y, i, w, sc in items:
        text, t0, t1, kw = words[i]
        if t < t0 - 0.03:
            continue
        current = t0 <= t < t1
        if current or kw:
            pad_x, pad_y = int(16 * sc), int(6 * sc)
            fs = font(int(A.font_size * sc))
            w2 = d.textlength(text, font=fs)
            x2 = x + (w - w2) / 2
            a2, d2 = fs.getmetrics()
            d.rounded_rectangle([x2 - pad_x, y - pad_y, x2 + w2 + pad_x,
                                 y + a2 + d2 + pad_y], radius=16, fill=WHITE)
            d.text((x2, y), text, font=fs, fill=BLACK)
        else:
            for dx in (-3, 0, 3):
                for dy in (-3, 0, 3):
                    d.text((x + dx, y + dy), text, font=f,
                           fill=(0, 0, 0, 200))
            d.text((x, y), text, font=f, fill=WHITE)
    return img


def main():
    if os.path.exists(A.frames_dir):
        shutil.rmtree(A.frames_dir)
    os.makedirs(A.frames_dir)
    n = int(A.dur * A.fps)
    for i in range(n):
        render(i / A.fps).save(os.path.join(A.frames_dir, f"{i:04d}.png"))
    print("caption frames:", n, "->", A.frames_dir)


if __name__ == "__main__":
    main()
