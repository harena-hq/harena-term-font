#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Build Harena Term — Iosevka Term Latin + Pretendard JP CJK.

See PLAN.md for the decisions. In short:

  * the Latin is the fixed frame and the CJK is fitted into it, never the
    reverse. Its letterspacing is set parametrically through Iosevka's own
    `metricOverride`, which redraws at unchanged stroke weight -- scaling it
    instead would thicken the strokes past a box-drawing frame that cannot
    follow, since block elements must tile the cell exactly;
  * each CJK script is scaled so its own advance lands exactly on the two-cell
    box, which reproduces Pretendard's own letterspacing as an identity;
  * because the scales differ per script, each script is instanced at the
    `wght` that makes its post-scale stroke match the Latin stem.

The scale is derived from the source advance in font units rather than from the
em-relative figure, so the advance lands on the cell exactly and no rounding
error can accumulate across a terminal row.

Usage:  python3 scripts/build.py [--region K|J|both] [--weight 400,700]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import unicodedata as ud
from dataclasses import dataclass, replace

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.subset import Options as SubsetOptions, Subsetter
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.misc.timeTools import timestampSinceEpoch

IOS_DIR = "sources/cand/IosevkaTerm"
PJP = "sources/pjp/public/variable/PretendardJPVariable.ttf"
OUT = "dist"

VERSION = "1.000"
VENDOR = "HRNA"

# Reproducible builds. Two builds from identical inputs differed in exactly one
# table -- `head` -- and within it only `created`, `modified` and the
# `checkSumAdjustment` derived from them. Everything else, all 38478 glyphs
# included, was byte-identical. So the clock is the only nondeterminism, and
# stamping it makes the whole build verifiable by hash.
#
# `created` is inherited from the Iosevka base, which stamps its own build time,
# so it has to be overwritten rather than left alone. Bump this with VERSION.
# SOURCE_DATE_EPOCH overrides it, following the reproducible-builds convention.
SOURCE_DATE = int(os.environ.get("SOURCE_DATE_EPOCH", "1785801600"))  # 2026-08-04


def stamp(font: TTFont) -> None:
    """Pin `head` to SOURCE_DATE and stop fontTools re-stamping it on save."""
    ts = timestampSinceEpoch(SOURCE_DATE)
    font["head"].created = ts
    font["head"].modified = ts
    font.recalcTimestamp = False

# --- script groups -----------------------------------------------------------
# Each group names the ranges it owns, the source weight that cancels the
# scale's effect on stroke weight (see docs/adr/0003), and the native advance in
# source units that the scale is derived from.


@dataclass(frozen=True)
class Group:
    name: str
    ranges: tuple[tuple[int, int], ...]
    native_adv: int          # source units at upm 2048
    wght: dict[int, float]   # output weight -> source wght
    hscale: float | None = None   # effective horizontal em-scale; None = fill the cell
    yscale: float | None = None   # effective vertical em-scale; None = uniform


HANGUL = Group(
    name="hangul",
    ranges=((0xAC00, 0xD7A3), (0x3130, 0x318F), (0x1100, 0x11FF)),
    native_adv=1770,                       # 0.8643 em at upm 2048
    wght={400: 336.0, 700: 524.0},
    # Filling the two-cell box horizontally is the whole point, but a uniform
    # scale drags the height up with it: hangul ink reaches 0.994 em, which
    # leaves only 0.256 em of leading against Sarasa's 0.355 and stands 1.35x
    # the Latin cap against a 1.22 reference. Correcting the vertical alone
    # restores both and costs 11% of stroke contrast (v/h 1.179 -> 1.312).
    hscale=None,
    yscale=None,
)
HANKANA = Group(
    name="han/kana",
    ranges=(
        (0x3000, 0x303F),                  # CJK punctuation
        (0x3040, 0x30FF),                  # kana
        (0x3400, 0x4DBF),                  # ext A
        (0x4E00, 0x9FFF),                  # unified
        (0xF900, 0xFAFF),                  # compatibility ideographs
        (0x3200, 0x32FF),                  # enclosed CJK letters and months
        (0x3300, 0x33FF),                  # squared units and era names
        (0xFE30, 0xFE4F),                  # CJK compat forms
        (0xFF01, 0xFF60),                  # fullwidth forms
        (0xFFE0, 0xFFE6),                  # fullwidth signs
    ),
    native_adv=1920,                       # 0.9375 em at upm 2048
    wght={400: 399.0, 700: 613.0},
)
GROUPS = (HANGUL, HANKANA)

# Pretendard draws the CJK brackets for proportional setting, where `palt`
# would tighten the box around them -- and it ships no `palt` at all, so they
# are sparse even in its own prose. In a grid the box stays full width and the
# result is 0.221 of the cell against Sarasa's 0.315.
#
# The kana already come from M PLUS 1p by way of Pretendard, so taking the
# brackets from the same place is matching a lineage rather than grafting a
# foreign one. Measured, M PLUS is fuller than Pretendard *and* Sarasa.
#
# Scale: intended as Pretendard's own resize of M PLUS composed with this
# build's 1.0667, so a glyph taken straight from M PLUS lands where one that
# arrived through Pretendard does.
#
# Measured, that relationship is not a uniform scale and no single factor
# reproduces it: Pretendard's kana ink is 0.980 of M PLUS's in width but 0.952
# in height, because what it actually did was narrow the *box* by 6.25% and
# leave the drawing nearly its original width -- which is what tightened the
# kana from T 0.2605 to 0.2037. Matching height composes to 1.0152, matching
# width to 1.0455. The shipped 1.0211 sits near the height-matched value, and
# the glyphs it governs were validated on cell fill instead, where M PLUS beats
# both alternatives. See docs/LINEAGE.md.
MPLUS = "sources/mplus1p/MPLUS1p-{style}.ttf"
MPLUS_STYLE = {400: "Regular", 700: "Medium"}     # stroke lands within 5%
MPLUS_SCALE = 1.0211
BRACKETS = (0x300C, 0x300D, 0x300E, 0x300F, 0x3010, 0x3011, 0x3014, 0x3015,
            0x3018, 0x3019, 0x301A, 0x301B, 0xFF08, 0xFF09, 0xFF3B, 0xFF3D,
            0xFF5B, 0xFF5D)

# Five more full-width glyphs that have to come from M PLUS, for two reasons.
# Pretendard has no 〇 〒 〓 at all. It does have 〈 〉, but draws them for
# proportional setting at advance 698 against the cell's 1920, so the advance
# guard rejects them -- the same situation as the brackets above, and 〈 lands
# at 0.362 of the cell here against 「 at 0.391.
#
# 〒 is ordinary in Japanese addresses and 〇 in dates and lists, so their
# absence was a real hole, not a rounding error.
MPLUS_SYMBOLS = (0x3007, 0x3008, 0x3009, 0x3012, 0x3013)

# Halfwidth katakana. Pretendard has none, Iosevka has none, and they were
# never even attempted because the han/kana ranges stopped at U+FF60. M PLUS
# draws all 63 at advance 500 of its 1000 em -- genuinely half-width, not a
# full-width glyph to be squeezed -- so they import at one cell directly.
# Widest is ﾍ at 0.958 of the cell after the tuning below, against 0.990 for
# the full-width kana already shipping.
MPLUS_HALFWIDTH = tuple(range(0xFF61, 0xFFA0))

# Three fullwidth signs Pretendard does not draw. Same source, same tuning as
# the brackets: ￢ lands at 0.756 of the cell, ￣ is a top macron at 0.762 and
# ￤ is a bar at 0.076, all comfortably inside.
MPLUS_SIGNS = (0xFFE2, 0xFFE3, 0xFFE4)

# The enclosed and squared blocks, and the archaic compatibility jamo, come
# from Noto Sans KR -- which is Source Han Sans, the font Pretendard's own
# hangul and han derive from.
#
# Pretendard has 81 of these but draws every one *proportionally*, at 2280-3638
# units against the cell's 1920, because it is an Inter-based proportional face
# that re-spaced them for Latin-first setting. A CJK-native font draws them
# full-width: measured, all 206 sit at exactly one em in Noto, so they import
# with no compression at all.
#
# This is not a fourth letterform system. Measured against the shipped face at
# 96px, Noto matches our hangul as closely as our own source does (IoU 0.915
# against Pretendard's 0.916) and our han more closely still, while M PLUS 1p
# -- which we already graft brackets from -- sits at 0.680 on han. Taking these
# from Source Han is returning to the well our letterforms came from.
#
# One source for the whole family, on purpose. ㈱ ㈲ were briefly taken from
# M PLUS 1 Code, which has those two and not ㈹; measured, its enclosure is 1.3%
# wider with a 10% thinner bracket, so ㈹ beside them would have read as a
# different design. Noto draws all three identically (ink 0.938 x 0.912,
# bracket stroke 0.062), so M PLUS 1 Code is dropped as a source.
#
# Two transforms, each solved against the shipped face the way the M PLUS one
# was -- `wght` to match ink area, scale to match ink height, `dy` to match the
# optical centre:
#
#              wght        scale            dy     matched against
#   enclosed   440 / 640   0.9993 / 0.9992  +11    our han
#   jamo       480 / 700   1.0988 / 1.0779   -1    our hangul
#
# The jamo scale is larger because Noto sets hangul at 920 units of its 1000 em
# and the cell is 1000; normalising that is the identity of ADR 0002 again.
SOURCE_HAN = "sources/notosanskr/NotoSansKR[wght].ttf"
SH_HAN_WGHT = {400: 440.0, 700: 640.0}
SH_HAN_SCALE = {400: 0.9993, 700: 0.9992}
SH_HAN_DY = {400: 11, 700: 11}
SH_HAN_RANGES = ((0x3200, 0x33FF),)          # enclosed, circled, squared

SH_JAMO_WGHT = {400: 480.0, 700: 700.0}
SH_JAMO_SCALE = {400: 1.0988, 700: 1.0779}
SH_JAMO_DY = {400: -1, 700: -1}
SH_JAMO_RANGES = ((0x3165, 0x318E),)         # archaic compatibility jamo

# ☎ ☏ ♨ are deliberately not taken. The provider reserves them **one** cell,
# and no source here draws them for one -- Noto sets them full-width. Scaling a
# full-width design down by half is uniform rather than distorting, but it would
# leave them visibly smaller than Iosevka's own one-cell symbols beside them.

STYLE = {400: ("Regular", "IosevkaTermNerdFontMono-Regular.ttf"),
         700: ("Bold", "IosevkaTermNerdFontMono-Bold.ttf")}

CUSTOM = "sources/iosevka-src/dist/{plan}/TTF/{plan}-{style}.ttf"
CUSTOM_UNHINTED = "sources/iosevka-src/dist/{plan}/TTF-Unhinted/{plan}-{style}.ttf"

# A single uniform scale cannot satisfy three measurements at once: hangul
# letterspacing (T), hangul height against the Latin cap (ratio), and the leading
# left between rows. Four approaches were built and measured; `redraw` won and is
# what `ship` now is.
#
#            T      ratio   leading   cost
#  fill    0.129    1.35     0.256    hangul towers over the Latin, rows crowd
#  fit     0.137    1.22     0.357    stroke contrast 1.179 -> 1.312
#  conform 0.241    1.23     0.348    forfeits the spacing the project exists for
#  redraw  0.129    1.23     0.356    8% fewer rows; needs a from-source Latin
#
# Reference points: Sarasa T 0.264, ratio 1.218, leading 0.355.
VARIANTS = {
    # The shipping configuration, and the only one. Latin redrawn parametrically
    # at cap 808, shape 500 and sb 45; hangul x1.1571 and han/kana x1.0667 with
    # the weight compensation of D3.
    #
    # One entry, because one cut ships. The parameter search behind it is in
    # latin/README.md and ADR 0001. Two axes closed on measurement rather than
    # preference: sb 40 -> 50 shifts the widest letters' gap by 0.02 em, which
    # is 0.26px at 13px, and cap 808 -> 760 changed no pixel above a 32/255
    # threshold.
    "ship": dict(label="", latin="custom", plan="HarenaLatin",
                hscale={400: None, 700: 1.1362}, yscale=None,
                wght={400: 403.7, 700: 585.8},
                han_wght={400: 474.6, 700: 684.0}),
}


XTERM_WIDTHS = "build/xterm-widths.json"


def cell_widths() -> dict[int, int]:
    """Ground-truth cell width per codepoint, from the real xterm.js unicode11
    provider, at the version pinned in package.json.

    The provider decides how many cells a terminal reserves; if an advance
    disagrees the row shears. Driving the build from this table makes zero
    mismatches structural rather than lucky -- scripts/verify.py then re-derives
    the advances from the built binary and checks them against the same external
    table.
    """
    if not os.path.exists(XTERM_WIDTHS):
        os.makedirs("build", exist_ok=True)
        with open(XTERM_WIDTHS, "w") as fh:
            subprocess.run(["node", "scripts/xterm_widths.mjs"],
                           stdout=fh, check=True)
    data = json.load(open(XTERM_WIDTHS))
    data.pop("_version", None)
    out: dict[int, int] = {}
    for block in data.values():
        for w, cps in block["widths"].items():
            for cp in cps:
                out[cp] = int(w)
    return out


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ss05_map(font: TTFont) -> dict[str, str]:
    """Korean regional *hanja* forms reachable from ss05, and nothing else.

    xterm cannot reach an OpenType feature at runtime, so for the K build the
    substitution is baked into cmap instead of shipped as a lookup.

    Restricted to the han range on purpose. ss05 carries 608 substitutions of
    which only 534 are hanja; the rest re-cut punctuation, and for the CJK
    brackets the alternate is a `.hang` glyph -- a proportional form whose
    advance drops to 698-988 against the full-width 1920. Those exist for tight
    proportional setting and have no meaning in a grid: baking them left the
    opening brackets stranded at the far left of a full-width cell, where
    Pretendard and Sarasa both hang them to the right.
    """
    if "GSUB" not in font:
        return {}
    t = font["GSUB"].table
    lookups: set[int] = set()
    for fr in t.FeatureList.FeatureRecord:
        if fr.FeatureTag == "ss05":
            lookups.update(fr.Feature.LookupListIndex)
    cmap = font.getBestCmap()
    han = {cmap[cp] for cp in cmap
           if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF}
    out: dict[str, str] = {}
    for li in lookups:
        for st in t.LookupList.Lookup[li].SubTable:
            mapping = getattr(st, "mapping", None)
            if mapping:
                out.update({k: v for k, v in mapping.items() if k in han})
    return out


def instance(wght: float) -> TTFont:
    f = TTFont(PJP)
    return instantiateVariableFont(f, {"wght": wght}, inplace=True,
                                   updateFontNames=False)


def set_name(font: TTFont, nid: int, value: str) -> None:
    font["name"].setName(value, nid, 3, 1, 0x409)
    font["name"].setName(value, nid, 1, 0, 0)


def trim_base(base: TTFont) -> int:
    """Drop the glyphs a terminal can never reach.

    Iosevka ships 52823 glyphs but only 17827 are in cmap; the other 34996 are
    cv01-cv99 / ss01-ss20 alternates reachable only through OpenType features.
    xterm.js builds ctx.font from a plain CSS shorthand with no
    font-feature-settings, so those features are unreachable at runtime for
    exactly the same reason ss05 is -- and 52823 + ~19000 CJK would overflow
    the uint16 glyph count anyway.
    """
    before = base["maxp"].numGlyphs
    opts = SubsetOptions()
    opts.layout_features = ["ccmp"]     # keep mark composition, drop the rest
    opts.glyph_names = False
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.drop_tables += ["GPOS"]
    opts.name_IDs = ["*"]
    opts.name_languages = ["*"]
    sub = Subsetter(options=opts)
    sub.populate(unicodes=sorted(base.getBestCmap()))
    sub.subset(base)
    return before - base["maxp"].numGlyphs


def modern_jamo() -> dict[int, str]:
    """Conjoining jamo -> the Unicode name suffix its compatibility form shares.

    Derived from decomposing the syllable block rather than hand-listed, so it
    is exactly the 19 + 21 + 27 that modern Korean uses. Archaic jamo are
    deliberately excluded: Pretendard has no glyph for them, and registering a
    blank would turn a visible fallback into silent data loss.
    """
    out: dict[int, str] = {}
    seq = ([ud.normalize("NFD", chr(0xAC00 + l * 588))[0] for l in range(19)]
           + [ud.normalize("NFD", chr(0xAC00 + v * 28))[1] for v in range(21)]
           + [ud.normalize("NFD", chr(0xAC00 + t))[2] for t in range(1, 28)])
    for ch in seq:
        n = ud.name(ch)
        for prefix in ("HANGUL CHOSEONG ", "HANGUL JUNGSEONG ",
                       "HANGUL JONGSEONG "):
            n = n.replace(prefix, "")
        out[ord(ch)] = n
    return out


def add_jamo(base: TTFont, src: TTFont, t: float, ty: float,
             widths: dict[int, int],
             latin_adv: int, glyf, hmtx, existing: set[str],
             new_names: list[str]) -> int:
    """Register conjoining jamo so an NFD syllable stays in this font.

    macOS filenames are NFD and agent output carries them through verbatim, so
    a decomposed 한 arrives as U+1112 U+1161 U+11AB. HarfBuzz's Hangul shaper
    would compose that onto the precomposed syllable this font already has --
    but Chromium picks the font by cmap coverage *before* shaping, so a missing
    U+1112 hands the whole run to a fallback and the composition never runs.
    Registering the codepoints is what keeps the run here; the outlines below
    are only ever drawn for an isolated jamo.

    Widths follow the shaping model and the provider agrees: the leading
    consonant carries the advance (2 cells), the vowel and trailing forms are
    zero-advance.
    """
    src_cmap = src.getBestCmap()
    gs = src.getGlyphSet()
    compat = {}
    for cp in range(0x3130, 0x3190):
        if cp in src_cmap:
            try:
                compat[ud.name(chr(cp)).replace("HANGUL LETTER ", "")] = cp
            except ValueError:
                pass

    added = 0
    for cp, key in modern_jamo().items():
        source_cp = compat.get(key)
        if source_cp is None:
            continue
        cells = widths.get(cp)
        if cells is None:
            continue
        new = f"jamo{cp:04X}"
        if new in existing:
            continue
        rec = DecomposingRecordingPen(gs)
        gs[src_cmap[source_cp]].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, (t, 0, 0, ty, 0, 0)))
        gl = pen.glyph()
        glyf[new] = gl
        gl.recalcBounds(glyf)
        hmtx[new] = (cells * latin_adv,
                     gl.xMin if gl.numberOfContours else 0)
        new_names.append(new)
        existing.add(new)
        added += 1
        for table in base["cmap"].tables:
            if table.isUnicode():
                table.cmap[cp] = new

    # The two fillers stand for an absent element in a well-formed jamo
    # sequence and are supposed to be invisible, so a blank is correct here
    # rather than a loss.
    for cp in (0x115F, 0x1160):
        cells = widths.get(cp)
        if cells is None:
            continue
        new = f"jamo{cp:04X}"
        if new in existing:
            continue
        glyf[new] = TTGlyphPen(None).glyph()
        hmtx[new] = (cells * latin_adv, 0)
        new_names.append(new)
        existing.add(new)
        added += 1
        for table in base["cmap"].tables:
            if table.isUnicode():
                table.cmap[cp] = new
    return added


def add_jamo_ccmp(base: TTFont) -> int:
    """Compose conjoining jamo into the precomposed syllable, inside the font.

    add_jamo() keeps an NFD run in this face. It does not make the run
    *readable*, and HarfBuzz hid the difference: its Hangul shaper normalises
    the buffer before any lookup runs, so U+1112 U+1161 U+11AB reached the font
    already composed and every gate passed. CoreText has no Hangul shaper -- it
    composes only what the font composes, which is how Apple's own Korean faces
    do it, through an AAT `morx` state machine. With neither, macOS drew the
    three jamo on top of one another, since the width model here gives the lead
    the whole two-cell advance and leaves the vowel and tail at zero. Every
    Korean filename on macOS is NFD, so this was every Korean filename.

    So the composition is built here, as `ccmp` ligatures, in the two stages
    Unicode's own algorithm uses: L+V onto the LV syllable, then LV+T onto LVT.
    11172 rules, which is every modern syllable, and the intermediate LV is a
    real glyph this font already has. Order is by lookup index, not feature
    order, so the two are appended in that sequence.

    Registered under `hang` as well as the inherited DFLT: an engine that finds
    the run's own script in the font may never consult the default.
    """
    from fontTools.otlLib.builder import (buildLigatureSubstSubtable,
                                          buildLookup)
    from fontTools.ttLib.tables import otTables as ot

    cmap = base.getBestCmap()
    L = [cmap.get(0x1100 + i) for i in range(19)]
    V = [cmap.get(0x1161 + i) for i in range(21)]
    T = [cmap.get(0x11A8 + i) for i in range(27)]
    if not (all(L) and all(V) and all(T)):
        return 0

    lv_map: dict[tuple[str, ...], str] = {}
    lvt_map: dict[tuple[str, ...], str] = {}
    for li in range(19):
        for vi in range(21):
            lv = cmap[0xAC00 + (li * 21 + vi) * 28]
            lv_map[(L[li], V[vi])] = lv
            for ti in range(27):
                lvt_map[(lv, T[ti])] = cmap[0xAC00 + (li * 21 + vi) * 28 + ti + 1]

    gsub = base["GSUB"].table
    lookups = gsub.LookupList.Lookup
    first = len(lookups)
    for mapping in (lv_map, lvt_map):
        lookups.append(buildLookup([buildLigatureSubstSubtable(mapping)]))
    gsub.LookupList.LookupCount = len(lookups)
    new_idx = list(range(first, len(lookups)))

    # Attached to the ccmp records already present rather than to a new one:
    # the FeatureList is ordered by tag and every LangSys refers to features by
    # index, so inserting one would renumber references across the table.
    ccmp = [i for i, fr in enumerate(gsub.FeatureList.FeatureRecord)
            if fr.FeatureTag == "ccmp"]
    assert ccmp, "base font has no ccmp feature to extend"
    for i in ccmp:
        feat = gsub.FeatureList.FeatureRecord[i].Feature
        feat.LookupListIndex = feat.LookupListIndex + new_idx
        feat.LookupCount = len(feat.LookupListIndex)

    if not any(r.ScriptTag == "hang" for r in gsub.ScriptList.ScriptRecord):
        rec = ot.ScriptRecord()
        rec.ScriptTag = "hang"
        rec.Script = ot.Script()
        rec.Script.DefaultLangSys = ot.DefaultLangSys()
        rec.Script.DefaultLangSys.LookupOrder = None
        rec.Script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
        rec.Script.DefaultLangSys.FeatureIndex = ccmp
        rec.Script.DefaultLangSys.FeatureCount = len(ccmp)
        rec.Script.LangSysRecord = []
        rec.Script.LangSysCount = 0
        gsub.ScriptList.ScriptRecord.append(rec)
        # Scripts are found by tag, so re-sorting costs nothing and keeps the
        # table conformant.
        gsub.ScriptList.ScriptRecord.sort(key=lambda r: r.ScriptTag)
        gsub.ScriptList.ScriptCount = len(gsub.ScriptList.ScriptRecord)

    return len(lv_map) + len(lvt_map)


def declare_scripts(base: TTFont) -> tuple[int, int]:
    """Recompute the OS/2 script declarations from the merged cmap.

    OS/2 carries two claims about what a font can set: `ulUnicodeRange*` and
    `ulCodePageRange*`. They are inherited from the base here, and the base is
    Iosevka, which has no CJK -- so the merged font shipped declaring **no CJK
    support at all** while containing 19000 CJK glyphs.

    That is not cosmetic. Word decides whether a font may serve East Asian text
    from these bits, so it refused to use this face for the hangul run and fell
    back, while spaces and Latin stayed. Sarasa declares 949 and the CJK ranges;
    we declared 1252 and nothing else.

    Chinese is pruned back out. fontTools sets 950 because Big5 shares much of
    its han with JIS and KS, but measured coverage is 46.9% of cp950 and 36.2%
    of cp936 against 98.9% of cp949 and 87.5% of cp932. Chinese is an explicit
    non-goal (ADR 0005), and declaring a codepage invites the OS to select this
    face for text it cannot set.
    """
    os2 = base["OS/2"]
    os2.recalcUnicodeRanges(base, pruneOnly=False)
    os2.recalcCodePageRanges(base, pruneOnly=False)
    for bit in (18, 20):        # 936 Chinese Simplified, 950 Chinese Traditional
        os2.ulCodePageRange1 &= ~(1 << bit)
    return os2.ulUnicodeRange1, os2.ulCodePageRange1


def graft_mplus(base: TTFont, weight: int, latin_adv: int, glyf, hmtx,
                existing: set[str], new_names: list[str],
                codepoints, cells: int = 2, path: str | None = None,
                scale: float | None = None, dy: int = 0,
                wght: float | None = None,
                widths: dict[int, int] | None = None,
                tag: str = "mp") -> int:
    """Import glyphs from an M PLUS face at a tuning that matches the CJK here.

    Defaults to M PLUS 1p and `MPLUS_SCALE`. `path`, `scale`, `dy` and `wght`
    override that for M PLUS 1 Code, which is a different font and needs its
    own solved transform -- see `MPLUS_CODE_*`.

    Used for four sets:

      * the eighteen brackets, where M PLUS is measurably fuller than
        Pretendard -- which draws them for proportional setting and ships no
        `palt` to tighten the box, so they sit at 0.221 of the cell against
        Sarasa's 0.315;
      * 〇 〒 〓 〈 〉, which Pretendard either lacks outright or draws at a
        proportional advance the grid rejects;
      * the 63 halfwidth katakana, at one cell.

    The scale is `MPLUS_SCALE`, which is Pretendard's own 0.9572 resize of M
    PLUS composed with this build's 1.0667 for han and kana. So a glyph taken
    straight from M PLUS lands at the same size as one that reached us through
    Pretendard, and the two sit together on a line. The advance is then forced
    onto the cell rather than scaled, exactly as elsewhere.
    """
    if path is None:
        path = MPLUS.format(style=MPLUS_STYLE[weight])
    if not os.path.exists(path):
        return 0
    src = TTFont(path)
    if "fvar" in src and wght is not None:
        src = instantiateVariableFont(src, {"wght": wght}, inplace=False)
    src_cmap, gs = src.getBestCmap(), src.getGlyphSet()
    t = (MPLUS_SCALE if scale is None else scale) \
        * base["head"].unitsPerEm / src["head"].unitsPerEm
    cell2 = latin_adv * cells
    n = 0
    for cp in codepoints:
        gname = src_cmap.get(cp)
        if gname is None:
            continue
        # never assume the cell count: the provider decides, and ☎ ☏ ♨ are one
        # cell where every source draws them full-width
        if widths is not None and widths.get(cp) != cells:
            continue
        rec = DecomposingRecordingPen(gs)
        gs[gname].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, (t, 0, 0, t, 0, dy)))
        gl = pen.glyph()
        new = f"{tag}{cp:04X}"
        glyf[new] = gl
        gl.recalcBounds(glyf)
        hmtx[new] = (cell2, gl.xMin if gl.numberOfContours else 0)
        if new not in existing:
            new_names.append(new)
            existing.add(new)
        for table in base["cmap"].tables:
            if table.isUnicode() and (table.format != 4 or cp <= 0xFFFF):
                table.cmap[cp] = new
        n += 1
    src.close()
    return n


def enforce_grid(base: TTFont, widths: dict[int, int], latin_adv: int) -> list[str]:
    """Make every advance agree with the provider's cell count.

    Iosevka ships 23 codepoints that disagree: eight zero-width formatting
    characters drawn a full cell wide (ZWSP, ZWJ, the invisible operators) and
    fifteen Emoji_Presentation symbols drawn one cell where Unicode 9+ and the
    provider both say two. Neither is introduced by the merge, but both shear a
    row when they appear -- ZWJ turns up in emoji sequences and the round and
    lightning symbols turn up in CLI status output.

    Generic rather than a fixed list, so an upstream bump is corrected too.
    """
    glyf, hmtx, cmap = base["glyf"], base["hmtx"], base.getBestCmap()
    fixed = []
    for cp, cells in widths.items():
        gname = cmap.get(cp)
        if gname is None:
            continue
        want, got = cells * latin_adv, hmtx[gname][0]
        if want == got:
            continue
        if want == 0:
            pen = TTGlyphPen(None)
            glyf[gname] = pen.glyph()
            hmtx[gname] = (0, 0)
            fixed.append(f"U+{cp:04X} -> zero width")
        elif want > got:
            # keep the drawing untouched and centre it in the wider cell
            rec = DecomposingRecordingPen(base.getGlyphSet())
            glyf[gname].draw(rec, glyf)
            pen = TTGlyphPen(None)
            rec.replay(TransformPen(pen, (1, 0, 0, 1, (want - got) / 2, 0)))
            gl = pen.glyph()
            glyf[gname] = gl
            gl.recalcBounds(glyf)
            hmtx[gname] = (want, gl.xMin if gl.numberOfContours else 0)
            fixed.append(f"U+{cp:04X} -> {cells} cells, centred")
        else:
            fixed.append(f"U+{cp:04X} UNHANDLED want {want} got {got}")

    # Condense anything whose ink is strictly wider than its cell. A heavier
    # weight widens the ink, and instancing Bold han/kana at wght 684 pushed
    # the fullwidth Latin past the edge -- U+FF37 reaches 1.027, which overlaps
    # its neighbour. Glyphs that sit exactly on the edge are left alone: the
    # fullwidth low line U+FF3F is 1.0000 in the source too, because a run of
    # them has to join up, the same reason box drawing fills its cell.
    #
    # Only the glyphs this build creates. Iosevka ships 1328 cmap-reachable
    # glyphs wider than their advance -- 1023 Nerd Font icons, and long arrows
    # at up to 1.87x that are drawn long on purpose, since the neighbouring cell
    # is normally blank. That is the Latin base's design and D1 takes it
    # untouched. Condensing them changed the symbol set for no correctness gain
    # and, because squashing a component moves the bounds of every composite
    # built on it, made the outcome depend on dictionary order and let the K and
    # J cuts drift apart in glyphs neither build had any reason to differ in.
    #
    # The overflow this exists for is ours: instancing Bold han/kana at wght 684
    # widens the ink, and U+FF37 reached 1.027.
    ours = tuple(n for n in glyf.keys() if n.startswith(("cjk", "jamo", "mp", "sh")))
    for gname in ours:
        gl = glyf[gname]
        if not gl.numberOfContours:
            continue
        adv = hmtx[gname][0]
        if adv <= 0:
            continue
        gl.recalcBounds(glyf)
        ink = gl.xMax - gl.xMin
        if ink <= adv:
            continue
        k = (adv * 0.98) / ink
        rec = DecomposingRecordingPen(base.getGlyphSet())
        gl.draw(rec, glyf)
        pen = TTGlyphPen(None)
        # condense about the cell centre so the glyph stays centred
        cx = adv / 2
        rec.replay(TransformPen(pen, (k, 0, 0, 1, cx * (1 - k), 0)))
        new_gl = pen.glyph()
        glyf[gname] = new_gl
        new_gl.recalcBounds(glyf)
        hmtx[gname] = (adv, new_gl.xMin)
        fixed.append(f"{gname} condensed x{k:.3f} (ink {ink}/{adv})")
    return fixed


def graft_symbols(base: TTFont, donor_path: str, glyf, hmtx,
                  existing: set[str], new_names: list[str]) -> int:
    """Copy the Nerd Fonts symbol set onto a from-source Latin.

    Iosevka built from source carries its own box drawing, block, geometric,
    arrows and Braille, but only 22 Powerline glyphs and none of the icon set —
    those are added by the Nerd Fonts patcher, which is not part of the Iosevka
    build. The symbols are half-width and drawn to fill the cell rather than to
    the cap height, so they transfer unchanged.
    """
    donor = TTFont(donor_path)
    dcmap, dgs, dhmtx = donor.getBestCmap(), donor.getGlyphSet(), donor["hmtx"]
    bcmap = base.getBestCmap()
    added = 0
    for cp, gname in sorted(dcmap.items()):
        if cp in bcmap:
            continue
        new = f"nf{cp:04X}"
        if new in existing:
            continue
        rec = DecomposingRecordingPen(dgs)
        dgs[gname].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(pen)
        gl = pen.glyph()
        glyf[new] = gl
        gl.recalcBounds(glyf)
        hmtx[new] = (dhmtx[gname][0], gl.xMin if gl.numberOfContours else 0)
        new_names.append(new)
        existing.add(new)
        added += 1
        for table in base["cmap"].tables:
            if table.isUnicode() and (table.format != 4 or cp <= 0xFFFF):
                table.cmap[cp] = new
    donor.close()
    ensure_full_cmap(base)
    return added


def ensure_full_cmap(base: TTFont) -> None:
    """Give the font a format 12 subtable if anything sits outside the BMP.

    Nerd Fonts v3 places the Material Design icons at U+F0001-F1AF0, and a
    from-source Iosevka ships only a format 4 subtable, which cannot address
    them. Rebuilt from the union of what is already mapped so nothing is lost.
    """
    merged: dict[int, str] = {}
    for t in base["cmap"].tables:
        if t.isUnicode():
            merged.update(t.cmap)
    if not any(cp > 0xFFFF for cp in merged):
        return
    bmp = {cp: g for cp, g in merged.items() if cp <= 0xFFFF}
    keep = [t for t in base["cmap"].tables if not t.isUnicode()]
    for fmt, plat, enc in ((4, 3, 1), (12, 3, 10), (4, 0, 3), (12, 0, 4)):
        sub = CmapSubtable.newSubtable(fmt)
        sub.platformID, sub.platEncID, sub.language = plat, enc, 0
        sub.cmap = dict(bmp if fmt == 4 else merged)
        keep.append(sub)
    base["cmap"].tables = keep


def build_one(weight: int, region: str, variant: str, report: dict) -> str:
    v = VARIANTS[variant]
    style, base_file = STYLE[weight]
    if v["latin"] == "custom":
        base_path = CUSTOM.format(plan=v["plan"], style=style)
        if not os.path.exists(base_path):
            base_path = CUSTOM_UNHINTED.format(plan=v["plan"], style=style)
    else:
        base_path = os.path.join(IOS_DIR, base_file)
    base = TTFont(base_path)
    trim_base(base)
    upm = base["head"].unitsPerEm
    latin_adv = base["hmtx"]["H"][0]
    cell2 = latin_adv * 2
    assert upm == 1000 and latin_adv == 500, (upm, latin_adv)

    glyf = base["glyf"]
    hmtx = base["hmtx"]
    # copy: getGlyphOrder() hands back the list glyf itself appends to
    order = list(base.getGlyphOrder())
    existing = set(order)
    new_names: list[str] = []

    added = {g.name: 0 for g in GROUPS}
    skipped: list[tuple[int, str]] = []
    widths = cell_widths()

    if v["latin"] == "custom":
        added["nerd"] = graft_symbols(
            base, os.path.join(IOS_DIR, base_file), glyf, hmtx,
            existing, new_names)

    for group in GROUPS:
        is_hangul = group is HANGUL
        if is_hangul:
            hs = v["hscale"]
            if isinstance(hs, dict):
                hs = hs.get(weight)
            group = replace(group, hscale=hs, yscale=v["yscale"],
                            wght=v["wght"])
        elif v.get("han_wght"):
            group = replace(group, wght=v["han_wght"])
        src = instance(group.wght[weight])
        src_cmap = src.getBestCmap()
        gs = src.getGlyphSet()
        src_hmtx = src["hmtx"]
        alt = ss05_map(src) if region == "K" else {}
        # exact, unit-derived: the advance lands on the cell with no residue
        src_upm = src["head"].unitsPerEm
        t = (cell2 / group.native_adv if group.hscale is None
             else group.hscale * upm / src_upm)
        # t already carries the horizontal em-scale (cell2 / native_adv, which
        # is 1.157x for hangul). yscale is stated as the *effective* vertical
        # em-scale, so it converts through the upm ratio rather than through t.
        ty = t if group.yscale is None else group.yscale * upm / src_upm

        for lo, hi in group.ranges:
            for cp in range(lo, hi + 1):
                gname = src_cmap.get(cp)
                if gname is None:
                    continue
                # the provider is the authority on how many cells this takes
                cells = widths.get(cp)
                if cells is None:
                    skipped.append((cp, "not in width table"))
                    continue
                if cells == 1:
                    # half-width: the Latin base already draws these on its own
                    # optical grid, so importing a CJK-proportioned glyph here
                    # would both shear and clash
                    skipped.append((cp, "half-width, left to the Latin base"))
                    continue
                target_adv = cells * latin_adv
                # substitute first, then validate: an alternate can carry a
                # different advance from the glyph it replaces, and scaling it
                # by the group's factor would misplace it in the cell
                gname = alt.get(gname, gname)
                adv = src_hmtx[gname][0]
                if cells == 2 and adv != group.native_adv:
                    skipped.append((cp, f"width 2 but src adv {adv}"))
                    continue

                new = f"cjk{cp:04X}"
                if new in existing:
                    continue
                # decompose: composites would otherwise reference source
                # glyph names that do not exist in the output
                rec = DecomposingRecordingPen(gs)
                gs[gname].draw(rec)
                pen = TTGlyphPen(None)
                rec.replay(TransformPen(pen, (t, 0, 0, ty, 0, 0)))
                gl = pen.glyph()
                glyf[new] = gl
                gl.recalcBounds(glyf)
                lsb = gl.xMin if gl.numberOfContours else 0
                hmtx[new] = (target_adv, lsb)
                new_names.append(new)
                existing.add(new)
                added[group.name] += 1

                for table in base["cmap"].tables:
                    if table.isUnicode():
                        table.cmap[cp] = new
        if is_hangul:
            added["jamo"] = add_jamo(base, src, t, ty, widths, latin_adv,
                                     glyf, hmtx, existing, new_names)
        src.close()

    added["brackets"] = graft_mplus(base, weight, latin_adv, glyf, hmtx,
                                    existing, new_names,
                                    BRACKETS + MPLUS_SYMBOLS + MPLUS_SIGNS,
                                    cells=2)
    added["halfwidth"] = graft_mplus(base, weight, latin_adv, glyf, hmtx,
                                     existing, new_names,
                                     MPLUS_HALFWIDTH, cells=1)
    def _expand(ranges):
        return tuple(cp for lo, hi in ranges for cp in range(lo, hi + 1))

    added["enclosed"] = graft_mplus(base, weight, latin_adv, glyf, hmtx,
                                    existing, new_names,
                                    _expand(SH_HAN_RANGES), cells=2,
                                    path=SOURCE_HAN, tag="sh",
                                    scale=SH_HAN_SCALE[weight],
                                    dy=SH_HAN_DY[weight],
                                    wght=SH_HAN_WGHT[weight], widths=widths)
    added["archaic jamo"] = graft_mplus(base, weight, latin_adv, glyf, hmtx,
                                        existing, new_names,
                                        _expand(SH_JAMO_RANGES), cells=2,
                                        path=SOURCE_HAN, tag="sh",
                                        scale=SH_JAMO_SCALE[weight],
                                        dy=SH_JAMO_DY[weight],
                                        wght=SH_JAMO_WGHT[weight],
                                        widths=widths)

    grid_fixes = enforce_grid(base, widths, latin_adv)
    added["ccmp"] = add_jamo_ccmp(base)
    declare_scripts(base)

    final_order = order + new_names
    base.setGlyphOrder(final_order)
    glyf.glyphOrder = final_order
    if hasattr(base, "_reverseGlyphOrderDict"):
        del base._reverseGlyphOrderDict
    base["maxp"].numGlyphs = len(final_order)
    assert len(glyf.glyphs) == len(final_order), (len(glyf.glyphs), len(final_order))

    # --- naming ---------------------------------------------------------
    # Built from nothing rather than patched over the base. Setting only the
    # IDs we care about lets the base's own records through: nameID 21, the WWS
    # family, keeps the Iosevka build plan's internal name, and macOS and
    # Windows both group faces by nameID 21 when it is present -- so all four
    # faces read as one family to the OS and Regular/Bold stop pairing.
    # nameID 8, 9 and 10 would carry Iosevka's author and description too.
    # See docs/adr/0009-the-name-table-is-rebuilt-never-patched.md.
    family = f"Harena Term {region}{v['label']}"
    ps = f"HarenaTerm{region}{v['label'].replace(' ', '')}-{style}"
    names = {
        0: ("Latin, symbols, box drawing, block elements, geometric shapes, "
            "arrows, Braille and Powerline: Copyright (c) 2015-2023 Renzhi Li "
            "(Iosevka), OFL-1.1. Hangul, han and kana: Copyright (c) 2021 "
            "Kil Hyung-jin (Pretendard JP), OFL-1.1, itself deriving hangul and "
            "han from Noto Sans CJK / Source Han Sans and kana from M PLUS 1p. "
            "CJK brackets: Copyright 2016 The M+ Project Authors (M PLUS 1p), "
            "OFL-1.1. Nerd Fonts symbols: see THIRD_PARTY_NOTICES.md."),
        1: family,
        2: style,
        3: f"{VERSION};{VENDOR};{ps}",
        4: f"{family} {style}",
        5: f"Version {VERSION}",
        6: ps,
        7: ("Iosevka is a trademark of Renzhi Li. Pretendard is a trademark of "
            "Kil Hyung-jin. Inter is a trademark of rsms. Source is a trademark "
            "of Adobe in the United States and/or other countries."),
        8: "Harena",
        9: ("Renzhi Li (Latin); Kil Hyung-jin, Sandoll Communications, Adobe and "
            "Ryoko Nishizuka (hangul and han); the M+ Project Authors (kana and "
            "brackets)"),
        13: ("This Font Software is licensed under the SIL Open Font License, "
             "Version 1.1. It is a derivative work and is not endorsed by or "
             "verified against any upstream project."),
        14: "https://openfontlicense.org",
        16: family,
        17: style,
    }
    base["name"].names = []
    for nid, value in names.items():
        set_name(base, nid, value)
    base["OS/2"].achVendID = VENDOR
    base["head"].fontRevision = float(VERSION)

    # Record provenance now: the glyph names still carry which source drew
    # each glyph, and ttfautohint regenerates them as uniXXXX, so after hinting
    # it is no longer knowable from the binary. scripts/coverage_table.py reads
    # this.
    SRC = {"cjk": "Pretendard JP", "jamo": "Pretendard JP",
           "mp": "M PLUS 1p", "sh": "Noto Sans KR", "nf": "Iosevka Term NF"}
    # Matched on prefix + hex, not prefix alone: the base has its own glyphs
    # whose names start with these letters (`shcy`, `mpsomething`) and they must
    # not be misattributed.
    import re
    pat = re.compile(r"^(cjk|jamo|mp|sh|nf)([0-9A-F]{4,6})$")
    prov = {}
    for cp, gname in base.getBestCmap().items():
        m = pat.match(gname)
        prov[cp] = SRC[m.group(1)] if m else "Iosevka Term NF"
    os.makedirs("build", exist_ok=True)
    with open("build/provenance.json", "w") as fh:
        json.dump({str(k): v for k, v in sorted(prov.items())}, fh)

    os.makedirs(OUT, exist_ok=True)
    out_ttf = os.path.join(OUT, f"{ps}.ttf")
    stamp(base)
    base.save(out_ttf)

    base.flavor = "woff2"
    base.save(os.path.join(OUT, f"{ps}.woff2"))
    base.close()

    report[ps] = {
        "variant": variant,
        "base": base_path,
        "base_sha256": sha256(base_path),
        "added": dict(added),
        "skipped": len(skipped),
        "grid_fixes": grid_fixes,
        "skipped_sample": skipped[:8],
        "ttf": out_ttf,
        "ttf_sha256": sha256(out_ttf),
        "size_mb": round(os.path.getsize(out_ttf) / 1e6, 2),
    }
    return out_ttf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="both", choices=["K", "J", "both"])
    ap.add_argument("--weight", default="400,700")
    ap.add_argument("--variant", default="ship",
                    help="only 'ship' remains; the retired cuts are in "
                         "scripts/legacy/comparison_variants.py")
    args = ap.parse_args()

    regions = ["K", "J"] if args.region == "both" else [args.region]
    weights = [int(w) for w in args.weight.split(",")]
    variants = list(VARIANTS) if args.variant == "all" else args.variant.split(",")

    report: dict = {}
    for variant in variants:
        for region in regions:
            for w in weights:
                print(f"building Harena Term {region}{VARIANTS[variant]['label']} "
                      f"{STYLE[w][0]} ...", flush=True)
                out = build_one(w, region, variant, report)
                r = report[os.path.basename(out)[:-4]]
                print(f"  hangul +{r['added']['hangul']}  "
                      f"han/kana +{r['added']['han/kana']}  "
                      f"jamo +{r['added'].get('jamo', 0)}  "
                      f"nerd +{r['added'].get('nerd', 0)}  "
                      f"brackets {r['added'].get('brackets', 0)}  "
                      f"grid-fixed {len(r['grid_fixes'])}  {r['size_mb']} MB")

    # merge rather than overwrite: verify.py reads the base path per face out of
    # this file, and a later partial build would otherwise orphan earlier ones.
    # Entries whose output is gone are dropped, though -- merging alone let the
    # rename leave behind faces that no longer exist, pointing at base binaries
    # that no longer exist either, which provenance.py then published as
    # "consumed" and verify.py could match by prefix.
    merged = {}
    if os.path.exists("build/build-report.json"):
        try:
            merged = json.load(open("build/build-report.json"))
        except ValueError:
            merged = {}
    merged = {k: v for k, v in merged.items()
              if os.path.exists(v.get("ttf", ""))}
    merged.update(report)
    with open("build/build-report.json", "w") as fh:
        json.dump(merged, fh, indent=1)
    print("\nwrote build/build-report.json")


if __name__ == "__main__":
    sys.exit(main())
