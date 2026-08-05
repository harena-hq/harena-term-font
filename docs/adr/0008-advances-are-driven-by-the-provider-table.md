# 0008 — Advances are driven by the width table, not checked against a list

Status: **permanent**.

## Context

If a glyph's advance disagrees with the number of cells the terminal reserved
for its codepoint, the row shears — everything after it is displaced. The
authority for how many cells are reserved is not the font and not Unicode's
`East_Asian_Width` directly, but the width provider the emulator actually loads.

The obvious approach is a hand-written cross-check list of the codepoints someone
judged risky. That can only confirm the cases someone thought of.

## Decision

`scripts/xterm_widths.mjs` extracts the **full per-codepoint table** from
`@xterm/addon-unicode11`, pinned exactly in this repository's `package.json`, and
the build is *driven* by it. `scripts/verify.py` then re-derives every advance
from the built binary and checks it against the same external table, across all
**21349** covered codepoints.

Zero mismatches becomes **structural** rather than lucky.

## What this immediately found

23 disagreements inherited from Iosevka, none introduced by the merge:

- **8 zero-width formatting characters** drawn a full cell wide —
  U+200B–200D, U+2060–2064
- **15 Emoji_Presentation symbols** drawn one cell where the provider reserves
  two — U+231A, U+231B, U+2329, U+232A, U+23E9–23EC, U+23F0, U+23F3, U+25FD,
  U+25FE, U+26A1, U+26AA, U+26AB

`⚡`, `⚪` and `⚫` appear in ordinary CLI output and each would have sheared its
row. A hand-written list would not have contained them.

`enforce_grid()` corrects them generically against the provider, so an upstream
bump is corrected too rather than needing the list re-audited.

## Guards the gate adds

- every advance is exactly 0, one cell, or two — nothing in between
- the CJK cell is exactly 2× the Latin advance
- no codepoint maps to `.notdef`

## Two things `enforce_grid()` must not do, and the gate must not skip

**The condense pass is scoped to glyphs this build introduced** — those named
`cjk*`, `jamo*` and `mp*` — and leaves inherited glyphs alone. Unscoped, it
squashes 1023 Nerd Font icons and long arrows that are drawn at up to 1.87× of a
cell **on purpose**, and the change cascades through composites so that K and J
drift apart outside the han range.

**The collision check scans every glyph in every full-width range**, never a
sample and never a subset of ranges. Sampling every 17th syllable reports a
maximum of 0.986 where the true maximum is 0.997, and scanning only hangul and
han leaves kana, CJK punctuation and fullwidth forms unchecked — where Bold
U+FF37 sits at 1.027, genuinely overlapping the cell after it. **Sampling hides
the extreme, and the extreme is the entire question.**

## Downstream

The provider is a dependency, not a constant. Bumping `@xterm/addon-unicode11`
means regenerating `build/xterm-widths.json` and rebuilding; the gate fails
loudly if the two disagree. And because the table decides every advance in the
font, the version is pinned exactly rather than by range — a resolve that drifts
is a font that drifts.

The extracted ranges must cover everything the build declares, including
U+1100–11FF. A range the table omits is a range the build silently skips and the
gate cannot check; see
[0013](0013-the-width-table-must-cover-what-the-build-declares.md).
