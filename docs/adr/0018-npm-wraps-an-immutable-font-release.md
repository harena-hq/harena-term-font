# 0018 — The npm package wraps an immutable font release

Status: **accepted**.

## Decision

Publish the four WOFF2 faces as `@harena-hq/term-font`. The tracked `npm/`
directory owns the package metadata and CSS; `scripts/package_npm.py` joins it
to verified `dist/*.woff2` only at the release boundary. TTF remains a GitHub
Release format for desktop installation.

The npm package version and embedded font version are independent:

```json
{
  "version": "1.0.1",
  "harena": { "fontVersion": "1.0.0" }
}
```

`version` identifies the registry-facing product: its CSS, exports, metadata,
notices and chosen font payload. `harena.fontVersion` identifies the immutable
Harena Term release inside it. The packager checks the latter against the
build's `VERSION` and each WOFF2's internal records, then checks every byte
against `SHA256SUMS`.

Font releases use `vX.Y.Z`. They change font data, update
`harena.fontVersion`, independently advance the package's own SemVer, and
publish GitHub font assets plus npm. Package-only releases use `npm-vX.Y.Z`.
They may change CSS or metadata and publish only npm while retaining the exact
font bytes and internal version already released. The numbers may coincide but
are never required to: a package-only `1.0.1` must not prevent a later font
`1.0.1` from shipping inside, for example, package `1.0.2`.

CSS uses `font-display: block`. A terminal font's 1:2 grid is part of its
behaviour; rendering a fallback and swapping after layout can visibly move
columns. Consumers that want another loading policy can provide their own
`@font-face` declaration against the exported font files.

The package declares the combined SPDX obligations of its contents and ships
`OFL.txt`, `THIRD_PARTY_NOTICES.md` and every referenced licence text. It runs
no install script, preserving [0016](0016-no-install-scripts.md).

## Why the versions are separate

Making the npm version equal the font's `nameID 5` looked consistent and made
the wrong object authoritative. A CSS typo would then require restamping every
font, changing otherwise identical TTF and WOFF2 bytes, rewriting
`SHA256SUMS`, and publishing a new desktop font release. Nothing about that
sequence improves the correction; it only destroys the identity of a proven
font build.

The inverse error is also prevented. Independent versions do not mean an
arbitrary local font can enter the package: the declared font version and
tracked hashes are gates, not documentation.

## Publishing boundary

Normal CI assembles, packs and installs the package before a tag exists. A
release build passes the resulting tarball to a separate job through an
immutable Actions artifact. Only that publisher job receives
`id-token: write`; it checks out no repository source and installs no
dependencies before npm trusted publishing. Upstream build scripts therefore
never run in an environment capable of minting registry credentials.

The font version remains declared in `scripts/build.py`. Release checks read it
through `scripts/font_version.py`, an AST reader that imports no build
dependency and accepts exactly one top-level literal `VERSION` assignment.
Normal CI executes it with Python's `-S` option to keep that dependency-free
boundary executable rather than documentary.

The registry is checked before the build and rejects a package version already
published. Every package version must also have an entry in
`npm/CHANGELOG.md`. Package-only tags produce a notes-only GitHub Release from
that entry, preserving a public history without duplicating the registry
tarball as a GitHub asset. That notes release depends on successful npm
publishing, so it cannot advertise a registry version that failed to appear.
It is explicitly excluded from GitHub's Latest selection, which remains the
font release carrying the TTF and WOFF2 archives.

## Revisit when

- npm ceases to support CSS and font-file exports in a package without a
  JavaScript entry point;
- the browser distribution needs subsets rather than the four full WOFF2
  faces; or
- a loading API replaces static `@font-face` CSS and can preserve the terminal
  grid with a better default than `block`.
