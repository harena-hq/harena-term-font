#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Draw the README specimen: this font beside a reference face at equal cell width.

The whole project rests on one claim -- that hangul in a monospace terminal is
set far looser than the source designer drew it, and that it does not have to
be. That claim is visual. A paragraph about T = 0.1260 against 0.264 does not
land; two panels of the same Korean text at the same cell width do.

The reference face is not fetched by scripts/fetch_sources.sh, because it is not
a build input -- it is only a comparison. Pass it explicitly, with the labels the
committed image carries. They are arguments rather than defaults, so the whole
invocation belongs here: without it the next regeneration silently relabels the
reference panel.

    python3 scripts/specimen.py \
      --against /path/to/SarasaTermK-Regular.ttf \
      --against-label "Sarasa Term K" \
      --against-note "hangul gap/ink T = 0.264 — set by the grid, not by the designer"

The output is committed to the repository, so a reader does not need the
reference face to see the argument.
"""

from __future__ import annotations

import argparse
import os

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

CELL = 16
EM = CELL * 2
LINEH = round(EM * 1.25)
PAD = 26
BG = (16, 16, 18)
FG = (228, 228, 234)
DIM = (140, 140, 152)
FRAME = (92, 148, 200)
OK = (126, 211, 133)

OURS = "dist/HarenaTermK-Regular.ttf"
OUT = "docs/specimen.png"

# No box frame. Box-drawing tiles correctly in a terminal, where the renderer
# places each cell; PIL rounds every draw origin independently, so a frame here
# shows hairline seams that are an artefact of this script, not of the font.
# The ambiguous-width symbols are left out for a second reason: they are one
# cell in this font and two in the reference face, so a shared frame would end
# in a different column per panel and read as a defect. That difference is real
# and is documented as D8, but a specimen is the wrong place to argue it.
LINES = [
    "한글 자간은 원본 글꼴의 것을 그대로",
    "서울 부산 대구 인천 광주 대전 울산",
    "日本語入力 と 漢字混在 のテスト",
    "const 결과 = await run('빌드');  // 주석",
    "⣷⣯⣟⡿⢿⣻  ▁▂▃▄▅▆▇█  100%",
]


def draw_block(d, x, y, path):
    """Lay the sample out on a real cell grid, as a terminal would."""
    f = ImageFont.truetype(path, EM)
    font = TTFont(path, lazy=True)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    cy = y
    for line in LINES:
        cx = x
        base = cy + round(EM * 0.965)
        for ch in line:
            gn = cmap.get(ord(ch))
            cells = 2 if (gn and hmtx[gn][0] == upm) else 1
            d.text((cx + cells * CELL // 2, base), ch, font=f, fill=FG,
                   anchor="ms")
            cx += cells * CELL
        cy += LINEH
    font.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--against", metavar="TTF",
                    help="reference monospace CJK face to compare against")
    ap.add_argument("--against-label", default="reference")
    ap.add_argument("--against-note", default="")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    ui = ImageFont.truetype(OURS, 14)
    ui_s = ImageFont.truetype(OURS, 11)

    panels = []
    if args.against:
        panels.append((args.against_label, args.against, args.against_note, DIM))
    panels.append(("Harena Term K", OURS,
                   "hangul gap/ink T = 0.1260 — Pretendard's own spacing", OK))

    pw = 42 * CELL + 46
    W = PAD * 2 + pw * len(panels)
    H = PAD * 2 + LINEH * len(LINES) + 56
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for i, (name, path, note, col) in enumerate(panels):
        x = PAD + i * pw
        d.text((x, PAD), name, font=ui, fill=col)
        d.text((x, PAD + 18), note, font=ui_s, fill=DIM)
        draw_block(d, x, PAD + 42, path)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    img.save(args.out)
    print(f"wrote {args.out} {img.size}")


if __name__ == "__main__":
    main()
