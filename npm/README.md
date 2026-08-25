# Harena Term

The web-font package for Harena Term, a Korean, Japanese and Latin terminal
typeface whose narrow and wide glyphs land on an exact 1:2 cell grid.

The package contains four WOFF2 faces: Regular and Bold for both the Korean
(`K`) and Japanese (`J`) regional cuts. It contains no JavaScript and runs no
install script.

The npm package and the embedded typeface are versioned independently. Package
metadata under `harena.fontVersion` identifies the exact Harena Term release
carried by each npm version.

Package-only changes are recorded in `CHANGELOG.md`.

## Install

```sh
npm install @harena-hq/term-font
```

Most users should load the Korean cut:

```css
@import "@harena-hq/term-font/k.css";

.xterm {
  font-family: "Harena Term K", monospace;
}
```

Load the Japanese cut when Japanese regional han forms are preferred:

```css
@import "@harena-hq/term-font/j.css";

.xterm {
  font-family: "Harena Term J", monospace;
}
```

Importing `@harena-hq/term-font` loads both cuts. Direct font-file subpaths are
also exported under `@harena-hq/term-font/fonts/`.

K and J differ only in 611 regional han glyphs. Their metrics are identical.
K is the default choice for Korean text or when there is no regional
preference.

## Compatibility

Harena Term follows the xterm.js Unicode 11 width provider and renders Unicode
East Asian Width `Ambiguous` characters as one cell. It is not suitable for a
terminal configured to reserve two cells for ambiguous characters.

The package is approximately 20 MB because each regional cut carries a large
CJK repertoire. Import only `k.css` or `j.css` unless both cuts are needed.

Desktop TTF archives, complete documentation, coverage and reproducible build
instructions are available from the
[Harena Term repository](https://github.com/harena-hq/harena-term-font).

## License

The fonts are distributed under the SIL Open Font License 1.1. Embedded icon
sets retain their own notices and attribution requirements; see
`THIRD_PARTY_NOTICES.md` and `licenses/` in this package.
