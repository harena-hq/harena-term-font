#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Stabilise the Claude Code spinner across ttfautohint grid fitting.

The source outlines for `· ✢ ✳ ✶ ✻ ✽` share one vertical centre, but
`ttfautohint` can snap each shape to a different pixel phase. Measure a probe
hinted font against the unhinted source raster, then emit control-file deltas
that move every contour point of each frame by the same vertical amount.

The all-points shift preserves the shape that ttfautohint chose; it only changes
where that shape sits vertically. Deltas are quantised to ttfautohint's 1/8 px
resolution.

Usage:
    python3 scripts/spinner_hinting.py source.ttf probe-hinted.ttf \
        --control build/harena-spinner.ctrl
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path

import freetype
from fontTools.ttLib import TTFont

SPINNER = "·✢✳✶✻✽"
PPEMS = range(13, 19)
DELTA_STEP = 0.125
MAX_DELTA = 1.0
MAX_SPREAD = 0.20


def _bitmap_row_start(bitmap, row: int) -> int:
    """Return the buffer offset for a visual top-to-bottom bitmap row."""
    pitch = bitmap.pitch
    if pitch >= 0:
        return row * pitch
    return (bitmap.rows - 1 - row) * -pitch


def coverage_centroid(face: freetype.Face, ch: str, ppem: int,
                      hinted: bool) -> float:
    """Coverage-weighted vertical ink centre in pixel coordinates."""
    face.set_pixel_sizes(0, ppem)
    flags = freetype.FT_LOAD_RENDER
    if not hinted:
        flags |= freetype.FT_LOAD_NO_HINTING
    face.load_char(ch, flags)
    slot = face.glyph
    bitmap = slot.bitmap
    if not bitmap.rows or not bitmap.width:
        raise ValueError(f"empty render for U+{ord(ch):04X} at {ppem} ppem")

    buf = bytes(bitmap.buffer)
    total = weighted = 0.0
    for row in range(bitmap.rows):
        y = slot.bitmap_top - row - 0.5
        start = _bitmap_row_start(bitmap, row)
        for col in range(bitmap.width):
            cov = buf[start + col]
            total += cov
            weighted += cov * y
    if not total:
        raise ValueError(f"zero coverage for U+{ord(ch):04X} at {ppem} ppem")
    return weighted / total


def centroids(path: str, ppem: int, hinted: bool = True) -> dict[str, float]:
    face = freetype.Face(path)
    return {ch: coverage_centroid(face, ch, ppem, hinted) for ch in SPINNER}


def spread(values: dict[str, float]) -> float:
    return max(values.values()) - min(values.values())


def quantize_delta(value: float) -> float:
    """Round to ttfautohint's 1/8 px delta grid, ties away from zero."""
    steps = math.floor(abs(value) / DELTA_STEP + 0.5)
    q = math.copysign(steps * DELTA_STEP, value)
    if steps == 0:
        return 0.0
    if abs(q) > MAX_DELTA:
        raise ValueError(
            f"ttfautohint delta {q:+.3f}px exceeds "
            f"[-{MAX_DELTA:g}, {MAX_DELTA:g}]"
        )
    return q


def _point_ranges(path: str) -> dict[str, tuple[int, int]]:
    """Map spinner frame to (glyph id, contour-point count)."""
    font = TTFont(path, lazy=False)
    try:
        cmap = font.getBestCmap()
        glyf = font["glyf"]
        result = {}
        for ch in SPINNER:
            cp = ord(ch)
            name = cmap.get(cp)
            if name is None:
                raise ValueError(f"source font has no U+{cp:04X} {ch}")
            glyph = glyf[name]
            if glyph.isComposite():
                raise ValueError(
                    f"U+{cp:04X} {ch} is composite; all-point delta needs "
                    "component-aware point numbering"
                )
            coords, _end_pts, _flags = glyph.getCoordinates(glyf)
            if not coords:
                raise ValueError(f"U+{cp:04X} {ch} has no contour points")
            result[ch] = (font.getGlyphID(name), len(coords))
        return result
    finally:
        font.close()


def measure(source_path: str, probe_path: str):
    """Measure probe wobble and derive per-frame, per-ppem corrections."""
    plain_face = freetype.Face(source_path)
    probe_face = freetype.Face(probe_path)
    rows = []
    corrections: dict[str, dict[float, list[int]]] = {
        ch: defaultdict(list) for ch in SPINNER
    }

    for ppem in PPEMS:
        plain = {
            ch: coverage_centroid(plain_face, ch, ppem, hinted=False)
            for ch in SPINNER
        }
        hinted = {
            ch: coverage_centroid(probe_face, ch, ppem, hinted=True)
            for ch in SPINNER
        }
        target = sum(plain.values()) / len(plain)
        deltas = {ch: quantize_delta(target - hinted[ch]) for ch in SPINNER}
        for ch, delta in deltas.items():
            if delta:
                corrections[ch][delta].append(ppem)
        rows.append((ppem, plain, hinted, target, deltas))

    return rows, corrections


def control_text(source_path: str, corrections) -> str:
    """Render ttfautohint control instructions for measured corrections."""
    ranges = _point_ranges(source_path)
    out = [
        "# Generated by scripts/spinner_hinting.py; do not hand-edit.",
        "# Claude Code frames: · ✢ ✳ ✶ ✻ ✽",
        "# Every contour point moves together: preserve hinted shape,",
        "# correct only its vertical pixel phase.",
    ]
    for ch in SPINNER:
        gid, count = ranges[ch]
        for delta, ppems in sorted(corrections[ch].items()):
            sizes = ",".join(str(p) for p in ppems)
            out.append(
                f"{gid} touch 0-{count - 1} yshift {delta:+.3f} @ {sizes}"
                f"  # U+{ord(ch):04X} {ch}"
            )
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="unhinted pre-postbuild TTF")
    ap.add_argument("probe", help="same font after the normal ttfautohint pass")
    ap.add_argument("--control", required=True,
                    help="write generated ttfautohint control instructions here")
    args = ap.parse_args()

    rows, corrections = measure(args.source, args.probe)
    print("ppem  hinted-spread  unhinted-spread  corrections (px)")
    for ppem, plain, hinted, _target, deltas in rows:
        ds = " ".join(f"{ch}{delta:+.3f}" for ch, delta in deltas.items())
        print(f"{ppem:>4}  {spread(hinted):>13.3f}  "
              f"{spread(plain):>15.3f}  {ds}")

    Path(args.control).write_text(
        control_text(args.source, corrections), encoding="utf-8"
    )
    print(f"wrote {args.control}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
