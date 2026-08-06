# Changelog

Notable changes to Harena Term. Binaries are attached to each
[release](../../releases); this repository holds the build that produces them.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
applied to the font: a **major** bump changes metrics or naming in a way that
moves existing text, a **minor** bump adds coverage or changes how glyphs are
drawn, a **patch** bump changes nothing a reader can see.

The tag and the font's internal version are kept equal — `head.fontRevision`
and `nameID 5` read the same number a release is tagged with, so a font manager
and this file cannot disagree.

### Why 0.x

The font is complete, gated and reproducible, and it is still below 1.0 on
purpose. **1.0.0 waits on two things**, both recorded rather than vague:

1. **[ADR 0014](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md)
   resolved** — fixed, or accepted with a written rationale. Fixing it changes
   every CJK outline, which 0.x permits in a minor bump and 1.x would not.
2. **Windows verified** — TUI rendering with no column shear, including the
   Braille spinner and box-drawn frames. Never run, and this is a terminal font.

A third condition is now met: the release workflow has been exercised for real.
Tagging v0.9.0 built the fonts on a clean runner from the pinned sources, ran
the gate at 154/154, reproduced every hash in `SHA256SUMS`, and published — in
17m45s. That is also what turned "byte-reproducible" from a claim into a
checked fact, since until then it had only ever been verified on the machine
that made the claim.

Until the two above are closed, a version number that claims stability would be
claiming something nobody has checked.

## [Unreleased]

### Removed

- **The install scripts.** Unzipping and using the system font installer is one
  step, and beyond that a package manager handles upgrade and uninstall too —
  neither of which these attempted. The download path hardcoded a release URL,
  which returned 404 for as long as this repository was private with nothing
  able to notice, and the Windows script was published having never been
  executed. See [ADR 0016](docs/adr/0016-no-install-scripts.md).

## [0.9.0] — 2026-08-05

First public release. Four faces: `Harena Term K` and `Harena Term J`, Regular
and Bold, at 38478 glyphs and 37652 codepoints each.

### Added

- **Hangul at Pretendard's own letterspacing.** Each script is scaled so its
  native advance lands exactly on the cell, which reproduces the source's
  spacing as an identity rather than an approximation. Measured `T = 0.1308`
  against Sarasa Term K's `0.264` — 50% tighter, on a grid that is still
  exactly 1:2.
- **Two regional cuts**, K and J, with `ss05` baked into `cmap` because a
  terminal cannot reach an OpenType feature at runtime. They differ in 611
  codepoints, all inside han, with zero advance differences.
- **NFD hangul composed by the font**, through 11172 `ccmp` ligatures — so
  Korean filenames on macOS render as syllables rather than stacked jamo.
- **Advances driven by the width provider**, not checked against a list:
  `@xterm/addon-unicode11` pinned exactly, and all 21349 covered codepoints
  asserted against it.
- **Stroke weight compensated through the source's `wght` axis**, so two scale
  groups do not read as two colours on one line.
- **`OS/2` recomputed from the merged `cmap`**, so the font is eligible for
  East Asian text in Windows applications. Chinese codepages are pruned back
  out — 46.9% of cp950 against 98.9% of cp949.
- Coverage: hangul 11172, han 7138, Braille 256/256, box drawing 128, block
  elements 32, geometric 96, arrows 112, plus the Nerd Font icon sets.
  cp932 100%, cp949 99.98%.
- Hinted with ttfautohint for ClearType.
- **A conformance gate**, `scripts/verify.py`: 154 checks that assert rather
  than report, run over the shipped binaries.
- **A byte-reproducible build** from pinned sources, with `SHA256SUMS` written
  by the build itself and enforced in CI.
- Installers for macOS, Linux and Windows.

### Known

- Compensating every script to the Latin stem divides out the relative weighting
  Pretendard's designers built between scripts — hangul reads light beside kana.
  Measured and specified in
  [ADR 0014](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md);
  it changes every CJK outline, so it lands on top of this release rather than
  inside it.
- Ambiguous-width characters resolve to **one** cell. A terminal configured
  `ambiguous = wide` will shear those rows.
- `☎ ☏ ♨` are not shipped. They are one cell here, every source draws them
  full-width, and halving a full-width design halves its stroke past what the
  `wght` axis can restore. This is the only gap in cp949.
- Hinting reaches y only, so vertical strokes gain nothing from it. Under
  grayscale antialiasing that is visible; under subpixel rendering it is not.
  See [ADR 0010](docs/adr/0010-ttfautohint-hints-y-only.md).
- TUI rendering is verified on macOS. **Not verified on Windows.**

[Unreleased]: ../../compare/v0.9.0...HEAD
[0.9.0]: ../../releases/tag/v0.9.0
