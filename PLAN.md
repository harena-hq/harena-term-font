# Harena Term — how it is built, and why

The goal in one line: **a terminal font whose hangul carries Pretendard's own
letterspacing inside a strict monospace grid.**

Every number here was measured. The load-bearing ones are re-derived from the
shipped binary by [`scripts/verify.py`](scripts/verify.py) on every build, which
fails if any of them has drifted — so this document cannot quietly go stale
against the font it describes.

Companion documents: [`docs/LINEAGE.md`](docs/LINEAGE.md) traces each source from
its origin through every hand it passed through, [`docs/COVERAGE.md`](docs/COVERAGE.md)
says which source drew each codepoint, and [`docs/adr/`](docs/adr/) holds the
decisions that could be arrived at wrongly a second time.

### Four counts, and they are not interchangeable

Stated up front because three of them are within 5% of each other and reading
one for another is the easiest mistake in this document.

| | per face | what it counts |
|---|---:|---|
| glyphs | **38478** | `maxp.numGlyphs` — everything in the font |
| hinted glyphs | **36859** | what ttfautohint instruments; composites and blanks are not among them |
| codepoints | **37652** | entries in `cmap`; what a reader can actually type |
| K/J divergence | **611** | codepoints whose outline differs between the two cuts |

---

## 1. Decisions

### D1 — Latin base: Iosevka Term Nerd Font Mono, rebuilt parametrically

A monospace face ships as a finished system: spacing, stroke weight, hinting and
the box-drawing set are already consistent with one another. Rescaling any part of
it breaks that consistency — scaling the Latin ink by 1.123 to tighten it also
thickens its strokes 12.3%, leaving text heavier than a box-drawing frame that
cannot follow, because block elements must tile the cell exactly. **So the Latin
is the fixed frame and the CJK is fitted into it**, never the reverse.

Iosevka specifically, on three measured grounds:

| | measured |
|---|---|
| Braille U+2800–28FF | **256/256** — agent TUIs emit a Braille spinner, so this is a requirement |
| box / block / geometric / arrows | 128 · 32 · 96 · 112, all half-width, one optical grid |
| vertical metrics | cap 0.7350, x-height 0.5200, desc −0.2150, linespace 1.2500 — identical to Sarasa Term K, so line height does not move |

Of twelve candidates surveyed, Braille is present only in Iosevka, ZedMono (an
Iosevka derivative), CascadiaMono and CommitMono. JetBrains Mono, Geist, IBM
Plex, Monaspace, Hack and IntelOne all measure 0/256.

**Rejected — a 0.600-advance base** (JetBrains Mono, CommitMono, GeistMono).
Not on taste: `cap / 2a` is a ceiling on hangul density that no CJK source can
raise, and widening the advance lowers it. See
[ADR 0004](docs/adr/0004-latin-advance-sets-the-hangul-ceiling.md) — a 0.600 base
held at the correct proportion produces hangul more than twice as loose as
Sarasa, which is the exact defect this font exists to remove.

**Rejected — the stock Nerd Font binary, untouched.** Iosevka's letterforms are
24% more condensed than Pretendard's Latin. That is not fixable by scaling, but
it *is* fixable parametrically, because Iosevka is generated from parameters and
`sb`, `cap` and `xHeight` are among them — they redraw the letters at unchanged
stroke weight. The shipping cut is `shape = 500`, `sb = 45`, `cap = 808`,
`xHeight = 572`. See [ADR 0001](docs/adr/0001-latin-spacing-reopened.md) and
[`latin/README.md`](latin/README.md).

### D2 — CJK source: Pretendard JP, per-script advance normalisation

Pretendard's CJK advances are already uniform *within* each script — hangul
1770 units at upm 2048, han and kana 1920. Scaling a whole script by
`cell / native_advance` therefore reproduces that script's own proportional
letterspacing **exactly**. `T = (advance − ink) / ink` is scale-invariant, so this
is an identity, not an approximation.

| script | scale | resulting T | Pretendard's own T |
|---|---|---|---|
| hangul | ×1.1571 | 0.1287 | **0.1287** |
| han | ×1.0667 | 0.0925 | **0.0925** |
| kana | ×1.0667 | 0.1871 | **0.1871** |

Against Sarasa Term K's hangul `T` of **0.264**, the shipped face measures
**0.1308 — 50% tighter** — even after the weight compensation of D3.

**Rejected — one uniform ×1.0667 for all CJK.** Tempting: one scale group,
Pretendard's inter-script proportions untouched, hangul height barely moving. But
hangul `T` only reaches 0.224, still 74% looser than Pretendard, which forfeits
the stated first priority. See [ADR 0002](docs/adr/0002-advance-normalisation-is-an-identity.md).

**Accepted cost:** hangul reads about 10% taller against the Latin than in
Sarasa. Direct consequence of prioritising spacing.

### D3 — Stroke weight compensated through the source's `wght` axis

Two scale groups produce two colours on one line: hangul lands +14.4% against
the Latin stem and +14.3% against han. Instancing the more-scaled script at a
*lighter* weight cancels that using Pretendard's own design space rather than
distorting outlines.

Reference stem: Iosevka's `|` at 0.0780 em Regular, 0.1120 em Bold.

| | scale | `wght` Regular | `wght` Bold |
|---|---|---|---|
| hangul | ×1.1571 | **403.7** | **585.8** |
| han / kana | ×1.0667 | **474.6** | **684.0** |

hangul/han stroke ratio: native 1.0533 → uncompensated 1.1426 → **compensated
1.0000**. Cost to the first priority is +5.9% on hangul `T`, which still leaves
the shipped face 50% tighter than Sarasa. See
[ADR 0003](docs/adr/0003-stroke-weight-compensated-through-wght.md).

**This target is under review.** Matching every script to the Latin stem divides
out the relative weighting Pretendard's designers built *between* scripts — they
draw hangul 13.5% heavier than han deliberately, so that a script with fewer
strokes per glyph reads at the same grayness. See
[ADR 0014](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md),
which is open and specifies the change.

### D4 — Han coverage: accept Pretendard JP's 7138, graft no third han source

7138 sounds thin against Sarasa's 20992. Measured, it is not an arbitrary subset:

| set | covered |
|---|---|
| JIS X 0208 kanji | **6356 / 6356** |
| cp932 (incl. NEC/IBM extensions) | **6682 / 6682** |
| KS X 1001 hanja | **4620 / 4620** |
| JIS X 0212 supplement | 597 / 5801 |
| JIS X 0213 level 3–4 | 81 / 567 |

Practical Japanese and Korean are complete. What is missing is rare name-kanji
and Chinese-only hanzi, and Chinese coverage is an explicit non-goal. A third han
source would import a fourth set of letterforms to reconcile, for glyphs that
will essentially never render. See [ADR 0005](docs/adr/0005-cjk-source-stays-pretendard-jp.md).

### D5 — Two regional cuts, with `ss05` baked into `cmap`

Korean and Japanese draw many of the same han differently — most visibly the
walking radical at the lower left of 運 進 週 選 過 達 通 連 遠, where Korean keeps
its traditional two dots and the Japanese shinjitai uses one.

Pretendard JP carries both, in `locl` and `ss05`. **A terminal cannot reach
either at runtime**: texture-atlas renderers build `ctx.font` from a plain CSS
shorthand, with no `font-feature-settings` and no language tag. So the forms are
baked into `cmap` and two faces ship.

- **Harena Term K** — `ss05` applied, restricted to the han range
- **Harena Term J** — default forms

611 codepoints of 37652 differ, all inside han, with **zero advance
differences** — so the two faces can even be mixed on one screen without
shearing a row. See [ADR 0006](docs/adr/0006-two-regional-cuts-with-ss05-baked-in.md).

Weights 400 and 700 only, no italic: a terminal renders SGR default and SGR 1 and
has no notion of an intermediate weight.

### D6 — No variable weight

Not achievable from these sources. Iosevka Term NF Mono Regular and Bold are
**not interpolation-compatible**: 1220 of 17827 cmap-reachable glyphs differ in
contour or point count, including `A` (18 points against 17), `B`, `C`, `G`, `K`,
`M`, `N` and `&`. Upstream publishes no variable assets — 453 release assets, all
static.

The Pretendard side is already variable and poses no problem; the blocker is
entirely the Latin. Utility would be low regardless, per D5.

### D7 — Advances are driven by the width provider, not checked against a list

If a glyph's advance disagrees with the number of cells the terminal reserved,
the row shears. [`scripts/xterm_widths.mjs`](scripts/xterm_widths.mjs) extracts
the full per-codepoint table from `@xterm/addon-unicode11` — pinned exactly in
`package.json` — and **the build is driven by it**. `verify.py` then re-derives
every advance from the binary and checks all **21349** covered codepoints against
the same table. Zero mismatches is structural rather than lucky.

This found 23 defects inherited from Iosevka that a hand-written list would not
have contained: eight zero-width formatting characters drawn a full cell wide,
and fifteen Emoji_Presentation symbols drawn one cell where the provider reserves
two — including `⚡`, `⚪` and `⚫`, each of which appears in ordinary CLI output
and would have sheared its row. See
[ADR 0008](docs/adr/0008-advances-are-driven-by-the-provider-table.md).

### D8 — Ambiguous-width characters resolve to one cell

The provider this build follows resolves all **1201** East_Asian_Width=Ambiguous
codepoints in its table to **one cell** — `♥ ○ → ± ′` and the rest. A terminal
configured `ambiguous = wide` reserves two cells for those, and this font will
draw one. **Sarasa makes the opposite choice.** A font has one advance per glyph
and cannot serve both readings.

The asymmetry decides the direction: a one-cell glyph in a two-cell slot leaves a
gap, while a two-cell glyph in a one-cell slot overlaps the character after it.

One consequence worth stating, because it is the only thing standing between this
font and 100% of cp949: **`☎ ☏ ♨` are not shipped.** They are one cell here,
every available source draws them full-width, and halving a full-width design
halves its stroke — measured, even at Noto's maximum `wght` 900 the stroke
reaches only 0.46× the Latin stem, 0.56px at 13px against the text's ~1.0px. The
`wght` axis runs out before D3's compensation can close it, and a visible
fallback beats a glyph that renders faint.

---

## 2. Done-when

Automated, in [`scripts/verify.py`](scripts/verify.py), **asserting rather than
reporting** — the exit code is the gate. Status: **154/154 across all four
faces.**

1. every CJK advance is exactly 2× the Latin advance; every half-width glyph exactly 1×
2. every advance agrees with the width provider across all 21349 covered
   codepoints, at **zero** mismatches
3. every range the build declares has coverage in the width table — a range the
   table omits is a range the build silently skips
4. coverage: hangul 11172, kana ≥182, han ≥7138, box 128, block 32, geometric 96,
   Braille **256**, arrows 112, Powerline ≥38
5. per-script measured `T` within 10% of Pretendard's own — measured hangul
   0.1308 (+1.7%), han 0.0885 (−4.3%) — and hangul at least 30% tighter than
   Sarasa (measured **50% tighter**)
6. no full-width glyph exceeds its cell, scanned exhaustively across every
   full-width range — never sampled
7. vertical metrics identical to the Iosevka base
8. hangul, han and Latin stems within 8% of each other (see D3's caveat)
9. `OS/2` declares all nine CJK blocks and codepages 949 and 932, and does **not**
   declare 936 or 950
10. K and J differ only inside the han range
11. no `.notdef` reachable from any asserted codepoint
12. **the font itself** composes all 11172 NFD hangul syllables through `ccmp`,
    walked from the ligature tree rather than inferred from a shaper
13. `head` carries the pinned build stamp, so the reproducibility claim is
    asserted on the shipped bytes rather than trusted from the stage that sets it

Manual, and the real gate:

14. TUIs render with no column shear, including the Braille idle spinner and
    box-drawn frames. **macOS: passed. Windows: not run.**

    What macOS closes is the font side. Shear is an advance disagreeing with what
    the emulator reserved, and advances are binary data — identical on both
    platforms and asserted by check 2. The residual Windows risk is whether the
    terminal there reserves the same widths this provider does, which is not a
    property of the font.
15. side-by-side against Sarasa Term K at equal cell width shows the hangul
    improvement. **If it does not, stop — the premise was wrong.** Passed.

---

## 3. Reproducibility

The build is byte-reproducible from pinned sources.
[`scripts/fetch_sources.sh`](scripts/fetch_sources.sh) downloads every input at a
pinned URL and verifies its SHA-256, clones Iosevka at a pinned tag and asserts
the commit, and installs with `npm ci` against upstream's lockfile. Python
dependencies are pinned in `requirements.txt` and the width provider in
`package.json`.

The only nondeterminism a font build has is the clock: `head.created`,
`head.modified` and the `checkSumAdjustment` derived from them. Those are stamped
from a constant next to `VERSION`, overridable by `SOURCE_DATE_EPOCH`, and
stamped again after ttfautohint, which rewrites `modified` and runs downstream of
`build.py`.

`SHA256SUMS` is written by `postbuild.py` itself rather than maintained by hand, so it
cannot drift from the binaries. A clean-room build reproduces all eight artefacts
byte for byte, and CI enforces it.

---

## 4. Deferred

**The stroke-weight target.**
[ADR 0014](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md)
is open, specified and measured. It changes every CJK outline, so it lands on top
of a released baseline where the diff is attributable to one decision.

**Hinting x as well as y.** ttfautohint hints in y only — measured, horizontal
strokes gain +21 to +36 and vertical strokes gain nothing, and no `-a` value
changes that. The tool that could is Microsoft Visual TrueType, which needs
hinting source per glyph; at ~19000 CJK glyphs that means writing a generator.
See [ADR 0010](docs/adr/0010-ttfautohint-hints-y-only.md) for the trigger.

**Element and curvature matching between scripts.** Merging two finished
typefaces can match size, spacing and weight. It cannot match the shape of a
terminal or the tension of a curve between two designers' work — that requires
drawing, not merging.

**A specimen page.** `docs/COVERAGE.md` carries the substance meanwhile.
