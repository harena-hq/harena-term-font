# 0013 — The width table must cover every range the build declares

Status: **permanent**. Third occurrence of the blind spot
[0008](0008-advances-are-driven-by-the-provider-table.md) describes.

## Context

Asking why cp932 coverage measured 87.5% turned up something structural rather
than a missing glyph or two.

`build.py` imports a CJK codepoint only if the width table has an entry for it,
and skips it otherwise with `"not in width table"` — recorded in the build
report and read by nobody. The width table comes from `xterm_widths.mjs`, which
asks the provider for an explicit list of ranges.

**The two lists had drifted.** `HANKANA` declared `U+FE30–FE4F` and
`U+FFE0–FFE6`; the extractor asked for neither. So every codepoint in them was
silently dropped, including `￥` — the fullwidth yen sign, which Pretendard has
and which is not a rare character.

This is the third time. The first was the jamo, where the same omission made the
gate structurally incapable of catching the NFD defect of
[0007](0007-the-font-composes-nfd-hangul-itself.md). A range absent from the
authority is a blind spot, not a pass.

## Decision

1. The extractor's ranges are widened to cover `U+3190–319F`, `U+3200–32FF`,
   `U+3300–33FF`, `U+FE30–FE4F` and `U+FFE0–FFE6`.
2. **The gate asserts the two lists agree**: every range in `build.py`'s
   `GROUPS` must have at least one entry in the width table. That is what stops
   a fourth occurrence.

## What the fix recovered

81 glyphs, all from sources already in use, at the tuning the rest of the CJK
carries — `MPLUS_SCALE`, which is Pretendard's own 0.9572 resize of M PLUS
composed with this build's 1.0667, so a glyph taken straight from M PLUS lands
at the same size as one that reached us through Pretendard.

| | count | source | why it was missing |
|---|---:|---|---|
| halfwidth katakana | **63** | M PLUS 1p | the han/kana ranges stopped at U+FF60 |
| 〇 〒 〓 | 3 | M PLUS 1p | Pretendard has none of them |
| 〈 〉 | 2 | M PLUS 1p | Pretendard draws them at advance 698 against the cell's 1920, so the advance guard rejected them — the bracket case again |
| ￠ ￡ ￥ | 3 | Pretendard | the width table did not cover U+FFE0–FFE6 |
| enclosed / squared | 10 | Pretendard | now in range |

M PLUS draws the halfwidth katakana at advance 500 of its 1000 em — genuinely
half-width, not a full-width glyph to be squeezed — so they import at one cell
directly. Widest is ﾍ at 0.958 of the cell after tuning, against 0.990 for the
full-width kana already shipping.

cp932 coverage excluding the gaiji rows went **87.5% → 99.4%** at this point, gaps 110 → 39, and the additions below took it to 99.56%.

## The rule for the enclosed and squared blocks

Pretendard has 81 of them — including **㈜**, the Korean counterpart of ㈱ — but
draws every one **proportionally**, at advances of 2280 to 3638 source units
against the cell's 1920. Fitting those to the grid needs a horizontal
compression of 0.53× to 0.84×. That is distortion, not scaling: the enclosing
circle of ㈜ would become an ellipse. The project has consistently refused to
squeeze outlines ([0003](0003-stroke-weight-compensated-through-wght.md) exists
because scaling to fix one metric breaks another), and this is the same refusal.

A squared unit is *designed* wide — it packs "mg" into a box. Putting it on a
1 em grid is a redesign, not a transform.

So the rule is: **a glyph is imported when some source draws it at full width,
and left out when the only source draws it proportionally.** What follows applies
that rule in both directions.

## Settled: the enclosed and squared blocks come from Source Han Sans

`㈱` and `㈲` were first taken from M PLUS 1 Code, the only other source that
had them. That was wrong for a reason worth recording: **㈹ is not in M PLUS 1
Code**, so three glyphs of one visual family would have come from two fonts.
Measured, M PLUS's enclosure is 1.3% wider with a 10% thinner bracket, while
Noto draws all three identically at ink 0.938 × 0.912 with a 0.062 bracket
stroke. `㈹` beside `㈱` would have read as a different design.

So the whole family comes from one source, and M PLUS 1 Code is dropped
entirely — one fewer pinned archive, licence entry and provenance row.

**The "fourth letterform system" objection was wrong**, and this ADR said it
before it was measured. Source Han Sans is where Pretendard's own hangul and han
come from. Against the shipped face at 96px:

| source | hangul | han | kana |
|---|---:|---:|---:|
| Pretendard JP — our actual source | 0.916 | 0.848 | 0.845 |
| **Noto Sans KR — Source Han Sans** | **0.915** | **0.892** | 0.608 |
| M PLUS 1p — already grafted from | — | 0.680 | 0.739 |

Noto matches our hangul as closely as our own source does, and is far closer on
han than M PLUS 1p, which we already ship glyphs from. This is returning to the
well, not introducing a stranger. (The han figure flatters Noto slightly: our
han are instanced at `wght` 474.6, so comparing both at 400 is not like for
like. The hangul figure is the solid one.)

Two transforms, each solved against the shipped face the way the M PLUS one was:

| | wght | scale | dy | matched against |
|---|---|---|---|---|
| enclosed and squared, U+3200–33FF | 440 / 640 | 0.9993 / 0.9992 | +11 | our han |
| archaic compatibility jamo, U+3165–318E | 480 / 700 | 1.0988 / 1.0779 | −1 | our hangul |

The jamo scale is larger because Noto sets hangul at 920 of its 1000 em against
our 1000 cell — normalising that is the identity of
[0002](0002-advance-normalisation-is-an-identity.md) again.

544 glyphs, and the graft now reads the provider per codepoint rather than
assuming a cell count, so the advance is never guessed.

`￢ ￣ ￤` stay with M PLUS 1p, and so do the brackets and the halfwidth
katakana. The rule is **match the source your neighbours came from**, not "one
source for everything": the brackets were chosen on measured fill (M PLUS 0.383
against Source Han 0.315 and Pretendard 0.221), and the halfwidth katakana are
siblings of the full-width kana, which are M PLUS by way of Pretendard.

## What remains excluded

cp932 **100.00%**. cp949 **99.98%** — four codepoints, one of which is `U+007F`
DEL and not a glyph at all:

| | EAW | provider | why |
|---|---|---|---|
| ☎ U+260E, ☏ U+260F, ♨ U+2668 | Ambiguous | **1 cell** | every source draws them full-width |

Their East_Asian_Width is **Ambiguous** — Unicode's own "depends on context":
narrow in a Western one, wide in a legacy East Asian one. Terminals expose that
as a setting; the provider this build follows resolves all 1201 Ambiguous
codepoints in its table to one cell, and `♥ ○ → ± '` are in that same class and
already ship at one cell from Iosevka.

A font has one advance per glyph, so it cannot satisfy both readings. The
asymmetry decides the direction: a one-cell glyph in a two-cell slot leaves a
gap, while a two-cell glyph in a one-cell slot overlaps the character after it.

Whether to import them at one cell is an open aesthetic call rather than a
constraint. Measured, Noto's ☎ scaled uniformly to a one-cell advance lands at
0.92 of the cell wide, right in the range Iosevka's own one-cell symbols occupy
(0.85–0.96) — an earlier claim here that it would look undersized was wrong on
the dimension that matters. It would be 0.34 em tall against 0.44 for ★ ● ■,
which follows from the glyph being a wide pictograph rather than from the scale.
