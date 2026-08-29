# Changelog

Notable changes to the `@harena-hq/term-font` npm package. Package versions
describe the CSS, exports, metadata, notices and selected immutable Harena Term
release; they are independent from the version embedded in the font files.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this package uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] — 2026-08-29

### Changed

- Package Harena Term 1.0.2, which stops the hinting erasing horizontal strokes
  at 15 and 16 ppem — the sizes a browser terminal at `devicePixelRatio` 1 most
  often lands on.

## [1.0.1] — 2026-08-27

### Changed

- Package Harena Term 1.0.1, which aligns the `*` working-indicator glyph with
  `·` and `+` in terminal animations.

## [1.0.0] — 2026-08-24

### Added

- Initial npm distribution of Harena Term 1.0.0: Korean and Japanese Regular
  and Bold WOFF2 faces, separate CSS entry points, package-relative font
  exports and the complete redistribution notices.

[Unreleased]: ../../../compare/v1.0.2...HEAD
[1.0.2]: ../../../compare/v1.0.1...v1.0.2
[1.0.1]: ../../../compare/v1.0.0...v1.0.1
[1.0.0]: ../../../releases/tag/v1.0.0
