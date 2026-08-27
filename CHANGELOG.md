# Changelog

Notable changes to Harena Term. Binaries are attached to each
[release](../../releases); this repository holds the build that produces them.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
applied to the font: a **major** bump changes metrics or naming in a way that
moves existing text, a **minor** bump adds coverage or changes the design
systemically, and a **patch** bump corrects a local glyph defect without
changing metrics, coverage or naming.

The tag and the font's internal version are kept equal — `head.fontRevision`
and `nameID 5` read the same number a release is tagged with, so a font manager
and this file cannot disagree.

### The road to 1.0

v0.9.0 shipped below 1.0 on purpose, waiting on three things. **All three are
closed**, and 1.0.0 is what closing them produced:

1. **The release workflow exercised for real** — met by tagging v0.9.0 itself.
2. **[ADR 0014](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md)**
   — fixed, which is exactly the CJK-wide outline change 0.x permits in a minor
   bump and 1.x would not.
3. **Windows verified** — TUI rendering with no column shear, including the
   Braille spinner and box-drawn frames, in **both** Windows Terminal and
   Windows Console Host, at an em of 14 px where ttfautohint's grid-fitting
   actually arbitrates. Measured off the captures rather than eyeballed, and
   recorded in [ADR 0017](docs/adr/0017-windows-verified.md) with the one
   platform difference it turned up: conhost gives every conjoining jamo a
   cell, so NFD Korean runs wider there. The font declares them 2/0/0, which
   is what the width provider says and what Windows Terminal renders.

On the first of those: tagging v0.9.0 built the fonts on a clean runner from the
pinned sources, ran the gate, reproduced every hash in `SHA256SUMS` and
published, in 17m45s. That is what turned "byte-reproducible" from a claim into
a checked fact, since until then it had only ever been verified on the machine
making the claim.

## [Unreleased]

## [1.0.1] — 2026-08-27

### Fixed

- Lower the asterisk to the optical centre shared by the middle dot and plus.
  Claude Code cycles through `·`, `+`, and `*` as an in-place working
  indicator; Iosevka's default high asterisk made that animation jump about
  0.27 em vertically. The Latin source build now selects Iosevka's
  `penta-low` variant, keeping the final hinted centres within 10 font units in
  Regular and Bold.

### Added

- A publish-ready `@harena-hq/term-font` npm distribution with separate K and
  J CSS entry points, WOFF2-only payloads and the complete licence bundle. The
  package is assembled from verified release bytes rather than storing fonts
  in git.

### Changed

- The npm wrapper and the embedded font now carry separate versions. CSS-only
  `npm-v*` releases reuse byte-identical fonts; `harena.fontVersion` and
  `SHA256SUMS` keep the payload tied to a specific font release.
- npm trusted publishing runs in a minimal job that receives only the verified
  tarball. The upstream font build never holds an OIDC publishing token.

## [1.0.0] — 2026-08-06

### Changed

- **The CJK is now weighted as one body against the Latin, not script by
  script.** v0.9.0 solved a source `wght` per script so each matched the Latin
  stem, which divided out the weighting Pretendard's designers built *between*
  the scripts — hangul is drawn heavier than han on purpose, because it carries
  fewer strokes per glyph and would otherwise read as a hole in the page. The
  build now instances the whole CJK at one source weight, solved so the page
  keeps its colour: stroke +6.5% on hangul, −6.2% on han/kana. **Every CJK
  outline changes and every hash in `SHA256SUMS` is new.** Hangul letterspacing
  tightens as a side effect, `T` 0.1308 → 0.1260, and han's improves from −4.3%
  to −1.8% against Pretendard's own.
  See [ADR 0014](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md).
- **README is now in three languages** — English, 日本語, 한국어 — with the same
  switcher in each.

### Fixed

- **`docs/sample.txt` did not say how to read it on Windows.** Console Host
  decodes with the system ANSI code page — 949 on a Korean install — so `type`
  mojibakes a UTF-8 file there, and garbled Korean in a font sample reads as
  the font failing. The header now gives the `chcp` and `OutputEncoding` forms
  and says which symptom is which: mojibake is encoding, boxes are coverage.
- **`docs/sample.txt` block 8 tested nothing.** It was titled "NERD FONT ICONS
  — Powerline and the icon sets" and contained four ordinary Unicode symbols
  and not one of the font's 3518 private-use glyphs, so on screen it read as
  though the font had no icons. It now uses real Powerline separators and icon
  glyphs, every one width-checked against the shipped `hmtx`. Found by running
  the sample on Windows — see [ADR 0017](docs/adr/0017-windows-verified.md).
- **The gate was asserting the defect above, not missing it.** It required
  `hangul stroke == han stroke` and passed at 1.000×. It now asserts the
  source's own ratio per weight, and on **both** axes: the two point opposite
  ways — hangul verticals run 14% heavier than han's, its horizontals 3–6%
  lighter — so no single number could ever have covered it. 154 checks → 158.
- **A gate message that claimed more than the gate asserted.** The
  letterspacing check reads `T <= target × 1.1`, one-sided by design, but was
  labelled "within 10% of Pretendard's" — a two-sided band. Bold han passes it
  at −21.1%. The label now says "no looser than".

### Removed

- **The install scripts.** Unzipping and using the system font installer is one
  step, and beyond that a package manager handles upgrade and uninstall too —
  neither of which these attempted. The download path hardcoded a release URL,
  which returned 404 for as long as this repository was private with nothing
  able to notice, and the Windows script was published having never been
  executed. See [ADR 0016](docs/adr/0016-no-install-scripts.md).

### Known

Each of these is a decision with a record behind it rather than an oversight.

- Ambiguous-width characters resolve to **one** cell. A terminal configured
  `ambiguous = wide` will shear those rows. A font has one advance per glyph
  and cannot serve both readings.
- **Windows Console Host widens NFD hangul**, giving every conjoining jamo a
  cell where the width provider says 2/0/0. Windows Terminal, same font, renders
  NFC and NFD identically. Changing the advances to suit conhost would shear
  every renderer that is right. See
  [ADR 0017](docs/adr/0017-windows-verified.md).
- `☎ ☏ ♨` are not shipped. They are one cell here, every source draws them
  full-width, and halving a full-width design halves its stroke past what the
  `wght` axis can restore. This is the only gap in cp949.
- Hinting reaches y only, so vertical strokes gain nothing from it. Under
  grayscale antialiasing that is visible; under subpixel rendering it is not.
  See [ADR 0010](docs/adr/0010-ttfautohint-hints-y-only.md).
- The `OS/2` codepage bits declare this face eligible for East Asian text in
  Windows applications. That is asserted by the gate and has never been
  **observed** — Word has not been run.

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

[Unreleased]: ../../compare/v1.0.1...HEAD
[1.0.1]: ../../compare/v1.0.0...v1.0.1
[1.0.0]: ../../releases/tag/v1.0.0
[0.9.0]: ../../releases/tag/v0.9.0
