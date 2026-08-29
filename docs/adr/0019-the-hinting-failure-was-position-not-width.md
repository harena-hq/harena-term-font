# 0019 — the hinting failure was stroke position, not stroke width

Status: **accepted and applied**. Ships in 1.0.2. Partly supersedes
[0010](0010-ttfautohint-hints-y-only.md): that record's decision on `-a` stands,
its ground for it does not, and its instruction to ship ttfautohint's defaults
is replaced.

## Context

A reader reported that at the size they work at, `텰` rendered as `뎔` and the
circle of `ㅇ` in `열` was open at the top. Measured, both are real and both are
the hinting rather than the outline:

```
텰 @ 16 ppem, the ㅌ, left half of the cell, both sides on a common baseline
(the two renders differ in bitmap_top, 15 against 14, so row indices do not
line up and printing each from its own row 0 pairs the wrong rows)

   y   unhinted                          shipping default
  14   168 220 220 220 220 220 220 123     6   8   8   8   8   8   8   4  <- top bar
  13   196 224 100 100 100 100 100  56   196 204   0   0   0   0   0   0
  12   196 204   0   0   0   0   0   0   196 204   0   0   0   0   0   0
  11   234 255 244 244 244 244 244  57   197 212   8   8   8   8   8   1
  10   206 255  64  64  64  64  64  15   236 255 255 255 255 255 255  60
   9   196 204   0   0   0   1  23  52   196 204   0   0   0   0   0   0
   8   255 255 222 226 234 250 255 255   202 212   8   8   8  16  36  57
   7    91 117 106 102  94  78  49  18   255 255 255 255 255 255 255 231
```

The top bar is not thinned. Its height rounds to zero and it is gone: at y=14
the design draws 220 and the shipped font draws 8, which is below anything a
reader can see. The other two bars survive, pushed down a row — 11 to 10 and 8
to 7 — which is what leaves a `ㄷ`. `ㅇ`'s top arc goes the same way, 254 down
to 98.

The outline is not at fault. Radial stroke thickness around `ㅇ`, in font units:
53 / 59 / 75 / 83 / 75 / 60 at 0-150°, against 53 / 60 / 73 / 80 / 72 / 58 at
180-330° — mirror-matched within 2 units. And the unhinted render of `텰` shows
three bars at every ppem from 12 to 22.

It is also not general, and not `ㅌ`'s alone. Of the 588 syllables with a `ㅌ`
initial, the gate below flags 8 at 15 ppem and 9 at 16; `티`, `타`, `토`, `투`,
`틸` are all clean. Only crowded combinations fail — which is why a per-jamo
spot check would have found nothing and why the gate this ADR adds sweeps all
11172.

`ㅌ` is where it was noticed rather than where it is worst. Of the 39 the gate
flags on 1.0.1, the initials are **`ㄹ` 19, `ㅌ` 17, `ㅇ` 2, `ㅋ` 1** — the same
mechanism wherever horizontal strokes stack, and `ㄹ` stacks three of them too.

## Why `-a` is the wrong instrument, and where 0010 was too broad

ADR 0010 closed the `-a` search space, and did not qualify it: "**Do not sweep
`-a` combinations** — the avenue is closed by the tool's design." Its reasoning
was about the y axis all along — "its three slots select stem *width*
quantisation, and for a y-only autohinter stem width is the thickness of a
horizontal stroke" — so this is not a case of 0010 having closed x while y
stayed open. **The general closure was too broad**, and saying otherwise would
make that record look more careful than it was.

What was too broad, precisely: 0010 tested one cut, `-a nsq`, and generalised
from it. Two findings from sweeping properly:

- **`-a` slot 1 is dead here.** `-a nsq` produces a font byte-identical to the
  shipping `-a qsq` in `glyf`, `fpgm` and `cvt`, differing only in `prep`, and
  renders identically. That is the one cut 0010 tested, and it explains that
  ADR's null result: `nsq` and `qsq` differ only in slot 1, grayscale, and the
  renderer reads slot 3. The measurement was sound; the slot was unused.
- **Slot 3 masks rather than fixes.** `-a qss` closes `ㅇ` but leaves `ㅌ`
  showing two bars, because the bar's edges still round together — and it costs
  glyph-to-glyph uniformity, exactly the trade 0010 weighed when it chose the
  quantised mode: ink-ratio standard deviation at 16 ppem goes 0.0218 → 0.0415.

So 0010's *decision* survives — `-a` keeps its shipping value — while its
*ground* does not: `-a` was closed for being unable to change anything, and slot
3 changes plenty. The reason to leave it alone is now a different one. The
failure is a stroke **position** problem, `-a` quantises width, and once
position is addressed `-a` buys nothing worth its cost in uniformity.

## The measurement had to be fixed first

**Twice**, and both mistakes are the same shape: a number that moved for a
reason other than the one being measured.

The first metric counted horizontal strokes in the hinted render against the
unhinted one and flagged any drop. It reported 14737 failures for the shipping
font, and ranked `-a qss -x 20 -X 15` a 29% improvement. Opening the flagged
glyphs showed the hinted render was usually *better*: two faint rows that the
design smears across a pixel boundary become one crisp bar, and the counter read
that merge as a deletion. Re-measured for damage rather than difference, the same
cut is a 12% **loss**, and the option that wins is one the first metric ranked
mid-field.

The narrower question is the one a reader notices:

> a horizontal stroke the unhinted outline draws at ≥50% coverage must still be
> drawn, at ≥25%, within ±2 rows of where it was.

Hinting may merge two faint strokes. It may not erase a solid one. The ±2
tolerance is measured, not guessed: over 2235 syllables at 16 and 17 ppem,
hinting never moved a glyph's ink top by more than two rows.

That still counted the wrong thing, which is the second mistake. A run of four
dark columns is not a bar: at 13-18 ppem the shallow tail of a diagonal — `ㅅ`
`ㅈ` `ㅊ` `ㄱ` — makes exactly four, and those swamp the signal. Of the 569 the
metric reported on the *fixed* font, every single one was four columns wide and
none was a bar. A budget set from that number would have been a noise floor
wearing the label of a defect count, and worse than no check at all: 30 bars
could go missing while 30 diagonals stopped being miscounted, and the total
would not move.

Requiring a run to span a third of the glyph's own ink separates them. The
shipping 1.0.1 binaries then flag **39** — every one at 15 or 16 ppem, which are
the two sizes that were reported, and among them `텰` at both and `열` at 15 —
and 1.0.2 flags **none**, in either weight and either cut. So the gate asserts
zero — which trades a fitted count for a fitted threshold rather than escaping
the fitting, but trades well: the count swung by hundreds on a two-flag change,
where this answer holds from 0.35 to 0.50.

Bold has no positive control. It reports 0 on the 1.0.1 binaries too, so the
check is proven against Regular and assumed to transfer.

That fraction was chosen, not derived, and the honest thing is to say by what
rule: **the smallest value at which the shipped font is clean.** Below 0.35
there is no margin — 1.0.2 reports 4 at 0.32 and 95 at 0.30. Above it the answer
is stable, 0.35 through 0.50 all reporting zero on 1.0.2 while still catching
34-39 on 1.0.1, so the conclusion holds anywhere in that band and only the
sensitivity moves. 0.35 is the one value in the band that also catches `열` at
15; 0.40 loses it. Maximum sensitivity subject to no false positives is a rule a
later reader can re-apply. "A third" is not.

## Decision

Hint with **`-x 20 -X 15`** and leave `-a` at its default.

`-x` extends x-height rounding-up through 20 ppem (default 14) and recovers 16;
`-X 15` exempts 15 ppem from that rounding and recovers 15. Both act on blue-zone
rounding, which is where the stroke's position is decided.

Bars erased over all 11172 syllables at 13-18 ppem, as `verify.py` counts them,
beside the glyph-to-glyph
uniformity 0010 weighed — the standard deviation of hinted ink over unhinted ink
at 16 ppem, where a high value is one syllable reading bolder than its
neighbours:

| | Regular | Bold | uniformity @16 | `텰` `열` |
|---|---|---|---|---|
| `-a qsq` (was shipping) | 39 | 0 | 0.0218 | broken |
| `-a qss -x 20 -X 15` | 2 | 0 | 0.0415 | fixed |
| **`-x 20 -X 15`** | **0** | **0** | 0.0212 | **fixed** |

Only the last row is re-derived by the gate on every build; the other two are
one-off measurements of binaries that are not in the tree, and a change to
`_bars` or `_kept` silently invalidates them. The `-a qss` cell has already been
wrong once for exactly that reason — it read 1 until `_kept` stopped using a
flat minimum, which added `힗`@18. Regenerate these two rows whenever the metric
moves, or they become the kind of stale number this ADR is about.

`-a qss` gets close on the bars and still costs the uniformity by half again,
which is the whole of its case against it: it buys nothing the blue-zone options
do not buy more cheaply.

The uniformity column is not bolded for the shipping cut on purpose. 0.0212
against 0.0218 is a 3% difference; an independent reading of the same idea, with
a different sample and normalisation, put the shipping cut marginally *worse*
than 1.0.1 rather than marginally better. **Unchanged within measurement noise**
is the claim that survives either reading. What does not move under either is
`-a qss` being far worse than both.

## Cost

- **The Latin moves at two sizes.** Ink height in px, counting rows that carry
  a pixel at coverage 64 or more out of 255, shipping → this: at 15 ppem `H`
  13 → 12, at 16 ppem `H` 13 → 14 and `x`/`o` 9 → 10. At 15 the new value is the
  unhinted design's own height at that floor; at 16 it runs a pixel over.
  Accepted deliberately —
  [0004](0004-latin-advance-sets-the-hangul-ceiling.md) already sets the Latin
  small against the hangul, so a pixel back at one size runs with that grain
  rather than against it.
- **Some syllables sit a pixel lower at 15 ppem**, `ㅎ` initials most often (40%
  of them, against a 23% baseline) — `ㅎ` has a bar above a circle and the least
  vertical room to give. Against that, the line as a whole is *more* even than
  before: syllables off the modal ink top or bottom fall from 36.2% to 25.3% at
  15 ppem and from 38.8% to 22.0% at 16. The unhinted design is 19.3% / 9.6%.

  Those five figures need their definition stated or they cannot be re-derived,
  which is the standard the rest of this repository holds to. Every third hangul
  syllable (3724 of them); ink top and ink bottom taken as the first and last
  rows carrying a pixel at coverage 64 or more out of 255, measured from the
  baseline; the
  fraction of syllables whose ink top differs from the modal ink top, and the
  same for the bottom, averaged. The `ㅎ` figures count syllables whose ink
  bottom falls below the modal one at 15 ppem, over all 588 with a `ㅎ` initial
  against the same third-of-everything sample.
- **The gate covers bars, not arcs.** `열` at 16 ppem, where the top of `ㅇ`
  opened, is not caught: a circle's arc is 4 columns of a 15 px glyph, below the
  threshold that makes the check mean anything. The fix covers it; the check
  does not prove it. Nor does the check have a positive control in Bold, which
  reports zero on the defective binaries as well.

## Downstream

`20` and `15` are fitted constants. They were found by search over the option
space and confirmed against every one of the 11172 syllables, but nothing derives
them, and a rebuild at different weights could need refitting. So `verify.py`
asserts the property they buy — no solidly drawn hangul bar is erased at 13-18
ppem — and not the values. If that assertion ever fails, the flags are the first
thing to re-fit.

## The recurring shape

**A baseline is not a target.** The first metric took the unhinted render as
what the hinted one should reproduce. But reproducing it is not the goal —
improving on it is, which is the whole reason the hinting stage exists. Measuring
deviation from a baseline answers "did it change" when the question was "did it
get worse", and the two part company precisely where the stage is doing its job.
The fix was not a better threshold; it was asking about damage instead of
difference.
