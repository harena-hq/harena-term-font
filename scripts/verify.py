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
    # The Conform variant traded spacing for proportion by design and needed a
    # waiver here. It is retired to scripts/legacy/comparison_variants.py, so
    # the waiver is gone and hangul is held to the target unconditionally.
    conform = False
    for script, (sample, target, tol) in DENSITY.items():
        if conform and script == "hangul":
            tol = 1.0        # this variant trades spacing for proportion by design
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
        g.check(T <= target * (1 + tol),
                f"{script} letterspacing within {tol:.0%} of Pretendard's {target}",
                f"T={T:.4f}, {(T / target - 1):+.1%} (n={len(vals)})")
        if script == "hangul" and not conform:
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

    # --- 6. stroke weight parity ----------------------------------------
    latin_stem = stem(f, upm, "|", gs)
    hangul_stem = stem(f, upm, "ㅣ", gs)
    han_stem = stem(f, upm, "丨", gs)
    if hangul_stem and han_stem and latin_stem:
        for label, s in (("hangul", hangul_stem), ("han", han_stem)):
            r = s / latin_stem
            g.check(0.92 <= r <= 1.08,
                    f"{label} stroke within 8% of the Latin stem",
                    f"{r:.3f}x")
        r = hangul_stem / han_stem
        g.check(0.94 <= r <= 1.06, "hangul and han strokes match each other",
                f"{r:.3f}x")
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
