#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Conformance gate for Harena Term. Asserts; does not merely report.

Every check re-derives its value from the built binary and compares it against
an authority that lives outside the build:

  * cell widths come from the real xterm.js unicode11 provider, pinned
    (build/xterm-widths.json, produced by scripts/xterm_widths.mjs)
  * vertical metrics come from the untouched Iosevka base
  * density targets come from proportional Pretendard

Exit code is the gate: 0 = sealable, 1 = not.

Usage:  python3 scripts/verify.py dist/HarenaTermK-Regular.ttf [...]
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unicodedata as ud

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.misc.timeTools import timestampSinceEpoch

try:
    import freetype
except ImportError:  # the stroke-erasure check is skipped, loudly, without it
    freetype = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402  -- needs the path above when run from elsewhere

XTERM_WIDTHS = "build/xterm-widths.json"
IOS = "sources/cand/IosevkaTerm/IosevkaTermNerdFontMono-{style}.ttf"

# coverage the terminal is required to carry, from PLAN.md sec.2
COVERAGE = {
    "hangul syllables": ((0xAC00, 0xD7A3), 11172, "=="),
    "kana": ((0x3040, 0x30FF), 182, ">="),
    "han unified": ((0x4E00, 0x9FFF), 7138, ">="),
    "box drawing": ((0x2500, 0x257F), 128, "=="),
    "block elements": ((0x2580, 0x259F), 32, "=="),
    "geometric": ((0x25A0, 0x25FF), 96, "=="),
    "braille": ((0x2800, 0x28FF), 256, "=="),
    "arrows": ((0x2190, 0x21FF), 112, "=="),
    "powerline": ((0xE0A0, 0xE0D4), 38, ">="),
}

# Proportional Pretendard's own gap/ink per script -- the value the advance
# normalisation of PLAN.md D2 reproduces as an identity. The weight
# compensation of D3 instances hangul lighter, which narrows its ink slightly,
# and integer coordinates at upm 1000 cost a little more. That inflation is an
# accepted cost, but it is capped: it may not eat more than 10% of the spacing
# the project exists to win.
DENSITY = {
    "hangul": (range(0xAC00, 0xD7A4, 37), 0.1287, 0.10),
    "han": (range(0x4E00, 0x9FA0, 29), 0.0925, 0.10),
}

SARASA_HANGUL_T = 0.264

# Pretendard's own hangul/han stroke ratio, each script normalised by its own
# advance -- which is exactly what this build must reproduce, since both
# advances land on the same cell here. Vertical is ㅣ against 丨 and horizontal
# ㅡ against 一, single-stroke glyphs where an ink dimension is the stroke.
#
# The two point opposite ways: hangul verticals run 14% heavier than han's, its
# horizontals 3-6% lighter. No single number could have stood in for both, and
# the check these replace asserted one number for one axis -- at a value that
# erased the relationship rather than holding it. See docs/adr/0014.
SOURCE_STROKE_RATIO = {
    "Regular": {"vertical": 1.1426, "horizontal": 0.9690},
    "Bold": {"vertical": 1.1461, "horizontal": 0.9449},
}

# Hinting must not erase a horizontal stroke the design draws.
#
# ttfautohint grid-fits horizontal edges. Where a stroke's top and bottom round
# onto the same pixel its height becomes zero and the stroke is simply gone: on
# the defaults, ㅌ's three bars came out as two at 15 and 16 ppem, so 텰 read as
# 뎔, and the top arc of ㅇ opened. `postbuild.HINT_ARGS` is what stops that;
# this check is what keeps it stopped. See docs/adr/0019.
#
# Two mistakes were made building this and both are worth not repeating.
#
# Counting strokes against the unhinted render and demanding equality does not
# work -- hinting legitimately merges two faint strokes into one crisp one, and
# that reads better, not worse. Measured, that reports 14737 failures where a
# reader sees two. So the question is the narrower one a reader notices: a
# stroke the unhinted outline draws at >=50% coverage must still be drawn, at
# >=25%, within +/-2 rows of where it was. The tolerance is measured rather
# than guessed -- over 2235 syllables at 16 and 17 ppem, hinting never moved a
# glyph's ink top by more than 2 rows.
#
# And a run of four dark columns is not yet a bar. At these sizes the shallow
# tail of a diagonal -- ㅅ ㅈ ㅊ ㄱ -- makes exactly four, and those swamp the
# real thing: with a flat four-column floor the shipped font reports 569
# "erasures", every one of them four columns wide and none of them a bar.
# Requiring a run to span a third of the glyph's own ink separates them. The
# fraction is used as-is, and the reason is narrower than it looks: a `max(4,
# ...)` floor is inert (measured, 39 and 0, unchanged -- it can only bind below
# an 11.43 px glyph, where it makes the check stricter). What brought the
# residue back was rounding the fraction to an integer first, `max(4, int(...))`
# giving 307 and 226. Truncation is the hazard here, not the floor.
#
# One inconsistency to know about: below an 11.43 px glyph the fraction falls
# under 4, so a four-column run is admitted after all -- the thing this
# paragraph says is not a bar. That is 1.0% of renders in this range (w = 11 at
# 13 ppem) and it costs nothing measured, but the code and this prose disagree
# there.
#
# Measured on the 1.0.1 binaries, which had the defect, it flags 39 -- all of
# them at 15 and 16 ppem, which are the two sizes that were reported, and among
# them 텰 at both and 열 at 15. On 1.0.2 it flags none, in either weight and
# either cut. So the assertion is zero. That trades a fitted count for a fitted
# threshold rather than removing the fitting -- but it is a far better trade: a
# budget that is mostly noise absorbs a real regression, since 30 bars could go
# missing while 30 diagonals stopped being miscounted and the total would not
# move, and the whole 1.0.1 defect is only 39 incidents. Where the count swung
# by hundreds on a two-flag change, this threshold's answer holds from 0.35 to
# 0.50. It still needs refitting if the noise floor moves.
#
# BAR_MIN_WIDTH was chosen rather than derived, and the rule it was chosen by is
# the part worth keeping: **the smallest fraction at which the shipped font is
# clean** -- most sensitive, subject to no false positives. Below it there is no
# margin at all (1.0.2 reports 4 at 0.32 and 95 at 0.30). Above it the answer is
# stable: 0.35 through 0.50 all report zero on 1.0.2 while still catching 34-39
# on 1.0.1, so the conclusion survives anywhere in that band. 0.35 is the only
# value in it that also catches 열 at 15 ppem, one of the two syllables that
# were reported. Re-derive by the rule, not by copying the number.
#
# Two things this does not cover. 열 at 16 ppem, where the top arc of ㅇ was
# also erased: a circle's arc is not a bar, and there its run is 4 columns of a
# 15 px glyph, 27%, below the threshold that makes the check mean anything. The
# check is named for bars because bars are what it asserts.
#
# And Bold has no positive control. It reports 0 on the 1.0.1 binaries too, so
# this check has never been shown to detect anything in that weight -- it is
# proven against Regular and assumed to transfer.
#
# 13-18 ppem is the range a terminal is read at on a 96-110 DPI display, and
# where grid-fitting arbitrates at all; ADR 0017 verified Windows at 14, and
# the report that started this was at 16.
HINTING_STROKE_RANGE = range(13, 19)
BAR_MIN_WIDTH = 0.35


class Gate:
    def __init__(self) -> None:
        self.fails: list[str] = []
        self.checks = 0

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.checks += 1
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
        if not ok:
            self.fails.append(label)
        return ok


def load_widths() -> dict[int, int]:
    data = json.load(open(XTERM_WIDTHS))
    data.pop("_version", None)
    out: dict[int, int] = {}
    for block in data.values():
        for w, cps in block["widths"].items():
            for cp in cps:
                out[cp] = int(w)
    return out


def ink_width(gs, hmtx, gname, upm):
    p = BoundsPen(gs)
    gs[gname].draw(p)
    if not p.bounds:
        return None
    return (p.bounds[2] - p.bounds[0]) / upm


def bar(font, upm, ch, gs=None):
    """Horizontal counterpart to `stem`: the ink *height* of a single
    horizontal stroke, which is that stroke's weight."""
    gs = gs or font.getGlyphSet()
    gn = font.getBestCmap().get(ord(ch))
    if not gn:
        return None
    p = BoundsPen(gs)
    gs[gn].draw(p)
    return (p.bounds[3] - p.bounds[1]) / upm if p.bounds else None


def _rows(face, ch, ppem, hinted):
    """Rasterise one glyph and return its rows as lists of coverage bytes,
    plus the ink top, so hinted and unhinted renders can be aligned."""
    flags = freetype.FT_LOAD_RENDER
    if not hinted:
        flags |= freetype.FT_LOAD_NO_HINTING
    face.set_pixel_sizes(0, ppem)
    face.load_char(ch, flags)
    b = face.glyph.bitmap
    if not (b.rows and b.width):
        return [], 0
    buf = b.buffer
    return ([buf[y * b.pitch:y * b.pitch + b.width] for y in range(b.rows)],
            face.glyph.bitmap_top)


def _bars(row, floor, least):
    """(start, end) of every run of at least `least` adjacent columns at or
    above floor. See BAR_MIN_WIDTH for why the threshold is not simply 1."""
    out, start = [], None
    for i, v in enumerate(row):
        if v >= floor and start is None:
            start = i
        elif v < floor and start is not None:
            if i - start >= least:
                out.append((start, i))
            start = None
    if start is not None and len(row) - start >= least:
        out.append((start, len(row)))
    return out


def _kept(rows, y, x0, x1, floor, tol, share=0.6):
    """Is a bar spanning [x0, x1) still drawn within tol rows of y?

    `share` of its columns must survive. A flat minimum alongside the fraction
    would make the demand non-monotonic -- max(4, int(w * 0.6)) asks for 100% of
    a 4-wide run but only 50% of an 8-wide one, loosest in the middle of the
    range this calls a bar -- so the fraction stands alone, as in `_bars`.
    """
    for dy in range(-tol, tol + 1):
        if not 0 <= y + dy < len(rows):
            continue
        seg = rows[y + dy][x0:x1]
        if seg and sum(v >= floor for v in seg) >= share * len(seg):
            return True
    return False


def erased_strokes(path, ppems=HINTING_STROKE_RANGE):
    """(syllable, ppem) pairs whose hinted render loses a horizontal stroke the
    unhinted outline draws solidly. See BAR_MIN_WIDTH for the rules."""
    SOLID, PRESENT, TOL = 128, 64, 2
    face = freetype.Face(path)
    lost = []
    for cp in range(0xAC00, 0xD7A4):
        ch = chr(cp)
        for ppem in ppems:
            plain, plain_top = _rows(face, ch, ppem, hinted=False)
            hinted, hinted_top = _rows(face, ch, ppem, hinted=True)
            if not plain or not hinted:
                continue
            shift = plain_top - hinted_top
            width = len(hinted[0])
            least = BAR_MIN_WIDTH * len(plain[0])
            # A stroke spans several rows; test its topmost row only, or a 2px
            # bar counts twice and a legitimate merge reads as a deletion.
            above_was_bar = False
            for y, row in enumerate(plain):
                bars = _bars(row, SOLID, least)
                if not bars:
                    above_was_bar = False
                    continue
                if above_was_bar:
                    continue
                above_was_bar = True
                if any(not _kept(hinted, y - shift, x0, min(x1, width),
                                 PRESENT, TOL)
                       for x0, x1 in bars if min(x1, width) - x0 >= least):
                    lost.append((ch, ppem))
                    break
    return lost


def stem(font, upm, ch, gs=None):
    cmap = font.getBestCmap()
    gs = gs or font.getGlyphSet()
    gn = cmap.get(ord(ch))
    if not gn:
        return None
    p = BoundsPen(gs)
    gs[gn].draw(p)
    return (p.bounds[2] - p.bounds[0]) / upm if p.bounds else None


def verify(path: str, g: Gate) -> None:
    print(f"\n=== {os.path.basename(path)} ===")
    f = TTFont(path)
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    gs = f.getGlyphSet()
    widths = load_widths()
    latin_adv = hmtx[cmap[ord("H")]][0]

    # --- 1. the grid ----------------------------------------------------
    # head is the only table that was ever nondeterministic between two builds
    # of identical inputs, and ttfautohint rewrites `modified` after build.py
    # has set it. Asserting the stamp here is what keeps "reproducible" true:
    # it is checked on the shipped bytes, downstream of every stage that could
    # undo it.
    want_ts = timestampSinceEpoch(build.SOURCE_DATE)
    head = f["head"]
    g.check(head.created == want_ts and head.modified == want_ts,
            "head carries the pinned build stamp",
            f"created={head.created} modified={head.modified} want={want_ts}")

    # The version a release is tagged with must be the version the font reports,
    # or a user installs 0.9.0 and their font manager says 1.000. VERSION feeds
    # two records that are set independently, so a partial edit is possible and
    # silent. head.fontRevision is Fixed 16.16, so 0.900 stores as 0.89999... --
    # compare at the precision the format actually has, not with ==.
    want_rev = float(build.VERSION)
    got_rev = head.fontRevision
    g.check(abs(got_rev - want_rev) < 1 / 65536,
            "head.fontRevision matches VERSION",
            f"fontRevision={got_rev} want={want_rev}")
    ver_names = {r.toUnicode() for r in f["name"].names if r.nameID == 5}
    g.check(ver_names == {f"Version {build.VERSION}"},
            "nameID 5 matches VERSION",
            f"nameID 5={sorted(ver_names)} want='Version {build.VERSION}'")

    g.check(upm == 1000, "upm is 1000", f"upm={upm}")
    g.check(latin_adv * 2 == 1000, "CJK cell is exactly 2x the Latin advance",
            f"latin={latin_adv} cell={latin_adv * 2}")

    mismatches: list[tuple[int, int, int]] = []
    checked = 0
    for cp, cells in widths.items():
        gname = cmap.get(cp)
        if gname is None:
            continue
        checked += 1
        want = cells * latin_adv
        got = hmtx[gname][0]
        if got != want:
            mismatches.append((cp, want, got))
    g.check(not mismatches,
            f"advance matches the unicode11 provider for all {checked} covered codepoints",
            f"{len(mismatches)} mismatches" if mismatches else "0 mismatches")
    for cp, want, got in mismatches[:10]:
        print(f"         U+{cp:04X} {chr(cp)!r} want {want} got {got}")

    # every advance must be one of 0 / 1 cell / 2 cells -- nothing in between
    strays = {hmtx[n][0] for n in f.getGlyphOrder()} - {0, latin_adv, latin_adv * 2}
    g.check(not strays, "every advance is 0, 1 or 2 cells",
            f"stray advances: {sorted(strays)[:8]}" if strays else "")

    # Claude Code animates its working indicator in place as `·`, `+`, `*`.
    # A high typographic asterisk makes that cell jump vertically even though
    # its advance is correct. The middle dot and plus establish the intended
    # centre; keep all three on the same optical row within rounding tolerance.
    indicator_centres = {}
    for cp in (0x00B7, 0x002B, 0x002A):
        pen = BoundsPen(gs)
        gs[cmap[cp]].draw(pen)
        indicator_centres[cp] = (pen.bounds[1] + pen.bounds[3]) / 2
    target = (indicator_centres[0x00B7] + indicator_centres[0x002B]) / 2
    offsets = {cp: centre - target
               for cp, centre in indicator_centres.items()}
    g.check(max(abs(offset) for offset in offsets.values()) <= 10,
            "Claude Code indicator glyphs share one optical centre",
            ", ".join(f"{chr(cp)} {offset:+.1f}u"
                      for cp, offset in offsets.items()))

    # --- 2. coverage ----------------------------------------------------
    for label, ((lo, hi), want, op) in COVERAGE.items():
        n = sum(1 for cp in range(lo, hi + 1) if cp in cmap)
        ok = (n == want) if op == "==" else (n >= want)
        g.check(ok, f"coverage {label} {op} {want}", f"got {n}")

    notdef = [cp for cp in cmap if cmap[cp] == ".notdef"]
    g.check(not notdef, "no codepoint maps to .notdef",
            f"{len(notdef)} do" if notdef else "")

    # --- 2a. the authority must cover everything the build claims -------
    # The build skips any codepoint the width table has no entry for, and says
    # so only in a report nobody reads. That is how the jamo went missing, and
    # it happened again: U+FE30-FE4F and U+FFE0-FFE6 were declared as han/kana
    # ranges while the extractor never asked for them, so ￥ and ￡ were
    # silently dropped. A range absent from the authority is a blind spot, not
    # a pass, so the two lists are now checked against each other.
    GROUPS = build.GROUPS
    uncovered = []
    for group in GROUPS:
        for lo, hi in group.ranges:
            n = sum(1 for cp in range(lo, hi + 1) if cp in widths)
            if n == 0:
                uncovered.append(f"U+{lo:04X}-U+{hi:04X} ({group.name})")
    g.check(not uncovered,
            "every range the build declares is in the width table",
            "; ".join(uncovered) if uncovered else
            f"{sum(len(gr.ranges) for gr in GROUPS)} ranges")

    # --- 2b. OS/2 must admit to carrying CJK ----------------------------
    # These bits are how Word and the Windows font machinery decide whether a
    # face may serve East Asian text. Inherited from Iosevka they said "Latin
    # only", so Word set the hangul run in a fallback while leaving spaces and
    # Latin in this face -- a defect invisible in every glyph-level check.
    os2 = f["OS/2"]
    ur = (os2.ulUnicodeRange1 | os2.ulUnicodeRange2 << 32
          | os2.ulUnicodeRange3 << 64 | os2.ulUnicodeRange4 << 96)
    RANGES = {28: "Hangul Jamo", 48: "CJK Symbols and Punctuation",
              49: "Hiragana", 50: "Katakana", 52: "Hangul Compatibility Jamo",
              56: "Hangul Syllables", 59: "CJK Unified Ideographs",
              61: "CJK Compatibility Ideographs",
              68: "Halfwidth and Fullwidth Forms"}
    absent = [name for bit, name in RANGES.items() if not ur >> bit & 1]
    g.check(not absent, "OS/2 declares every CJK block this font carries",
            f"missing: {', '.join(absent)}" if absent else f"{len(RANGES)}/{len(RANGES)}")

    cp1 = os2.ulCodePageRange1
    for bit, name in ((19, "949 Korean Wansung"), (17, "932 Japanese")):
        g.check(bool(cp1 >> bit & 1), f"OS/2 declares codepage {name}",
                "" if cp1 >> bit & 1 else "Word will not set East Asian text in this face")
    # Chinese is a non-goal and coverage is under half; declaring it would have
    # the OS pick this face for text it cannot set.
    for bit, name in ((18, "936 Chinese Simplified"), (20, "950 Chinese Traditional")):
        g.check(not cp1 >> bit & 1, f"OS/2 does not claim codepage {name}",
                "claimed, but coverage is well under half" if cp1 >> bit & 1 else "")

    # --- 3. density: the reason the project exists ----------------------
    # This carried a waiver for the retired Conform cut, which traded spacing
    # for proportion by design. One cut ships, so hangul is held to the target
    # unconditionally and the waiver is gone rather than switched off.
    for script, (sample, target, tol) in DENSITY.items():
        vals = []
        for cp in sample:
            gname = cmap.get(cp)
            if not gname:
                continue
            w = ink_width(gs, hmtx, gname, upm)
            if w is None:
                continue
            box = hmtx[gname][0] / upm
            vals.append((box - w) / w)
        T = sum(vals) / len(vals)
        # One-sided on purpose, and the message now says so. Looser than the
        # source is the defect this project exists to remove; tighter is the
        # direction of travel, and what bounds it is the cell-clearance check
        # rather than a floor here. The label used to read "within 10%", which
        # announces a two-sided band that was never asserted -- Bold han passes
        # at -21.1%.
        g.check(T <= target * (1 + tol),
                f"{script} letterspacing no looser than Pretendard's "
                f"{target} +{tol:.0%}",
                f"T={T:.4f}, {(T / target - 1):+.1%} (n={len(vals)})")
        if script == "hangul":
            g.check(T < SARASA_HANGUL_T * 0.7,
                    "hangul is at least 30% tighter than Sarasa Term K",
                    f"T={T:.4f} vs Sarasa {SARASA_HANGUL_T} "
                    f"({(1 - T / SARASA_HANGUL_T):.0%} tighter)")

    # --- 3b. NFD Korean must render as NFC does -------------------------
    # macOS filenames are NFD and agent output carries them through verbatim.
    # Chromium picks the font by cmap coverage before shaping, so the jamo have
    # to be present here or the whole run goes to a fallback and HarfBuzz's
    # Hangul composition never gets a chance to run.
    modern = ([ud.normalize("NFD", chr(0xAC00 + l * 588))[0] for l in range(19)]
              + [ud.normalize("NFD", chr(0xAC00 + v * 28))[1] for v in range(21)]
              + [ud.normalize("NFD", chr(0xAC00 + t))[2] for t in range(1, 28)])
    absent = [c for c in modern if ord(c) not in cmap]
    g.check(not absent, "all 67 modern conjoining jamo are in cmap",
            f"{len(absent)} missing" if absent else "67/67")

    # the leading consonant carries the advance; vowel and trailing are zero
    bad_w = []
    for ch in modern:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        want = latin_adv * 2 if 0x1100 <= ord(ch) <= 0x115F else 0
        if hmtx[gname][0] != want:
            bad_w.append((ord(ch), want, hmtx[gname][0]))
    g.check(not bad_w, "jamo advances follow the shaping model (L=2 cells, V/T=0)",
            f"{len(bad_w)} wrong" if bad_w else "")

    # an NFD syllable must sum to the same advance as its NFC form
    drift = []
    for cp in range(0xAC00, 0xD7A4, 401):
        nfc = cmap.get(cp)
        seq = ud.normalize("NFD", chr(cp))
        if nfc is None or any(ord(c) not in cmap for c in seq):
            continue
        if sum(hmtx[cmap[ord(c)]][0] for c in seq) != hmtx[nfc][0]:
            drift.append(cp)
    g.check(not drift, "NFD advance sum equals the NFC advance",
            f"{len(drift)} syllables drift" if drift else "checked 28")

    # The font itself must compose the sequence, not the shaper. HarfBuzz's
    # Hangul shaper normalises the buffer before any lookup runs, so shaping
    # NFD through it proves nothing about the font -- it passed for months
    # while macOS drew the three jamo stacked on one another, because CoreText
    # has no such shaper and composes only what the font composes. So the
    # ccmp ligature tree is walked directly, and exhaustively.
    gsub = f["GSUB"].table
    ccmp_idx = {i for fr in gsub.FeatureList.FeatureRecord
                if fr.FeatureTag == "ccmp" for i in fr.Feature.LookupListIndex}
    ligs: dict[tuple[str, str], str] = {}
    for i in sorted(ccmp_idx):
        lk = gsub.LookupList.Lookup[i]
        if lk.LookupType != 4:
            continue
        for st in lk.SubTable:
            for head, entries in st.ligatures.items():
                for lig in entries:
                    if len(lig.Component) == 1:
                        ligs[(head, lig.Component[0])] = lig.LigGlyph

    uncomposed = []
    for cp in range(0xAC00, 0xD7A4):
        seq = [cmap.get(ord(c)) for c in ud.normalize("NFD", chr(cp))]
        cur = seq[0]
        for nxt in seq[1:]:
            cur = ligs.get((cur, nxt)) if cur and nxt else None
        if cur != cmap.get(cp):
            uncomposed.append(cp)
    g.check(not uncomposed, "font composes every NFD syllable through ccmp",
            f"{len(uncomposed)} of 11172 fail to compose"
            if uncomposed else "11172/11172")

    hang = [r for r in gsub.ScriptList.ScriptRecord if r.ScriptTag == "hang"]
    reachable = bool(hang) and bool(
        set(hang[0].Script.DefaultLangSys.FeatureIndex) & {
            i for i, fr in enumerate(gsub.FeatureList.FeatureRecord)
            if fr.FeatureTag == "ccmp"})
    g.check(reachable, "ccmp is registered under the 'hang' script",
            "" if reachable else "engines that key on the run's script miss it")

    # and end to end, with the Hangul shaper explicitly out of the way
    hb = shutil.which("hb-shape")
    if hb:
        def shape(codes, script):
            out = subprocess.run(
                [hb, f"--font-file={path}", f"--script={script}",
                 "--unicodes=" + ",".join(f"{c:04X}" for c in codes)],
                capture_output=True, text=True)
            return out.stdout.strip()
        # cluster indices differ by construction; compare glyph + advance
        norm = lambda r: [p.split("=")[0] + "+" + p.split("+")[-1]  # noqa: E731
                          for p in r.strip("[]").split("|")]
        same = []
        for script in ("Zyyy", "hang"):
            for cp in (0xD55C, 0xAE00, 0xAC00, 0xD7A3):
                nfc = shape([cp], script)
                nfd = shape([ord(c) for c in ud.normalize("NFD", chr(cp))],
                            script)
                same.append(norm(nfc) == norm(nfd))
        g.check(all(same), "hb-shape collapses NFD to NFC with and without "
                           "the Hangul shaper", f"{sum(same)}/{len(same)}")
    else:
        print("         (hb-shape not found — composition check skipped)")

    # --- 4. nothing collides --------------------------------------------
    # Every glyph in every full-width range, not a sample and not just the two
    # big blocks. A collision check asks for the worst case: sampling every 17th
    # syllable reported 0.986 where the true maximum was 0.997, and scanning only
    # hangul and han let kana and the fullwidth forms through -- U+FF3F and a
    # Bold U+FF37 were already at or past the cell edge.
    worst = (0.0, None)
    scan = (list(range(0xAC00, 0xD7A4)) + list(range(0x4E00, 0xA000))
            + list(range(0x3041, 0x3097)) + list(range(0x30A1, 0x30FB))
            + list(range(0x3000, 0x3040)) + list(range(0xFF01, 0xFF61)))
    for cp in scan:
        gname = cmap.get(cp)
        if not gname:
            continue
        w = ink_width(gs, hmtx, gname, upm)
        box = hmtx[gname][0] / upm
        if w and box and w / box > worst[0]:
            worst = (w / box, cp)
    # 0.99 leaves 5 units a side on a 1000-unit cell. Sarasa never gets near it
    # -- its widest syllable fills 0.870, a 13% clearance -- but normalising the
    # advance onto the cell pushes ours to 0.97 and the heavier cuts higher
    # still, so this is the binding constraint on how bold the CJK can go.
    # Two thresholds. Nothing may exceed its cell at all -- that is overlap --
    # and hangul and han additionally keep a margin, since Sarasa's widest
    # syllable sits at 0.870 and ours are pushed to 0.97 by the advance
    # normalisation. Glyphs that legitimately fill the cell to join up, like the
    # fullwidth low line, land exactly on 1.0 and are not overflow.
    g.check(worst[0] <= 1.0, "no glyph overflows its cell",
            f"max {worst[0]:.4f} at U+{worst[1]:04X}")

    worst_hh = (0.0, None)
    for cp in list(range(0xAC00, 0xD7A4)) + list(range(0x4E00, 0xA000)):
        gname = cmap.get(cp)
        if not gname:
            continue
        w = ink_width(gs, hmtx, gname, upm)
        box = hmtx[gname][0] / upm
        if w and box and w / box > worst_hh[0]:
            worst_hh = (w / box, cp)
    worst = worst_hh
    g.check(worst[0] <= 0.99, "widest hangul/han ink leaves clearance in its cell",
            f"max {worst[0]:.4f} at U+{worst[1]:04X} "
            f"(Sarasa 0.870)")

    # --- 5. vertical metrics unchanged from the base --------------------
    # Read the base out of the build report rather than assuming it: the
    # `redraw` variant is built on a from-source Latin whose leading is
    # deliberately 1.350 instead of 1.250, and asserting against the stock
    # Iosevka would flag that intended change as a defect.
    style = "Bold" if "Bold" in path else "Regular"
    base_path = IOS.format(style=style)
    try:
        rep = json.load(open("build/build-report.json"))
        name = os.path.basename(path)[:-4]
        entry = rep.get(name)
        if entry is None:
            # hinted cuts carry a tag folded into the filename, so
            # a hinted or suffixed cut has no report entry of its own; fall
            # back to the longest report key whose stem prefixes this one
            face_stem, _, sty = name.rpartition("-")   # not `stem`: that is a
            cands = [k for k in rep                     # module function below
                     if k.rpartition("-")[2] == sty
                     and face_stem.startswith(k.rpartition("-")[0])]
            if cands:
                entry = rep[max(cands, key=len)]
        if entry:
            base_path = entry["base"]
    except (OSError, ValueError):
        pass
    base = TTFont(base_path, lazy=True)
    bu = base["head"].unitsPerEm
    same = True
    for tag, attr in (("hhea", "ascender"), ("hhea", "descender"),
                      ("hhea", "lineGap"), ("OS/2", "sTypoAscender"),
                      ("OS/2", "sTypoDescender"), ("OS/2", "usWinAscent"),
                      ("OS/2", "usWinDescent")):
        a = getattr(f[tag], attr) / upm
        b = getattr(base[tag], attr) / bu
        if abs(a - b) > 1e-9:
            same = False
            print(f"         {tag}.{attr}: {a} vs base {b}")
    g.check(same, "vertical metrics identical to the Latin base",
            os.path.basename(base_path))

    # --- 6. stroke weight ------------------------------------------------
    # Two different requirements, and conflating them is what ADR 0014 is
    # about. Against the Latin, the CJK must not read as a second colour on a
    # mixed line -- that is the 8% band, and it applies to the CJK as a whole.
    # Between the CJK scripts, the requirement is the opposite of parity: the
    # source draws hangul heavier than han on purpose, because hangul carries
    # fewer strokes per glyph and would otherwise read as a hole in the page.
    # This gate used to assert that those two were equal, so it did not merely
    # miss the erasure -- it required it.
    latin_stem = stem(f, upm, "|", gs)
    hangul_stem = stem(f, upm, "ㅣ", gs)
    han_stem = stem(f, upm, "丨", gs)
    hangul_bar = bar(f, upm, "ㅡ", gs)
    han_bar = bar(f, upm, "一", gs)
    if hangul_stem and han_stem and latin_stem:
        for label, s in (("hangul", hangul_stem), ("han", han_stem)):
            r = s / latin_stem
            g.check(0.92 <= r <= 1.08,
                    f"{label} stroke within 8% of the Latin stem",
                    f"{r:.3f}x")
    if hangul_stem and han_stem and hangul_bar and han_bar:
        want = SOURCE_STROKE_RATIO[style]
        # 5%, because the build has one `wght` per group and the two axes are
        # not independently reachable: the vertical ratio is solved and the
        # horizontal follows. Measured, it follows to within 2%.
        for axis, ours, target in (
                ("vertical", hangul_stem / han_stem, want["vertical"]),
                ("horizontal", hangul_bar / han_bar, want["horizontal"])):
            g.check(abs(ours / target - 1) <= 0.05,
                    f"hangul/han {axis} stroke ratio holds Pretendard's "
                    f"{target}",
                    f"{ours:.4f}, {(ours / target - 1):+.1%}")
    # --- 7. the two regional cuts differ only in han --------------------
    # PLAN.md D5 claims it; assert it. ss05 also re-cuts punctuation, and its
    # bracket alternates are proportional `.hang` forms that do not belong in a
    # grid, so baking the feature wholesale silently moved the opening brackets.
    twin = path.replace("TermK", "TermJ") if "TermK" in path else None
    if twin and os.path.exists(twin):
        tf = TTFont(twin)
        tc, th = tf.getBestCmap(), tf["hmtx"]
        tgs = tf.getGlyphSet()
        tu = tf["head"].unitsPerEm
        stray = []
        for cp in sorted(set(cmap) & set(tc)):
            if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
                continue          # han is where they are meant to differ
            a, b = cmap[cp], tc[cp]
            if hmtx[a][0] != th[b][0]:
                stray.append(cp)
                continue
            pa, pb = BoundsPen(gs), BoundsPen(tgs)
            gs[a].draw(pa)
            tgs[b].draw(pb)
            if pa.bounds != pb.bounds:
                stray.append(cp)
        tf.close()
        g.check(not stray, "K and J cuts differ only inside the han range",
                (f"{len(stray)} stray: "
                 + " ".join(f"U+{c:04X}" for c in stray[:8])) if stray else "")

    # --- 8. hinting must not erase a horizontal stroke ------------------
    lo, hi = HINTING_STROKE_RANGE[0], HINTING_STROKE_RANGE[-1]
    label = f"hinting erases no hangul bar at {lo}-{hi} ppem"
    if freetype is None:
        # Announced, not silently skipped: a gate that runs one check short and
        # still says PASS is worse than one that says it could not run.
        print(f"  [SKIP] {label}  (pip install freetype-py)")
    else:
        lost = erased_strokes(path)
        g.check(not lost, label,
                " ".join(f"{c}@{ppem}" for c, ppem in lost[:8]) if lost
                else f"11172 syllables x {hi - lo + 1} sizes")

    base.close()
    f.close()


def main() -> int:
    paths = sys.argv[1:]
    if not paths:
        import glob
        paths = sorted(glob.glob("dist/*.ttf"))
    if not paths:
        print("no fonts to verify", file=sys.stderr)
        return 1
    g = Gate()
    for p in paths:
        verify(p, g)
    print(f"\n{g.checks - len(g.fails)}/{g.checks} checks passed")
    if g.fails:
        print("FAILED:")
        for x in g.fails:
            print("  -", x)
        return 1
    print("gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
