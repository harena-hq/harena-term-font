#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Turn the merged faces into the artefacts that ship.

Four steps, in this order, because each depends on the one before:

  1. hint with ttfautohint, for Windows;
  2. re-stamp `head`, because ttfautohint writes its own `modified`;
  3. derive the WOFF2 from the hinted TTF, not the unhinted one;
  4. record SHA256SUMS over the result.

Step 4 lives here rather than in a script of its own on purpose: a manifest
maintained beside the thing it describes drifts from it. Written by the stage
that produces the bytes, it cannot.

The name says where this runs rather than what it does, deliberately. A name
that lists responsibilities goes stale the moment one is added, and this stage
is the likeliest in the pipeline to gain steps. "After build" cannot go stale.

The hinting, on why step 1 exists at all.

The CJK arrives here as outlines: glyphs are imported through a pen and scaled,
which drops the source's instructions -- and they would be wrong after scaling
anyway. So the built font carries Iosevka's hinting on the Latin and symbols and
nothing at all on the ~19000 CJK glyphs.

macOS does not care. CoreText largely ignores TrueType instructions and
positions subpixels itself, which is why the faces look right there. ClearType
does care: GDI and DirectWrite grid-fit from the instructions at small sizes, so
unhinted CJK at 13px on a 96 DPI display has stems landing off the pixel grid.
Sarasa hints its CJK, so shipping without this would be a visible regression on
the one platform not yet tested.

ttfautohint generates every instruction in the shipped font, including the
Latin's. Measured: feed it Iosevka's hinted `TTF/` build or its `TTF-Unhinted`
one and the output is byte-identical in `glyf`, `prep`, `fpgm` and `cvt` -- even
though the unhinted base carries no `prep`, `fpgm` or `cvt` at all. Nothing of
the base's own hinting survives, which is why the blue-zone options below move
the Latin as well as the hangul.

`build.py` reads the hinted `TTF/` build (CUSTOM; CUSTOM_UNHINTED is a fallback
for a tree without it), and that base's Latin bytecode happens to come out of
ttfautohint unchanged -- 'H' is 39 bytes either way, and `cvt` is byte-equal.
That coincidence is easy to misread as survival, and was. It is not a
coincidence at all: `TTF/` stamps `Version 34.8.0; ttfautohint (v1.8.4.16-eb64)`
into its name table where `TTF-Unhinted/` stamps only `Version 34.8.0`, so
Iosevka hinted with this same tool. A different build of it, which is why `fpgm`
is 3605 bytes there and 3596 here while `H` and `cvt` land identically.

The family suffix is deliberate: it lets the hinted and unhinted cuts be
installed side by side on Windows and switched in a terminal config, which is
the only way to judge whether ttfautohint's CJK hinting actually helps. Its CJK
support is basic stem snapping, not the hand-tuned kind, so it is not obviously
an improvement.

Usage:  python3 scripts/postbuild.py [--suffix " H"] [dist/*.ttf]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import os
import subprocess
import sys

from fontTools.ttLib import TTFont

from build import stamp

HINTER = "build/bin/ttfautohint"
OUT = "dist"

# Blue-zone rounding, and why the shipping build does not take the defaults.
#
# ttfautohint's defaults erase horizontal strokes the design draws solidly: at
# 15 and 16 ppem the three bars of ㅌ came out as two, so 텰 read as 뎔, and the
# top arc of ㅇ opened. Not every syllable -- 8 of the 588 with a ㅌ initial at
# 15 ppem and 9 at 16, and 티/타/토/투 are all clean. Only crowded combinations
# break, which is why a per-jamo spot check would not have found it, and not ㅌ
# alone: of the 39 the gate flags on 1.0.1 the initials are ㄹ 19, ㅌ 17, ㅇ 2,
# ㅋ 1. See docs/adr/0019.
#
# `-a` cannot fix it. That option selects stem *width* quantisation, and this is
# a stroke *position* failure: the bar's edges round onto each other and its
# height becomes zero. Moving `-a` to `s` masks the symptom at the cost of
# glyph-to-glyph uniformity, which is the trade ADR 0010 already weighed and
# settled -- so 0010's conclusion stands and these options sit beside it.
#
# `-x 20` extends x-height rounding-up through 20 ppem (default 14) and fixes
# 16; `-X 15` exempts 15 ppem from that rounding and fixes 15. Both are fitted
# constants, found by search over the option space and measured against every
# one of the 11172 syllables -- not derived. A rebuild at different weights
# could need refitting, which is why `verify.py` asserts the *property* they
# buy rather than the values themselves.
HINT_ARGS = ["-x", "20", "-X", "15"]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def out_name(src: str, suffix: str) -> str:
    """Fold the family suffix into the filename.

    The suffix alone is not enough: two cuts that differ only by family name
    still collide on disk when installed, which is exactly what happened.
    HarenaTermK-Regular.ttf + suffix " HS" -> HarenaTermKHS-Regular.ttf
    """
    base = os.path.basename(src)
    stem, _, style = base.rpartition("-")
    tag = suffix.replace(" ", "")
    return f"{stem}{tag}-{style}" if stem else base


def hint(src: str, dst: str, suffix: str, extra: list[str]) -> tuple[int, int]:
    """Hint src into dst. ttfautohint cannot write over its own input, so an
    in-place run goes through a temporary file and is moved into position."""
    before = os.path.getsize(src)
    inplace = os.path.abspath(src) == os.path.abspath(dst)
    tmp = dst + ".tmp" if inplace else dst
    cmd = [HINTER, "--no-info", "-f", "none"]
    if suffix:
        cmd += ["--family-suffix", suffix]
    cmd += extra + [src, tmp]
    subprocess.run(cmd, check=True, capture_output=True)
    if inplace:
        os.replace(tmp, dst)
    return before, os.path.getsize(dst)


def hinted_glyph_count(path: str) -> int:
    f = TTFont(path, lazy=True)
    g = f["glyf"]
    n = sum(1 for name in f.getGlyphOrder()
            if getattr(g[name], "program", None)
            and len(g[name].program.getBytecode()))
    f.close()
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="",
                    help="appended to the family and file name, so competing "
                         "cuts can be installed at once and switched in a "
                         "terminal config. Empty by default: the shipping font "
                         "is hinted in place.")
    ap.add_argument("--out", default=OUT,
                    help="output directory; the default overwrites dist in "
                         "place, since the unhinted intermediate has no use "
                         "of its own")
    ap.add_argument("--args", default="",
                    help="extra ttfautohint arguments, space separated, "
                         "appended after the shipping set "
                         f"{' '.join(HINT_ARGS)}. ttfautohint takes the last "
                         "occurrence of a repeated option -- measured, "
                         "`-x 20 -x 0` and `-x 0` produce identical glyf, "
                         "prep, fpgm and cvt -- so an experiment overrides by "
                         "restating the option, e.g. `-x 14` for the stock "
                         "value. It cannot clear -X: that needs an empty "
                         "argument and this string is split on whitespace. "
                         "-a picks the stem width mode for grayscale, GDI and "
                         "DirectWrite in that order: n natural, q quantized, "
                         "s strong. The default is qsq, so a modern Windows "
                         "terminal on DirectWrite gets the quantized mode and "
                         "stems are not snapped hard to the grid.")
    ap.add_argument("fonts", nargs="*", default=None)
    args = ap.parse_args()

    if not os.path.exists(HINTER):
        print(f"{HINTER} not found — pip install ttfautohint-py and re-create "
              f"the shim (see latin/README.md)", file=sys.stderr)
        return 1

    fonts = args.fonts or sorted(glob.glob("dist/*.ttf"))
    if not fonts:
        print("no fonts to hint", file=sys.stderr)
        return 1

    extra = HINT_ARGS + args.args.split()
    os.makedirs(args.out, exist_ok=True)
    print(f"{'face':34s} {'before':>9s} {'after':>9s} {'hinted glyphs':>15s}")
    print("-" * 72)
    for src in fonts:
        base = os.path.basename(src)
        dst = os.path.join(args.out, out_name(src, args.suffix))
        before = hinted_glyph_count(src)
        a, b = hint(src, dst, args.suffix, extra)
        after = hinted_glyph_count(dst)
        # ttfautohint writes its own head.modified, so the stamp build.py set
        # has to be restored here -- these are the shipped bytes, not dist/
        # before hinting. Written through a temporary because the font is read
        # lazily from the file being replaced.
        f = TTFont(dst, lazy=False)
        stamp(f)
        f.save(dst + ".tmp")
        f.flavor = "woff2"
        f.save(dst[:-4] + ".woff2")
        f.close()
        os.replace(dst + ".tmp", dst)
        print(f"{os.path.basename(dst):34s} {a/1e6:8.2f}M {b/1e6:8.2f}M "
              f"{before:6d} -> {after:<6d}")
    print(f"\nwrote {args.out}/  — family and file names carry {args.suffix!r}")

    # The reproducibility claim, written by the tool that produces the bytes so
    # it cannot go stale the way a hand-maintained manifest would. A clean-room
    # build from the pinned sources reproduces exactly these hashes; CI checks
    # that, and a release attaches this file.
    if args.out == OUT and not args.suffix:
        names = sorted(os.path.basename(p)
                       for p in glob.glob(os.path.join(OUT, "*.ttf"))
                       + glob.glob(os.path.join(OUT, "*.woff2")))
        with open("SHA256SUMS", "w") as fh:
            for n in names:
                fh.write(f"{sha256(os.path.join(OUT, n))}  {n}\n")
        print(f"wrote SHA256SUMS — {len(names)} artefacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
