# Changelog

Notable changes to Harena Term. Binaries are attached to each
[release](../../releases); this repository holds the build that produces them.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
applied to the font: a **major** bump changes metrics or naming in a way that
moves existing text, a **minor** bump adds coverage or fixes a glyph, a
**patch** bump changes nothing a reader can see.

## [Unreleased]

Nothing yet.

## [1.0.0] — 2026-08-04

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
- **A conformance gate**, `scripts/verify.py`: 146 checks that assert rather
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

[Unreleased]: ../../compare/v1.0.0...HEAD
[1.0.0]: ../../releases/tag/v1.0.0
